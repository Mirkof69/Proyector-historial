"""El recorrido de una cita en el día: llega, espera, consulta y se cierra.

Hallado al probar el flujo de negocio:
- Cita.clean() rechazaba TODA cita cuya hora ya pasó, también al cambiarle el
  estado: a las 10:05 no se podía marcar presente, pasar a consulta, completar
  ni marcar «No asistió» la cita de las 10:00 («No se pueden agendar citas en
  el pasado»), ni corregir sus observaciones.
- «Completar» solo aceptaba agendada/confirmada: la paciente que estaba en
  consulta (el paso anterior del flujo) no se podía cerrar.
- Se podía marcar «No asistió» una cita de la semana próxima, marcar presente
  una de otro día, cancelar una ya cerrada como «No asistió».
- El cruce de horarios ignoraba las citas en espera o en consulta, y la misma
  paciente podía tener dos citas a la misma hora con dos médicos.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from citas.models import Cita, Disponibilidad
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/citas/citas/"


class FlujoDeLaCitaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(
            email="admin.flujo@hospital.bo", nombre="A", apellido_paterno="Flujo",
            password="clave-segura-123", rol="administrador")
        cls.medico = Usuario.objects.create_user(
            email="medico.flujo@hospital.bo", nombre="M", apellido_paterno="Flujo",
            password="clave-segura-123", rol="medico")
        cls.otro_medico = Usuario.objects.create_user(
            email="medico2.flujo@hospital.bo", nombre="O", apellido_paterno="Flujo",
            password="clave-segura-123", rol="medico")
        for medico in (cls.medico, cls.otro_medico):
            for dia in range(7):
                Disponibilidad.objects.create(medico=medico, dia_semana=dia, hora_inicio=datetime.time(0, 0),
                                              hora_fin=datetime.time(23, 30), duracion_cita=30, activo=True)
        cls.paciente = Paciente.objects.create(
            nombre="Ana", apellido_paterno="Flujo", apellido_materno="Cita",
            fecha_nacimiento=datetime.date(1995, 1, 1), genero="femenino", ci="7712001")
        cls.hoy = timezone.localdate()
        cls.manana = cls.hoy + datetime.timedelta(days=1)

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.admin)

    def _cita(self, fecha, hora, estado="agendada", medico=None, paciente=None):
        # bulk_create: una cita de hoy a las 00:00 ya «pasó» y save() no la deja crear.
        return Cita.objects.bulk_create([Cita(
            paciente=paciente or self.paciente, medico=medico or self.medico, fecha_cita=fecha, hora_cita=hora,
            tipo_cita="control", estado=estado, motivo="Control prenatal")])[0]

    def _accion(self, cita, accion, **datos):
        return self.cliente.post(f"{URL}{cita.id}/{accion}/", datos, format="json")

    def test_la_cita_de_hoy_ya_pasada_recorre_todo_el_flujo(self):
        cita = self._cita(self.hoy, datetime.time(0, 0))
        for accion, estado in (("confirmar", "confirmada"), ("marcar-presente", "en_espera"),
                               ("pasar-consulta", "en_consulta"), ("completar", "completada")):
            r = self._accion(cita, accion)
            # ESPERADO: 200 en cada paso (antes: 400 «No se pueden agendar citas en el pasado»).
            self.assertEqual(r.status_code, 200, (accion, r.data))
            cita.refresh_from_db()
            self.assertEqual(cita.estado, estado)
        self.assertEqual(list(cita.historial.values_list("estado_nuevo", flat=True).order_by("id")),
                         ["confirmada", "en_espera", "en_consulta", "completada"])

    def test_no_asistio_de_una_cita_de_hoy_ya_pasada(self):
        cita = self._cita(self.hoy, datetime.time(0, 0))
        self.assertEqual(self._accion(cita, "no-asistio").status_code, 200)

    def test_se_corrigen_las_observaciones_de_una_cita_ya_pasada(self):
        cita = self._cita(self.hoy, datetime.time(0, 0), estado="completada")
        r = self.cliente.patch(f"{URL}{cita.id}/", {"observaciones": "Trajo ecografía"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)

    def test_no_asistio_y_presente_solo_el_dia_de_la_cita(self):
        cita = self._cita(self.manana, datetime.time(9, 0))
        r = self._accion(cita, "no-asistio")
        self.assertEqual(r.status_code, 400)
        self.assertIn("todavía no llegó", r.data["error"])
        r = self._accion(cita, "marcar-presente")
        self.assertEqual(r.status_code, 400)
        self.assertIn("solo el día de la cita", r.data["error"])
        cita.refresh_from_db()
        self.assertEqual(cita.estado, "agendada")

    def test_no_se_cancela_una_cita_ya_cerrada(self):
        for estado in ("completada", "cancelada", "no_asistio"):
            cita = self._cita(self.hoy, datetime.time(0, 0), estado=estado)
            self.assertEqual(self._accion(cita, "cancelar").status_code, 400, estado)

    def test_un_turno_con_la_paciente_en_consulta_no_se_vuelve_a_dar(self):
        self._cita(self.manana, datetime.time(9, 0), estado="en_espera")
        otra = Paciente.objects.create(nombre="Eva", apellido_paterno="Flujo", apellido_materno="Dos",
                                       fecha_nacimiento=datetime.date(1990, 2, 2), genero="femenino", ci="7712002")
        r = self.cliente.post(URL, {
            "paciente": otra.id, "medico": self.medico.id, "tipo_cita": "control",
            "fecha_cita": self.manana.isoformat(), "hora_cita": "09:00:00", "motivo": "Control"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("hora_cita", r.data)

    def test_la_paciente_no_puede_tener_dos_citas_a_la_misma_hora(self):
        self._cita(self.manana, datetime.time(9, 0))
        r = self.cliente.post(URL, {
            "paciente": self.paciente.id, "medico": self.otro_medico.id, "tipo_cita": "control",
            "fecha_cita": self.manana.isoformat(), "hora_cita": "09:00:00", "motivo": "Control"}, format="json")
        # ESPERADO: 400 (antes: 201, la paciente quedaba con dos médicos a la vez).
        self.assertEqual(r.status_code, 400)
        self.assertIn("paciente", r.data)

    def test_reprogramar_valida_fecha_y_turno(self):
        cita = self._cita(self.manana, datetime.time(9, 0))
        self._cita(self.manana, datetime.time(10, 0), paciente=Paciente.objects.create(
            nombre="Lia", apellido_paterno="Flujo", apellido_materno="Tres",
            fecha_nacimiento=datetime.date(1991, 3, 3), genero="femenino", ci="7712003"))
        ayer = (self.hoy - datetime.timedelta(days=1)).isoformat()
        self.assertEqual(self._accion(cita, "reprogramar", fecha_cita=ayer, hora_cita="09:00").status_code, 400)
        r = self._accion(cita, "reprogramar", fecha_cita=self.manana.isoformat(), hora_cita="10:00")
        self.assertEqual(r.status_code, 400)
        r = self._accion(cita, "reprogramar", fecha_cita=self.manana.isoformat(), hora_cita="11:00")
        self.assertEqual(r.status_code, 200, r.data)
        cita.refresh_from_db()
        self.assertEqual(cita.hora_cita, datetime.time(11, 0))


class LaCitaSigueALaPacienteTest(TestCase):
    """El triaje registra la llegada y el control de hoy cierra la cita."""

    @classmethod
    def setUpTestData(cls):
        cls.enfermera = Usuario.objects.create_user(
            email="enf.flujo@hospital.bo", nombre="E", apellido_paterno="Flujo",
            password="clave-segura-123", rol="enfermera")
        cls.medico = Usuario.objects.create_user(
            email="med.sigue@hospital.bo", nombre="M", apellido_paterno="Sigue",
            password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(
            nombre="Sol", apellido_paterno="Flujo", apellido_materno="Sigue",
            fecha_nacimiento=datetime.date(1996, 6, 6), genero="femenino", ci="7712010")

    def _cita(self, estado="confirmada"):
        return Cita.objects.bulk_create([Cita(
            paciente=self.paciente, medico=self.medico, fecha_cita=timezone.localdate(),
            hora_cita=datetime.time(0, 0), tipo_cita="control", estado=estado, motivo="Control")])[0]

    def test_el_triaje_vincula_la_cita_de_hoy_y_la_pone_en_espera(self):
        cita = self._cita()
        cliente = APIClient()
        cliente.force_authenticate(self.enfermera)
        r = cliente.post("/api/triaje/triajes/", {
            "paciente": self.paciente.id, "prioridad": "normal", "peso_kg": "62.0", "talla_cm": "158.0",
            "presion_sistolica": 110, "presion_diastolica": 70, "temperatura": "36.6",
            "frecuencia_cardiaca": 80, "frecuencia_respiratoria": 16, "motivo_visita": "Control prenatal"})
        self.assertEqual(r.status_code, 201, r.content)
        cita.refresh_from_db()
        # ESPERADO: en espera y con su triaje (antes: seguía «confirmada» sin triaje).
        self.assertEqual(cita.estado, "en_espera")
        self.assertEqual(cita.triaje.id, r.json()["id"])
        self.assertEqual(cita.historial.get().usuario, self.enfermera)

    def test_el_control_de_hoy_completa_la_cita(self):
        from citas.flujo import atendida_por_control
        from controles.models import ControlPrenatal
        from embarazos.models import Embarazo

        cita = self._cita(estado="en_consulta")
        embarazo = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1, estado="activo",
                                           fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=20))
        control = ControlPrenatal.objects.create(
            embarazo=embarazo, paciente=self.paciente, numero_control=3, fecha_control=timezone.localdate(),
            semanas_gestacion=20, peso_actual=60, talla=158, presion_arterial_sistolica=110,
            presion_arterial_diastolica=70)
        self.assertEqual(atendida_por_control(control, self.medico), cita)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, "completada")
        self.assertIn("control prenatal n.º 3", cita.historial.get().motivo_cambio)

    def test_un_control_cargado_con_fecha_pasada_no_toca_la_cita_de_hoy(self):
        from citas.flujo import atendida_por_control

        cita = self._cita()

        class Control:
            fecha_control = timezone.localdate() - datetime.timedelta(days=7)
            paciente_id = self.paciente.id
            numero_control = 1

        self.assertIsNone(atendida_por_control(Control, self.medico))
        cita.refresh_from_db()
        self.assertEqual(cita.estado, "confirmada")
