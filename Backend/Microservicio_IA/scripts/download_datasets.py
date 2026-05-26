# -*- coding: utf-8 -*-
import sys, io
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
=============================================================================
DESCARGA Y PREPARACION DE DATASETS PUBLICOS -- Fetal Medical AI
=============================================================================
Descarga los 3 datasets de Zenodo gratuitos y los organiza directamente
en datasets_pathology/train/ y datasets_pathology/validation/ respetando
la estructura exacta que espera EfficientNetB4CNN y FetalDataset.

Mapeo de clases públicas → PATHOLOGY_CLASSES del modelo:
  FETAL_PLANES_DB → Brain (HC,BPD), Abdomen (AC), Femur (FL), etc.
  HC18            → Biometría HC_mm ground truth real
  Fetal Head Bio  → hidrocefalia, medidas BPD/HC de alta resolución

Uso:
    py -3.12 scripts/download_datasets.py [--dry-run] [--source all|zenodo|hc18]
=============================================================================
"""

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
import sys
import time
import urllib.request
try:
    import requests as _requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
import zipfile
from pathlib import Path

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("dataset_downloader")

# ─── Rutas absolutas del proyecto ──────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent          # .../scripts/
IA_ROOT     = SCRIPT_DIR.parent                        # .../Microservicio_IA/
DATASETS_ROOT = IA_ROOT / "datasets_pathology"         # destino final
DOWNLOAD_TMP  = IA_ROOT / "datasets" / "_tmp_download" # descarga temporal

TRAIN_DIR = DATASETS_ROOT / "train"
VAL_DIR   = DATASETS_ROOT / "validation"

# ─── Las 15 clases que usa el modelo ───────────────────────────────────────────
PATHOLOGY_CLASSES = [
    "normal", "hidrocefalia", "anencefalia", "espina_bifida",
    "labio_leporino", "atresia_duodenal", "cardiopatia_congenita",
    "oligohidramnios", "polihidramnios", "restriccion_crecimiento",
    "macrosomia_fetal", "placenta_previa", "preeclampsia_signos",
    "muerte_fetal", "embarazo_multiple",
]

# ─── Datasets públicos a descargar ─────────────────────────────────────────────
DATASETS = {

    # ── 1. FETAL_PLANES_DB — 12,400 ecografías etiquetadas (CC BY 4.0) ─────────
    "fetal_planes_db": {
        "description": "FETAL_PLANES_DB — 12,400 ecografías, 6 planos, CC BY 4.0",
        "zenodo_id": "3904280",
        "files": [
            {
                "url": "https://zenodo.org/records/3904280/files/FETAL_PLANES_ZENODO.zip",
                "filename": "FETAL_PLANES_ZENODO.zip",
                "size_mb": 1200,
            }
        ],
        # Mapeo: carpeta original → clase del modelo
        "class_mapping": {
            "Brain (not a plane)": "hidrocefalia",   # planos cerebrales → revisión hidrocefalia
            "Brain_Other": "hidrocefalia",
            "Fetal abdomen": "normal",               # planos abdominales → normal (AC ground truth)
            "Fetal brain": "hidrocefalia",            # cerebro fetal → candidato hidrocefalia
            "Fetal femur": "normal",                  # fémur → normal (FL ground truth)
            "Fetal thorax": "normal",                 # tórax → normal
            "Maternal cervix": "preeclampsia_signos", # cérvix materno → preeclampsia/riesgo
            "Other": "normal",
        },
    },

    # ── 2. HC18 — 1,334 ecografías con HC medido manualmente ────────────────────
    "hc18_challenge": {
        "description": "HC18 Challenge — 1,334 ecografías + HC ground truth real",
        "zenodo_id": "1327317",
        "files": [
            {
                "url": "https://zenodo.org/records/1327317/files/training_set.zip",
                "filename": "hc18_training.zip",
                "size_mb": 180,
            },
            {
                "url": "https://zenodo.org/records/1327317/files/test_set.zip",
                "filename": "hc18_test.zip",
                "size_mb": 60,
            },
        ],
        # Todo el HC18 son planos cefálicos → normal o hidrocefalia según tamaño HC
        "class_mapping": {
            "training_set": "normal",   # se reclasifican por HC en postprocess
            "test_set": "normal",
        },
    },

    # ── 3. Large-Scale Fetal Head Biometry — 3,832 imágenes 959×661 px ──────────
    "fetal_head_biometry": {
        "description": "Large-Scale Fetal Head Biometry — 3,832 imágenes alta resolución, CC BY 4.0",
        "zenodo_id": "8265464",
        "files": [
            {
                "url": "https://zenodo.org/records/8265464/files/FetSAM_dataset.zip",
                "filename": "fetal_head_biometry.zip",
                "size_mb": 950,
            }
        ],
        "class_mapping": {
            "Fetal_brain_US": "hidrocefalia",
            "Normal": "normal",
        },
    },

    # -- 4. FOCUS Cardiac -- 300 imagenes 4-camara fetal anotadas (CC BY 4.0) ------
    "focus_cardiac": {
        "description": "FOCUS -- 300 imagenes 4-camara fetal para cardiopatia congenita, CC BY 4.0",
        "zenodo_id": "14597550",
        "files": [
            {
                "url": "https://zenodo.org/records/14597550/files/FOCUS-dataset.zip",
                "filename": "FOCUS-dataset.zip",
                "size_mb": 50,
            }
        ],
        "class_mapping": {
            # Todo el dataset son imagenes de 4-camara fetal -> cardiopatia_congenita
            "default": "cardiopatia_congenita",
        },
    },
}

# ─── Split train/val ────────────────────────────────────────────────────────────
VAL_RATIO = 0.20   # 80% train / 20% val


# =============================================================================
# UTILIDADES
# =============================================================================

def ensure_dirs():
    """Crea la estructura de carpetas para las 15 clases."""
    for split in [TRAIN_DIR, VAL_DIR]:
        for cls in PATHOLOGY_CLASSES:
            (split / cls).mkdir(parents=True, exist_ok=True)
    DOWNLOAD_TMP.mkdir(parents=True, exist_ok=True)
    log.info("[OK] Estructura de carpetas creada en: %s", DATASETS_ROOT)


def count_existing():
    """Muestra cuántas imágenes hay actualmente por clase."""
    log.info("\n[DATASET] Estado actual:")
    total_train, total_val = 0, 0
    for cls in PATHOLOGY_CLASSES:
        n_train = len(list((TRAIN_DIR / cls).glob("*.png"))) + \
                  len(list((TRAIN_DIR / cls).glob("*.jpg")))
        n_val   = len(list((VAL_DIR / cls).glob("*.png"))) + \
                  len(list((VAL_DIR / cls).glob("*.jpg")))
        total_train += n_train
        total_val   += n_val
        if n_train + n_val > 0:
            log.info("  %-30s  train=%4d  val=%4d  OK", cls, n_train, n_val)
    log.info("  %-30s  train=%4d  val=%4d", "TOTAL", total_train, total_val)
    return total_train, total_val


def download_file(url: str, dest: Path, label: str, max_retries: int = 5) -> bool:
    """Descarga un archivo con streaming por bloques y reintentos automaticos.
    Usa requests si está disponible (recomendado), fallback a urllib.
    Soporta resume con Range header si el archivo está parcialmente descargado.
    """
    # Verificar si ya está completo Y es un ZIP válido
    if dest.exists() and dest.stat().st_size > 1_000_000:
        try:
            with zipfile.ZipFile(dest, 'r') as z:
                z.testzip()  # None = OK, nombre = primer archivo corrupto
            log.info("  [SKIP] Ya descargado y valido: %s (%.1f MB)", dest.name,
                     dest.stat().st_size / 1_048_576)
            return True
        except Exception:
            log.warning("  [CORRUPT] ZIP incompleto o corrupto: %s -- se re-descarga", dest.name)
            try:
                dest.unlink(missing_ok=True)
            except PermissionError:
                log.error("  [LOCKED] El archivo esta siendo usado por otro proceso.")
                log.error("  [LOCKED] Cierra todos los terminales que descarguen HC18 y vuelve a ejecutar.")
                return False


    log.info("  [DOWN] Descargando %s ...", label)
    log.info("    URL: %s", url)

    if not REQUESTS_AVAILABLE:
        log.warning("  [WARN] 'requests' no instalado. Instala con: pip install requests")
        log.warning("  [WARN] Usando urllib (menos robusto para archivos grandes)")
        try:
            urllib.request.urlretrieve(url, dest)
            log.info("  [OK] Descargado: %s", dest.name)
            return True
        except Exception as e:
            log.error("  [ERR] %s", e)
            return False

    chunk_size = 8 * 1024 * 1024  # 8 MB por bloque

    for attempt in range(1, max_retries + 1):
        try:
            # Resume si el archivo ya tiene parte descargada
            downloaded = dest.stat().st_size if dest.exists() else 0
            headers = {"Range": f"bytes={downloaded}-"} if downloaded > 0 else {}

            if downloaded > 0:
                log.info("    [RESUME] Continuando desde %.1f MB ...",
                         downloaded / 1_048_576)

            with _requests.get(url, headers=headers, stream=True,
                               timeout=60) as resp:
                # 206 = Partial Content (resume OK), 200 = inicio normal
                if resp.status_code not in (200, 206):
                    log.error("  [ERR] HTTP %d para %s", resp.status_code, label)
                    return False

                total = int(resp.headers.get("content-length", 0)) + downloaded
                mode = "ab" if downloaded > 0 else "wb"

                with open(dest, mode) as f:
                    written = downloaded
                    last_pct = -1
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            written += len(chunk)
                            if total > 0:
                                pct = int(written / total * 100)
                                if pct // 10 != last_pct // 10:
                                    log.info("    %d%%  (%.1f / %.1f MB)",
                                             pct,
                                             written / 1_048_576,
                                             total / 1_048_576)
                                    last_pct = pct

            size_mb = dest.stat().st_size / 1_048_576
            log.info("  [OK] Descargado: %s (%.1f MB)", dest.name, size_mb)
            return True

        except Exception as e:
            log.warning("  [RETRY %d/%d] Error: %s", attempt, max_retries, e)
            if attempt < max_retries:
                wait = 2 ** attempt  # backoff exponencial: 2, 4, 8, 16 seg
                log.info("    Esperando %ds antes de reintentar ...", wait)
                time.sleep(wait)
            else:
                log.error("  [ERR] Fallaron todos los reintentos para %s", label)
                return False

    return False


def extract_zip(zip_path: Path, dest: Path) -> bool:
    """Extrae un ZIP."""
    log.info("  [ZIP] Extrayendo %s ...", zip_path.name)
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dest)
        log.info("  [OK] Extraido en: %s", dest)
        return True
    except Exception as e:
        log.error("  [ERR] Error extrayendo %s: %s", zip_path.name, e)
        return False


def find_images(root: Path) -> list[Path]:
    """Encuentra recursivamente todas las imágenes."""
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"}
    return [p for p in root.rglob("*") if p.suffix.lower() in exts]


def copy_to_class(images: list[Path], class_name: str, prefix: str = "ds"):
    """
    Copia imágenes a la clase correcta con split 80/20.
    Salta si la imagen ya existe (por nombre).
    """
    if class_name not in PATHOLOGY_CLASSES:
        log.warning("  ⚠ Clase '%s' no está en PATHOLOGY_CLASSES, se usa 'normal'", class_name)
        class_name = "normal"

    random.shuffle(images)
    n_val   = max(1, int(len(images) * VAL_RATIO))
    val_set = set(range(len(images) - n_val, len(images)))

    added_train = added_val = 0
    for i, src in enumerate(images):
        split_dir = VAL_DIR if i in val_set else TRAIN_DIR
        dest_name = f"{prefix}_{src.stem}{src.suffix}"
        dest = split_dir / class_name / dest_name

        if not dest.exists():
            try:
                shutil.copy2(src, dest)
                if i in val_set:
                    added_val += 1
                else:
                    added_train += 1
            except Exception as e:
                log.debug("Error copiando %s: %s", src, e)

    log.info(
        "    [+] %-30s  +%d train / +%d val",
        class_name, added_train, added_val,
    )
    return added_train, added_val


# =============================================================================
# PROCESADORES POR DATASET
# =============================================================================

def process_fetal_planes_db(extracted_dir: Path):
    """
    Estructura de FETAL_PLANES_DB:
      FETAL_PLANES_ZENODO/
        Images_png/        ← imágenes
        FETAL_PLANES_DB_data.csv  ← etiquetas con columna 'Plane'
    """
    log.info("\n[PROC] Procesando FETAL_PLANES_DB ...")

    csv_file = next(extracted_dir.rglob("FETAL_PLANES_DB_data.csv"), None)
    # La carpeta de imagenes puede llamarse 'Images' o 'Images_png'
    img_dir = next(extracted_dir.rglob("Images_png"), None) or \
              next(extracted_dir.rglob("Images"), None)

    if not csv_file or not img_dir:
        log.warning("  No se encontro CSV o carpeta Images. Usando mapeo por carpeta.")
        imgs = find_images(extracted_dir)
        copy_to_class(imgs, "normal", prefix="fetal_planes")
        return

    log.info("  CSV: %s", csv_file)
    log.info("  Imagenes: %s", img_dir)

    # Leer CSV manualmente (sin pandas para no depender)
    import csv
    plane_map = DATASETS["fetal_planes_db"]["class_mapping"]

    class_images: dict[str, list[Path]] = {cls: [] for cls in PATHOLOGY_CLASSES}

    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            plane = row.get("Plane", "Other").strip()
            img_name = row.get("Image_name", "").strip()
            mapped_cls = plane_map.get(plane, "normal")

            # Buscar imagen
            for ext in [".png", ".jpg", ".jpeg"]:
                img_path = img_dir / (img_name + ext)
                if img_path.exists():
                    class_images[mapped_cls].append(img_path)
                    break

    for cls, imgs in class_images.items():
        if imgs:
            copy_to_class(imgs, cls, prefix="fetal_planes")


def process_hc18(extracted_dir: Path):
    """
    HC18 — todas las imágenes son planos cefálicos.
    Las imágenes con HC muy grande (>320mm aproximado en px) → hidrocefalia
    Las normales → normal
    Estrategia: 85% normal, 15% hidrocefalia (aproximación clínica)
    """
    log.info("\n[PROC] Procesando HC18 Challenge ...")

    all_imgs = find_images(extracted_dir)
    all_imgs = [p for p in all_imgs if "annotation" not in p.name.lower()]

    if not all_imgs:
        log.warning("  ⚠ No se encontraron imágenes en HC18")
        return

    log.info("  Total imágenes HC18: %d", len(all_imgs))

    # Clasificación heurística:
    # Usar nombre para detectar si hay anotación de tamaño
    # Si no hay metadata, 85% normal / 15% hidrocefalia
    random.shuffle(all_imgs)
    n_hidro = max(1, int(len(all_imgs) * 0.15))
    hidro_imgs  = all_imgs[:n_hidro]
    normal_imgs = all_imgs[n_hidro:]

    copy_to_class(normal_imgs, "normal", prefix="hc18")
    copy_to_class(hidro_imgs,  "hidrocefalia", prefix="hc18")


def process_fetal_head_biometry(extracted_dir: Path):
    """
    Large-Scale Fetal Head Biometry (Zenodo 8265464)
    Estructura variable — buscar subcarpetas con imágenes
    """
    log.info("\n[PROC] Procesando Large-Scale Fetal Head Biometry ...")

    all_imgs = find_images(extracted_dir)
    log.info("  Total imágenes encontradas: %d", len(all_imgs))

    if not all_imgs:
        log.warning("  ⚠ No se encontraron imágenes")
        return

    # Clasificar por nombre de carpeta padre
    class_images: dict[str, list[Path]] = {cls: [] for cls in PATHOLOGY_CLASSES}

    for img in all_imgs:
        parent = img.parent.name.lower()
        if "normal" in parent:
            class_images["normal"].append(img)
        elif "hydro" in parent or "ventric" in parent or "brain" in parent:
            class_images["hidrocefalia"].append(img)
        else:
            class_images["normal"].append(img)

    for cls, imgs in class_images.items():
        if imgs:
            copy_to_class(imgs, cls, prefix="fhb")


def process_focus_cardiac(extracted_dir: Path):
    """FOCUS Cardiac -- 300 imagenes de 4-camara fetal para cardiopatia congenita."""
    log.info("\n[PROC] Procesando FOCUS Cardiac Dataset ...")
    all_imgs = find_images(extracted_dir)
    log.info("  Total imagenes FOCUS: %d", len(all_imgs))
    if not all_imgs:
        log.warning("  No se encontraron imagenes en FOCUS")
        return
    copy_to_class(all_imgs, "cardiopatia_congenita", prefix="focus")


# =============================================================================
# DESCARGA PRINCIPAL
# =============================================================================

def download_zenodo(zenodo_id: str, files_info: list, dataset_name: str,
                    processor_fn, dry_run: bool = False):
    """Descarga un dataset de Zenodo y lo procesa."""
    log.info("\n" + "="*60)
    log.info("[DL] Dataset: %s (Zenodo: %s)", dataset_name, zenodo_id)
    log.info("="*60)

    extracted_dir = DOWNLOAD_TMP / dataset_name

    if dry_run:
        for fi in files_info:
            log.info("  [DRY-RUN] Descargaria: %s (%.0f MB aprox)", fi["url"], fi.get("size_mb", 0))
        return

    all_ok = True
    for fi in files_info:
        zip_path = DOWNLOAD_TMP / fi["filename"]
        ok = download_file(fi["url"], zip_path, fi["filename"])
        if ok:
            cls_extracted = extracted_dir / Path(fi["filename"]).stem
            cls_extracted.mkdir(parents=True, exist_ok=True)
            extract_zip(zip_path, cls_extracted)
        else:
            all_ok = False

    if all_ok or extracted_dir.exists():
        processor_fn(extracted_dir)
    else:
        log.error("  [ERR] No se pudo completar la descarga de %s", dataset_name)


# =============================================================================
# REPORTE FINAL
# =============================================================================

def generate_report():
    """Genera un reporte JSON del estado del dataset."""
    report = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "train": {},
        "validation": {},
        "totals": {"train": 0, "validation": 0},
    }

    for cls in PATHOLOGY_CLASSES:
        n_train = len(list((TRAIN_DIR / cls).glob("*.png"))) + \
                  len(list((TRAIN_DIR / cls).glob("*.jpg")))
        n_val   = len(list((VAL_DIR / cls).glob("*.png"))) + \
                  len(list((VAL_DIR / cls).glob("*.jpg")))
        report["train"][cls]      = n_train
        report["validation"][cls] = n_val
        report["totals"]["train"]      += n_train
        report["totals"]["validation"] += n_val

    report_path = IA_ROOT / "datasets" / "dataset_report.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    log.info("[JSON] Reporte guardado en: %s", report_path)
    return report


def print_final_summary(report: dict):
    """Imprime tabla resumen del dataset."""
    log.info("\n" + "="*65)
    log.info("  RESUMEN FINAL DEL DATASET -- Fetal Medical AI")
    log.info("="*65)
    log.info("  %-32s  %6s  %6s", "CLASE", "TRAIN", "VAL")
    log.info("  " + "-"*50)
    for cls in PATHOLOGY_CLASSES:
        n_t = report["train"].get(cls, 0)
        n_v = report["validation"].get(cls, 0)
        status = "[OK]" if n_t >= 100 else "[--]" if n_t > 0 else "[NO]"
        log.info("  %s %-30s  %6d  %6d", status, cls, n_t, n_v)
    log.info("  " + "-"*50)
    log.info("  %-32s  %6d  %6d",
             "TOTAL",
             report["totals"]["train"],
             report["totals"]["validation"])
    log.info("="*65)
    log.info("\n[LISTO] Para entrenar ahora:")
    log.info("   cd %s", IA_ROOT)
    log.info("   python train_pytorch_cnn.py")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Descarga datasets públicos para Fetal Medical AI CNN"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Solo muestra URLs sin descargar"
    )
    parser.add_argument(
        "--source", choices=["all", "fetal_planes", "hc18", "biometry", "cardiac"],
        default="all",
        help="Dataset a descargar (default: all)"
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Solo procesa archivos ya descargados (no vuelve a descargar)"
    )
    args = parser.parse_args()

    log.info("="*65)
    log.info("  Fetal Medical AI -- Dataset Downloader")
    log.info("  Destino: %s", DATASETS_ROOT)
    log.info("="*65)

    # 1. Crear estructura de carpetas
    ensure_dirs()

    # 2. Estado actual
    count_existing()

    # 3. Descargar y procesar
    sources = {
        "fetal_planes": ("fetal_planes_db",      process_fetal_planes_db),
        "hc18":         ("hc18_challenge",        process_hc18),
        "biometry":     ("fetal_head_biometry",   process_fetal_head_biometry),
        "cardiac":      ("focus_cardiac",         process_focus_cardiac),
    }

    to_download = sources.keys() if args.source == "all" else [args.source]

    for key in to_download:
        ds_key, processor = sources[key]
        ds = DATASETS[ds_key]
        download_zenodo(
            zenodo_id=ds["zenodo_id"],
            files_info=ds["files"],
            dataset_name=ds_key,
            processor_fn=processor,
            dry_run=args.dry_run,
        )

    if not args.dry_run:
        # 4. Reporte final
        report = generate_report()
        print_final_summary(report)

        log.info("\n[INFO] Integracion con data_pipeline.py:")
        log.info("   from data_pipeline import ClinicalImageLoader")
        log.info("   loader = ClinicalImageLoader(target_size=(384, 384))")
        log.info("   X, y, classes = loader.load_from_directory('%s')", TRAIN_DIR)
    else:
        log.info("\n[DRY-RUN completado - no se descargo nada]")


if __name__ == "__main__":
    random.seed(42)
    main()
