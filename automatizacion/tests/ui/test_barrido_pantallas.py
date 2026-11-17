"""TC-102: cada pantalla permitida de cada rol carga sin error de JavaScript, sin 5xx y sin quedar en blanco.

Reutiliza el recorrido de tools/explorer.py (inventario de rutas generado del código): abre cada ruta permitida
del rol y una muestra de rutas prohibidas, y guarda la captura de cada una. Lento (≈ 350 pantallas): va en la
suite «regression» y en la completa, no en la de humo.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from utils import config
from utils.api_client import ApiCliente

pytestmark = [pytest.mark.ui, pytest.mark.regression]

RAIZ = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("explorer", RAIZ / "tools" / "explorer.py")
explorer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(explorer)


@pytest.fixture(scope="module")
def ids_ejemplo():
    return explorer.ids_de_ejemplo(ApiCliente(config.ROLES["administrador"]).iniciar())


@pytest.mark.tc("TC-102")
@pytest.mark.parametrize("rol", list(config.ROLES))
def test_tc102_pantallas_del_rol_cargan_sanas(rol, ids_ejemplo):
    """Recorre todas las pantallas permitidas del rol (y una muestra de prohibidas)."""
    inv = json.loads((RAIZ / "docs" / "inventario" / "inventario.json").read_text(encoding="utf-8"))
    hallazgos = explorer.explorar_rol(rol, inv["rutas"], ids_ejemplo)
    salida = RAIZ / "reports" / "explorador"
    salida.mkdir(parents=True, exist_ok=True)
    (salida / f"tc102_{rol}.json").write_text(json.dumps(hallazgos, ensure_ascii=False, indent=1), encoding="utf-8")
    visitadas = [h for h in hallazgos if "url" in h]
    con_problemas = [f"{h['url']}: {'; '.join(h['problemas'])}" for h in hallazgos if h.get("problemas")]
    assert visitadas, f"No se visitó ninguna pantalla de {rol}"
    assert not con_problemas, f"{len(con_problemas)} de {len(visitadas)} pantallas de {rol} con problemas: {con_problemas}"
