"""Los hallazgos clínicos críticos llegan a «Alertas Médicas».

Antes la tabla AlertaMedica solo se llenaba a mano y estaba vacía aunque miles
de controles tenían alertas críticas calculadas (reportes/alertas_clinicas.py).
"""
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from pacientes.models import Paciente
from reportes.alertas_clinicas import desde_control
from reportes.models import AlertaMedica
from usuarios.models import Usuario


class AlertasDesdeControlesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.alertas@test.bo", nombre="Ana", apellido_paterno="Alerta",
                                                 password="clave-segura-123", rol="medico")
        cls.paciente = Paciente.objects.create(nombre="Rosa", apellido_paterno="Alerta", ci="7700991",
                                               fecha_nacimiento=datetime.date(1992, 3, 1), genero="femenino")
        cls.embarazo = Embarazo.objects.create(paciente=cls.paciente, numero_gesta=1, numero_para=0, tipo_embarazo="simple",
                                               fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=12))

    def control(self, sistolica, diastolica, numero=1):
        return ControlPrenatal.objects.create(
            embarazo=self.embarazo, paciente=self.paciente, medico=self.medico, numero_control=numero,
            fecha_control=timezone.localdate(), semanas_gestacion=12, peso_actual=Decimal("65.00"),
            talla=Decimal("160.00"), presion_arterial_sistolica=sistolica, presion_arterial_diastolica=diastolica)

    def test_control_con_hipertension_crea_alerta_activa(self):
        c = self.control(160, 110)
        alerta = AlertaMedica.objects.get(modulo_origen="controles", registro_origen_id=c.pk,
                                          datos_contexto__categoria="presion_arterial")
        self.assertEqual((alerta.estado, alerta.prioridad, alerta.paciente_id), ("activa", "critica", self.paciente.pk))
        self.assertIn("160/110", alerta.valor_actual)

    def test_control_normal_no_crea_alertas(self):
        c = self.control(110, 70)
        self.assertFalse(AlertaMedica.objects.filter(registro_origen_id=c.pk, modulo_origen="controles").exists())

    def test_guardar_otra_vez_no_duplica(self):
        c = self.control(160, 110)
        c.save()
        self.assertEqual(AlertaMedica.objects.filter(modulo_origen="controles", registro_origen_id=c.pk).count(),
                         AlertaMedica.objects.filter(modulo_origen="controles", registro_origen_id=c.pk)
                         .values("datos_contexto__categoria").distinct().count())

    def test_recalcular_es_idempotente(self):
        # El comando generar_alertas_clinicas recorre los controles con desde_control().
        c = self.control(160, 110)
        antes = AlertaMedica.objects.count()
        self.assertEqual(desde_control(c), 0)
        self.assertEqual(AlertaMedica.objects.count(), antes)
