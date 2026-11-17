r"""Interfaz web propia para ejecutar la automatización (FastAPI).

    .venv\Scripts\python -m uvicorn runner_web.app:app --host 127.0.0.1 --port 8090      (o EJECUTAR_PANEL.bat)

Permite elegir la suite y el navegador, ver el registro en vivo (SSE), cancelar, consultar el historial (SQLite)
y descargar los reportes HTML, Word, PDF y ZIP de cada corrida. Al terminar genera los reportes y, si se pidió,
el análisis con IA y el correo. Acceso con usuario y clave (RUNNER_USER / RUNNER_PASSWORD de .env); escucha solo
en este equipo. Una corrida a la vez: comparten el sistema bajo prueba y sus cuentas.
"""
from __future__ import annotations

import asyncio
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from utils import config

RAIZ = config.RAIZ
REPORTES = RAIZ / "reports"
BD = Path(__file__).resolve().parent / "historial.sqlite3"
plantillas = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "plantillas"))
app = FastAPI(title="Fetal Medical · Panel de pruebas", docs_url=None, redoc_url=None)
seguridad = HTTPBasic()

BARRIDO = "tests/ui/test_barrido_pantallas.py"
SUITES = {
    "humo": ("Humo (camino crítico, ≈ 2 min)", ["-m", "smoke"]),
    "api": ("API completa (permisos, clínica, IA, robustez)", ["tests/api"]),
    "ui": ("Interfaz con Selenium (sin el barrido de pantallas)", ["tests/ui", f"--deselect={BARRIDO}"]),
    "roles": ("Roles y permisos (UI y API)", ["-m", "roles"]),
    "autenticacion": ("Autenticación y doble factor", ["-m", "auth"]),
    "pacientes": ("Pacientes", ["-m", "pacientes"]),
    "clinico": ("Historia clínica: embarazo, controles, triaje, ecografía", ["-m", "historia_clinica"]),
    "ia": ("Ecografía e inteligencia artificial", ["-m", "ecografia_ia"]),
    "ide": ("Selenium IDE: los 35 proyectos .side", ["tests/ide"]),
    "busqueda": ("Buscadores y filtros de los 17 listados (WebDriver)", ["-m", "busqueda"]),
    "barrido": ("Barrido de todas las pantallas por rol (≈ 15 min)", [BARRIDO]),
    "rendimiento": ("Rendimiento con Locust (carga de 40 usuarios)", ["tests/rendimiento"]),
    "regresion": ("Regresión: API + interfaz + IDE + barrido", ["tests/api", "tests/ui", "tests/ide"]),
    "completa": ("Completa: regresión + rendimiento", ["tests"]),
}

ACTUAL: dict = {"proceso": None, "run_id": "", "lineas": [], "estado": "libre"}


