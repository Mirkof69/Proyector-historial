"""Datos imposibles que el flujo aceptaba (sondeo de casos inválidos, 28/10).

- Un control prenatal de hace 200 días en un embarazo de 20 semanas (anterior
  a la FUM), o con el embarazo de otra paciente.
- Un triaje con presión 60/120 (sistólica menor que diastólica).
- Una vacuna «aplicada» pasado mañana.
- Una cita a las 09:17, fuera de los turnos de la agenda.
- El parto rechazaba «39» con el mensaje «Use formato: 39 o 39+2».
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from citas.models import Disponibilidad
from embarazos.models import Embarazo
from pacientes.models import Paciente
from partos.serializers import PartoSerializer
from usuarios.models import Usuario
from vacunas.models import TipoVacuna


class ValidacionesDelFlujoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="medico.valida@hospital.bo", nombre="V", apellido_paterno="Valida",
            password="clave-segura-123", rol="medico")
        cls.hoy = timezone.localdate()
        cls.paciente = Paciente.objects.create(
            nombre="Iris", apellido_paterno="Valida", apellido_materno="Flujo",
            fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7713001")
        cls.otra = Paciente.objects.create(
            nombre="Noa", apellido_paterno="Valida", apellido_materno="Otra",
            fecha_nacimiento=datetime.date(1992, 2, 2), genero="femenino", ci="7713002")
        cls.embarazo = Embarazo.objects.create(
            paciente=cls.paciente, numero_gesta=1, estado="activo",
            fecha_ultima_menstruacion=cls.hoy - datetime.timedelta(weeks=20))

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def _control(self, **cambios):
        datos = {"embarazo": self.embarazo.id, "paciente": self.paciente.id, "numero_control": 1,
                 "fecha_control": self.hoy.isoformat(), "semanas_gestacion": 20, "peso_actual": "62.0",
                 "talla": "158", "presion_arterial_sistolica": 110, "presion_arterial_diastolica": 70, **cambios}
        return self.cliente.post("/api/controles/", datos, format="json")

    def test_control_anterior_a_la_fum(self):
        r = self._control(fecha_control=(self.hoy - datetime.timedelta(days=200)).isoformat())
        self.assertEqual(r.status_code, 400)
        self.assertIn("anterior a la FUM", str(r.data["fecha_control"]))

    def test_control_con_el_embarazo_de_otra_paciente(self):
        r = self._control(paciente=self.otra.id)
        self.assertEqual(r.status_code, 400)
        self.assertIn("paciente", r.data)

    def test_control_valido(self):
        self.assertEqual(self._control().status_code, 201)

    def test_triaje_con_la_presion_invertida(self):
        r = self.cliente.post("/api/triaje/triajes/", {
            "paciente": self.paciente.id, "prioridad": "normal", "peso_kg": "62.0", "talla_cm": "158.0",
            "presion_sistolica": 60, "presion_diastolica": 120, "temperatura": "36.6",
            "frecuencia_cardiaca": 80, "frecuencia_respiratoria": 16, "motivo_visita": "Control"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("presion_sistolica", r.data)

    def test_vacuna_aplicada_en_el_futuro(self):
        tipo = TipoVacuna.objects.create(nombre="dT", dosis_requeridas=1)
        r = self.cliente.post("/api/vacunas/registros/", {
            "paciente": self.paciente.id, "tipo_vacuna": tipo.id, "numero_dosis": 1, "lote": "L1",
            "laboratorio": "Lab", "via_administracion": "intramuscular", "sitio_aplicacion": "Deltoides",
            "fecha_aplicacion": (timezone.now() + datetime.timedelta(days=2)).isoformat()}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("fecha_aplicacion", r.data)

    def test_cita_fuera_de_los_turnos_de_la_agenda(self):
        manana = self.hoy + datetime.timedelta(days=1)
        Disponibilidad.objects.create(medico=self.medico, dia_semana=manana.weekday(), hora_inicio=datetime.time(8),
                                      hora_fin=datetime.time(12), duracion_cita=30, activo=True)
        datos = {"paciente": self.paciente.id, "medico": self.medico.id, "tipo_cita": "control",
                 "fecha_cita": manana.isoformat(), "motivo": "Control"}
        r = self.cliente.post("/api/citas/citas/", {**datos, "hora_cita": "09:17:00"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("turno de la agenda", str(r.data["hora_cita"]))
        r = self.cliente.post("/api/citas/citas/", {**datos, "hora_cita": "09:30:00"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)

    def test_edad_gestacional_del_parto_con_y_sin_dias(self):
        s = PartoSerializer()
        self.assertEqual(s.validate_edad_gestacional_parto("39"), "39")
        self.assertEqual(s.validate_edad_gestacional_parto("39+2"), "39+2")
        for invalida in ("39+7", "abc", "39+"):
            with self.subTest(invalida):
                with self.assertRaises(Exception):
                    s.validate_edad_gestacional_parto(invalida)


class RecepcionSinVacunasTest(TestCase):
    """Recepción no ve datos clínicos: las vacunas solo pedían estar conectado."""

    def test_recepcion_no_lee_ni_registra_vacunas(self):
        recepcion = Usuario.objects.create_user(
            email="recep.vacunas@hospital.bo", nombre="R", apellido_paterno="Vac",
            password="clave-segura-123", rol="recepcion")
        cliente = APIClient()
        cliente.force_authenticate(recepcion)
        self.assertEqual(cliente.get("/api/vacunas/registros/").status_code, 403)
        self.assertEqual(cliente.post("/api/vacunas/registros/", {}, format="json").status_code, 403)


class EstadosDelExamenTest(TestCase):
    """Un examen no se completa vacío, no se reabre y no acepta parámetros ajenos."""

    @classmethod
    def setUpTestData(cls):
        from laboratorio.models import ExamenLaboratorio, TipoExamen, ValorReferencia

        cls.medico = Usuario.objects.create_user(
            email="med.examen@hospital.bo", nombre="E", apellido_paterno="Examen",
            password="clave-segura-123", rol="medico")
        cls.hemograma = TipoExamen.objects.create(nombre="Hemograma F", codigo="HEMF1", categoria="hematologia",
                                                  tiempo_resultado=1)
        glucosa = TipoExamen.objects.create(nombre="Glucosa F", codigo="GLUF1", categoria="bioquimica",
                                            tiempo_resultado=1)
        cls.hb = ValorReferencia.objects.create(tipo_examen=cls.hemograma, parametro="Hemoglobina", valor_minimo=11,
                                                valor_maximo=16, unidad="g/dL")
        cls.glu = ValorReferencia.objects.create(tipo_examen=glucosa, parametro="Glucosa", valor_minimo=70,
                                                 valor_maximo=100, unidad="mg/dL")
        paciente = Paciente.objects.create(nombre="Ema", apellido_paterno="Examen", apellido_materno="F",
                                           fecha_nacimiento=datetime.date(1991, 1, 1), genero="femenino", ci="7713050")
        cls.examen = ExamenLaboratorio.objects.create(paciente=paciente, tipo_examen=cls.hemograma,
                                                      fecha_solicitud=timezone.now())
        cls.cancelado = ExamenLaboratorio.objects.create(paciente=paciente, tipo_examen=cls.hemograma,
                                                         fecha_solicitud=timezone.now(), estado="cancelado")

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def _url(self, examen, accion):
        return f"/api/laboratorios/examenes/{examen.id}/{accion}/"

    def test_no_se_completa_sin_resultados(self):
        r = self.cliente.post(self._url(self.examen, "cambiar-estado"), {"estado": "completado"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("al menos un resultado", r.data["error"])

    def test_un_examen_cancelado_no_se_reabre_ni_recibe_resultados(self):
        r = self.cliente.post(self._url(self.cancelado, "cambiar-estado"), {"estado": "completado"}, format="json")
        self.assertEqual(r.status_code, 400)
        r = self.cliente.post(self._url(self.cancelado, "crear-resultado-multiple"),
                              {"resultados": [{"valor_referencia": self.hb.id, "valor_numerico": 12}]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_parametro_de_otro_examen_o_sin_valor(self):
        url = self._url(self.examen, "crear-resultado-multiple")
        r = self.cliente.post(url, {"resultados": [{"valor_referencia": self.glu.id, "valor_numerico": 90}]},
                              format="json")
        # ESPERADO: 400 (antes: 201 y una glucosa dentro del hemograma).
        self.assertEqual(r.status_code, 400)
        self.assertIn("no es un parámetro", r.data["error"])
        r = self.cliente.post(url, {"resultados": [{"valor_referencia": self.hb.id}]}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_resultados_validos_completan_el_examen(self):
        r = self.cliente.post(self._url(self.examen, "crear-resultado-multiple"),
                              {"resultados": [{"valor_referencia": self.hb.id, "valor_numerico": 12.5}],
                               "completar_examen": True}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        self.examen.refresh_from_db()
        self.assertEqual(self.examen.estado, "completado")


class EpicrisisDeUnPartoTerminadoTest(TestCase):
    """El alta (epicrisis) se aceptaba con el parto «en curso»: el embarazo
    seguía activo para siempre."""

    def test_solo_con_el_parto_finalizado(self):
        from partos.models import Parto

        medico = Usuario.objects.create_user(email="med.epi@hospital.bo", nombre="E", apellido_paterno="Epi",
                                             password="clave-segura-123", rol="medico")
        paciente = Paciente.objects.create(nombre="Ada", apellido_paterno="Epi", apellido_materno="F",
                                           fecha_nacimiento=datetime.date(1990, 9, 9), genero="femenino", ci="7713090")
        parto = Parto.objects.create(paciente=paciente, fecha_parto=timezone.now() - datetime.timedelta(hours=6),
                                     edad_gestacional_parto="39", tipo_parto="vaginal_espontaneo")
        cliente = APIClient()
        cliente.force_authenticate(medico)
        datos = {"parto": parto.id, "fecha_egreso": timezone.now().isoformat(),
                 "diagnostico_ingreso": "Trabajo de parto", "diagnostico_egreso": "Puerperio normal",
                 "resumen_clinico": "Parto eutócico."}
        r = cliente.post("/api/partos/epicrisis/", datos, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("parto", r.data)
        Parto.objects.filter(pk=parto.pk).update(parto_finalizado=True)
        r = cliente.post("/api/partos/epicrisis/", datos, format="json")
        self.assertEqual(r.status_code, 201, r.data)


class AvisosDeRecepcionTest(TestCase):
    """A recepción le llegaban los factores de riesgo de la paciente que
    registraba: un dato clínico que no puede ver."""

    def test_recepcion_recibe_el_registro_pero_no_el_riesgo(self):
        from notificaciones.models import Notificacion

        Usuario.objects.create_user(email="admin.avisos@hospital.bo", nombre="A", apellido_paterno="Av",
                                    password="clave-segura-123", rol="administrador")
        recepcion = Usuario.objects.create_user(email="recep.avisos@hospital.bo", nombre="R", apellido_paterno="Av",
                                                password="clave-segura-123", rol="recepcion")
        cliente = APIClient()
        cliente.force_authenticate(recepcion)
        r = cliente.post("/api/pacientes/", {
            "nombre": "Olga", "apellido_paterno": "Avisos", "apellido_materno": "R", "ci": "7713200",
            "fecha_nacimiento": "1984-01-01", "genero": "femenino", "consentimiento_datos_aceptado": True},
            format="json")
        self.assertEqual(r.status_code, 201, r.data)
        suyas = Notificacion.objects.filter(usuario=recepcion)
        self.assertEqual(list(suyas.values_list("titulo", "url")),
                         [("Paciente Registrada", f"/dashboard/pacientes/{r.data['id']}")])
        # 42 años: el aviso de riesgo existe, pero no para recepción.
        self.assertTrue(Notificacion.objects.filter(titulo="Factores de Riesgo Detectados").exists())

    def test_la_campana_lleva_a_recepcion_a_la_ficha_y_no_a_la_historia(self):
        """La campana usa /no_leidas/ y /resumen/: armaban el enlace sin saber
        quién miraba y a recepción le daban la historia clínica (sin permiso)."""
        recepcion = Usuario.objects.create_user(email="recep.campana@hospital.bo", nombre="R", apellido_paterno="Ca",
                                                password="clave-segura-123", rol="recepcion")
        cliente = APIClient()
        cliente.force_authenticate(recepcion)
        r = cliente.post("/api/pacientes/", {
            "nombre": "Ines", "apellido_paterno": "Campana", "apellido_materno": "R", "ci": "7713300",
            "fecha_nacimiento": "1996-01-01", "genero": "femenino", "consentimiento_datos_aceptado": True},
            format="json")
        self.assertEqual(r.status_code, 201, r.data)
        esperado = f"/dashboard/pacientes/{r.data['id']}"
        for ruta in ("/api/notificaciones/no_leidas/", "/api/notificaciones/resumen/"):
            datos = cliente.get(ruta).json()
            lista = datos.get("ultimas") or datos.get("results") or datos.get("notificaciones") or datos
            if isinstance(lista, dict):
                lista = next((v for v in lista.values() if isinstance(v, list)), [])
            self.assertIn(esperado, [n["enlace"] for n in lista], ruta)
