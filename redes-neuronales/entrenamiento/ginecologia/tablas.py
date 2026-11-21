"""Modelos supervisados en tabla (ginecología y obstetricia), medidos sin trampas.

    python entrenamiento/ginecologia/tablas.py

Protocolo fijado ANTES de mirar la prueba:
  · Filas idénticas fuera (en riesgo materno son 562 de 1.014: con ellas, la
    misma fila cae en entrenamiento y en prueba y la exactitud se infla).
  · 20 % estratificado como prueba; con el 80 % restante, validación cruzada
    de 5 pliegues para elegir entre modelos. La prueba se mira una sola vez.
  · Siempre contra una referencia sin aprendizaje (la clase más frecuente o la
    regla clínica): un modelo que no le gana no se usa.

Datasets (UCI, CC BY 4.0):
  · 383 Cervical cancer (Risk Factors): 858 pacientes, Hospital Universitario de
    Caracas. Objetivo: biopsia positiva. Dos preguntas distintas:
      A) solo factores de riesgo (lo que se sabe sin examinar);
      B) con las pruebas de tamizaje (colposcopía de Hinselmann, Schiller,
         citología): ¿a quién biopsiar? La referencia es la regla «alguna
         prueba positiva».
  · 863 Maternal Health Risk: edad, presión, glucemia, temperatura y
    frecuencia cardíaca → riesgo bajo / medio / alto (Bangladés, IoT).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, confusion_matrix, f1_score,
                             roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
TABLAS = AQUI.parents[1] / "datos" / "extraidos" / "ginecologia" / "tablas"
SALIDA = AQUI / "salidas" / "tablas"
SEMILLA = 2026

CANDIDATOS = {
    "logistica": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                               LogisticRegression(max_iter=2000, class_weight="balanced")),
    "bosque_aleatorio": make_pipeline(SimpleImputer(strategy="median"),
                                      RandomForestClassifier(400, min_samples_leaf=3, class_weight="balanced",
                                                             random_state=SEMILLA)),
    "gradient_boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
                                                        class_weight="balanced", random_state=SEMILLA),
}


def ic_bootstrap(y, pred, funcion, veces=2000):
    rng = np.random.default_rng(SEMILLA)
    v = []
    for _ in range(veces):
        i = rng.integers(0, len(y), len(y))
        if len(np.unique(y[i])) < 2:
            continue
        v.append(funcion(y[i], pred[i]))
    return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)]


def binario(y, prob, umbral) -> dict:
    pred = (prob >= umbral).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"casos_positivos": int(y.sum()), "casos_negativos": int((1 - y).sum()),
            "auc": round(float(roc_auc_score(y, prob)), 4), "auc_ic95": ic_bootstrap(y, prob, roc_auc_score),
            "auc_pr": round(float(average_precision_score(y, prob)), 4),
            "umbral": round(float(umbral), 4), "sensibilidad": round(tp / max(1, tp + fn), 4),
            "especificidad": round(tn / max(1, tn + fp), 4), "vpp": round(tp / max(1, tp + fp), 4),
            "verdaderos_positivos": int(tp), "falsos_negativos": int(fn), "falsos_positivos": int(fp)}


def umbral_por_sensibilidad(y, prob, objetivo=0.9) -> float:
    """Mayor umbral con sensibilidad >= objetivo en la validación cruzada (no en la prueba)."""
    for u in sorted(np.unique(prob), reverse=True):
        if ((prob >= u) & (y == 1)).sum() / max(1, y.sum()) >= objetivo:
            return float(u)
    return 0.0


def cancer_cervicouterino() -> dict:
    df = pd.read_csv(TABLAS / "risk_factors_cervical_cancer.csv", na_values="?").drop_duplicates()
    y = df["Biopsy"].to_numpy()
    pruebas = ["Hinselmann", "Schiller", "Citology"]
    # Diagnósticos previos (Dx:*) y tiempos con 92 % de faltantes: fuera
    riesgo = [c for c in df.columns if c not in pruebas + ["Biopsy"] and not c.startswith("Dx")
              and not c.startswith("STDs: Time")]
    res = {"dataset": "UCI 383 Cervical cancer (Risk Factors) · Hospital Universitario de Caracas",
           "pacientes_unicas": len(df), "biopsias_positivas": int(y.sum())}
    for pregunta, columnas in (("A_solo_factores_de_riesgo", riesgo), ("B_con_pruebas_de_tamizaje", riesgo + pruebas)):
        X = df[columnas].to_numpy(dtype=float)
        Xe, Xp, ye, yp = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEMILLA)
        cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
        cv_auc = {}
        for nombre, modelo in CANDIDATOS.items():
            p = cross_val_predict(clone(modelo), Xe, ye, cv=cv, method="predict_proba")[:, 1]
            cv_auc[nombre] = (roc_auc_score(ye, p), p)
        mejor = max(cv_auc, key=lambda k: cv_auc[k][0])
        umbral = umbral_por_sensibilidad(ye, cv_auc[mejor][1])
        modelo = clone(CANDIDATOS[mejor]).fit(Xe, ye)
        fila = {"variables": columnas, "auc_validacion_cruzada": {k: round(v[0], 4) for k, v in cv_auc.items()},
                "modelo_elegido": mejor, "prueba": binario(yp, modelo.predict_proba(Xp)[:, 1], umbral)}
        if pregunta.startswith("B"):
            regla = (df[pruebas].sum(axis=1) > 0).astype(int).to_numpy()
            _, regla_p = train_test_split(regla, test_size=0.2, stratify=y, random_state=SEMILLA)
            fila["referencia_regla_alguna_prueba_positiva"] = binario(yp, regla_p.astype(float), 0.5)
        res[pregunta] = fila
    return res


def riesgo_materno() -> dict:
    df = pd.read_csv(TABLAS / "Maternal Health Risk Data Set.csv")
    filas, unicas = len(df), df.drop_duplicates()
    # Misma combinación de variables con distinta etiqueta: no se sabe cuál es cierta
    conflictivas = unicas.duplicated(subset=unicas.columns[:-1], keep=False)
    unicas = unicas[~conflictivas]
    clases = ["low risk", "mid risk", "high risk"]
    X = unicas.drop(columns="RiskLevel").to_numpy(dtype=float)
    y = unicas["RiskLevel"].map(clases.index).to_numpy()
    Xe, Xp, ye, yp = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEMILLA)
    cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
    cv_bal = {}
    for nombre, modelo in CANDIDATOS.items():
        p = cross_val_predict(clone(modelo), Xe, ye, cv=cv)
        cv_bal[nombre] = round(float(balanced_accuracy_score(ye, p)), 4)
    mejor = max(cv_bal, key=cv_bal.get)
    modelo = clone(CANDIDATOS[mejor]).fit(Xe, ye)
    pred = modelo.predict(Xp)
    base = DummyClassifier(strategy="most_frequent").fit(Xe, ye).predict(Xp)
    cm = confusion_matrix(yp, pred, labels=[0, 1, 2])
    return {"dataset": "UCI 863 Maternal Health Risk (Bangladés)", "filas_originales": filas,
            "filas_unicas": int(len(df.drop_duplicates())), "conflictivas_excluidas": int(conflictivas.sum()),
            "casos_usados": int(len(unicas)), "balanced_accuracy_validacion_cruzada": cv_bal,
            "modelo_elegido": mejor,
            "prueba": {"casos": int(len(yp)), "exactitud": round(float((pred == yp).mean()), 4),
                       "exactitud_balanceada": round(float(balanced_accuracy_score(yp, pred)), 4),
                       "exactitud_balanceada_ic95": ic_bootstrap(yp, pred, balanced_accuracy_score),
                       "f1_macro": round(float(f1_score(yp, pred, average="macro")), 4),
                       "sensibilidad_riesgo_alto": round(float(cm[2, 2] / max(1, cm[2].sum())), 4),
                       "matriz_confusion": {"orden": clases, "valores": cm.tolist()}},
            "referencia_clase_mas_frecuente": {"exactitud": round(float((base == yp).mean()), 4),
                                               "exactitud_balanceada": round(float(
                                                   balanced_accuracy_score(yp, base)), 4)}}


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    resultado = {"cancer_cervicouterino": cancer_cervicouterino(), "riesgo_materno": riesgo_materno()}
    (SALIDA / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
