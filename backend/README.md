# backend

API clínica de Fetal Medical Bolivia: Django 6 con Django REST Framework, django-tenants (un esquema de PostgreSQL
por clínica) y Django Channels para las notificaciones en vivo.

## Cómo corre

| Proceso | Comando (lo arranca `INICIAR.bat` desde la raíz) | Puerto |
|---|---|---|
| API REST (WSGI) | `.venv\Scripts\python -m waitress ... wsgi:application` | 8000 |
| Notificaciones en vivo (ASGI) | `.venv\Scripts\python -m uvicorn asgi:application` | 8010 |

La API llama al servicio de IA (`../servicio-ia`, puerto 8001) por `AI_SERVICE_URL` y lee los modelos tabulares
(cardiotocografía y peso al nacer) de `../modelos-ia/tabulares` (`ML_MODELOS_DIR`). Las rutas del resto del
repositorio están en `settings.py` (`REPO_DIR`, `FRONTEND_DIR`, `DATASETS_DIR`, `ENTRENAMIENTO_IA_DIR`).

## Módulos

| Carpeta | Qué contiene |
|---|---|
| `pacientes/`, `antecedentes/`, `embarazos/`, `controles/`, `triaje/` | Registro de la paciente, embarazo y controles prenatales con alertas |
| `laboratorio/`, `ecografias/`, `ecografias_archivos/` | Exámenes con rangos de referencia, ecografías, biometría y archivos |
| `partos/`, `evoluciones/`, `notas_evolucion/`, `vacunas/` | Parto, partograma, recién nacido, epicrisis, evolución y vacunas |
| `citas/`, `consultorios/`, `clientes/` | Agenda por médico, consultorios y clínicas (tenants) |
| `calculadoras/`, `calculadoras_avanzadas/` | Calculadoras clínicas (Bishop, preeclampsia, crecimiento, riesgo cromosómico, dosis) |
| `ia_medica/` | Integración con el servicio de IA, cardiotocografía, peso al nacer y Guía de IA |
| `reportes/`, `graficos/`, `notificaciones/`, `notifications_websocket/` | Reportes, indicadores, alertas y WebSockets |
| `usuarios/`, `roles/`, `auditoria/`, `core/`, `monitoring/`, `soporte/` | Cuentas, doble factor, permisos, auditoría inmutable, salud del sistema |
| `cache_utils/`, `seeders/` | Caché y carga de catálogos |
| `tests/`, `e2e/` | Pruebas de la API (pytest) y de punta a punta (Playwright) |
| `scripts/` | Utilidades del lanzador (`arranque.py`), muestras de IA y recifrado de datos |

## Entorno

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env      # completar las claves (ver el README de la raíz)
.venv\Scripts\python manage.py migrate_schemas --noinput
```

## Pruebas

```powershell
.venv\Scripts\python -m pytest
```

Las pruebas de punta a punta (`e2e/`) necesitan el sistema en marcha: `cd e2e` y `npx playwright test`.

## Datos que no se versionan

`media/` (archivos de las pacientes), `backups/` (respaldos de la base), `logs/`, `.env` y `reportes_generados/`.
