# -*- coding: utf-8 -*-
"""
Descarga imagenes de Radiopaedia usando su API JSON interna.
Radiopaedia carga resultados via AJAX - usamos el endpoint directamente.
"""
import json
import re
import time
import logging
import sys
import os
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("radiopaedia")

BASE_DIR  = Path(__file__).resolve().parent.parent
TRAIN_DIR = BASE_DIR / "datasets_pathology" / "train"
VAL_DIR   = BASE_DIR / "datasets_pathology" / "validation"

# Mapeo clase -> terminos de busqueda en Radiopaedia
SEARCHES = {
    "labio_leporino":    ["cleft lip fetal", "cleft palate fetal ultrasound"],
    "placenta_previa":   ["placenta previa", "low lying placenta"],
    "oligohidramnios":   ["oligohydramnios", "reduced amniotic fluid"],
    "polihidramnios":    ["polyhydramnios", "polyhydramnios ultrasound"],
    "espina_bifida":     ["spina bifida", "myelomeningocele fetal"],
    "anencefalia":       ["anencephaly", "anencephalic fetus"],
    "embarazo_multiple": ["twin pregnancy", "dichorionic diamniotic"],
    "atresia_duodenal":  ["duodenal atresia", "double bubble sign fetus"],
}

MAX_PER_CLASS = 40
VAL_RATIO = 0.20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://radiopaedia.org/",
    "X-Requested-With": "XMLHttpRequest",
}


def search_radiopaedia_api(session, query, page=1):
    """
    Usa el endpoint JSON de Radiopaedia para buscar casos.
    """
    # Endpoint de busqueda JSON interno de Radiopaedia
    api_url = "https://radiopaedia.org/search.json"
    params = {
        "q": query,
        "scope": "cases",
        "lang": "us",
        "page": page,
    }
    try:
        r = session.get(api_url, params=params, timeout=20)
        log.info("    API response: HTTP %d", r.status_code)
        if r.status_code == 200:
            try:
                data = r.json()
                return data
            except Exception:
                log.debug("    No es JSON valido")
        return None
    except Exception as e:
        log.warning("    Error en API: %s", e)
        return None


def get_case_images(session, case_url):
    """
    Obtiene las imagenes de un caso clinico especifico.
    Usa el endpoint JSON del caso.
    """
    # Extraer ID del caso de la URL
    case_id_match = re.search(r"/cases/(\d+)", case_url)
    if not case_id_match:
        return []

    case_id = case_id_match.group(1)

    # API JSON del caso
    api_url = f"https://radiopaedia.org/cases/{case_id}.json"
    try:
        r = session.get(api_url, timeout=20)
        if r.status_code == 200:
            try:
                data = r.json()
                imgs = []
                # Buscar imagenes en la respuesta JSON
                text = json.dumps(data)
                urls = re.findall(
                    r'https://prod-images-static\.radiopaedia\.org/[^\s"\']+\.(:jpg|jpeg|png|webp)',
                    text
                )
                imgs.extend(urls)
                return list(set(imgs))
            except Exception:
                pass
    except Exception:
        pass

    # Fallback: buscar en HTML del caso
    try:
        r = session.get(case_url, timeout=20)
        if r.status_code == 200:
            urls = re.findall(
                r'https://prod-images-static\.radiopaedia\.org/[^\s"\'<>]+\.(:jpg|jpeg|png|webp)',
                r.text
            )
            # Tambien buscar thumbnails
            thumbs = re.findall(
                r'"(https://[^"]+radiopaedia[^"]+(:jpg|png|jpeg))"',
                r.text
            )
            return list(set(urls + thumbs))
    except Exception:
        pass

    return []


def download_image(session, img_url, dest_path):
    """Descarga una imagen."""
    if dest_path.exists():
        return True
    try:
        r = session.get(img_url, timeout=30)
        if r.status_code == 200 and len(r.content) > 3000:
            # Verificar que es imagen real (magic bytes)
            magic = r.content[:4]
            is_img = (
                magic[:2] == b'\xff\xd8' or   # JPEG
                magic[:4] == b'\x89PNG' or    # PNG
                magic[:4] == b'RIFF'          # WebP
            )
            if is_img:
                with open(dest_path, "wb") as f:
                    f.write(r.content)
                return True
    except Exception as e:
        log.debug("    Error: %s", e)
    return False


