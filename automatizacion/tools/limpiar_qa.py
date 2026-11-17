r"""Limpia los datos sintéticos QA que una corrida interrumpida dejó activos.

    .venv\Scripts\python tools\limpiar_qa.py [--solo-contar]

Da de baja (baja lógica) a las pacientes cuyo nombre empieza con «QA » y cuya cédula empieza con 99, y cancela
las citas agendadas cuyo motivo empieza con «QA». Nunca toca un registro que no cumpla las dos marcas.
Una corrida normal ya limpia al terminar (fixture limpieza_qa); esto cubre las canceladas.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import config  # noqa: E402
from utils.api_client import ApiCliente  # noqa: E402


def _todas(api: ApiCliente, ruta: str, **params) -> list[dict]:
    filas, pagina = [], 1
    while True:
        r = api.get(ruta, params={**params, "page_size": 100, "page": pagina}).json()
        filas += r.get("results", []) if isinstance(r, dict) else r
        if not isinstance(r, dict) or not r.get("next"):
            return filas
        pagina += 1


def limpiar(solo_contar: bool = False) -> dict:
    admin = ApiCliente(config.ROLES["administrador"]).iniciar()
    pacientes = [p for p in _todas(admin, "/pacientes/", search=config.PREFIJO_DATOS)
                 if str(p.get("nombre", "")).startswith(f"{config.PREFIJO_DATOS} ") and str(p.get("ci", "")).startswith("99")
                 and p.get("activo")]
    citas = [c for c in _todas(admin, "/citas/citas/", search=config.PREFIJO_DATOS)
             if str(c.get("motivo", "")).startswith(config.PREFIJO_DATOS) and c.get("estado") == "agendada"]
    hechas = {"pacientes_activas": len(pacientes), "citas_agendadas": len(citas), "bajas": 0, "canceladas": 0}
    if solo_contar:
        return hechas
    for c in citas:
        if admin.post(f"/citas/citas/{c['id']}/cancelar/", {"motivo": "Limpieza de datos QA"}).status_code < 400:
            hechas["canceladas"] += 1
    for p in pacientes:
        if admin.delete(f"/pacientes/{p['id']}/").status_code < 400:
            hechas["bajas"] += 1
    return hechas


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-contar", action="store_true")
    print(limpiar(ap.parse_args().solo_contar))
