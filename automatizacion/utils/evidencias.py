"""Evidencias de ejecución con código EV: capturas, registro de consola y HTML de la página.

Nombre de cada captura: EV-<TC>-<paso>-<marca de tiempo>.png, en reports/<run_id>/evidencias/.
Cada evidencia se registra en la lista del caso para que los reportes la muestren junto a su resultado.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from utils import config

RUN_ID = os.environ.get("QA_RUN_ID") or datetime.now().strftime("%Y%m%d-%H%M%S")
os.environ["QA_RUN_ID"] = RUN_ID
DIR_RUN = config.RAIZ / "reports" / RUN_ID
DIR_EV = DIR_RUN / "evidencias"

# evidencias del caso en curso: el conftest las vacía al empezar cada prueba y las guarda en el resultado
REGISTRO: list[dict] = []
CASO_ACTUAL = {"tc": "SIN-TC"}


def _limpio(t: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", t)[:40]


def captura(driver, paso: str, descripcion: str = "") -> str:
    """Guarda una captura del navegador y la registra como evidencia del caso en curso."""
    DIR_EV.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    nombre = f"EV-{_limpio(CASO_ACTUAL['tc'])}-{_limpio(paso)}-{marca}.png"
    ruta = DIR_EV / nombre
    try:
        driver.save_screenshot(str(ruta))
    except Exception:
        return ""
    REGISTRO.append({"codigo": nombre[:-4], "archivo": str(ruta.relative_to(DIR_RUN)).replace("\\", "/"),
                     "paso": paso, "descripcion": descripcion or paso, "url": _url(driver), "hora": marca})
    return str(ruta)


def volcado_fallo(driver, paso: str = "fallo") -> dict:
    """Al fallar un caso: captura, consola del navegador y HTML recortado de la página."""
    from utils.driver_factory import consola
    salida = {"captura": captura(driver, paso, "Estado de la pantalla al fallar")}
    DIR_EV.mkdir(parents=True, exist_ok=True)
    base = DIR_EV / f"EV-{_limpio(CASO_ACTUAL['tc'])}-{paso}"
    try:
        log = consola(driver)
        Path(f"{base}-consola.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        salida["consola"] = log[-20:]
    except Exception:
        salida["consola"] = []
    try:
        html = driver.page_source
        Path(f"{base}.html").write_text(html, encoding="utf-8")
        salida["html"] = re.sub(r"\s+", " ", re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S))[:4000]
    except Exception:
        salida["html"] = ""
    return salida


def _url(driver) -> str:
    try:
        return driver.current_url
    except Exception:
        return ""


def captura_texto(lineas: list[str], paso: str, descripcion: str = "", ancho: int = 118) -> str:
    """Evidencia de una ejecución sin navegador propio (Selenium IDE, Locust): su salida como imagen EV."""
    import textwrap

    from PIL import Image, ImageDraw, ImageFont
    try:
        fuente = ImageFont.truetype("consola.ttf", 16)
    except OSError:
        fuente = ImageFont.load_default()
    filas = []
    for linea in lineas:
        filas += textwrap.wrap(linea.rstrip(), ancho, subsequent_indent="    ") or [""]
    alto = 22
    img = Image.new("RGB", (int(fuente.getlength("M" * ancho)) + 40, alto * len(filas) + 36), "#0F1718")
    d = ImageDraw.Draw(img)
    for i, fila in enumerate(filas):
        color = "#D6E4E4"
        if "PASS" in fila or "✓" in fila or " passed" in fila:
            color = "#5FD39A"
        if "FAIL" in fila or "×" in fila or " failed" in fila or "Error" in fila:
            color = "#FF8A80"
        d.text((20, 18 + i * alto), fila, font=fuente, fill=color)
    DIR_EV.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    nombre = f"EV-{_limpio(CASO_ACTUAL['tc'])}-{_limpio(paso)}-{marca}.png"
    img.save(DIR_EV / nombre)
    REGISTRO.append({"codigo": nombre[:-4], "archivo": f"evidencias/{nombre}", "paso": paso, "descripcion": descripcion,
                     "url": "", "hora": marca})
    return nombre
