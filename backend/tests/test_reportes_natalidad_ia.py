"""Reportes de natalidad/morbilidad y de IA: cifras reales del período.

Esperado vs obtenido con dos partos conocidos (uno vaginal de 3.200 g y una
cesárea pretérmino de 2.100 g con Apgar 6 y hemorragia posparto).
"""
import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from partos.models import Parto
from usuarios.models import Usuario


class ReporteNatalidadTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.nat@test.bo", nombre="M", apellido_paterno="N",
                                                 password="clave-segura-123", rol="medico")
        cls.recepcion = Usuario.objects.create_user(email="rec.nat@test.bo", nombre="R", apellido_paterno="N",
                                                    password="clave-segura-123", rol="recepcion")
        c = APIClient()
        c.force_authenticate(cls.medico)
        for ci, tipo, eg, peso, apgar, hpp in (("7911501", "vaginal_espontaneo", "39+2", 3200, 9, False),
                                               ("7911502", "cesarea_urgencia", "34+0", 2100, 6, True)):
            p = Paciente.objects.create(nombre="Nat", apellido_paterno="Al", apellido_materno="X", ci=ci,
                                        fecha_nacimiento=datetime.date(1992, 1, 1), genero="femenino")
            emb = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="simple",
                                          fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=39))
            r = c.post("/api/partos/", {
                "embarazo": emb.id, "paciente": p.id, "tipo_parto": tipo, "fecha_parto": timezone.now().isoformat(),
                "edad_gestacional_parto": eg, "parto_finalizado": True, "sexo_bebe": "femenino", "peso_bebe": peso,
                "talla_bebe": 48, "apgar_1min": apgar, "apgar_5min": apgar,
                "indicaciones_cesarea": "Sufrimiento fetal agudo" if tipo.startswith("cesarea") else "",
            }, format="json")
            assert r.status_code == 201, r.content[:300]
            if hpp:
                Parto.objects.filter(pk=r.json()["id"]).update(hemorragia_postparto=True)

    def cliente(self, usuario=None):
        c = APIClient()
        c.force_authenticate(usuario or self.medico)
        return c

    def test_cifras_del_periodo(self):
        d = self.cliente().get("/api/reportes/natalidad/").json()
        self.assertEqual(d["totales"], {"partos": 2, "recien_nacidos": 2, "cesareas": 1, "vaginales": 1})
        self.assertEqual((d["tasas"]["cesarea_pct"], d["tasas"]["bajo_peso_pct"], d["tasas"]["pretermino_pct"],
                          d["tasas"]["apgar5_menor_7_pct"], d["tasas"]["hemorragia_posparto_pct"]),
                         (50.0, 50.0, 50.0, 50.0, 50.0))
        self.assertEqual(sum(f["total"] for f in d["peso_al_nacer"]), 2)
        self.assertEqual(d["nacimientos_por_mes"][-1]["partos"], 2)

    def test_periodo_sin_partos_da_ceros_no_inventa(self):
        d = self.cliente().get("/api/reportes/natalidad/?desde=2020-01-01&hasta=2020-12-31").json()
        self.assertEqual(d["totales"]["partos"], 0)
        self.assertIsNone(d["tasas"]["cesarea_pct"])
        self.assertEqual(d["nacimientos_por_mes"], [])

    def test_fechas_invalidas_400(self):
        self.assertEqual(self.cliente().get("/api/reportes/natalidad/?desde=ayer").status_code, 400)
        self.assertEqual(self.cliente().get("/api/reportes/natalidad/?desde=2026-05-01&hasta=2026-01-01").status_code, 400)

    def test_excel(self):
        r = self.cliente().get("/api/reportes/natalidad/excel/")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.content.startswith(b"PK"))

    def test_recepcion_no_accede(self):
        self.assertEqual(self.cliente(self.recepcion).get("/api/reportes/natalidad/").status_code, 403)

    def test_reporte_ia_sin_microservicio(self):
        with mock.patch("requests.get", side_effect=ConnectionError("apagado")):
            d = self.cliente().get("/api/reportes/ia/").json()
        self.assertEqual(d["analisis_imagen"]["total"], 0)
        self.assertEqual(d["prediccion_peso"]["cerradas_con_nacimiento"], 0)
        self.assertTrue(any(m["codigo"] == "segmentacion_cabeza" and m["metrica_principal"] is None for m in d["modelos"]))
