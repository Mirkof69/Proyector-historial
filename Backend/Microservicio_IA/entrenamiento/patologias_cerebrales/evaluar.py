"""Métricas honestas de la red de anomalías cerebrales.

    python evaluar.py   → salidas/metricas.json + INFORME.md

Antes: entrenar.py, prueba_otro_hospital.py y prueba_estilo.py.

Todo con intervalo de confianza del 95 % por bootstrap de imágenes originales
(2.000 remuestreos). Umbral fijo 0,5, decidido antes de entrenar.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_auc_score

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI / "salidas"
FAMILIAS = ["normal", "ventriculomegalia_hidrocefalia", "fosa_posterior", "encefalocele",
            "lesion_quistica_vascular"]
UMBRAL = 0.5
NOMBRE_FAMILIA = {"ventriculomegalia_hidrocefalia": "Ventriculomegalia / hidrocefalia",
                  "fosa_posterior": "Fosa posterior", "encefalocele": "Encefalocele",
                  "lesion_quistica_vascular": "Lesión quística, hemorrágica o vascular"}
NOMBRE_ANOMALIA = {
    "mild-ventriculomegaly": "Ventriculomegalia leve", "moderate-ventriculomegaly": "Ventriculomegalia moderada",
    "severe-ventriculomegaly": "Ventriculomegalia severa", "hydracenphaly": "Hidranencefalia",
    "colphocephaly": "Colpocefalia", "cerebellah-hypoplasia": "Hipoplasia cerebelosa",
    "anold-chiari-malformation": "Malformación de Arnold-Chiari", "m-magna": "Megacisterna magna",
    "encephalocele": "Encefalocele", "arachnoid-cyst": "Quiste aracnoideo", "polencephaly": "Porencefalia",
    "intracranial-hemorrdge": "Hemorragia intracraneal", "intracranial-tumor": "Tumor intracraneal",
    "vein-of-galen": "Aneurisma de la vena de Galeno", "holoprosencephaly": "Holoprosencefalia"}
rng = np.random.default_rng(2026)


def ic(valores):
    v = np.asarray([x for x in valores if x is not None and not np.isnan(x)])
    return [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)] if len(v) else None


def binarias(y, p):
    pred = p >= UMBRAL
    vp, fn = int(np.sum(pred & (y == 1))), int(np.sum(~pred & (y == 1)))
    vn, fp = int(np.sum(~pred & (y == 0))), int(np.sum(pred & (y == 0)))
    div = lambda a, b: a / b if b else float("nan")  # noqa: E731
    return {"sensibilidad": div(vp, vp + fn), "especificidad": div(vn, vn + fp),
            "vpp": div(vp, vp + fp), "vpn": div(vn, vn + fn), "tasa_falsos_positivos": div(fp, fp + vn),
            "exactitud": div(vp + vn, len(y)),
            "auc": roc_auc_score(y, p) if 0 < y.sum() < len(y) else float("nan"),
            "vp": vp, "fn": fn, "vn": vn, "fp": fp}


def con_ic(y, p, n=2000):
    base = binarias(y, p)
    muestras = {k: [] for k in ("sensibilidad", "especificidad", "vpp", "vpn", "tasa_falsos_positivos",
                                "exactitud", "auc")}
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        m = binarias(y[i], p[i])
        for k in muestras:
            muestras[k].append(m[k])
    return {k: ({"valor": round(v, 3), "ic95": ic(muestras[k])} if k in muestras else v) for k, v in base.items()}


def pacientes_duplicados():
    """Pacientes de FETAL_PLANES cuyas imágenes están TAMBIÉN entre las normales
    de Roboflow (se llaman «Patient00738_Plane3_…»). Sus cortes pueden haberse
    visto al entrenar con otro nombre: se excluyen de toda medida."""
    man = pd.read_csv(SALIDAS / "manifiesto.csv")
    rf = man[(man["fuente"] == "roboflow") & (man["familia"] == "normal")]["grupo"]
    return {"FP-P" + m.group(1) for g in rf if (m := re.search(r"Patient(\d+)", g))}


def main():
    duplicados = pacientes_duplicados()
    oof = pd.read_csv(SALIDAS / "predicciones_fuera_de_pliegue.csv")
    ext = pd.read_csv(SALIDAS / "predicciones_externas.csv")
    excluidas = int(oof["grupo"].isin(duplicados).sum() + ext["grupo"].isin(duplicados).sum())
    oof = oof[~oof["grupo"].isin(duplicados)]
    ext = ext[~ext["grupo"].isin(duplicados)]
    for d in (oof, ext):
        d["p_anomalia"] = 1 - d["p_normal"]
        d["y"] = (d["familia"] != "normal").astype(int)
        d["pred_familia"] = d[["p_" + f for f in FAMILIAS]].to_numpy().argmax(1)

    res = {"umbral": UMBRAL, "unidad": "imagen original (copias aumentadas promediadas)",
           "excluidas_por_duplicado": {"pacientes": len(duplicados), "imagenes": excluidas}}
    res["todas_fuera_de_pliegue"] = con_ic(oof["y"].to_numpy(), oof["p_anomalia"].to_numpy())
    rf = oof[oof["fuente"] == "roboflow"]
    # La prueba justa: normales y anomalías de la MISMA fuente. Si aquí cae el
    # AUC, la red estaría distinguiendo fuentes y no cerebros.
    res["solo_roboflow"] = con_ic(rf["y"].to_numpy(), rf["p_anomalia"].to_numpy())
    res["n"] = {"anomalias": int(oof["y"].sum()), "normales_roboflow": int(((rf["y"] == 0)).sum()),
                "normales_fetal_planes": int(((oof["fuente"] == "fetal_planes")).sum()),
                "externas": len(ext), "pacientes_externos": int(ext["grupo"].nunique())}

    fp_ext = ext["p_anomalia"] >= UMBRAL
    boot = [float(np.mean(rng.choice(fp_ext.to_numpy(), len(fp_ext)))) for _ in range(2000)]
    res["externa_falsos_positivos"] = {"valor": round(float(fp_ext.mean()), 4), "ic95": ic(boot),
                                       "fp": int(fp_ext.sum()), "n": len(ext),
                                       "por_ecografo": {e: {"fp": int(g["p_anomalia"].ge(UMBRAL).sum()), "n": len(g)}
                                                        for e, g in ext.groupby("ecografo")}}

    anom = oof[oof["y"] == 1]
    y_fam = anom["familia"].map(FAMILIAS.index).to_numpy()
    # Familia: argmax entre las 4 familias (dado que es anomalía)
    pred_fam = anom[["p_" + f for f in FAMILIAS[1:]]].to_numpy().argmax(1) + 1
    cm = confusion_matrix(y_fam, pred_fam, labels=range(1, 5))
    res["familia_entre_anomalias"] = {
        "exactitud": round(float((y_fam == pred_fam).mean()), 3),
        "ic95": ic([float(np.mean((y_fam == pred_fam)[i])) for i in
                    (rng.integers(0, len(y_fam), len(y_fam)) for _ in range(2000))]),
        "sensibilidad_por_familia": {FAMILIAS[k]: {"aciertos": int(cm[k - 1, k - 1]), "n": int(cm[k - 1].sum())}
                                     for k in range(1, 5)},
        "matriz_confusion": {"filas_real_columnas_predicha": FAMILIAS[1:], "valores": cm.tolist()},
    }
    res["deteccion_por_anomalia_fina"] = {
        e: {"detectadas": int((g["p_anomalia"] >= UMBRAL).sum()), "n": len(g)}
        for e, g in anom.groupby("etiqueta_fina")}
    res["auc_por_pliegue"] = {int(k): round(float(roc_auc_score(g["y"], g["p_anomalia"])), 3)
                              for k, g in oof.groupby("pliegue")}

    hc = pd.read_csv(SALIDAS / "predicciones_hc18.csv")
    alarma = (hc["p_anomalia"] >= UMBRAL).to_numpy()
    res["otro_hospital_hc18"] = {
        "valor": round(float(alarma.mean()), 4), "fp": int(alarma.sum()), "n": len(hc),
        "ic95": ic([float(np.mean(rng.choice(alarma, len(alarma)))) for _ in range(2000)]),
        "por_trimestre": {t: {"fp": int(g["p_anomalia"].ge(UMBRAL).sum()), "n": len(g)}
                          for t, g in hc.groupby("trimestre")}}
    res["prueba_estilo"] = json.loads((SALIDAS / "prueba_estilo.json").read_text(encoding="utf-8"))
    v1 = SALIDAS / "v1_sin_estilo" / "prueba_estilo.json"
    if v1.exists():
        res["prueba_estilo_v1"] = json.loads(v1.read_text(encoding="utf-8"))

    (SALIDAS / "metricas.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    (AQUI / "INFORME.md").write_text(informe(res), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


def _f(m, pct=True):
    """«91,2 % (IC95 85,0–96,1)» a partir de {"valor", "ic95"}."""
    if not isinstance(m, dict) or m.get("valor") is None or np.isnan(m["valor"]):
        return "—"
    k, u = (100, " %") if pct else (1, "")
    fmt = (lambda x: f"{x * k:.1f}".replace(".", ",")) if pct else (lambda x: f"{x:.3f}".replace(".", ","))
    ic_txt = f" (IC95 {fmt(m['ic95'][0])}–{fmt(m['ic95'][1])})" if m.get("ic95") else ""
    return f"{fmt(m['valor'])}{u}{ic_txt}"


def informe(r):
    """El informe se genera de los números medidos; no se escribe a mano."""
    filas = []
    for nombre, clave in (("Solo Roboflow (normales y anomalías del mismo dataset)", "solo_roboflow"),
                          ("Todas (con las normales de FETAL_PLANES)", "todas_fuera_de_pliegue")):
        m = r[clave]
        filas.append(f"| {nombre} | {_f(m['auc'], pct=False)} | {_f(m['sensibilidad'])} | "
                     f"{_f(m['especificidad'])} | {m['vp']}/{m['vp'] + m['fn']} | {m['fp']}/{m['fp'] + m['vn']} |")
    e, hc = r["externa_falsos_positivos"], r["otro_hospital_hc18"]
    fam = r["familia_entre_anomalias"]
    fam_filas = "\n".join(f"| {NOMBRE_FAMILIA[k]} | {v['aciertos']}/{v['n']} |"
                          for k, v in fam["sensibilidad_por_familia"].items())
    fina = "\n".join(f"| {NOMBRE_ANOMALIA.get(k, k)} | {v['detectadas']}/{v['n']} |"
                     for k, v in sorted(r["deteccion_por_anomalia_fina"].items(), key=lambda kv: -kv[1]["n"]))
    tri = "\n".join(f"| {t} | {v['fp']}/{v['n']} |" for t, v in hc["por_trimestre"].items())
    v1 = r.get("prueba_estilo_v1", {})
    estilo = "\n".join(
        f"| {k.replace('_', ' ')} | {(str(v1[k]['falsas_alarmas']) + '/' + str(v1[k]['n'])) if k in v1 else '—'} | "
        f"{v['falsas_alarmas']}/{v['n']} |" for k, v in r["prueba_estilo"].items())
    n = r["n"]
    pct = lambda x: f"{x * 100:.1f}".replace(".", ",") + " %"  # noqa: E731
    miles = lambda x: f"{x:,}".replace(",", ".")  # noqa: E731
    return f"""# Red de anomalías cerebrales fetales — informe de resultados

