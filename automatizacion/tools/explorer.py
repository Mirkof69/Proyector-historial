"""Fase 1 - Explorador automatizado con Selenium WebDriver.

Para cada rol inicia sesión y recorre TODAS las pantallas del inventario que su rol puede abrir (y, como control,
una muestra de las que no). Por pantalla registra: carga correcta, tiempo de carga, errores de la consola de
JavaScript, respuestas HTTP 4xx/5xx (registro de rendimiento de Chrome), pantalla en blanco, desborde horizontal,
textos sin traducir (claves tipo «menu.item» o «undefined») y accesibilidad básica (campos sin etiqueta, imágenes
sin texto alternativo, botones sin nombre accesible). Guarda una captura por pantalla y rol.

    python tools/explorer.py                 (todos los roles)
    python tools/explorer.py --roles recepcion enfermera
Salida: docs/inventario/capturas/<rol>/*.png y reports/explorador/hallazgos_<fecha>.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

from pages.login_page import LoginPage  # noqa: E402
from utils import config  # noqa: E402
from utils.api_client import ApiCliente  # noqa: E402
from utils.driver_factory import consola, crear_driver, respuestas_http  # noqa: E402

CAPTURAS = RAIZ / "docs" / "inventario" / "capturas"
SALIDA = RAIZ / "reports" / "explorador"

A11Y_JS = """
const sinEtiqueta = [...document.querySelectorAll('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select, textarea')]
  .filter(e => e.offsetParent !== null)
  .filter(e => !(e.labels && e.labels.length) && !e.getAttribute('aria-label') && !e.getAttribute('aria-labelledby')
               && !e.getAttribute('placeholder') && !e.closest('.ant-select'))
  .length;
const imgsSinAlt = [...document.querySelectorAll('img')].filter(i => i.offsetParent !== null && !i.hasAttribute('alt')).length;
const botonesSinNombre = [...document.querySelectorAll('button')]
  .filter(b => b.offsetParent !== null && !b.innerText.trim() && !b.getAttribute('aria-label') && !b.getAttribute('title'))
  .length;
const desborde = document.documentElement.scrollWidth - document.documentElement.clientWidth;
const texto = document.body.innerText || '';
const claves = (texto.match(/\\b[a-z]+(\\.[a-z_]+){2,}\\b|\\bundefined\\b|\\bNaN\\b|\\[object Object\\]/g) || []).slice(0, 5);
const zona = document.querySelector('.ant-layout-content') || document.querySelector('main') || document.body;
const contenido = Math.max(zona.innerText.trim().length, (document.querySelector('.ant-card, .ant-table, .ant-descriptions, form') ? 50 : 0));
return {sinEtiqueta, imgsSinAlt, botonesSinNombre, desborde, claves, contenido,
        titulo: (document.querySelector('h1, h2, .ant-page-header-heading-title, .ant-typography h1') || {}).innerText || ''};
