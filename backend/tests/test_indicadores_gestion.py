"""«Indicadores y metas» se calcula con los datos y no sale vacío.

Antes la pestaña leía /reportes/dashboard-kpis/ (otra forma) y mostraba
«Sin indicadores» (reportes/services/indicadores_gestion.py).
"""
import datetime

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario


class IndicadoresGestionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.ind@test.bo", nombre="Ana", apellido_paterno="Ind",
                                                 password="clave-segura-123", rol="medico")
        p = Paciente.objects.create(nombre="Lia", apellido_paterno="Ind", ci="7711223",
                                    fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino")
        emb = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="simple",
                                      fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=39))
        c = APIClient()
        c.force_authenticate(cls.medico)
        r = c.post("/api/partos/", {
            "embarazo": emb.id, "paciente": p.id, "tipo_parto": "cesarea_electiva",
            "fecha_parto": (timezone.now() - datetime.timedelta(days=3)).isoformat(), "edad_gestacional_parto": "36+2",
            "indicaciones_cesarea": "Presentación podálica", "parto_finalizado": True, "sexo_bebe": "femenino", "peso_bebe": 2300, "talla_bebe": 46,
            "apgar_1min": 7, "apgar_5min": 8,
        }, format="json")
        assert r.status_code == 201, r.content[:300]

    def test_calcula_los_nueve_indicadores_con_su_meta(self):
        c = APIClient()
        c.force_authenticate(self.medico)
        r = c.get("/api/reportes/indicadores-gestion/")
        self.assertEqual(r.status_code, 200)
        filas = {f["codigo"]: f for f in r.json()}
        self.assertEqual(len(filas), 9)
        # Un parto: cesárea, pretérmino (36 s) y bajo peso (2.300 g).
        self.assertEqual((filas["CES"]["valor_actual"], filas["PRET"]["valor_actual"], filas["BPN"]["valor_actual"]),
                         (100.0, 100.0, 100.0))
        self.assertEqual(filas["CES"]["estado_vs_meta"], "bajo_minimo")
        self.assertEqual(filas["APG"]["valor_actual"], 0.0)
        self.assertTrue(all(f["meta"] for f in filas.values()))
