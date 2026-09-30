"""El puente Django → microservicio para las redes entrenadas con
ecografías reales. El microservicio se simula: aquí se prueba el reenvío,
no la red (eso lo prueba Microservicio_IA/test_ecografia_real.py).
"""
from unittest.mock import MagicMock, patch

import requests
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from usuarios.models import Usuario


def _respuesta(codigo: int, cuerpo: dict) -> MagicMock:
    r = MagicMock(status_code=codigo)
    r.json.return_value = cuerpo
    return r


def _png() -> SimpleUploadedFile:
    return SimpleUploadedFile("eco.png", b"\x89PNG falso", content_type="image/png")


@override_settings(AI_SERVICE_URL="http://ia:8001")
class PuenteRedesReales(TestCase):
    def setUp(self):
        self.cliente = APIClient()
        medico = Usuario.objects.create_user(
            email="medico-redes@test.com", nombre="Dr", apellido_paterno="Redes",
            password="medicopass123", rol="medico",
        )
        self.cliente.force_authenticate(medico)

    def test_sin_sesion_no_entra(self):
        r = APIClient().post("/api/ecografias/plano-anatomico/", {"file": _png()})
        self.assertIn(r.status_code, (401, 403))

    @patch("ecografias.ai_views.requests.post")
    def test_plano_llega_tal_cual_del_microservicio(self, post):
        """ESPERADO: 200 con el plano y a la URL correcta del microservicio."""
        post.return_value = _respuesta(200, {"plano": "cerebro fetal", "confianza": 0.97})
        r = self.cliente.post("/api/ecografias/plano-anatomico/", {"file": _png()})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["plano"], "cerebro fetal")
        self.assertEqual(post.call_args.args[0], "http://ia:8001/api/plano-anatomico")

    @patch("ecografias.ai_views.requests.post")
    def test_circunferencia_pasa_el_tamano_de_pixel(self, post):
        post.return_value = _respuesta(200, {"circunferencia_cefalica_mm": 174.2})
        r = self.cliente.post(
            "/api/ecografias/circunferencia-cefalica/",
            {"file": _png(), "tamano_pixel_mm": "0.12"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(post.call_args.kwargs["data"], {"tamano_pixel_mm": "0.12"})

    def test_circunferencia_sin_tamano_de_pixel_da_400_sin_llamar(self):
        with patch("ecografias.ai_views.requests.post") as post:
            r = self.cliente.post("/api/ecografias/circunferencia-cefalica/", {"file": _png()})
        self.assertEqual(r.status_code, 400)
        self.assertIn("tamano_pixel_mm", r.json()["error"])
        post.assert_not_called()

    def test_sin_archivo_da_400(self):
        r = self.cliente.post("/api/ecografias/plano-anatomico/", {})
        self.assertEqual(r.status_code, 400)

    @patch("ecografias.ai_views.requests.post")
    def test_error_del_microservicio_se_reenvia_con_su_mensaje(self, post):
        """ESPERADO: el 503 «modelo sin entrenar» llega como 503 con su texto,
        no convertido en un 500 genérico."""
        post.return_value = _respuesta(503, {"detail": "No está el modelo x.pth"})
        r = self.cliente.post("/api/ecografias/plano-anatomico/", {"file": _png()})
        self.assertEqual(r.status_code, 503)
        self.assertIn("x.pth", r.json()["error"])

    @patch("ecografias.ai_views.requests.post")
    def test_anomalias_cerebrales_va_a_su_red(self, post):
        """ESPERADO: 200 con la alarma y a la URL de la red de anomalías."""
        post.return_value = _respuesta(200, {"aplicable": True, "alarma_anomalia": False})
        r = self.cliente.post("/api/ecografias/anomalias-cerebrales/", {"file": _png()})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["alarma_anomalia"])
        self.assertEqual(post.call_args.args[0], "http://ia:8001/api/anomalias-cerebrales")

    @patch("ecografias.ai_views.requests.post", side_effect=requests.ConnectionError())
    def test_microservicio_apagado_da_503_claro(self, _post):
        r = self.cliente.post("/api/ecografias/plano-anatomico/", {"file": _png()})
        self.assertEqual(r.status_code, 503)
        self.assertIn("8001", r.json()["error"])
