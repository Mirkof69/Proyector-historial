"""Análisis completo de una ecografía con las redes MEDIDAS (un solo flujo).

    imagen → plano anatómico (EfficientNet-B0, 92,7 %)
           ├─ cerebro → segmentación de cabeza (HC, DBP, EG) + cribado de anomalías cerebrales
           ├─ tórax   → segmentación de tórax y corazón (índice cardiotorácico)
           ├─ abdomen → segmentación abdominal (¿plano correcto para medir CA?)
           └─ fémur, cuello uterino, otro → se informa el plano; no hay red de medida validada

Reemplaza a la EfficientNet-B4 de «14 patologías», que se entrenó con
etiquetas no verificables (ver datos/CATALOGO.md) y no tenía ninguna métrica
válida. Aquí cada número viene de una red con su métrica en datos no vistos,
y la respuesta la lleva.

La respuesta es un informe estructurado (JSON) que el backend guarda tal cual
y el frontend dibuja; `informe_texto` es el mismo contenido en prosa.
"""
from __future__ import annotations

import logging
import time

from .ecografia_real import ARCHIVO_CEREBRO, ARCHIVO_PLANO, redes
from .segmentacion import segmentacion

logger = logging.getLogger(__name__)

VERSION_FLUJO = "2.0"
#: Plano → tarea de segmentación
TAREA_POR_PLANO = {"cerebro fetal": "cabeza", "tórax fetal": "torax", "abdomen fetal": "abdomen"}


def _texto(informe: dict) -> str:
    partes = [f"Plano detectado: {informe['plano']['plano']} ({informe['plano']['confianza']:.0%})."]
    m = informe.get("medidas", {})
    if "circunferencia_cefalica_mm" in m:
        partes.append(f"Circunferencia cefálica {m['circunferencia_cefalica_mm']} mm (±{m['margen_hc_mm']}), "
                      f"diámetro biparietal {m['diametro_biparietal_mm']} mm (±{m['margen_dbp_mm']}).")
        if "edad_gestacional_por_hc_semanas" in m:
            partes.append(f"Edad gestacional por HC (Hadlock 1984): {m['edad_gestacional_por_hc_semanas']} semanas.")
    if "indice_cardiotoracico_areas" in m:
        partes.append(f"Índice cardiotorácico por áreas {m['indice_cardiotoracico_areas']} "
                      f"(referencia {m['referencia_areas'][0]}–{m['referencia_areas'][1]}).")
    if "plano_adecuado_para_ca" in m:
        partes.append("Corte adecuado para medir la circunferencia abdominal." if m["plano_adecuado_para_ca"]
                      else "El corte no muestra estómago y vena umbilical: no es el adecuado para medir la CA.")
    a = informe.get("anomalias_cerebrales")
    if a and a.get("aplicable"):
        partes.append(f"Cribado cerebral: {'ALARMA — ' + a['familia_sospechada_nombre'] if a['alarma_anomalia'] else 'sin anomalía visible'}.")
    for h in informe["hallazgos"]:
        partes.append(h)
    partes.append("Apoyo al diagnóstico: todo hallazgo lo confirma un especialista.")
    return " ".join(partes)


def analizar(imagen, tamano_pixel_mm: float | None = None) -> dict:
    """Informe completo. Lanza FileNotFoundError si falta el clasificador de planos."""
    t0 = time.perf_counter()
    if not redes.disponible(ARCHIVO_PLANO):
        raise FileNotFoundError("Falta la red de plano anatómico (plano_anatomico_fetal_planes.pth).")
    plano = redes.clasificar_plano(imagen)
    informe: dict = {"version_flujo": VERSION_FLUJO, "plano": plano, "medidas": {}, "hallazgos": [],
                     "avisos": list(plano.get("avisos", [])), "estructuras_vistas": {}, "superposicion_png": None,
                     "modelos_usados": [plano["modelo"]]}

    tarea = TAREA_POR_PLANO.get(plano["plano"])
    if tarea and segmentacion.disponible(tarea):
        if tarea == "cabeza":
            r = segmentacion.medir_cabeza(imagen, tamano_pixel_mm)
        elif tarea == "torax":
            r = segmentacion.medir_torax(imagen)
        else:
            r = segmentacion.analizar_abdomen(imagen)
        informe["medidas"] = r["medidas"]
        informe["estructuras_vistas"] = r["estructuras_vistas"]
        informe["superposicion_png"] = r["superposicion_png"]
        informe["avisos"] += r["avisos"]
        informe["modelos_usados"].append(r["modelo"])
    elif tarea:
        informe["avisos"].append(f"La red de segmentación de {tarea} no está instalada en este servidor.")
    else:
        informe["hallazgos"].append(
            f"Para el plano «{plano['plano']}» no hay una red de medida validada: solo se informa el plano.")

    # El cribado cerebral decide solo si aplica (también ve cabezas deformadas
    # que el clasificador de planos no reconoce como cerebro).
    if redes.disponible(ARCHIVO_CEREBRO):
        anomalias = redes.detectar_anomalia_cerebral(imagen)
        if anomalias.get("aplicable"):
            informe["anomalias_cerebrales"] = {k: anomalias[k] for k in (
                "aplicable", "alarma_anomalia", "probabilidad_anomalia", "umbral", "familia_sospechada",
                "familia_sospechada_nombre", "probabilidades")}
            informe["avisos"] += anomalias.get("avisos", [])
            informe["modelos_usados"].append(anomalias["modelo"])
            if anomalias["alarma_anomalia"]:
                informe["hallazgos"].append(
                    f"Posible anomalía cerebral ({anomalias['familia_sospechada_nombre']}): derivar a especialista.")

    informe["requiere_revision"] = bool(informe["hallazgos"] and any("anomalía" in h for h in informe["hallazgos"])) \
        or plano["confianza"] < 0.70
    informe["informe_texto"] = _texto(informe)
    informe["tiempo_ms"] = round((time.perf_counter() - t0) * 1000)
    return informe
