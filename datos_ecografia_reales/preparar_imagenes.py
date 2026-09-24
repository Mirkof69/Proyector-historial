"""Arma el dataset real de ecografía: imágenes + una fila de información por imagen.

    python preparar_imagenes.py

Lee los zips de `../nuveos data seeds/` y escribe:

    imagenes/hc18/            999 ecografías de cabeza fetal
    imagenes/planos_fetales/  12.400 ecografías de planos anatómicos
    catalogo_imagenes.xlsx    una fila por imagen, con toda su información

POR QUÉ ESTOS DOS DATASETS
--------------------------
Son los únicos de la carpeta de descargas que cumplen las tres condiciones:
imágenes reales, información medida por profesionales para CADA imagen, y una
publicación que se puede citar.

  HC18 (Radboud University Medical Center, Países Bajos)
    van den Heuvel TLA, de Bruijn D, de Korte CL, van Ginneken B.
    «Automated measurement of fetal head circumference using 2D ultrasound
    images». PLoS ONE 2018;13(8):e0200412. Datos: Zenodo 1327317, CC BY 4.0.
    Cada imagen trae la circunferencia cefálica medida por un ecografista.

  FETAL_PLANES_DB (BCNatal, Hospital Clínic y Sant Joan de Déu, Barcelona)
    Burgos-Artizzu XP, Coronado-Gutiérrez D, Valenzuela-Alcaraz B, et al.
    «Evaluation of deep convolutional neural networks for automatic
    classification of common maternal fetal ultrasound planes».
    Scientific Reports 2020;10:10200. Datos: Zenodo 3904280, CC BY 4.0.
    Cada imagen trae el plano anatómico, la paciente, el operador y el
    ecógrafo, más una separación oficial entre entrenamiento y prueba.

Los que se descartaron y por qué quedan en la hoja «Fuentes» del Excel.

PARTICIONES SIN FUGAS
---------------------
Una misma madre nunca queda a la vez en entrenamiento y en prueba. Si quedara,
la red «reconocería» a la paciente y el resultado saldría inflado.

  - Planos: se respeta la separación oficial del dataset, que ya es por
    paciente, y se aparta un 10% de las pacientes de entrenamiento para
    validar.
  - HC18: el dataset no trae número de paciente, pero lo codifica en el
    nombre: `15_HC`, `16_2HC`, `17_3HC` son la 1.ª, 2.ª y 3.ª imagen de la
    misma madre (sus medidas son casi iguales: 65,7 / 63,3 / 62,9 mm). Cada
    imagen se agrupa con el último `_HC` anterior. Esa agrupación puede juntar
    de más, pero nunca deja a una paciente en los dos lados.
"""
from __future__ import annotations

import io
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

AQUI = Path(__file__).resolve().parent
DESCARGAS = AQUI.parent / "nuveos data seeds"
ZIP_HC18 = DESCARGAS / "cráneos fetales, 999 imágenes.zip"
ZIP_PLANOS = DESCARGAS / "FETAL_PLANES_ZENODO.zip"

DIR_HC18 = AQUI / "imagenes" / "hc18"
DIR_PLANOS = AQUI / "imagenes" / "planos_fetales"
CATALOGO = AQUI / "catalogo_imagenes.xlsx"

SEMILLA = 2026

PLANOS_ES = {
    "Fetal abdomen": "abdomen fetal",
    "Fetal brain": "cerebro fetal",
    "Fetal femur": "fémur fetal",
    "Fetal thorax": "tórax fetal",
    "Maternal cervix": "cuello uterino materno",
    "Other": "otro",
}


def edad_gestacional_por_hc(hc_mm: float) -> float:
    """Semanas de gestación estimadas a partir de la circunferencia cefálica.

    Hadlock FP, Deter RL, Harrist RB, Park SK. «Estimating fetal age:
    computer-assisted analysis of multiple fetal growth parameters».
    Radiology 1984;152:497-501.

        EG (semanas) = 8,96 + 0,540·CC + 0,0003·CC³      con CC en centímetros

    Comprobado: CC 17,5 cm -> 20,0 semanas; CC 33 cm -> 37,6 semanas.
    """
    cc = hc_mm / 10.0
    return round(8.96 + 0.540 * cc + 0.0003 * cc**3, 1)


# ─────────────────────────────── HC18 ──────────────────────────────────────

