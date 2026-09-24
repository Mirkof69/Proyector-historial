"""La antigüedad de la FUM solo limita a los embarazos en curso.

Fallo que previene: la regla «FUM de hace más de un año» se aplicaba a todo,
así que un embarazo terminado hace dos años no se podía editar (ni para
corregir una nota) y tampoco registrar un embarazo anterior como historia.
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

HOY = timezone.localdate()


class FumHistoricaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.fum@test.bo", nombre="M", apellido_paterno="F",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(nombre="Rosa", apellido_paterno="Hist", apellido_materno="Fum",
                                               fecha_nacimiento=datetime.date(1990, 5, 1), genero="femenino",
                                               ci="7977001")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)

    def _datos(self, **cambios):
        return {"paciente": self.paciente.pk, "numero_gesta": 1, "numero_para": 0, "numero_abortos": 0,
                "fecha_ultima_menstruacion": (HOY - datetime.timedelta(weeks=10)).isoformat(), **cambios}

    def test_registrar_un_embarazo_finalizado_de_hace_dos_anios(self):
        r = self.c.post("/api/embarazos/", self._datos(
            estado="finalizado", fecha_ultima_menstruacion=(HOY - datetime.timedelta(days=730)).isoformat()),
            format="json")
        self.assertEqual(r.status_code, 201, r.content[:300])

    def test_editar_las_notas_de_un_embarazo_antiguo(self):
        """ESPERADO: 200. Antes: 400 «no puede ser mayor a 1 año atrás»."""
        e = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1, estado="finalizado",
                                    fecha_ultima_menstruacion=HOY - datetime.timedelta(days=800))
        r = self.c.patch(f"/api/embarazos/{e.pk}/", {"notas": "corregido"}, format="json")
        self.assertEqual(r.status_code, 200, r.content[:300])

    def test_un_embarazo_activo_de_50_semanas_se_rechaza(self):
        r = self.c.post("/api/embarazos/", self._datos(
            fecha_ultima_menstruacion=(HOY - datetime.timedelta(weeks=50)).isoformat()), format="json")
        self.assertEqual(r.status_code, 400)

    def test_cerrar_un_embarazo_activo_olvidado(self):
        """Un activo que quedó sin cerrar se puede pasar a finalizado."""
        e = Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                    fecha_ultima_menstruacion=HOY - datetime.timedelta(weeks=60))
        r = self.c.patch(f"/api/embarazos/{e.pk}/", {"estado": "finalizado"}, format="json")
        self.assertEqual(r.status_code, 200, r.content[:300])

    def test_la_fum_futura_sigue_rechazada(self):
        r = self.c.post("/api/embarazos/", self._datos(
            fecha_ultima_menstruacion=(HOY + datetime.timedelta(days=2)).isoformat()), format="json")
        self.assertEqual(r.status_code, 400)
