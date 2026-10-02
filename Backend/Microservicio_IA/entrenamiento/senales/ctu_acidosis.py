"""Acidemia fetal al nacer desde el monitoreo intraparto (CTU-UHB, PhysioNet), medida sin trampas.

    python entrenamiento/senales/ctu_acidosis.py

Datos: CTU-UHB Intrapartum Cardiotocography Database (Chudáček et al. 2014,
PhysioNet, ODC-By 1.0): 552 monitoreos de la Universidad de Brno con la
gasometría de la arteria umbilical al nacer.

Protocolo fijado ANTES de mirar la prueba:
  · Objetivo: acidemia = pH arterial umbilical < 7,15 (también se informa < 7,05).
  · Entradas: SOLO lo que se conoce antes de nacer: los últimos 30 minutos de la
    primera etapa (antes de «Pos. II.st.») y los factores maternos. Nada de
    Apgar, peso, vía del parto ni duración de las etapas (se saben después).
  · 20 % estratificado de prueba; el 80 % restante, 5 pliegues para elegir
    modelo y umbral (sensibilidad >= 0,8 en la validación cruzada).
  · Referencia: regresión logística con tres rasgos clásicos (línea de base,
    variabilidad, desaceleraciones). Si el modelo completo no le gana, se dice.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import wfdb
from scipy.signal import welch
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
DATOS = AQUI.parents[1] / "datos" / "extraidos" / "obstetricia" / "ctu_uhb" / \
    "ctu-chb-intrapartum-cardiotocography-database-1.0.0"
SALIDA = AQUI / "salidas" / "ctu_acidosis"
SEMILLA = 2026
HZ = 4
VENTANA_MIN = 30
MATERNOS = ["Age", "Gravidity", "Parity", "Diabetes", "Hypertension", "Preeclampsia", "Liq. praecox", "Pyrexia",
            "Meconium", "Gest. weeks", "Presentation", "Induced"]


def cabecera(ruta: Path) -> dict:
    valores = {}
    for linea in ruta.read_text().splitlines():
        m = re.match(r"#\s*([A-Za-z0-9 .()/!]+?)\s{2,}(-?[0-9.]+)\s*$", linea)
        if m:
            valores[m.group(1).strip()] = float(m.group(2))
    return valores


def rasgos_fcf(fcf: np.ndarray, uc: np.ndarray) -> dict:
    """Rasgos de la frecuencia cardíaca fetal en la ventana (4 Hz). 0 = pérdida de señal."""
    valida = (fcf > 50) & (fcf < 220)
    perdida = 1 - valida.mean()
    f = pd.Series(np.where(valida, fcf, np.nan)).interpolate(limit_direction="both").to_numpy()
    if np.isnan(f).all():
        return {"perdida_senal": 1.0}
    linea = pd.Series(f).rolling(HZ * 60 * 5, center=True, min_periods=HZ * 60).median().to_numpy()
    base = float(np.nanmedian(linea))
    # Variabilidad a corto plazo: diferencias de medias de 2,5 s (Dawes-Redman simplificado)
    medias = f[: len(f) // 10 * 10].reshape(-1, 10).mean(1)
    stv = float(np.mean(np.abs(np.diff(medias))))
    # Variabilidad a largo plazo: amplitud por minuto
    por_min = f[: len(f) // (HZ * 60) * HZ * 60].reshape(-1, HZ * 60)
    ltv = float(np.mean(por_min.max(1) - por_min.min(1)))
    # Desaceleraciones / aceleraciones: >= 15 lpm respecto de la línea durante >= 15 s
    def episodios(mascara):
        n, largo, area = 0, 0, 0.0
        cuenta = 0
        for i, v in enumerate(mascara):
            if v:
                cuenta += 1
            else:
                if cuenta >= 15 * HZ:
                    n += 1
                    largo += cuenta
                cuenta = 0
        if cuenta >= 15 * HZ:
            n += 1
            largo += cuenta
        return n, largo / HZ
    bajo = f < linea - 15
    n_dec, seg_dec = episodios(bajo)
    n_acel, _ = episodios(f > linea + 15)
    area_dec = float(np.nansum(np.clip(linea - f, 0, None)[bajo]) / HZ / 60)
    fr, pot = welch(f - np.nanmean(f), fs=HZ, nperseg=min(len(f), 1024))
    banda = lambda a, b: float(pot[(fr >= a) & (fr < b)].sum())  # noqa: E731
    total = banda(0.0, 1.0) or 1e-9
    contracciones = 0
    if uc is not None and np.isfinite(uc).any():
        u = pd.Series(uc).interpolate(limit_direction="both").to_numpy()
        u = pd.Series(u).rolling(HZ * 10, center=True, min_periods=1).mean().to_numpy()
        umbral = np.nanmedian(u) + 15
        sobre = u > umbral
        contracciones = int(np.sum(sobre[1:] & ~sobre[:-1]))
    return {"perdida_senal": perdida, "linea_base": base, "stv": stv, "ltv": ltv, "media": float(np.nanmean(f)),
            "desvio": float(np.nanstd(f)), "minimo_p5": float(np.nanpercentile(f, 5)),
            "desaceleraciones": n_dec, "segundos_en_desaceleracion": seg_dec, "area_desaceleraciones": area_dec,
            "aceleraciones": n_acel, "contracciones_30min": contracciones,
            "potencia_vlf": banda(0, 0.03) / total, "potencia_lf": banda(0.03, 0.15) / total,
            "potencia_mf": banda(0.15, 0.5) / total, "potencia_hf": banda(0.5, 1.0) / total}


def tabla() -> pd.DataFrame:
    filas = []
    for hea in sorted(DATOS.glob("*.hea")):
        c = cabecera(hea)
        reg = wfdb.rdrecord(str(hea.with_suffix("")))
        fcf = reg.p_signal[:, reg.sig_name.index("FHR")]
        uc = reg.p_signal[:, reg.sig_name.index("UC")]
        fin = int(c.get("Pos. II.st.", len(fcf)))
        fin = len(fcf) if fin <= 0 or fin > len(fcf) else fin
        ini = max(0, fin - VENTANA_MIN * 60 * HZ)
        fila = {"registro": hea.stem, "ph": c.get("pH"), **{k: c.get(k) for k in MATERNOS}}
        fila |= rasgos_fcf(fcf[ini:fin], uc[ini:fin])
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
    df = df[df["ph"].notna()].reset_index(drop=True)
    candidatos = {
        "logistica": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                   LogisticRegression(max_iter=3000, class_weight="balanced", C=0.3)),
        "bosque_aleatorio": make_pipeline(SimpleImputer(strategy="median"),
                                          RandomForestClassifier(500, min_samples_leaf=5, class_weight="balanced",
                                                                 random_state=SEMILLA)),
        "gradient_boosting": HistGradientBoostingClassifier(max_iter=200, learning_rate=0.03, max_depth=3,
                                                            class_weight="balanced", random_state=SEMILLA),
    }
    rasgos = [c for c in df.columns if c not in ("registro", "ph")]
    clasicos = ["linea_base", "stv", "desaceleraciones"]
    resultado = {"dataset": "CTU-UHB Intrapartum CTG (PhysioNet, Brno, 552 registros)",
                 "registros": len(df), "ventana": f"últimos {VENTANA_MIN} min de la primera etapa",
                 "variables": rasgos}
    for nombre, corte in (("acidemia_ph_menor_7_15", 7.15), ("acidemia_grave_ph_menor_7_05", 7.05)):
        y = (df["ph"] < corte).astype(int).to_numpy()
        X = df[rasgos].to_numpy(dtype=float)
        idx_e, idx_p = train_test_split(np.arange(len(df)), test_size=0.2, stratify=y, random_state=SEMILLA)
        cv = StratifiedKFold(5, shuffle=True, random_state=SEMILLA)
        cv_auc = {}
        for n_m, m in candidatos.items():
            p = cross_val_predict(clone(m), X[idx_e], y[idx_e], cv=cv, method="predict_proba")[:, 1]
            cv_auc[n_m] = (roc_auc_score(y[idx_e], p), p)
        mejor = max(cv_auc, key=lambda k: cv_auc[k][0])
        umbral = umbral_sens(y[idx_e], cv_auc[mejor][1])
        modelo = clone(candidatos[mejor]).fit(X[idx_e], y[idx_e])
        ref = clone(candidatos["logistica"])
        Xc = df[clasicos].to_numpy(dtype=float)
        p_ref_cv = cross_val_predict(clone(ref), Xc[idx_e], y[idx_e], cv=cv, method="predict_proba")[:, 1]
        ref.fit(Xc[idx_e], y[idx_e])
        resultado[nombre] = {
            "prevalencia": round(float(y.mean()), 4),
            "auc_validacion_cruzada": {k: round(v[0], 4) for k, v in cv_auc.items()},
            "modelo_elegido": mejor,
            "prueba": evaluar(y[idx_p], modelo.predict_proba(X[idx_p])[:, 1], umbral),
            "referencia_3_rasgos_clasicos": evaluar(y[idx_p], ref.predict_proba(Xc[idx_p])[:, 1],
                                                     umbral_sens(y[idx_e], p_ref_cv)),
        }
        if nombre.startswith("acidemia_ph"):
            import joblib

            joblib.dump(modelo, SALIDA / "modelo.joblib")
            (SALIDA / "columnas.json").write_text(json.dumps(rasgos), encoding="utf-8")
    (SALIDA / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in resultado.items() if k != "variables"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
