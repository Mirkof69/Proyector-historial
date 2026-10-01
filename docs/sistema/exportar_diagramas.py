"""Exporta cada diagrama Mermaid de esta carpeta a SVG en diagramas/.

    python docs/sistema/exportar_diagramas.py

Necesita mermaid-cli (`npm install @mermaid-js/mermaid-cli`) y un Chrome o
Chromium; la ruta del navegador se pasa con MERMAID_CHROME y la de `mmdc` con
MERMAID_CLI. Si un diagrama tiene un error de sintaxis, el script lo dice y
termina con código 1.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "diagramas"
BLOQUE = re.compile(r"```mermaid\n(.*?)```", re.S)


def main() -> int:
    mmdc = os.environ.get("MERMAID_CLI", "mmdc")
    chrome = os.environ.get("MERMAID_CHROME")
    SALIDA.mkdir(exist_ok=True)
    config = Path(tempfile.mkstemp(suffix=".json")[1])
    config.write_text(json.dumps({"executablePath": chrome} if chrome else {}), encoding="utf-8")
    errores, hechos = [], 0
    for doc in sorted(AQUI.glob("[0-9][0-9]_*.md")):
        for n, codigo in enumerate(BLOQUE.findall(doc.read_text(encoding="utf-8")), 1):
            nombre = f"{doc.stem}_{n}"
            fuente = Path(tempfile.mkstemp(suffix=".mmd")[1])
            fuente.write_text(codigo, encoding="utf-8")
            r = subprocess.run([mmdc, "-i", str(fuente), "-o", str(SALIDA / f"{nombre}.svg"),
                                "-p", str(config), "-b", "white", "-q"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", shell=os.name == "nt")
            if r.returncode or not (SALIDA / f"{nombre}.svg").exists():
                errores.append(f"{nombre}: {(r.stderr or r.stdout).strip().splitlines()[-1:] }")
            else:
                hechos += 1
    print(f"{hechos} diagramas exportados a {SALIDA}")
    for e in errores:
        print("ERROR", e)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
