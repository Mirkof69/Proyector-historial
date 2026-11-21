"""Manifiesto de la red de anomalías cerebrales fetales.

Solo imágenes reales con etiqueta verificable:

  · Fetal Brain Abnormalities (Roboflow, CC BY 4.0): 1.768 archivos de 212
    imágenes originales. Cada original tiene 3-8 copias aumentadas; el GRUPO
    de cada archivo es su imagen original, y la partición se hace por grupo.
    (Las particiones de Roboflow ponían copias de la misma imagen en train y
    en test en el 45 % de los casos: exactitud inflada.)
  · FETAL_PLANES_DB (Zenodo 3904280, CC BY 4.0): cortes cerebrales de
    rutina, NORMALES, de 2 hospitales y varios ecógrafos. Grupo = paciente.
    Se usan (a) como normales de entrenamiento, para que la red no aprenda
    «esta imagen viene de Roboflow» y (b) como prueba externa de falsos
    positivos, con pacientes que no vio.

Partición: validación cruzada de 5 pliegues agrupada y estratificada. Cada
pliegue es un 80 % entrenamiento / 20 % prueba; al rotar, TODAS las imágenes se
usan para entrenar y TODAS se prueban exactamente una vez, con un modelo que no
las vio. Con 21 anomalías originales en un único 20 % los intervalos serían
enormes; con 5 pliegues se mide sobre las 110.

Los pacientes de FETAL_PLANES que no entran en el reparto (unos 680) forman la
prueba EXTERNA (pliegue -1): nunca se entrena con ellos.

Salida: salidas/manifiesto.csv
"""
import csv
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
ROBOFLOW = IA / "datos" / "extraidos" / "fetal_brain_abnormalities"
REDES = IA / "entrenamiento" / "redes_ecografia_real"
SALIDAS = AQUI / "salidas"
SEMILLA = 2026

#: Anomalía original -> familia clínica. Con 1-21 imágenes por anomalía no se
#: puede medir cada una por separado; las familias agrupan por conducta.
FAMILIA = {
    "normal": "normal",
    "mild-ventriculomegaly": "ventriculomegalia_hidrocefalia",
    "moderate-ventriculomegaly": "ventriculomegalia_hidrocefalia",
    "severe-ventriculomegaly": "ventriculomegalia_hidrocefalia",
    "hydracenphaly": "ventriculomegalia_hidrocefalia",
    "colphocephaly": "ventriculomegalia_hidrocefalia",
    "cerebellah-hypoplasia": "fosa_posterior",
    "anold-chiari-malformation": "fosa_posterior",
    "m-magna": "fosa_posterior",
    "encephalocele": "encefalocele",
    "arachnoid-cyst": "lesion_quistica_vascular",
    "polencephaly": "lesion_quistica_vascular",
    "intracranial-hemorrdge": "lesion_quistica_vascular",
    "intracranial-tumor": "lesion_quistica_vascular",
    "vein-of-galen": "lesion_quistica_vascular",
    "holoprosencephaly": "lesion_quistica_vascular",
}


def origen_roboflow(nombre: str) -> str:
    base = re.sub(r"_aug_\d+.*$", "", nombre)
    return re.sub(r"_png_jpg.*$|\.rf\..*$", "", base)


def filas_roboflow():
    filas = []
    for particion in ("train", "valid", "test"):
        tabla = list(csv.reader(open(ROBOFLOW / particion / "_classes.csv", encoding="utf-8")))
        clases = [c.strip() for c in tabla[0][1:]]
        for fila in tabla[1:]:
            etiquetas = [clases[i] for i, v in enumerate(fila[1:]) if v.strip() == "1"]
            if len(etiquetas) != 1:
                continue
            fina = etiquetas[0]
            filas.append({"ruta": str(ROBOFLOW / particion / fila[0]), "fuente": "roboflow",
                          "grupo": "RF-" + origen_roboflow(fila[0]), "etiqueta_fina": fina,
                          "familia": FAMILIA[fina], "anomalia": int(fina != "normal")})
    return filas


def filas_fetal_planes(maximo_pacientes: int, excluir: set[str]):
    """Cortes cerebrales normales: (reparto, externos) por paciente.

    `excluir`: pacientes cuyas imágenes ya están entre las normales de
    Roboflow (con otro nombre); si entraran aquí, la misma imagen podría
    estar en entrenamiento y en prueba.
    """
    cat = pd.read_excel(REDES / "catalogo_imagenes.xlsx", sheet_name="Planos")
    cerebros = cat[(cat["plano"] == "cerebro fetal") & ~cat["paciente"].isin(excluir)]
    pacientes = sorted(cerebros["paciente"].unique())
    random.Random(SEMILLA).shuffle(pacientes)
    elegidos = set(pacientes[:maximo_pacientes])
    reparto, externos = [], []
    for _, f in cerebros.iterrows():
        fila = {"ruta": str(REDES / f["ruta"]), "fuente": "fetal_planes", "grupo": f["paciente"],
                "etiqueta_fina": "normal", "familia": "normal", "anomalia": 0, "ecografo": f["ecografo"]}
        (reparto if f["paciente"] in elegidos else externos).append(fila)
    return reparto, externos


def particionar(filas, pliegues: int = 5):
    """Asigna a cada grupo un pliegue 0..4, estratificado por (fuente, familia)."""
    rng = random.Random(SEMILLA)
    grupos_por_estrato = defaultdict(set)
    for f in filas:
        grupos_por_estrato[(f["fuente"], f["familia"])].add(f["grupo"])
    pliegue = {}
    for _, grupos in sorted(grupos_por_estrato.items()):
        grupos = sorted(grupos)
        rng.shuffle(grupos)
        desfase = rng.randrange(pliegues)
        for i, g in enumerate(grupos):
            pliegue[g] = (i + desfase) % pliegues
    for f in filas:
        f["pliegue"] = pliegue[f["grupo"]]
    return filas


def main():
    SALIDAS.mkdir(exist_ok=True)
    roboflow = filas_roboflow()
    # FETAL_PLANES: 400 pacientes (~1.370 cortes) para no ahogar a las
    # anomalías; los demás quedan para la prueba externa de falsos positivos.
    # Las «normales» de Roboflow son cortes de FETAL_PLANES (Patient00738_Plane3_…)
    ya_en_roboflow = {"FP-P" + m.group(1) for f in roboflow if (m := re.search(r"Patient(\d+)", f["grupo"]))}
    print(f"Pacientes de FETAL_PLANES ya presentes en Roboflow (se excluyen): {len(ya_en_roboflow)}")
    planes, externos = filas_fetal_planes(maximo_pacientes=400, excluir=ya_en_roboflow)
    filas = particionar(roboflow + planes)
    for f in externos:
        f["pliegue"] = -1
    filas += externos
    df = pd.DataFrame(filas)
    faltan = [r for r in df["ruta"] if not Path(r).exists()]
    # Rutas relativas al microservicio: el manifiesto se versiona y vale en cualquier equipo.
    df["ruta"] = [Path(r).relative_to(IA).as_posix() for r in df["ruta"]]
    df.to_csv(SALIDAS / "manifiesto.csv", index=False, encoding="utf-8")

    resumen = df.groupby(["pliegue", "familia"]).agg(archivos=("ruta", "size"), grupos=("grupo", "nunique"))
    print(resumen.to_string())
    fuga = df.groupby("grupo")["pliegue"].nunique().max()
    print(f"\nGrupos repartidos en más de una partición: {'ninguno' if fuga == 1 else 'HAY FUGA'}")
    print(f"Archivos que no existen: {len(faltan)}")


if __name__ == "__main__":
    main()
