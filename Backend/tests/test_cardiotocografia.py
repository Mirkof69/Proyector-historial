"""Clasificador supervisado de cardiotocografía: datos, entrenamiento honesto y API.

El entrenamiento real (2.113 registros, ~30 s) se ejecuta una vez por clase en
una carpeta temporal: así se comprueba la MÉTRICA de verdad, no un modelo de
juguete. Esperado vs obtenido en cada prueba.
"""
import datetime
import shutil
import tempfile
from pathlib import Path

import numpy as np
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from ia_medica.ml import cardiotocografia as ctg

URL = "/api/ia/cardiotocografia/"

# Registro 1 del dataset (consenso: patológica) y uno normal típico.
NORMAL = {"linea_base": 132, "aceleraciones": 0.006, "movimientos_fetales": 0, "contracciones": 0.006,
          "desaceleraciones_leves": 0.003, "desaceleraciones_severas": 0, "desaceleraciones_prolongadas": 0,
          "vcp_anormal_pct": 17, "vcp_media": 2.1, "vlp_anormal_pct": 0, "vlp_media": 10.4,
          "histograma_ancho": 130, "histograma_minimo": 68, "histograma_maximo": 198, "histograma_picos": 6,
          "histograma_ceros": 1, "histograma_moda": 141, "histograma_media": 136, "histograma_mediana": 140,
          "histograma_varianza": 12, "histograma_tendencia": 0}


class DatosTest(TestCase):
    def test_quita_duplicados_antes_de_partir(self):
        """ESPERADO: 2.126 filas − 13 duplicadas exactas = 2.113, sin duplicados."""
        X, y, quitados = ctg.cargar_datos()
        self.assertEqual((len(X), quitados), (2113, 13))
        self.assertFalse(X.assign(y=y).duplicated().any())
        self.assertEqual(sorted(np.unique(y)), [0, 1, 2])


class EntrenamientoYApiTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carpeta = Path(tempfile.mkdtemp())
        cls.ajustes = override_settings(ML_MODELOS_DIR=cls.carpeta)
        cls.ajustes.enable()
        ctg.cargar.cache_clear()
        cls.modelo, cls.ficha = ctg.entrenar(registro=lambda *_: None)
        ctg.guardar(cls.modelo, cls.ficha)

    @classmethod
    def tearDownClass(cls):
        ctg.cargar.cache_clear()
        cls.ajustes.disable()
        shutil.rmtree(cls.carpeta, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        from usuarios.models import Usuario

        cls.medico = Usuario.objects.create_user(email="dr.ctg@test.bo", nombre="Ana", apellido_paterno="Ctg",
                                                 password="clave-de-prueba-123", rol="medico")
        cls.recepcion = Usuario.objects.create_user(email="rec.ctg@test.bo", nombre="Eva", apellido_paterno="Ctg",
                                                    password="clave-de-prueba-123", rol="recepcion")
        cls.enfermera = Usuario.objects.create_user(email="enf.ctg@test.bo", nombre="Iris", apellido_paterno="Ctg",
                                                    password="clave-de-prueba-123", rol="enfermera")
        from embarazos.models import Embarazo
        from pacientes.models import Paciente

        cls.paciente = Paciente.objects.create(nombre="Rosa", apellido_paterno="Trazado", ci="7700401",
                                               genero="femenino", fecha_nacimiento=datetime.date(1994, 3, 3))
        cls.embarazo = Embarazo.objects.create(
            paciente=cls.paciente, numero_gesta=1, numero_para=0, tipo_embarazo="simple", riesgo_embarazo="bajo",
            medico_responsable=cls.medico, fecha_ultima_menstruacion=timezone.localdate() - datetime.timedelta(weeks=36))
        cls.otra = Paciente.objects.create(nombre="Nora", apellido_paterno="Otra", ci="7700402",
                                           genero="femenino", fecha_nacimiento=datetime.date(1990, 1, 1))

    def setUp(self):
        self.api = APIClient()
        self.api.force_authenticate(self.medico)

    def test_metricas_reales_en_prueba(self):
        """ESPERADO: en 423 registros nunca vistos, exactitud ≥ 0,90 y sensibilidad
        para «patológica» ≥ 0,85; y supera al suelo (decir siempre «normal»)."""
        p = self.ficha["prueba"]
        self.assertEqual(self.ficha["registros_prueba"], 423)
        self.assertGreaterEqual(p["exactitud"], 0.90)
        self.assertGreaterEqual(p["sensibilidad"]["patologica"], 0.85)
        suelo = self.ficha["comparativa_validacion_cruzada"]["constante_normal"]["cv"]["exactitud"]
        self.assertGreater(p["exactitud"], suelo + 0.1)

    def test_elige_con_validacion_cruzada_no_con_la_prueba(self):
        """ESPERADO: el algoritmo elegido es el de mejor F1 macro en validación
        cruzada (o su versión de 11 variables si empata a menos de 0,01)."""
        comp = {k: v for k, v in self.ficha["comparativa_validacion_cruzada"].items() if "__" in k}
        mejor = max(comp, key=lambda k: comp[k]["cv"]["f1_macro"])
        alternativa = mejor.split("__")[0] + "__nucleo_11"
        self.assertIn(self.ficha["algoritmo"], {mejor, alternativa})

    def test_get_dice_que_pedir_y_cuanto_acierta(self):
        r = self.api.get(URL)
        self.assertEqual(r.status_code, 200)
        claves = [v["clave"] for v in r.json()["variables"]]
        self.assertIn("linea_base", claves)
        self.assertGreaterEqual(r.json()["modelo"]["prueba"]["exactitud"], 0.90)

    def test_clasifica_un_registro_normal(self):
        """ESPERADO: un trazado con línea de base 132, aceleraciones y buena
        variabilidad sale «normal», con probabilidades que suman 1."""
        r = self.api.post(URL, NORMAL, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()["clase"], "normal")
        self.assertAlmostEqual(sum(r.json()["probabilidades"].values()), 1.0, places=3)
        self.assertTrue(r.json()["advertencias"])

    def test_registro_patologico_del_dataset(self):
        """ESPERADO: un registro que los tres obstetras clasificaron patológico
        (bradicardia sin variabilidad y con desaceleraciones prolongadas) no sale «normal»."""
        X, y, _ = ctg.cargar_datos()
        fila = X[y == 2].iloc[0]
        datos = {ctg.VARIABLES[c][0]: float(fila[c]) for c in ctg.VARIABLES}
        r = self.api.post(URL, datos, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(r.json()["clase"], "normal")

    def test_faltan_datos_409_sin_clase(self):
        r = self.api.post(URL, {"linea_base": 130}, format="json")
        self.assertEqual(r.status_code, 409)
        self.assertNotIn("clase", r.json())
        self.assertIn("Faltan datos", r.json()["error"])

    def test_valor_fuera_de_rango_409(self):
        r = self.api.post(URL, NORMAL | {"linea_base": 400}, format="json")
        self.assertEqual(r.status_code, 409)
        self.assertIn("fuera de rango", r.json()["error"])

    def test_texto_en_vez_de_numero_400(self):
        r = self.api.post(URL, NORMAL | {"linea_base": "ciento treinta"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_recepcion_no_puede(self):
        self.api.force_authenticate(self.recepcion)
        self.assertEqual(self.api.post(URL, NORMAL, format="json").status_code, 403)

    def test_queda_auditado(self):
        from auditoria.models import RegistroAuditoria

        self.api.post(URL, NORMAL, format="json")
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="Cardiotocografia").exists())


    def test_sin_paciente_clasifica_pero_no_guarda(self):
        """ESPERADO: sin paciente el resultado llega igual, con guardado=false y ninguna fila nueva."""
        from ia_medica.models import RegistroCardiotocografia

        r = self.api.post(URL, NORMAL, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["guardado"])
        self.assertFalse(RegistroCardiotocografia.objects.exists())

    def test_con_paciente_queda_en_su_historial(self):
        """ESPERADO: con paciente se guarda una fila con sus valores, la clase, la semana del
        embarazo activo (36) y quién la clasificó; y aparece solo en su lista."""
        from ia_medica.models import RegistroCardiotocografia

        r = self.api.post(URL, NORMAL | {"paciente_id": self.paciente.id}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.json()["guardado"])
        fila = RegistroCardiotocografia.objects.get(pk=r.json()["registro_id"])
        self.assertEqual((fila.paciente_id, fila.embarazo_id, fila.semana_gestacional, fila.clase),
                         (self.paciente.id, self.embarazo.id, 36, r.json()["clase"]))
        self.assertEqual(fila.valores["linea_base"], 132)
        self.assertNotIn("paciente_id", fila.valores)
        self.assertEqual(fila.realizado_por, self.medico)

        lista = self.api.get(f"{URL[:-1]}s/", {"paciente_id": self.paciente.id}).json()
        self.assertEqual(lista["count"], 1)
        self.assertEqual(lista["results"][0]["paciente_nombre"], self.paciente.nombre_completo)
        self.assertEqual(lista["results"][0]["realizado_por_nombre"], self.medico.nombre_completo)
        self.assertEqual(lista["results"][0]["valores_etiquetados"][0],
                         {"clave": "linea_base", "etiqueta": "Línea de base de la FCF", "unidad": "lpm", "valor": 132.0})
        self.assertEqual(self.api.get(f"{URL[:-1]}s/", {"paciente_id": self.otra.id}).json()["count"], 0)

    def test_busca_por_paciente_y_filtra_por_clase(self):
        """ESPERADO: la lista general encuentra por apellido de la paciente (campo cifrado) y por clase."""
        self.api.post(URL, NORMAL | {"paciente_id": self.paciente.id}, format="json")
        self.api.post(URL, NORMAL | {"paciente_id": self.otra.id}, format="json")
        lista = f"{URL[:-1]}s/"
        self.assertEqual(self.api.get(lista).json()["count"], 2)
        encontrados = self.api.get(lista, {"search": "Trazado"}).json()
        self.assertEqual([f["paciente"] for f in encontrados["results"]], [self.paciente.id])
        self.assertEqual(self.api.get(lista, {"clase": "patologica"}).json()["count"], 0)

    def test_paciente_inexistente_no_guarda(self):
        r = self.api.post(URL, NORMAL | {"paciente_id": 999999}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.json()["guardado"])

    def test_enfermeria_lee_y_recepcion_no(self):
        """ESPERADO: enfermería ve las cardiotocografías de la ficha (no clasifica); recepción, nada."""
        self.api.post(URL, NORMAL | {"paciente_id": self.paciente.id}, format="json")
        lista = f"{URL[:-1]}s/"
        self.api.force_authenticate(self.enfermera)
        self.assertEqual(self.api.get(lista).status_code, 200)
        self.assertEqual(self.api.post(URL, NORMAL, format="json").status_code, 403)
        self.api.force_authenticate(self.recepcion)
        self.assertEqual(self.api.get(lista).status_code, 403)

    def test_la_lista_no_se_modifica_por_la_api(self):
        self.api.post(URL, NORMAL | {"paciente_id": self.paciente.id}, format="json")
        from ia_medica.models import RegistroCardiotocografia

        fila = RegistroCardiotocografia.objects.get()
        self.assertEqual(self.api.delete(f"{URL[:-1]}s/{fila.id}/").status_code, 405)
        self.assertEqual(self.api.patch(f"{URL[:-1]}s/{fila.id}/", {"clase": "normal"}, format="json").status_code, 405)


class SinModeloTest(TestCase):
    def test_sin_modelo_responde_409(self):
        from usuarios.models import Usuario

        medico = Usuario.objects.create_user(email="dr.ctg2@test.bo", nombre="Ana", apellido_paterno="Ctg",
                                             password="clave-de-prueba-123", rol="medico")
        with tempfile.TemporaryDirectory() as vacia, override_settings(ML_MODELOS_DIR=Path(vacia)):
            ctg.cargar.cache_clear()
            api = APIClient()
            api.force_authenticate(medico)
            r = api.post(URL, NORMAL, format="json")
            ctg.cargar.cache_clear()
        self.assertEqual(r.status_code, 409)
        self.assertIn("entrenar_modelo_ctg", r.json()["error"])