# ---------------------------------------------------------------------- historial
def _bd():
    c = sqlite3.connect(BD)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS corridas (run_id TEXT PRIMARY KEY, suite TEXT, navegador TEXT,
                 inicio TEXT, fin TEXT, estado TEXT, total INT, pasaron INT, fallaron INT, bloqueadas INT,
                 no_ejecutadas INT, correo TEXT, ia TEXT)""")
    return c


def _guardar(run_id: str, **campos):
    with _bd() as c:
        c.execute("INSERT OR IGNORE INTO corridas (run_id) VALUES (?)", (run_id,))
        for k, v in campos.items():
            c.execute(f"UPDATE corridas SET {k} = ? WHERE run_id = ?", (v, run_id))  # noqa: S608 - claves internas


def _historial(limite: int = 40) -> list[dict]:
    with _bd() as c:
        return [dict(f) for f in c.execute("SELECT * FROM corridas ORDER BY run_id DESC LIMIT ?", (limite,))]


# ---------------------------------------------------------------------- acceso
def acceso(cred: HTTPBasicCredentials = Depends(seguridad)) -> str:
    usuario, clave = config.env("RUNNER_USER"), config.env("RUNNER_PASSWORD")
    if not usuario or not clave:
        raise HTTPException(503, "Defina RUNNER_USER y RUNNER_PASSWORD en .env")
    if not (secrets.compare_digest(cred.username.encode(), usuario.encode())
            and secrets.compare_digest(cred.password.encode(), clave.encode())):
        raise HTTPException(401, "Usuario o clave incorrectos", headers={"WWW-Authenticate": "Basic"})
    return cred.username


# ---------------------------------------------------------------------- ejecución
def _ejecutar(run_id: str, suite: str, navegador: str, visible: bool, correo: bool, ia: bool):
    dir_run = REPORTES / run_id
    dir_run.mkdir(parents=True, exist_ok=True)
    entorno = {**os.environ, "QA_RUN_ID": run_id, "PYTHONIOENCODING": "utf-8", "PYTHONUNBUFFERED": "1"}
    orden = [sys.executable, "-m", "pytest", *SUITES[suite][1], "--suite", suite, "--navegador", navegador,
             "--tb=short", "-v"] + (["--visible"] if visible else [])
    nuevo_grupo = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0

    def anotar(linea: str):
        ACTUAL["lineas"].append(linea.rstrip("\n"))
        with open(dir_run / "ejecucion.log", "a", encoding="utf-8") as f:
            f.write(linea if linea.endswith("\n") else linea + "\n")

    anotar(f"== Corrida {run_id} · suite {suite} · navegador {navegador} · {datetime.now():%d/%m/%Y %H:%M:%S}")
    p = subprocess.Popen(orden, cwd=str(RAIZ), env=entorno, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, encoding="utf-8", errors="replace", creationflags=nuevo_grupo)
    ACTUAL["proceso"] = p
    for linea in p.stdout:
        anotar(linea)
    p.wait()
    cancelada = ACTUAL["estado"] == "cancelando"
    anotar(f"== pytest terminó con código {p.returncode}{' (cancelada)' if cancelada else ''}")
    estado = "cancelada" if cancelada else "terminada"
    if cancelada:   # al cortar el proceso no corre la limpieza de la sesión de pytest: se hace aquí
        try:
            sys.path.insert(0, str(RAIZ / "tools"))
            from limpiar_qa import limpiar
            anotar(f"== Limpieza de datos QA tras la cancelación: {limpiar()}")
        except Exception as e:
            anotar(f"== No se pudo limpiar los datos QA: {type(e).__name__}: {e} (ejecute tools\\limpiar_qa.py)")
    try:
        if (dir_run / "results.json").exists():
            if ia:
                from ai import tareas
                r1, r2 = tareas.resumen_ejecutivo(run_id), tareas.analizar_fallos(run_id)
                nota_ia = "hecho" if r1["disponible"] else f"no disponible: {r1['motivo'][:120]}"
                anotar(f"== IA: resumen {nota_ia}; fallos analizados {r2.get('analizados', 0)}")
                _guardar(run_id, ia=nota_ia)
            from reporting import generar
            from reporting.modelo import cargar
            anotar("== Generando reportes (HTML, Word, PDF, ZIP)…")
            s = generar.generar(run_id)
            anotar(f"== Reportes listos: {', '.join(k for k, v in s.items() if v and k != 'run_id')}")
            t = cargar(run_id).totales
            _guardar(run_id, total=t["total"], pasaron=t["PASS"], fallaron=t["FAIL"], bloqueadas=t["BLOCKED"],
                     no_ejecutadas=t["NOT RUN"])
            if correo:
                from reporting.correo import enviar
                e = enviar(run_id)
                nota = "enviado a " + ", ".join(e["para"]) if e["enviado"] else f"no enviado: {e['motivo']}"
                anotar(f"== Correo: {nota}")
                _guardar(run_id, correo=nota)
        else:
            anotar("== La corrida no dejó results.json: no hay reportes")
            estado = "sin resultados" if not cancelada else estado
    except Exception as e:  # los reportes no deben dejar el panel bloqueado
        anotar(f"== Error al generar reportes: {type(e).__name__}: {e}")
    _guardar(run_id, fin=datetime.now().isoformat(timespec="seconds"), estado=estado)
    anotar("== FIN")
    ACTUAL.update(proceso=None, estado="libre")


@app.get("/", response_class=HTMLResponse)
def panel(request: Request, _: str = Depends(acceso)):
    from ai import servicio
    from reporting.correo import configurado
    return plantillas.TemplateResponse(request, "panel.html", {
        "suites": SUITES, "historial": _historial(), "actual": ACTUAL, "ia": servicio.estado(),
        "correo": configurado(), "sut": config.SUT_URL})


@app.post("/ejecutar")
def ejecutar(suite: str = Form(...), navegador: str = Form("chrome"), visible: str = Form(""),
             correo: str = Form(""), ia: str = Form(""), _: str = Depends(acceso)):
    if suite not in SUITES or navegador not in ("chrome", "edge", "firefox"):
        raise HTTPException(400, "Suite o navegador no válidos")
    if ACTUAL["estado"] != "libre":
        raise HTTPException(409, "Ya hay una corrida en curso")
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    ACTUAL.update(run_id=run_id, lineas=[], estado="en curso")
    _guardar(run_id, suite=suite, navegador=navegador, inicio=datetime.now().isoformat(timespec="seconds"),
             estado="en curso")
    threading.Thread(target=_ejecutar, args=(run_id, suite, navegador, bool(visible), bool(correo), bool(ia)),
                     daemon=True).start()
    return RedirectResponse("/", status_code=303)


@app.post("/cancelar")
def cancelar(_: str = Depends(acceso)):
    p = ACTUAL["proceso"]
    if p is None or p.poll() is not None:
        raise HTTPException(409, "No hay corrida en curso")
    ACTUAL["estado"] = "cancelando"
    if sys.platform == "win32":   # pytest y sus navegadores: se cierra el árbol completo
        subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True)
    else:
        p.terminate()
    return RedirectResponse("/", status_code=303)


@app.get("/registro")
async def registro(_: str = Depends(acceso)):
    """Registro en vivo de la corrida en curso (Server-Sent Events)."""
    async def flujo():
        enviado = 0
        while True:
            lineas = ACTUAL["lineas"]
            while enviado < len(lineas):
                yield f"data: {lineas[enviado]}\n\n"
                enviado += 1
            if ACTUAL["estado"] == "libre":
                yield "event: fin\ndata: fin\n\n"
                return
            await asyncio.sleep(0.5)   # sondeo del registro en memoria, no una espera de prueba
    return StreamingResponse(flujo(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.get("/estado")
def estado(_: str = Depends(acceso)):
    return {"estado": ACTUAL["estado"], "run_id": ACTUAL["run_id"], "lineas": len(ACTUAL["lineas"])}


PERMITIDOS = {"reporte.html", "reporte.docx", "reporte.pdf", "ejecucion.log", "results.json"}


@app.get("/corrida/{run_id}/{ruta:path}")
def archivo(run_id: str, ruta: str, _: str = Depends(acceso)):
    """Reportes y evidencias de una corrida (solo dentro de reports/<run_id>/)."""
    base = (REPORTES / run_id).resolve()
    destino = (base / ruta).resolve()
    if REPORTES.resolve() not in base.parents or base not in destino.parents or not destino.is_file():
        raise HTTPException(404, "No existe")
    en_carpeta = destino.parent != base
    if not en_carpeta and destino.name not in PERMITIDOS and destino.suffix != ".zip":
        raise HTTPException(404, "No existe")
    descarga = destino.suffix in (".docx", ".zip")
    return FileResponse(destino, filename=f"{run_id}_{destino.name}" if descarga else None)


@app.post("/reportes/{run_id}")
def regenerar(run_id: str, _: str = Depends(acceso)):
    if not (REPORTES / run_id / "results.json").is_file():
        raise HTTPException(404, "La corrida no tiene resultados")
    from reporting import generar
    generar.generar(run_id)
    return RedirectResponse("/", status_code=303)
