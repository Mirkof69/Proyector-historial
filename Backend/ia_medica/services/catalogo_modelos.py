"""Catálogo REAL de los modelos de IA del sistema, con su métrica medida.

Reemplaza a la tabla fija de `cnn_service.MODELOS_CONFIG`, que mostraba
exactitudes inventadas («EfficientNet-B4 94,1 %», «U-Net 88,7 %») para redes
que no existían o no tenían ninguna métrica válida.

Cada entrada sale de la ficha que dejó el entrenamiento:
- redes de imagen: `GET /api/modelos` del microservicio (los .json junto a cada .pth);
- modelos supervisados tabulares: `ml_modelos/<nombre>/<versión>/ficha.json`.

Si el microservicio no responde, sus redes figuran como «no disponible»: nunca
se rellena con números de referencia.

Antes el catálogo listaba 7 de las 13 redes que sirve el microservicio: faltaban
las cuatro de ginecología y las dos de puntos (fémur y circunferencia
abdominal), y la pestaña «Modelos y métricas» y la Guía de IA no las mostraban.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _pct(v: float, decimales: int = 1) -> str:
    """0.927 → «92,7 %» (coma decimal, como el resto de la interfaz)."""
    return f"{v * 100:.{decimales}f} %".replace(".", ",")


def _num(v: float, decimales: int = 1) -> str:
    return f"{v:.{decimales}f}".replace(".", ",")


def _ent(n: int) -> str:
    """5271 → «5.271»."""
    return f"{n:,}".replace(",", ".")


def _plano(m: dict) -> str:
    return (f"Exactitud {_pct(m['exactitud'])} en {_ent(m['imagenes_prueba'])} imágenes de "
            f"{m['madres_prueba']} madres no vistas; cabezas del primer trimestre reconocidas: "
            f"{_pct(m['cabezas_primer_trimestre_reconocidas'])}")


def _cabeza(m: dict) -> str:
    e = m["prueba_externa_hc18"]
    return (f"Circunferencia cefálica en otro hospital (HC18, {e['imagenes']} imágenes): error medio "
            f"{_num(e['hc_error_medio_mm'])} mm, {_pct(e['dentro_de_5_por_ciento'], 0)} dentro del 5 %")


def _torax(m: dict) -> str:
    return (f"Dice {_num(m['dice_prueba_medio'], 2)}; índice cardiotorácico ±"
            f"{_num(m['indice_cardiotoracico_prueba']['ict_areas_error_medio'], 2)} en {m['imagenes_prueba']} "
            "imágenes. Solo corazones normales: no valida la detección de cardiomegalia")


def _abdomen(m: dict) -> str:
    return (f"Dice {_num(m['dice_prueba_medio'], 2)}; estómago visto en el "
            f"{_pct(m['marcadores_plano_abdominal']['estomago']['sensibilidad'], 0)} de {m['imagenes_prueba']} "
            f"imágenes de {m['pacientes_prueba']} pacientes")


def _femur(m: dict) -> str:
    fl = m["prueba"]["fl"]
    return (f"Error medio {_num(fl['error_medio_mm'])} mm (mediana {_num(fl['error_mediano_mm'])} mm), "
            f"{_pct(fl['dentro_de_5_por_ciento'], 0)} dentro del 5 % en {m['imagenes_prueba']} imágenes de "
            f"{m['pacientes_prueba']} pacientes")


def _ca(m: dict) -> str:
    ca = m["prueba"]["ca"]
    return (f"Error relativo {_pct(ca['error_relativo_medio'])} (mediana {_num(ca['error_mediano_mm'])} mm), "
            f"{_pct(ca['dentro_de_5_por_ciento'], 0)} dentro del 5 % en {ca['imagenes']} imágenes")


def _intraparto(m: dict) -> str:
    a = m["angulo_progresion_prueba"]
    return (f"Error medio {_num(a['aop_error_medio_grados'])}° en {a['imagenes']} imágenes de otros años; "
            f"AoP ≥ 120°: sensibilidad {_pct(a['sensibilidad_aop_120'], 0)}, "
            f"especificidad {_pct(a['especificidad_aop_120'], 0)}")


def _anomalias(m: dict) -> str:
    e = m["externa_falsos_positivos"]
    return (f"Falsas alarmas en cabezas normales de otro hospital: {e['fp']} de {_ent(e['n'])}. "
            "Sensibilidad real no medible con datos públicos")


def _hc18(m: dict) -> str:
    return (f"R² {_num(m['r2'], 3)}; error medio {_num(m['error_medio_mm'])} mm en {m['imagenes_prueba']} "
            f"imágenes de {m['madres_prueba']} madres (la U-Net de cabeza mide mejor)")


def _ovario(m: dict) -> str:
    return (f"Dice {_num(m['dice_prueba_medio'], 2)}; lesión encontrada en el "
            f"{_pct(m['lesion_ovarica_prueba']['lesion_encontrada_iou_0_5'], 0)} de {m['imagenes_prueba']} "
            f"imágenes de {m['pacientes_prueba']} pacientes")


def _tipo_ovario(m: dict) -> str:
    p, mal = m["prueba"], m["prueba"]["malignidad"]
    detectados = round(mal["sensibilidad"] * mal["casos_malignos"])
    return (f"Exactitud {_pct(p['exactitud'])} (IC95 {_pct(p['exactitud_ic95'][0], 0)}–"
            f"{_pct(p['exactitud_ic95'][1], 0)}) en {p['imagenes']} imágenes, 8 clases. Alarma de carcinoma: "
            f"detecta {detectados} de {mal['casos_malignos']} con especificidad {_pct(mal['especificidad'])}; "
            "sin alarma no descarta")


def _mioma(m: dict) -> str:
    return (f"Mioma ubicado en el {_pct(m['mioma_prueba']['mioma_encontrado_iou_0_5'])} de {m['imagenes_prueba']} "
            f"imágenes de {m['pacientes_prueba']} pacientes. Solo vio úteros con mioma: no sirve para descartarlo")


def _pco(m: dict) -> str:
    p = m["prueba"]
    return (f"Exactitud {_pct(p['exactitud'])} (IC95 {_pct(p['exactitud_ic95'][0], 0)}–"
            f"{_pct(p['exactitud_ic95'][1], 0)}) en {p['imagenes']} imágenes, 5 pliegues. "
            "El SOP se diagnostica con los criterios de Rotterdam, no con la imagen")


#: archivo del microservicio → (nombre, tipo, cómo redactar su métrica principal, datos de entrenamiento).
#: Las cifras salen SIEMPRE de `metricas_prueba` (GET /api/modelos); aquí solo se redactan.
REDES_IMAGEN = {
    "plano_anatomico_fetal_planes": ("Plano anatómico (EfficientNet-B0)", "clasificación de imagen (CNN)",
                                     _plano, "FETAL_PLANES_DB (Barcelona, Zenodo 3904280)"),
    "segmentacion_cabeza": ("Segmentación de cabeza (U-Net)", "segmentación y medida (CNN U-Net)", _cabeza,
                            "Large-Scale Fetal Head Biometry (Zenodo 8265464); prueba externa HC18"),
    "segmentacion_torax": ("Segmentación de tórax y corazón (U-Net)", "segmentación y medida (CNN U-Net)",
                           _torax, "FOCUS (Zenodo 14597550)"),
    "segmentacion_abdomen": ("Segmentación abdominal (U-Net)", "segmentación (CNN U-Net)", _abdomen,
                             "Fetal Abdominal Structures Segmentation (Mendeley Data)"),
    "biometria_femur": ("Longitud del fémur (U-Net de puntos)", "puntos anatómicos (CNN de mapas de calor)",
                        _femur, "Multicentre Fetal Biometry 2026 (Barcelona y Londres)"),
    "biometria_abdomen": ("Circunferencia abdominal (U-Net de puntos)", "puntos anatómicos (CNN de mapas de calor)",
                          _ca, "Multicentre Fetal Biometry 2026 (Barcelona y Londres)"),
    "segmentacion_intraparto": ("Ángulo de progresión intraparto (U-Net)", "segmentación y medida (CNN U-Net)",
                                _intraparto, "IUGC MICCAI 2024 (ecografía transperineal)"),
    "anomalias_cerebrales_fetales": ("Cribado de anomalías cerebrales (EfficientNet-B0)",
                                     "cribado (CNN de clasificación)", _anomalias,
                                     "Fetal Brain Abnormalities (Roboflow) + cortes normales de FETAL_PLANES_DB"),
    "circunferencia_cefalica_hc18": ("Circunferencia cefálica por regresión (EfficientNet-B0)", "regresión (CNN)",
                                     _hc18, "HC18 (Radboud)"),
    "segmentacion_ovario": ("Lesión ovárica: contorno (U-Net)", "segmentación (CNN U-Net)", _ovario,
                            "MMOTU OTU_2d (Beijing Shijitan Hospital)"),
    "clasificador_ovario": ("Tipo de lesión ovárica (ensamble de 2 EfficientNet-B0)",
                            "clasificación de imagen (CNN)", _tipo_ovario, "MMOTU OTU_2d con anatomía patológica"),
    "segmentacion_mioma": ("Mioma uterino (U-Net)", "segmentación (CNN U-Net)", _mioma,
                           "Uterine fibroid ultrasound images (Mendeley n2zcmcypgb)"),
    "clasificador_ovario_pco": ("Ovario poliquístico (EfficientNet-B0)", "clasificación de imagen (CNN)", _pco,
                                "Borna et al. 2025 (ecografías transvaginales)"),
}

#: Modelos que se entrenaron, se midieron y NO pasaron a servicio. Las cifras son
#: las que dejó cada entrenamiento (`evidencia`, relativa a
#: Microservicio_IA/entrenamiento/); tests/test_guia_ia.py las compara con esos
#: archivos cuando están en el disco.
DESCARTADOS = [
    {"codigo": "acidemia_ctu_uhb", "nombre": "Acidemia al nacer desde la señal del monitoreo",
     "tipo": "modelos supervisados sobre la señal (logística, bosque aleatorio, gradient boosting)",
     "datos": "CTU-UHB Intrapartum CTG (PhysioNet, 552 registros)",
     "metrica": "AUC 0,73 en la prueba; para detectar el 90 % de las acidemias, especificidad 33 %",
     "motivo": "Demasiadas falsas alarmas para decidir una conducta en el parto.",
     "evidencia": "senales/salidas/ctu_acidosis/metricas.json"},
    {"codigo": "prematuro_tpehg", "nombre": "Parto prematuro desde el electrohisterograma",
     "tipo": "modelos supervisados sobre la señal uterina",
     "datos": "Term-Preterm EHG Database (PhysioNet, 300 registros)",
     "metrica": "AUC 0,42–0,43 en validación cruzada (señal y datos clínicos)",
     "motivo": "No distingue un parto prematuro de uno a término mejor que el azar.",
     "evidencia": "senales/salidas/tpehg_prematuro/metricas.json"},
    {"codigo": "translucencia_nucal", "nombre": "Calidad del corte para medir la translucencia nucal",
     "tipo": "CNN EfficientNet-B0 de clasificación",
     "datos": "Dataset for Fetus Framework (Shenzhen; prueba externa en otra sede)",
     "metrica": "94,8 % en el mismo hospital; 68,6 % en otra sede",
     "motivo": "No generaliza a otro centro: en un hospital nuevo fallaría de forma imprevisible.",
     "evidencia": "translucencia/salidas/zoom/metricas.json"},
    {"codigo": "cardiopatia_cardium", "nombre": "Cardiopatía congénita por variables maternas",
     "tipo": "modelos supervisados sobre tablas clínicas",
     "datos": "CARDIUM, tablas clínicas (1.104 pacientes)",
     "metrica": "AUC 0,70; valor predictivo positivo 7–9 %",
     "motivo": "De cada 100 alarmas, más de 90 serían falsas.",
     "evidencia": "senales/salidas/cardium_tabla/metricas.json"},
    {"codigo": "cancer_cervicouterino", "nombre": "Cáncer cervicouterino por factores de riesgo",
     "tipo": "modelos supervisados sobre tablas clínicas",
     "datos": "UCI 383 Cervical cancer (Risk Factors), Caracas",
     "metrica": "AUC 0,60 solo con factores de riesgo",
     "motivo": "No supera a la referencia clínica: el tamizaje (PAP, IVAA, VPH) sigue siendo el criterio.",
     "evidencia": "ginecologia/salidas/tablas/metricas.json"},
    {"codigo": "riesgo_materno", "nombre": "Riesgo materno general",
     "tipo": "modelos supervisados sobre tablas clínicas",
     "datos": "UCI 863 Maternal Health Risk (Bangladés)",
     "metrica": "Exactitud balanceada 71 % en 77 casos de prueba",
     "motivo": "La etiqueta de riesgo del dataset no tiene un criterio clínico definido.",
     "evidencia": "ginecologia/salidas/tablas/metricas.json"},
    {"codigo": "efficientnet_b4_14_patologias", "nombre": "EfficientNet-B4 de «14 patologías»",
     "tipo": "CNN de clasificación", "datos": "Etiquetas no verificables",
     "metrica": "Sin métrica válida",
     "motivo": "Retirada el 01/10/2026: sus etiquetas no se podían verificar.",
     "evidencia": "b4_retirada/LEEME.md"},
]


def _redes_del_microservicio() -> list[dict]:
    import requests

    from ecografias.ai_views import obtener_url_ia

    try:
        estado = requests.get(f"{obtener_url_ia()}/api/modelos", timeout=3).json()
    except Exception:
        logger.info("Microservicio de IA no disponible para el catálogo de modelos")
        estado = {}
    salida = []
    for archivo, (nombre, tipo, resumen, datos) in REDES_IMAGEN.items():
        info = estado.get(archivo) or {}
        metricas = info.get("metricas_prueba")
        try:
            metrica = resumen(metricas) if metricas else None
        except (KeyError, TypeError, IndexError):
            logger.warning("Las métricas de %s no tienen la forma esperada", archivo)
            metrica = None
        salida.append({"codigo": archivo, "nombre": nombre, "tipo": tipo, "origen": "microservicio",
                       "disponible": bool(info.get("disponible")), "metrica_principal": metrica,
                       "datos": datos, "datos_reales": True, "huella": (info.get("sha256") or "")[:12] or None})
    return salida


def _modelos_tabulares() -> list[dict]:
    from django.conf import settings

    base = Path(getattr(settings, "ML_MODELOS_DIR", settings.BASE_DIR / "ml_modelos"))
    salida = []

    def ultima(nombre: str) -> tuple[str, dict] | None:
        carpeta = base / nombre
        fichas = sorted(carpeta.glob("*/ficha.json"), key=lambda p: p.stat().st_mtime) if carpeta.exists() else []
        return (fichas[-1].parent.name, json.loads(fichas[-1].read_text(encoding="utf-8"))) if fichas else None

    if (ctg := ultima("cardiotocografia")):
        version, f = ctg
        p = f["prueba"]
        patologica = (p.get("sensibilidad") or {}).get("patologica")
        metrica = (f"Exactitud {_pct(p['exactitud'])} (IC95 {_pct(p['exactitud_ic95'][0])}–"
                   f"{_pct(p['exactitud_ic95'][1])}) en {f['registros_prueba']} registros no vistos")
        if patologica is not None:
            metrica += f"; detecta el {_pct(patologica)} de las patológicas"
        salida.append({"codigo": "cardiotocografia", "nombre": "Cardiotocografía (Gradient Boosting)",
                       "tipo": "clasificación supervisada (tabla de variables)", "origen": "backend",
                       "disponible": True, "version": version, "metrica_principal": metrica,
                       "datos": f.get("dataset"), "datos_reales": True})
    if (peso := ultima("peso_nacimiento")):
        version, f = peso
        mae = f.get("comparativa", {}).get(f.get("algoritmo"), {}).get("mae_g", {}).get("media")
        metrica = f"Error medio {mae:.0f} g en partos simulados" if mae else None
        reales = _desempeno_peso_real()
        if reales:
            metrica = f"{metrica} · con {reales[0]} nacimientos reales: {reales[1]:.0f} g"
        salida.append({"codigo": "peso_nacimiento", "nombre": "Peso al nacer (regresión supervisada)",
                       "tipo": "regresión supervisada (tabla de variables)", "origen": "backend",
                       "disponible": True, "version": version, "metrica_principal": metrica,
                       "datos": "Partos del sistema" if not f.get("entrenado_con_datos_sinteticos", True)
                       else "Partos simulados del sistema",
                       "datos_reales": not f.get("entrenado_con_datos_sinteticos", True)})
    return salida


def _desempeno_peso_real() -> tuple[int, float] | None:
    """(n, error medio) del modelo de peso sobre predicciones ya cerradas con el bebé real."""
    from ia_medica.models import PrediccionPesoNacimiento

    errores = list(PrediccionPesoNacimiento.objects.filter(error_modelo_g__isnull=False)
                   .values_list("error_modelo_g", flat=True))
    return (len(errores), sum(map(abs, errores)) / len(errores)) if errores else None


def catalogo() -> list[dict]:
    """Todos los modelos, cada uno con la métrica que se midió de verdad."""
    return _redes_del_microservicio() + _modelos_tabulares()


def descartados() -> list[dict]:
    """Los modelos evaluados y descartados, sin la ruta interna de la evidencia."""
    return [{k: v for k, v in d.items() if k != "evidencia"} for d in DESCARTADOS]
