"""¿La red mira el cerebro o el «estilo» de las imágenes de anomalía?

Las anomalías de Fetal Brain Abnormalities vienen de compilaciones con otro
aspecto: más lavadas, con fondo gris, reescaladas. Seis estadísticas triviales
del píxel (sin anatomía) ya separan normal de anomalía con AUC 0,84.

Prueba de control: a cabezas NORMALES de otro hospital (HC18) se les pone ese
estilo, sin tocar la anatomía. Si la red da alarmas, está mirando el estilo.

    python prueba_estilo.py   → salidas/prueba_estilo.json
"""
import io
import json
import zlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageFilter

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import entrenar  # noqa: E402
from entrenar import IA, SALIDAS, UMBRAL, nueva_red, predecir  # noqa: E402

REDES = IA / "entrenamiento" / "redes_ecografia_real"


def lavada(im):
    """Contraste comprimido hacia el gris, como muchas imágenes de atlas."""
    a = np.asarray(im, dtype=np.float32)
    return Image.fromarray(np.clip(a * 0.6 + 70, 0, 255).astype(np.uint8))


def fondo_gris(im):
    """Rotación con relleno gris 128 (el relleno de los aumentos de Roboflow)."""
    return im.rotate(20, fillcolor=128, expand=True)


def reescalada(im):
    """Baja resolución y vuelta a subir: pérdida de detalle."""
    w, h = im.size
    return im.resize((w // 3, h // 3), Image.BILINEAR).resize((w, h), Image.BILINEAR)


def borrosa(im):
    return im.filter(ImageFilter.GaussianBlur(2))


def foto_de_pantalla(im):
    """Gamma, speckle, viñeteado y JPEG fuerte, como una foto del monitor
    reenviada por mensajería. NO se usa en el aumento de entrenamiento."""
    rng = np.random.default_rng(zlib.crc32(im.tobytes()))  # reproducible entre ejecuciones
    a = np.asarray(im, dtype=np.float32) / 255
    a = a ** 1.6
    a = a * rng.gamma(8, 1 / 8, a.shape)  # speckle multiplicativo
    h, w = a.shape
    yy, xx = np.mgrid[:h, :w]
    a = a * (1 - 0.35 * (((yy - h / 2) / h) ** 2 + ((xx - w / 2) / w) ** 2) * 4)
    buf = io.BytesIO()
    Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).save(buf, "JPEG", quality=15)
    return Image.open(io.BytesIO(buf.getvalue())).convert("L")


ESTILOS = {"original": lambda im: im, "lavada": lavada, "fondo_gris": fondo_gris,
           "reescalada": reescalada, "borrosa": borrosa,
           "todo_junto": lambda im: fondo_gris(lavada(reescalada(im))),
           "foto_de_pantalla": foto_de_pantalla}


def main(pesos=SALIDAS / "anomalias_cerebrales_b0.pth", destino=SALIDAS / "prueba_estilo.json"):
    cat = pd.read_excel(REDES / "catalogo_imagenes.xlsx", sheet_name="HC18")
    cat = cat[cat["trimestre"] != "primero"].sample(300, random_state=2026)
    red = nueva_red()
    red.load_state_dict(torch.load(pesos, weights_only=True))
    resultado = {}
    for nombre, estilo in ESTILOS.items():
        entrenar._CACHE.clear()
        rutas = []
        for r in cat["ruta"]:
            clave = f"estilo_{nombre}_{Path(r).name}"
            im = estilo(Image.open(REDES / r).convert("L"))
            im.thumbnail((entrenar.LADO + 32, entrenar.LADO + 32))
            lienzo = Image.new("L", (entrenar.LADO + 32, entrenar.LADO + 32))
            lienzo.paste(im, ((lienzo.width - im.width) // 2, (lienzo.height - im.height) // 2))
            entrenar._CACHE[clave] = torch.from_numpy(np.array(lienzo)).unsqueeze(0)
            rutas.append(clave)
        p = predecir(red, pd.DataFrame({"ruta": rutas, "familia": "normal"}))
        alarmas = int(((1 - p[:, 0]) >= UMBRAL).sum())
        resultado[nombre] = {"falsas_alarmas": alarmas, "n": len(rutas), "tasa": round(alarmas / len(rutas), 4)}
        print(f"{nombre:12s} falsas alarmas {alarmas:3d}/{len(rutas)}  ({alarmas / len(rutas):.1%})", flush=True)
    destino.write_text(json.dumps(resultado, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if "--v1" in sys.argv:
        v1 = SALIDAS / "v1_sin_estilo"
        main(v1 / "anomalias_cerebrales_b0.pth", v1 / "prueba_estilo.json")
    else:
        main()
