"""Tests para el módulo de Laboratorio"""

from decimal import Decimal

from django.test import TestCase

from pacientes.models import Paciente
from usuarios.models import Usuario

from .models import ExamenLaboratorio, ResultadoLaboratorio, TipoExamen, ValorReferencia


class LaboratorioTestCase(TestCase):
    """Laboratoriotestcase"""
    def setUp(self):
        """Setup"""
        self.medico = Usuario.objects.create_user(
            email="biologo@clinica.com",
            nombre="Biologo",
            apellido_paterno="Lab",
            password="password123",
            rol="medico",
        )
        self.paciente = Paciente.objects.create(
            nombre="Paciente",
            apellido_paterno="Lab",
            fecha_nacimiento="1990-01-01",
            ci="998877",
        )
        self.tipo_examen = TipoExamen.objects.create(
            nombre="Hemograma",
            codigo="HEM001",
            categoria="hematologia",
            precio=Decimal("50.00"),
        )
        self.valor_ref = ValorReferencia.objects.create(
            tipo_examen=self.tipo_examen,
            parametro="Hemoglobina",
            unidad="g/dL",
            valor_minimo=Decimal("12.0"),
            valor_maximo=Decimal("16.0"),
            es_critico_bajo=Decimal("7.0"),
        )

    def test_crear_examen(self):
        """Test crear examen"""
        examen = ExamenLaboratorio.objects.create(
            paciente=self.paciente,
            tipo_examen=self.tipo_examen,
            medico_solicitante=self.medico,
            prioridad="normal",
        )
        self.assertIsNotNone(examen.id)
        self.assertEqual(examen.estado, "solicitado")
        self.assertEqual(examen.get_costo_total_estimado(), Decimal("50.00"))

    def test_examen_urgente_costo(self):
        """Test recargo por urgencia"""
        examen = ExamenLaboratorio.objects.create(
            paciente=self.paciente, tipo_examen=self.tipo_examen, prioridad="urgente",
        )
        # 50 * 1.5 = 75
        self.assertEqual(examen.get_costo_total_estimado(), Decimal("75.00"))

    def test_resultado_automatico_normal(self):
        """Test evaluación automática de resultado normal"""
        examen = ExamenLaboratorio.objects.create(
            paciente=self.paciente, tipo_examen=self.tipo_examen,
        )
        resultado = ResultadoLaboratorio.objects.create(
            examen=examen,
            valor_referencia=self.valor_ref,
            valor_numerico=Decimal("14.0"),  # Normal
        )
        resultado.calcular_estado_automatico()
        self.assertTrue(resultado.es_normal)
        self.assertFalse(resultado.es_critico)

    def test_resultado_automatico_critico(self):
        """Test evaluación automática de resultado crítico"""
        examen = ExamenLaboratorio.objects.create(
            paciente=self.paciente, tipo_examen=self.tipo_examen,
        )
        resultado = ResultadoLaboratorio.objects.create(
            examen=examen,
            valor_referencia=self.valor_ref,
            valor_numerico=Decimal("6.0"),  # Crítico bajo (< 7.0)
        )
        resultado.calcular_estado_automatico()
        self.assertFalse(resultado.es_normal)
        self.assertTrue(resultado.es_critico)
        self.assertIn("CRÍTICO", resultado.get_interpretacion_medica())