def preparar_hc18() -> pd.DataFrame:
    with zipfile.ZipFile(ZIP_HC18) as zf:
        tabla = pd.read_csv(io.BytesIO(zf.read("training_set_pixel_size_and_HC.csv")))
        interno = next(n for n in zf.namelist() if "training" in n.lower() and n.endswith(".zip"))
        imagenes = zipfile.ZipFile(io.BytesIO(zf.read(interno)))

    DIR_HC18.mkdir(parents=True, exist_ok=True)
    por_nombre = {Path(n).name: n for n in imagenes.namelist()
                  if n.lower().endswith(".png") and "annotation" not in n.lower()}
    for nombre in tabla["filename"]:
        destino = DIR_HC18 / nombre
        if not destino.exists():
            destino.write_bytes(imagenes.read(por_nombre[nombre]))

    d = pd.DataFrame({
        "archivo": tabla["filename"],
        "ruta": "imagenes/hc18/" + tabla["filename"],
        "tamano_pixel_mm": tabla["pixel size"].round(6),
        "circunferencia_cefalica_mm": tabla["head circumference (mm)"],
    })
    d["numero"] = d["archivo"].str.extract(r"^(\d+)_")[0].astype(int)
    d["imagen_de_la_paciente"] = d["archivo"].str.extract(r"^\d+_(\d*)HC")[0].replace("", "1").astype(int)
    d = d.sort_values("numero").reset_index(drop=True)

    # Agrupación por paciente: cada imagen va con el último "_HC" anterior.
    grupo, actual = [], None
    for num, orden in zip(d["numero"], d["imagen_de_la_paciente"]):
        if orden == 1 or actual is None:
            actual = num
        grupo.append(f"HC18-P{actual:04d}")
    d["paciente"] = grupo

    d["edad_gestacional_hadlock_sem"] = d["circunferencia_cefalica_mm"].map(edad_gestacional_por_hc)
    d["trimestre"] = pd.cut(d["edad_gestacional_hadlock_sem"], [0, 13.9, 27.9, 50],
                            labels=["primero", "segundo", "tercero"]).astype(str)

    # 70 / 15 / 15 por paciente.
    rng = np.random.default_rng(SEMILLA)
    pacientes = d["paciente"].unique()
    rng.shuffle(pacientes)
    n = len(pacientes)
    asignacion = {p: "entrenamiento" for p in pacientes[: int(n * 0.70)]}
    asignacion |= {p: "validacion" for p in pacientes[int(n * 0.70): int(n * 0.85)]}
    asignacion |= {p: "prueba" for p in pacientes[int(n * 0.85):]}
    d["particion"] = d["paciente"].map(asignacion)

    return d[["archivo", "ruta", "paciente", "imagen_de_la_paciente", "tamano_pixel_mm",
              "circunferencia_cefalica_mm", "edad_gestacional_hadlock_sem", "trimestre",
              "particion"]]


# ─────────────────────────── FETAL_PLANES_DB ───────────────────────────────

def preparar_planos() -> pd.DataFrame:
    DIR_PLANOS.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_PLANOS) as zf:
        tabla = pd.read_csv(io.BytesIO(zf.read("FETAL_PLANES_DB_data.csv")), sep=";")
        tabla.columns = [c.strip() for c in tabla.columns]
        for n in zf.namelist():
            if n.lower().endswith(".png"):
                destino = DIR_PLANOS / Path(n).name
                if not destino.exists():
                    with zf.open(n) as origen, open(destino, "wb") as salida:
                        shutil.copyfileobj(origen, salida)

    d = pd.DataFrame({
        "archivo": tabla["Image_name"].str.strip() + ".png",
        "paciente": "FP-P" + tabla["Patient_num"].astype(int).astype(str).str.zfill(5),
        "plano_original": tabla["Plane"].str.strip(),
        "subplano_cerebral": tabla["Brain_plane"].str.strip(),
        "operador": tabla["Operator"].astype(str).str.strip(),
        "ecografo": tabla["US_Machine"].astype(str).str.strip(),
        "particion_oficial": tabla["Train"].astype(int).map({1: "entrenamiento", 0: "prueba"}),
    })
    d["ruta"] = "imagenes/planos_fetales/" + d["archivo"]
    d["plano"] = d["plano_original"].map(PLANOS_ES)

    # Validación: un 10% de las PACIENTES de entrenamiento, no de las imágenes.
    rng = np.random.default_rng(SEMILLA)
    pacientes_ent = d.loc[d["particion_oficial"] == "entrenamiento", "paciente"].unique()
    rng.shuffle(pacientes_ent)
    validacion = set(pacientes_ent[: int(len(pacientes_ent) * 0.10)])
    d["particion"] = np.where(d["particion_oficial"] == "prueba", "prueba",
                              np.where(d["paciente"].isin(validacion), "validacion", "entrenamiento"))

    faltan = [r for r in d["ruta"] if not (AQUI / r).exists()]
    if faltan:
        raise SystemExit(f"Faltan {len(faltan)} imágenes, por ejemplo {faltan[:3]}")

    return d[["archivo", "ruta", "paciente", "plano", "plano_original", "subplano_cerebral",
              "operador", "ecografo", "particion_oficial", "particion"]]


# ─────────────────────────────── Excel ─────────────────────────────────────

