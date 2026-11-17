r"""Tareas de IA sobre una corrida. Cada salida es una SUGERENCIA para el analista y queda rotulada como tal.

    .venv\Scripts\python -m ai.tareas estado
    .venv\Scripts\python -m ai.tareas resumen [--run ID]      -> reports/<run>/ia_resumen.json
    .venv\Scripts\python -m ai.tareas fallos  [--run ID]      -> reports/<run>/ia_fallos.json
    .venv\Scripts\python -m ai.tareas gherkin "RF-12 Registrar control prenatal ..."
    .venv\Scripts\python -m ai.tareas localizador archivo.html "botón Guardar Control"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ai import servicio
from reporting.modelo import cargar

BASE = ("Eres analista de QA de un sistema web de historia clínica obstétrica (React + Django REST). Respondes en "
        "español, breve y concreto. Solo usas los datos que recibes: si algo no está, dices que no hay datos. "
        "No decides si una prueba pasó o falló: eso ya lo decidió su aserción.")


def resumen_ejecutivo(run_id: str | None = None) -> dict:
    r = cargar(run_id)
    datos = {"totales": r.totales, "exito_sobre_ejecutadas_pct": r.tasa_exito, "por_modulo": r.por_modulo,
             "fallos": [{"tc": c["tc"], "prueba": c["nombre"], "modulo": c["modulo"], "error": c["error"][:300],
                         "clasificacion": c["clasificacion"]} for c in r.fallos[:25]],
             "rendimiento": [{k: v for k, v in x.items() if k != "por_endpoint"} for x in r.rendimiento],
             "no_ejecutadas": [{"tc": c["tc"], "motivo": c["error"][:120]} for c in r.casos
                               if c["estado"] in ("BLOCKED", "NOT RUN")][:15]}
    s = servicio.consultar("resumen_ejecutivo", BASE + " Redacta un resumen ejecutivo de 120 a 180 palabras para "
                           "el responsable del proyecto: estado general con sus cifras, módulos con fallos, riesgo "
                           "principal y siguiente paso. Sin viñetas ni títulos.",
                           json.dumps(datos, ensure_ascii=False))
    if s["disponible"]:
        (r.dir_run / "ia_resumen.json").write_text(json.dumps(
            {"resumen": s["texto"], "proveedor": s["proveedor"], "modelo": s["modelo"]}, ensure_ascii=False, indent=1),
            encoding="utf-8")
    return s


def analizar_fallos(run_id: str | None = None, maximo: int = 20) -> dict:
    r = cargar(run_id)
    salida, ultimo = [], {"disponible": True, "motivo": "", "texto": ""}
    for c in r.fallos[:maximo]:
        contenido = json.dumps({"caso": c["tc"], "prueba": c["nombre"], "error": c["error"],
                                "traza": c["traceback"][-1500:], "consola_navegador": c.get("consola", [])[:5],
                                "clasificacion_inicial": c["clasificacion"]}, ensure_ascii=False)
        ultimo = servicio.consultar("analisis_fallo", BASE + " Analiza este fallo en 3 líneas: (1) causa probable; "
                                    "(2) si parece defecto del sistema, del script, de los datos o del ambiente y por "
                                    "qué; (3) severidad sugerida (Crítica, Alta, Media, Baja) y qué revisar primero.",
                                    contenido)
        if not ultimo["disponible"]:
            break
        salida.append({"nodeid": c["nodeid"], "tc": c["tc"], "texto": ultimo["texto"],
                       "proveedor": ultimo["proveedor"], "modelo": ultimo["modelo"]})
    if salida:
        (r.dir_run / "ia_fallos.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    return {**ultimo, "texto": "", "analizados": len(salida), "fallos": len(r.fallos)}


def escenarios_gherkin(requisito: str) -> dict:
    return servicio.consultar("escenarios_gherkin", BASE + " A partir del requisito, propone de 4 a 6 escenarios "
                              "Gherkin (Dado/Cuando/Entonces) en español: camino feliz, validaciones, valores límite "
                              "y permisos por rol. Son propuestas para revisión del analista.", requisito)


def sugerir_localizador(html: str, elemento: str) -> dict:
    return servicio.consultar("sugerir_localizador", BASE + " Recibes un fragmento de HTML y la descripción de un "
                              "elemento. Propón hasta 3 localizadores de Selenium en orden de preferencia "
                              "(data-testid, id, name, CSS, XPath relativo) y di cuál es más estable y por qué.",
                              f"Elemento buscado: {elemento}\n\nHTML:\n{html[:8000]}")


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("tarea", choices=["estado", "resumen", "fallos", "gherkin", "localizador"])
    ap.add_argument("argumentos", nargs="*")
    ap.add_argument("--run")
    a = ap.parse_args()
    if a.tarea == "estado":
        r = servicio.estado()
    elif a.tarea == "resumen":
        r = resumen_ejecutivo(a.run)
    elif a.tarea == "fallos":
        r = analizar_fallos(a.run)
    elif a.tarea == "gherkin":
        r = escenarios_gherkin(" ".join(a.argumentos))
    else:
        r = sugerir_localizador(Path(a.argumentos[0]).read_text(encoding="utf-8", errors="ignore"),
                                " ".join(a.argumentos[1:]))
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
