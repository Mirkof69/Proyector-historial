"""Genera docs/defectos/BUG-XXX.md y docs/defectos/registro_defectos.csv desde data/defectos.py."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from data.defectos import DEFECTOS  # noqa: E402

DESTINO = RAIZ / "docs" / "defectos"
CAMPOS = ["id", "titulo", "modulo", "pantalla_endpoint", "pasos", "esperado", "obtenido", "severidad", "prioridad",
          "estado", "responsable", "caso", "evidencia", "causa_raiz", "detectado_por", "correccion", "commit",
          "fecha_correccion", "retesting", "regresion"]


def principal():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for d in DEFECTOS:
        L = [f"# {d['id']} · {d['titulo']}", "",
             "| Campo | Valor |", "|---|---|"]
        for etiqueta, clave in (("Módulo", "modulo"), ("Pantalla / endpoint", "pantalla_endpoint"),
                                ("Severidad", "severidad"), ("Prioridad", "prioridad"), ("Estado", "estado"),
                                ("Responsable", "responsable"), ("Caso relacionado", "caso"),
                                ("Detectado por", "detectado_por")):
            L.append(f"| {etiqueta} | {d.get(clave, '')} |")
        L += ["", "## Pasos para reproducir", "", d["pasos"], "", "## Resultado esperado", "", d["esperado"], "",
              "## Resultado obtenido", "", d["obtenido"], "", "## Causa raíz", "", d["causa_raiz"], "",
              "## Evidencia", "", d["evidencia"], ""]
        if d.get("correccion"):
            L += ["## Corrección", "", d["correccion"], "", f"- Commit: `{d.get('commit', '')}`",
                  f"- Fecha: {d.get('fecha_correccion', '')}", "", "## Retesting", "", d.get("retesting", ""), "",
                  "## Regresión", "", d.get("regresion", ""), ""]
        (DESTINO / f"{d['id']}.md").write_text("\n".join(L), encoding="utf-8")
    with open(DESTINO / "registro_defectos.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, extrasaction="ignore")
        w.writeheader()
        for d in DEFECTOS:
            w.writerow({k: d.get(k, "") for k in CAMPOS})
    print(f"{len(DEFECTOS)} defectos escritos en {DESTINO}")


if __name__ == "__main__":
    principal()
