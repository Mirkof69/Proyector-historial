"""Importación de resultados de laboratorio desde Excel.

Una fila = un parámetro. Las filas de la misma paciente, examen y fecha forman
un solo examen completado. Cada valor se evalúa contra su rango (igual que a
mano). Vista previa sin guardar; al confirmar, cada examen entero o nada.
"""
import datetime
from io import BytesIO, StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from openpyxl import Workbook, load_workbook
from rest_framework.test import APIClient

from laboratorio.models import ExamenLaboratorio, ResultadoLaboratorio
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/laboratorios/examenes/"
ENCABEZADOS = ["CI de la paciente *", "Código de examen *", "Fecha del resultado *", "Parámetro *", "Valor *",
               "Observaciones"]


def _excel(filas):
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Resultados"
    hoja.append(ENCABEZADOS)
    for f in filas:
        hoja.append(f)
    buf = BytesIO()
    libro.save(buf)
    return SimpleUploadedFile("resultados.xlsx", buf.getvalue(),
                              content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


class ImportacionLaboratorioTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("poblar_valores_referencia", stdout=StringIO())
        cls.medico = Usuario.objects.create_user(email="lab.imp@test.bo", nombre="Lia", apellido_paterno="Imp",
                                                 password="clave-segura-123", rol="medico")
        cls.p = Paciente.objects.create(nombre="Rut", apellido_paterno="Lab", apellido_materno="X",
                                        fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7866601")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.medico)
        self.ayer = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    def _filas(self):
        return [
            ["7866601", "HEM001", self.ayer, "Hemoglobina", "11,8", ""],
            ["7866601", "HEM001", self.ayer, "Plaquetas", "250000", ""],
            ["7866601", "HEM001", self.ayer, "Hemoglobina", "12", "repetida"],      # duplicada en el archivo
            ["9999999", "HEM001", self.ayer, "Hemoglobina", "12", ""],              # paciente inexistente
            ["7866601", "XXX999", self.ayer, "Hemoglobina", "12", ""],              # examen inexistente
            ["7866601", "HEM001", "01/01/2099", "Hemoglobina", "12", ""],           # fecha futura
            ["7866601", "HEM001", self.ayer, "Hemoglobina", "alta", ""],            # no numérico
        ]

    def test_plantilla_trae_el_catalogo(self):
        r = self.c.get(URL + "plantilla-excel/")
        self.assertEqual(r.status_code, 200)
        libro = load_workbook(BytesIO(r.content))
        self.assertIn("Catálogo", libro.sheetnames)
        self.assertGreater(libro["Catálogo"].max_row, 70)

    def test_vista_previa_no_guarda_y_explica_cada_error(self):
        r = self.c.post(URL + "importar-excel/", {"archivo": _excel(self._filas())}, format="multipart").json()
        self.assertEqual(r["resumen"]["valida"], 2)
        self.assertEqual(r["resumen"]["duplicada"], 1)
        self.assertEqual(r["resumen"]["error"], 4)
        self.assertEqual(ExamenLaboratorio.objects.count(), 0)
        errores = " | ".join(e for f in r["filas"] for e in f["errores"])
        for texto in ("9999999", "XXX999", "futura", "no es un número"):
            self.assertIn(texto, errores)

    def test_confirmar_crea_un_examen_con_sus_resultados_evaluados(self):
        r = self.c.post(URL + "importar-excel/", {"archivo": _excel(self._filas()), "confirmar": "1"},
                        format="multipart").json()
        self.assertEqual(r["resumen"]["creada"], 2)
        examen = ExamenLaboratorio.objects.get()
        self.assertEqual(examen.estado, "completado")
        self.assertEqual(examen.resultados.count(), 2)
        hb = examen.resultados.get(valor_referencia__parametro="Hemoglobina")
        self.assertEqual(float(hb.valor_numerico), 11.8)          # coma decimal aceptada

    def test_reimportar_el_mismo_archivo_no_duplica(self):
        for _ in range(2):
            self.c.post(URL + "importar-excel/", {"archivo": _excel(self._filas()), "confirmar": "1"},
                        format="multipart")
        self.assertEqual(ResultadoLaboratorio.objects.count(), 2)

    def test_archivo_sin_columnas_obligatorias_pide_mapeo(self):
        """ESPERADO: no se guarda nada y se devuelven los encabezados para que el
        usuario diga qué columna es cada dato."""
        libro = Workbook()
        libro.active.append(["Otra cosa"])
        buf = BytesIO()
        libro.save(buf)
        r = self.c.post(URL + "importar-excel/", {"archivo": SimpleUploadedFile("x.xlsx", buf.getvalue())},
                        format="multipart")
        self.assertTrue(r.json()["requiere_mapeo"])
        self.assertEqual(r.json()["encabezados"], ["Otra cosa"])
        self.assertIn("Faltan columnas", r.json()["error"])
        self.assertEqual(ResultadoLaboratorio.objects.count(), 0)
