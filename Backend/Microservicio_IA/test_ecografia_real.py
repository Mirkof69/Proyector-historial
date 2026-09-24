"""Las dos redes entrenadas con ecografías reales, probadas a través de la API.

Lo importante: el endpoint tiene que dar el MISMO resultado que el notebook.
Si el preprocesado de aquí se desvía del de entrenamiento (otro relleno, otra
normalización), la red sigue respondiendo sin error, pero con números peores.
Por eso se pasa el conjunto de prueba entero por la API y se exige el error
medido en el notebook.

Ejecutar (necesita torch y timm):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_ecografia_real.py -v
"""
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import ecografia_real
from app.ecografia_real import (
    ARCHIVO_HC,
    ARCHIVO_PLANO,
    RedesEcografiaReal,
    edad_gestacional_hadlock_1984,
    redes,
)
from app.main import app

DATOS = Path(__file__).resolve().parents[2] / "datos_ecografia_reales"
CATALOGO = DATOS / "catalogo_imagenes.xlsx"

hay_modelos = pytest.mark.skipif(
    not (redes.disponible(ARCHIVO_HC) and redes.disponible(ARCHIVO_PLANO)),
    reason="faltan los .pth en trained_models/",
)
hay_imagenes = pytest.mark.skipif(not CATALOGO.exists(), reason="no están las imágenes reales")

# Sin `with`: no se dispara el lifespan, que cargaría la EfficientNet-B4.
cliente = TestClient(app)


def _png(ruta: Path) -> bytes:
    return ruta.read_bytes()


def _prueba(hoja: str) -> pd.DataFrame:
    d = pd.read_excel(CATALOGO, sheet_name=hoja)
    return d[d["particion"] == "prueba"].reset_index(drop=True)


# ─────────────────────────── fórmula ───────────────────────────


def test_hadlock_1984_valores_de_la_tabla_publicada():
    """HC 175 mm ≈ 20 semanas y HC 330 mm ≈ 37,5 semanas (Hadlock 1984)."""
    assert edad_gestacional_hadlock_1984(175) == pytest.approx(20.0, abs=0.3)
    assert edad_gestacional_hadlock_1984(330) == pytest.approx(37.6, abs=0.5)


# ─────────────────────────── entradas malas ───────────────────────────


def test_extension_no_permitida_da_400():
    r = cliente.post("/api/plano-anatomico", files={"file": ("a.txt", b"hola", "text/plain")})
    assert r.status_code == 400


def test_archivo_que_no_es_imagen_da_400_no_500():
    r = cliente.post("/api/plano-anatomico", files={"file": ("a.png", b"no soy png", "image/png")})
    assert r.status_code == 400


def test_sin_tamano_de_pixel_da_422():
    r = cliente.post("/api/biometria/circunferencia-cefalica",
                     files={"file": ("a.png", b"x", "image/png")})
    assert r.status_code == 422


@hay_modelos
def test_tamano_de_pixel_absurdo_da_400():
    buf = BytesIO()
    Image.new("L", (100, 80), 30).save(buf, "PNG")
    r = cliente.post("/api/biometria/circunferencia-cefalica",
                     files={"file": ("a.png", buf.getvalue(), "image/png")},
                     data={"tamano_pixel_mm": "5"})
    assert r.status_code == 400
    assert "tamano_pixel_mm" in r.json()["detail"]


def test_sin_modelo_responde_503_y_no_inventa(monkeypatch, tmp_path):
    monkeypatch.setattr(ecografia_real, "redes", RedesEcografiaReal(carpeta=tmp_path))
    import app.routes as rutas
    monkeypatch.setattr(rutas, "redes_reales", RedesEcografiaReal(carpeta=tmp_path))
    buf = BytesIO()
    Image.new("L", (64, 64)).save(buf, "PNG")
    r = cliente.post("/api/plano-anatomico", files={"file": ("a.png", buf.getvalue(), "image/png")})
    assert r.status_code == 503
    assert "redes_ecografia_real.ipynb" in r.json()["detail"]


# ─────────────────────────── resultados reales ───────────────────────────


@hay_modelos
@hay_imagenes
def test_circunferencia_por_la_api_reproduce_el_error_del_notebook():
    """ESPERADO: error medio ≈ 7,0 mm sobre las 146 imágenes de prueba, como
    en el notebook. Se admite hasta 8 mm (la GPU no es bit a bit determinista)."""
    prueba = _prueba("HC18")
    errores = []
    for _, fila in prueba.iterrows():
        r = cliente.post(
            "/api/biometria/circunferencia-cefalica",
            files={"file": (fila["archivo"], _png(DATOS / fila["ruta"]), "image/png")},
            data={"tamano_pixel_mm": str(fila["tamano_pixel_mm"])},
        )
        assert r.status_code == 200, r.text
        errores.append(abs(r.json()["circunferencia_cefalica_mm"] - fila["circunferencia_cefalica_mm"]))
    mae = float(np.mean(errores))
    print(f"\nMAE por la API: {mae:.2f} mm en {len(errores)} imágenes")
    assert mae < 8.0


@hay_modelos
@hay_imagenes
def test_respuesta_de_circunferencia_trae_edad_y_plano():
    fila = _prueba("HC18").iloc[0]
    r = cliente.post(
        "/api/biometria/circunferencia-cefalica",
        files={"file": (fila["archivo"], _png(DATOS / fila["ruta"]), "image/png")},
        data={"tamano_pixel_mm": str(fila["tamano_pixel_mm"])},
    ).json()
    assert r["plano_detectado"] is not None
    if r["plano_detectado"] != "cerebro fetal":
        assert any("falsa alarma" in a for a in r["avisos"])
    assert 10 <= r["edad_gestacional_semanas"] <= 42
    assert r["modelo"]["metricas_prueba"]["madres_prueba"] == 117


@hay_modelos
@hay_imagenes
def test_plano_por_la_api_acierta_como_en_el_notebook():
    """ESPERADO: ≈ 92,7% de aciertos. Muestra de 600 imágenes de prueba al
    azar (semilla fija); se exige ≥ 89%."""
    prueba = _prueba("Planos").sample(600, random_state=2026)
    aciertos = 0
    for _, fila in prueba.iterrows():
        r = cliente.post("/api/plano-anatomico",
                         files={"file": (Path(fila["ruta"]).name, _png(DATOS / fila["ruta"]), "image/png")})
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        assert sum(cuerpo["probabilidades"].values()) == pytest.approx(1, abs=0.01)
        aciertos += cuerpo["plano"] == fila["plano"]
    exactitud = aciertos / len(prueba)
    print(f"\nExactitud por la API: {exactitud:.1%}")
    assert exactitud >= 0.89


@hay_modelos
@hay_imagenes
def test_un_femur_no_se_mide_como_cabeza_sin_avisar():
    """Si mandan una imagen de fémur a medir la cabeza, la respuesta avisa."""
    planos = _prueba("Planos")
    fila = planos[planos["plano"] == "fémur fetal"].iloc[0]
    r = cliente.post(
        "/api/biometria/circunferencia-cefalica",
        files={"file": ("f.png", _png(DATOS / fila["ruta"]), "image/png")},
        data={"tamano_pixel_mm": "0.14"},
    ).json()
    if r["plano_detectado"] != "cerebro fetal":
        assert any("no un corte de la cabeza" in a for a in r["avisos"])
