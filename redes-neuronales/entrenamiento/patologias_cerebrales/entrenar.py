"""Entrena y mide la red de anomalías cerebrales fetales.

    python preparar.py          # una vez: salidas/manifiesto.csv
    python entrenar.py          # 5 pliegues + modelo final (GPU, ~35 min)

Decisiones fijadas ANTES de ver ningún resultado de prueba:

  · EfficientNet-B0 preentrenada en ImageNet, 320 px, 5 salidas
    (normal + 4 familias). P(anomalía) = 1 - P(normal).
  · Cada pliegue aparta el 15 % de sus grupos de entrenamiento como validación
    interna: con ella se elige la época. El pliegue de prueba no se usa para
    nada hasta la evaluación final.
  · Umbral de alarma: 0,5. No se ajusta mirando la prueba.
  · Muestreo equilibrado: cada imagen ORIGINAL pesa igual (no sus copias
    aumentadas), cada familia pesa igual, y los normales de las dos fuentes
    pesan igual, para que la red no aprenda «Roboflow = anomalía».
  · Se evalúa por imagen original (media de sus copias), nunca por archivo:
    contar 8 copias de la misma imagen como 8 aciertos infla la muestra.
  · Aumento de ESTILO para todas las clases por igual (v2): las anomalías del
    dataset vienen de compilaciones con otro aspecto (lavadas, fondo gris,
    baja resolución) y la v1 aprendió en parte ese aspecto: con él, el 46 % de
    cabezas normales de otro hospital daban alarma (prueba_estilo.py). Si el
    estilo aparece igual en normales y anomalías, deja de servir para
    distinguirlas y la red tiene que mirar la anatomía.
"""
import json
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import timm
import torch
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision.transforms import v2 as T

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
IA = AQUI.parents[1]  # las rutas del manifiesto son relativas al microservicio
SALIDAS = AQUI / "salidas"
SEMILLA = 2026
LADO = 320
EPOCAS = 30
LOTE = 32
FAMILIAS = ["normal", "ventriculomegalia_hidrocefalia", "fosa_posterior", "encefalocele",
            "lesion_quistica_vascular"]
UMBRAL = 0.5
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"


def fijar_semilla(s):
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


_CACHE = {}


