r"""Genera los proyectos de Selenium IDE (formato 2.0) a partir de data/casos_ide.py.

    .venv\Scripts\python tools\generar_side.py

Escribe en selenium_ide/:
  - un proyecto por caso (TC-XXX_<nombre>.side), que es lo que reproduce tools/ejecutar_side.py;
  - FetalMedical_SeleniumIDE.side, con todos los casos en un solo proyecto y una suite por módulo, para abrirlo en
    la extensión Selenium IDE y verlos organizados.
Las credenciales no se escriben: quedan como marcadores que el ejecutor reemplaza en una copia temporal.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from data.casos_ide import CASOS_IDE  # noqa: E402

SALIDA = RAIZ / "selenium_ide"
URL = "http://localhost:3000"
COMPLETO = "FetalMedical_SeleniumIDE.side"


def _id(*partes: str) -> str:
    """Identificador estable: regenerar no cambia los archivos si el caso no cambió."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "fetal-medical/" + "/".join(partes)))


def _prueba(caso: dict) -> dict:
    return {"id": _id(caso["id"]), "name": f"{caso['id']} {caso['titulo']}",
            "commands": [{"id": _id(caso["id"], str(i)), "comment": x["comment"], "command": x["command"],
                          "target": x["target"], "targets": [], "value": x["value"]} for i, x in enumerate(caso["comandos"])]}


def _proyecto(nombre: str, pruebas: list[dict], suites: list[dict]) -> dict:
    return {"id": _id("proyecto", nombre), "version": "2.0", "name": nombre, "url": URL, "tests": pruebas,
            "suites": suites, "urls": [URL + "/"], "plugins": []}


def _suite(nombre: str, pruebas: list[dict]) -> dict:
    return {"id": _id("suite", nombre), "name": nombre, "persistSession": False, "parallel": False, "timeout": 300,
            "tests": [p["id"] for p in pruebas]}


def principal():
    SALIDA.mkdir(exist_ok=True)
    vigentes = {COMPLETO}
    por_modulo: dict[str, list[dict]] = {}
    for caso in CASOS_IDE:
        prueba = _prueba(caso)
        archivo = f"{caso['id']}_{caso['archivo']}.side"
        vigentes.add(archivo)
        (SALIDA / archivo).write_text(json.dumps(_proyecto(f"Fetal Medical - {caso['id']}", [prueba], [_suite(caso["id"], [prueba])]),
                                                 ensure_ascii=False, indent=2), encoding="utf-8")
        por_modulo.setdefault(caso["modulo"], []).append(prueba)
    todas = [p for ps in por_modulo.values() for p in ps]
    (SALIDA / COMPLETO).write_text(json.dumps(_proyecto("Fetal Medical Bolivia - Selenium IDE", todas,
                                                        [_suite(m, ps) for m, ps in por_modulo.items()]),
                                              ensure_ascii=False, indent=2), encoding="utf-8")
    sobrantes = [f for f in SALIDA.glob("*.side") if f.name not in vigentes]
    for f in sobrantes:
        f.unlink()
    comandos = sum(len(c["comandos"]) for c in CASOS_IDE)
    print(f"{len(CASOS_IDE)} casos, {comandos} comandos, {len(por_modulo)} suites; retirados: {[f.name for f in sobrantes]}")


if __name__ == "__main__":
    principal()
