"""El listado de exámenes trae el estado y los valores de cada parámetro.

Sin `resumen` la lista mostraba «Sin resultados» en exámenes completos y la
historia clínica marcaba «Normal» un examen con un valor crítico (BUG-008).
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from laboratorio.models import ExamenLaboratorio, ResultadoLaboratorio, TipoExamen, ValorReferencia
from pacientes.models import Paciente
from usuarios.models import Usuario


class ListadoLaboratorioTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.lab@test.bo", nombre="Lia", apellido_paterno="Lab",
                                                 password="clave-segura-123", rol="medico")
        tipo = TipoExamen.objects.create(nombre="Hemograma prueba", codigo="HEMP1", categoria="hematologia",
                                         tiempo_resultado=1)
        hb = ValorReferencia.objects.create(tipo_examen=tipo, parametro="Hemoglobina", valor_minimo=11,
                                            valor_maximo=16, es_critico_bajo=7, unidad="g/dL")
        hto = ValorReferencia.objects.create(tipo_examen=tipo, parametro="Hematocrito", valor_minimo=33,
                                             valor_maximo=44, unidad="%")
        cls.paciente = Paciente.objects.create(nombre="Lis", apellido_paterno="Tado", apellido_materno="X",
                                               fecha_nacimiento=datetime.date(1993, 4, 4), genero="femenino",
                                               ci="7855501")
        cls.completo = ExamenLaboratorio.objects.create(paciente=cls.paciente, tipo_examen=tipo,
                                                        fecha_solicitud=timezone.now(), estado="completado")
        ResultadoLaboratorio.objects.create(examen=cls.completo, valor_referencia=hb, valor_numerico=6.2)
        ResultadoLaboratorio.objects.create(examen=cls.completo, valor_referencia=hto, valor_numerico=36)
        cls.pendiente = ExamenLaboratorio.objects.create(paciente=cls.paciente, tipo_examen=tipo,
                                                         fecha_solicitud=timezone.now(), estado="solicitado")

    def _listado(self):
        c = APIClient()
        c.force_authenticate(self.medico)
        r = c.get(f"/api/laboratorios/examenes/?paciente={self.paciente.pk}")
        self.assertEqual(r.status_code, 200, r.content[:300])
        datos = r.json()
        return {e["id"]: e for e in datos.get("results", datos)}

    def test_examen_con_valor_critico(self):
        e = self._listado()[self.completo.pk]
        self.assertEqual((e["resumen"]["total_parametros"], e["resumen"]["criticos"]), (2, 1))
        hb = next(f for f in e["resultados"] if f["parametro"] == "Hemoglobina")
        self.assertEqual((hb["estado"], hb["unidad"], hb["rango_referencia"]), ("CRÍTICO", "g/dL", "11.00-16.00"))
        self.assertTrue(e["tiene_resultados"])

    def test_examen_sin_resultados(self):
        e = self._listado()[self.pendiente.pk]
        self.assertIsNone(e["resumen"])
        self.assertEqual(e["resultados"], [])
