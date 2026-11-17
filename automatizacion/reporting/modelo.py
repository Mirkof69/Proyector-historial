"""Modelo único del reporte de una ejecución: lo usan el HTML, el Word/PDF, el correo y la interfaz web.

Junta reports/<run_id>/results.json con el catálogo de casos (módulo, título, prioridad), el registro de defectos
y los resúmenes de Locust. No calcula nada que no esté en esos archivos.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from data.catalogo_tc import CASOS
from data.defectos import DEFECTOS
from utils import config

DIR_REPORTES = config.RAIZ / "reports"
ESTADOS = ("PASS", "FAIL", "BLOCKED", "NOT RUN")


@dataclass
class Reporte:
    run_id: str
    dir_run: Path
    datos: dict
    casos: list[dict] = field(default_factory=list)
    por_tc: dict[str, dict] = field(default_factory=dict)
    por_modulo: list[dict] = field(default_factory=list)
    rendimiento: list[dict] = field(default_factory=list)
    defectos: list[dict] = field(default_factory=list)
    clasificacion_fallos: dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------ cifras
    @property
    def totales(self) -> dict:
        return self.datos["totales"]

    @property
    def ejecutadas(self) -> int:
        return self.totales["PASS"] + self.totales["FAIL"]

    @property
    def tasa_exito(self) -> float:
        """Pruebas que pasaron sobre las ejecutadas (las BLOCKED y NOT RUN no se ejecutaron)."""
        return round(100 * self.totales["PASS"] / self.ejecutadas, 1) if self.ejecutadas else 0.0

    @property
    def tcs_con_resultado(self) -> dict[str, int]:
        return dict(Counter(t["estado"] for t in self.por_tc.values()))

    @property
    def cobertura_catalogo(self) -> dict:
        automatizables = [c["id"] for c in CASOS if c["automatiza"] == "Sí"]
        ejecutados = [tc for tc in automatizables if tc in self.por_tc and self.por_tc[tc]["estado"] in ("PASS", "FAIL")]
        return {"catalogo": len(CASOS), "automatizables": len(automatizables), "ejecutados": len(ejecutados),
                "pct": round(100 * len(ejecutados) / len(automatizables), 1) if automatizables else 0.0,
                "sin_ejecutar": [tc for tc in automatizables if tc not in ejecutados]}

    @property
    def fallos(self) -> list[dict]:
        return [c for c in self.casos if c["estado"] == "FAIL"]

    @property
    def duracion_legible(self) -> str:
        s = int(self.datos.get("duracion_s", 0))
        return f"{s // 3600} h {s % 3600 // 60} min" if s >= 3600 else f"{s // 60} min {s % 60} s"


def _estado_tc(estados: list[str]) -> str:
    """Estado del caso a partir de sus pruebas: un FAIL basta; PASS solo si todas pasaron."""
    for e in ("FAIL", "BLOCKED"):
        if e in estados:
            return e
    if "PASS" in estados:
        return "PASS"
    return "NOT RUN"


def cargar(run_id: str | None = None) -> Reporte:
    if not run_id:
        candidatas = sorted((p for p in DIR_REPORTES.iterdir() if (p / "results.json").exists()), reverse=True)
        if not candidatas:
            raise FileNotFoundError("No hay corridas en reports/")
        run_id = candidatas[0].name
    dir_run = DIR_REPORTES / run_id
    datos = json.loads((dir_run / "results.json").read_text(encoding="utf-8"))
    catalogo = {c["id"]: c for c in CASOS}
    defectos_por_tc = defaultdict(list)
    for d in DEFECTOS:
        for tc in str(d.get("caso", "")).replace(",", " ").split():
            defectos_por_tc[tc].append(d["id"])

    casos = []
    for c in datos["casos"]:
        info = catalogo.get(c["tc"], {})
        casos.append({**c, "modulo": info.get("modulo", "Configuración"), "titulo_tc": info.get("titulo", c["nombre"]),
                      "prioridad": info.get("prioridad", ""), "tipo": info.get("tipo", ""),
                      "tecnica": info.get("tecnica", ""), "herramienta": info.get("herramienta", ""),
                      "defectos": defectos_por_tc.get(c["tc"], [])})

    por_tc: dict[str, dict] = {}
    for c in casos:
        t = por_tc.setdefault(c["tc"], {"tc": c["tc"], "titulo": c["titulo_tc"], "modulo": c["modulo"],
                                         "prioridad": c["prioridad"], "pruebas": [], "defectos": c["defectos"]})
        t["pruebas"].append(c)
    for t in por_tc.values():
        t["estado"] = _estado_tc([p["estado"] for p in t["pruebas"]])
        t["duracion_s"] = round(sum(p["duracion_s"] for p in t["pruebas"]), 2)

    modulos = defaultdict(lambda: Counter())
    for c in casos:
        modulos[c["modulo"]][c["estado"]] += 1
    por_modulo = []
    for nombre, cont in sorted(modulos.items()):
        ejec = cont["PASS"] + cont["FAIL"]
        por_modulo.append({"modulo": nombre, **{e: cont[e] for e in ESTADOS}, "total": sum(cont.values()),
                           "tasa": round(100 * cont["PASS"] / ejec, 1) if ejec else 0.0})

    rendimiento = []
    for archivo in sorted((dir_run / "locust").glob("*_resumen.json")) if (dir_run / "locust").exists() else []:
        rendimiento.append(json.loads(archivo.read_text(encoding="utf-8")))

    tcs_ejecutados = set(por_tc)
    defectos = [{**d, "visto_en_corrida": any(tc in tcs_ejecutados for tc in str(d.get("caso", "")).split())}
                for d in DEFECTOS]
    return Reporte(run_id=run_id, dir_run=dir_run, datos=datos, casos=casos, por_tc=por_tc, por_modulo=por_modulo,
                   rendimiento=rendimiento, defectos=defectos,
                   clasificacion_fallos=dict(Counter(c["clasificacion"] or "sin clasificar" for c in casos
                                                     if c["estado"] == "FAIL")))


def corridas(limite: int = 50) -> list[dict]:
    """Resumen de las últimas corridas (para la interfaz web y el historial)."""
    salida = []
    for p in sorted((x for x in DIR_REPORTES.iterdir() if (x / "results.json").exists()), reverse=True)[:limite]:
        try:
            d = json.loads((p / "results.json").read_text(encoding="utf-8"))
        except ValueError:
            continue
        salida.append({"run_id": p.name, "suite": d.get("suite", ""), "inicio": d.get("inicio", ""),
                       "duracion_s": d.get("duracion_s", 0), **d["totales"]})
    return salida
