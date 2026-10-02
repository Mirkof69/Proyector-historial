"""Catálogos de los datasets ginecológicos, con particiones sin fugas.

    python entrenamiento/ginecologia/preparar.py

Deja en `catalogos/`:
  ovario.csv      MMOTU (tumores de ovario, 8 clases con informe de anatomía patológica)
  ovario_pco.csv  ovario normal / folículo dominante / poliquístico (Borna et al. 2025)
  mioma.csv       miomas uterinos con su caja (Mendeley n2zcmcypgb)

Reglas (las mismas que en obstetricia):
  · Nada de la prueba puede tener una casi copia en entrenamiento. Las casi
    copias se agrupan (dHash a <= 12 bits de 256) y el grupo entero va a una
    sola partición.
  · MMOTU trae una partición oficial «por paciente», pero la auditoría encontró
    37 pares de casi copias que la cruzan (p. ej. 1290-1291-1292) y 5 pares de
    casi copias con DIAGNÓSTICOS DISTINTOS (716 teratoma / 718 quiste
    endometriósico): esas imágenes se excluyen —no se sabe cuál etiqueta es
    la verdadera— y de la prueba se quitan las que tienen grupo en entrenamiento.
  · Miomas: el XML trae en <folder> el nombre de la paciente. Se usa solo para
    agrupar (sha256 truncado); el texto no se guarda en ningún archivo.
"""
from __future__ import annotations

import hashlib
import random
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
from auditar import dhash  # noqa: E402

DATOS = IA / "datos" / "extraidos" / "ginecologia"
CATALOGOS = AQUI / "catalogos"
SEMILLA = 2026
UMBRAL_CASI_COPIA = 12

CLASES_OVARIO = ["quiste_endometriosico", "cistoadenoma_seroso", "teratoma", "tumor_celulas_teca",
                 "quiste_simple", "ovario_normal", "cistoadenoma_mucinoso", "carcinoma_seroso_alto_grado"]
NOMBRES_OVARIO = ["Quiste endometriósico (chocolate)", "Cistoadenoma seroso", "Teratoma",
                  "Tumor de células de la teca", "Quiste simple", "Ovario normal", "Cistoadenoma mucinoso",
                  "Carcinoma seroso de alto grado"]
CLASES_PCO = ["normal", "foliculo_dominante", "poliquistico"]
CARPETAS_PCO = {"Normal": "normal", "Dominant_Follicle": "foliculo_dominante", "PCO": "poliquistico"}


def rel(p: Path) -> str:
    return p.relative_to(IA).as_posix()


def grupos_por_casi_copia(rutas: list[Path], umbral: int = UMBRAL_CASI_COPIA) -> dict[str, int]:
    """Unión de casi copias: {nombre: id de grupo}."""
    nombres = [r.name for r in rutas]
    h = [dhash(r) for r in rutas]
    padre = list(range(len(rutas)))

    def raiz(i: int) -> int:
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for i in range(len(h)):
        for j in range(i + 1, len(h)):
            if bin(h[i] ^ h[j]).count("1") <= umbral:
                padre[raiz(i)] = raiz(j)
    ids: dict[int, int] = {}
    return {n: ids.setdefault(raiz(i), len(ids)) for i, n in enumerate(nombres)}


def apartar_validacion(df: pd.DataFrame, columna_clase: str, fraccion: float = 0.15) -> pd.Series:
    """Fracción de los GRUPOS de cada clase como validación (para elegir la época)."""
    rng = random.Random(SEMILLA)
    val = set()
    clase_grupo = df.groupby("grupo")[columna_clase].agg(lambda s: s.mode().iloc[0])
    for _, grupos in clase_grupo.groupby(clase_grupo):
        g = sorted(grupos.index)
        rng.shuffle(g)
        val.update(g[:max(1, round(len(g) * fraccion))])
    return df["grupo"].isin(val)


def ovario() -> pd.DataFrame:
    base = DATOS / "mmotu"
    clase, oficial = {}, {}
    for archivo, part in (("train_cls.txt", "entrenamiento"), ("val_cls.txt", "prueba")):
        for linea in (base / archivo).read_text().splitlines():
            if linea.strip():
                nombre, c = linea.split()
                clase[nombre], oficial[nombre] = int(c), part
    rutas = sorted((base / "MMOTU" / "images").glob("*.JPG"))
    grupo = grupos_por_casi_copia(rutas)
    df = pd.DataFrame({"imagen": [rel(r) for r in rutas],
                       "mascara": [rel(base / "MMOTU" / "labels" / (r.stem + ".PNG")) for r in rutas],
                       "nombre": [r.name for r in rutas]})
    df["clase"] = df["nombre"].map(clase)
    df["clase_nombre"] = df["clase"].map(lambda c: CLASES_OVARIO[c])
    df["oficial"] = df["nombre"].map(oficial)
    df["grupo"] = df["nombre"].map(grupo)
    df["paciente"] = df["grupo"]  # entrenar.py de segmentación agrupa por esta columna

    # Grupos con diagnósticos contradictorios: fuera (no hay forma de saber cuál es cierto)
    contradictorios = df.groupby("grupo")["clase"].nunique()
    contradictorios = set(contradictorios[contradictorios > 1].index)
    # Grupos con imágenes en las dos particiones oficiales: su parte de prueba se quita
    cruzados = df.groupby("grupo")["oficial"].nunique()
    cruzados = set(cruzados[cruzados > 1].index)

    df["excluida"] = ""
    df.loc[df["grupo"].isin(contradictorios), "excluida"] = "casi copia con otro diagnóstico"
    df.loc[(df["excluida"] == "") & df["grupo"].isin(cruzados) & (df["oficial"] == "prueba"),
           "excluida"] = "casi copia de una imagen de entrenamiento"
    df["particion"] = np.where(df["excluida"] != "", "excluida", df["oficial"])
    entreno = df["particion"] == "entrenamiento"
    df.loc[entreno & apartar_validacion(df[entreno], "clase"), "particion"] = "validacion"
    return df.drop(columns=["nombre"])


