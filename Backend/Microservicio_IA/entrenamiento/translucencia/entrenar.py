"""¿El corte sirve para medir la translucencia nucal? (control de calidad del tamizaje del 1.er trimestre)

    python entrenamiento/translucencia/entrenar.py

Datos: Dataset for Fetus Framework (Mendeley n2rbrb9t4f, CC BY 4.0): cortes
sagitales de 11–13+6 semanas del Shenzhen People's Hospital, etiquetados por
expertos como «estándar» o «no estándar» según la guía para medir la TN, más una
prueba EXTERNA de otra sede (Longhua). No es un diagnóstico de trisomía: dice si
el corte cumple la guía, porque una TN medida en un corte incorrecto invalida el
cálculo de riesgo (FMF) del sistema.

Fijado ANTES de mirar la prueba:
  · EfficientNet-B0 (la misma receta de entrenamiento/ginecologia/clasificar.py).
  · Entrenamiento = Set1 + Set2; 15 % estratificado para elegir la época.
  · Copias: la auditoría encontró 1 imagen de la prueba interna idéntica a una de
    entrenamiento (1660 = 1290) y 2 pares repetidos dentro de entrenamiento: fuera.
  · Umbral 0,5. Se informan la prueba interna y la externa por separado.

Ronda 2 (`--zoom`), decidida tras ver que la ronda 1 caía de 92 % a 58 % en la
otra sede: las imágenes de entrenamiento casi todas miden 640×450 con la cabeza
llenando el cuadro, y las de Longhua vienen con otro zoom y encuadre. La red usaba
el zoom como atajo. Aumento fijado de antemano (no se ajusta mirando la prueba
externa): alejar y acercar 0,5–1,15, recorte 0,6–1, desenfoque y contraste. Se
informan las dos rondas.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

import pandas as pd
import torch
from PIL import Image

AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]
sys.path.insert(0, str(IA / "entrenamiento" / "ginecologia"))
import clasificar  # noqa: E402
from clasificar import DESV, MEDIA, cuadrado, entrenar, metricas, predecir  # noqa: E402
from torchvision.transforms import v2 as T  # noqa: E402


class ImagenesConZoom(clasificar.Imagenes):
    """Igual que en clasificar.py, con zoom y estilo variables solo al entrenar."""

    def __init__(self, tensores, y, lado, entrenar):
        super().__init__(tensores, y, lado, entrenar)
        self.aumento = T.Compose([
            T.RandomAffine(degrees=12, scale=(0.5, 1.15), translate=(0.1, 0.1)),
            T.RandomResizedCrop(lado, scale=(0.6, 1.0), ratio=(0.85, 1.15), antialias=True),
            T.RandomHorizontalFlip(),
            T.RandomApply([T.GaussianBlur(5, sigma=(0.3, 2.0))], p=0.3),
            T.ColorJitter(brightness=0.35, contrast=0.35)])

BASE = IA / "datos" / "extraidos" / "obstetricia" / "nt" / "Dataset for Fetus Framework" / "Dataset for Fetus Framework"
CLASES = ["no_estandar", "estandar"]
NOMBRES = ["Corte no estándar para medir la TN", "Corte estándar para medir la TN"]
LADO = 320
SEMILLA = 2026
PARTES = {"Set1-Training&Validation Sets CNN": "entrenamiento", "Set2-Training&Validation Sets ANN Scoring system":
          "entrenamiento", "Internal Test Set": "prueba_interna", "External Test Set": "prueba_externa"}


def catalogo() -> pd.DataFrame:
    filas = []
    for p in sorted(BASE.glob("*/*/*.png")):
        filas.append({"ruta": p, "particion": PARTES[p.parent.parent.name],
                      "clase": CLASES.index("estandar" if p.parent.name == "Standard" else "no_estandar"),
                      "md5": hashlib.md5(p.read_bytes()).hexdigest()})
    df = pd.DataFrame(filas)
    en_entreno = set(df.loc[df["particion"] == "entrenamiento", "md5"])
    copias_prueba = df["particion"].str.startswith("prueba") & df["md5"].isin(en_entreno)
    df = df[~copias_prueba].drop_duplicates("md5").reset_index(drop=True)
    rng = random.Random(SEMILLA)
    df["validacion"] = False
    for c in (0, 1):
        idx = list(df[(df["particion"] == "entrenamiento") & (df["clase"] == c)].index)
        rng.shuffle(idx)
        df.loc[idx[: round(0.15 * len(idx))], "validacion"] = True
    return df, int(copias_prueba.sum())


def main() -> None:
    inicio = time.time()
    ronda = "zoom" if "--zoom" in sys.argv else "base"
    if ronda == "zoom":
        clasificar.Imagenes = ImagenesConZoom
    df, quitadas = catalogo()
    ent = df[(df["particion"] == "entrenamiento") & ~df["validacion"]]
    val = df[(df["particion"] == "entrenamiento") & df["validacion"]]
    x = {i: cuadrado(Image.open(r), LADO) for i, r in df["ruta"].items()}
    print(f"entrenamiento {len(ent)} · validación {len(val)} · interna {(df.particion == 'prueba_interna').sum()} · "
          f"externa {(df.particion == 'prueba_externa').sum()}", flush=True)
    red, historia, mejor = entrenar([x[i] for i in ent.index], ent["clase"].to_numpy(),
                                    [x[i] for i in val.index], val["clase"].to_numpy(), 2, LADO, "tn")
    salida = AQUI / "salidas" / ronda
    salida.mkdir(parents=True, exist_ok=True)
    m = {"tarea": "translucencia_nucal_calidad_del_corte",
         "dataset": "Dataset for Fetus Framework (Shenzhen People's Hospital; externa: sede Longhua) · Mendeley "
                    "n2rbrb9t4f · CC BY 4.0",
         "particion": "oficial: entrenamiento (Set1+Set2), prueba interna y prueba externa de otra sede",
         "copias_quitadas_de_la_prueba": quitadas, "ronda": ronda, "exactitud_balanceada_validacion": round(mejor, 4)}
    tablas = []
    for parte in ("prueba_interna", "prueba_externa"):
        d = df[df["particion"] == parte]
        prob = predecir(red, [x[i] for i in d.index], LADO)
        m[parte] = metricas(d["clase"].to_numpy(), prob, CLASES)
        from sklearn.metrics import roc_auc_score

        m[parte]["auc"] = round(float(roc_auc_score(d["clase"].to_numpy(), prob[:, 1])), 4)  # binaria
        t = pd.DataFrame({"imagen": d["ruta"].map(lambda r: r.relative_to(IA).as_posix()), "particion": parte,
                          "clase": d["clase"].map(lambda c: CLASES[c]), "p_estandar": prob[:, 1].round(4)})
        tablas.append(t)
    pd.concat(tablas).to_csv(salida / "predicciones_prueba.csv", index=False)
    torch.save({"estado": red.state_dict(), "meta": {
        "arquitectura": "efficientnet_b0", "clases": CLASES, "nombres": NOMBRES, "lado": LADO, "media": MEDIA,
        "desv": DESV, "variante": "imagen", "volteo_prueba": True, "metricas": m}},
        salida / "clasificador_translucencia_nucal.pth")
    (salida / "metricas.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    (salida / "historia.json").write_text(json.dumps(historia, indent=1), encoding="utf-8")
    for parte in ("prueba_interna", "prueba_externa"):
        p = m[parte]
        print(parte, {k: p[k] for k in ("imagenes", "exactitud", "exactitud_ic95", "exactitud_balanceada", "auc")},
              {k: v["sensibilidad"] for k, v in p["por_clase"].items()}, flush=True)
    print(f"Listo en {(time.time() - inicio) / 60:.1f} min")


if __name__ == "__main__":
    main()
