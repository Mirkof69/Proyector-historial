"""Ecografía ginecológica con IA: puente al microservicio, permisos y auditoría.

Esperado vs obtenido. Fallos que previenen: una caída del microservicio
convertida en error 500; enfermería o recepción analizando sin permiso; una
alarma de malignidad que no queda registrada; la imagen viajando en base64.
"""
from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from auditoria.models import RegistroAuditoria
from usuarios.models import Usuario

URL = "/api/ia/ginecologia/{}/"
PNG_1x1 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAAAAAA6fptVAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg==")


def _png():
    buf = BytesIO()
    Image.new("L", (64, 64), 30).save(buf, "PNG")
    return SimpleUploadedFile("ovario.png", buf.getvalue(), content_type="image/png")


def _respuesta(datos, codigo=200):
    r = mock.Mock(status_code=codigo, headers={"content-type": "application/json"})
    r.json.return_value = datos
    return r


class AnalisisGinecologicoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        def crear(email, rol):
            return Usuario.objects.create_user(email=email, nombre="N", apellido_paterno="A",
                                               password="clave-segura-123", rol=rol)
        cls.medico = crear("med.gin@test.bo", "medico")
        cls.enfermera = crear("enf.gin@test.bo", "enfermera")
        cls.recepcion = crear("rec.gin@test.bo", "recepcion")

    def cliente(self, u=None):
        c = APIClient()
        c.force_authenticate(u or self.medico)
        return c

    def test_lesion_ovarica_con_alarma_queda_auditada_y_la_imagen_viaja_como_archivo(self):
        """ESPERADO: 200, tipo y malignidad intactos, superposición como URL, auditoría con «ALARMA»."""
        datos = {"tarea": "ovario", "tipo_probable": "Carcinoma seroso de alto grado",
                 "malignidad": {"probabilidad": 0.81, "alarma": True}, "superposicion_png": PNG_1x1}
        with mock.patch("ia_medica.views_ginecologia.requests.post", return_value=_respuesta(datos)) as post:
            r = self.cliente().post(URL.format("ovario"), {"file": _png(), "tamano_pixel_mm": "0.2",
                                                           "paciente_id": "7"}, format="multipart")
        self.assertEqual(r.status_code, 200)
        cuerpo = r.json()
        self.assertTrue(cuerpo["malignidad"]["alarma"])
        self.assertNotIn("superposicion_png", cuerpo)
        self.assertIn("superposicion_url", cuerpo)
        self.assertTrue(post.call_args.args[0].endswith("/api/ginecologia/ovario"))
        self.assertEqual(post.call_args.kwargs["data"], {"tamano_pixel_mm": "0.2"})
        registro = RegistroAuditoria.objects.get(modulo="Ecografía ginecológica")
        self.assertIn("ALARMA", registro.detalle)
        self.assertIn("paciente 7", registro.detalle)

    def test_tarea_desconocida_404(self):
        self.assertEqual(self.cliente().post(URL.format("pulmon"), {"file": _png()}, format="multipart").status_code,
                         404)

    def test_sin_imagen_400(self):
        self.assertEqual(self.cliente().post(URL.format("mioma"), {}, format="multipart").status_code, 400)

    def test_microservicio_caido_503_con_mensaje(self):
        import requests

        with mock.patch("ia_medica.views_ginecologia.requests.post", side_effect=requests.ConnectionError("x")):
            r = self.cliente().post(URL.format("ovario-pco"), {"file": _png()}, format="multipart")
        self.assertEqual(r.status_code, 503)
        self.assertIn("8001", r.json()["error"])

    def test_red_sin_entrenar_devuelve_el_motivo(self):
        falta = _respuesta({"detail": "No está el modelo clasificador_ovario_pco.pth."}, 503)
        with mock.patch("ia_medica.views_ginecologia.requests.post", return_value=falta):
            r = self.cliente().post(URL.format("ovario-pco"), {"file": _png()}, format="multipart")
        self.assertEqual(r.status_code, 503)
        self.assertIn("clasificador_ovario_pco", r.json()["error"])

    def test_enfermeria_y_recepcion_no_analizan(self):
        for usuario in (self.enfermera, self.recepcion):
            r = self.cliente(usuario).post(URL.format("ovario"), {"file": _png()}, format="multipart")
            self.assertEqual(r.status_code, 403, usuario.rol)
