"""Clasificación supervisada de la cardiotocografía (CTG): normal, sospechosa o patológica.

Datos: 2.126 cardiotocografías REALES (Ayres-de-Campos D. et al., «SisPorto
2.0: a program for automated analysis of cardiotocograms», J Matern Fetal Med
2000;9:311-8; UCI Machine Learning Repository «Cardiotocography», CC BY 4.0).
Cada registro trae las variables que calcula el programa SisPorto y la
clasificación por CONSENSO DE TRES OBSTETRAS (normal / sospechosa /
patológica). Copia en `datos/fetal_health.csv`.

Cómo se mide (y qué NO se puede afirmar)
----------------------------------------
- Se quitan los registros duplicados exactos antes de partir: si no, el mismo
  registro podría estar en entrenamiento y en prueba.
- 20 % de prueba estratificada que no se toca hasta el final. Con el 80 %
  restante se comparan los modelos por validación cruzada estratificada de 5
  particiones y se elige por F1 macro (las tres clases pesan igual: acertar
  mucho «normal» no tapa fallar «patológica»).
- El dataset no trae identificador de paciente; si una gestante tuviera varios
  registros, podrían caer en ambos lados. Es un límite del dataset y se dice.
- Es un hospital (Porto) y un programa (SisPorto): en otro monitor las
  variables pueden calcularse distinto. Hay que validarlo localmente.
"""
from __future__ import annotations

import json
import logging
import threading
import time
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NOMBRE_MODELO = "cardiotocografia"
SEMILLA = 2026
DATOS = Path(__file__).resolve().parent / "datos" / "fetal_health.csv"
CLASES = ["normal", "sospechosa", "patologica"]
NOMBRES_CLASE = {"normal": "Normal", "sospechosa": "Sospechosa", "patologica": "Patológica"}

#: columna del dataset → (nombre en el sistema, etiqueta, unidad, mínimo, máximo)
VARIABLES: dict[str, tuple[str, str, str, float, float]] = {
    "baseline value": ("linea_base", "Línea de base de la FCF", "lpm", 50, 220),
    "accelerations": ("aceleraciones", "Aceleraciones", "por segundo", 0, 0.1),
    "fetal_movement": ("movimientos_fetales", "Movimientos fetales", "por segundo", 0, 1),
    "uterine_contractions": ("contracciones", "Contracciones uterinas", "por segundo", 0, 0.1),
    "light_decelerations": ("desaceleraciones_leves", "Desaceleraciones leves", "por segundo", 0, 0.1),
    "severe_decelerations": ("desaceleraciones_severas", "Desaceleraciones severas", "por segundo", 0, 0.1),
    "prolongued_decelerations": ("desaceleraciones_prolongadas", "Desaceleraciones prolongadas", "por segundo", 0, 0.1),
    "abnormal_short_term_variability": ("vcp_anormal_pct", "Tiempo con variabilidad a corto plazo anormal", "%", 0, 100),
    "mean_value_of_short_term_variability": ("vcp_media", "Variabilidad a corto plazo media", "lpm", 0, 20),
    "percentage_of_time_with_abnormal_long_term_variability": ("vlp_anormal_pct", "Tiempo con variabilidad a largo plazo anormal", "%", 0, 100),
    "mean_value_of_long_term_variability": ("vlp_media", "Variabilidad a largo plazo media", "lpm", 0, 100),
    "histogram_width": ("histograma_ancho", "Histograma: ancho", "lpm", 0, 250),
    "histogram_min": ("histograma_minimo", "Histograma: mínimo", "lpm", 30, 220),
    "histogram_max": ("histograma_maximo", "Histograma: máximo", "lpm", 60, 260),
    "histogram_number_of_peaks": ("histograma_picos", "Histograma: número de picos", "", 0, 50),
    "histogram_number_of_zeroes": ("histograma_ceros", "Histograma: número de ceros", "", 0, 50),
    "histogram_mode": ("histograma_moda", "Histograma: moda", "lpm", 30, 220),
    "histogram_mean": ("histograma_media", "Histograma: media", "lpm", 30, 220),
    "histogram_median": ("histograma_mediana", "Histograma: mediana", "lpm", 30, 220),
    "histogram_variance": ("histograma_varianza", "Histograma: varianza", "", 0, 500),
    "histogram_tendency": ("histograma_tendencia", "Histograma: tendencia (−1, 0, 1)", "", -1, 1),
}
#: Las 11 que se leen del trazado (frecuencia, eventos y variabilidad). Las 10
#: del histograma solo las da un análisis automático.
NUCLEO = list(VARIABLES)[:11]
CONJUNTOS = {"nucleo_11": NUCLEO, "completo_21": list(VARIABLES)}

