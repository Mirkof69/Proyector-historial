"""Unidades al importar laboratorio (CSV y Excel), esperado vs obtenido.

Fallo que previenen (29/10/2026): plaquetas «250000» (por µL) en un parámetro
de 10³/µL se guardaban como 250 millones y avisaban «RESULTADO CRÍTICO».
"""
import datetime
from decimal import Decimal
from io import BytesIO, StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from openpyxl import Workbook
from rest_framework.test import APIClient

from laboratorio.models import ResultadoLaboratorio
from laboratorio.unidades import UnidadIncompatible, convertir, corregir_conteo_sin_unidad
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/laboratorios/examenes/importar-excel/"


class _Rango:
    def __init__(self, unidad, maximo, critico_alto=None):
        self.unidad, self.valor_maximo, self.es_critico_alto = unidad, Decimal(maximo), critico_alto


class ConversionTest(SimpleTestCase):
    def test_conteos(self):
        self.assertEqual(convertir(Decimal(250000), "/µL", "10³/µL"), Decimal(250))
        self.assertEqual(convertir(Decimal(7500), "cél/mm³", "10³/µL"), Decimal("7.5"))
        self.assertEqual(convertir(Decimal("7.5"), "x10^9/L", "10³/µL"), Decimal("7.5"))

    def test_masa_por_volumen(self):
        self.assertEqual(convertir(Decimal(119), "g/L", "g/dL"), Decimal("11.9"))
        self.assertEqual(convertir(Decimal("0.9"), "mg/dL", "mg/dL"), Decimal("0.9"))
        self.assertEqual(convertir(Decimal(10), "mg/L", "mg/dL"), Decimal(1))

    def test_actividad(self):
        self.assertEqual(convertir(Decimal(5), "mUI/mL", "UI/L"), Decimal(5))

    def test_masa_a_molar_no_se_adivina(self):
        """ESPERADO: glucosa en mmol/L no se convierte a mg/dL (depende del analito)."""
        with self.assertRaises(UnidadIncompatible):
            convertir(Decimal("5.2"), "mmol/L", "mg/dL")

    def test_sin_unidad_solo_corrige_lo_imposible(self):
        plaquetas = _Rango("10³/µL", 400, Decimal(1000))
        leucocitos = _Rango("10³/µL", 17, Decimal(30))
        self.assertEqual(corregir_conteo_sin_unidad(Decimal(250000), plaquetas)[0], Decimal(250))
        self.assertEqual(corregir_conteo_sin_unidad(Decimal(20000), plaquetas)[0], Decimal(20))
        self.assertEqual(corregir_conteo_sin_unidad(Decimal(7500), leucocitos)[0], Decimal("7.5"))
        self.assertEqual(corregir_conteo_sin_unidad(Decimal(250), plaquetas), (Decimal(250), ""))
        valor, aviso = corregir_conteo_sin_unidad(Decimal(1500), plaquetas)
        self.assertEqual(valor, Decimal(1500))
        self.assertIn("verifique", aviso)
        # Una hemoglobina nunca se toca sin unidad.
        self.assertEqual(corregir_conteo_sin_unidad(Decimal(119), _Rango("g/dL", 16)), (Decimal(119), ""))


class ImportacionConUnidadesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("poblar_valores_referencia", stdout=StringIO())
        cls.lab = Usuario.objects.create_user(email="lab.uni@test.bo", nombre="Lu", apellido_paterno="Uni",
                                              password="clave-segura-123", rol="laboratorista")
        Paciente.objects.create(nombre="Una", apellido_paterno="Unidad", apellido_materno="X",
                                fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7866801")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.lab)
        self.ayer = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    def _importar(self, archivo):
        r = self.c.post(URL, {"archivo": archivo, "confirmar": "1"}, format="multipart")
        self.assertEqual(r.status_code, 200, r.content[:400])
        return r.json()

    def test_csv_sin_unidad_plaquetas_por_microlitro(self):
        texto = (f"Cédula;Código de examen;Fecha;Analito;Resultado\n"
                 f"7866801;HEM001;{self.ayer};Plaquetas;250000\n")
        datos = self._importar(SimpleUploadedFile("r.csv", texto.encode(), content_type="text/csv"))
        self.assertEqual(datos["resumen"]["creada"], 1)
        self.assertIn("/µL", datos["filas"][0]["avisos"][0])
        r = ResultadoLaboratorio.objects.get()
        self.assertEqual(r.valor_numerico, Decimal(250))
        self.assertFalse(r.es_critico)
        self.assertIn("Valor original del laboratorio: 250000", r.observaciones)

    def test_excel_con_columna_unidad(self):
        libro = Workbook()
        hoja = libro.active
        hoja.append(["CI", "Código", "Fecha", "Parámetro", "Valor", "Unidad"])
        hoja.append(["7866801", "HEM001", self.ayer, "Hemoglobina", 119, "g/L"])
        hoja.append(["7866801", "HEM001", self.ayer, "Leucocitos", 7500, "/mm3"])
        salida = BytesIO()
        libro.save(salida)
        datos = self._importar(SimpleUploadedFile("r.xlsx", salida.getvalue()))
        self.assertEqual(datos["resumen"]["creada"], 2, datos["filas"])
        valores = dict(ResultadoLaboratorio.objects.values_list("valor_referencia__parametro", "valor_numerico"))
        self.assertEqual(valores["Hemoglobina"], Decimal("11.9"))
        self.assertEqual(valores["Leucocitos"], Decimal("7.5"))

    def test_unidad_incompatible_es_error_de_la_fila(self):
        texto = f"CI,Código,Fecha,Parámetro,Valor,Unidad\n7866801,HEM001,{self.ayer},Hemoglobina,7.4,mmol/L\n"
        datos = self._importar(SimpleUploadedFile("r.csv", texto.encode(), content_type="text/csv"))
        self.assertEqual(datos["resumen"]["error"], 1)
        self.assertIn("no se puede convertir", datos["filas"][0]["errores"][0])
        self.assertFalse(ResultadoLaboratorio.objects.exists())
