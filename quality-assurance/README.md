# Quality Assurance — Fetal Medical Bolivia

Sistema de control y análisis de calidad del código, basado en el modelo de
calidad de producto **ISO/IEC 25010** con métricas **reales** extraídas del
código (no estimaciones).

## Qué mide

El scanner (`qa_scan.py`) recorre el backend Django **módulo por módulo** y
calcula una puntuación 0–100 por cada dimensión de calidad, usando herramientas
de análisis estático reales:

| Dimensión ISO 25010 | Cómo se mide | Herramienta |
|---|---|---|
| **Maintainability** (Mantenibilidad) | Densidad de hallazgos de lint de deuda real por cada 100 líneas | `ruff` (F, E9, B, SIM, RET, PERF, C4, PIE) |
| **Security** (Seguridad) | Hallazgos de severidad media/alta por módulo | `bandit -ll` |
| **Reliability** (Fiabilidad) | Presencia de tests + (opcional) cobertura | `coverage` / Django test |
| **Testability** (Testabilidad) | ¿El módulo tiene suite de tests dedicada? | inspección |

La **puntuación global** por módulo pondera:
`Maintainability 30% · Reliability 30% · Security 25% · Testability 15%`.

> Se **excluyen** deliberadamente las reglas `RUF012` (mutable-class-default) y
> `ARG002` (unused-method-argument): en Django/DRF son idiomas del framework
> (`Meta.fields = [...]`, firmas de vistas), **no** defectos. Contarlas
> distorsionaría la puntuación con ~900 falsos positivos.

## Cómo se usa

```bash
# Escaneo rápido (ruff + bandit por módulo)
Backend/.venv/Scripts/python.exe quality-assurance/qa_scan.py

# Con cobertura de tests real por módulo (lento, ~5 min)
Backend/.venv/Scripts/python.exe quality-assurance/qa_scan.py --coverage
```

Genera `reports/qa_report.json`, que alimenta el dashboard web
(`dashboard.html`).

## Interpretación de la puntuación

| Rango | Estado | Significado |
|---|---|---|
| 85–100 | ✅ Excelente | Mantenible, con tests, sin deuda notable |
| 70–84 | 🟢 Bueno | Sólido; mejoras menores |
| 50–69 | 🟡 A mejorar | Falta cobertura o hay deuda acumulada |
| 0–49 | 🔴 Crítico | Sin tests y/o alta densidad de hallazgos |

## Estructura

```
quality-assurance/
├── README.md          ← este archivo (metodología ISO 25010)
├── qa_scan.py         ← scanner: métricas reales por módulo → JSON
├── dashboard.html     ← tablero web interactivo (scores + plan)
└── reports/
    └── qa_report.json ← salida del scanner
```
