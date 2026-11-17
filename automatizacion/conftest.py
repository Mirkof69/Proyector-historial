"""Fixtures y complemento de resultados de la automatización.

- `navegador(rol)`: un Chrome/Edge/Firefox con la sesión del rol ya iniciada (se reutiliza durante la corrida).
- `navegador_limpio`: un navegador sin sesión, para probar el login.
- `api(rol)`: un cliente de la API con la sesión del rol.
- `@pytest.mark.tc("TC-012")`: enlaza cada prueba con su caso de prueba.
- Al fallar: captura, consola del navegador y HTML de la página (evidencias.volcado_fallo).
- Al terminar: reports/<run_id>/results.json con cada caso, su estado (PASS/FAIL/BLOCKED/NOT RUN),
  su duración, su error, la clasificación del fallo y sus evidencias.
"""
from __future__ import annotations

import json
import platform
import re
from datetime import datetime

import pytest

from utils import config, evidencias
from utils.api_client import ApiCliente
from utils.driver_factory import crear_driver

_DRIVERS: dict[str, object] = {}
_APIS: dict[str, ApiCliente] = {}
_RESULTADOS: list[dict] = []
_INICIO = datetime.now()


def pytest_addoption(parser):
    parser.addoption("--navegador", default=None, help="chrome | edge | firefox")
    parser.addoption("--visible", action="store_true", help="muestra el navegador (por defecto headless)")
    parser.addoption("--suite", default="", help="nombre de la suite para el reporte")


def pytest_configure(config):  # noqa: F811 - pytest exige este nombre de parámetro
    from utils import config as ajustes
    if config.getoption("--navegador"):
        ajustes.NAVEGADOR = config.getoption("--navegador")
    if config.getoption("--visible"):
        ajustes.HEADLESS = False


# ---------------------------------------------------------------------- fixtures
@pytest.fixture(scope="session")
def roles():
    return config.ROLES


@pytest.fixture
def navegador(request):
    """Fábrica: navegador("medico") devuelve un driver con la sesión de ese rol."""
    usados = []

    def obtener(clave: str):
        if clave not in _DRIVERS:
            from pages.login_page import LoginPage
            d = crear_driver()
            r = LoginPage(d).iniciar_sesion(config.ROLES[clave])
            if r != "panel":
                d.quit()
                pytest.skip(f"BLOCKED: no se pudo iniciar sesión como {clave} ({r})")
            _DRIVERS[clave] = d
        usados.append(_DRIVERS[clave])
        return _DRIVERS[clave]

    request.node._drivers = usados
    return obtener


@pytest.fixture
def navegador_limpio(request):
    d = crear_driver()
    request.node._drivers = [d]
    yield d
    d.quit()


@pytest.fixture
def api():
    def obtener(clave: str) -> ApiCliente:
        if clave not in _APIS:
            _APIS[clave] = ApiCliente(config.ROLES[clave]).iniciar()
        return _APIS[clave]
    return obtener


@pytest.fixture
def api_anonima():
    return ApiCliente()


def cliente(clave: str) -> ApiCliente:
    """Cliente con sesión, compartido por toda la corrida (también lo usan los fixtures de datos)."""
    if clave not in _APIS:
        _APIS[clave] = ApiCliente(config.ROLES[clave]).iniciar()
    return _APIS[clave]


@pytest.fixture(scope="session")
def paciente_qa():
    """Paciente sintética QA registrada por recepción (se da de baja al final de la corrida)."""
    from data import fabrica
    r = cliente("recepcion").post("/pacientes/", fabrica.paciente(), verificar=True)
    return {"id": fabrica.anotar("pacientes", r.json()["id"]), **r.json()}


@pytest.fixture(scope="session")
def embarazo_qa(paciente_qa):
    """Embarazo activo de 29 semanas de la paciente QA, registrado por el médico."""
    from data import fabrica
    r = cliente("medico").post("/embarazos/", fabrica.embarazo(paciente_qa["id"], dias_fum=203), verificar=True)
    return r.json()


@pytest.fixture(scope="session", autouse=True)
def limpieza_qa():
    """Al terminar: baja lógica de las pacientes QA y cancelación de las citas QA creadas en esta corrida."""
    yield
    from data import fabrica
    if not fabrica.CREADOS:
        return
    try:
        admin = cliente("administrador")
    except Exception:
        return
    for ruta, ident in reversed(fabrica.CREADOS):
        try:
            if ruta == "pacientes":
                admin.delete(f"/pacientes/{ident}/")
            elif ruta == "citas":
                admin.post(f"/citas/citas/{ident}/cancelar/", {"motivo": "Limpieza de datos QA"})
        except Exception:
            pass


def pytest_sessionfinish(session, exitstatus):
    for d in _DRIVERS.values():
        try:
            d.quit()
        except Exception:
            pass
    _escribir_resultados(session)


# ---------------------------------------------------------------------- resultados por caso
def _tc_de(item) -> str:
    m = item.get_closest_marker("tc")
    if m and m.args:
        return m.args[0]
    hallado = re.search(r"(TC-[A-Z]*-?\d+)", item.name.upper().replace("_", "-"))
    return hallado.group(1) if hallado else item.name


