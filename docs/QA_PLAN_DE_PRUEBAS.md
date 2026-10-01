# Plan de QA y plan de pruebas — Fetal Medical Bolivia

Versión del 01/10/2026 · rama `produccion-hospital`.
Casos de prueba con resultado esperado y obtenido: [QA_CASOS_DE_PRUEBA.md](QA_CASOS_DE_PRUEBA.md)
(se generan ejecutando las pruebas, no a mano).

## 1. Objetivo

Que el sistema pueda usarse en un hospital sin perder ni inventar datos
clínicos: desde el registro de la paciente hasta el análisis de una ecografía,
el parto y los reportes. Cada requisito importante tiene una prueba automática
que lo comprueba, y ninguna versión se entrega con una prueba en rojo.

## 2. Alcance

| Componente | Qué se prueba |
|---|---|
| Backend Django + DRF (django-tenants, PostgreSQL) | Modelos y validaciones clínicas, API, permisos por rol, auditoría, importación/exportación Excel, tareas (recordatorios), migraciones |
| Frontend React + TypeScript | Utilidades clínicas (peso fetal, diabetes gestacional, ILA, preeclampsia), hook de listados, compilación sin errores de tipos, lint |
| Microservicio de IA (FastAPI) | Redes con ecografías reales (plano, circunferencia cefálica, anomalías cerebrales): que la API reproduzca las métricas medidas al entrenar; respuestas honestas sin modelo |
| Modelo supervisado (peso al nacer) | Predicción con Hadlock al lado, negativas con motivo, contrato de columnas |
| Flujo completo en navegador | Paciente → embarazo → control → ecografía con imagen → IA → parto |
| Lanzadores y operación | `.bat` con comandos válidos, respaldo y restauración, fecha local |

Fuera de alcance (ver §9): validación clínica prospectiva de la IA con
pacientes bolivianas y pruebas de aceptación con el personal del hospital.

## 3. Estrategia por niveles

| Nivel | Herramienta | Dónde | Qué protege |
|---|---|---|---|
| Unitarias | pytest, Jest | `Backend/tests`, `*/tests.py`, `frontend/src/**/*.test.ts` | Fórmulas clínicas, validaciones, reglas de negocio |
| Integración de API | pytest + `APIClient` | `Backend/tests` | Contratos de cada endpoint, filtros en el servidor, permisos, auditoría |
| Regresión de rutas | `test_rutas_sin_500.py` | Backend | ≈330 rutas GET: ninguna responde 500 |
| IA (contrato y rendimiento) | pytest con el Python que tiene torch | `Backend/Microservicio_IA/test_*.py` | La API da lo mismo que el entrenamiento; métricas mínimas |
| E2E | Playwright | `Backend/e2e` | El flujo clínico completo en un navegador real |
| Recorrido de pantallas | `e2e/recorrido_listados.js` | Navegador | Cada listado: peticiones, tiempo, errores JS y 500 |
| Carga | Locust (corridas previas, ver `Backend/DESPLIEGUE_MEDIDO.md`) | Backend | 8 workers; límites de login |

Cada prueba declara en su docstring el fallo real que previene y compara un
**ESPERADO** con lo **OBTENIDO**. Las pruebas se escriben cuando se encuentra o
se corrige un fallo (regresión), no para inflar la cobertura.

## 4. Puertas de calidad (no se entrega si alguna falla)

| Puerta | Comando | Umbral |
|---|---|---|
| Lint backend | `ruff check .` | 0 errores |
| Tests backend + cobertura | `pytest --cov-fail-under=55` | 0 fallos |
| Migraciones | `manage.py makemigrations --check` | Sin cambios pendientes |
| Tipos frontend | `npx tsc --noEmit` | 0 errores |
| Lint frontend | `npx eslint src` | 0 errores (avisos ≤ 56 en CI) |
| Tests frontend | `react-scripts test` | 0 fallos |
| Microservicio de IA | `pytest` en `Microservicio_IA` | 0 fallos |
| E2E | `npx playwright test` | 6/6 |
| Casos de prueba | `python quality-assurance/casos_de_prueba.py` | todos «Pasa» |

Las seis primeras corren en CI (`.github/workflows/ci.yml`) en cada push y
pull request a `main` y `produccion-hospital`.

## 5. Entornos y datos de prueba

| Entorno | Base | Datos |
|---|---|---|
| Tests automáticos | SQLite en memoria, sin multi-tenant | Creados por cada test |
| Demo / E2E | PostgreSQL, esquema `clinica_demo` | `MIGRAR_Y_SEED.bat`: 3.200 pacientes simulados que pasan `full_clean()`, sin fechas futuras; los datos E2E (apellido «E2E») se borran con `limpiar_datos_e2e` |
| Producción | PostgreSQL, un esquema por clínica | Reales; respaldo diario `RESPALDO_DIARIO.bat` (restauración verificada) |

Cuentas demo (clave `Demo2026!`): `dra.garcia@`, `enf.mamani@`, `recep.flores@`,
`admin.demo@fetalmedical.bo`. Nunca usar la demo en el hospital.

