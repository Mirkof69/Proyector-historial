"""Redes de segmentación y análisis completo, probados a través de la API.

Lo que se protege (esperado vs obtenido):
  · sin modelo, 503: nunca un resultado inventado;
  · la API mide IGUAL que el entrenamiento: sobre 40 cabezas de HC18 (otro
    hospital) la circunferencia por la API tiene el mismo error que midió
    `entrenar.py` (si el preprocesado se desvía, la red sigue respondiendo
    sin error pero con otros números, y esto lo detecta);
  · el análisis completo elige la red según el plano y lleva sus métricas;
  · la B4 ya no existe: sus rutas dan 404.

Ejecutar (necesita torch y timm):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_segmentacion.py -v
"""
import base64
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.ecografia_real import ARCHIVO_PLANO, redes
from app.main import app
from app.segmentacion import RedesSegmentacion, edad_por_dbp_hadlock_1982, segmentacion

AQUI = Path(__file__).resolve().parent
EXTERNA = AQUI / "entrenamiento" / "segmentacion" / "salidas" / "cabeza" / "externa_hc18.csv"
HC18 = AQUI / "entrenamiento" / "redes_ecografia_real" / "imagenes" / "hc18"
FOCUS = AQUI / "entrenamiento" / "segmentacion" / "catalogos" / "torax.csv"

hay_cabeza = pytest.mark.skipif(not segmentacion.disponible("cabeza"), reason="falta segmentacion_cabeza.pth")
hay_todo = pytest.mark.skipif(
    not all(segmentacion.disponible(t) for t in ("cabeza", "torax", "abdomen")) or not redes.disponible(ARCHIVO_PLANO),
    reason="faltan redes en trained_models/")
cliente = TestClient(app)


def _png(imagen: Image.Image) -> bytes:
    buf = BytesIO()
    imagen.save(buf, "PNG")
    return buf.getvalue()


def test_formula_dbp_hadlock():
    """ESPERADO: DBP de 90 mm ≈ 36,5 semanas (tabla de Hadlock 1982)."""
    assert abs(edad_por_dbp_hadlock_1982(90) - 36.4) < 0.3


def test_sin_modelo_responde_503(monkeypatch, tmp_path):
    import app.routes as rutas
    monkeypatch.setattr(rutas, "segmentacion", RedesSegmentacion(carpeta=tmp_path))
    r = cliente.post("/api/segmentacion/cabeza", files={"file": ("a.png", _png(Image.new("L", (64, 64))), "image/png")})
    assert r.status_code == 503


def test_tarea_desconocida_404():
    r = cliente.post("/api/segmentacion/rodilla", files={"file": ("a.png", _png(Image.new("L", (64, 64))), "image/png")})
    assert r.status_code == 404


@pytest.mark.parametrize("ruta", ["/api/detect-pathologies", "/api/detect-anomalies", "/api/classify"])
def test_las_rutas_de_la_b4_ya_no_existen(ruta):
    r = cliente.post(ruta, files={"file": ("a.png", _png(Image.new("L", (64, 64))), "image/png")})
    assert r.status_code == 404


@hay_cabeza
@pytest.mark.skipif(not EXTERNA.exists(), reason="no está la prueba externa del entrenamiento")
def test_la_api_mide_igual_que_el_entrenamiento_en_hc18():
    """40 cabezas de HC18: la HC por la API coincide con la del entrenamiento (±0,5 mm)
    y el error contra el ecografista se mantiene por debajo del 5 %."""
    externa = pd.read_csv(EXTERNA).dropna().sample(40, random_state=7)
    catalogo = pd.read_excel(AQUI / "entrenamiento" / "redes_ecografia_real" / "catalogo_imagenes.xlsx",
                             sheet_name="HC18").set_index("archivo")
    diferencias, errores_relativos = [], []
    for _, fila in externa.iterrows():
        tam = float(catalogo.loc[fila["archivo"], "tamano_pixel_mm"])
        with open(HC18 / fila["archivo"], "rb") as f:
            r = cliente.post("/api/segmentacion/cabeza", files={"file": (fila["archivo"], f.read(), "image/png")},
                             data={"tamano_pixel_mm": tam})
        assert r.status_code == 200
        hc = r.json()["medidas"]["circunferencia_cefalica_mm"]
        diferencias.append(abs(hc - fila["hc_red_mm"]))
        errores_relativos.append(abs(hc - fila["hc_ecografista_mm"]) / fila["hc_ecografista_mm"])
    assert max(diferencias) < 0.5, f"la API se desvía del entrenamiento hasta {max(diferencias):.2f} mm"
    assert np.mean(errores_relativos) < 0.05