Generado por `evaluar.py` a partir de `salidas/`. No editar a mano.

## Resumen en cuatro frases

1. Falsas alarmas sobre cabezas **normales** de hospitales que la red no vio:
   {pct(hc['valor'])} en {hc['n']} cabezas de HC18 (Países Bajos) y
   {pct(e['valor'])} en {miles(e['n'])} cortes de FETAL_PLANES (Barcelona).
2. Detecta {r['solo_roboflow']['vp']} de {r['solo_roboflow']['vp'] + r['solo_roboflow']['fn']} anomalías
   que no vio, **pero esa cifra no es la sensibilidad real**: en el dataset
   público todas las normales vienen de un hospital y todas las anomalías de
   otras fuentes. La prueba de estilo indica que la v2 no se guía por el
   aspecto de la imagen, pero sin normales y anomalías del mismo hospital no se
   puede medir cuánto acertaría en la práctica.
3. Con las anomalías de fuentes clínicas reales (p. ej. un hospital boliviano)
   la sensibilidad es **desconocida**: no existe un dataset público que permita medirla.
4. Uso posible hoy: **cribado de apoyo** que avisa para que el especialista
   mire otra vez. Nunca descarta una anomalía ni la diagnostica.

## Cómo se midió

- **Datos reales**: {n['anomalias']} imágenes originales con anomalía y {n['normales_roboflow']}
  normales (Fetal Brain Abnormalities, Roboflow), más {miles(n['normales_fetal_planes'])} cortes
  cerebrales normales de FETAL_PLANES_DB.