def ovario_pco() -> pd.DataFrame:
    base = DATOS / "ovario_pco"
    rutas = sorted(base.glob("*/*.jpg"))
    grupo = grupos_por_casi_copia(rutas)
    df = pd.DataFrame({"ruta": [rel(r) for r in rutas], "clase_nombre": [CARPETAS_PCO[r.parent.name] for r in rutas],
                       "grupo": [grupo[r.name] for r in rutas]})
    df["clase"] = df["clase_nombre"].map(CLASES_PCO.index)
    # Copias exactas o casi exactas dentro de una misma clase: se deja una sola.
    df = df.drop_duplicates("grupo").reset_index(drop=True)
    # 5 pliegues estratificados por clase (una imagen por paciente según los autores)
    rng = random.Random(SEMILLA)
    df["pliegue"] = -1
    for _, idx in df.groupby("clase").groups.items():
        idx = list(idx)
        rng.shuffle(idx)
        for k, i in enumerate(idx):
            df.loc[i, "pliegue"] = k % 5
    return df


def mioma() -> pd.DataFrame:
    base = DATOS / "miomas"
    salida_masc = base / "mascaras"
    salida_masc.mkdir(exist_ok=True)
    filas = []
    for xml in sorted((base / "Annotations").glob("*.xml")):
        img = base / "JPEGImages" / (xml.stem + ".jpg")
        if not img.exists():
            continue
        t = xml.read_text(encoding="utf-8", errors="replace")
        carpeta = re.search(r"<folder>(.*?)</folder>", t)
        paciente = hashlib.sha256((carpeta.group(1) if carpeta else xml.stem).encode()).hexdigest()[:12]
        cajas = [tuple(int(float(v)) for v in m) for m in re.findall(
            r"<xmin>(.*?)</xmin>\s*<ymin>(.*?)</ymin>\s*<xmax>(.*?)</xmax>\s*<ymax>(.*?)</ymax>", t)]
        if not cajas:
            continue  # 9 imágenes sin ningún mioma marcado: sin caja no hay qué aprender ni medir
        with Image.open(img) as im:
            w, h = im.size
        masc = Image.new("L", (w, h), 0)
        dibujo = ImageDraw.Draw(masc)
        for x0, y0, x1, y1 in cajas:
            dibujo.rectangle([x0, y0, x1, y1], fill=1)
        ruta_masc = salida_masc / (xml.stem + ".png")
        masc.save(ruta_masc)
        filas.append({"imagen": rel(img), "mascara": rel(ruta_masc), "paciente": paciente,
                      "cajas": ";".join(",".join(map(str, c)) for c in cajas), "miomas": len(cajas)})
    df = pd.DataFrame(filas)
    # Las casi copias de pacientes distintas se unen al mismo grupo (auditoría: 0, pero se garantiza).
    rutas = [IA / r for r in df["imagen"]]
    casi = grupos_por_casi_copia(rutas)
    union: dict[str, str] = {}
    for p, c in zip(df["paciente"], (casi[r.name] for r in rutas)):
        union.setdefault(f"c{c}", p)
    df["grupo"] = [union[f"c{casi[r.name]}"] for r in rutas]
    # 70/15/15 por paciente
    rng = random.Random(SEMILLA)
    grupos = sorted(df["grupo"].unique())
    rng.shuffle(grupos)
    n = len(grupos)
    part = {g: ("entrenamiento" if i < 0.70 * n else "validacion" if i < 0.85 * n else "prueba")
            for i, g in enumerate(grupos)}
    df["particion"] = df["grupo"].map(part)
    return df


def main() -> None:
    CATALOGOS.mkdir(exist_ok=True)
    for nombre, funcion in (("ovario", ovario), ("ovario_pco", ovario_pco), ("mioma", mioma)):
        df = funcion()
        df.to_csv(CATALOGOS / f"{nombre}.csv", index=False)
        col = "particion" if "particion" in df else "pliegue"
        print(f"\n{nombre}: {len(df)} imágenes")
        print(df.groupby(col).agg(imagenes=("grupo", "size"), grupos=("grupo", "nunique")).to_string())
        if "clase_nombre" in df:
            print(pd.crosstab(df["clase_nombre"], df[col]).to_string())
        if "excluida" in df:
            print(df[df["excluida"] != ""]["excluida"].value_counts().to_string())


if __name__ == "__main__":
    main()