def cargar(ruta):
    """Escala de grises, lado mayor LADO+32, en memoria."""
    if ruta not in _CACHE:
        im = Image.open(IA / ruta).convert("L")
        im.thumbnail((LADO + 32, LADO + 32))
        lienzo = Image.new("L", (LADO + 32, LADO + 32))
        lienzo.paste(im, ((LADO + 32 - im.width) // 2, (LADO + 32 - im.height) // 2))
        _CACHE[ruta] = torch.from_numpy(np.array(lienzo)).unsqueeze(0)
    return _CACHE[ruta]


AUMENTO = T.Compose([
    T.RandomResizedCrop(LADO, scale=(0.75, 1.0), ratio=(0.9, 1.1), antialias=True),
    T.RandomHorizontalFlip(),
    T.RandomAffine(degrees=15),
    T.ColorJitter(brightness=0.25, contrast=0.25),
])
PRUEBA = T.Compose([T.CenterCrop(LADO)])


def estilo_aleatorio(x):
    """Con probabilidad 0,5, aspecto de «imagen de compilación» (uint8, 1×H×W).

    Cada efecto se aplica por separado con probabilidad 0,6. La prueba de
    «foto de pantalla» de prueba_estilo.py (JPEG, gamma, speckle) NO se usa
    aquí, para que siga siendo una prueba que la red no vio.
    """
    if random.random() >= 0.5:
        return x
    x = x.float()
    if random.random() < 0.6:  # baja resolución
        f = random.uniform(2, 4)
        h, w = x.shape[-2:]
        x = F.interpolate(F.interpolate(x[None], size=(int(h / f), int(w / f)), mode="bilinear"),
                          size=(h, w), mode="bilinear")[0]
    if random.random() < 0.6:  # contraste lavado hacia el gris
        x = x * random.uniform(0.5, 0.9) + random.uniform(20, 90)
    if random.random() < 0.6:  # rotación con relleno gris
        x = T.functional.affine(x, angle=random.uniform(-30, 30), translate=[0, 0], scale=1.0, shear=[0.0],
                                fill=[random.uniform(60, 190)])
    if random.random() < 0.3:
        x = T.functional.gaussian_blur(x, kernel_size=5, sigma=random.uniform(0.5, 2))
    return x.clamp(0, 255).to(torch.uint8)


class Imagenes(Dataset):
    def __init__(self, df, entrenar):
        self.rutas = df["ruta"].tolist()
        self.y = [FAMILIAS.index(f) for f in df["familia"]]
        self.entrenar = entrenar
        self.t = AUMENTO if entrenar else PRUEBA

    def __len__(self):
        return len(self.rutas)

    def __getitem__(self, i):
        x = cargar(self.rutas[i])
        if self.entrenar:
            x = estilo_aleatorio(x)
        x = self.t(x).float().div(255)
        x = (x - 0.45) / 0.225
        return x.expand(3, -1, -1), self.y[i]


def pesos_muestreo(df):
    """Cada original pesa igual dentro de su estrato; normales de ambas fuentes
    igual; y normal frente a anomalía 50/50 (las 4 familias se reparten su mitad).
    """
    archivos_grupo = df.groupby("grupo")["ruta"].transform("size")
    grupos_estrato = df.groupby(["fuente", "familia"])["grupo"].transform("nunique")
    fuentes_familia = df.groupby("familia")["fuente"].transform("nunique")
    mitad = np.where(df["familia"] == "normal", len(FAMILIAS) - 1, 1)
    return (mitad / archivos_grupo / grupos_estrato / fuentes_familia).to_numpy()


def nueva_red():
    return timm.create_model("efficientnet_b0.ra_in1k", pretrained=True, num_classes=len(FAMILIAS),
                             drop_rate=0.3).to(DISPOSITIVO)


@torch.no_grad()
def predecir(red, df):
    red.eval()
    carga = DataLoader(Imagenes(df, entrenar=False), batch_size=64)
    probs = []
    for x, _ in carga:
        x = x.to(DISPOSITIVO)
        with torch.autocast(DISPOSITIVO, dtype=torch.float16):
            # prueba con volteo horizontal (fijado de antemano, no se elige)
            p = F.softmax(red(x).float(), 1) + F.softmax(red(torch.flip(x, [3])).float(), 1)
        probs.append((p / 2).cpu())
    return torch.cat(probs).numpy()


def perdida_media(red, df):
    p = predecir(red, df)
    y = np.array([FAMILIAS.index(f) for f in df["familia"]])
    w = pesos_muestreo(df)
    return float(np.sum(-np.log(p[np.arange(len(y)), y] + 1e-7) * w) / w.sum())


def entrenar(df_entreno, df_val, etiqueta):
    fijar_semilla(SEMILLA)
    red = nueva_red()
    muestreo = WeightedRandomSampler(pesos_muestreo(df_entreno), num_samples=len(df_entreno), replacement=True)
    carga = DataLoader(Imagenes(df_entreno, entrenar=True), batch_size=LOTE, sampler=muestreo)
    opt = torch.optim.AdamW(red.parameters(), lr=3e-4, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=3e-4, total_steps=EPOCAS * len(carga), pct_start=0.1)
    escala = torch.amp.GradScaler()
    mejor, mejor_estado, historia = 1e9, None, []
    for epoca in range(1, EPOCAS + 1):
        red.train()
        total = 0.0
        for x, y in carga:
            x, y = x.to(DISPOSITIVO), y.to(DISPOSITIVO)
            with torch.autocast(DISPOSITIVO, dtype=torch.float16):
                perdida = F.cross_entropy(red(x), y, label_smoothing=0.05)
            opt.zero_grad()
            escala.scale(perdida).backward()
            escala.step(opt)
            escala.update()
            sched.step()
            total += perdida.item()
        val = perdida_media(red, df_val)
        historia.append({"epoca": epoca, "perdida_entreno": total / len(carga), "perdida_val": val})
        if val < mejor:
            mejor, mejor_estado = val, {k: v.detach().clone() for k, v in red.state_dict().items()}
        print(f"  [{etiqueta}] época {epoca:2d}  entreno {total / len(carga):.3f}  val {val:.3f}"
              f"{'  *' if val == mejor else ''}", flush=True)
    red.load_state_dict(mejor_estado)
    return red, historia


def apartar_validacion(df):
    """15 % de los grupos de cada estrato como validación interna."""
    rng = random.Random(SEMILLA)
    val = set()
    for _, grupos in df.groupby(["fuente", "familia"])["grupo"]:
        g = sorted(set(grupos))
        rng.shuffle(g)
        val.update(g[:max(1, round(len(g) * 0.15))])
    es_val = df["grupo"].isin(val)
    return df[~es_val], df[es_val]


def por_original(df, probs):
    """Media de las copias de cada imagen original."""
    tabla = df[["grupo", "fuente", "familia", "etiqueta_fina", "pliegue"]].copy()
    for i, f in enumerate(FAMILIAS):
        tabla["p_" + f] = probs[:, i]
    if "ecografo" in df:
        tabla["ecografo"] = df["ecografo"].to_numpy()
    # En FETAL_PLANES cada archivo es una imagen distinta; en Roboflow las copias
    # de un original comparten grupo.
    tabla["clave"] = np.where(tabla["fuente"] == "roboflow", tabla["grupo"], df["ruta"].to_numpy())
    agregado = tabla.groupby("clave").agg({**{"p_" + f: "mean" for f in FAMILIAS},
                                           "grupo": "first", "fuente": "first", "familia": "first",
                                           "etiqueta_fina": "first", "pliegue": "first",
                                           **({"ecografo": "first"} if "ecografo" in tabla else {})})
    return agregado.reset_index()


def main():
    SALIDAS.mkdir(exist_ok=True)
    df = pd.read_csv(SALIDAS / "manifiesto.csv")
    reparto, externos = df[df["pliegue"] >= 0], df[df["pliegue"] < 0]
    print(f"Precargando {len(df)} imágenes…", flush=True)
    for r in df["ruta"]:
        cargar(r)

    inicio = time.time()
    fuera_de_pliegue, historias = [], {}
    for k in range(5):
        prueba = reparto[reparto["pliegue"] == k]
        entreno, val = apartar_validacion(reparto[reparto["pliegue"] != k])
        print(f"\nPliegue {k}: entreno {len(entreno)}  val {len(val)}  prueba {len(prueba)}", flush=True)
        red, historias[f"pliegue_{k}"] = entrenar(entreno, val, f"p{k}")
        fuera_de_pliegue.append(por_original(prueba, predecir(red, prueba)))
        del red
        torch.cuda.empty_cache()
    oof = pd.concat(fuera_de_pliegue, ignore_index=True)
    oof.to_csv(SALIDAS / "predicciones_fuera_de_pliegue.csv", index=False, encoding="utf-8")

    # Modelo final: todo el reparto (con 15 % de validación para la época).
    print("\nModelo final con todos los pliegues", flush=True)
    entreno, val = apartar_validacion(reparto)
    red, historias["final"] = entrenar(entreno, val, "final")
    ext = por_original(externos, predecir(red, externos))
    ext.to_csv(SALIDAS / "predicciones_externas.csv", index=False, encoding="utf-8")

    pesos = SALIDAS / "anomalias_cerebrales_b0.pth"  # v2: con aumento de estilo
    torch.save(red.state_dict(), pesos)
    (SALIDAS / "historia.json").write_text(json.dumps(historias, indent=1), encoding="utf-8")
    print(f"\nListo en {(time.time() - inicio) / 60:.1f} min. Métricas: python evaluar.py", flush=True)


if __name__ == "__main__":
    main()
