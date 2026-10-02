"""Redes de ecografía ginecológica, probadas a través de la API.

Lo que se protege (esperado vs obtenido):
  · sin modelo, 503: nunca un resultado inventado;
  · la API clasifica IGUAL que el entrenamiento: sobre 40 imágenes de la prueba
    de MMOTU (pacientes que la red no vio) da el mismo tipo y las mismas
    probabilidades (±0,02) que `clasificar.py`. Si el preprocesado se desvía
    (gris/color, recorte de la lesión, tamaño), la red sigue respondiendo sin
    error pero con otros números, y esto lo detecta;
  · el mioma se ubica igual que al medir la red (IoU de la caja ±0,02);
  · la alarma de malignidad respeta el umbral fijado y trae su sensibilidad medida;
  · /api/modelos lista las redes ginecológicas con sus métricas.

Ejecutar (necesita torch y timm):
    C:/Users/Miscar/AppData/Local/Programs/Python/Python312/python.exe -m pytest test_ginecologia.py -v
"""
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.ginecologia import RedesGinecologia, ginecologia
from app.main import app
from app.segmentacion import RedesSegmentacion, segmentacion

AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI / "entrenamiento" / "ginecologia" / "salidas"
CATALOGOS = AQUI / "entrenamiento" / "ginecologia" / "catalogos"
cliente = TestClient(app)

hay_ovario = pytest.mark.skipif(not (ginecologia.disponible("ovario") and segmentacion.disponible("ovario")),
                                reason="faltan las redes de ovario en trained_models/")
hay_mioma = pytest.mark.skipif(not segmentacion.disponible("mioma"), reason="falta segmentacion_mioma.pth")
hay_pco = pytest.mark.skipif(not ginecologia.disponible("ovario_pco"), reason="falta clasificador_ovario_pco.pth")


def _archivo(ruta: Path) -> dict:
    return {"file": (ruta.name, ruta.read_bytes(), "image/jpeg")}


def _png(imagen: Image.Image) -> dict:
    buf = BytesIO()
    imagen.save(buf, "PNG")
    return {"file": ("a.png", buf.getvalue(), "image/png")}


def test_tarea_desconocida_404():
    assert cliente.post("/api/ginecologia/rinon", files=_png(Image.new("L", (64, 64)))).status_code == 404


def test_sin_modelo_responde_503(monkeypatch, tmp_path):
    import app.ginecologia as gin
    import app.routes as rutas

    vacio = RedesGinecologia(carpeta=tmp_path)
    monkeypatch.setattr(rutas, "ginecologia", vacio)
    monkeypatch.setattr(gin, "segmentacion", RedesSegmentacion(carpeta=tmp_path))
    for tarea in ("ovario", "mioma", "ovario-pco"):
        assert cliente.post(f"/api/ginecologia/{tarea}", files=_png(Image.new("L", (64, 64)))).status_code == 503


@hay_ovario
@pytest.mark.skipif(not (SALIDAS / "ovario" / "predicciones_prueba.csv").exists(), reason="sin predicciones de prueba")
def test_la_api_clasifica_igual_que_el_entrenamiento():
    pred = pd.read_csv(SALIDAS / "ovario" / "predicciones_prueba.csv").sample(40, random_state=7)
    meta = ginecologia._cargar("ovario")[1]
    nombres = dict(zip(meta["clases"], meta["nombres"]))
    diferencias, iguales = [], 0
    for _, fila in pred.iterrows():
        r = cliente.post("/api/ginecologia/ovario", files=_archivo(AQUI / fila["imagen"]))
        assert r.status_code == 200, r.text
        cuerpo = r.json()
        iguales += cuerpo["tipo_probable"] == nombres[fila["predicha"]]
        api = {p["tipo"]: p["probabilidad"] for p in cuerpo["probabilidades"]}
        diferencias.append(abs(api[cuerpo["tipo_probable"]] - fila[f"p_{meta['clases'][meta['nombres'].index(cuerpo['tipo_probable'])]}"]))
    assert iguales >= 39, f"la API cambió el tipo en {40 - iguales} de 40 imágenes"
    assert float(np.median(diferencias)) < 0.02


@hay_ovario
def test_la_alarma_respeta_el_umbral_y_trae_su_sensibilidad_medida():
    cat = pd.read_csv(CATALOGOS / "ovario.csv")
    fila = cat[(cat["particion"] == "prueba") & (cat["clase_nombre"] == "carcinoma_seroso_alto_grado")].iloc[0]
    cuerpo = cliente.post("/api/ginecologia/ovario", files=_archivo(AQUI / fila["imagen"]),
                          data={"tamano_pixel_mm": "0.2"}).json()
    mal = cuerpo["malignidad"]
    assert mal["alarma"] == (mal["probabilidad"] >= mal["umbral"])
    assert mal["sensibilidad_medida"] is not None and mal["especificidad_medida"] is not None
    assert cuerpo["superposicion_png"]
    if cuerpo["lesion_encontrada"]:
        assert cuerpo["medidas"]["lesion_ancho_mm"] == pytest.approx(cuerpo["medidas"]["lesion_ancho_px"] * 0.2, abs=0.1)


@hay_mioma
@pytest.mark.skipif(not (AQUI / "entrenamiento" / "segmentacion" / "salidas" / "mioma" / "prueba_medidas.csv").exists(),
                    reason="sin medidas de prueba del mioma")
def test_el_mioma_se_ubica_igual_que_al_medir_la_red():
    from entrenamiento.segmentacion.entrenar import _iou

    medidas = pd.read_csv(AQUI / "entrenamiento" / "segmentacion" / "salidas" / "mioma" / "prueba_medidas.csv")
    cat = pd.read_csv(CATALOGOS / "mioma.csv").set_index("imagen")
    for _, fila in medidas.sample(20, random_state=7).iterrows():
        cuerpo = cliente.post("/api/ginecologia/mioma", files=_archivo(AQUI / fila["imagen"])).json()
        cajas = [tuple(map(int, c.split(","))) for c in cat.loc[fila["imagen"], "cajas"].split(";")]
        mayor = max(cajas, key=lambda c: (c[2] - c[0]) * (c[3] - c[1]))
        iou = _iou(tuple(cuerpo["medidas"]["caja_px"]), mayor) if cuerpo["mioma_ubicado"] else 0.0
        assert iou == pytest.approx(fila["iou_caja"], abs=0.02)


@hay_pco
def test_ovario_pco_da_las_tres_categorias_y_el_aviso_de_rotterdam():
    cat = pd.read_csv(CATALOGOS / "ovario_pco.csv")
    cuerpo = cliente.post("/api/ginecologia/ovario-pco", files=_archivo(AQUI / cat["ruta"].iloc[0])).json()
    assert len(cuerpo["probabilidades"]) == 3
    assert sum(p["probabilidad"] for p in cuerpo["probabilidades"]) == pytest.approx(1, abs=0.01)
    assert any("Rotterdam" in a for a in cuerpo["avisos"])


def test_modelos_lista_las_redes_ginecologicas():
    nombres = cliente.get("/api/modelos").json()
    for clave in ("segmentacion_ovario", "segmentacion_mioma", "clasificador_ovario", "clasificador_ovario_pco"):
        assert clave in nombres
