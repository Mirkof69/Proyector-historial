"""Tests para el módulo de Controles Prenatales.

Verifican la lógica clínica de detección de alertas (hipertensión, FCF anormal),
que es crítica para la seguridad del paciente.
"""
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from embarazos.models import Embarazo
from pacientes.models import Paciente

from .models import ControlPrenatal


def _control(**kwargs):
    paciente = Paciente.objects.create(
        id_clinico=f"PAC-C-{kwargs.get('ci','1')}", nombre="Rosa",
        apellido_paterno="Díaz", fecha_nacimiento=date(1992, 1, 1),
        genero="femenino", ci=f"7{kwargs.get('ci','000001')}",
    )
    embarazo = Embarazo.objects.create(
        paciente=paciente, numero_gesta=1,
        fecha_ultima_menstruacion=date.today() - timedelta(weeks=24),
    )
    defaults = {
        "embarazo": embarazo, "paciente": paciente, "numero_control": 1,
        "fecha_control": date.today(), "semanas_gestacion": 24,
        "peso_actual": Decimal("65.0"), "talla": Decimal("160"),
        "presion_arterial_sistolica": 110, "presion_arterial_diastolica": 70,
    }
    defaults.update({k: v for k, v in kwargs.items() if k != "ci"})
    return ControlPrenatal.objects.create(**defaults)


class ControlPrenatalClinicaTest(TestCase):

    def test_presion_normal_sin_hipertension(self):
        c = _control(presion_arterial_sistolica=110, presion_arterial_diastolica=70)
        self.assertFalse(c.tiene_hipertension())

    def test_hipertension_sistolica(self):
        c = _control(ci="000002", presion_arterial_sistolica=145, presion_arterial_diastolica=85)
        self.assertTrue(c.tiene_hipertension())

    def test_hipertension_diastolica(self):
        c = _control(ci="000003", presion_arterial_sistolica=130, presion_arterial_diastolica=95)
        self.assertTrue(c.tiene_hipertension())

    def test_prehipertension(self):
        c = _control(ci="000004", presion_arterial_sistolica=125, presion_arterial_diastolica=78)
        self.assertTrue(c.tiene_prehipertension())
        self.assertFalse(c.tiene_hipertension())

    def test_fcf_normal(self):
        c = _control(ci="000005", frecuencia_cardiaca_fetal=140)
        self.assertFalse(c.fcf_es_anormal())

    def test_fcf_bradicardia(self):
        c = _control(ci="000006", frecuencia_cardiaca_fetal=100)
        self.assertTrue(c.fcf_es_anormal())

    def test_fcf_taquicardia(self):
        c = _control(ci="000007", frecuencia_cardiaca_fetal=170)
        self.assertTrue(c.fcf_es_anormal())

    def test_alerta_critica_con_hipertension(self):
        c = _control(ci="000008", presion_arterial_sistolica=150, presion_arterial_diastolica=100)
        self.assertTrue(c.tiene_alertas_criticas())

    def test_sin_alertas_criticas_en_control_normal(self):
        c = _control(ci="000009", presion_arterial_sistolica=110,
                     presion_arterial_diastolica=70, frecuencia_cardiaca_fetal=140)
        self.assertFalse(c.tiene_alertas_criticas())