def _suites_de(item) -> list[str]:
    return [m.name for m in item.iter_markers() if m.name not in ("tc", "parametrize", "usefixtures", "flaky",
                                                                    "timeout", "skip", "skipif", "xfail")]


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    evidencias.REGISTRO.clear()
    evidencias.CASO_ACTUAL["tc"] = _tc_de(item)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    salida = yield
    rep = salida.get_result()
    if rep.when == "call" and rep.failed:
        volcados = []
        for d in getattr(item, "_drivers", []) or []:
            volcados.append(evidencias.volcado_fallo(d))
        item._volcado = volcados[0] if volcados else {}
    if rep.when == "call" or (rep.when == "setup" and (rep.failed or rep.skipped)):
        _registrar(item, rep, call)


def _clasificar(texto: str) -> str:
    """Clasificación inicial del FAIL (la revisa el analista o la IA): sistema, script, datos o ambiente."""
    t = texto.lower()
    if any(x in t for x in ("connectionerror", "connection refused", "max retries", "err_connection", "timeout")
           ) and "assert" not in t:
        return "ambiente"
    if any(x in t for x in ("nosuchelement", "stale element", "invalid selector", "attributeerror", "typeerror",
                            "nameerror", "fixture")):
        return "script"
    if any(x in t for x in ("duplicate", "ya existe", "ya está registrad", "unique")):
        return "datos"
    return "sistema"


def _resumen_error(excinfo, traza: str) -> str:
    """Mensaje legible del fallo: sin el volcado de Selenium y, si la espera venció sin mensaje, con la línea de la
    prueba o del Page Object donde ocurrió."""
    tipo = excinfo.type.__name__
    mensaje = re.split(r"\n\s*(Stacktrace|\(Session info)", str(excinfo.value).replace("Message: ", "", 1))[0].strip()
    lineas = re.findall(r"^((?:tests|pages|components|utils)[\\/][^\s:]+\.py):(\d+)", traza, flags=re.M)
    donde = f" en {lineas[-1][0]}:{lineas[-1][1]}" if lineas else ""
    if tipo == "AssertionError":
        return mensaje[:1500]
    return f"{tipo}{donde}: {mensaje}"[:1500] if mensaje else f"{tipo}{donde}"


def _registrar(item, rep, call):
    if rep.passed:
        estado = "PASS"
    elif rep.skipped:
        motivo = rep.longrepr[2] if isinstance(rep.longrepr, tuple) else str(rep.longrepr)
        estado = "BLOCKED" if "BLOCKED" in motivo else "NOT RUN"
    else:
        estado = "FAIL"
    error = ""
    tb = ""
    if rep.failed:
        error = _resumen_error(call.excinfo, str(rep.longrepr)) if call.excinfo else str(rep.longrepr)[:1500]
        # sin el volcado nativo del controlador («Stacktrace: … (No symbol)»), que no aporta al análisis
        tb = "\n".join(x for x in str(rep.longrepr).splitlines()
                       if "(No symbol)" not in x and "Stacktrace:" not in x and "Symbols not available" not in x)[-4000:]
    elif rep.skipped:
        error = (rep.longrepr[2] if isinstance(rep.longrepr, tuple) else str(rep.longrepr))[:500]
    volcado = getattr(item, "_volcado", {}) or {}
    doc = (item.function.__doc__ or "").strip().splitlines()
    _RESULTADOS.append({
        "nodeid": item.nodeid, "tc": _tc_de(item), "nombre": doc[0] if doc else item.name,
        "suites": _suites_de(item), "estado": estado, "duracion_s": round(rep.duration, 2),
        "error": error, "traceback": tb, "clasificacion": _clasificar(error + tb) if estado == "FAIL" else "",
        "evidencias": list(evidencias.REGISTRO), "consola": volcado.get("consola", []),
        "html_recorte": volcado.get("html", "")[:3000],
    })


def _escribir_resultados(session):
    evidencias.DIR_RUN.mkdir(parents=True, exist_ok=True)
    tot = {k: sum(r["estado"] == k for r in _RESULTADOS) for k in ("PASS", "FAIL", "BLOCKED", "NOT RUN")}
    datos = {
        "run_id": evidencias.RUN_ID, "inicio": _INICIO.isoformat(timespec="seconds"),
        "fin": datetime.now().isoformat(timespec="seconds"),
        "duracion_s": round((datetime.now() - _INICIO).total_seconds(), 1),
        "suite": session.config.getoption("--suite") or " ".join(session.config.args),
        "marcadores": session.config.getoption("-m") or "",
        "ambiente": {"sut_url": config.SUT_URL, "sut_api": config.SUT_API, "navegador": config.NAVEGADOR,
                     "headless": config.HEADLESS, "so": f"{platform.system()} {platform.release()}",
                     "python": platform.python_version()},
        "totales": {**tot, "total": len(_RESULTADOS)},
        "casos": _RESULTADOS,
    }
    previo = evidencias.DIR_RUN / "results.json"
    if previo.exists():  # varias corridas de pytest en una misma ejecución de la interfaz: se acumulan
        try:
            ant = json.loads(previo.read_text(encoding="utf-8"))
            datos["casos"] = ant.get("casos", []) + datos["casos"]
            datos["inicio"] = ant.get("inicio", datos["inicio"])
            datos["totales"] = {k: sum(r["estado"] == k for r in datos["casos"]) for k in
                                ("PASS", "FAIL", "BLOCKED", "NOT RUN")}
            datos["totales"]["total"] = len(datos["casos"])
        except ValueError:
            pass
    previo.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