def scrape_class(session, class_name, queries):
    """Descarga imagenes para una clase usando multiples queries."""
    log.info("\n[CLASS] %s", class_name)

    train_dir = TRAIN_DIR / class_name
    val_dir   = VAL_DIR   / class_name
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    existing_t = len(list(train_dir.glob("*.jpg"))) + len(list(train_dir.glob("*.png")))
    existing_v = len(list(val_dir.glob("*.jpg"))) + len(list(val_dir.glob("*.png")))
    existing = existing_t + existing_v

    if existing >= MAX_PER_CLASS:
        log.info("  Ya tiene %d imagenes, saltando", existing)
        return existing

    downloaded = 0
    img_counter = existing

    for query in queries:
        if downloaded >= MAX_PER_CLASS:
            break

        log.info("  Query: '%s'", query)

        # Probar API JSON
        data = search_radiopaedia_api(session, query)

        case_urls = []
        if data:
            text = json.dumps(data)
            # Extraer URLs de casos del JSON
            found = re.findall(r'https://radiopaedia\.org/cases/\d+[^"\']*', text)
            found += re.findall(r'/cases/\d+[^"\']*', text)
            for u in found:
                if not u.startswith("http"):
                    u = "https://radiopaedia.org" + u
                if u not in case_urls:
                    case_urls.append(u)

        # Si no hay resultados JSON, buscar en pagina HTML
        if not case_urls:
            try:
                url = f"https://radiopaedia.org/searchq={query.replace(' ','+')}&scope=cases&lang=us"
                r = session.get(url, timeout=20)
                if r.status_code == 200:
                    found = re.findall(r'href="(/cases/\d+[^"]*)"', r.text)
                    case_urls = [f"https://radiopaedia.org{u}" for u in found[:15]]
            except Exception:
                pass

        log.info("  Casos encontrados: %d", len(case_urls))

        for case_url in case_urls[:15]:
            if downloaded >= MAX_PER_CLASS:
                break

            imgs = get_case_images(session, case_url)
            if not imgs:
                continue

            for img_url in imgs[:2]:
                if downloaded >= MAX_PER_CLASS:
                    break

                ext = ".png" if ".png" in img_url.lower() else ".jpg"

                # 80/20 split
                if img_counter % 5 == 0:
                    dest = val_dir / f"rad_{class_name}_{img_counter:04d}{ext}"
                else:
                    dest = train_dir / f"rad_{class_name}_{img_counter:04d}{ext}"

                ok = download_image(session, img_url, dest)
                if ok:
                    downloaded += 1
                    img_counter += 1
                    log.info("    [+] %s (total: %d)", dest.name, downloaded)

            time.sleep(0.5)

    log.info("  Descargadas para %s: %d", class_name, downloaded)
    return downloaded


def main():
    log.info("=" * 65)
    log.info("  Radiopaedia Scraper v2 -- Fetal Medical AI")
    log.info("=" * 65)

    session = requests.Session()
    session.headers.update(HEADERS)

    # Test conexion
    try:
        r = session.get("https://radiopaedia.org", timeout=10)
        log.info("  Conexion: OK (HTTP %d)", r.status_code)
    except Exception as e:
        log.error("  Sin conexion: %s", e)
        return

    results = {}
    for class_name, queries in SEARCHES.items():
        n = scrape_class(session, class_name, queries)
        results[class_name] = n

    log.info("\n" + "=" * 65)
    log.info("  RESUMEN FINAL -- Radiopaedia")
    log.info("=" * 65)
    total = 0
    for cls, n in results.items():
        status = "[OK]" if n > 0 else "[NO]"
        log.info("  %s %-28s: %d imagenes", status, cls, n)
        total += n
    log.info("  TOTAL: %d imagenes descargadas de Radiopaedia", total)

    if total == 0:
        log.info("")
        log.info("  Radiopaedia require JavaScript para mostrar resultados.")
        log.info("  Descarga manual: abre el navegador, ve a radiopaedia.org")
        log.info("  y descarga cada imagen a datasets_pathology/train/[clase]/")


if __name__ == "__main__":
    main()
