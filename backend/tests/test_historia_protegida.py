"""La historia clínica no se borra en cascada.

Fallos que previene:
- DELETE de un embarazo ejecutaba SQL directo que borraba sus controles y
  partos sin dejar rastro (y reventaba con un 500 si tenía ecografías).
- Borrar una paciente desde el admin arrastraba embarazos, controles,
  ecografías, laboratorio y vacunas.
"""
import datetime

from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from ecografias.models import Ecografia
from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

HOY = timezone.localdate()


class HistoriaProtegidaTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = Usuario.objects.create_user(email="adm.prot@test.bo", nombre="A", apellido_paterno="P",
                                                password="clave-segura-123", rol="administrador")
        cls.medico = Usuario.objects.create_user(email="med.prot@test.bo", nombre="M", apellido_paterno="P",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(nombre="Lia", apellido_paterno="Prot", apellido_materno="Hist",
                                               fecha_nacimiento=datetime.date(1991, 3, 1), genero="femenino",
                                               ci="7988001")

    def _embarazo(self, **extra):
        return Embarazo.objects.create(paciente=self.paciente, numero_gesta=1,
                                       fecha_ultima_menstruacion=HOY - datetime.timedelta(weeks=20), **extra)

    def _cliente(self, usuario):
        c = APIClient()
        c.force_authenticate(usuario)
        return c

    def test_un_embarazo_con_ecografia_no_se_borra(self):
        """ESPERADO: 409 y la ecografía sigue ahí."""
        e = self._embarazo()
        eco = Ecografia.objects.create(paciente=self.paciente, embarazo=e, fecha_ecografia=HOY,
                                       tipo_ecografia="segundo_trimestre", edad_gestacional_semanas=20,
                                       edad_gestacional_dias=0)
        r = self._cliente(self.admin).delete(f"/api/embarazos/{e.pk}/")
        self.assertEqual(r.status_code, 409, r.content[:300])
        self.assertTrue(Embarazo.objects.filter(pk=e.pk).exists())
        self.assertTrue(Ecografia.objects.filter(pk=eco.pk).exists())

    def test_un_embarazo_vacio_se_borra_y_queda_auditado(self):
        e = self._embarazo()
        r = self._cliente(self.admin).delete(f"/api/embarazos/{e.pk}/")
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertFalse(Embarazo.objects.filter(pk=e.pk).exists())
        self.assertTrue(RegistroAuditoria.objects.filter(accion="ELIMINAR_EMBARAZO", registro_id=str(e.pk)).exists())

    def test_el_medico_no_borra_embarazos(self):
        e = self._embarazo()
        r = self._cliente(self.medico).delete(f"/api/embarazos/{e.pk}/")
        self.assertEqual(r.status_code, 403)

    def test_borrar_una_paciente_con_embarazo_esta_protegido(self):
        self._embarazo()
        with self.assertRaises(ProtectedError):
            self.paciente.delete()
