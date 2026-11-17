"""Fábrica de navegadores para Selenium WebDriver 4 (Selenium Manager descarga el driver correcto).

Soporta Chrome, Edge y Firefox, modo visible o headless, ventana de 1440x900 y registros de consola.
En Chrome y Edge se habilita además el registro de rendimiento (protocolo DevTools) para leer los códigos
HTTP de cada respuesta que recibe la página: así se detectan errores 4xx/5xx de la API sin un proxy.
"""
from __future__ import annotations

import json

from selenium import webdriver

from utils import config


def crear_driver(navegador: str | None = None, headless: bool | None = None):
    navegador = (navegador or config.NAVEGADOR).lower()
    headless = config.HEADLESS if headless is None else headless
    if navegador in ("chrome", "edge"):
        op = webdriver.ChromeOptions() if navegador == "chrome" else webdriver.EdgeOptions()
        if headless:
            op.add_argument("--headless=new")
        op.add_argument("--window-size=1440,900")
        op.add_argument("--lang=es-BO")
        op.add_argument("--disable-search-engine-choice-screen")
        op.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
        driver = webdriver.Chrome(options=op) if navegador == "chrome" else webdriver.Edge(options=op)
    elif navegador == "firefox":
        op = webdriver.FirefoxOptions()
        if headless:
            op.add_argument("-headless")
        op.set_preference("intl.accept_languages", "es-BO")
        driver = webdriver.Firefox(options=op)
        driver.set_window_size(1440, 900)
    else:
        raise ValueError(f"Navegador no soportado: {navegador}")
    if not headless:
        driver.maximize_window()
    driver.set_page_load_timeout(60)
    return driver


def consola(driver) -> list[dict]:
    """Mensajes de la consola del navegador desde la última lectura (Chrome/Edge)."""
    try:
        return [{"nivel": e.get("level"), "mensaje": e.get("message", "")[:500]} for e in driver.get_log("browser")]
    except Exception:  # Firefox no expone get_log
        return []


def respuestas_http(driver) -> list[dict]:
    """Respuestas HTTP recibidas por la página desde la última lectura (registro de rendimiento de Chrome)."""
    salida = []
    try:
        for e in driver.get_log("performance"):
            msg = json.loads(e["message"]).get("message", {})
            if msg.get("method") == "Network.responseReceived":
                r = msg["params"]["response"]
                salida.append({"url": r.get("url", ""), "estado": r.get("status", 0), "tipo": msg["params"].get("type", "")})
    except Exception:
        pass
    return salida
