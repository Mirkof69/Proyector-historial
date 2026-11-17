r"""Reproduce una grabación y muestra el final de la salida del ejecutor (para depurar un caso).

    .venv\Scripts\python tools\ver_side.py selenium_ide\TC-111_buscar_pacientes.side
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ejecutar_side  # noqa: E402

for ruta in sys.argv[1:]:
    r = ejecutar_side.reproducir(Path(ruta))
    lineas = [x for x in r["salida"].splitlines() if x.strip() and not x.strip().startswith("at ")
              and "Deprecation" not in x and "trace-deprecation" not in x]
    print(f"== {r['archivo']}: {r['estado']} en {r['duracion_s']} s")
    if r["estado"] != "PASS":
        print("\n".join(lineas[-22:]))
