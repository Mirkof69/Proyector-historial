"""Extrae los tres datasets de segmentación y arma sus catálogos.

    python entrenamiento/segmentacion/preparar.py [cabeza] [abdomen] [torax]

| Tarea   | Dataset (crudos/)                                   | Clases                                   |
|---------|-----------------------------------------------------|------------------------------------------|
| cabeza  | Large-Scale Annotation Dataset for Fetal Head Biometry (Alzubaidi et al., Sci Data 2023, Zenodo 8265464) | cráneo (Brain), cavum del septum pellucidum (CSP), ventrículo lateral (LV) |
| abdomen | Fetal Abdominal Structures Segmentation (Mendeley Data, CC BY 4.0) | hígado, estómago, vena umbilical, aorta |
| torax   | FOCUS (Zenodo 14597550, CC BY 4.0)                   | tórax, corazón                           |

Salida: imágenes en gris y máscaras de índices (0 = fondo) en
`datos/extraidos/segmentacion/<tarea>/`, y `catalogos/<tarea>.csv` con la
partición. La partición es POR PACIENTE (70/15/15, semilla fija): una misma
madre nunca está en entrenamiento y prueba a la vez.

Cabeza: el grupo «Diverse Fetal Head Images» son las 999 imágenes de HC18
(otro hospital, Radboud) reescaladas. NO se usan para entrenar: quedan como
prueba externa, porque HC18 trae la circunferencia medida por el ecografista.
FOCUS no trae paciente: se respeta su partición oficial.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
CRUDOS = RAIZ / "datos" / "crudos"
SALIDA = RAIZ / "datos" / "extraidos" / "segmentacion"
CATALOGOS = AQUI / "catalogos"
SEMILLA = 2026

CLASES = {
    "cabeza": ["fondo", "craneo", "csp", "ventriculo_lateral"],
    "abdomen": ["fondo", "higado", "estomago", "vena_umbilical", "aorta"],
    "torax": ["fondo", "torax", "corazon"],
}


def _particion_por_paciente(pacientes: pd.Series, prop=(0.70, 0.15)) -> pd.Series:
    unicos = np.array(sorted(pacientes.unique()))
    rng = np.random.default_rng(SEMILLA)
    rng.shuffle(unicos)
    n_e = int(round(len(unicos) * prop[0]))
    n_v = int(round(len(unicos) * prop[1]))
    destino = {p: "entrenamiento" for p in unicos[:n_e]}
    destino |= {p: "validacion" for p in unicos[n_e:n_e + n_v]}
    destino |= {p: "prueba" for p in unicos[n_e + n_v:]}
    return pacientes.map(destino)


def _guardar(carpeta: Path, nombre: str, gris: np.ndarray, mascara: np.ndarray) -> tuple[str, str]:
    (carpeta / "imagenes").mkdir(parents=True, exist_ok=True)
    (carpeta / "mascaras").mkdir(parents=True, exist_ok=True)
    ri, rm = carpeta / "imagenes" / f"{nombre}.png", carpeta / "mascaras" / f"{nombre}.png"
    Image.fromarray(gris).save(ri)
    Image.fromarray(mascara.astype(np.uint8)).save(rm)
    return str(ri.relative_to(RAIZ)).replace("\\", "/"), str(rm.relative_to(RAIZ)).replace("\\", "/")


def _colores(labelmap: str, nombres: dict[str, int]) -> dict[tuple, int]:
    """«Brain:255,0,0::» → {(255,0,0): 1}. Cada grupo del dataset usa sus colores."""
    colores = {}
    for linea in labelmap.splitlines():
        if linea.startswith("#") or ":" not in linea:
            continue
        etiqueta, rgb = linea.split(":")[:2]
        if etiqueta in nombres:
            colores[tuple(int(v) for v in rgb.split(","))] = nombres[etiqueta]
    return colores


def preparar_cabeza() -> pd.DataFrame:
    z = zipfile.ZipFile(CRUDOS / "Large-Scale Annotation Dataset for Fetal Head Biometry in Ultrasound Images.zip")
    nombres = {"Brain": 1, "CSP": 2, "LV": 3}
    filas = []
    for grupo in ("Trans-thalamic", "Trans-cerebellum", "Trans-ventricular", "Diverse Fetal Head Images"):
        interno = zipfile.ZipFile(io.BytesIO(z.read(f"{grupo}.zip")))
        lista = interno.namelist()
        seg_zip = next(x for x in lista if x.lower().endswith(("segmentation.zip", "segmentation-mask.zip")))
        seg = zipfile.ZipFile(io.BytesIO(interno.read(seg_zip)))
        colores = _colores(seg.read("labelmap.txt").decode("utf-8"), nombres)
        tamanos = {}
        csv = next((x for x in lista if x.endswith("Pixel-Size.csv")), None)
        if csv:
            t = pd.read_csv(io.BytesIO(interno.read(csv)), encoding="utf-8-sig")
            tamanos = dict(zip(t.iloc[:, 0], t.iloc[:, 1]))
        imagenes = {Path(x).name: x for x in lista if x.lower().endswith(".png")}
        for m in seg.namelist():
            if not (m.startswith("SegmentationClass/") and m.endswith(".png")):
                continue
            nombre = Path(m).name
            if nombre not in imagenes:
                continue
            rgb = np.array(Image.open(io.BytesIO(seg.read(m))).convert("RGB"))
            mascara = np.zeros(rgb.shape[:2], np.uint8)
            for color, idx in colores.items():
                mascara[np.all(rgb == color, axis=-1)] = idx
            gris = np.array(Image.open(io.BytesIO(interno.read(imagenes[nombre]))).convert("L"))
            if gris.shape != mascara.shape:
                continue
            externo = grupo.startswith("Diverse")
            paciente = nombre.split("_")[0] if not externo else f"HC18_{nombre.split('_')[0]}"
            ri, rm = _guardar(SALIDA / "cabeza", f"{grupo.split()[0]}_{Path(nombre).stem}", gris, mascara)
            filas.append({"imagen": ri, "mascara": rm, "paciente": paciente, "grupo": grupo,
                          "archivo_original": nombre, "tamano_pixel_mm": tamanos.get(nombre),
                          "externo": externo})
    cat = pd.DataFrame(filas)
    internos = ~cat["externo"]
    cat.loc[internos, "particion"] = _particion_por_paciente(cat.loc[internos, "paciente"])
    cat.loc[~internos, "particion"] = "externa_hc18"
    return cat


def preparar_abdomen() -> pd.DataFrame:
    z = zipfile.ZipFile(CRUDOS / "Fetal Abdominal Structures Segmentation Dataset.zip")
    orden = [("liver", 1), ("stomach", 2), ("vein", 3), ("artery", 4)]  # lo pequeño se pinta encima
    filas = []
    for x in z.namelist():
        if not x.endswith(".npy"):
            continue
        d = np.load(io.BytesIO(z.read(x)), allow_pickle=True).item()
        gris = np.array(Image.fromarray(d["image"]).convert("L"))
        mascara = np.zeros(gris.shape, np.uint8)
        for clave, idx in orden:
            mascara[d["structures"][clave] > 0] = idx
        stem = Path(x).stem  # P0100_IMG1 / P028_IMG1
        paciente = f"P{int(re.match(r'P(\d+)_', stem).group(1)):04d}"
        ri, rm = _guardar(SALIDA / "abdomen", stem, gris, mascara)
        filas.append({"imagen": ri, "mascara": rm, "paciente": paciente, "archivo_original": stem})
    cat = pd.DataFrame(filas)
    cat["particion"] = _particion_por_paciente(cat["paciente"])
    return cat


def preparar_torax() -> pd.DataFrame:
    z = zipfile.ZipFile(CRUDOS / "FOCUS-dataset.zip")
    oficial = {"training": "entrenamiento", "validation": "validacion", "testing": "prueba"}
    filas = []
    for x in z.namelist():
        m = re.match(r"(training|validation|testing)/images/(\d+)\.png$", x)
        if not m:
            continue
        parte, num = m.groups()
        gris = np.array(Image.open(io.BytesIO(z.read(x))).convert("L"))
        mascara = np.zeros(gris.shape, np.uint8)
        for estructura, idx in (("thorax", 1), ("cardiac", 2)):
            ruta = f"{parte}/annfiles_mask/{num}-{estructura}.png"
            capa = np.array(Image.open(io.BytesIO(z.read(ruta))).convert("L"))
            if capa.shape != gris.shape:
                capa = np.array(Image.fromarray(capa).resize(gris.shape[::-1], Image.NEAREST))
            mascara[capa > 127] = idx
        ri, rm = _guardar(SALIDA / "torax", f"{parte}_{num}", gris, mascara)
        filas.append({"imagen": ri, "mascara": rm, "paciente": f"{parte}_{num}",
                      "archivo_original": x, "particion": oficial[parte]})
    return pd.DataFrame(filas)


def main(tareas: list[str]) -> None:
    CATALOGOS.mkdir(exist_ok=True)
    funciones = {"cabeza": preparar_cabeza, "abdomen": preparar_abdomen, "torax": preparar_torax}
    for tarea in tareas or list(funciones):
        funcion = funciones[tarea]
        cat = funcion()
        cat.to_csv(CATALOGOS / f"{tarea}.csv", index=False, encoding="utf-8")
        resumen = cat.groupby("particion").agg(imagenes=("imagen", "size"), pacientes=("paciente", "nunique"))
        print(f"\n{tarea}: {len(cat)} imágenes\n{resumen.to_string()}")


if __name__ == "__main__":
    import sys

    main(sys.argv[1:])