_cerrojo = threading.Lock()


class CTGNoDisponible(Exception):
    """No se puede clasificar. El mensaje dice por qué."""


# ─────────────────────────────── datos ─────────────────────────────────────

def cargar_datos() -> tuple[pd.DataFrame, np.ndarray, int]:
    """(X con las 21 columnas, y con 0/1/2, duplicados quitados)."""
    d = pd.read_csv(DATOS)
    antes = len(d)
    d = d.drop_duplicates().reset_index(drop=True)
    y = d["fetal_health"].astype(int).to_numpy() - 1
    return d[list(VARIABLES)], y, antes - len(d)


def _candidatos():
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    return {
        "regresion_logistica": ("Regresión logística (lineal)", lambda: make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=3000, class_weight="balanced"))),
        "random_forest": ("Random Forest, 500 árboles", lambda: RandomForestClassifier(
            n_estimators=500, class_weight="balanced_subsample", min_samples_leaf=1,
            random_state=SEMILLA, n_jobs=-1)),
        "gradient_boosting": ("Gradient Boosting por histogramas", lambda: HistGradientBoostingClassifier(
            learning_rate=0.08, max_iter=400, class_weight="balanced", random_state=SEMILLA)),
    }


def _metricas(y: np.ndarray, pred: np.ndarray, prob: np.ndarray | None = None) -> dict:
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score, roc_auc_score

    cm = confusion_matrix(y, pred, labels=[0, 1, 2])
    sens = cm.diagonal() / cm.sum(1).clip(min=1)
    vpp = cm.diagonal() / cm.sum(0).clip(min=1)
    m = {
        "exactitud": float(accuracy_score(y, pred)),
        "exactitud_balanceada": float(balanced_accuracy_score(y, pred)),
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "sensibilidad": {c: float(s) for c, s in zip(CLASES, sens)},
        "valor_predictivo_positivo": {c: float(v) for c, v in zip(CLASES, vpp)},
        "matriz_confusion": {"filas_real_columnas_predicha": CLASES, "valores": cm.tolist()},
    }
    if prob is not None:
        m["auc_macro"] = float(roc_auc_score(y, prob, multi_class="ovr", average="macro"))
    return m


def _intervalo(y: np.ndarray, pred: np.ndarray, n: int = 2000) -> dict:
    """IC 95 % por bootstrap de la exactitud y de la sensibilidad de «patológica»."""
    rng = np.random.default_rng(SEMILLA)
    exact, sens_p = [], []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        exact.append(float(np.mean(y[i] == pred[i])))
        pat = y[i] == 2
        if pat.any():
            sens_p.append(float(np.mean(pred[i][pat] == 2)))
    return {"exactitud_ic95": [round(float(np.percentile(exact, 2.5)), 4), round(float(np.percentile(exact, 97.5)), 4)],
            "sensibilidad_patologica_ic95": [round(float(np.percentile(sens_p, 2.5)), 4),
                                             round(float(np.percentile(sens_p, 97.5)), 4)]}


