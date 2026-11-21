"""Extrae IUGC 2024 (ecografía intraparto transperineal) y arma su catálogo.

    python entrenamiento/intraparto/preparar.py

IUGC MICCAI 2024: vídeos de ecografía transperineal en el trabajo de parto
con, en los cuadros anotados, la máscara de la SÍNFISIS DEL PUBIS y de la
CABEZA FETAL, y el ÁNGULO DE PROGRESIÓN (AoP) medido por el experto.

- La imagen es el cuadro anotado del vídeo (se lee con OpenCV).
- Máscara: viene en varias codificaciones (7/8, 127/255, colores RGB, 16 bits).
  En CADA máscara, de los dos valores distintos de cero, el de menor área es la
  sínfisis del pubis y el de mayor área la cabeza fetal (la cabeza ocupa ~8
  veces más). Se guarda como 1 = sínfisis del pubis, 2 = cabeza fetal; las
  máscaras sin exactamente dos estructuras se descartan.
- Partición: la OFICIAL del desafío para la prueba (test, adquirido en
  2020-2021) y, dentro de train, 15 % de los EXÁMENES para validación
  (los clips del mismo examen comparten el prefijo antes de «I»); el val
  oficial (40) se suma a validación.
"""
from __future__ import annotations

import io
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ZIP = RAIZ / "datos" / "crudos" / "IUGC MICCAI 2024.zip"
SALIDA = RAIZ / "datos" / "extraidos" / "intraparto"
CATALOGO = AQUI / "catalogo.csv"
SEMILLA = 2026


def _examen(video: str) -> str:
    return re.split(r"I\d+$", video)[0]


def _cuadro(z: zipfile.ZipFile, ruta_video: str, indice: int, cache: dict) -> np.ndarray | None:
    if ruta_video not in cache:
        cache.clear()
        t = tempfile.NamedTemporaryFile(suffix=".avi", delete=False)
        t.write(z.read(ruta_video))
        t.close()
        cache[ruta_video] = t.name
    cap = cv2.VideoCapture(cache[ruta_video])
    cap.set(cv2.CAP_PROP_POS_FRAMES, indice)
    ok, cuadro = cap.read()
    cap.release()
    return cv2.cvtColor(cuadro, cv2.COLOR_BGR2GRAY) if ok else None


