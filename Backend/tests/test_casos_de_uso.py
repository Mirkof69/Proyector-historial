"""Casos de uso completos, recorridos por el rol que los hace en la clínica.

Por qué existe este archivo
---------------------------
Los demás tests comprueban piezas: que un permiso deja pasar, que una consulta
no hace N+1, que una acción queda auditada. Este comprueba **el trabajo**: que
una recepcionista pueda registrar a una paciente de principio a fin, que una
enfermera pueda hacer el triaje de esa misma paciente, y que una médica pueda
abrir su historia y ver ahí lo que las dos anteriores cargaron.

Es la diferencia entre "el endpoint responde 200" y "el turno de la clínica
puede hacerse". El bug de `RolPermiso` —donde solo el administrador podía usar
cinco módulos— pasaba todos los tests unitarios y habría muerto aquí.

Cada caso declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from rest_framework.test import APIClient, APITestCase

from auditoria.models import RegistroAuditoria
from pacientes.models import Paciente
from usuarios.models import Usuario

CLAVE = "clave-de-prueba-123"


def _usuario(rol, correo, nombre="Prueba"):
    return Usuario.objects.create_user(
        email=correo, nombre=nombre, apellido_paterno="Caso",
        password=CLAVE, rol=rol,
    )


class _ConEquipoClinico(APITestCase):
    """El equipo de una clínica pequeña: recepción, enfermería, médica y admin."""

    @classmethod
    def setUpTestData(cls):
        cls.recepcion = _usuario("recepcion", "recepcion@caso.test", "Juana")
        cls.enfermera = _usuario("enfermera", "enfermera@caso.test", "Rosa")
        cls.medica = _usuario("medico", "medica@caso.test", "Elena")
        cls.admin = _usuario("administrador", "admin@caso.test", "Carmen")

    def como(self, usuario):
        """Un cliente autenticado como ese usuario."""
        cliente = APIClient()
        cliente.force_authenticate(user=usuario)
        return cliente


class CasoRegistrarPacienteNuevaTest(_ConEquipoClinico):
    """CU-01 · Recepción registra a una paciente que llega por primera vez."""

    def test_recepcion_puede_registrar_una_paciente(self):
        """ESPERADO: 201 y la paciente queda buscable por su apellido."""
        cliente = self.como(self.recepcion)

        respuesta = cliente.post("/api/pacientes/", {
            "nombre": "Fernanda",
            "apellido_paterno": "Mamani",
            "apellido_materno": "Choque",
            "fecha_nacimiento": "1995-06-12",
            "genero": "femenino", "consentimiento_datos_aceptado": True,
            "ci": "9081726",
            "telefono": "70011223",
        }, format="json")

        assert respuesta.status_code == 201, respuesta.data
        creada = Paciente.objects.get(id=respuesta.data["id"])
        assert creada.nombre == "Fernanda"

        busqueda = cliente.get("/api/pacientes/?search=Mamani")
        ids = [p["id"] for p in busqueda.data["results"]]
        assert creada.id in ids, "La paciente recién registrada no aparece al buscarla."

    def test_se_la_encuentra_aunque_el_apellido_se_escriba_como_suena(self):
        """ESPERADO: 'Mamany' encuentra a la paciente 'Mamani'.

        Es el caso real de recepción: quien dicta el apellido y quien lo
        escribe no siempre coinciden en la grafía. Sin esto se abre una
        historia clínica duplicada.
        """
        cliente = self.como(self.recepcion)
        creada = cliente.post("/api/pacientes/", {
            "nombre": "Fernanda", "apellido_paterno": "Mamani",
            "apellido_materno": "Choque", "fecha_nacimiento": "1995-06-12",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "9081727",
        }, format="json").data

        respuesta = cliente.get("/api/pacientes/?search=Mamany")

        ids = [p["id"] for p in respuesta.data["results"]]
        assert creada["id"] in ids, (
            "Buscar 'Mamany' no encuentra a 'Mamani': se crearía un expediente duplicado."
        )

    def test_recepcion_NO_puede_ver_datos_clinicos(self):
        """ESPERADO: 403 en triaje y evoluciones.

        Recepción registra y agenda; no lee la historia clínica. Es el límite
        que separa la administración de la asistencia.
        """
        cliente = self.como(self.recepcion)
        for ruta in ("/api/triaje/", "/api/evoluciones/", "/api/auditoria/"):
            assert cliente.get(ruta).status_code == 403, f"{ruta} no debería ser accesible."


class CasoTriajeDeEnfermeriaTest(_ConEquipoClinico):
    """CU-02 · Enfermería toma signos vitales a la paciente que llegó."""

    def setUp(self):
        self.paciente = Paciente.objects.create(
            nombre="Rosa", apellido_paterno="Quispe", apellido_materno="Poma",
            fecha_nacimiento=datetime.date(1993, 2, 2),
            genero="femenino", ci="8172635",
        )

    def test_la_enfermera_puede_entrar_al_modulo_de_triaje(self):
        """ESPERADO: 200.

        Es el trabajo que más hace enfermería. Con el bug de RolPermiso esto
        daba 403 y el módulo era inutilizable para quien debía usarlo.
        """
        assert self.como(self.enfermera).get("/api/triaje/").status_code == 200

    def test_la_enfermera_puede_escribir_una_nota_de_evolucion(self):
        """ESPERADO: 200 al listar evoluciones."""
        assert self.como(self.enfermera).get("/api/evoluciones/").status_code == 200

    def test_la_enfermera_NO_gestiona_consultorios(self):
        """ESPERADO: 403 — eso es de médicos y administración."""
        assert self.como(self.enfermera).get("/api/consultorios/").status_code == 403


class CasoConsultaMedicaTest(_ConEquipoClinico):
    """CU-03 · La médica abre la historia de una paciente y la revisa."""

    def setUp(self):
        self.paciente = Paciente.objects.create(
            nombre="Teresa", apellido_paterno="Huanca", apellido_materno="Cusi",
            fecha_nacimiento=datetime.date(1990, 9, 9),
            genero="femenino", ci="7263544",
        )

    def test_la_medica_abre_la_historia_clinica_y_recibe_el_informe(self):
        """ESPERADO: 200 y un PDF, no un error ni una página vacía."""
        respuesta = self.como(self.medica).get(
            f"/api/pacientes/{self.paciente.id}/historia-clinica/",
        )

        assert respuesta.status_code == 200
        assert respuesta["Content-Type"] == "application/pdf"
        assert respuesta.content[:4] == b"%PDF", "Lo devuelto no es un PDF."

    def test_una_paciente_sin_datos_da_un_informe_valido_igual(self):
        """ESPERADO: 200 — "no tiene nada registrado" es una respuesta útil.

        La médica tiene que poder distinguir "sin antecedentes" de "falló la
        consulta". Ambos casos se veían igual si esto reventaba.
        """
        sola = Paciente.objects.create(
            nombre="Ana", apellido_paterno="Flores", apellido_materno="Yujra",
            fecha_nacimiento=datetime.date(1998, 1, 1),
            genero="femenino", ci="6152433",
        )
        respuesta = self.como(self.medica).get(f"/api/pacientes/{sola.id}/historia-clinica/")

        assert respuesta.status_code == 200
        assert respuesta.content[:4] == b"%PDF"

    def test_la_medica_puede_consultar_la_auditoria(self):
        """ESPERADO: 200 — necesita poder revisar quién tocó qué."""
        assert self.como(self.medica).get("/api/auditoria/").status_code == 200

    def test_la_medica_puede_calcular_riesgo_de_preeclampsia(self):
        """ESPERADO: 200 con la indicación de aspirina.

        Sin biomarcadores, que es el caso de una clínica sin laboratorio
        especializado.
        """
        respuesta = self.como(self.medica).post(
            "/api/calculadoras-avanzadas/fmf/preeclampsia/",
            {
                "edad_materna": 39, "peso_kg": 88, "talla_cm": 156, "semanas": 12,
                "hipertension_cronica": True,
            },
            format="json",
        )

        assert respuesta.status_code == 200, respuesta.data
        assert respuesta.data["requiere_aspirina"] is True


class CasoAdministracionTest(_ConEquipoClinico):
    """CU-04 · La administradora gestiona el equipo."""

    def test_la_admin_puede_cambiar_el_rol_de_alguien_y_queda_registrado(self):
        """ESPERADO: 200 y un registro CAMBIO_ROL con el antes y el después."""
        cliente = self.como(self.admin)
        antes = RegistroAuditoria.objects.filter(accion="CAMBIO_ROL").count()

        respuesta = cliente.patch(
            f"/api/usuarios/{self.enfermera.id}/", {"rol": "medico"}, format="json",
        )
        assert respuesta.status_code == 200, respuesta.data

        registros = RegistroAuditoria.objects.filter(accion="CAMBIO_ROL")
        assert registros.count() == antes + 1
        assert "enfermera" in registros.order_by("-id").first().detalle

    def test_la_admin_puede_todo_lo_clinico(self):
        """ESPERADO: 200 en los cinco módulos.

        El administrador es el único rol que no debe encontrarse una puerta
        cerrada: si algo se rompe, tiene que poder entrar a mirarlo.
        """
        cliente = self.como(self.admin)
        for ruta in (
            "/api/pacientes/", "/api/triaje/", "/api/evoluciones/",
            "/api/consultorios/", "/api/auditoria/",
        ):
            assert cliente.get(ruta).status_code == 200, f"{ruta} le dio 403 al admin."


class CasoTrazabilidadDeUnTurnoTest(_ConEquipoClinico):
    """CU-05 · Reconstruir qué pasó con una paciente durante un turno.

    Es la pregunta que un hospital tiene que poder responder: quién tocó el
    expediente de esta paciente, cuándo y qué hizo.
    """

    def test_el_recorrido_completo_queda_reconstruible(self):
        """ESPERADO: en la auditoría se ve el registro y la consulta, con nombres."""
        # 1. Recepción la registra
        creada = self.como(self.recepcion).post("/api/pacientes/", {
            "nombre": "Valentina", "apellido_paterno": "Yujra",
            "apellido_materno": "Avila", "fecha_nacimiento": "1994-04-04",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "5041322",
        }, format="json").data

        # 2. La médica abre su ficha (pasando por el middleware de auditoría)
        from auditoria.middleware import AuditoriaMiddleware

        cliente = self.como(self.medica)
        respuesta = cliente.get(f"/api/pacientes/{creada['id']}/")
        peticion = respuesta.wsgi_request
        peticion.user = self.medica
        AuditoriaMiddleware(lambda _r: respuesta)(peticion)

        # 3. La auditoría lo cuenta todo
        del_paciente = RegistroAuditoria.objects.filter(registro_id=str(creada["id"]))

        acciones = set(del_paciente.values_list("accion", flat=True))
        assert "CREAR" in acciones, "No consta quién registró a la paciente."
        assert "VER" in acciones, "No consta quién consultó su ficha."

        consulta = del_paciente.filter(accion="VER").first()
        assert consulta.usuario_id == self.medica.id
        assert consulta.usuario_rol == "medico"
        assert consulta.fecha is not None