def entrenar(registro=print) -> tuple[object, dict]:
    """Compara modelos y conjuntos de variables; devuelve (modelo final, ficha)."""
    from sklearn.base import clone
    from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split

    X, y, duplicados = cargar_datos()
    X_e, X_p, y_e, y_p = train_test_split(X, y, test_size=0.20, stratify=y, random_state=SEMILLA)
    registro(f"{len(X)} registros ({duplicados} duplicados quitados): {len(X_e)} para elegir, {len(X_p)} de prueba")
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)

    # El suelo: decir siempre «normal» (la clase mayoritaria).
    comparativa = {"constante_normal": {"descripcion": "Siempre «normal» (suelo)",
                                        "cv": _metricas(y_e, np.zeros_like(y_e))}}
    for conjunto, columnas in CONJUNTOS.items():
        for clave, (desc, fabrica) in _candidatos().items():
            t0 = time.perf_counter()
            prob = cross_val_predict(fabrica(), X_e[columnas], y_e, cv=cv, method="predict_proba")
            m = _metricas(y_e, prob.argmax(1), prob)
            comparativa[f"{clave}__{conjunto}"] = {"descripcion": f"{desc} · {len(columnas)} variables", "cv": m}
            registro(f"  {clave:<20} {conjunto:<12} F1 macro {m['f1_macro']:.3f}  exactitud {m['exactitud']:.3f}  "
                     f"sens. patológica {m['sensibilidad']['patologica']:.3f}  ({time.perf_counter() - t0:.0f} s)")

    aprendidos = {k: v for k, v in comparativa.items() if "__" in k}
    mejor = max(aprendidos, key=lambda k: aprendidos[k]["cv"]["f1_macro"])
    # Preferir 11 variables si rinden casi igual: menos datos que pedir, menos errores al cargarlos.
    clave, conjunto = mejor.split("__")
    alternativa = f"{clave}__nucleo_11"
    if conjunto != "nucleo_11" and aprendidos[mejor]["cv"]["f1_macro"] - aprendidos[alternativa]["cv"]["f1_macro"] < 0.01:
        mejor, conjunto = alternativa, "nucleo_11"
    columnas = CONJUNTOS[conjunto]
    registro(f"Elegido por validación cruzada: {mejor}")

    modelo = clone(_candidatos()[clave][1]()).fit(X_e[columnas], y_e)
    prob_p = modelo.predict_proba(X_p[columnas])
    pred_p = prob_p.argmax(1)
    prueba = _metricas(y_p, pred_p, prob_p) | _intervalo(y_p, pred_p)
    registro(f"PRUEBA ({len(y_p)} registros nunca vistos): exactitud {prueba['exactitud']:.3f} "
             f"{prueba['exactitud_ic95']}, F1 macro {prueba['f1_macro']:.3f}, sensibilidad patológica "
             f"{prueba['sensibilidad']['patologica']:.3f} {prueba['sensibilidad_patologica_ic95']}")

    ficha = {
        "nombre": NOMBRE_MODELO,
        "algoritmo": mejor,
        "descripcion": aprendidos[mejor]["descripcion"],
        "variables": [VARIABLES[c][0] for c in columnas],
        "columnas_dataset": columnas,
        "clases": CLASES,
        "dataset": "UCI Cardiotocography / SisPorto (Ayres-de-Campos 2000), consenso de 3 obstetras",
        "registros": len(X), "duplicados_quitados": duplicados,
        "registros_prueba": len(y_p),
        "distribucion_prueba": {c: int((y_p == i).sum()) for i, c in enumerate(CLASES)},
        "comparativa_validacion_cruzada": comparativa,
        "prueba": prueba,
        "entrenado_con_datos_reales": True,
        "limites": [
            "Sin identificador de paciente: no se pudo partir por gestante.",
            "Un hospital (Porto) y un programa de análisis (SisPorto): validar con el monitor local.",
            "Apoya la lectura del trazado; la conducta la decide el obstetra con la clasificación FIGO.",
        ],
        "fecha_entrenamiento": time.strftime("%Y-%m-%d %H:%M"),
    }
    return modelo, ficha


# ─────────────────────────────── guardar / servir ──────────────────────────

def directorio_modelos() -> Path:
    from django.conf import settings

    return Path(settings.ML_MODELOS_DIR) / NOMBRE_MODELO


