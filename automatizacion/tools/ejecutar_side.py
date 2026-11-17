"""Reproduce las grabaciones de Selenium IDE (selenium_ide/*.side) con selenium-side-runner 4.0.13.

Antes de reproducir, copia cada .side a una carpeta temporal y cambia los marcadores (__QA_EMAIL_<ROL>__,
__QA_PASSWORD__, __QA_TOTP_<ROL>__, __QA_CI__) por los valores de .env, el código TOTP vigente y una cédula QA. La copia se borra al terminar.

    .venv\\Scripts\\python tools\\ejecutar_side.py [--visible] [archivo.side ...]
Devuelve un JSON por grabación: {archivo, estado PASS/FAIL, duracion_s, salida}.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from utils import config, totp  # noqa: E402

# selenium-side-runner lanza jest por la consola sin comillas: falla si su ruta tiene espacios («Nueva carpeta»).
# Por eso se instala en una carpeta del usuario sin espacios, con la versión fijada en tools/side_runner/package.json.
CARPETA_RUNNER = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "fetal-medical" / "side_runner"
RUNNER = CARPETA_RUNNER / "node_modules" / ".bin" / ("selenium-side-runner.cmd" if sys.platform == "win32"
                                                       else "selenium-side-runner")


def instalar_runner() -> bool:
    if RUNNER.exists():
        return True
    CARPETA_RUNNER.mkdir(parents=True, exist_ok=True)
    shutil.copy(RAIZ / "tools" / "side_runner" / "package.json", CARPETA_RUNNER / "package.json")
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=str(CARPETA_RUNNER), capture_output=True,
                   timeout=900)
    return RUNNER.exists()


def reproducir(side: Path, visible: bool = False) -> dict:
    """Reproduce el proyecto. Si Chrome no llega a arrancar («Driver took too long to build», equipo cargado), lo
    intenta una vez más: es una condición del ambiente, no un resultado de la prueba."""
    r = _reproducir(side, visible)
    if r["estado"] == "FAIL" and "Driver took too long to build" in r["salida"]:
        segundo = _reproducir(side, visible)
        segundo["salida"] = "(Segundo intento: en el primero el navegador no llegó a arrancar.)\n" + segundo["salida"]
        return segundo
    return r


def _reproducir(side: Path, visible: bool = False) -> dict:
    if " " in str(CARPETA_RUNNER) or not instalar_runner():
        return {"archivo": side.name, "estado": "BLOCKED", "duracion_s": 0,
                "salida": f"No se pudo instalar selenium-side-runner en {CARPETA_RUNNER} (ruta sin espacios)"}
    texto = side.read_text(encoding="utf-8").replace("__QA_PASSWORD__", config.PASSWORD)
    for clave, rol in config.ROLES.items():
        texto = texto.replace(f"__QA_EMAIL_{clave.upper()}__", rol.email)
        if rol.totp_secret:   # código TOTP vigente al momento de reproducir (el ejecutor inicia sesión en segundos)
            texto = texto.replace(f"__QA_TOTP_{clave.upper()}__", totp.codigo(rol.totp_secret))
    texto = texto.replace("__QA_CI__", "99" + "".join(random.choice("0123456789") for _ in range(7)))
    tmp = Path(tempfile.mkdtemp(prefix="side_"))
    try:
        copia = tmp / side.name
        copia.write_text(texto, encoding="utf-8")
        args = ["--headless=new", "--window-size=1366,900"] if not visible else ["--window-size=1366,900"]
        capacidades = f"browserName=chrome goog:chromeOptions.args=[{','.join(args)}]"
        t0 = time.perf_counter()
        # Jest tarda unos 30 s en salir tras terminar (deja conexiones abiertas): se lee su salida en vivo y, cuando
        # imprime el resumen «Tests: …», se cierra el proceso con su árbol. El veredicto sale de ese resumen.
        p = subprocess.Popen([str(RUNNER), "-c", capacidades, "--base-url", config.SUT_URL, "--timeout", "30000",
                              "--jest-timeout", "240000", "--screenshot-failure-directory", str(tmp / "fallos"), str(copia)],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                             cwd=str(tmp))
        lineas, resumen = [], ""
        for linea in p.stdout:
            lineas.append(linea)
            if linea.startswith("Tests:"):
                resumen = linea
                break
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
        else:
            p.terminate()
        salida = "".join(lineas).replace(config.PASSWORD, "********")
        salida = re.sub(r"\[[0-9;]*m", "", salida)   # sin los códigos de color de la consola
        estado = "PASS" if resumen and "passed" in resumen and "failed" not in resumen else "FAIL"
        capturas = sorted((tmp / "fallos").glob("*.png")) if (tmp / "fallos").exists() else []
        return {"archivo": side.name, "estado": estado, "duracion_s": round(time.perf_counter() - t0, 1),
                "salida": salida[-5000:], "captura_fallo": capturas[0].read_bytes() if capturas else b""}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--visible", action="store_true")
    ap.add_argument("archivos", nargs="*")
    a = ap.parse_args()
    lista = [Path(x) for x in a.archivos] or sorted((RAIZ / "selenium_ide").glob("TC-*.side"))
    resultados = [reproducir(s, a.visible) for s in lista]
    print(json.dumps([{k: v for k, v in r.items() if k not in ("salida", "captura_fallo")} for r in resultados], ensure_ascii=False, indent=1))
    sys.exit(0 if all(r["estado"] == "PASS" for r in resultados) else 1)


if __name__ == "__main__":
    principal()
