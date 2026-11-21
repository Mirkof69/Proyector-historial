"""Importación de pacientes desde Excel: plantilla, vista previa y confirmación.

Pedido: «importación y exportación Excel fáciles de usar». Antes había un
modal de importación que no importaba nada (se eliminó).
"""
import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from openpyxl import Workbook, load_workbook
from rest_framework.test import APIClient

from pacientes.importacion_excel import COLUMNAS
from pacientes.fields import compute_search_hash
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/pacientes/importar-excel/"


def _excel(filas):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Pacientes"
    hoja.append([enc + (" *" if oblig else "") for _, enc, oblig, *_ in COLUMNAS])
    campos = [c for c, *_ in COLUMNAS]
    for f in filas:
        hoja.append([f.get(c, "") for c in campos])
    buf = BytesIO()
    libro.save(buf)
    return SimpleUploadedFile("pacientes.xlsx", buf.getvalue())


BUENA = {"ci": "8123456", "nombre": "Lucía", "apellido_paterno": "Choque", "fecha_nacimiento": "15/03/1995",
         "telefono": "71234567", "consentimiento_datos_aceptado": "SI"}


class ImportacionPacientesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.recepcion = Usuario.objects.create_user(email="rec.imp@test.bo", nombre="R", apellido_paterno="I",
                                                    password="clave-segura-123", rol="recepcion")
        Paciente.objects.create(nombre="Ya", apellido_paterno="Existe", apellido_materno="X",
                                fecha_nacimiento=datetime.date(1990, 1, 1), genero="femenino", ci="8999999")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.recepcion)

    def test_la_plantilla_trae_encabezados_e_instrucciones(self):
        r = self.c.get("/api/pacientes/plantilla-excel/")
        self.assertEqual(r.status_code, 200)
        libro = load_workbook(BytesIO(r.content))
        self.assertEqual(libro.sheetnames, ["Pacientes", "Instrucciones"])
        self.assertEqual(libro["Pacientes"]["A1"].value, "CI *")

    def test_la_vista_previa_no_crea_nada_y_clasifica_cada_fila(self):
        filas = [
            BUENA,
            {**BUENA, "ci": "8123457", "consentimiento_datos_aceptado": "NO"},   # sin consentimiento
            {**BUENA, "ci": "8999999"},                                         # ya existe
            {**BUENA, "ci": "8123458", "fecha_nacimiento": "no es fecha"},     # fecha inválida
        ]
        antes = Paciente.objects.count()
        r = self.c.post(URL, {"archivo": _excel(filas)}, format="multipart")
        self.assertEqual(r.status_code, 200, r.content[:300])
        estados = [f["estado"] for f in r.json()["filas"]]
        self.assertEqual(estados, ["valida", "error", "duplicada", "error"])
        self.assertIn("Consentimiento", " ".join(r.json()["filas"][1]["errores"]))
        self.assertEqual(Paciente.objects.count(), antes)

    def test_confirmar_crea_solo_las_validas(self):
        filas = [BUENA, {**BUENA, "ci": "8123457", "consentimiento_datos_aceptado": "NO"}]
        r = self.c.post(URL, {"archivo": _excel(filas), "confirmar": "1"}, format="multipart")
        self.assertEqual(r.json()["resumen"]["creada"], 1)
        p = Paciente.objects.get(ci_hash=compute_search_hash("8123456"))
        self.assertEqual(p.fecha_nacimiento, datetime.date(1995, 3, 15))
        self.assertTrue(p.consentimiento_datos_aceptado)
        self.assertIsNotNone(p.consentimiento_datos_fecha)
        self.assertFalse(Paciente.objects.filter(ci_hash=compute_search_hash("8123457")).exists())

    def test_un_archivo_sin_columnas_obligatorias_se_rechaza(self):
        libro = Workbook()
        libro.active.append(["Nombre", "Otra"])
        buf = BytesIO()
        libro.save(buf)
        r = self.c.post(URL, {"archivo": SimpleUploadedFile("x.xlsx", buf.getvalue())}, format="multipart")
        self.assertEqual(r.status_code, 400)
        self.assertIn("CI", r.json()["error"])

    def test_un_archivo_que_no_es_excel_se_rechaza(self):
        r = self.c.post(URL, {"archivo": SimpleUploadedFile("x.xlsx", b"no soy excel")}, format="multipart")
        self.assertEqual(r.status_code, 400)