- **80 / 20 rotando (5 pliegues)**: cada imagen se prueba una vez con una red
  que no la vio; las copias aumentadas de una misma imagen van siempre juntas.
- Se excluyeron los {r['excluidas_por_duplicado']['pacientes']} pacientes de FETAL_PLANES cuyas
  imágenes estaban también en Roboflow con otro nombre.
- Umbral de alarma fijo en {str(r['umbral']).replace('.', ',')}, decidido antes de entrenar. IC95 por bootstrap.

## Normal frente a anomalía (validación cruzada)

| Conjunto | AUC | Sensibilidad | Especificidad | Anomalías detectadas | Falsas alarmas |
|---|---|---|---|---|---|
{chr(10).join(filas)}

**Por qué no hay que tomar esto como la sensibilidad real.** Las {n['normales_roboflow']} «normales» de
Roboflow son cortes de FETAL_PLANES_DB (se llaman `Patient00738_Plane3_…`); las
anomalías vienen de compilaciones con otro aspecto. Seis estadísticas del
píxel, sin mirar el cerebro, ya separan las dos clases con AUC 0,84. Una
separación perfecta aquí no demuestra que la red vea las anomalías.

## Falsas alarmas en cabezas normales que la red no vio

| Conjunto | Falsas alarmas |
|---|---|
| HC18 — Radboud UMC, Países Bajos (otro hospital, otros ecógrafos) | **{_f(hc)}** · {hc['fp']}/{hc['n']} |
| FETAL_PLANES — pacientes no usados al entrenar | {_f(e)} · {e['fp']}/{miles(e['n'])} |

