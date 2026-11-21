"""Importación de laboratorio: CSV, mapeo de columnas y deshacer el lote.

Esperado vs obtenido. Fallos que previenen:
- un CSV con punto y coma o en Latin-1 que no se puede subir;
- un archivo del laboratorio con otros encabezados que obliga a copiar a mano a la plantilla;
- un archivo equivocado que ya no se puede retirar sin borrar resultado por resultado.
"""
import datetime
import json
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from laboratorio.models import ExamenLaboratorio, ImportacionLaboratorio, ResultadoLaboratorio
from pacientes.models import Paciente
from usuarios.models import Usuario

URL = "/api/laboratorios/examenes/importar-excel/"


def _csv(texto: str, codificacion="utf-8", nombre="resultados.csv"):
    return SimpleUploadedFile(nombre, texto.encode(codificacion), content_type="text/csv")


class ImportacionCsvTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("poblar_valores_referencia", stdout=StringIO())
        cls.lab = Usuario.objects.create_user(email="lab.csv@test.bo", nombre="Lia", apellido_paterno="Csv",
                                              password="clave-segura-123", rol="laboratorista")
        cls.recepcion = Usuario.objects.create_user(email="rec.csv@test.bo", nombre="Ro", apellido_paterno="Csv",
                                                    password="clave-segura-123", rol="recepcion")
        Paciente.objects.create(nombre="Rut", apellido_paterno="Csv", apellido_materno="X",
                                fecha_nacimiento=datetime.date(1994, 4, 4), genero="femenino", ci="7866701")

    def setUp(self):
        self.c = APIClient()
        self.c.force_authenticate(self.lab)
        self.ayer = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%d/%m/%Y")

    def test_csv_punto_y_coma_latin1_con_sinonimos(self):
        """ESPERADO: «Cédula;Código de examen;Fecha;Analito;Resultado» se reconoce solo, en Latin-1."""
        texto = (f"Cédula;Código de examen;Fecha;Analito;Resultado\n"
                 f"7866701;HEM001;{self.ayer};Hemoglobina;11,9\n7866701;HEM001;{self.ayer};Plaquetas;240000\n")
        r = self.c.post(URL, {"archivo": _csv(texto, "cp1252")}, format="multipart")
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertEqual(r.json()["resumen"]["valida"], 2)

    def test_encabezados_desconocidos_piden_mapeo_y_luego_importan(self):
        texto = f"Paciente,Prueba lab,Dia,Analito,Cifra\n7866701,HEM001,{self.ayer},Hemoglobina,12.1\n"
        r = self.c.post(URL, {"archivo": _csv(texto)}, format="multipart")
        self.assertTrue(r.json()["requiere_mapeo"])
        self.assertEqual(r.json()["encabezados"], ["Paciente", "Prueba lab", "Dia", "Analito", "Cifra"])
        self.assertEqual(r.json()["sugerido"], {"parametro": "Analito"})
        mapeo = {"ci": "Paciente", "codigo": "Prueba lab", "fecha": "Dia", "valor": "Cifra"}
        r = self.c.post(URL, {"archivo": _csv(texto), "mapeo": json.dumps(mapeo), "confirmar": "1"}, format="multipart")
        self.assertEqual(r.json()["resumen"]["creada"], 1, r.content[:300])

    def test_mapeo_a_columna_inexistente_400(self):
        r = self.c.post(URL, {"archivo": _csv("a,b\n1,2\n"), "mapeo": json.dumps({"ci": "Z"})}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_archivo_binario_no_valido_400(self):
        r = self.c.post(URL, {"archivo": SimpleUploadedFile("x.xlsx", b"\x00\x01\x02basura")}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_deshacer_lote_borra_todo_lo_que_creo(self):
        texto = (f"CI de la paciente,Código de examen,Fecha del resultado,Parámetro,Valor\n"
                 f"7866701,HEM001,{self.ayer},Hemoglobina,11.5\n7866701,HEM001,{self.ayer},Plaquetas,210000\n")
        r = self.c.post(URL, {"archivo": _csv(texto), "confirmar": "1"}, format="multipart")
        importacion_id = r.json()["importacion_id"]
        self.assertEqual(ResultadoLaboratorio.objects.count(), 2)
        corto = self.c.post(f"/api/laboratorios/importaciones/{importacion_id}/deshacer/", {"motivo": "mal"})
        self.assertEqual(corto.status_code, 400)
        r = self.c.post(f"/api/laboratorios/importaciones/{importacion_id}/deshacer/",
                        {"motivo": "Archivo de otro día, se subió por error"})
        self.assertEqual((r.status_code, r.json()["resultados_borrados"], r.json()["examenes_borrados"]), (200, 2, 1))
        self.assertEqual((ResultadoLaboratorio.objects.count(), ExamenLaboratorio.objects.count()), (0, 0))
        self.assertTrue(ImportacionLaboratorio.objects.get(pk=importacion_id).anulada)
        otra_vez = self.c.post(f"/api/laboratorios/importaciones/{importacion_id}/deshacer/",
                               {"motivo": "Archivo de otro día, se subió por error"})
        self.assertEqual(otra_vez.status_code, 409)

    def test_deshacer_no_borra_resultados_cargados_aparte(self):
        """ESPERADO: si el examen ya existía con otro resultado, se quita solo lo importado."""
        base = f"CI de la paciente,Código de examen,Fecha del resultado,Parámetro,Valor\n7866701,HEM001,{self.ayer},"
        self.c.post(URL, {"archivo": _csv(base + "Hemoglobina,11.5\n"), "confirmar": "1"}, format="multipart")
        r = self.c.post(URL, {"archivo": _csv(base + "Plaquetas,200000\n"), "confirmar": "1"}, format="multipart")
        self.c.post(f"/api/laboratorios/importaciones/{r.json()['importacion_id']}/deshacer/",
                    {"motivo": "Se cargó el valor equivocado"})
        self.assertEqual(ResultadoLaboratorio.objects.count(), 1)
        self.assertEqual(ExamenLaboratorio.objects.count(), 1)

    def test_recepcion_no_ve_importaciones(self):
        self.c.force_authenticate(self.recepcion)
        self.assertEqual(self.c.get("/api/laboratorios/importaciones/").status_code, 403)
