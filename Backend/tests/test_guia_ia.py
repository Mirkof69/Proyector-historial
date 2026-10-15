"""Catálogo de modelos que alimenta la Guía de IA y la pestaña «Modelos y métricas»,
y el reenvío de errores del análisis completo.

Esperado vs obtenido. Fallos que previene:
- el catálogo listaba 7 de las 13 redes en servicio: faltaban la lesión ovárica,
  su tipo, el mioma, el ovario poliquístico, el fémur y la circunferencia abdominal;
- una cifra de la guía que no coincide con la que dejó el entrenamiento;
- un modelo descartado (translucencia nucal, acidemia, prematuro...) presentado como disponible;
- el análisis completo devolvía 500 «Error en el microservicio de IA» cuando la
  imagen era de una extensión no permitida o el tamaño de píxel era absurdo (400).

Datos: `tests/datos/modelos_microservicio.json` es la respuesta real de
GET /api/modelos del microservicio el 14/10/2026 (las métricas de cada red).
"""
import json
import re
from pathlib import Path
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from ia_medica.services import catalogo_modelos as cat
from usuarios.models import Usuario

AQUI = Path(__file__).resolve().parent
ESTADO_REAL = json.loads((AQUI / "datos" / "modelos_microservicio.json").read_text(encoding="utf-8"))
ENTRENAMIENTO = AQUI.parent / "Microservicio_IA" / "entrenamiento"

REDES_EN_SERVICIO = {
    "plano_anatomico_fetal_planes", "segmentacion_cabeza", "segmentacion_torax", "segmentacion_abdomen",
    "biometria_femur", "biometria_abdomen", "segmentacion_intraparto", "anomalias_cerebrales_fetales",
    "circunferencia_cefalica_hc18", "segmentacion_ovario", "clasificador_ovario", "segmentacion_mioma",
    "clasificador_ovario_pco",
}


def _respuesta(cuerpo):
    r = mock.MagicMock(status_code=200)
    r.json.return_value = cuerpo
    return r


class CatalogoCompletoTest(SimpleTestCase):
    def _redes(self, estado):
        with mock.patch("requests.get", return_value=_respuesta(estado)):
            return {m["codigo"]: m for m in cat._redes_del_microservicio()}

    def test_estan_las_13_redes_que_sirve_el_microservicio(self):
        """ESPERADO: cada red del microservicio en el catálogo, disponible y con su métrica."""
        redes = self._redes(ESTADO_REAL)
        self.assertEqual(set(redes), REDES_EN_SERVICIO)
        self.assertEqual(set(ESTADO_REAL), REDES_EN_SERVICIO, "el microservicio sirve una red que el catálogo no conoce")
        for codigo, m in redes.items():
            self.assertTrue(m["disponible"], codigo)
            self.assertTrue(m["metrica_principal"], f"{codigo} sin métrica")
            self.assertTrue(m["datos"], f"{codigo} sin datos de entrenamiento")

    def test_las_cifras_son_las_medidas(self):
        """ESPERADO: las cifras de docs/sistema/10_inteligencia_artificial.md, con coma decimal."""
        redes = self._redes(ESTADO_REAL)
        esperado = {
            "plano_anatomico_fetal_planes": ["92,7 %", "5.271", "58,8 %"],
            "segmentacion_cabeza": ["4,4 mm", "92 % dentro del 5 %", "999"],
            "segmentacion_torax": ["0,93", "±0,02", "no valida"],
            "biometria_femur": ["1,3 mm", "353 imágenes de 271 pacientes"],
            "biometria_abdomen": ["2,9 %", "89 %"],
            "segmentacion_intraparto": ["6,7°", "65 %", "96 %"],
            "anomalias_cerebrales_fetales": ["1 de 1.866", "no medible"],
            "segmentacion_ovario": ["0,85", "88 %"],
            "clasificador_ovario": ["68,6 %", "7 de 13", "97,6 %", "no descarta"],
            "segmentacion_mioma": ["96,9 %", "no sirve para descartarlo"],
            "clasificador_ovario_pco": ["80,0 %", "Rotterdam"],
        }
        for codigo, trozos in esperado.items():
            for t in trozos:
                self.assertIn(t, redes[codigo]["metrica_principal"], codigo)
        # Sin punto decimal inglés en ninguna cifra («92.7%»).
        for m in redes.values():
            self.assertIsNone(re.search(r"\d\.\d+ ?%", m["metrica_principal"]), m["metrica_principal"])

    def test_metricas_con_otra_forma_no_inventan_numero(self):
        estado = {k: {"disponible": True, "metricas_prueba": {"otra": 1}} for k in REDES_EN_SERVICIO}
        redes = self._redes(estado)
        self.assertTrue(all(m["metrica_principal"] is None for m in redes.values()))

    def test_descartados_no_figuran_como_en_servicio(self):
        codigos = {d["codigo"] for d in cat.descartados()}
        self.assertEqual(len(codigos), 7)
        self.assertFalse(codigos & REDES_EN_SERVICIO)
        self.assertIn("translucencia_nucal", codigos)
        self.assertTrue(all(d["motivo"] and d["metrica"] for d in cat.descartados()))
        self.assertTrue(all("evidencia" not in d for d in cat.descartados()))


