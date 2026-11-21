"""Horarios de un médico que atiende mañana y tarde.

Con dos Disponibilidad el mismo día, la API tomaba solo la primera
(`.first()`): los turnos de la tarde nunca se ofrecían en «Nueva cita» y sus
citas no salían en la agenda del médico (hallado por la prueba E2E de módulos).
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from citas.models import Disponibilidad
from usuarios.models import Usuario


class BloquesDelDiaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="medico.bloques@test.bo", nombre="N", apellido_paterno="A",
            password="clave-segura-123", rol="medico")
        # El próximo lunes, para no depender del día en que corre la prueba.
        hoy = timezone.localdate()
        cls.lunes = hoy + datetime.timedelta(days=(7 - hoy.weekday()) % 7 or 7)
        for inicio, fin in ((8, 12), (14, 18)):
            Disponibilidad.objects.create(
                medico=cls.medico, dia_semana=0, hora_inicio=datetime.time(inicio),
                hora_fin=datetime.time(fin), duracion_cita=30, activo=True)

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def test_ofrece_los_turnos_de_la_manana_y_de_la_tarde(self):
        r = self.cliente.get("/api/citas/disponibilidades/horarios-disponibles/",
                             {"medico_id": self.medico.id, "fecha": self.lunes.isoformat()})
        self.assertEqual(r.status_code, 200)
        horas = [str(h["hora"])[:5] for h in r.data["horarios"]]
        # ESPERADO: 8 turnos de mañana + 8 de tarde (antes: solo los 8 de la mañana).
        self.assertEqual(len(horas), 16)
        self.assertIn("14:00", horas)
        self.assertEqual(horas, sorted(horas))

    def test_la_agenda_del_medico_incluye_la_tarde(self):
        r = self.cliente.get("/api/citas/citas/agenda-medico/",
                             {"medico_id": self.medico.id, "fecha": self.lunes.isoformat()})
        self.assertEqual(r.status_code, 200)
        self.assertIn("17:30", [str(h["hora"])[:5] for h in r.data["horarios"]])

    def test_agendar_y_editar_una_cita_por_la_api(self):
        """Toda alta o edición de cita respondía 500: la vista pasaba
        created_by/updated_by, que son de Disponibilidad y no de Cita."""
        from citas.models import Cita
        from pacientes.models import Paciente
        paciente = Paciente.objects.create(
            nombre="Rosa", apellido_paterno="Test", apellido_materno="Cita",
            fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7811088")
        r = self.cliente.post("/api/citas/citas/", {
            "paciente": paciente.id, "medico": self.medico.id, "tipo_cita": "control",
            "fecha_cita": self.lunes.isoformat(), "hora_cita": "14:00:00", "duracion": 30,
            "motivo": "Control prenatal", "estado": "agendada",
        }, format="json")
        # ESPERADO: 201 y la cita a nombre de quien la agendó (antes: 500).
        self.assertEqual(r.status_code, 201, r.data)
        cita = Cita.objects.get(paciente=paciente)
        self.assertEqual(cita.creado_por, self.medico)
        r = self.cliente.patch(f"/api/citas/citas/{cita.id}/", {"observaciones": "Traer ecografía"}, format="json")
        self.assertEqual(r.status_code, 200, r.data)
        cita.refresh_from_db()
        self.assertEqual(cita.observaciones, "Traer ecografía")
        self.assertEqual(cita.modificado_por, self.medico)
