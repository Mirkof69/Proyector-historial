"""Ecografía y análisis con redes neuronales por la API.

Las imágenes son de la partición de PRUEBA de los conjuntos públicos que usa el sistema (sin datos personales):
la red no las vio al entrenar. Estas pruebas comprueban la INTEGRACIÓN de la red con el sistema (que la API
responde, con su contrato y con una exactitud coherente con la medida del modelo); no re-evalúan el modelo.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import cliente
from data import fabrica
from utils import config
from utils.api_client import ApiCliente

pytestmark = [pytest.mark.api, pytest.mark.ecografia_ia]

IMG = Path(__file__).resolve().parents[2] / "data" / "imagenes_ia"
MANIFIESTO = json.loads((IMG / "manifiesto.json").read_text(encoding="utf-8"))


def _enviar(ruta: str, archivo: Path, rol="medico", extra=None, timeout=180):
    tipo = "image/png" if archivo.suffix.lower() == ".png" else "image/jpeg"
    with open(archivo, "rb") as f:
        return cliente(rol).post(ruta, extra or {}, archivos={"file": (archivo.name, f, tipo)}, timeout=timeout)


@pytest.fixture(scope="module")
def ecografia_termino(paciente_qa, embarazo_qa):
    """Ecografía de 34 semanas con biometría en mm (la usan Hadlock, adjuntos y la predicción de peso)."""
    r = cliente("medico").post("/ecografias/", {
        "embarazo": embarazo_qa["id"], "paciente": paciente_qa["id"], "fecha_ecografia": fabrica.dia(0),
        "tipo_ecografia": "tercer_trimestre", "edad_gestacional_semanas": 34,
        "diagnostico": f"{config.PREFIJO_DATOS} feto único vivo",
        "biometria": {"diametro_biparietal": "86.0", "circunferencia_cefalica": "310.0",
                      "circunferencia_abdominal": "300.0", "longitud_femur": "65.0"}})
    assert r.status_code == 201, r.text[:400]
    return r.json()


@pytest.mark.tc("TC-064")
def test_tc064_hadlock_con_medidas_en_mm(ecografia_termino):
    """Peso fetal estimado (Hadlock) con medidas en mm."""
    eco = cliente("medico").get(f"/ecografias/{ecografia_termino['id']}/").json()
    peso = (eco.get("biometria") or {}).get("peso_fetal_estimado")
    assert peso, "No estimó el peso fetal"
    assert 1800 <= int(peso) <= 3200, f"Peso de {peso} g fuera de lo esperable a las 34 semanas"


@pytest.mark.tc("TC-066")
def test_tc066_html_disfrazado_de_pdf(ecografia_termino):
    """Un HTML disfrazado de PDF se rechaza."""
    falso = b"<html><body><script>alert(1)</script>Informe</body></html>"
    r = cliente("medico").post("/ecografias-archivos/archivos/", {"ecografia": ecografia_termino["id"]},
                               archivos={"archivo": ("informe.pdf", falso, "application/pdf")})
    assert r.status_code == 400, f"Aceptó un HTML con extensión .pdf (HTTP {r.status_code})"


@pytest.mark.tc("TC-065")
def test_tc065_imagenes_de_ecografia_protegidas():
    """Imágenes de ecografía protegidas (sin sesión y para recepción)."""
    imgs = cliente("medico").lista("/ia/imagenes/", page_size=5)
    if not imgs:
        pytest.skip("BLOCKED: no hay imágenes de ecografía en el módulo de IA para probar el acceso")
    url = imgs[0].get("url_imagen") or imgs[0].get("imagen")
    assert url, f"El listado no expone la imagen: {list(imgs[0].keys())}"
    anonimo = ApiCliente().get(url)
    assert anonimo.status_code in (401, 403, 404), f"Sin sesión la imagen se descarga (HTTP {anonimo.status_code})"
    assert cliente("recepcion").get("/ia/imagenes/").status_code == 403


@pytest.mark.smoke
@pytest.mark.tc("TC-068")
def test_tc068_cascada_reconoce_cerebro_fetal():
    """Analizar una ecografía de cerebro fetal con la cascada de redes."""
    cerebro = next(p for p in MANIFIESTO["planos"] if p["plano"] == "cerebro fetal")
    r = _enviar("/ecografias/analyze-with-ai/", IMG / cerebro["archivo"])
    assert r.status_code == 200, r.text[:300]
    ia = r.json()["ai_analysis"]
    assert ia["plano"]["plano"] == "cerebro fetal", f"Reconoció «{ia['plano']['plano']}»"
    assert 0 <= ia["plano"]["confianza"] <= 1
    assert abs(sum(ia["plano"]["probabilidades"].values()) - 1) < 0.02, "Las probabilidades no suman 1"


@pytest.mark.tc("TC-070")
def test_tc070_exactitud_del_plano_en_la_muestra():
    """Exactitud del plano anatómico en una muestra de la partición de prueba."""
    aciertos, errores = 0, []
    for p in MANIFIESTO["planos"]:
        r = _enviar("/ecografias/plano-anatomico/", IMG / p["archivo"])
        assert r.status_code == 200, f"{p['archivo']}: HTTP {r.status_code}"
        pred = r.json()["plano"]
        if pred == p["plano"]:
            aciertos += 1
        else:
            errores.append(f"{p['archivo']}: {p['plano']} -> {pred}")
    exactitud = aciertos / len(MANIFIESTO["planos"])
    print(f"exactitud {exactitud:.3f} ({aciertos}/{len(MANIFIESTO['planos'])}); errores: {errores}")
    assert exactitud >= 0.85, f"Exactitud {exactitud:.1%} en la muestra (< 85 %). Errores: {errores}"


@pytest.mark.tc("TC-071")
def test_tc071_sin_falsa_alarma_en_imagenes_que_no_son_cabeza():
    """La red de anomalías no da alarma en imágenes que no son cabezas."""
    otras = [p for p in MANIFIESTO["planos"] if p["plano"] in ("fémur fetal", "abdomen fetal")]
    alarmas = []
    for p in otras:
        r = _enviar("/ecografias/analyze-with-ai/", IMG / p["archivo"])
        assert r.status_code == 200
        ia = r.json()["ai_analysis"]
        anom = ia.get("anomalias_cerebrales") or ia.get("anomalias") or {}
        if isinstance(anom, dict) and anom.get("alarma"):
            alarmas.append(p["archivo"])
    assert not alarmas, f"Alarma de anomalía cerebral en imágenes que no son cabezas: {alarmas}"


@pytest.mark.tc("TC-077")
def test_tc077_longitud_del_femur():
    """Longitud del fémur desde la imagen."""
    femur = next(p for p in MANIFIESTO["planos"] if p["plano"] == "fémur fetal")
    r = _enviar("/ecografias/analyze-with-ai/", IMG / femur["archivo"])
    assert r.status_code == 200
    ia = r.json()["ai_analysis"]
    texto = json.dumps(ia, ensure_ascii=False).lower()
    assert ia["plano"]["plano"] == "fémur fetal", f"Plano reconocido: {ia['plano']['plano']}"
    assert "femur" in texto, "La respuesta no trae la medida del fémur"


@pytest.mark.tc("TC-073")
def test_tc073_prediccion_de_peso_al_nacer(ecografia_termino):
    """Predicción del peso al nacer."""
    r = cliente("medico").post("/ia/prediccion-peso/", {"ecografia_id": ecografia_termino["id"], "semanas_objetivo": 39})
    if r.status_code == 409:
        pytest.skip(f"BLOCKED: el sistema no tiene el modelo de peso cargado ({r.text[:120]})")
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert d.get("peso_previsto_g") and d.get("margen_g") is not None, f"Faltan peso o margen: {list(d)}"
    assert "hadlock" in json.dumps(d).lower(), "No trae el peso de Hadlock al lado"


@pytest.fixture(scope="module")
def variables_ctg():
    return cliente("medico").get("/ia/cardiotocografia/").json()["variables"]


@pytest.mark.tc("TC-074")
def test_tc074_cardiotocografia_clasifica(variables_ctg):
    """Clasificar una cardiotocografía."""
    datos = {v["clave"]: round((v["minimo"] + v["maximo"]) / 2, 4) for v in variables_ctg}
    datos["linea_base"] = 135
    r = cliente("medico").post("/ia/cardiotocografia/", datos)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    probs = d.get("probabilidades") or {}
    assert d.get("clase") or d.get("clasificacion"), f"No devolvió la clase: {list(d)}"
    assert abs(sum(float(x) for x in probs.values()) - 1) < 0.02, f"Las probabilidades no suman 1: {probs}"


@pytest.mark.tc("TC-075")
def test_tc075_cardiotocografia_con_dato_faltante(variables_ctg):
    """CTG con un dato faltante."""
    datos = {v["clave"]: round((v["minimo"] + v["maximo"]) / 2, 4) for v in variables_ctg[1:]}
    r = cliente("medico").post("/ia/cardiotocografia/", datos)
    # el sistema responde 409 («faltan datos: no se clasifica», CP-083); lo importante es que no invente una clase
    assert r.status_code in (400, 409), f"Clasificó con una variable faltante (HTTP {r.status_code})"
    assert not r.json().get("clase"), "Devolvió una clase con datos incompletos"


@pytest.mark.tc("TC-076")
@pytest.mark.parametrize("tarea,archivo", [("ovario", "ovario_muestra.JPG"), ("mioma", "mioma_muestra.jpg"),
                                            ("ovario-pco", "pco_muestra.jpg")])
def test_tc076_ginecologia(tarea, archivo):
    """Masa ovárica, mioma y ovario poliquístico."""
    r = _enviar(f"/ia/ginecologia/{tarea}/", IMG / "ginecologia" / archivo)
    assert r.status_code == 200, f"{tarea}: HTTP {r.status_code} {r.text[:200]}"
    d = r.json()
    assert d.get("avisos") is not None, f"{tarea}: la respuesta no trae avisos para el médico"


@pytest.mark.tc("TC-076")
def test_tc076_ginecologia_no_para_enfermeria():
    """Enfermería no puede pedir el análisis ginecológico."""
    r = _enviar("/ia/ginecologia/ovario/", IMG / "ginecologia" / "ovario_muestra.JPG", rol="enfermera")
    assert r.status_code == 403, f"Enfermería pidió el análisis (HTTP {r.status_code})"
