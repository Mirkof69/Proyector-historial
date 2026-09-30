"""La red de anomalías cerebrales, probada a través de la API.

Lo que se protege:
  · sin modelo, 503 (nunca un resultado inventado);
  · una imagen que no es una cabeza NO se clasifica (evita falsas alarmas);
  · la API da las MISMAS probabilidades que el script de entrenamiento sobre
    los cortes externos: si el preprocesado se desvía, la red sigue
    respondiendo sin error pero con otros números, y esto lo detecta.

Ejecutar (necesita torch y timm):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_anomalias_cerebrales.py -v
"""
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.ecografia_real import ARCHIVO_CEREBRO, ARCHIVO_PLANO, RedesEcografiaReal, redes
from app.main import app

AQUI = Path(__file__).resolve().parent
EXTERNAS = AQUI / "entrenamiento" / "patologias_cerebrales" / "salidas" / "predicciones_externas.csv"
REDES = AQUI / "entrenamiento" / "redes_ecografia_real"

hay_modelo = pytest.mark.skipif(
    not (redes.disponible(ARCHIVO_CEREBRO) and redes.disponible(ARCHIVO_PLANO)),
    reason="falta anomalias_cerebrales_fetales.pth o el de planos en trained_models/",
)
hay_datos = pytest.mark.skipif(not EXTERNAS.exists(), reason="no están las predicciones del entrenamiento")

cliente = TestClient(app)


def _png(imagen: Image.Image) -> bytes:
    buf = BytesIO()
    imagen.save(buf, "PNG")
    return buf.getvalue()


def test_sin_modelo_responde_503(monkeypatch, tmp_path):
    import app.routes as rutas
    monkeypatch.setattr(rutas, "redes_reales", RedesEcografiaReal(carpeta=tmp_path))
    r = cliente.post("/api/anomalias-cerebrales",
                     files={"file": ("a.png", _png(Image.new("L", (64, 64))), "image/png")})
    assert r.status_code == 503


def test_sin_modelo_el_estado_no_revienta(tmp_path):
    estado = RedesEcografiaReal(carpeta=tmp_path).estado()
    assert estado[ARCHIVO_CEREBRO] == {"disponible": False, "metricas_prueba": None, "sha256": None}


@hay_modelo
def test_respuesta_trae_metricas_medidas_y_uso():
    r = cliente.post("/api/anomalias-cerebrales",
                     files={"file": ("a.png", _png(Image.new("L", (300, 200), 40)), "image/png")})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    metricas = cuerpo["modelo"]["metricas_prueba"]
    assert "externa_falsos_positivos" in metricas and "solo_roboflow" in metricas
    assert "No es un diagnóstico" in cuerpo["uso"]


@hay_modelo
def test_un_femur_no_se_clasifica():
    """ESPERADO: aplicable=False y ninguna alarma sobre una imagen de fémur."""
    cat = pd.read_excel(REDES / "catalogo_imagenes.xlsx", sheet_name="Planos")
    fila = cat[(cat["plano"] == "fémur fetal") & (cat["particion"] == "prueba")].iloc[0]
    r = cliente.post("/api/anomalias-cerebrales",
                     files={"file": ("f.png", (REDES / fila["ruta"]).read_bytes(), "image/png")}).json()
    assert r["aplicable"] is False
    assert "alarma_anomalia" not in r


@hay_modelo
@hay_datos
def test_la_api_reproduce_las_probabilidades_del_entrenamiento():
    """ESPERADO: sobre 200 cortes externos, la P(anomalía) de la API difiere de
    la del script de entrenamiento menos de 0,03 de media, y la tasa de falsas
    alarmas es la misma ±2 puntos."""
    ext = pd.read_csv(EXTERNAS).sample(200, random_state=2026)
    diferencias, alarmas_api = [], []
    for _, fila in ext.iterrows():
        r = cliente.post("/api/anomalias-cerebrales",
                         files={"file": ("c.png", (AQUI / fila["clave"]).read_bytes(), "image/png")}).json()
        if not r["aplicable"]:
            # El clasificador de planos no vio cabeza: la API no da alarma.
            alarmas_api.append(False)
            continue
        diferencias.append(abs(r["probabilidad_anomalia"] - (1 - fila["p_normal"])))
        alarmas_api.append(r["alarma_anomalia"])
    print(f"\nDiferencia media {np.mean(diferencias):.4f} en {len(diferencias)} cortes; "
          f"alarmas API {np.mean(alarmas_api):.1%} vs entrenamiento {(1 - ext['p_normal'] >= 0.5).mean():.1%}")
    assert np.mean(diferencias) < 0.03
    assert np.mean(alarmas_api) <= (1 - ext["p_normal"] >= 0.5).mean() + 0.02


MANIFIESTO = AQUI / "entrenamiento" / "patologias_cerebrales" / "salidas" / "manifiesto.csv"
hay_manifiesto = pytest.mark.skipif(not MANIFIESTO.exists(), reason="no están las imágenes de Roboflow")


@hay_modelo
def test_imagenes_que_no_son_cabezas_casi_nunca_dan_alarma():
    """ESPERADO: ≤ 2 % de alarmas en 300 imágenes de prueba de abdomen, fémur,
    tórax, cuello uterino u otros planos (medido: 0,4 % en 3.199)."""
    cat = pd.read_excel(REDES / "catalogo_imagenes.xlsx", sheet_name="Planos")
    muestra = cat[(cat["particion"] == "prueba") & (cat["plano"] != "cerebro fetal")].sample(300, random_state=7)
    alarmas = 0
    for _, fila in muestra.iterrows():
        r = cliente.post("/api/anomalias-cerebrales",
                         files={"file": ("x.png", (REDES / fila["ruta"]).read_bytes(), "image/png")}).json()
        alarmas += bool(r.get("alarma_anomalia"))
    print(f"\nAlarmas en imágenes que no son cabezas: {alarmas}/300")
    assert alarmas <= 6


@hay_modelo
@hay_manifiesto
def test_las_cabezas_deformadas_por_la_anomalia_no_se_descartan():
    """El clasificador de planos no ve «cerebro» en el 40 % de las cabezas con
    anomalía. ESPERADO: aun así, ≥ 90 % de las 110 anomalías llegan a la red y
    dan alarma (medido: 104). Son imágenes con las que se entrenó la red de
    anomalías: esto prueba el filtro de planos, no la sensibilidad."""
    man = pd.read_csv(MANIFIESTO)
    anom = man[(man["fuente"] == "roboflow") & (man["familia"] != "normal")]
    anom = anom.assign(orig=~anom["ruta"].str.contains("_aug_")).sort_values("orig", ascending=False)
    unas = anom.groupby("grupo").first()
    avisadas = 0
    for ruta in unas["ruta"]:
        r = cliente.post("/api/anomalias-cerebrales",
                         files={"file": ("a.jpg", (AQUI / ruta).read_bytes(), "image/jpeg")}).json()
        avisadas += bool(r.get("alarma_anomalia"))
    print(f"\nAnomalías que llegan a la red y avisan: {avisadas}/{len(unas)}")
    assert avisadas >= 0.9 * len(unas)
