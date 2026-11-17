"""El aviso «RESULTADO CRÍTICO» se calcula con el parámetro del resultado.

Regresión (29/10/2026): obtener_rango_referencia tomaba el PRIMER parámetro
del tipo de examen. En un hemograma, una hemoglobina de 11,9 g/dL se medía
contra el rango de los basófilos (0-1 %) y le llegaba al médico como
«Requiere atención inmediata». También ignoraba los límites críticos
configurados en el valor de referencia.
"""
import datetime

from django.test import TestCase
from django.utils import timezone

from laboratorio.models import ExamenLaboratorio, ResultadoLaboratorio, TipoExamen, ValorReferencia
from notificaciones.models import Notificacion, TipoNotificacion
from pacientes.models import Paciente
from usuarios.models import Usuario


class AvisoDeResultadoCriticoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(
            email="med.critico@hospital.bo", nombre="C", apellido_paterno="Critico",
            password="clave-segura-123", rol="medico")
        hemograma = TipoExamen.objects.create(nombre="Hemograma C", codigo="HEMC1", categoria="hematologia",
                                              tiempo_resultado=1)
        # «Basófilos» va primero por orden alfabético: es el que se usaba para todo.
        ValorReferencia.objects.create(tipo_examen=hemograma, parametro="Basófilos", valor_minimo=0,
                                       valor_maximo=1, unidad="%")
        cls.hb = ValorReferencia.objects.create(tipo_examen=hemograma, parametro="Hemoglobina", valor_minimo=12,
                                                valor_maximo=16, es_critico_bajo=7, es_critico_alto=18, unidad="g/dL")
        cls.leu = ValorReferencia.objects.create(tipo_examen=hemograma, parametro="Leucocitos", valor_minimo=4,
                                                 valor_maximo=10, unidad="10³/µL")
        paciente = Paciente.objects.create(nombre="Rita", apellido_paterno="Critico", apellido_materno="Lab",
                                           fecha_nacimiento=datetime.date(1993, 3, 3), genero="femenino",
                                           ci="7713090")
        cls.examen = ExamenLaboratorio.objects.create(paciente=paciente, tipo_examen=hemograma,
                                                      medico_solicitante=cls.medico, fecha_solicitud=timezone.now())

    def _avisos(self):
        return Notificacion.objects.filter(tipo=TipoNotificacion.EXAMEN_CRITICO).count()

    def _resultado(self, referencia, valor):
        return ResultadoLaboratorio.objects.create(examen=self.examen, valor_referencia=referencia,
                                                   valor_numerico=valor)

    def test_hemoglobina_algo_baja_no_es_critica(self):
        """ESPERADO: 11,9 g/dL queda fuera de rango pero sin aviso crítico."""
        r = self._resultado(self.hb, 11.9)
        self.assertFalse(r.es_critico)
        self.assertEqual(self._avisos(), 0)

    def test_hemoglobina_bajo_el_limite_critico_avisa(self):
        """ESPERADO: 6,5 g/dL < 7 (límite crítico configurado) → aviso."""
        self._resultado(self.hb, 6.5)
        self.assertEqual(self._avisos(), 1)

    def test_sin_limites_criticos_usa_el_30_por_ciento_de_su_propio_rango(self):
        """ESPERADO: leucocitos 12 no es crítico (≤ 10 × 1,3); 14 sí."""
        self.assertFalse(self._resultado(self.leu, 12).es_critico)
        self.assertEqual(self._avisos(), 0)
        # La ficha dice lo mismo que el aviso (antes: aviso «CRÍTICO», ficha «fuera de rango»).
        self.assertTrue(self._resultado(self.leu, 14).es_critico)
        self.assertEqual(self._avisos(), 1)