@hay_cabeza
def test_sin_tamano_de_pixel_no_da_milimetros():
    with open(next(HC18.glob("*.png")), "rb") as f:
        r = cliente.post("/api/segmentacion/cabeza", files={"file": ("c.png", f.read(), "image/png")})
    cuerpo = r.json()
    assert "circunferencia_cefalica_mm" not in cuerpo["medidas"]
    assert any("tamaño del píxel" in a for a in cuerpo["avisos"])
    assert Image.open(BytesIO(base64.b64decode(cuerpo["superposicion_png"]))).size[0] > 0


@hay_todo
@pytest.mark.skipif(not FOCUS.exists(), reason="no está el catálogo de FOCUS")
def test_torax_de_prueba_da_indice_en_rango_y_metricas():
    fila = pd.read_csv(FOCUS).query("particion == 'prueba'").iloc[0]
    with open(AQUI / fila["imagen"], "rb") as f:
        r = cliente.post("/api/segmentacion/torax", files={"file": ("t.png", f.read(), "image/png")})
    m = r.json()["medidas"]
    assert 0.15 < m["indice_cardiotoracico_areas"] < 0.45
    assert r.json()["modelo"]["metricas_prueba"]["dice_prueba_medio"] > 0.9


@hay_todo
def test_analisis_completo_de_una_cabeza():
    """ESPERADO: plano cerebro → medidas de cabeza con margen, red de anomalías
    aplicada, varias redes declaradas con sus métricas, informe en texto."""
    archivo = next(HC18.glob("*_HC.png"))
    with open(archivo, "rb") as f:
        r = cliente.post("/api/analyze", files={"file": (archivo.name, f.read(), "image/png")},
                         data={"tamano_pixel_mm": 0.15})
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "success" and d["version_flujo"] == "2.0"
    if d["plano"]["plano"] == "cerebro fetal":
        assert "circunferencia_cefalica_mm" in d["medidas"]
        assert d["superposicion_png"]
    assert all(m.get("metricas_prueba") for m in d["modelos_usados"])
    assert "especialista" in d["informe_texto"]


@hay_todo
def test_un_plano_sin_red_no_inventa_medidas():
    """Una imagen negra: el plano será «otro» o de baja confianza; no se inventan medidas."""
    r = cliente.post("/api/analyze", files={"file": ("n.png", _png(Image.new("L", (400, 300), 0)), "image/png")})
    d = r.json()
    if d["plano"]["plano"] not in ("cerebro fetal", "tórax fetal", "abdomen fetal"):
        assert d["medidas"] == {}
        assert d["hallazgos"]


def test_health_lista_todas_las_redes():
    d = cliente.get("/health").json()
    assert {"segmentacion_cabeza", "segmentacion_torax", "segmentacion_abdomen", "segmentacion_intraparto",
            "plano_anatomico_fetal_planes"} <= set(d["redes"])


INTRAPARTO = AQUI / "entrenamiento" / "segmentacion" / "salidas" / "intraparto" / "prueba_medidas.csv"


@pytest.mark.skipif(not segmentacion.disponible("intraparto") or not INTRAPARTO.exists(),
                    reason="falta la red intraparto o su prueba")
def test_angulo_de_progresion_igual_que_el_entrenamiento():
    """20 imágenes de prueba de IUGC (otros años): el AoP por la API coincide con el
    del entrenamiento (±0,5°) y el error contra el experto queda en el orden medido."""
    medidas = pd.read_csv(INTRAPARTO).dropna().sample(20, random_state=3)
    difs, errores = [], []
    for _, fila in medidas.iterrows():
        with open(AQUI / fila["imagen"], "rb") as f:
            r = cliente.post("/api/segmentacion/intraparto", files={"file": ("i.png", f.read(), "image/png")})
        assert r.status_code == 200
        aop = r.json()["medidas"]["angulo_progresion_grados"]
        difs.append(abs(aop - fila["aop_red"]))
        errores.append(abs(aop - fila["aop_experto"]))
    assert max(difs) < 0.5, f"la API se desvía del entrenamiento hasta {max(difs):.2f}°"
    assert np.mean(errores) < 12
    assert r.json()["modelo"]["metricas_prueba"]["angulo_progresion_prueba"]["sensibilidad_aop_120"] is not None
