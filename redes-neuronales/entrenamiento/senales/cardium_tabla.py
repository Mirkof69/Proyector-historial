"""¿Predicen las variables clínicas maternas la cardiopatía congénita? (tablas públicas de CARDIUM)

    python entrenamiento/senales/cardium_tabla.py

Datos: CARDIUM (BCV-Uniandes, ICCV 2025, CC BY-NC 4.0): registro clínico de 1.103
gestantes colombianas (2013–2024), 79 con cardiopatía congénita. Las imágenes
piden formulario; las tablas están en el repositorio.

Fijado ANTES de mirar la prueba:
  · Una fila por paciente; 20 % estratificado de prueba; 5 pliegues en el resto
    para elegir modelo y umbral (sensibilidad >= 0,8 en la validación cruzada).
  · Dos variantes:
      A) todas las variables (como el artículo, que informa AUC 0,79 solo con tablas);
      B) solo lo que se conoce ANTES de la ecografía: sin «anomalía cromosómica»
         ni «procedimientos de tamizaje» (suelen registrarse después de sospechar
         la cardiopatía) ni semanas de gestación de la imagen.
  · Categorías (antecedentes, fármacos): presencia sí/no de las que aparecen al
    menos 4 veces en ENTRENAMIENTO (nada derivado de la etiqueta).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from ctu_acidosis import evaluar, umbral_sens  # noqa: E402

ARCHIVO = AQUI.parents[1] / "datos" / "crudos" / "obstetricia" / "cardium_tablas" / \
    "cardium_clinical_data_wnm_translated_final_cleaned.json"
SALIDA = AQUI / "salidas" / "cardium_tabla"
SEMILLA = 2026
CATEGORICAS = ["pathological_history", "hereditary_history", "pharmacological_history"]
POSTERIORES = ["chromosomal_abnormality", "screening_procedures", "gestational_week_of_imaging", "gestational_age"]


def primera(v):
    if isinstance(v, list):
        v = [x for x in v if x not in (-1, -1.0, None)]
        return float(np.mean(v)) if v else np.nan
    return np.nan if v in (-1, -1.0, None) else float(v)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
    df = pd.DataFrame(datos).drop_duplicates("id").reset_index(drop=True)
    y = df["CHD"].astype(int).to_numpy()
    numericas = [c for c in df.columns if c not in CATEGORICAS + ["id", "CHD", "ultrasound_date"]]
    base = pd.DataFrame({c: df[c].map(primera) for c in numericas})
    idx_e, idx_p = train_test_split(np.arange(len(df)), test_size=0.2, stratify=y, random_state=SEMILLA)
    frecuentes = {}
    for c in CATEGORICAS:
        conteo = pd.Series([x for lista in df.loc[idx_e, c] for x in (lista or [])]).value_counts()
        frecuentes[c] = list(conteo[conteo >= 4].index)
        for cat in frecuentes[c]:
            base[f"{c}:{cat}"] = df[c].map(lambda lista, cat=cat: float(cat in (lista or [])))
    candidatos = {
        "logistica": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                   LogisticRegression(max_iter=4000, class_weight="balanced", C=0.1)),
        "bosque_aleatorio": make_pipeline(SimpleImputer(strategy="median"),
                                          RandomForestClassifier(500, min_samples_leaf=3, class_weight="balanced",
                                                                 random_state=SEMILLA)),
        "gradient_boosting": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, max_depth=3,
                                                            class_weight="balanced", random_state=SEMILLA),
    }
    resultado = {"dataset": "CARDIUM, tablas clínicas (BCV-Uniandes, CC BY-NC 4.0)", "pacientes": len(df),
                 "con_cardiopatia": int(y.sum())}
    variantes = {"A_todas_las_variables": list(base.columns),
                 "B_solo_antes_de_la_ecografia": [c for c in base.columns if c not in POSTERIORES]}
    for nombre, columnas in variantes.items():
        X = base[columnas].to_numpy(dtype=float)
        cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
        cv_auc = {}
        for n_m, m in candidatos.items():
            p = cross_val_predict(clone(m), X[idx_e], y[idx_e], cv=cv, method="predict_proba")[:, 1]
            cv_auc[n_m] = (roc_auc_score(y[idx_e], p), p)
        mejor = max(cv_auc, key=lambda k: cv_auc[k][0])
        modelo = clone(candidatos[mejor]).fit(X[idx_e], y[idx_e])
        resultado[nombre] = {"variables": len(columnas),
                             "auc_validacion_cruzada": {k: round(v[0], 4) for k, v in cv_auc.items()},
                             "modelo_elegido": mejor,
                             "prueba": evaluar(y[idx_p], modelo.predict_proba(X[idx_p])[:, 1],
                                               umbral_sens(y[idx_e], cv_auc[mejor][1]))}
    (SALIDA / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
