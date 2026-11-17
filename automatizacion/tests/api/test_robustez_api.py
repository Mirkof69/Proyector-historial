"""Robustez y contrato de la API: ningún listado responde 500, esquema de los recursos principales y latencia."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

import pytest

from conftest import cliente

pytestmark = [pytest.mark.api]

INVENTARIO = json.loads((Path(__file__).resolve().parents[2] / "docs" / "inventario" / "inventario.json").read_text("utf-8"))
# GET sin parámetros de ruta; se omiten exportaciones pesadas, plantillas y la documentación de la API
_EXCLUIR = ("exportar", "plantilla", "pdf", "/docs", "/redoc", "/schema", "descargar", "excel", "backup", "respaldo",
            "informe", "reporte-narrativo")
LISTADOS = sorted({e["ruta"] for e in INVENTARIO["endpoints"] if "GET" in e["metodos"] and "{" not in e["ruta"]
                   and not any(x in e["ruta"] for x in _EXCLUIR)})


@pytest.mark.regression
@pytest.mark.tc("TC-103")
@pytest.mark.parametrize("ruta", LISTADOS)
def test_tc103_ningun_listado_responde_500(ruta):
    """Ningún listado de la API responde 500."""
    r = cliente("administrador").get(ruta.replace("/api", "", 1), timeout=120)
    assert r.status_code < 500, f"GET {ruta} -> HTTP {r.status_code}: {r.text[:200]}"


ESQUEMAS = {
    "/usuarios/me/": {"id": int, "email": str, "rol": str},
}


@pytest.mark.tc("TC-104")
def test_tc104_esquema_de_los_recursos_principales(paciente_qa, embarazo_qa):
    """Esquema de respuesta de los endpoints principales."""
    med = cliente("medico")
    contratos = {
        f"/pacientes/{paciente_qa['id']}/": {"id": int, "id_clinico": str, "nombre": str, "ci": str, "activo": bool},
        f"/embarazos/{embarazo_qa['id']}/": {"id": int, "paciente": int, "estado": str},
        "/usuarios/me/": {"id": int, "email": str, "rol": str},
    }
    errores = []
    for ruta, campos in contratos.items():
        d = med.get(ruta).json()
        for campo, tipo in campos.items():
            if campo not in d:
                errores.append(f"{ruta}: falta «{campo}»")
            elif not isinstance(d[campo], tipo):
                errores.append(f"{ruta}: «{campo}» es {type(d[campo]).__name__}, se esperaba {tipo.__name__}")
    lista = med.get("/controles/", params={"page_size": 5}).json()
    for k in ("count", "results"):
        if k not in lista:
            errores.append(f"/controles/: el listado paginado no trae «{k}»")
    assert not errores, "; ".join(errores)


LATENCIA = ["/pacientes/?page=1&page_size=20", "/pacientes/resumen/", "/pacientes/?search=quispe&page=1&page_size=20",
            "/embarazos/?page=1&page_size=20", "/embarazos/resumen/", "/controles/?page=1&page_size=20",
            "/ecografias/?page=1&page_size=20", "/laboratorios/examenes/?page=1&page_size=20",
            "/laboratorios/examenes/resumen/", "/vacunas/registros/?page=1&page_size=20", "/citas/citas/?page=1&page_size=20",
            "/partos/?page=1&page_size=20", "/notas-evolucion/?page=1&page_size=20", "/triaje/triajes/?page=1&page_size=20",
            "/reportes/dashboard-kpis/", "/reportes/natalidad/"]
_MEDIDAS: dict[str, dict] = {}


@pytest.mark.tc("TC-116")
@pytest.mark.parametrize("ruta", LATENCIA)
def test_tc116_latencia_p95_de_los_listados(ruta):
    """Percentil 95 de los listados principales (20 repeticiones, criterio p95 < 200 ms de RNF-01)."""
    admin = cliente("administrador")
    admin.get(ruta)   # calentamiento: la primera petición carga cachés y no representa el uso normal
    tiempos = []
    for _ in range(20):
        r = admin.get(ruta)
        assert r.status_code == 200, f"{ruta}: HTTP {r.status_code}"
        tiempos.append(admin.ultima_duracion_ms)
    tiempos.sort()
    p95 = tiempos[int(round(0.95 * len(tiempos))) - 1]
    _MEDIDAS[ruta] = {"mediana_ms": round(statistics.median(tiempos), 1), "p95_ms": round(p95, 1), "max_ms": round(max(tiempos), 1)}
    salida = Path(__file__).resolve().parents[2] / "reports" / "latencia_api.json"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(json.dumps(_MEDIDAS, ensure_ascii=False, indent=1), encoding="utf-8")
    assert p95 < 200, f"{ruta}: p95 = {p95:.0f} ms (≥ 200 ms)"
