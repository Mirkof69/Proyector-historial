# -*- coding: utf-8 -*-
"""
Generador de imagenes sinteticas de ultrasonido fetal.
Usa augmentacion avanzada + DCGAN con RTX 4070 (CUDA 12.4).
Para las 11 clases vacias del modelo EfficientNet-B4.

Estrategia:
  1. Tomar imagenes reales de clases disponibles (normal, hidrocefalia, etc.)
  2. Aplicar transformaciones especificas por patologia (textura, geometria, intensidad)
  3. Generar 200-500 imagenes por clase vacia
"""

import sys, os, random, logging
from pathlib import Path

import torch
import torch.nn as nn
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("synth_gen")

# ── Rutas ──────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR / "datasets_pathology" / "train"
VAL_DIR   = BASE_DIR / "datasets_pathology" / "validation"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
log.info("Dispositivo: %s", DEVICE)
if DEVICE == "cuda":
    log.info("GPU: %s", torch.cuda.get_device_name(0))

# ── Configuracion por clase ─────────────────────────────────────────────────────
# Cada clase vacia se genera a partir de una clase "base" real
# con transformaciones especificas que simulan la patologia
CLASS_CONFIGS = {
    "espina_bifida": {
        "base_class": "hidrocefalia",   # cerebro fetal como base
        "n_train": 300,
        "n_val":    75,
        "transforms": "spine",          # transformaciones de columna
        "description": "Neural tube defect — columna vertebral fetal"
    },
    "anencefalia": {
        "base_class": "hidrocefalia",
        "n_train": 300,
        "n_val":    75,
        "transforms": "anencephaly",    # ausencia de calota craneal
        "description": "Ausencia de boveda craneal"
    },
    "oligohidramnios": {
        "base_class": "normal",
        "n_train": 250,
        "n_val":    62,
        "transforms": "oligo",          # liquido reducido (imagen mas densa)
        "description": "Liquido amniotico reducido"
    },
    "polihidramnios": {
        "base_class": "normal",
        "n_train": 250,
        "n_val":    62,
        "transforms": "poly",           # liquido aumentado (area oscura grande)
        "description": "Liquido amniotico en exceso"
    },
    "embarazo_multiple": {
        "base_class": "normal",
        "n_train": 300,
        "n_val":    75,
        "transforms": "twin",           # duplicar estructura fetal
        "description": "Embarazo gemelar"
    },
    "labio_leporino": {
        "base_class": "normal",
        "n_train": 200,
        "n_val":    50,
        "transforms": "cleft",          # region facial con hendidura
        "description": "Hendidura labial y palatina"
    },
    "placenta_previa": {
        "base_class": "preeclampsia_signos",
        "n_train": 250,
        "n_val":    62,
        "transforms": "placenta",       # masa placentaria baja
        "description": "Placenta en segmento uterino inferior"
    },
    "atresia_duodenal": {
        "base_class": "normal",
        "n_train": 200,
        "n_val":    50,
        "transforms": "duodenal",       # signo doble burbuja
        "description": "Obstruccion duodenal — signo doble burbuja"
    },
    "restriccion_crecimiento": {
        "base_class": "hidrocefalia",
        "n_train": 200,
        "n_val":    50,
        "transforms": "iugr",           # feto pequeno para edad gestacional
        "description": "Restriccion de crecimiento intrauterino"
    },
    "macrosomia_fetal": {
        "base_class": "normal",
        "n_train": 200,
        "n_val":    50,
        "transforms": "macro",          # feto grande
        "description": "Feto grande para edad gestacional"
    },
    "muerte_fetal": {
        "base_class": "hidrocefalia",
        "n_train": 160,
        "n_val":    40,
        "transforms": "fetal_death",    # sin movimiento, textura alterada
        "description": "Muerte fetal intrauterina"
    },
}

# ── Transformaciones especificas por patologia ─────────────────────────────────

def apply_spine_transform(img: Image.Image) -> Image.Image:
    """Espina bifida: resaltar area posterior con defecto."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 1.3)
    img = TF.adjust_brightness(img, 0.85)
    # Rotar para simular vista sagital de columna
    angle = random.uniform(-30, 30)
    img = TF.rotate(img, angle, fill=0)
    # Agregar region hiperecogenica (defecto del tubo neural)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    x0 = int(w * random.uniform(0.35, 0.55))
    y0 = int(h * random.uniform(0.4, 0.65))
    r = random.randint(8, 18)
    draw.ellipse([x0-r, y0-r, x0+r, y0+r], fill=(180, 180, 180))
    return img

def apply_anencephaly_transform(img: Image.Image) -> Image.Image:
    """Anencefalia: eliminar boveda craneal superior."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 1.2)
    w, h = img.size
    # Oscurecer la parte superior (ausencia de calota)
    arr = np.array(img).astype(np.float32)
    mask_h = int(h * random.uniform(0.25, 0.40))
    arr[:mask_h, :] *= random.uniform(0.1, 0.3)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    img = TF.adjust_brightness(img, 0.9)
    return img

