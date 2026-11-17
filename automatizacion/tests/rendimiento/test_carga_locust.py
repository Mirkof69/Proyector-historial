"""TC-112 a TC-115: rendimiento con Locust (locust/locustfile.py), solo lecturas sobre la base real.

TC-112 (carga esperada de una clínica, 40 usuarios) se ejecuta en la suite completa. TC-113 (estrés),
TC-114 (pico) y TC-115 (resistencia) pueden saturar el equipo: corren solo con AUTORIZAR_ESTRES=1 en .env o en
el entorno (punto de control del plan de pruebas); sin ella quedan NOT RUN con el motivo.

Se usa 127.0.0.1 y no «localhost»: en Windows el cliente intenta primero IPv6 (::1) y cada conexión nueva
espera ~2 s antes de caer a IPv4 (medido: 2 074 ms contra 16 ms). Ese retraso es del cliente, no del sistema.
"""
from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

from utils import config, evidencias

pytestmark = [pytest.mark.rendimiento]

RAIZ = Path(__file__).resolve().parents[2]
HOST = config.SUT_API.replace("localhost", "127.0.0.1").rsplit("/api", 1)[0]
AUTORIZADO = config.env("AUTORIZAR_ESTRES") == "1"   # .env ya está cargado en el entorno


def _locust(escenario: str, extra: list[str], limite_s: int) -> dict:
    salida = evidencias.DIR_RUN / "locust"
    salida.mkdir(parents=True, exist_ok=True)
    prefijo = salida / escenario
    entorno = {**os.environ, "ESCENARIO": escenario, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-m", "locust", "-f", str(RAIZ / "locust" / "locustfile.py"), "--headless",
                        "--host", HOST, "--csv", str(prefijo), "--html", str(prefijo) + ".html", "--only-summary",
                        *extra], capture_output=True, text=True, encoding="utf-8", errors="replace", env=entorno,
                       timeout=limite_s, cwd=str(RAIZ))
    with open(f"{prefijo}_stats.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    total = next(x for x in filas if x["Name"] == "Aggregated")
    peticiones = int(total["Request Count"])
    fallas = int(total["Failure Count"])
    resumen = {"escenario": escenario, "peticiones": peticiones, "fallas": fallas,
               "error_pct": round(100 * fallas / max(peticiones, 1), 2), "p50_ms": float(total["50%"]),
               "p95_ms": float(total["95%"]), "p99_ms": float(total["99%"]), "rps": float(total["Requests/s"]),
               "html": str(Path(str(prefijo) + ".html").relative_to(evidencias.DIR_RUN)).replace("\\", "/"),
               "por_endpoint": [{"nombre": x["Name"], "peticiones": int(x["Request Count"]),
                                 "fallas": int(x["Failure Count"]), "p95_ms": float(x["95%"])}
                                for x in filas if x["Name"] != "Aggregated"],
               "codigo_salida": r.returncode}
    (salida / f"{escenario}_resumen.json").write_text(__import__("json").dumps(resumen, ensure_ascii=False, indent=1),
                                                       encoding="utf-8")
    return resumen


@pytest.mark.tc("TC-112")
def test_tc112_carga_esperada_40_usuarios():
    """40 usuarios concurrentes durante 3 minutos: p95 < 2 s y errores < 1 %."""
    r = _locust("carga", ["-u", "40", "-r", "4", "-t", "3m"], 600)
    lentos = [e["nombre"] for e in r["por_endpoint"] if e["p95_ms"] >= 2000]
    assert r["peticiones"] > 500, f"La carga no llegó a generar tráfico suficiente: {r['peticiones']} peticiones"
    assert r["error_pct"] < 1, f"Errores {r['error_pct']} % ({r['fallas']} de {r['peticiones']})"
    assert r["p95_ms"] < 2000, f"p95 global {r['p95_ms']} ms; endpoints con p95 ≥ 2 s: {lentos}"


def _requiere_autorizacion():
    if not AUTORIZADO:
        pytest.skip("NOT RUN: prueba que puede saturar el equipo; requiere autorización (AUTORIZAR_ESTRES=1)")


@pytest.mark.tc("TC-113")
def test_tc113_estres_hasta_degradacion():
    """Escalones de 20 usuarios cada minuto hasta 200: se registra el punto de degradación."""
    _requiere_autorizacion()
    r = _locust("estres", [], 900)
    assert r["peticiones"] > 0
    # el criterio de aceptación es identificar el punto: el resultado detallado queda en estres_stats_history.csv


@pytest.mark.tc("TC-114")
def test_tc114_pico_repentino():
    """Salto de 10 a 150 usuarios durante un minuto: el sistema se recupera sin errores persistentes."""
    _requiere_autorizacion()
    r = _locust("pico", [], 600)
    assert r["error_pct"] < 5, f"Errores durante el pico: {r['error_pct']} %"


@pytest.mark.tc("TC-115")
def test_tc115_resistencia_15_minutos():
    """40 usuarios estables durante 15 minutos sin degradación ni errores crecientes."""
    _requiere_autorizacion()
    r = _locust("resistencia", [], 1500)
    assert r["error_pct"] < 1 and r["p95_ms"] < 2000, f"p95 {r['p95_ms']} ms, errores {r['error_pct']} %"