"""


def ids_de_ejemplo(api: ApiCliente) -> dict[str, int]:
    """Un id real por tipo de recurso para abrir las pantallas con :id."""
    ids = {}
    for clave, ruta in {"pacientes": "/pacientes/", "embarazos": "/embarazos/", "controles": "/controles/",
                        "ecografias": "/ecografias/", "partos": "/partos/", "laboratorio": "/laboratorios/examenes/",
                        "citas": "/citas/citas/", "triaje": "/triaje/triajes/", "vacunas": "/vacunas/registros/",
                        "notas-evolucion": "/notas-evolucion/", "alertas": "/alertas/", "consultorios": "/consultorios/",
                        "historia-clinica": "/pacientes/"}.items():
        try:
            filas = api.lista(ruta, page_size=1)
            if filas:
                ids[clave] = filas[0]["id"]
        except Exception:
            pass
    return ids


def ruta_concreta(ruta: str, ids: dict) -> str | None:
    if ":" not in ruta:
        return ruta
    modulo = ruta.split("/dashboard/")[-1].split("/")[0]
    ident = ids.get(modulo) or ids.get(modulo.rstrip("s"))
    if not ident:
        return None
    return re.sub(r":[a-z_]+", str(ident), ruta)


def explorar_rol(rol: str, rutas: list[dict], ids: dict, prohibidas_muestra: int = 6) -> list[dict]:
    d = crear_driver()
    hallazgos = []
    try:
        if LoginPage(d).iniciar_sesion(config.ROLES[rol]) != "panel":
            return [{"rol": rol, "ruta": "/login", "problemas": ["no pudo iniciar sesión"]}]
        (CAPTURAS / rol).mkdir(parents=True, exist_ok=True)
        consola(d), respuestas_http(d)   # descarta lo del login
        # /setup-mfa queda fuera del recorrido: abrirla con el MFA activo REEMPLAZA la clave del doble factor en el
        # servidor (BUG-004, hallado por este explorador el 13/11/2026). /login y / cierran la sesión del recorrido.
        excluir = {"/setup-mfa", "/login", "/", "/dashboard/*", "/403", "*"}
        rutas = [r for r in rutas if r["ruta"] not in excluir]
        permitidas = [r for r in rutas if rol in r["roles"] and not r["redirige_a"]]
        prohibidas = [r for r in rutas if rol not in r["roles"] and not r["redirige_a"] and ":" not in r["ruta"]][:prohibidas_muestra]
        for r, debe_ver in [(x, True) for x in permitidas] + [(x, False) for x in prohibidas]:
            url = ruta_concreta(r["ruta"], ids)
            if not url:
                hallazgos.append({"rol": rol, "ruta": r["ruta"], "omitida": "sin un registro de ejemplo para el :id"})
                continue
            t0 = time.perf_counter()
            d.get(config.SUT_URL + url)
            try:
                WebDriverWait(d, 30).until(lambda x: x.execute_script("return document.readyState") == "complete")
                WebDriverWait(d, 15).until(lambda x: not x.find_elements("css selector", ".ant-spin-spinning")
                                           or x.execute_script("return document.querySelectorAll('.ant-spin-spinning').length") == 0)
                # pantallas con su propio indicador de carga («Cargando perfil…», esqueletos de Ant Design)
                WebDriverWait(d, 20).until(lambda x: "Cargando" not in x.find_element("tag name", "body").text
                                           and not x.find_elements("css selector", ".ant-skeleton-active"))
            except Exception:
                pass
            carga_ms = round((time.perf_counter() - t0) * 1000)
            info = d.execute_script(A11Y_JS)
            errores_js = [m["mensaje"] for m in consola(d) if m["nivel"] == "SEVERE" and "favicon" not in m["mensaje"]]
            http = [x for x in respuestas_http(d) if x["estado"] >= 400 and "/api/" in x["url"]]
            final = d.current_url.replace(config.SUT_URL, "")
            problemas = []
            if debe_ver:
                if "/403" in final or "/login" in final:
                    problemas.append(f"no se pudo abrir (terminó en {final})")
                if info["contenido"] < 20:
                    problemas.append("pantalla en blanco")
                if any(h["estado"] >= 500 for h in http):
                    problemas.append("respuesta 5xx de la API")
                if errores_js:
                    problemas.append("errores de JavaScript")
                if info["desborde"] > 8:
                    problemas.append(f"desborde horizontal de {info['desborde']} px")
                if info["claves"]:
                    problemas.append(f"textos sin traducir: {info['claves']}")
            else:
                if "/403" not in final and "/login" not in final and info["contenido"] > 50:
                    problemas.append(f"un rol sin permiso abrió la pantalla (terminó en {final})")
            nombre = re.sub(r"[^A-Za-z0-9]+", "_", url.strip("/"))[:80] or "inicio"
            captura = CAPTURAS / rol / f"{'NEGADA_' if not debe_ver else ''}{nombre}.png"
            d.save_screenshot(str(captura))
            hallazgos.append({"rol": rol, "ruta": r["ruta"], "url": url, "debe_ver": debe_ver, "final": final,
                              "carga_ms": carga_ms, "errores_js": errores_js[:5], "http_4xx_5xx": http[:8],
                              "a11y": {k: info[k] for k in ("sinEtiqueta", "imgsSinAlt", "botonesSinNombre")},
                              "desborde_px": info["desborde"], "problemas": problemas,
                              "captura": str(captura.relative_to(RAIZ)).replace("\\", "/")})
            print(f"  [{rol}] {url:<55} {carga_ms:>5} ms {'OK' if not problemas else '; '.join(problemas)}", flush=True)
    finally:
        d.quit()
    return hallazgos


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roles", nargs="*", default=list(config.ROLES))
    a = ap.parse_args()
    inv = json.loads((RAIZ / "docs" / "inventario" / "inventario.json").read_text(encoding="utf-8"))
    ids = ids_de_ejemplo(ApiCliente(config.ROLES["administrador"]).iniciar())
    todos = []
    for rol in a.roles:
        print(f"== {rol}", flush=True)
        todos += explorar_rol(rol, inv["rutas"], ids)
    SALIDA.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M")
    (SALIDA / f"hallazgos_{marca}.json").write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
    (SALIDA / "ultimo.json").write_text(json.dumps(todos, ensure_ascii=False, indent=1), encoding="utf-8")
    con = [h for h in todos if h.get("problemas")]
    print(f"pantallas visitadas: {sum('url' in h for h in todos)} | con problemas: {len(con)}")


if __name__ == "__main__":
    principal()