def guardar(modelo, ficha: dict, version: str | None = None) -> Path:
    import joblib

    base = directorio_modelos()
    existentes = [int(d.name) for d in base.glob("*") if d.name.isdigit()] if base.exists() else []
    carpeta = base / (version or str(max(existentes, default=0) + 1))
    carpeta.mkdir(parents=True, exist_ok=True)
    joblib.dump(modelo, carpeta / "modelo.joblib")
    (carpeta / "ficha.json").write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    (carpeta / "columnas.json").write_text(json.dumps(ficha["columnas_dataset"]), encoding="utf-8")
    cargar.cache_clear()
    return carpeta


@lru_cache(maxsize=1)
def cargar() -> tuple[object, dict]:
    """(modelo, ficha) de la versión más alta. Solo lee de ML_MODELOS_DIR (un
    .joblib es un pickle: cargarlo ejecuta código)."""
    with _cerrojo:
        base = directorio_modelos()
        versiones = sorted((d for d in base.glob("*") if d.name.isdigit() and (d / "modelo.joblib").exists()),
                           key=lambda d: int(d.name)) if base.exists() else []
        if not versiones:
            raise CTGNoDisponible("No hay un modelo de cardiotocografía entrenado. Se entrena con "
                                  "`python manage.py entrenar_modelo_ctg`.")
        carpeta = versiones[-1]
        columnas = json.loads((carpeta / "columnas.json").read_text(encoding="utf-8"))
        if not set(columnas) <= set(VARIABLES):
            raise CTGNoDisponible(f"El modelo {carpeta.name} usa variables que el sistema no conoce; reentrénelo.")
        import joblib

        modelo = joblib.load(carpeta / "modelo.joblib")
        ficha = json.loads((carpeta / "ficha.json").read_text(encoding="utf-8")) | {"version": carpeta.name}
        return modelo, ficha


def variables_requeridas() -> list[dict]:
    """Lo que hay que cargar en el formulario, según el modelo en uso."""
    try:
        _, ficha = cargar()
        columnas = ficha["columnas_dataset"]
    except CTGNoDisponible:
        columnas = NUCLEO
    return [{"clave": VARIABLES[c][0], "etiqueta": VARIABLES[c][1], "unidad": VARIABLES[c][2],
             "minimo": VARIABLES[c][3], "maximo": VARIABLES[c][4]} for c in columnas]


def clasificar(valores: dict[str, float]) -> dict:
    """Clase, probabilidades y la fiabilidad medida del modelo en uso."""
    modelo, ficha = cargar()
    columnas = ficha["columnas_dataset"]
    faltan = [VARIABLES[c][1] for c in columnas if valores.get(VARIABLES[c][0]) is None]
    if faltan:
        raise CTGNoDisponible("Faltan datos del registro: " + ", ".join(faltan) + ".")
    fuera = [f"{VARIABLES[c][1]} ({valores[VARIABLES[c][0]]})" for c in columnas
             if not (VARIABLES[c][3] <= float(valores[VARIABLES[c][0]]) <= VARIABLES[c][4])]
    if fuera:
        raise CTGNoDisponible("Valores fuera de rango: " + ", ".join(fuera) + ".")
    fila = pd.DataFrame([[float(valores[VARIABLES[c][0]]) for c in columnas]], columns=columnas)
    prob = modelo.predict_proba(fila)[0]
    clase = CLASES[int(np.argmax(prob))]
    prueba = ficha["prueba"]
    return {
        "clase": clase,
        "clase_nombre": NOMBRES_CLASE[clase],
        "probabilidades": {c: round(float(p), 4) for c, p in zip(CLASES, prob)},
        "modelo": {"version": ficha["version"], "algoritmo": ficha["descripcion"], "dataset": ficha["dataset"],
                   "exactitud_prueba": round(prueba["exactitud"], 3),
                   "exactitud_ic95": prueba["exactitud_ic95"],
                   "sensibilidad_patologica": round(prueba["sensibilidad"]["patologica"], 3),
                   "registros_prueba": ficha["registros_prueba"]},
        "advertencias": ["Apoyo a la lectura del trazado: la conducta se decide con la clasificación FIGO "
                         "y el criterio del obstetra."] + (
            ["El modelo duda entre clases: revise el trazado completo."] if float(prob.max()) < 0.6 else []),
    }