## 6. Criterios de entrada y salida

**Entrada a pruebas:** la rama compila, las migraciones aplican en un esquema
vacío y la demo se siembra sin registros inválidos.

**Salida (listo para producción):** todas las puertas de §4 en verde, casos de
prueba 100 % «Pasa», ningún defecto abierto de riesgo alto, y los puntos de §9
acordados con el hospital.

## 7. Riesgos priorizados

| Riesgo | Impacto | Mitigación y prueba |
|---|---|---|
| Cálculo clínico erróneo (peso fetal, diabetes gestacional, preeclampsia, ILA, rangos de laboratorio) | Alto | Una sola implementación por cálculo, con los mismos valores de prueba en backend y frontend (CP-030, CP-051, CP-080, CP-081, CP-082) |
| La IA da una alarma falsa o un número inventado | Alto | Métricas medidas dentro del modelo, filtro de planos, 503/409 sin modelo (CP-033 a CP-036) |
| Pérdida de historia clínica | Alto | Borrado protegido y auditado (CP-013, CP-092) |
| Datos ocultos por paginación (más de 200) | Alto | Listados y cifras en el servidor (CP-004, CP-060) |
| Acceso indebido a datos de pacientes | Alto | Permisos por rol, archivos protegidos (CP-031, CP-090, CP-091) |
| Fecha UTC en lugar de la local (Bolivia, UTC−4) | Medio | `timezone.localdate()`/`localtime()` y pruebas a las 21:00 y 23:00 (CP-100) |
| El sistema no arranca en el hospital | Alto | Lanzadores validados contra los comandos reales (CP-101) |

## 8. Defectos encontrados y corregidos en esta revisión (con su prueba)

| Defecto | Prueba que lo fija |
|---|---|
| Las 4 calculadoras de peso fetal del frontend daban ~0 g (mm en fórmula de cm, `Math.exp`, coeficientes cambiados) | `pesoFetal.test.ts` |
| Diabetes gestacional exigía 2 valores alterados (IADPSG: basta 1) | `diabetesGestacional.test.ts` |
| Rangos de laboratorio con mínimo 0 o un solo límite daban siempre «normal» (89 resultados de la demo mal marcados) | `test_catalogo_laboratorio.py` |
| El catálogo de rangos nunca cargó (tipos inexistentes; método de otro archivo) | `test_catalogo_laboratorio.py` |
| Editar un resultado de laboratorio daba 500 | `test_catalogo_laboratorio.py` |
| Vacunas y notas mostraban solo 200 registros sin avisar; la tabla de laboratorio salía vacía | `test_vacunas_listado_servidor.py`, recorrido de listados |
| Recordatorios y «hoy/del mes» con fecha UTC: de 20:00 a 24:00 era el día siguiente | `test_notificaciones_clinicas.py` |
| Los tres `.bat` usaban una opción inexistente: el sistema no arrancaba | `test_lanzadores_bat.py` |
| Base nueva: grupos por rol con 0 permisos (el médico no veía nada) | `test_permisos_por_rol.py` |
| Triaje no guardaba la prioridad y registrarlo daba 400 | `test_triaje_listado_servidor.py` |
| Demo con 437 partos en el futuro | `test_seed_carga.py` |
| Red de anomalías: 100 % por atajo de fuente | `entrenamiento/patologias_cerebrales/INFORME.md`, `test_anomalias_cerebrales.py` |

## 9. Pendiente antes del uso clínico (no automatizable)

1. **Pruebas de aceptación (UAT)** con médicos, enfermería y recepción del
   hospital, sobre sus flujos reales y en sus equipos y red.
2. **Validación clínica local de la IA**: la sensibilidad de la red de
   anomalías cerebrales no se puede medir con datos públicos; el modelo de peso
   al nacer está entrenado con partos simulados. Ambos muestran esa
   advertencia en pantalla y deben reentrenarse o validarse con casos del
   hospital antes de influir en decisiones.
3. Prueba de carga en el servidor definitivo del hospital.

## 10. Cómo ejecutar todo

```bash
# Backend
cd Backend && .venv/Scripts/python.exe -m ruff check . && .venv/Scripts/python.exe -m pytest
# Frontend
cd Backend/frontend && npx tsc --noEmit && npx eslint src && set CI=true && npx react-scripts test --watchAll=false
# Microservicio de IA (Python con torch)
cd Backend/Microservicio_IA && python -m pytest
# E2E (sistema levantado con INICIAR_SISTEMA.bat y la demo cargada)
cd Backend/e2e && npx playwright test
# Casos de prueba esperado/obtenido → docs/QA_CASOS_DE_PRUEBA.md
python quality-assurance/casos_de_prueba.py
```

## 11. Estado al 01/10/2026

| Suite | Resultado |
|---|---|
| Backend (pytest) | 924 pasan, 6 omitidas, 0 fallos · cobertura 61 % |
| Frontend (Jest) | 107/107 · tsc 0 errores · eslint 0 errores |
| Microservicio de IA | 32/32 |
| E2E (Playwright) | 6/6 (21 s) |
| Casos de prueba | 38/38 pasan |
