"""TC-109 a TC-111: las grabaciones de Selenium IDE reproducidas con selenium-side-runner (tools/ejecutar_side.py).

La salida del runner queda como evidencia de texto en la carpeta de la corrida.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from utils import evidencias

pytestmark = [pytest.mark.ui, pytest.mark.ide]

RAIZ = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("ejecutar_side", RAIZ / "tools" / "ejecutar_side.py")
ejecutar_side = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ejecutar_side)

GRABACIONES = sorted((RAIZ / "selenium_ide").glob("TC-*.side"))


@pytest.mark.parametrize("side", GRABACIONES, ids=[s.stem for s in GRABACIONES])
def test_grabacion_selenium_ide(request, side):
    """Reproduce la grabación .side y exige que termine sin fallas."""
    tc = side.stem.split("_")[0]
    request.node.add_marker(pytest.mark.tc(tc))
    evidencias.CASO_ACTUAL["tc"] = tc
    r = ejecutar_side.reproducir(side)
    salida = evidencias.DIR_EV / f"EV-{tc}-side-runner.txt"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(r["salida"], encoding="utf-8")
    comandos = json.loads(side.read_text(encoding="utf-8"))["tests"][0]["commands"]
    validaciones = [x["command"] for x in comandos if x["command"].startswith(("assert", "verify"))]
    resumen = [x for x in r["salida"].splitlines() if x.strip() and not x.strip().startswith("at ") and "Deprecation" not in x
               and "trace-deprecation" not in x and "Jest did not exit" not in x and "usually means" not in x]
    evidencias.captura_texto(
        [f"Selenium IDE · {side.name} · selenium-side-runner 4.0.13 · Chrome", f"Comandos: {len(comandos)} · "
         f"validaciones: {len(validaciones)} ({', '.join(sorted(set(validaciones)))})", ""] + resumen[-16:]
        + ["", f"Resultado: {r['estado']} en {r['duracion_s']} s"], "ejecucion", f"Reproducción de {side.name}")
    if r.get("captura_fallo"):
        (evidencias.DIR_EV / f"EV-{tc}-fallo-side.png").write_bytes(r["captura_fallo"])
    if r["estado"] == "BLOCKED":
        pytest.skip(f"BLOCKED: {r['salida']}")
    assert r["estado"] == "PASS", f"La grabación {side.name} falló:\n{r['salida'][-1200:]}"