class DescartadosCoincidenConElEntrenamientoTest(SimpleTestCase):
    """Cada cifra de un modelo descartado sale del metricas.json de su entrenamiento."""

    def _leer(self, ruta):
        archivo = ENTRENAMIENTO / ruta
        if not archivo.exists():
            self.skipTest(f"no está {ruta}")
        return json.loads(archivo.read_text(encoding="utf-8"))

    def _metrica(self, codigo):
        return next(d for d in cat.DESCARTADOS if d["codigo"] == codigo)["metrica"]

    def test_acidemia(self):
        p = self._leer("senales/salidas/ctu_acidosis/metricas.json")["acidemia_ph_menor_7_15"]["prueba"]
        self.assertIn(cat._num(p["auc"], 2), self._metrica("acidemia_ctu_uhb"))
        self.assertIn(cat._pct(p["especificidad"], 0), self._metrica("acidemia_ctu_uhb"))
        self.assertIn(cat._pct(p["sensibilidad"], 0), self._metrica("acidemia_ctu_uhb"))

    def test_prematuro(self):
        cv = self._leer("senales/salidas/tpehg_prematuro/metricas.json")["ehg_y_clinicos"]["auc_validacion_cruzada"]
        self.assertIn(f"{cat._num(min(cv.values()), 2)}–{cat._num(max(cv.values()), 2)}", self._metrica("prematuro_tpehg"))

    def test_translucencia(self):
        d = self._leer("translucencia/salidas/zoom/metricas.json")
        m = self._metrica("translucencia_nucal")
        self.assertIn(cat._pct(d["prueba_interna"]["exactitud"]), m)
        self.assertIn(cat._pct(d["prueba_externa"]["exactitud"]), m)

    def test_cardium(self):
        d = self._leer("senales/salidas/cardium_tabla/metricas.json")
        m = self._metrica("cardiopatia_cardium")
        self.assertIn(cat._num(d["A_todas_las_variables"]["prueba"]["auc"], 2), m)
        vpp = sorted([d["A_todas_las_variables"]["prueba"]["vpp"], d["B_solo_antes_de_la_ecografia"]["prueba"]["vpp"]])
        self.assertIn(f"{round(vpp[0] * 100)}–{round(vpp[1] * 100)} %", m)

    def test_cervix_y_riesgo_materno(self):
        d = self._leer("ginecologia/salidas/tablas/metricas.json")
        self.assertIn(cat._num(d["cancer_cervicouterino"]["A_solo_factores_de_riesgo"]["prueba"]["auc"], 2),
                      self._metrica("cancer_cervicouterino"))
        prueba = d["riesgo_materno"]["prueba"]
        self.assertIn(cat._pct(prueba["exactitud_balanceada"], 0), self._metrica("riesgo_materno"))
        self.assertIn(str(prueba["casos"]), self._metrica("riesgo_materno"))