def main() -> None:
    z = zipfile.ZipFile(ZIP)
    nombres = z.namelist()
    videos = {Path(x).stem: x for x in nombres if x.endswith(".avi")}
    # En train los vídeos se llaman «<nombre>__<nombre>.avi».
    videos |= {Path(x).stem.split("__")[-1]: x for x in nombres if x.endswith(".avi") and "__" in Path(x).stem}
    (SALIDA / "imagenes").mkdir(parents=True, exist_ok=True)
    (SALIDA / "mascaras").mkdir(parents=True, exist_ok=True)
    filas, cache, valores_area = [], {}, {"pubis": [], "cabeza": []}
    for parte in ("train", "val", "test"):
        ruta_lm = next(x for x in nombres if f"/{parte}/seg/landmark" in x and x.endswith(".json"))
        marcas = json.loads(z.read(ruta_lm))
        mascaras = {Path(x).name: x for x in nombres if f"/{parte}/seg/" in x and x.endswith(".png")}
        info = pd.read_csv(io.BytesIO(z.read(next(x for x in nombres if f"/{parte}/seg/seg_info.csv" in x))))
        columna = "labeled_frame_index" if "labeled_frame_index" in info else None
        cuadros_info = ({Path(str(f)).stem: int(i) for f, i in zip(info["filename"], info[columna])
                         if str(i).isdigit()} if columna else {})
        for nombre_mascara, m in marcas.items():
            if nombre_mascara not in mascaras:
                continue
            base = nombre_mascara[:-4]
            # val: el nombre ES el vídeo y el cuadro está en seg_info.csv;
            # train: <vídeo>_<cuadro>_6 ; test: <vídeo>_<cuadro>
            if base in videos:
                video, cuadro = base, cuadros_info.get(base)
            elif base.endswith("_6") and base.rsplit("_", 2)[0] in videos:
                video, cuadro = base.rsplit("_", 2)[0], int(base.rsplit("_", 2)[1])
            elif base.rsplit("_", 1)[0] in videos:
                video, cuadro = base.rsplit("_", 1)[0], int(base.rsplit("_", 1)[1])
            else:
                continue
            if cuadro is None:
                continue
            gris = _cuadro(z, videos[video], cuadro, cache)
            if gris is None:
                continue
            im = Image.open(io.BytesIO(z.read(mascaras[nombre_mascara])))
            original = np.array(im.convert("L") if im.mode in ("RGB", "RGBA", "P") else im)
            if original.shape != gris.shape:
                continue
            valores = [v for v in np.unique(original) if v != 0]
            if len(valores) != 2:
                continue
            areas = {v: int((original == v).sum()) for v in valores}
            pubis, cabeza = sorted(valores, key=areas.get)
            nueva = np.zeros(original.shape, np.uint8)
            nueva[original == pubis] = 1
            nueva[original == cabeza] = 2
            valores_area["pubis"].append(areas[pubis])
            valores_area["cabeza"].append(areas[cabeza])
            filas.append({"nombre": base, "parte": parte, "video": video, "examen": _examen(video), "cuadro": cuadro,
                          "aop": float(m["aop"]), "hsd": float(m["hsd"]),
                          "ps1_y": float(m["ps_points"][0][0]), "ps1_x": float(m["ps_points"][0][1]),
                          "ps2_y": float(m["ps_points"][1][0]), "ps2_x": float(m["ps_points"][1][1]),
                          "tan_y": float(m["aop_tangency"][0]), "tan_x": float(m["aop_tangency"][1]),
                          "_gris": gris, "_mascara": nueva})
    for ruta in cache.values():
        os.unlink(ruta)
    print(f"Área mediana: pubis {np.median(valores_area['pubis']):.0f} px, cabeza {np.median(valores_area['cabeza']):.0f} px")

    for f in filas:
        mascara = f["_mascara"]
        Image.fromarray(f.pop("_gris")).save(SALIDA / "imagenes" / f"{f['nombre']}.png")
        Image.fromarray(mascara).save(SALIDA / "mascaras" / f"{f['nombre']}.png")
        f.pop("_mascara")
        f["imagen"] = f"datos/extraidos/intraparto/imagenes/{f['nombre']}.png"
        f["mascara"] = f"datos/extraidos/intraparto/mascaras/{f['nombre']}.png"

    cat = pd.DataFrame(filas)
    examenes = np.array(sorted(cat.loc[cat["parte"] == "train", "examen"].unique()))
    np.random.default_rng(SEMILLA).shuffle(examenes)
    validacion = set(examenes[: int(round(len(examenes) * 0.15))])
    cat["particion"] = np.where(cat["parte"] == "test", "prueba",
                                np.where((cat["parte"] == "val") | cat["examen"].isin(validacion), "validacion", "entrenamiento"))
    solapados = set(cat.loc[cat["particion"] == "prueba", "examen"]) & set(cat.loc[cat["particion"] != "prueba", "examen"])
    cat["examen_tambien_en_entrenamiento"] = cat["examen"].isin(solapados) & (cat["particion"] == "prueba")
    cat.to_csv(CATALOGO, index=False, encoding="utf-8")
    print(cat.groupby("particion").agg(imagenes=("nombre", "size"), examenes=("examen", "nunique"),
                                       aop_medio=("aop", "mean")).round(1).to_string())
    print(f"Exámenes de prueba que también aparecen en entrenamiento/validación: {len(solapados)}")


if __name__ == "__main__":
    main()
