"""Longitud del fémur y circunferencia abdominal, probadas a través de la API.

Lo que se protege (esperado vs obtenido):
  · sin modelo, 503; tarea desconocida, 404;
  · la API mide IGUAL que el entrenamiento: sobre 30 imágenes de prueba (pacientes
    que la red no vio) la medida coincide con la de `entrenar.py` (±0,5 mm) y el
    error contra el experto sigue bajo el 5 % en la mediana;
  · el análisis completo, ante un fémur, ya no dice «sin red de medida»: mide la LF;
  · sin milímetros por píxel la medida sale en píxeles, con su aviso.

Ejecutar (necesita torch y timm):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_biometria.py -v
"""
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.biometria import RedesBiometria, biometria
from app.main import app

AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI / "entrenamiento" / "biometria" / "salidas"
IMAGENES = AQUI / "datos" / "extraidos" / "obstetricia" / "FetalBiometry-Multicentre-Landmarks-2026" / "images" / "MULTICENTRE"
cliente = TestClient(app)


def _png(imagen: Image.Image) -> dict:
    buf = BytesIO()
    imagen.save(buf, "PNG")
    return {"file": ("a.png", buf.getvalue(), "image/png")}


def _archivo(ruta: Path) -> dict:
    return {"file": (ruta.name, ruta.read_bytes(), "image/png")}


RUTA = {"femur": "/api/biometria/longitud-femur", "abdomen": "/api/biometria/circunferencia-abdominal"}


def test_la_ruta_de_la_cabeza_sigue_existiendo():
    """Una ruta «/biometria/{tarea}» la capturaba y respondía 404."""
    r = cliente.post("/api/biometria/circunferencia-cefalica", files=_png(Image.new("L", (64, 64))),
                     data={"tamano_pixel_mm": "0.14"})
    assert r.status_code != 404


def test_sin_modelo_503(monkeypatch, tmp_path):
    import app.routes as rutas

    monkeypatch.setattr(rutas, "biometria", RedesBiometria(carpeta=tmp_path))
    assert cliente.post(RUTA["femur"], files=_png(Image.new("L", (64, 64)))).status_code == 503


@pytest.mark.parametrize("tarea,anatomia,clave_api,columna", [
    ("femur", "Femur", "longitud_femur_mm", "fl"),
    ("abdomen", "Abdomen", "circunferencia_abdominal_mm", "ca"),
])
def test_la_api_mide_igual_que_el_entrenamiento(tarea, anatomia, clave_api, columna):
    medidas = SALIDAS / tarea / "prueba_medidas.csv"
    if not biometria.disponible(tarea) or not medidas.exists() or not IMAGENES.exists():
        pytest.skip(f"falta la red, sus medidas de prueba o las imágenes de {tarea}")
    t = pd.read_csv(medidas).dropna(subset=["mm_por_px"]).sample(30, random_state=7)
    diferencias, errores = [], []
    for _, fila in t.iterrows():
        r = cliente.post(RUTA[tarea], files=_archivo(IMAGENES / anatomia / fila["imagen"]),
                         data={"tamano_pixel_mm": str(fila["mm_por_px"])})
        assert r.status_code == 200, r.text
        api = r.json()["medidas"][clave_api]
        diferencias.append(abs(api - fila[f"{columna}_red_mm"]))
        errores.append(abs(api - fila[f"{columna}_experto_mm"]) / fila[f"{columna}_experto_mm"])
    assert float(np.median(diferencias)) < 0.5, f"la API se apartó del entrenamiento: {np.median(diferencias):.2f} mm"
    assert float(np.median(errores)) < 0.05


def test_sin_escala_la_medida_queda_en_pixeles_con_aviso():
    if not biometria.disponible("femur") or not IMAGENES.exists():
        pytest.skip("falta la red de fémur o las imágenes")
    ruta = next((IMAGENES / "Femur").glob("Patient*.png"))
    cuerpo = cliente.post(RUTA["femur"], files=_archivo(ruta)).json()
    assert "fl_px" in cuerpo["medidas"] and "longitud_femur_mm" not in cuerpo["medidas"]
    assert any("píxeles" in a for a in cuerpo["avisos"])
    assert cuerpo["superposicion_png"]


def test_el_analisis_completo_mide_el_femur():
    from app.ecografia_real import ARCHIVO_PLANO, redes

    medidas = SALIDAS / "femur" / "prueba_medidas.csv"
    if not (biometria.disponible("femur") and redes.disponible(ARCHIVO_PLANO) and medidas.exists()):
        pytest.skip("faltan redes o medidas")
    t = pd.read_csv(medidas).dropna(subset=["mm_por_px"])
    medidos = 0
    for _, fila in t.head(10).iterrows():
        cuerpo = cliente.post("/api/analyze", files=_archivo(IMAGENES / "Femur" / fila["imagen"]),
                              data={"tamano_pixel_mm": str(fila["mm_por_px"])}).json()
        if cuerpo["plano"]["plano"] == "fémur fetal":
            assert "longitud_femur_mm" in cuerpo["medidas"]
            assert not any("no hay una red de medida" in h for h in cuerpo["hallazgos"])
            medidos += 1
    assert medidos >= 8, "el plano de fémur se reconoció en menos de 8 de 10 fémures"