@override_settings(AI_SERVICE_URL="http://ia:8001")
class EndpointsTest(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        self.medico = Usuario.objects.create_user(
            email="medico-guia@test.com", nombre="Dra", apellido_paterno="Guía",
            password="medicopass123", rol="medico",
        )
        self.cliente.force_authenticate(self.medico)

    def test_modelos_trae_las_redes_y_los_descartados(self):
        """ESPERADO: GET /api/ia/imagenes/modelos/ — lo que lee la Guía de IA."""
        with mock.patch("requests.get", return_value=_respuesta(ESTADO_REAL)):
            r = self.cliente.get("/api/ia/imagenes/modelos/")
        self.assertEqual(r.status_code, 200)
        d = r.json()
        codigos = {m["codigo"] for m in d["modelos_builtin"]}
        self.assertTrue(REDES_EN_SERVICIO <= codigos)
        self.assertEqual(len(d["modelos_descartados"]), 7)

    def test_sin_sesion_no_ve_el_catalogo(self):
        self.assertIn(APIClient().get("/api/ia/imagenes/modelos/").status_code, (401, 403))

    def _post_analisis(self, codigo, cuerpo, **datos):
        respuesta = mock.MagicMock(status_code=codigo, text=json.dumps(cuerpo))
        respuesta.json.return_value = cuerpo
        with mock.patch("ecografias.ai_views.requests.post", return_value=respuesta):
            archivo = SimpleUploadedFile("eco.png", b"\x89PNG falso", content_type="image/png")
            return self.cliente.post("/api/ecografias/analyze-with-ai/", {"file": archivo, **datos})

    def test_extension_no_permitida_llega_como_400_con_su_motivo(self):
        """ANTES: 500 «Error en el microservicio de IA» con el JSON crudo en `details`."""
        r = self._post_analisis(400, {"detail": "Extensión no permitida. Use: ['.png']"})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Extensión no permitida", r.json()["error"])

    def test_tamano_de_pixel_absurdo_llega_como_400(self):
        r = self._post_analisis(400, {"detail": "tamano_pixel_mm fuera de rango (0,01–2,0 mm por píxel)."},
                                tamano_pixel_mm="5")
        self.assertEqual(r.status_code, 400)
        self.assertIn("fuera de rango", r.json()["error"])

    def test_red_sin_instalar_llega_como_503(self):
        r = self._post_analisis(503, {"detail": "Falta segmentacion_cabeza.pth"})
        self.assertEqual(r.status_code, 503)
        self.assertIn("segmentacion_cabeza", r.json()["error"])

    def test_fallo_interno_del_microservicio_es_502(self):
        r = self._post_analisis(500, {"detail": "Traceback..."})
        self.assertEqual(r.status_code, 502)


@override_settings(AI_SERVICE_URL="http://ia:8001")
class AsistenteConsultaTest(TestCase):
    """POST /api/ia/consultas/consultar/ desde cualquier pantalla del frontend."""

    def setUp(self):
        self.cliente = APIClient()
        self.cliente.force_authenticate(Usuario.objects.create_user(
            email="medico-chat@test.com", nombre="Dra", apellido_paterno="Chat",
            password="medicopass123", rol="medico",
        ))

    def _consultar(self, **extra):
        r = mock.MagicMock(status_code=200)
        r.json.return_value = {"respuesta": "Preeclampsia: PA ≥ 140/90.", "categoria": "preeclampsia",
                               "confianza": 70, "tiempo_respuesta_ms": 1}
        with mock.patch("ia_medica.views.requests.post", return_value=r):
            return self.cliente.post("/api/ia/consultas/consultar/",
                                     {"consulta": "¿Cómo detectar preeclampsia?", **extra}, format="json")

    def test_paciente_cero_no_tumba_la_consulta(self):
        """ANTES: el frontend mandaba paciente_id = 0 fuera de la ficha de una paciente y daba 500."""
        from ia_medica.models import ConsultaIA

        r = self._consultar(paciente_id=0)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["consulta"]["respuesta_ia"], "Preeclampsia: PA ≥ 140/90.")
        self.assertIsNone(ConsultaIA.objects.get(id=r.json()["consulta"]["id"]).paciente_id)

    def test_paciente_inexistente_va_sin_paciente(self):
        r = self._consultar(paciente_id=987654)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIsNone(r.json()["consulta"]["paciente"])

    def test_sin_paciente(self):
        self.assertEqual(self._consultar().status_code, 200)
