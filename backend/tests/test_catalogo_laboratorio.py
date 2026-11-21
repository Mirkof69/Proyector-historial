"""El catálogo de laboratorio se carga de verdad.

Antes `poblar_valores_referencia` buscaba tipos de examen que nadie creaba (no
cargaba nada) y llamaba a métodos que solo existían en otro comando (se caía
con AttributeError). Sin parámetros con rango, ningún resultado de laboratorio
se podía registrar ni importar.
"""
from io import StringIO

from django.core.management import call_command
from django.db.models import Count
from django.test import TestCase

from laboratorio.catalogo import PANEL_PRENATAL, TIPOS_EXAMEN, asegurar_tipos_examen
from laboratorio.models import TipoExamen, ValorReferencia


class CatalogoLaboratorioTest(TestCase):
    def test_el_comando_crea_tipos_y_rangos_para_todo_el_catalogo(self):
        call_command("poblar_valores_referencia", stdout=StringIO())
        self.assertEqual(TipoExamen.objects.filter(codigo__in=TIPOS_EXAMEN).count(), len(TIPOS_EXAMEN))
        sin_rangos = TipoExamen.objects.annotate(n=Count("valores_referencia")).filter(n=0)
        self.assertEqual(list(sin_rangos.values_list("codigo", flat=True)), [])
        self.assertGreater(ValorReferencia.objects.count(), 70)

    def test_es_idempotente(self):
        call_command("poblar_valores_referencia", stdout=StringIO())
        antes = (TipoExamen.objects.count(), ValorReferencia.objects.count())
        call_command("poblar_valores_referencia", stdout=StringIO())
        self.assertEqual((TipoExamen.objects.count(), ValorReferencia.objects.count()), antes)

    def test_adopta_un_examen_existente_con_otro_codigo_sin_duplicarlo(self):
        """La demo tenía «Hemograma completo» como HEM-001; nombre es único."""
        viejo = TipoExamen.objects.create(nombre="Hemograma completo", codigo="HEM-001", categoria="hematologia",
                                          tiempo_resultado=24)
        asegurar_tipos_examen()
        viejo.refresh_from_db()
        self.assertEqual(viejo.codigo, "HEM001")
        self.assertEqual(TipoExamen.objects.filter(nombre="Hemograma completo").count(), 1)

    def test_el_panel_prenatal_esta_en_el_catalogo(self):
        self.assertTrue(set(PANEL_PRENATAL) <= set(TIPOS_EXAMEN))


class EvaluacionDeResultadosTest(TestCase):
    """Antes: un 0 era «sin valor», un rango con mínimo 0 se saltaba (todo
    salía normal) y un rango de un solo límite también salía siempre normal."""

    @classmethod
    def setUpTestData(cls):
        cls.tipo = TipoExamen.objects.create(nombre="Prueba eval", codigo="EVAL1", categoria="bioquimica",
                                             tiempo_resultado=1)

    def _rango(self, **kw):
        return ValorReferencia(tipo_examen=self.tipo, parametro="p", unidad="u", **kw)

    def test_minimo_cero_no_desactiva_el_rango(self):
        basofilos = self._rango(valor_minimo=0, valor_maximo=1)
        self.assertEqual(basofilos.evaluar_valor(1.2)["estado"], "anormal")
        # Sin límites críticos configurados, pasar el máximo en más de un 30 % es crítico.
        self.assertEqual(basofilos.evaluar_valor(5)["estado"], "critico_alto")
        self.assertEqual(basofilos.evaluar_valor(0)["estado"], "normal")

    def test_un_solo_limite(self):
        glucosa = self._rango(valor_maximo=92)
        self.assertEqual(glucosa.evaluar_valor(100)["estado"], "anormal")
        self.assertTrue(glucosa.evaluar_valor(130)["es_critico"])
        self.assertEqual(glucosa.evaluar_valor(80)["estado"], "normal")
        self.assertEqual(self._rango(valor_minimo=3.5).evaluar_valor(3)["estado"], "anormal")
        self.assertEqual(self._rango(valor_minimo=3.5).evaluar_valor(2)["estado"], "critico_bajo")

    def test_cero_es_un_valor(self):
        self.assertEqual(self._rango(valor_minimo=1, valor_maximo=4).evaluar_valor(0)["estado"], "critico_bajo")
        self.assertEqual(self._rango(valor_minimo=1, valor_maximo=4).evaluar_valor(None)["estado"], "sin_valor")

    def test_rango_texto(self):
        self.assertEqual(self._rango(valor_maximo=92).rango_texto(), "≤ 92")
        self.assertEqual(self._rango(valor_normal="No reactivo").rango_texto(), "No reactivo")


class InterpretacionNoSeRepiteTest(TestCase):
    def test_editar_un_resultado_no_duplica_la_interpretacion(self):
        import datetime

        from django.utils import timezone

        from laboratorio.models import ExamenLaboratorio, ResultadoLaboratorio
        from pacientes.models import Paciente

        tipo = TipoExamen.objects.create(nombre="Interp", codigo="INT1", categoria="bioquimica", tiempo_resultado=1)
        rango = ValorReferencia.objects.create(tipo_examen=tipo, parametro="Glucosa", valor_minimo=70,
                                               valor_maximo=92, unidad="mg/dL")
        p = Paciente.objects.create(nombre="Ina", apellido_paterno="Terp", apellido_materno="X",
                                    fecha_nacimiento=datetime.date(1992, 3, 3), genero="femenino", ci="7844401")
        ex = ExamenLaboratorio.objects.create(paciente=p, tipo_examen=tipo, fecha_solicitud=timezone.now(),
                                              estado="completado")
        r = ResultadoLaboratorio.objects.create(examen=ex, valor_referencia=rango, valor_numerico=130,
                                                observaciones="Muestra hemolizada")
        r.valor_numerico = 85
        r.save()
        r.save()
        r.refresh_from_db()
        self.assertTrue(r.es_normal)
        self.assertEqual(r.observaciones.count("Interpretación:"), 1)
        self.assertIn("Muestra hemolizada", r.observaciones)
