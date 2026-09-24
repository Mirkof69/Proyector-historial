"""La tarea Celery de análisis funciona y usa la traducción única.

Fallo que previene: select_for_update se llamaba fuera de una transacción;
en PostgreSQL eso lanza TransactionManagementError y la tarea fallaba siempre
en su primera línea (las imágenes quedaban «pendientes» para siempre).
"""
import datetime
from unittest import mock

from django.test import TestCase

from ia_medica.models import AnalisisCNN, ImagenEcografica
from ia_medica.services.result_mapping import defaults_analisis_cnn
from ia_medica.tasks import analizar_imagen_task
from pacientes.models import Paciente

RESPUESTA = {
    "status": "success", "fuente": "efficientnet_b4", "score_global": 0.9,
    "pathology_detection": {"pathologies": [{"pathology": "anencefalia", "confidence": 0.9, "severity": "alta"}]},
    "biometry": {"disponible": False}, "advertencia": "Detector experimental",
}


class TareaAnalisisTest(TestCase):
    def setUp(self):
        p = Paciente.objects.create(nombre="Ana", apellido_paterno="Cel", apellido_materno="Ery",
                                    fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="7911001")
        self.imagen = ImagenEcografica.objects.create(paciente=p, imagen="ia_medica/x.png", nombre_original="x.png")

    def test_la_tarea_guarda_el_analisis(self):
        traducido = {**defaults_analisis_cnn(RESPUESTA), "fuente": "efficientnet_b4"}
        traducido.pop("realizado_por")
        with mock.patch("ia_medica.services.cnn_service.cnn_service.analizar_imagen", return_value=traducido):
            r = analizar_imagen_task.run(self.imagen.id, "efficientnet")
        self.assertEqual(r["status"], "success", r)
        a = AnalisisCNN.objects.get(imagen=self.imagen)
        self.assertEqual(a.resultado, "anomalia_grave")
        self.assertEqual(a.nivel_riesgo, "ALTO")
        self.assertIn("Detector experimental", a.alertas)
        self.imagen.refresh_from_db()
        self.assertEqual(self.imagen.estado, "analizada")

    def test_imagen_inexistente(self):
        self.assertEqual(analizar_imagen_task.run(999999, "efficientnet")["status"], "error")
