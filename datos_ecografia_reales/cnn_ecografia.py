"""Las dos redes neuronales convolucionales sobre ecografías reales.

1. REGRESIÓN — de la imagen de la cabeza a su circunferencia en milímetros (HC18).
2. CLASIFICACIÓN — de la imagen al plano anatómico que muestra (FETAL_PLANES_DB).

Las dos parten de EfficientNet-B0 preentrenada en ImageNet: una red que ya sabe
reconocer bordes, texturas y formas, y a la que solo hay que enseñarle
ecografía. Con 709 imágenes de entrenamiento, empezar de cero no funcionaría.

Decisiones que importan
-----------------------
**La circunferencia se predice en fracción de la imagen, no en milímetros.**
La red ve píxeles y no puede saber cuántos milímetros mide cada uno: eso
depende del zoom del ecógrafo. Por eso aprende «qué fracción del ancho de la
imagen mide el contorno de la cabeza», y los milímetros se obtienen después
multiplicando por el tamaño del píxel, que viene con cada imagen. Es la parte
«información» del modelo: sin ese dato, la misma imagen no tiene medida.

**Las imágenes se encuadran sin deformarlas.** Se rellenan hasta hacerlas
cuadradas antes de reducirlas. Estirar una imagen de 800×540 a un cuadrado
achataría la cabeza, y su contorno dejaría de corresponder a la medida real.

**En la regresión no se aumenta con zoom.** Voltear y girar la imagen no cambia
el contorno de la cabeza; ampliarla sí, y el objetivo dejaría de ser correcto.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

AQUI = Path(__file__).resolve().parent
MODELOS = AQUI / "modelos"
DISPOSITIVO = "cuda" if torch.cuda.is_available() else "cpu"
SEMILLA = 2026

PLANOS = ["abdomen fetal", "cerebro fetal", "fémur fetal", "tórax fetal",
          "cuello uterino materno", "otro"]

MEDIA, DESV = 0.485, 0.229   # de ImageNet, canal único replicado a 3


def fijar_semilla(s: int = SEMILLA) -> None:
    import random
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


# ───────────────────────────── imágenes ────────────────────────────────────

def cargar_cuadrada(ruta: Path, lado: int) -> tuple[np.ndarray, int]:
    """Imagen en gris, rellenada a cuadrado SIN deformar y reducida a `lado`.

    Devuelve también el lado mayor original en píxeles: hace falta para pasar
    la predicción de la red a milímetros.
    """
    img = Image.open(ruta).convert("L")
    w, h = img.size
    mayor = max(w, h)
    lienzo = Image.new("L", (mayor, mayor), 0)
    lienzo.paste(img, ((mayor - w) // 2, (mayor - h) // 2))
    return np.asarray(lienzo.resize((lado, lado), Image.BILINEAR), dtype=np.uint8), mayor


def precargar(rutas: list[Path], lado: int) -> tuple[np.ndarray, np.ndarray]:
    """Todas las imágenes en memoria, una vez. Entrenar leyendo PNG en cada
    época sería varias veces más lento, y con 60 GB de RAM caben de sobra."""
    with ThreadPoolExecutor(max_workers=12) as pool:
        res = list(pool.map(lambda r: cargar_cuadrada(r, lado), rutas))
    return np.stack([r[0] for r in res]), np.array([r[1] for r in res])


def a_tensor(lote: np.ndarray) -> torch.Tensor:
    x = torch.from_numpy(lote).float().div_(255.0).sub_(MEDIA).div_(DESV)
    return x.unsqueeze(1).repeat(1, 3, 1, 1)


def aumentar(x: torch.Tensor, con_zoom: bool) -> torch.Tensor:
    """Aumento de datos en GPU, por lote.

    Volteos y giros de 90°: no cambian ni el plano ni el contorno de la cabeza.
    Brillo y contraste: los ecógrafos no calibran igual.
    Zoom y desplazamiento pequeños: solo en clasificación, porque en regresión
    cambiarían el tamaño aparente de la cabeza.
    """
    n = x.shape[0]
    if torch.rand(1).item() < 0.5:
        x = x.flip(3)
    if torch.rand(1).item() < 0.5:
        x = x.flip(2)
    k = int(torch.randint(0, 4, (1,)).item())
    if k:
        x = torch.rot90(x, k, dims=(2, 3))
    brillo = (torch.rand(n, 1, 1, 1, device=x.device) - 0.5) * 0.4
    contraste = 1 + (torch.rand(n, 1, 1, 1, device=x.device) - 0.5) * 0.4
    x = x * contraste + brillo
    if con_zoom:
        escala = 1 + (torch.rand(n, device=x.device) - 0.5) * 0.2
        desp = (torch.rand(n, 2, device=x.device) - 0.5) * 0.1
        theta = torch.zeros(n, 2, 3, device=x.device)
        theta[:, 0, 0] = escala
        theta[:, 1, 1] = escala
        theta[:, :, 2] = desp
        rejilla = F.affine_grid(theta, x.shape, align_corners=False)
        x = F.grid_sample(x, rejilla, align_corners=False)
    return x


def crear_red(salidas: int) -> nn.Module:
    import timm
    return timm.create_model("efficientnet_b0", pretrained=True, num_classes=salidas)


def _entrenar(modelo, X, y, X_val, y_val, *, epocas, lote, lr, perdida, es_regresion,
              registro, pesos_clase=None):
    """Bucle común. Se queda con la época que mejor va en VALIDACIÓN, nunca en
    prueba: elegir con la prueba sería mirar las respuestas del examen."""
    modelo.to(DISPOSITIVO)
    opt = torch.optim.AdamW(modelo.parameters(), lr=lr, weight_decay=1e-4)
    pasos = epocas * int(np.ceil(len(X) / lote))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=pasos, pct_start=0.15)
    escalador = torch.amp.GradScaler("cuda", enabled=DISPOSITIVO == "cuda")
    y_t = torch.as_tensor(y)
    mejor, mejor_estado, historia = float("inf"), None, []

    for ep in range(1, epocas + 1):
        modelo.train()
        orden = np.random.permutation(len(X))
        total, t0 = 0.0, time.perf_counter()
        for i in range(0, len(X), lote):
            idx = orden[i:i + lote]
            xb = aumentar(a_tensor(X[idx]).to(DISPOSITIVO, non_blocking=True),
                          con_zoom=not es_regresion)
            yb = y_t[idx].to(DISPOSITIVO)
            with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
                salida = modelo(xb)
                salida = salida.squeeze(1) if es_regresion else salida
                loss = perdida(salida.float(), yb)
            opt.zero_grad(set_to_none=True)
            escalador.scale(loss).backward()
            escalador.step(opt)
            escalador.update()
            sched.step()
            total += loss.item() * len(idx)

        pred_val = predecir(modelo, X_val, es_regresion)
        if es_regresion:
            metrica = float(np.mean(np.abs(pred_val - y_val)))
        else:
            metrica = float(F.cross_entropy(torch.as_tensor(np.log(pred_val + 1e-9)),
                                            torch.as_tensor(y_val), reduction="mean"))
        historia.append({"epoca": ep, "perdida_entreno": total / len(X), "val": metrica})
        if metrica < mejor:
            mejor = metrica
            mejor_estado = {k: v.detach().cpu().clone() for k, v in modelo.state_dict().items()}
        if registro:
            registro(f"  época {ep:2d}/{epocas}  pérdida {total / len(X):.4f}  "
                     f"validación {metrica:.4f}  ({time.perf_counter() - t0:.0f} s)")

    modelo.load_state_dict(mejor_estado)
    return modelo, historia


@torch.no_grad()
def predecir(modelo, X, es_regresion, lote=128):
    modelo.eval()
    salidas = []
    for i in range(0, len(X), lote):
        xb = a_tensor(X[i:i + lote]).to(DISPOSITIVO)
        with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
            s = modelo(xb).float()
        salidas.append(s.squeeze(1).cpu().numpy() if es_regresion else s.softmax(1).cpu().numpy())
    return np.concatenate(salidas)


# ───────────────────────── 1. circunferencia cefálica ──────────────────────

LADO_HC = 320


def entrenar_circunferencia(catalogo: pd.DataFrame, epocas=40, registro=print):
    """Entrena la regresión y devuelve (modelo, historia, tabla de prueba)."""
    fijar_semilla()
    datos = {}
    for parte in ("entrenamiento", "validacion", "prueba"):
        d = catalogo[catalogo["particion"] == parte].reset_index(drop=True)
        X, mayor = precargar([AQUI / r for r in d["ruta"]], LADO_HC)
        # Objetivo: fracción del lado mayor que mide el contorno de la cabeza.
        y = (d["circunferencia_cefalica_mm"] / (d["tamano_pixel_mm"] * mayor)).to_numpy(np.float32)
        datos[parte] = (d, X, y, mayor)
        registro(f"  {parte:<13} {len(d):4d} imágenes")

    d_e, X_e, y_e, _ = datos["entrenamiento"]
    d_v, X_v, y_v, _ = datos["validacion"]
    modelo, historia = _entrenar(
        crear_red(1), X_e, y_e, X_v, y_v, epocas=epocas, lote=24, lr=6e-4,
        perdida=nn.SmoothL1Loss(beta=0.01), es_regresion=True, registro=registro,
    )

    d_p, X_p, _, mayor_p = datos["prueba"]
    return modelo, historia, _tabla_prueba_hc(modelo, d_p, X_p, mayor_p)


def _tabla_prueba_hc(modelo, d_p, X_p, mayor_p) -> pd.DataFrame:
    fraccion = predecir(modelo, X_p, True)
    prueba = d_p.copy()
    prueba["hc_predicha_mm"] = (fraccion * d_p["tamano_pixel_mm"].to_numpy() * mayor_p).round(2)
    prueba["error_mm"] = (prueba["hc_predicha_mm"] - prueba["circunferencia_cefalica_mm"]).round(2)
    return prueba


def evaluar_circunferencia(catalogo: pd.DataFrame, modelo) -> pd.DataFrame:
    """La tabla de prueba de una red ya entrenada (la guardada en modelos/)."""
    d_p = catalogo[catalogo["particion"] == "prueba"].reset_index(drop=True)
    X_p, mayor_p = precargar([AQUI / r for r in d_p["ruta"]], LADO_HC)
    return _tabla_prueba_hc(modelo.to(DISPOSITIVO), d_p, X_p, mayor_p)


# ──────────────────────────── 2. plano anatómico ───────────────────────────

LADO_PLANO = 224


def entrenar_planos(catalogo: pd.DataFrame, epocas=14, registro=print):
    """Entrena la clasificación y devuelve (modelo, historia, tabla de prueba)."""
    fijar_semilla()
    idx_clase = {p: i for i, p in enumerate(PLANOS)}
    datos = {}
    for parte in ("entrenamiento", "validacion", "prueba"):
        d = catalogo[catalogo["particion"] == parte].reset_index(drop=True)
        X, _ = precargar([AQUI / r for r in d["ruta"]], LADO_PLANO)
        y = d["plano"].map(idx_clase).to_numpy(np.int64)
        datos[parte] = (d, X, y)
        registro(f"  {parte:<13} {len(d):5d} imágenes")

    _, X_e, y_e = datos["entrenamiento"]
    _, X_v, y_v = datos["validacion"]

    # Pesos por clase (raíz de la inversa de la frecuencia): «otro» tiene seis
    # veces más imágenes que «abdomen». Sin compensar, la red aprendería a decir
    # «otro» ante la duda. La raíz suaviza para no irse al extremo contrario.
    frec = np.bincount(y_e, minlength=len(PLANOS)).astype(float)
    pesos = torch.tensor((frec.sum() / frec) ** 0.5, dtype=torch.float32)
    pesos = pesos / pesos.mean()
    perdida = nn.CrossEntropyLoss(weight=pesos.to(DISPOSITIVO), label_smoothing=0.05)

    modelo, historia = _entrenar(
        crear_red(len(PLANOS)), X_e, y_e, X_v, y_v, epocas=epocas, lote=64, lr=1e-3,
        perdida=perdida, es_regresion=False, registro=registro,
    )

    d_p, X_p, _ = datos["prueba"]
    return modelo, historia, _tabla_prueba_planos(modelo, d_p, X_p)


def _tabla_prueba_planos(modelo, d_p, X_p) -> pd.DataFrame:
    prob = predecir(modelo, X_p, False)
    prueba = d_p.copy()
    prueba["plano_predicho"] = [PLANOS[i] for i in prob.argmax(1)]
    for i, p in enumerate(PLANOS):
        prueba[f"prob_{p}"] = prob[:, i].round(5)
    return prueba


def evaluar_planos(catalogo: pd.DataFrame, modelo) -> pd.DataFrame:
    """La tabla de prueba de una red ya entrenada (la guardada en modelos/)."""
    d_p = catalogo[catalogo["particion"] == "prueba"].reset_index(drop=True)
    X_p, _ = precargar([AQUI / r for r in d_p["ruta"]], LADO_PLANO)
    return _tabla_prueba_planos(modelo.to(DISPOSITIVO), d_p, X_p)


# ─────────────────────────────── guardar ───────────────────────────────────

def guardar(modelo, nombre: str, meta: dict) -> Path:
    """Pesos + la información necesaria para usarlos igual en el sistema."""
    MODELOS.mkdir(exist_ok=True)
    ruta = MODELOS / f"{nombre}.pth"
    torch.save({"estado": modelo.state_dict(), "meta": meta}, ruta)
    (MODELOS / f"{nombre}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def cargar(nombre: str):
    """(red, ficha) de un modelo guardado con `guardar`."""
    import timm
    paquete = torch.load(MODELOS / f"{nombre}.pth", map_location=DISPOSITIVO, weights_only=True)
    meta = paquete["meta"]
    salidas = len(meta["clases"]) if "clases" in meta else 1
    red = timm.create_model(meta["arquitectura"], pretrained=False, num_classes=salidas)
    red.load_state_dict(paquete["estado"])
    return red.to(DISPOSITIVO).eval(), meta


@torch.no_grad()
def rasgos_imagenet(rutas: list[Path], lado: int = LADO_PLANO, lote: int = 128) -> np.ndarray:
    """1.280 rasgos por imagen de una EfficientNet-B0 preentrenada SOLO en
    ImageNet (fotos generales). No ha visto ninguna etiqueta de ecografía: es
    la base para probar un modelo NO supervisado sobre estas imágenes."""
    import timm
    red = timm.create_model("efficientnet_b0", pretrained=True, num_classes=0).to(DISPOSITIVO).eval()
    X, _ = precargar(rutas, lado)
    salida = []
    for i in range(0, len(X), lote):
        with torch.autocast("cuda", dtype=torch.float16, enabled=DISPOSITIVO == "cuda"):
            salida.append(red(a_tensor(X[i:i + lote]).to(DISPOSITIVO)).float().cpu().numpy())
    return np.concatenate(salida)
