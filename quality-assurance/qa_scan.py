#!/usr/bin/env python3
"""=============================================================================
QA SCANNER — Fetal Medical Bolivia
=============================================================================
Escanea el backend Django módulo por módulo y calcula una puntuación de calidad
por módulo basada en el modelo de calidad de producto ISO/IEC 25010, usando
métricas REALES del código (no estimaciones):

  - Maintainability  : densidad de hallazgos de lint (ruff) por cada 100 LOC
  - Reliability      : presencia de tests + cobertura del módulo
  - Security         : hallazgos de bandit (severidad media/alta) por módulo
  - Testability      : ¿tiene suite de tests dedicada?
  - Size/Complexity  : LOC y nº de archivos (contexto)

Salida: quality-assurance/reports/qa_report.json

Uso:
    python quality-assurance/qa_scan.py           # sin cobertura (rápido)
    python quality-assurance/qa_scan.py --coverage  # con cobertura (lento)
=============================================================================
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "Backend"
REPORTS = Path(__file__).resolve().parent / "reports"
REPORTS.mkdir(exist_ok=True)

VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
RUFF = BACKEND / ".venv" / "Scripts" / "ruff.exe"

EXCLUDE_DIRS = {
    ".venv", ".venv_gpu", "node_modules", "__pycache__", "staticfiles",
    "media", "logs", "backups", "frontend", "Microservicio_IA", "docs",
    "scripts", "zip", "_archive", "seeders",
}

# Reglas de ruff que SÍ indican deuda real (se excluye RUF012 y ARG002 que son
# idiomas de Django/DRF, no bugs).
RUFF_REAL = "F,E9,B,SIM,RET,PERF,C4,PIE"


def discover_apps() -> list[str]:
    apps = []
    for d in sorted(os.listdir(BACKEND)):
        p = BACKEND / d
        if not p.is_dir() or d in EXCLUDE_DIRS:
            continue
        if (p / "apps.py").exists() or (p / "models.py").exists():
            apps.append(d)
    return apps


def count_loc_files(app: str) -> tuple[int, int]:
    loc = files = 0
    for root, _, fnames in os.walk(BACKEND / app):
        if "migrations" in root or "__pycache__" in root:
            continue
        for f in fnames:
            if f.endswith(".py"):
                files += 1
                try:
                    loc += sum(1 for _ in open(Path(root) / f, encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
    return loc, files


def has_tests(app: str) -> bool:
    return (BACKEND / app / "tests.py").exists() or (BACKEND / app / "tests").is_dir()


def ruff_findings(app: str) -> int:
    """Nº de hallazgos ruff (reglas de deuda real) en el módulo."""
    try:
        out = subprocess.run(
            [str(RUFF), "check", "--select", RUFF_REAL, "--exclude", "migrations",
             "--output-format", "concise", app],
            cwd=BACKEND, capture_output=True, text=True, timeout=120,
        )
        return sum(1 for ln in out.stdout.splitlines() if f"{app}\\" in ln or f"{app}/" in ln)
    except (subprocess.TimeoutExpired, OSError):
        return -1


def bandit_medium_high(app: str) -> int:
    """Nº de hallazgos bandit de severidad media/alta en el módulo."""
    try:
        out = subprocess.run(
            [str(VENV_PY), "-m", "bandit", "-r", app, "-ll", "-f", "json"],
            cwd=BACKEND, capture_output=True, text=True, timeout=120,
        )
        data = json.loads(out.stdout) if out.stdout.strip().startswith("{") else {"results": []}
        return sum(
            1 for r in data.get("results", [])
            if r.get("issue_severity") in ("MEDIUM", "HIGH")
            and "tests" not in r.get("filename", "")
        )
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        return -1


import ast
import re as _re

# Patrones de baja portabilidad: rutas absolutas y hosts/puertos hardcodeados.
_HARDCODED_PATH = _re.compile(r"[A-Za-z]:\\\\|['\"]/(?:home|Users|var|etc|opt)/")
_HARDCODED_HOST = _re.compile(r"(?:localhost|127\.0\.0\.1|0\.0\.0\.0):\d{2,5}")


def portability_findings(app: str) -> int:
    """Cuenta rutas absolutas y host:puerto hardcodeados (baja portabilidad).
    Se saltan tests y migraciones."""
    n = 0
    for root, _, fnames in os.walk(BACKEND / app):
        if "migrations" in root or "__pycache__" in root:
            continue
        for f in fnames:
            if not f.endswith(".py") or f == "tests.py" or f.startswith("test_"):
                continue
            try:
                txt = (Path(root) / f).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            n += len(_HARDCODED_PATH.findall(txt)) + len(_HARDCODED_HOST.findall(txt))
    return n


def documentation_ratio(app: str) -> float:
    """% de funciones/clases con docstring (proxy de usabilidad para quien
    mantiene el código). Usa AST; ignora tests y migraciones."""
    documented = total = 0
    for root, _, fnames in os.walk(BACKEND / app):
        if "migrations" in root or "__pycache__" in root:
            continue
        for f in fnames:
            if not f.endswith(".py") or f == "tests.py":
                continue
            try:
                tree = ast.parse((Path(root) / f).read_text(encoding="utf-8", errors="ignore"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name.startswith("_"):
                        continue
                    total += 1
                    if ast.get_docstring(node):
                        documented += 1
    return round(documented / total * 100, 1) if total else 100.0


def score(loc: int, tests: bool, ruff_n: int, bandit_n: int, cov: float | None,
          port_n: int = 0, doc_pct: float = 100.0) -> dict:
    """Calcula subpuntuaciones 0-100 por dimensión ISO/IEC 25010 medible."""
    per100 = (ruff_n / loc * 100) if loc else 0
    # Maintainability: 100 si <0.5 hallazgos/100LOC, baja linealmente
    maint = max(0, min(100, round(100 - per100 * 25)))
    # Security: 100 si 0 hallazgos media/alta; -20 por cada uno
    sec = max(0, 100 - (bandit_n * 20 if bandit_n > 0 else 0))
    # Reliability: cobertura real si está disponible, si no presencia de tests
    rel = round(cov) if cov is not None else (70 if tests else 25)
    # Testability
    test_score = 100 if tests else 0
    # Portability: penaliza rutas/hosts hardcodeados por cada 1000 LOC
    port_density = (port_n / loc * 1000) if loc else 0
    portability = max(0, min(100, round(100 - port_density * 8)))
    # Documentation (proxy de Usabilidad/Mantenibilidad para el desarrollador)
    documentation = round(doc_pct)
    overall = round(
        maint * 0.24 + sec * 0.22 + rel * 0.24 + test_score * 0.12
        + portability * 0.09 + documentation * 0.09,
    )
    return {
        "maintainability": maint,
        "security": sec,
        "reliability": rel,
        "testability": test_score,
        "portability": portability,
        "documentation": documentation,
        "overall": overall,
        "ruff_per_100loc": round(per100, 2),
    }


def run_coverage(apps: list[str]) -> dict[str, float]:
    """Corre la suite Django bajo coverage y devuelve el % de líneas cubiertas
    por cada app (profundidad real de los tests, no solo presencia)."""
    print("  Corriendo suite bajo coverage (esto tarda ~4 min)...")
    src = ",".join(apps)
    subprocess.run(
        [str(VENV_PY), "-m", "coverage", "run", f"--source={src}",
         "manage.py", "test", "--verbosity", "0"],
        cwd=BACKEND, capture_output=True, text=True, timeout=1200, check=False,
    )
    cov_json = REPORTS / "coverage.json"
    subprocess.run(
        [str(VENV_PY), "-m", "coverage", "json", "-o", str(cov_json)],
        cwd=BACKEND, capture_output=True, text=True, timeout=120, check=False,
    )
    if not cov_json.exists():
        print("  ⚠ coverage.json no generado; se usa fiabilidad por presencia.")
        return {}
    data = json.loads(cov_json.read_text(encoding="utf-8"))
    agg: dict[str, list[int]] = {a: [0, 0] for a in apps}  # [cubiertas, total]
    for path, info in data.get("files", {}).items():
        norm = path.replace("\\", "/")
        app = norm.split("/")[0]
        if app in agg:
            s = info.get("summary", {})
            agg[app][0] += s.get("covered_lines", 0)
            agg[app][1] += s.get("num_statements", 0)
    return {a: (round(cov / tot * 100, 1) if tot else 0.0) for a, (cov, tot) in agg.items()}


def main() -> None:
    use_cov = "--coverage" in sys.argv
    apps = discover_apps()
    cov_map = run_coverage(apps) if use_cov else {}
    results = []
    for app in apps:
        loc, files = count_loc_files(app)
        tests = has_tests(app)
        ruff_n = ruff_findings(app)
        bandit_n = bandit_medium_high(app)
        cov = cov_map.get(app) if use_cov else None
        port_n = portability_findings(app)
        doc_pct = documentation_ratio(app)
        sc = score(loc, tests, max(ruff_n, 0), max(bandit_n, 0), cov, port_n, doc_pct)
        results.append({
            "module": app, "loc": loc, "files": files, "has_tests": tests,
            "ruff_findings": ruff_n, "bandit_medium_high": bandit_n,
            "coverage_pct": cov, "portability_findings": port_n,
            "documentation_pct": doc_pct, **sc,
        })
        cov_txt = f" cov={cov:>5.1f}%" if cov is not None else ""
        print(f"  {app:<24} overall={sc['overall']:>3}  loc={loc:>5}  tests={'sí' if tests else 'NO'}{cov_txt}")

    results.sort(key=lambda r: r["overall"])
    total_loc = sum(r["loc"] for r in results)
    covs = [r["coverage_pct"] for r in results if r.get("coverage_pct") is not None]
    totals = {
        "modules": len(results),
        "loc": total_loc,
        "modules_without_tests": sum(1 for r in results if not r["has_tests"]),
        "avg_overall": round(sum(r["overall"] for r in results) / len(results)) if results else 0,
        "coverage_mode": use_cov,
    }
    if covs:
        totals["avg_coverage"] = round(sum(covs) / len(covs), 1)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard": "ISO/IEC 25010 (subset medible)",
        "totals": totals,
        "modules": results,
    }
    out = REPORTS / "qa_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReporte: {out}")
    cov_msg = f" · cobertura promedio {totals['avg_coverage']}%" if "avg_coverage" in totals else ""
    print(f"Promedio global: {totals['avg_overall']}/100 · "
          f"{totals['modules_without_tests']} módulos sin tests{cov_msg}")


if __name__ == "__main__":
    main()
