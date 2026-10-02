"""Ángulo de progresión intraparto: puente al microservicio y campo del partograma.

Esperado vs obtenido. Fallos que previenen: una caída del microservicio
convertida en error 500; enfermería midiendo sin permiso; un ángulo imposible
guardado en el partograma.
"""
import datetime
from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from embarazos.models import Embarazo
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/partos/angulo-progresion/"


def _png():
    buf = BytesIO()
    Image.new("L", (64, 64), 30).save(buf, "PNG")
    return SimpleUploadedFile("intraparto.png", buf.getvalue(), content_type="image/png")


class AnguloProgresionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.medico = Usuario.objects.create_user(email="med.aop@test.bo", nombre="M", apellido_paterno="A",
                                                 password="clave-segura-123", rol="medico")
        cls.enfermera = Usuario.objects.create_user(email="enf.aop@test.bo", nombre="E", apellido_paterno="A",
                                                    password="clave-segura-123", rol="enfermera")

    def cliente(self, u=None):
        c = APIClient()
        c.force_authenticate(u or self.medico)
        return c

    def test_devuelve_la_medida_y_queda_auditado(self):
        respuesta = mock.Mock(status_code=200, headers={"content-type": "application/json"})
        respuesta.json.return_value = {"tarea": "intraparto", "medidas": {"angulo_progresion_grados": 118.4,
                                                                          "margen_grados": 6.7}, "avisos": []}
        with mock.patch("partos.views_intraparto.requests.post", return_value=respuesta):
            r = self.cliente().post(URL, {"file": _png()}, format="multipart")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["medidas"]["angulo_progresion_grados"], 118.4)
        from auditoria.models import RegistroAuditoria

        self.assertTrue(RegistroAuditoria.objects.filter(modulo="Partograma").exists())

    def test_microservicio_caido_503_con_mensaje(self):
        import requests

        with mock.patch("partos.views_intraparto.requests.post", side_effect=requests.ConnectionError("apagado")):
            r = self.cliente().post(URL, {"file": _png()}, format="multipart")
        self.assertEqual(r.status_code, 503)
        self.assertIn("8001", r.json()["error"])

    def test_sin_imagen_400(self):
        self.assertEqual(self.cliente().post(URL, {}, format="multipart").status_code, 400)

    def test_enfermeria_no_mide(self):
        self.assertEqual(self.cliente(self.enfermera).post(URL, {"file": _png()}, format="multipart").status_code, 403)

    def test_partograma_rechaza_un_angulo_imposible(self):
        p = Paciente.objects.create(nombre="Aop", apellido_paterno="Prueba", apellido_materno="X", ci="7922001",
                                    fecha_nacimiento=datetime.date(1993, 1, 1), genero="femenino")
        emb = Embarazo.objects.create(paciente=p, numero_gesta=1, tipo_embarazo="simple",
                                      fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=39))
        parto = self.cliente().post("/api/partos/", {
            "embarazo": emb.id, "paciente": p.id, "tipo_parto": "vaginal_espontaneo", "fecha_parto": timezone.now().isoformat(),
            "edad_gestacional_parto": "39+0", "parto_finalizado": True, "sexo_bebe": "femenino", "peso_bebe": 3100,
            "talla_bebe": 49, "apgar_1min": 8, "apgar_5min": 9}, format="json").json()["id"]
        base = {"parto": parto, "hora_registro": timezone.now().isoformat(), "horas_trabajo_parto": 3,
                "dilatacion_cervical": 6, "estacion_fetal": "0", "contracciones_10min": 3}
        mal = self.cliente().post("/api/partos/partograma/", base | {"angulo_progresion": 250}, format="json")
        self.assertEqual(mal.status_code, 400)
        bien = self.cliente().post("/api/partos/partograma/", base | {"angulo_progresion": "118.4"}, format="json")
        self.assertEqual((bien.status_code, bien.json()["angulo_progresion"]), (201, "118.4"))
