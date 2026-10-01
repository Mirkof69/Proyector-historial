"""Mide la latencia de la API con la base de demostración (3.200 pacientes).

    python quality-assurance/medir_latencia_api.py [--repeticiones 30] [--base http://localhost:8000]

Inicia sesión como la médica de demostración y pide cada listado igual que
la pantalla (primera página de 20, con su `resumen` y una búsqueda), N veces.
Reporta mediana, percentil 95 y máximo por endpoint, y escribe
`quality-assurance/reports/latencia_api.json`. Meta (RNF-01): percentil 95
por debajo de 200 ms en el servidor del hospital.

Lo medido aquí es el equipo de desarrollo; en el servidor definitivo hay que
volver a correrlo.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
META_MS = 200

ENDPOINTS = [
    ("Pacientes", "/api/pacientes/?page=1&page_size=20"),
    ("Pacientes · resumen", "/api/pacientes/resumen/"),
    ("Pacientes · búsqueda", "/api/pacientes/?search=quispe&page=1&page_size=20"),
    ("Embarazos", "/api/embarazos/?page=1&page_size=20"),
    ("Embarazos · resumen", "/api/embarazos/resumen/"),
    ("Controles", "/api/controles/?page=1&page_size=20"),
    ("Ecografías", "/api/ecografias/?page=1&page_size=20"),
    ("Laboratorio", "/api/laboratorios/examenes/?page=1&page_size=20"),
    ("Laboratorio · resumen", "/api/laboratorios/examenes/resumen/"),
    ("Vacunas", "/api/vacunas/registros/?page=1&page_size=20"),
    ("Citas", "/api/citas/?page=1&page_size=20"),
    ("Partos", "/api/partos/?page=1&page_size=20"),
    ("Notas de evolución", "/api/notas-evolucion/?page=1&page_size=20"),
    ("Triaje", "/api/triaje/?page=1&page_size=20"),
    ("Dashboard KPIs", "/api/reportes/dashboard-kpis/"),
    ("Reporte natalidad (mes)", "/api/reportes/natalidad/"),
]


def iniciar_sesion(base: str, email: str, clave: str) -> requests.Session:
    s = requests.Session()
    s.get(f"{base}/api/token/csrf/", timeout=10)
    token = s.cookies.get("csrftoken", "")
    r = s.post(f"{base}/api/usuarios/login/", json={"email": email, "password": clave},
               headers={"X-CSRFToken": token, "Referer": base}, timeout=15)
    r.raise_for_status()
    return s


def percentil(valores: list[float], p: float) -> float:
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * p
    i = int(k)
    return ordenados[i] + (ordenados[min(i + 1, len(ordenados) - 1)] - ordenados[i]) * (k - i)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--repeticiones", type=int, default=30)
    ap.add_argument("--email", default=os.environ.get("DEMO_EMAIL", "dra.garcia@fetalmedical.bo"))
    ap.add_argument("--clave", default=os.environ.get("DEMO_CLAVE", "Demo2026!"))
    a = ap.parse_args()

    sesion = iniciar_sesion(a.base, a.email, a.clave)
    filas = []
    for nombre, ruta in ENDPOINTS:
        r = sesion.get(a.base + ruta, timeout=30)  # calentamiento (y comprobar que responde)
        if r.status_code != 200:
            filas.append({"endpoint": nombre, "ruta": ruta, "error": f"HTTP {r.status_code}"})
            continue
        tiempos = []
        for _ in range(a.repeticiones):
            t0 = time.perf_counter()
            sesion.get(a.base + ruta, timeout=30)
            tiempos.append((time.perf_counter() - t0) * 1000)
        filas.append({"endpoint": nombre, "ruta": ruta, "mediana_ms": round(statistics.median(tiempos), 1),
                      "p95_ms": round(percentil(tiempos, 0.95), 1), "max_ms": round(max(tiempos), 1),
                      "cumple_meta": percentil(tiempos, 0.95) < META_MS})

    ancho = max(len(f["endpoint"]) for f in filas)
    print(f"{'Endpoint':<{ancho}}  mediana    p95    máx  meta <{META_MS} ms")
    for f in filas:
        if "error" in f:
            print(f"{f['endpoint']:<{ancho}}  {f['error']}")
        else:
            print(f"{f['endpoint']:<{ancho}}  {f['mediana_ms']:7.1f} {f['p95_ms']:6.1f} {f['max_ms']:6.1f}  "
                  f"{'sí' if f['cumple_meta'] else 'NO'}")
    medidos = [f for f in filas if "error" not in f]
    resumen = {"fecha": time.strftime("%Y-%m-%d %H:%M"), "base": a.base, "repeticiones": a.repeticiones,
               "meta_p95_ms": META_MS, "cumplen": sum(f["cumple_meta"] for f in medidos), "total": len(medidos),
               "errores": [f for f in filas if "error" in f], "endpoints": filas}
    (AQUI / "reports").mkdir(exist_ok=True)
    (AQUI / "reports" / "latencia_api.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{resumen['cumplen']} de {resumen['total']} endpoints con p95 < {META_MS} ms. "
          f"Errores: {len(resumen['errores'])}")
    return 0 if not resumen["errores"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