HC18 por trimestre (la red se entrenó sobre todo con segundo y tercero):

| Trimestre | Falsas alarmas |
|---|---|
{tri}

## Prueba de estilo: ¿mira el cerebro o el aspecto de la imagen?

A 300 cabezas **normales** de HC18 se les cambia el aspecto sin tocar la
anatomía. Una red que mira el cerebro no debería alarmarse. La v1 se entrenó
sin aumento de estilo; la v2 (la que se usa) con él. «Foto de pantalla» (JPEG
fuerte, gamma, speckle) no se usó en ningún entrenamiento.

| Aspecto | v1: falsas alarmas | v2: falsas alarmas |
|---|---|---|
{estilo}

## Qué familia de anomalía (entre las anomalías)

Aquí las dos partes vienen de la misma fuente, así que la cifra es más fiable:
exactitud {_f({'valor': fam['exactitud'], 'ic95': fam['ic95']})} con 4 familias.

| Familia | Acertadas |
|---|---|
{fam_filas}

## Detección por anomalía concreta (con la misma reserva que la sensibilidad)

| Anomalía | Detectadas |
|---|---|
{fina}

## Límites

- 212 imágenes originales, una sola compilación pública de anomalías, sin
  datos de pacientes ni de ecógrafo. Varias anomalías tienen 1–5 imágenes.
- Ninguna ecografía boliviana. Antes de uso clínico: validación local
  prospectiva con anomalías confirmadas.
- Solo cortes axiales de cabeza; el microservicio rechaza otros planos.
"""


if __name__ == "__main__":
    main()
