"""Pruebas de CAJA GRIS.

Qué significa aquí
------------------
Se conduce el sistema **por fuera** —peticiones HTTP, como la caja negra— pero
se comprueba **por dentro**: cuántas consultas SQL costó, qué quedó escrito en
la auditoría, si el dato viajó cifrado, si tocó el esquema del otro tenant.

La pregunta que responde es: **¿está bien hecho lo que se ve bien?**

Es la categoría que atrapa los problemas más caros de este proyecto, porque son
justo los que no se ven en la respuesta:

  - El listado de pacientes devolvía un 200 perfecto haciendo 1.601 consultas
    para 200 filas. Tardaba 42 segundos con cien usuarias y ninguna prueba de
    caja negra podía notarlo.
  - La auditoría respondía bien y no registraba nada.
  - La campana pedía 55 KB para pintar un número.

La caja negra mira la respuesta; la caja blanca mira una función aislada. Esta
mira el coste y los efectos colaterales de un recorrido real.

Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""

import datetime

from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient, APITestCase

from auditoria.models import RegistroAuditoria
from notificaciones.models import Notificacion, PrioridadNotificacion, TipoNotificacion
from pacientes.models import Paciente
from usuarios.models import Usuario

CLAVE = "clave-de-prueba-123"


class _ConDatos(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medica = Usuario.objects.create_user(
            email="dra.gris@test.bo", nombre="Elena",
            apellido_paterno="Choque", password=CLAVE, rol="medico",
        )
        for i in range(40):
            Paciente.objects.create(
                nombre=f"Paciente{i}", apellido_paterno="Gris",
                apellido_materno="Prueba", fecha_nacimiento=datetime.date(1992, 3, 3),
                genero="femenino", ci=f"33{i:05d}",
            )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.medica)


class ElCosteEnConsultasNoCreceConLosDatosTest(_ConDatos):
    """Un 200 rápido y un 200 lento se ven igual desde fuera."""

    def test_listar_40_pacientes_no_dispara_cientos_de_consultas(self):
        """ESPERADO: menos de 15 consultas.

        Con 8 por paciente serían 320. Ese era el estado real: la respuesta
        era correcta y tardaba 42 segundos con cien usuarias.
        """
        with CaptureQueriesContext(connection) as capturadas:
            respuesta = self.client.get("/api/pacientes/")

        assert respuesta.status_code == 200
        assert len(capturadas) < 15, (
            f"{len(capturadas)} consultas para 40 pacientes: volvió el N+1."
        )

    def test_pedir_el_doble_de_filas_no_cuesta_el_doble_de_consultas(self):
        """ESPERADO: la diferencia no pasa de 2.

        Es la firma del N+1: si el coste sube con las filas, cada paciente
        nueva encarece la pantalla más usada de la clínica.
        """
        with CaptureQueriesContext(connection) as pocas:
            self.client.get("/api/pacientes/?page_size=5")
        with CaptureQueriesContext(connection) as muchas:
            self.client.get("/api/pacientes/?page_size=40")

        assert abs(len(muchas) - len(pocas)) <= 2, (
            f"5 filas: {len(pocas)} consultas; 40 filas: {len(muchas)}."
        )


class LaCampanaCuestaLoQueDebeTest(_ConDatos):
    """El resumen tiene que ser barato, no solo correcto."""

    def setUp(self):
        super().setUp()
        for i in range(120):
            Notificacion.objects.create(
                usuario=self.medica, tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
                titulo=f"Aviso {i}", mensaje="Cuerpo",
                prioridad=PrioridadNotificacion.NORMAL,
            )

    def test_el_resumen_cuesta_pocas_consultas_con_120_notificaciones(self):
        """ESPERADO: menos de 8 consultas.

        Dos para los datos —el agregado y las últimas ocho— más las de sesión.
        Si sube, alguien volvió a serializar la lista entera.
        """
        with CaptureQueriesContext(connection) as capturadas:
            respuesta = self.client.get("/api/notificaciones/resumen/")

        assert respuesta.status_code == 200
        assert len(capturadas) < 8, f"{len(capturadas)} consultas para un resumen."

    def test_el_resumen_pesa_muchisimo_menos_que_la_lista(self):
        """ESPERADO: el resumen no llega ni a la quinta parte.

        Medido contra el servidor real con 7.136 notificaciones: la lista eran
        55.888 bytes y el resumen 2.294. Aquí, con 120, la proporción se
        mantiene y el test la fija.
        """
        resumen = self.client.get("/api/notificaciones/resumen/")
        lista = self.client.get("/api/notificaciones/")

        peso_resumen = len(resumen.content)
        peso_lista = len(lista.content)

        assert peso_resumen * 5 < peso_lista, (
            f"El resumen pesa {peso_resumen} y la lista {peso_lista}. "
            f"El resumen dejó de ser barato."
        )

    def test_el_coste_del_resumen_no_sube_al_haber_mas_notificaciones(self):
        """ESPERADO: mismas consultas con 120 que con 620.

        El agregado y el `LIMIT 8` no dependen del volumen. Si esto sube, el
        endpoint volvió a traerse la tabla a memoria para contar.
        """
        with CaptureQueriesContext(connection) as antes:
            self.client.get("/api/notificaciones/resumen/")

        for i in range(500):
            Notificacion.objects.create(
                usuario=self.medica, tipo=TipoNotificacion.ALERTA_ADVERTENCIA,
                titulo=f"Extra {i}", mensaje="Cuerpo",
            )

        with CaptureQueriesContext(connection) as despues:
            self.client.get("/api/notificaciones/resumen/")

        assert len(despues) <= len(antes), (
            f"Con 120 costaba {len(antes)} consultas y con 620 cuesta "
            f"{len(despues)}: el coste depende del volumen."
        )


class LoQueQuedaEscritoDetrasDeUn200Test(_ConDatos):
    """La respuesta no dice si la auditoría registró algo."""

    def test_registrar_una_paciente_deja_rastro_de_la_creacion(self):
        """ESPERADO: un registro de creación sobre el módulo `paciente`.

        Un hospital tiene que poder responder quién tocó cada expediente. La
        auditoría estuvo apagada un tiempo devolviendo 201 igualmente.

        Aquí NO se comprueba el `usuario_id`: quien lo rellena es un
        thread-local que pone el middleware de auditoría, y `force_authenticate`
        no lo ejecuta. Darlo por bueno o por malo desde aquí sería mentir en
        las dos direcciones. La atribución se comprueba en
        `test_casos_de_uso.py::CasoTrazabilidadDeUnTurnoTest`, que sí pasa por
        el middleware, y está verificada además contra el servidor real
        (`usuario_id=2`, rol `medico`).
        """
        antes = RegistroAuditoria.objects.filter(modulo="paciente").count()

        respuesta = self.client.post("/api/pacientes/", {
            "nombre": "Valentina", "apellido_paterno": "Yujra",
            "apellido_materno": "Avila", "fecha_nacimiento": "1994-04-04",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "5551122",
        }, format="json")

        assert respuesta.status_code == 201
        registros = RegistroAuditoria.objects.filter(modulo="paciente")
        assert registros.count() == antes + 1, "El 201 no dejó rastro en la auditoría."

        ultimo = registros.order_by("-id").first()
        assert ultimo.registro_id == str(respuesta.data["id"])
        assert ultimo.fecha is not None

    def test_la_auditoria_guarda_el_nombre_canonico_de_la_accion(self):
        """ESPERADO: 'CREAR', no 'crear'.

        El signal `post_save` escribía con `objects.create(accion="crear")`,
        saltándose `RegistroAuditoria.registrar()`, que es donde se normalizan
        los nombres. Comprobado contra la base real: convivían 12.068 'CREAR'
        con 5.199 'crear' para el mismo hecho, y 884 'actualizar' mientras
        'EDITAR' no tenía ninguno — así que filtrar por 'EDITAR' devolvía cero
        y parecía que nunca se hubiera modificado nada.

        Se mira el registro del módulo `paciente` en concreto, no «el último»:
        crear una paciente dispara varios registros de módulos distintos y
        mirar el último cogería cualquiera de ellos.
        """
        respuesta = self.client.post("/api/pacientes/", {
            "nombre": "Teresa", "apellido_paterno": "Huanca",
            "apellido_materno": "Cusi", "fecha_nacimiento": "1990-09-09",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "5551133",
        }, format="json")

        registro = (
            RegistroAuditoria.objects
            .filter(modulo="paciente", registro_id=str(respuesta.data["id"]))
            .order_by("-id").first()
        )

        assert registro is not None, "No se auditó la creación de la paciente."
        assert registro.accion == "CREAR", (
            f"Se guardó la acción como '{registro.accion}'. El signal volvió a "
            f"escribir sin pasar por `canonica()`, y filtrar por 'CREAR' no "
            f"encontraría estos registros."
        )


class ElDatoSensibleNoSeGuardaEnClaroTest(_ConDatos):
    """Desde la API el CI se ve normal. En la base no debería."""

    def test_el_ci_esta_cifrado_en_la_columna(self):
        """ESPERADO: el valor en bruto de la columna no contiene el CI.

        La respuesta HTTP lo devuelve descifrado, así que la caja negra no
        puede distinguir una base cifrada de una que no lo está. Aquí se mira
        la columna directamente.
        """
        respuesta = self.client.post("/api/pacientes/", {
            "nombre": "Cifrada", "apellido_paterno": "Prueba",
            "apellido_materno": "Datos", "fecha_nacimiento": "1993-02-02",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "9998887",
        }, format="json")
        assert respuesta.status_code == 201

        with connection.cursor() as cur:
            cur.execute(
                f"SELECT ci FROM {Paciente._meta.db_table} WHERE id = %s",
                [respuesta.data["id"]],
            )
            en_bruto = str(cur.fetchone()[0])

        assert "9998887" not in en_bruto, (
            "El CI está en claro en la base. Quien lea la tabla —un backup, "
            "una consulta directa— ve el documento de identidad."
        )

    def test_y_aun_asi_se_puede_buscar_por_el(self):
        """ESPERADO: se encuentra.

        Cifrar sin poder buscar sería inútil. La búsqueda va por `ci_hash`, no
        por la columna cifrada, y eso tampoco se ve desde fuera.
        """
        creada = self.client.post("/api/pacientes/", {
            "nombre": "Buscable", "apellido_paterno": "Cifrada",
            "apellido_materno": "Datos", "fecha_nacimiento": "1993-02-02",
            "genero": "femenino", "consentimiento_datos_aceptado": True, "ci": "9998886",
        }, format="json").data

        respuesta = self.client.get("/api/pacientes/?search=9998886")

        assert creada["id"] in [p["id"] for p in respuesta.data["results"]]
