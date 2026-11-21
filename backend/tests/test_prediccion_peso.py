"""El modelo de peso al nacer servido por la API: POST /api/ia/prediccion-peso/.

Se entrena un modelo pequeño en una carpeta temporal para no depender del que
haya en `modelos-ia/tabulares/`. Lo que se comprueba es el servicio, no la calidad del
modelo (eso lo mide `entrenar_modelo_peso` y el notebook).
"""
import datetime
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from ia_medica.ml.caracteristicas_peso import CARACTERISTICAS

URL = "/api/ia/prediccion-peso/"


def _modelo_de_juguete(carpeta: Path, version="9.9.9", columnas=None):
    """Una regresión lineal entrenada con filas del simulador, guardada igual
    que la guarda `entrenar_modelo_peso`."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline

    from ia_medica.ml.entrenamiento_peso import guardar

    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(60, len(CARACTERISTICAS))), columns=list(CARACTERISTICAS))
    X["peso_hadlock_g"] = rng.uniform(2500, 4000, 60)
    y = X["peso_hadlock_g"] * 0.95 + rng.normal(0, 50, 60)
    modelo = make_pipeline(SimpleImputer(strategy="median"), Ridge()).fit(X, y)
    destino = carpeta / "peso_nacimiento" / version
    guardar(destino, modelo, {
        "version": version, "algoritmo": "ridge", "descripcion": "Ridge",
        "entrenado_con_datos_sinteticos": True,
        "comparativa": {"ridge": {"mae_g": {"media": 183.0}, "r2": {"media": 0.836}}},
    })
    if columnas is not None:
        (destino / "columnas.json").write_text(json.dumps(columnas), encoding="utf-8")
    return modelo


class PrediccionPesoTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        from ecografias.models import BiometriaFetal, Ecografia
        from embarazos.models import Embarazo
        from pacientes.models import Paciente
        from usuarios.models import Usuario

        cls.medico = Usuario.objects.create_user(
            email="dr.peso@test.bo", nombre="Ana", apellido_paterno="Peso",
            password="clave-de-prueba-123", rol="medico")
        cls.enfermera = Usuario.objects.create_user(
            email="enf.peso@test.bo", nombre="Eva", apellido_paterno="Peso",
            password="clave-de-prueba-123", rol="enfermera")

        def crear(ci, tipo="simple", semanas=38, con_biometria=True):
            paciente = Paciente.objects.create(
                nombre="Madre", apellido_paterno="Peso", apellido_materno="Test",
                fecha_nacimiento=datetime.date(1992, 3, 1), genero="femenino", ci=ci)
            fum = datetime.date(2025, 1, 1)
            embarazo = Embarazo.objects.create(
                paciente=paciente, numero_gesta=1, numero_para=0, numero_abortos=0,
                fecha_ultima_menstruacion=fum, tipo_embarazo=tipo, medico_responsable=cls.medico,
                peso_pregestacional=60, talla_materna=160)
            eco = Ecografia.objects.create(
                paciente=paciente, embarazo=embarazo,
                fecha_ecografia=fum + datetime.timedelta(weeks=semanas),
                edad_gestacional_semanas=semanas, edad_gestacional_dias=0)
            if con_biometria:
                BiometriaFetal.objects.create(
                    ecografia=eco, diametro_biparietal=92, circunferencia_cefalica=330,
                    circunferencia_abdominal=335, longitud_femur=71)
            return eco

        cls.eco = crear("8100001")
        cls.eco_gemelar = crear("8100002", tipo="gemelar")
        cls.eco_sin_medidas = crear("8100003", con_biometria=False)
        cls.eco_temprana = crear("8100004", semanas=16)

    def setUp(self):
        from ia_medica.ml import servicio_peso

        self.carpeta = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.carpeta, ignore_errors=True)
        servicio_peso.cargar.cache_clear()
        self.addCleanup(servicio_peso.cargar.cache_clear)
        self.cliente = APIClient()
        self.cliente.force_authenticate(self.medico)

    def _post(self, eco, **extra):
        with override_settings(ML_MODELOS_DIR=self.carpeta):
            return self.cliente.post(URL, {"ecografia_id": eco.pk, **extra}, format="json")

    def test_predice_y_trae_hadlock_al_lado(self):
        """ESPERADO: 200 con peso, clase, margen, Hadlock y la advertencia de datos simulados."""
        _modelo_de_juguete(self.carpeta)
        r = self._post(self.eco, semanas_objetivo=39)
        self.assertEqual(r.status_code, 200, r.content)
        d = r.json()
        self.assertTrue(1500 < d["peso_previsto_g"] < 5000, d)
        self.assertIn(d["clase"], ("bajo_peso", "normal", "macrosomia"))
        self.assertEqual(d["margen_g"], 183)
        self.assertIsNotNone(d["peso_hadlock_proyectado_g"])
        self.assertTrue(any("SIMULADOS" in a for a in d["advertencias"]))

    def test_lo_que_se_sirve_es_lo_que_se_entreno(self):
        """ESPERADO: la predicción de la API = modelo.predict sobre las mismas
        características que construye el dataset. Si el servicio calculara una
        variable a su manera, esto fallaría aunque el número pareciera sensato."""
        from ia_medica.ml.caracteristicas_peso import construir_vector
        from ia_medica.ml.dataset_peso import caracteristicas_de

        modelo = _modelo_de_juguete(self.carpeta)
        esperado = caracteristicas_de(
            self.eco, embarazo=self.eco.embarazo, paciente=self.eco.paciente,
            antecedentes={"diabetes": 0, "hipertension": 0, "preeclampsia_previa": 0,
                          "diabetes_gestacional_previa": 0},
            controles=[], eg_al_nacer=39.0)
        fila = pd.DataFrame([construir_vector(esperado)], columns=list(CARACTERISTICAS))
        r = self._post(self.eco, semanas_objetivo=39)
        self.assertEqual(r.json()["peso_previsto_g"], int(round(float(modelo.predict(fila)[0]))))

    def test_enfermeria_no_puede(self):
        _modelo_de_juguete(self.carpeta)
        self.cliente.force_authenticate(self.enfermera)
        self.assertEqual(self._post(self.eco).status_code, 403)

    def test_sin_modelo_entrenado_responde_409_sin_inventar(self):
        r = self._post(self.eco)
        self.assertEqual(r.status_code, 409)
        self.assertIn("entrenar_modelo_peso", r.json()["error"])
        self.assertNotIn("peso_previsto_g", r.json())

    def test_columnas_distintas_se_niega_a_servir(self):
        """ESPERADO: 409. Un modelo entrenado con otras variables daría números
        plausibles y equivocados; el cargador tiene que negarse."""
        _modelo_de_juguete(self.carpeta, columnas=["otra", "lista"])
        r = self._post(self.eco)
        self.assertEqual(r.status_code, 409)
        self.assertIn("otras variables", r.json()["error"])

    def test_gemelar_sin_biometria_y_temprana_dan_409_con_motivo(self):
        _modelo_de_juguete(self.carpeta)
        for eco, texto in [(self.eco_gemelar, "múltiple"), (self.eco_sin_medidas, "cuatro medidas"),
                           (self.eco_temprana, "20 o más")]:
            r = self._post(eco)
            self.assertEqual(r.status_code, 409, eco)
            self.assertIn(texto, r.json()["error"])

    def test_semana_fuera_de_rango_es_400(self):
        _modelo_de_juguete(self.carpeta)
        self.assertEqual(self._post(self.eco, semanas_objetivo=50).status_code, 400)

    def test_usa_la_version_mas_alta(self):
        """ESPERADO: 1.10.0 gana a 1.9.0 (orden numérico, no alfabético)."""
        _modelo_de_juguete(self.carpeta, version="1.9.0")
        _modelo_de_juguete(self.carpeta, version="1.10.0")
        self.assertEqual(self._post(self.eco).json()["modelo"]["version"], "1.10.0")