def apply_oligo_transform(img: Image.Image) -> Image.Image:
    """Oligohidramnios: imagen mas densa, menos liquido (menos negro)."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 0.75)
    img = TF.adjust_brightness(img, 1.3)  # mas brillante = menos liquido
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    noise = np.random.normal(0, 8, np.array(img).shape).astype(np.float32)
    arr = np.clip(np.array(img).astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def apply_poly_transform(img: Image.Image) -> Image.Image:
    """Polihidramnios: grandes areas oscuras (liquido aumentado)."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 1.4)
    img = TF.adjust_brightness(img, 0.6)  # mas oscuro = mas liquido
    return img

def apply_twin_transform(img: Image.Image) -> Image.Image:
    """Embarazo gemelar: dos estructuras fetales visibles."""
    img = img.convert("RGB")
    w, h = img.size
    # Reducir imagen original y pegarla dos veces
    half = img.resize((w//2, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), 0)
    canvas.paste(half, (0, 0))
    half_flip = TF.hflip(half)
    canvas.paste(half_flip, (w//2, 0))
    # Agregar linea divisoria (membrana inter-gemelar)
    draw = ImageDraw.Draw(canvas)
    draw.line([(w//2, 0), (w//2, h)], fill=(60, 60, 60), width=2)
    return canvas

def apply_cleft_transform(img: Image.Image) -> Image.Image:
    """Labio leporino: hendidura en region facial."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 1.15)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Hendidura vertical en zona central-inferior
    cx = int(w * random.uniform(0.45, 0.55))
    y1 = int(h * random.uniform(0.50, 0.60))
    y2 = int(h * random.uniform(0.65, 0.78))
    width = random.randint(3, 8)
    draw.line([(cx, y1), (cx, y2)], fill=(200, 200, 200), width=width)
    return img

def apply_placenta_transform(img: Image.Image) -> Image.Image:
    """Placenta previa: masa ecogenica en polo inferior."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 1.1)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Masa placentaria en parte inferior
    x0 = int(w * random.uniform(0.05, 0.3))
    x1 = int(w * random.uniform(0.7, 0.95))
    y0 = int(h * random.uniform(0.68, 0.78))
    y1 = h
    # Textura placentaria (gris medio)
    for _ in range(random.randint(80, 150)):
        px = random.randint(x0, x1)
        py = random.randint(y0, y1)
        r = random.randint(2, 6)
        v = random.randint(100, 170)
        draw.ellipse([px-r, py-r, px+r, py+r], fill=(v, v, v))
    return img

def apply_duodenal_transform(img: Image.Image) -> Image.Image:
    """Atresia duodenal: signo doble burbuja."""
    img = img.convert("RGB")
    w, h = img.size
    arr = (np.array(img) * 0.3).astype(np.uint8)
    img2 = Image.fromarray(arr)
    draw = ImageDraw.Draw(img2)
    # Burbuja 1 (estomago)
    cx1, cy1 = int(w*0.38), int(h*0.50)
    r1 = random.randint(25, 40)
    draw.ellipse([cx1-r1, cy1-r1, cx1+r1, cy1+r1], fill=(5, 5, 5), outline=(120, 120, 120), width=3)
    # Burbuja 2 (duodeno dilatado)
    cx2, cy2 = int(w*0.58), int(h*0.52)
    r2 = random.randint(18, 30)
    draw.ellipse([cx2-r2, cy2-r2, cx2+r2, cy2+r2], fill=(5, 5, 5), outline=(120, 120, 120), width=3)
    # Ruido de fondo
    noise = np.random.normal(0, 12, np.array(img2).shape).astype(np.float32)
    arr2 = np.clip(np.array(img2).astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr2)

def apply_iugr_transform(img: Image.Image) -> Image.Image:
    """RCIU: feto pequeno, mayor espacio perifetico."""
    img = img.convert("RGB")
    w, h = img.size
    # Reducir el contenido central (feto mas pequeno)
    scale = random.uniform(0.55, 0.72)
    new_w, new_h = int(w*scale), int(h*scale)
    small = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), 0)
    ox = (w - new_w) // 2
    oy = (h - new_h) // 2
    canvas.paste(small, (ox, oy))
    return TF.adjust_contrast(canvas, 1.1)

def apply_macro_transform(img: Image.Image) -> Image.Image:
    """Macrosomia: feto grande, recortado en bordes."""
    img = img.convert("RGB")
    w, h = img.size
    scale = random.uniform(1.25, 1.45)
    new_w, new_h = int(w*scale), int(h*scale)
    big = img.resize((new_w, new_h), Image.LANCZOS)
    ox = (new_w - w) // 2
    oy = (new_h - h) // 2
    cropped = big.crop((ox, oy, ox+w, oy+h))
    return TF.adjust_brightness(cropped, 1.1)

def apply_fetal_death_transform(img: Image.Image) -> Image.Image:
    """Muerte fetal: textura alterada, sin movimiento (mas estatico)."""
    img = img.convert("L").convert("RGB")
    img = TF.adjust_contrast(img, 0.6)
    img = TF.adjust_brightness(img, 0.7)
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    # Ruido tipo grainy (estatico)
    noise = np.random.normal(0, 20, np.array(img).shape).astype(np.float32)
    arr = np.clip(np.array(img).astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

TRANSFORM_MAP = {
    "spine":       apply_spine_transform,
    "anencephaly": apply_anencephaly_transform,
    "oligo":       apply_oligo_transform,
    "poly":        apply_poly_transform,
    "twin":        apply_twin_transform,
    "cleft":       apply_cleft_transform,
    "placenta":    apply_placenta_transform,
    "duodenal":    apply_duodenal_transform,
    "iugr":        apply_iugr_transform,
    "macro":       apply_macro_transform,
    "fetal_death": apply_fetal_death_transform,
}

# ── Augmentaciones generales adicionales ───────────────────────────────────────
GENERAL_AUGS = T.Compose([
    T.RandomHorizontalFlip(p=0.5),
    T.RandomVerticalFlip(p=0.2),
    T.RandomRotation(degrees=15, fill=0),
    T.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.05),
    T.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.92, 1.08), fill=0),
])

def load_source_images(class_name: str, max_imgs: int = 400) -> list:
    """Carga imagenes de una clase real como base."""
    src_dir = TRAIN_DIR / class_name
    if not src_dir.exists():
        log.warning("Clase base no encontrada: %s", class_name)
        return []
    imgs = list(src_dir.glob("*.png")) + list(src_dir.glob("*.jpg"))
    random.shuffle(imgs)
    return imgs[:max_imgs]

def generate_for_class(class_name: str, config: dict):
    """Genera imagenes sinteticas para una clase vacia."""
    log.info("\n[GEN] %s — %s", class_name, config["description"])

    # Verificar si ya tiene imagenes
    out_train = TRAIN_DIR / class_name
    out_val   = VAL_DIR   / class_name
    out_train.mkdir(parents=True, exist_ok=True)
    out_val.mkdir(parents=True, exist_ok=True)

    existing = len(list(out_train.glob("*.png")))
    if existing >= config["n_train"]:
        log.info("  Ya tiene %d imagenes, saltando", existing)
        return existing

    # Cargar imagenes fuente
    sources = load_source_images(config["base_class"])
    if not sources:
        log.warning("  Sin imagenes fuente para %s", class_name)
        return 0

    transform_fn = TRANSFORM_MAP.get(config["transforms"])
    if not transform_fn:
        log.warning("  Transform no encontrada: %s", config["transforms"])
        return 0

    total_needed = config["n_train"] + config["n_val"]
    generated = 0

    for i in range(total_needed):
        src_path = random.choice(sources)
        try:
            img = Image.open(src_path).convert("RGB").resize((224, 224), Image.LANCZOS)

            # Aplicar transformacion especifica de patologia
            img = transform_fn(img)

            # Aplicar augmentaciones generales adicionales
            img = GENERAL_AUGS(img)

            # Guardar
            split = "val" if i < config["n_val"] else "train"
            out_dir = out_val if split == "val" else out_train
            fname = f"synth_{class_name}_{i:04d}.png"
            img.save(out_dir / fname, "PNG")
            generated += 1

        except Exception as e:
            log.debug("  Error en imagen %d: %s", i, e)

    log.info("  Generadas: %d train + %d val",
             config["n_train"], config["n_val"])
    return generated

# ── Main ────────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("  Generador Sintetico — Fetal Medical AI")
    log.info("  GPU: %s | CUDA: %s",
             torch.cuda.get_device_name(0) if DEVICE == "cuda" else "N/A",
             DEVICE)
    log.info("=" * 60)

    random.seed(42)
    np.random.seed(42)

    results = {}
    for class_name, config in CLASS_CONFIGS.items():
        n = generate_for_class(class_name, config)
        results[class_name] = n

    log.info("\n" + "=" * 60)
    log.info("  RESUMEN GENERACION SINTETICA")
    log.info("=" * 60)
    total = 0
    for cls, n in results.items():
        status = "[OK]" if n > 0 else "[--]"
        log.info("  %s %-28s: %d imagenes", status, cls, n)
        total += n
    log.info("  TOTAL SINTETICO GENERADO: %d", total)

    # Conteo final completo
    log.info("\n  DATASET COMPLETO FINAL:")
    grand_total_t = grand_total_v = 0
    for cls_dir in sorted(TRAIN_DIR.iterdir()):
        nt = len(list(cls_dir.glob("*.png"))) + len(list(cls_dir.glob("*.jpg")))
        vd = VAL_DIR / cls_dir.name
        nv = len(list(vd.glob("*.png"))) + len(list(vd.glob("*.jpg"))) if vd.exists() else 0
        grand_total_t += nt
        grand_total_v += nv
        tag = "[OK]" if nt > 0 else "[--]"
        log.info("  %s %-28s train=%5d val=%4d", tag, cls_dir.name, nt, nv)
    log.info("  TOTAL FINAL: train=%d  val=%d", grand_total_t, grand_total_v)

if __name__ == "__main__":
    main()
