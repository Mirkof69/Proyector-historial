"""Carga concurrente sobre la API: N usuarios a la vez durante T segundos.

    python quality-assurance/prueba_concurrencia.py --usuarios 30 --segundos 60 [--base http://127.0.0.1:8000]
    python quality-assurance/prueba_concurrencia.py --usuarios 40 --segundos 90 --pausa 2 6   # uso realista

Cada usuario inicia sesión y recorre en bucle los listados que usa una
clínica (pacientes, búsqueda, embarazos, controles, ecografías, laboratorio,
citas, partos). Sin `--pausa` cada usuario dispara sin respiro (prueba de
saturación); con `--pausa MIN MAX` espera entre pantallas como una persona
que lee (prueba de uso realista). Reporta peticiones por segundo, mediana, percentil 95 y
errores, y lo guarda en `reports/concurrencia_api.json`.

Referencia de volumen: 100 pacientes al día con ~15 pantallas cada una son
~1.500 peticiones en 8 horas, es decir 0,05 por segundo. Esta prueba exige
cientos de veces eso.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import threading
import time
from pathlib import Path

from medir_latencia_api import iniciar_sesion, percentil

AQUI = Path(__file__).resolve().parent
RUTAS = [
    "/api/pacientes/?page=1&page_size=20", "/api/pacientes/?search=mamani&page=1&page_size=20",
    "/api/embarazos/?page=1&page_size=20", "/api/controles/?page=1&page_size=20",
    "/api/ecografias/?page=1&page_size=20", "/api/laboratorios/examenes/?page=1&page_size=20",
    "/api/citas/?page=1&page_size=20", "/api/partos/?page=1&page_size=20", "/api/reportes/dashboard-kpis/",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--usuarios", type=int, default=30)
    ap.add_argument("--segundos", type=int, default=60)
    ap.add_argument("--pausa", type=float, nargs=2, default=None, metavar=("MIN", "MAX"),
                    help="segundos de espera entre pantallas (uso realista)")
    ap.add_argument("--email", default="dra.garcia@fetalmedical.bo")
    ap.add_argument("--clave", default="Demo2026!")
    a = ap.parse_args()

    tiempos: list[float] = []
    errores: list[str] = []
    cerrojo = threading.Lock()
    fin = time.time() + a.segundos

    def usuario(n: int) -> None:
        sesion = iniciar_sesion(a.base, a.email, a.clave)
        rng = random.Random(n)
        while time.time() < fin:
            ruta = rng.choice(RUTAS)
            t0 = time.perf_counter()
            try:
                r = sesion.get(a.base + ruta, timeout=30)
                ok = r.status_code == 200
            except Exception as e:  # noqa: BLE001
                ok, r = False, e
            ms = (time.perf_counter() - t0) * 1000
            with cerrojo:
                tiempos.append(ms)
                if not ok:
                    errores.append(f"{ruta}: {getattr(r, 'status_code', r)}")
            if a.pausa:
                time.sleep(rng.uniform(*a.pausa))

    hilos = [threading.Thread(target=usuario, args=(i,)) for i in range(a.usuarios)]
    inicio = time.time()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    duracion = time.time() - inicio
    resumen = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "base": a.base, "usuarios": a.usuarios,
               "pausa_s": a.pausa,
               "segundos": round(duracion, 1), "peticiones": len(tiempos),
               "peticiones_por_segundo": round(len(tiempos) / duracion, 1),
               "mediana_ms": round(statistics.median(tiempos), 1), "p95_ms": round(percentil(tiempos, 0.95), 1),
               "max_ms": round(max(tiempos), 1), "errores": len(errores), "ejemplos_error": errores[:5]}
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    (AQUI / "reports").mkdir(exist_ok=True)
    (AQUI / "reports" / "concurrencia_api.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                                                            encoding="utf-8")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