DICCIONARIO = [
    ("HC18", "archivo", "Nombre del archivo de la imagen"),
    ("HC18", "ruta", "Dónde está la imagen, relativa a esta carpeta"),
    ("HC18", "paciente", "Madre a la que pertenece la imagen (agrupación explicada en Fuentes)"),
    ("HC18", "imagen_de_la_paciente", "1.ª, 2.ª, 3.ª... imagen de esa misma madre"),
    ("HC18", "tamano_pixel_mm", "Cuántos milímetros mide un píxel. Hace falta para pasar de píxeles a mm"),
    ("HC18", "circunferencia_cefalica_mm", "Contorno de la cabeza, medido por un ecografista. LO QUE LA RED APRENDE A PREDECIR"),
    ("HC18", "edad_gestacional_hadlock_sem", "Semanas de embarazo estimadas con la fórmula de Hadlock 1984 a partir de la circunferencia"),
    ("HC18", "trimestre", "Trimestre según esa edad gestacional"),
    ("HC18", "particion", "entrenamiento / validacion / prueba, por paciente"),
    ("Planos", "archivo", "Nombre del archivo de la imagen"),
    ("Planos", "ruta", "Dónde está la imagen, relativa a esta carpeta"),
    ("Planos", "paciente", "Madre a la que pertenece la imagen"),
    ("Planos", "plano", "Qué parte del cuerpo muestra la ecografía. LO QUE LA RED APRENDE A RECONOCER"),
    ("Planos", "plano_original", "El mismo plano, con el nombre en inglés del dataset"),
    ("Planos", "subplano_cerebral", "Si es de cerebro: transtalámico, transventricular o transcerebelar"),
    ("Planos", "operador", "Profesional que hizo la ecografía (anonimizado)"),
    ("Planos", "ecografo", "Modelo del equipo de ecografía"),
    ("Planos", "particion_oficial", "Separación publicada con el dataset, por paciente"),
    ("Planos", "particion", "entrenamiento / validacion / prueba usada aquí"),
]

FUENTES = [
    ("HC18", "USADO", "999 imágenes de cabeza fetal con la circunferencia medida por ecografista",
     "van den Heuvel TLA et al. PLoS ONE 2018;13(8):e0200412 · Zenodo 1327317 · CC BY 4.0"),
    ("FETAL_PLANES_DB", "USADO", "12.400 imágenes de 6 planos anatómicos de 1.792 pacientes",
     "Burgos-Artizzu XP et al. Sci Rep 2020;10:10200 · Zenodo 3904280 · CC BY 4.0"),
    ("Large-Scale Fetal Head Biometry", "NO USADO", "Solo máscaras de segmentación; la medida habría que calcularla nosotros", "CC BY 4.0"),
    ("Fetal Brain Abnormalities (Roboflow)", "NO USADO", "Trae varias copias aumentadas de la misma imagen: se colarían entre entrenamiento y prueba", "Roboflow"),
    ("Fetal Abdominal Structures", "NO USADO", "Solo máscaras de segmentación, sin información numérica", "—"),
    ("fetal-ultrasound-brain", "NO USADO", "Es un subconjunto de FETAL_PLANES_DB (solo planos cerebrales)", "Kaggle"),
    ("IUGC MICCAI 2024", "NO USADO", "Ecografía durante el parto: otro problema clínico", "MICCAI 2024"),
    ("Fetal Health Classification", "NO USADO", "Solo tabla de cardiotocografía, sin imágenes", "UCI / Kaggle"),
    ("Agrupación por paciente en HC18", "NOTA", "15_HC, 16_2HC, 17_3HC = 1.ª, 2.ª y 3.ª imagen de la misma madre; cada imagen se agrupa con el último _HC anterior", "—"),
]


def formato(hoja, anchos=None):
    for c in hoja[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="2E5B86")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    hoja.row_dimensions[1].height = 32
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions
    for i, col in enumerate(hoja.iter_cols(min_row=1, max_row=1), start=1):
        nombre = str(col[0].value)
        hoja.column_dimensions[get_column_letter(i)].width = (anchos or {}).get(
            nombre, max(12, min(34, len(nombre) + 3)))


def main():
    print("Preparando HC18...")
    hc = preparar_hc18()
    print(f"  {len(hc)} imágenes, {hc['paciente'].nunique()} pacientes")
    print("Preparando FETAL_PLANES_DB (2 GB, tarda unos minutos)...")
    planos = preparar_planos()
    print(f"  {len(planos)} imágenes, {planos['paciente'].nunique()} pacientes")

    with pd.ExcelWriter(CATALOGO, engine="openpyxl") as w:
        hc.to_excel(w, sheet_name="HC18", index=False)
        planos.to_excel(w, sheet_name="Planos", index=False)
        pd.DataFrame(DICCIONARIO, columns=["hoja", "columna", "significado"]).to_excel(
            w, sheet_name="Diccionario", index=False)
        pd.DataFrame(FUENTES, columns=["dataset", "estado", "motivo", "cita_y_licencia"]).to_excel(
            w, sheet_name="Fuentes", index=False)
        formato(w.sheets["HC18"], {"archivo": 16, "ruta": 30})
        formato(w.sheets["Planos"], {"archivo": 36, "ruta": 58})
        formato(w.sheets["Diccionario"], {"hoja": 10, "columna": 30, "significado": 90})
        formato(w.sheets["Fuentes"], {"dataset": 34, "estado": 12, "motivo": 80, "cita_y_licencia": 70})

    print(f"\nEscrito {CATALOGO}")
    print("HC18 por partición:", hc["particion"].value_counts().to_dict())
    print("Planos por partición:", planos["particion"].value_counts().to_dict())
    print("Planos por clase:", planos["plano"].value_counts().to_dict())


if __name__ == "__main__":
    main()
