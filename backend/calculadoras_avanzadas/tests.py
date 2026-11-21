"""Tests para Calculadoras Avanzadas.

Verifican que las calculadoras clínicas (que computan en save()) produzcan
resultados correctos para entradas conocidas — no solo que no crasheen.
"""
from datetime import date

from django.test import TestCase
from django.utils import timezone

from pacientes.models import Paciente

from .models import ScoreBishop


def _paciente():
    return Paciente.objects.create(
        id_clinico="PAC-CA-1", nombre="Ana", apellido_paterno="Ruiz",
        fecha_nacimiento=date(1990, 3, 15), genero="femenino", ci="9000001",
    )


class ScoreBishopTest(TestCase):
    """El Score de Bishop se calcula automáticamente en save()."""

    def setUp(self):
        self.paciente = _paciente()

    def test_cervix_inmaduro_da_score_bajo(self):
        """Todas las condiciones mínimas → score 0 → cérvix inmaduro."""
        s = ScoreBishop.objects.create(
            paciente=self.paciente, fecha_evaluacion=timezone.now(),
            edad_gestacional_semanas=39, dilatacion_cervical=0,
            borramiento_cervical=20, consistencia_cervical="dura",
            posicion_cervical="posterior", estacion_fetal="-3",
        )
        self.assertEqual(s.score_total, 0)
        self.assertIn("inmaduro", s.interpretacion.lower())

    def test_cervix_maduro_da_score_alto(self):
        """Condiciones favorables → score alto → cérvix maduro (inducción favorable)."""
        s = ScoreBishop.objects.create(
            paciente=self.paciente, fecha_evaluacion=timezone.now(),
            edad_gestacional_semanas=40, dilatacion_cervical=5,   # +3
            borramiento_cervical=90,                               # +3
            consistencia_cervical="blanda",                        # +2
            posicion_cervical="anterior",                          # +2
            estacion_fetal="0",                                    # +3
        )
        self.assertEqual(s.score_total, 13)
        self.assertIn("maduro", s.interpretacion.lower())
        self.assertGreaterEqual(s.probabilidad_parto_espontaneo, 80)

    def test_score_intermedio(self):
        """Score entre 6 y 8 → moderadamente maduro."""
        s = ScoreBishop.objects.create(
            paciente=self.paciente, fecha_evaluacion=timezone.now(),
            edad_gestacional_semanas=39, dilatacion_cervical=2,    # +1
            borramiento_cervical=60,                               # +2
            consistencia_cervical="media",                         # +1
            posicion_cervical="media",                             # +1
            estacion_fetal="-2",                                   # +1
        )
        self.assertEqual(s.score_total, 6)
        self.assertIn("moderadamente", s.interpretacion.lower())

    def test_recomendacion_sin_datos(self):
        s = ScoreBishop(paciente=self.paciente, fecha_evaluacion=timezone.now())
        self.assertIn("Complete", s.get_recomendacion_clinica())
