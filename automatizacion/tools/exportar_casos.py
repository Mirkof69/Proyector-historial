r"""Exporta los casos de prueba, la matriz de trazabilidad y las coberturas con los resultados de una corrida.

    .venv\Scripts\python tools\exportar_casos.py [--run 20261114-105512]

Salida en docs/: casos_prueba.xlsx (hojas Casos, Trazabilidad, Cobertura), casos_prueba.md,
matriz_trazabilidad.md y cobertura.json (lo usa el Capítulo 6). Nada se escribe a mano: el catálogo sale de
data/catalogo_tc.py, los scripts de los marcadores @pytest.mark.tc, los resultados de results.json y los
defectos de data/defectos.py.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from data.catalogo_tc import CASOS  # noqa: E402
from data.defectos import DEFECTOS  # noqa: E402
from reporting.modelo import cargar  # noqa: E402

DOCS = RAIZ / "docs"
TECNICAS = {"EP": "Partición de equivalencia", "VL": "Valores límite", "TD": "Tabla de decisión",
            "TE": "Transición de estados", "FL": "Flujo / caso de uso", "EX": "Exploratoria", "-": "No aplica"}


def scripts_por_tc() -> dict[str, list[str]]:
    """TC → archivos de prueba que lo implementan (marcador tc o nombre de la grabación .side)."""
    mapa = defaultdict(set)
    for f in sorted((RAIZ / "tests").rglob("test_*.py")):
        rel = f.relative_to(RAIZ).as_posix()
        for tc in re.findall(r'tc\("(TC-\d+)"\)', f.read_text(encoding="utf-8")):
            mapa[tc].add(rel)
    for s in sorted((RAIZ / "selenium_ide").glob("TC-*.side")):
        mapa[s.stem.split("_")[0]].add(f"selenium_ide/{s.name}")
    return {k: sorted(v) for k, v in mapa.items()}


def calcular(run_id: str | None = None) -> dict:
    r = cargar(run_id)
    scripts = scripts_por_tc()
    # casos que reciben su identificador al ejecutarse (pruebas parametrizadas): el archivo sale del resultado
    for c in r.casos:
        archivo = c["nodeid"].split("::")[0].replace("\\", "/")
        if archivo.startswith("tests/") and archivo not in scripts.setdefault(c["tc"], []):
            scripts[c["tc"]] = sorted(set(scripts[c["tc"]]) | {archivo})
    inv = json.loads((DOCS / "inventario" / "inventario.json").read_text(encoding="utf-8"))
    requisitos = inv["requisitos"]["rf"] + inv["requisitos"]["rnf"]
    defectos_tc = defaultdict(list)
    for d in DEFECTOS:
        for tc in str(d.get("caso", "")).replace(",", " ").split():
            defectos_tc[tc].append(d["id"])
    filas = []
    for c in CASOS:
        res = r.por_tc.get(c["id"])
        estado = res["estado"] if res else ("NOT RUN" if c["automatiza"] == "Sí" else "MANUAL")
        filas.append({**c, "scripts": scripts.get(c["id"], []), "estado": estado,
                      "pruebas": len(res["pruebas"]) if res else 0, "defectos": defectos_tc.get(c["id"], []),
                      "evidencias": [ev["codigo"] for p in (res["pruebas"] if res else []) for ev in p["evidencias"]][:3]})
    seleccionados = [f for f in filas if f["automatiza"] == "Sí"]
    implementados = [f for f in seleccionados if f["scripts"]]
    por_req = defaultdict(list)
    for f in filas:
        por_req[f["requisito"]].append(f)
    traz = []
    for q in requisitos:
        casos = por_req.get(q["id"], [])
        estados = Counter(f["estado"] for f in casos)
        traz.append({"id": q["id"], "descripcion": q["descripcion"], "casos": [f["id"] for f in casos],
                     "automatizados": [f["id"] for f in casos if f["scripts"]],
                     "defectos": sorted({d for f in casos for d in f["defectos"]}),
                     "resultado": ("Sin casos" if not casos else "FAIL" if estados["FAIL"] else
                                   "PASS" if estados["PASS"] and not estados["NOT RUN"] and not estados["BLOCKED"]
                                   else "Parcial" if estados["PASS"] else "Sin ejecutar"), "estados": dict(estados)})
    rf = [t for t in traz if t["id"].startswith("RF-")]
    rnf = [t for t in traz if t["id"].startswith("RNF-")]
    cob = {
        "run_id": r.run_id, "casos_diseñados": len(filas), "seleccionados_automatizar": len(seleccionados),
        "automatizados": len(implementados), "pendientes_automatizar": [f["id"] for f in seleccionados if not f["scripts"]],
        "cobertura_automatizacion_pct": round(100 * len(implementados) / len(seleccionados), 1),
        "manuales": len(filas) - len(seleccionados),
        "rf_total": len(rf), "rf_con_casos": sum(bool(t["casos"]) for t in rf),
        "rf_sin_casos": [t["id"] for t in rf if not t["casos"]],
        "rnf_total": len(rnf), "rnf_con_casos": sum(bool(t["casos"]) for t in rnf),
        "rnf_sin_casos": [t["id"] for t in rnf if not t["casos"]],
        "cobertura_requisitos_pct": round(100 * sum(bool(t["casos"]) for t in rf + rnf) / len(rf + rnf), 1),
        "estados_tc": dict(Counter(f["estado"] for f in filas)),
        "pruebas": r.totales, "exito_pruebas_pct": r.tasa_exito,
        "por_tecnica": dict(Counter(TECNICAS.get(f["tecnica"], f["tecnica"]) for f in filas)),
        "por_herramienta": dict(Counter(f["herramienta"] for f in filas)),
        "por_modulo": {m: dict(Counter(f["estado"] for f in filas if f["modulo"] == m))
                       for m in dict.fromkeys(f["modulo"] for f in filas)},
    }
    return {"filas": filas, "trazabilidad": traz, "cobertura": cob}


def _hoja(wb, titulo, encabezados, filas, anchos):
    ws = wb.create_sheet(titulo)
    ws.append(encabezados)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for f in filas:
        ws.append(f)
    for i, a in enumerate(anchos, 1):
        ws.column_dimensions[get_column_letter(i)].width = a
    for fila in ws.iter_rows(min_row=2):
        for c in fila:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    return ws


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run")
    a = ap.parse_args()
    d = calcular(a.run)
    filas, traz, cob = d["filas"], d["trazabilidad"], d["cobertura"]
    wb = Workbook()
    wb.remove(wb.active)
    _hoja(wb, "Casos", ["ID", "Módulo", "Funcionalidad", "Título", "Requisito", "Prioridad", "Tipo", "Técnica",
                         "Precondiciones", "Datos de prueba", "Pasos", "Resultado esperado", "¿Se automatiza?",
                         "Herramienta", "Justificación", "Script", "Estado", "Defectos", "Evidencias", "Origen"],
          [[f["id"], f["modulo"], f["funcionalidad"], f["titulo"], f["requisito"], f["prioridad"], f["tipo"],
            TECNICAS.get(f["tecnica"], f["tecnica"]), f["precondiciones"], f["datos"], f["pasos"], f["esperado"],
            f["automatiza"], f["herramienta"], f["justificacion"], "\n".join(f["scripts"]), f["estado"],
            ", ".join(f["defectos"]), ", ".join(f["evidencias"]), f["origen"]] for f in filas],
          [9, 18, 22, 44, 10, 10, 12, 20, 30, 30, 50, 44, 12, 20, 40, 38, 11, 14, 34, 10])
    _hoja(wb, "Trazabilidad", ["Requisito", "Descripción", "Casos", "Casos automatizados", "Defectos", "Resultado"],
          [[t["id"], t["descripcion"], ", ".join(t["casos"]), ", ".join(t["automatizados"]), ", ".join(t["defectos"]),
            t["resultado"]] for t in traz], [11, 70, 40, 40, 18, 14])
    _hoja(wb, "Cobertura", ["Indicador", "Valor", "Base de cálculo"], [
        ["Casos diseñados", cob["casos_diseñados"], "data/catalogo_tc.py"],
        ["Casos seleccionados para automatizar", cob["seleccionados_automatizar"], "columna «¿Se automatiza?» = Sí"],
        ["Casos automatizados (con script)", cob["automatizados"], "marcadores @pytest.mark.tc y grabaciones .side"],
        ["Cobertura de automatización", f"{cob['cobertura_automatizacion_pct']} %", "automatizados / seleccionados × 100"],
        ["Requisitos con al menos un caso", f"{cob['rf_con_casos'] + cob['rnf_con_casos']} de {cob['rf_total'] + cob['rnf_total']}",
         "RF y RNF de docs/sistema"],
        ["Cobertura de requisitos", f"{cob['cobertura_requisitos_pct']} %", "requisitos con caso / requisitos × 100"],
        ["Pruebas ejecutadas con éxito", f"{cob['exito_pruebas_pct']} %", f"PASS / (PASS + FAIL) de la corrida {cob['run_id']}"],
    ], [42, 18, 60])
    wb.save(DOCS / "casos_prueba.xlsx")

    L = ["# Casos de prueba", "", f"{len(filas)} casos. Estado según la corrida `{cob['run_id']}`.", "",
         "| ID | Módulo | Título | Requisito | Prioridad | Técnica | Automatiza | Herramienta | Estado |",
         "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {f['id']} | {f['modulo']} | {f['titulo']} | {f['requisito']} | {f['prioridad']} | "
          f"{TECNICAS.get(f['tecnica'], f['tecnica'])} | {f['automatiza']} | {f['herramienta']} | {f['estado']} |" for f in filas]
    (DOCS / "casos_prueba.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    L = ["# Matriz de trazabilidad", "", "Requisito → casos → scripts → defectos → resultado "
         f"(corrida `{cob['run_id']}`).", "", "| Requisito | Casos | Automatizados | Defectos | Resultado |", "|---|---|---|---|---|"]
    L += [f"| {t['id']} | {', '.join(t['casos']) or '—'} | {', '.join(t['automatizados']) or '—'} | "
          f"{', '.join(t['defectos']) or '—'} | {t['resultado']} |" for t in traz]
    (DOCS / "matriz_trazabilidad.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    (DOCS / "cobertura.json").write_text(json.dumps(cob, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in cob.items() if k not in ("por_modulo",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
