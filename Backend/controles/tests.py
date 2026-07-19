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


class ControlesNoSeCruzanEntrePacientesTest(TestCase):
    """Filtrar controles por embarazo NO puede devolver los de otras pacientes.

    Regresión del bug más grave de la ronda de carga: el filterset declaraba
    solo "embarazo_id", así que `/controles/?embarazo=N` no era un filtro
    válido y django-filter lo IGNORABA EN SILENCIO — devolvía la lista
    completa. La Historia Clínica pedía los controles de un embarazo y
    recibía los de TODAS las pacientes, mostrándolos como propios.

    No hay error ni excepción: el único síntoma es que vienen de más. Por eso
    el test afirma sobre a QUIÉN pertenecen los controles devueltos, no solo
    sobre el status.
    """

    def setUp(self):
        from rest_framework.test import APIClient

        from usuarios.models import Usuario

        self.control_ana = _control(ci="000101", presion_arterial_sistolica=115)
        self.control_rosa = _control(ci="000102", presion_arterial_sistolica=120)
        # Segundo control de la misma paciente, para distinguir "filtra bien"
        # de "devuelve exactamente uno por casualidad".
        ControlPrenatal.objects.create(
            embarazo=self.control_ana.embarazo, paciente=self.control_ana.paciente,
            numero_control=2, fecha_control=date.today(), semanas_gestacion=28,
            peso_actual=Decimal("66.0"), talla=Decimal("160"),
            presion_arterial_sistolica=118, presion_arterial_diastolica=72,
        )
        usuario = Usuario.objects.create_superuser(
            email="ctrl@test.bo", nombre="C", apellido_paterno="T", password="x12345678",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=usuario)

    def test_filtrar_por_embarazo_solo_devuelve_los_de_esa_paciente(self):
        respuesta = self.client.get(
            "/api/controles/", {"embarazo": self.control_ana.embarazo.id},
        )
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.data["results"] if "results" in respuesta.data else respuesta.data
        self.assertEqual(len(datos), 2, "debe devolver los 2 controles de ESE embarazo")
        embarazos = {c["embarazo"] for c in datos}
        self.assertEqual(embarazos, {self.control_ana.embarazo.id})

    def test_filtrar_por_embarazo_no_incluye_controles_ajenos(self):
        """La afirmación que importa clínicamente: nada de otra paciente."""
        respuesta = self.client.get(
            "/api/controles/", {"embarazo": self.control_ana.embarazo.id},
        )
        datos = respuesta.data["results"] if "results" in respuesta.data else respuesta.data
        ids = {c["id"] for c in datos}
        self.assertNotIn(
            self.control_rosa.id, ids,
            "un control de OTRA paciente apareció en la historia clínica",
        )

    def test_filtrar_por_paciente_no_devuelve_la_lista_completa(self):
        respuesta = self.client.get(
            "/api/controles/", {"paciente": self.control_rosa.paciente.id},
        )
        datos = respuesta.data["results"] if "results" in respuesta.data else respuesta.data
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["id"], self.control_rosa.id)
