"""No todo hallazgo es «crítico»: cada alerta lleva su gravedad.

Medido el 29/10/2026 con 1.302 pacientes simuladas: toda PA ≥ 140/90, una
proteinuria de una cruz o un edema salían como «crítica»; 4.352 avisos
críticos por 7.033 controles, el 62 % de los embarazos reclasificado de alto
riesgo y un aviso «alto riesgo» repetido en cada guardado del embarazo.
"""
import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from controles.models import ControlPrenatal
from embarazos.models import Embarazo
from notificaciones.models import Notificacion
from pacientes.models import Paciente
from reportes.models import AlertaMedica
from usuarios.models import Usuario


class GravedadDeAlertasTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.grav@test.bo", nombre="Gina", apellido_paterno="Grav",
                                                 password="clave-segura-123", rol="medico")
        cls.n = 0

    def setUp(self):
        GravedadDeAlertasTest.n += 1
        self.paciente = Paciente.objects.create(nombre="Rosa", apellido_paterno="Grav", ci=f"77009{self.n:02d}",
                                                fecha_nacimiento=datetime.date(1992, 3, 1), genero="femenino")
        self.embarazo = Embarazo.objects.create(
            paciente=self.paciente, numero_gesta=1, numero_para=0, tipo_embarazo="simple", riesgo_embarazo="bajo",
            medico_responsable=self.medico,
            fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=30))

    def control(self, sist=110, diast=70, **extra):
        return ControlPrenatal.objects.create(
            embarazo=self.embarazo, paciente=self.paciente, medico=self.medico, numero_control=1,
            fecha_control=timezone.localdate(), semanas_gestacion=30, peso_actual=Decimal("65.00"),
            talla=Decimal("160.00"), presion_arterial_sistolica=sist, presion_arterial_diastolica=diast,
            frecuencia_cardiaca_fetal=140, **extra)

    def _prioridad_alerta(self, control, categoria):
        return AlertaMedica.objects.get(modulo_origen="controles", registro_origen_id=control.pk,
                                        datos_contexto__categoria=categoria).prioridad

    def test_hta_moderada_es_media_y_severa_critica(self):
        moderada = self.control(145, 92)
        self.assertEqual(self._prioridad_alerta(moderada, "presion_arterial"), "media")
        self.assertTrue(moderada.tiene_alertas_criticas())  # RF-06: sigue siendo alerta
        severa = self.control(165, 112)
        self.assertEqual(self._prioridad_alerta(severa, "presion_arterial"), "critica")

    def test_hta_con_proteinuria_es_alta(self):
        c = self.control(150, 95, proteinuria="positiva_1")
        self.assertEqual(self._prioridad_alerta(c, "presion_arterial"), "alta")
        self.assertEqual(self._prioridad_alerta(c, "proteinuria"), "alta")

    def test_proteinuria_aislada_no_reclasifica_ni_es_critica(self):
        c = self.control(proteinuria="positiva_1")
        self.assertEqual(self._prioridad_alerta(c, "proteinuria"), "media")
        self.embarazo.refresh_from_db()
        self.assertEqual(self.embarazo.riesgo_embarazo, "bajo")
        self.assertFalse(Notificacion.objects.filter(titulo="Alerta Crítica en Control Prenatal").exists())
        self.assertTrue(Notificacion.objects.filter(titulo="Hallazgo en Control Prenatal").exists())

    def test_hipertension_reclasifica_con_un_solo_aviso(self):
        self.control(150, 95)
        self.embarazo.refresh_from_db()
        self.assertEqual(self.embarazo.riesgo_embarazo, "alto")
        self.assertEqual(Notificacion.objects.filter(titulo="Embarazo Reclasificado como ALTO RIESGO").count(), 1)
        self.assertFalse(Notificacion.objects.filter(titulo__startswith="ALERTA: Embarazo de Alto Riesgo").exists())

    def test_aviso_de_alto_riesgo_solo_al_cambiar(self):
        Notificacion.objects.all().delete()
        self.embarazo.riesgo_embarazo = "alto"
        self.embarazo.save()
        self.embarazo.notas = "editada"
        self.embarazo.save()
        self.assertEqual(Notificacion.objects.filter(titulo__startswith="ALERTA: Embarazo de Alto Riesgo").count(), 1)

    def test_movimientos_ausentes_es_emergencia(self):
        c = self.control(movimientos_fetales="ausentes")
        self.assertEqual(self._prioridad_alerta(c, "movimientos"), "emergencia")
        self.assertTrue(Notificacion.objects.filter(titulo="Alerta Crítica en Control Prenatal").exists())
