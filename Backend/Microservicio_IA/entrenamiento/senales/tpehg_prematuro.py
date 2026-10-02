"""Parto prematuro desde el electrohisterograma (TPEHG DB, PhysioNet), medido sin trampas.

    python entrenamiento/senales/tpehg_prematuro.py

Datos: Term-Preterm EHG Database (Fele-Žorž et al. 2008, PhysioNet, ODC-By):
300 registros de 30 min de la actividad eléctrica del útero (3 canales,
20 Hz), tomados hacia la semana 23 o la 31, y la semana en que nació el bebé.

Protocolo fijado ANTES de mirar la prueba:
  · Objetivo: parto prematuro = nacimiento antes de la semana 37.
  · Entradas: rasgos del EHG en la banda 0,34–1 Hz (la de las contracciones que
    preceden al parto) de cada canal y los datos clínicos conocidos al momento
    del registro (edad, paridad, abortos previos, peso, hipertensión, diabetes,
    sangrado, embudización cervical, tabaco, semana del registro).
  · SIN sobremuestreo (SMOTE/ADASYN) antes de partir: muchos trabajos con este
    dataset informan 95–99 % porque las copias sintéticas de un caso caen en
    entrenamiento y prueba a la vez. Aquí el desbalance se maneja con pesos.
  · 20 % estratificado de prueba; 5 pliegues en el resto para elegir modelo y
    umbral (sensibilidad >= 0,8 en la validación cruzada).
  · Referencia: solo los datos clínicos (sin EHG). Si el EHG no aporta, se dice.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import wfdb
from scipy.signal import butter, filtfilt, welch
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salidas" / "tpehg_prematuro"
SEMILLA = 2026
HZ = 20
CLINICOS = ["Rectime", "Age", "Parity", "Abortions", "Weight", "Hypertension", "Diabetes", "Placental_position",
            "Bleeding_first_trimester", "Bleeding_second_trimester", "Funneling", "Smoker"]


def carpeta() -> Path:
    base = AQUI.parents[1] / "datos" / "extraidos" / "obstetricia" / "tpehg"
    return next(base.rglob("tpehg*.hea")).parent


def cabecera(ruta: Path) -> dict:
    """Comentarios «#Clave valor» del .hea; «None» y «N/A» quedan vacíos; yes/no → 1/0."""
    valores = {}
    for linea in ruta.read_text(errors="replace").splitlines():
        m = re.match(r"#\s*([A-Za-z][A-Za-z_]*)\s+(\S+)\s*$", linea)
        if not m:
            continue
        clave, v = m.group(1).strip(), m.group(2).strip().lower()
        if v in ("yes", "no", "positive", "negative"):
            valores[clave] = 1.0 if v in ("yes", "positive") else 0.0
        elif v in ("front", "end"):  # posición de la placenta
            valores[clave] = 1.0 if v == "front" else 0.0
        else:
            try:
                valores[clave] = float(v)
            except ValueError:
                valores[clave] = np.nan
    return valores


def entropia_muestral(x: np.ndarray, m: int = 2, r: float = 0.15) -> float:
    """Sample entropy sobre la señal submuestreada a 4 Hz (rápido y suficiente para 0,34–1 Hz)."""
    x = x[:: HZ // 4][:4000]
    x = (x - x.mean()) / (x.std() or 1.0)
    n = len(x)

    def phi(k):
        plantillas = np.lib.stride_tricks.sliding_window_view(x, k)
        cuenta = 0
        for i in range(len(plantillas) - 1):
            cuenta += np.sum(np.max(np.abs(plantillas[i + 1:] - plantillas[i]), axis=1) <= r)
        return cuenta

    b, a = phi(m), phi(m + 1)
    return float(-np.log(a / b)) if a > 0 and b > 0 and n > m + 1 else np.nan


def rasgos_ehg(senal: np.ndarray) -> dict:
    b, a = butter(4, [0.34 / (HZ / 2), 1.0 / (HZ / 2)], btype="band")
    salida = {}
    for c in range(senal.shape[1]):
        x = filtfilt(b, a, senal[:, c] - np.mean(senal[:, c]))
        x = x[HZ * 180: -HZ * 180] if len(x) > HZ * 600 else x   # fuera los primeros y últimos 3 min (artefactos)
        f, p = welch(x, fs=HZ, nperseg=HZ * 60)
        banda = (f >= 0.34) & (f <= 1.0)
        acumulada = np.cumsum(p[banda])
        salida |= {f"c{c + 1}_rms": float(np.sqrt(np.mean(x ** 2))),
                   f"c{c + 1}_frec_pico": float(f[banda][np.argmax(p[banda])]),
                   f"c{c + 1}_frec_mediana": float(f[banda][np.searchsorted(acumulada, acumulada[-1] / 2)]),
                   f"c{c + 1}_entropia": entropia_muestral(x)}
    return salida


def tabla() -> pd.DataFrame:
    filas = []
    for hea in sorted(carpeta().glob("tpehg*.hea")):
        c = cabecera(hea)
        reg = wfdb.rdrecord(str(hea.with_suffix("")))
        crudos = [reg.sig_name.index(n) for n in ("1", "2", "3")]  # canales sin filtrar; se filtra aquí
        fila = {"registro": hea.stem, "semana_parto": c.get("Gestation"),
                **{k: c.get(k, np.nan) for k in CLINICOS}}
        fila |= rasgos_ehg(reg.p_signal[:, crudos])
        filas.append(fila)
    return pd.DataFrame(filas)


def ic(y, p, n=2000):
    rng = np.random.default_rng(SEMILLA)
    v = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if 0 < y[i].sum() < len(i):
            v.append(roc_auc_score(y[i], p[i]))
    return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]


def evaluar(y, p, umbral) -> dict:
    pred = (p >= umbral).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"casos_positivos": int(y.sum()), "casos_negativos": int(len(y) - y.sum()),
            "auc": round(float(roc_auc_score(y, p)), 4), "auc_ic95": ic(y, p),
            "auc_pr": round(float(average_precision_score(y, p)), 4), "umbral": round(float(umbral), 4),
            "sensibilidad": round(tp / max(1, tp + fn), 4), "especificidad": round(tn / max(1, tn + fp), 4),
            "vpp": round(tp / max(1, tp + fp), 4), "verdaderos_positivos": int(tp), "falsos_negativos": int(fn),
            "falsos_positivos": int(fp)}


def umbral_sens(y, p, objetivo=0.8) -> float:
    for u in sorted(np.unique(p), reverse=True):
        if ((p >= u) & (y == 1)).sum() / max(1, y.sum()) >= objetivo:
            return float(u)
    return 0.0


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    df = tabla()
    df.to_csv(SALIDA / "rasgos.csv", index=False)
    df = df[df["semana_parto"].notna()].reset_index(drop=True)
    y = (df["semana_parto"] < 37).astype(int).to_numpy()
    candidatos = {
        "logistica": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                   LogisticRegression(max_iter=3000, class_weight="balanced", C=0.3)),
        "bosque_aleatorio": make_pipeline(SimpleImputer(strategy="median"),
                                          RandomForestClassifier(500, min_samples_leaf=3, class_weight="balanced",
                                                                 random_state=SEMILLA)),
        "gradient_boosting": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, max_depth=3,
                                                            class_weight="balanced", random_state=SEMILLA),
    }
    todas = [c for c in df.columns if c not in ("registro", "semana_parto")]
    idx_e, idx_p = train_test_split(np.arange(len(df)), test_size=0.2, stratify=y, random_state=SEMILLA)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
    resultado = {"dataset": "Term-Preterm EHG Database (PhysioNet, Ljubljana)", "registros": len(df),
                 "prematuros": int(y.sum())}
    for nombre, columnas in (("ehg_y_clinicos", todas), ("referencia_solo_clinicos", CLINICOS)):
        X = df[columnas].to_numpy(dtype=float)
        cv_auc = {}
        for n_m, m in candidatos.items():
            p = cross_val_predict(clone(m), X[idx_e], y[idx_e], cv=cv, method="predict_proba")[:, 1]
            cv_auc[n_m] = (roc_auc_score(y[idx_e], p), p)
        mejor = max(cv_auc, key=lambda k: cv_auc[k][0])
        modelo = clone(candidatos[mejor]).fit(X[idx_e], y[idx_e])
        resultado[nombre] = {"auc_validacion_cruzada": {k: round(v[0], 4) for k, v in cv_auc.items()},
                             "modelo_elegido": mejor,
                             "prueba": evaluar(y[idx_p], modelo.predict_proba(X[idx_p])[:, 1],
                                               umbral_sens(y[idx_e], cv_auc[mejor][1]))}
    (SALIDA / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
