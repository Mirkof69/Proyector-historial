# Reporte de diagnóstico y estado del sistema

**Fetal Medical Bolivia** — Julio 2026
Cubre desde el merge del refactor de *giants* (`338d15a`) hasta `7a9d73f`: **36 commits**.

---

## 0. Conclusión primero

**El sistema funciona hoy**, y hay evidencia concreta de eso: 430 pacientes con
historia clínica completa creadas, editadas, buscadas y borradas desde la
aplicación real; 8 usuarios concurrentes sin corrupción; navegación completa sin
rutas rotas; auditoría registrando quién/cuándo/qué. No es "los tests están en
verde": es el sistema ejercitado.

**Con dos salvedades que hay que decir en voz alta:**

1. **Casi todo lo grave que se encontró fallaba en silencio.** 16 bugs reales,
   ninguno producía un error visible. La auditoría clínica llevaba apagada un
   tiempo indeterminado; el buscador de pacientes no encontraba a nadie por
   nombre ni cédula en ninguna pantalla; la historia clínica mostraba controles
   de otras pacientes. Todo eso con la suite de tests pasando.

2. **La suite no es todavía una red de seguridad suficiente.** 54.1% de
   cobertura real, y de los 379 tests solo el 38% verifica comportamiento; el
   55% se queda en el contrato (status HTTP, estructura) y un 5% es humo.

Lo más importante a resolver a continuación está en §6.

---

## 1. Lo que se hizo y quedó verificado con evidencia

### 1.1 Ronda de carga en 7 fases (el grueso de la evidencia)

| Fase | Qué se hizo | Evidencia |
|---|---|---|
| 1 | Diagnóstico del test skipped y del QA 91/100 | Test reescrito al contrato de cookies; QA honesto = **87/100, 54.1% cobertura** |
| 2 | Auditoría de navegación con Playwright | Todos los botones/enlaces/menús llevan a donde corresponde; 1 bug real (404 de tipos de vacunas) |
| 3 | Seed de volumen | **500 pacientes** (250 completos + 250 editables) con antecedentes, embarazo, controles, ecografías, labs, vacunas y desenlace |
| 4 | CRUD real sobre los editables | Editados y releídos: los cambios persisten; partos registrados sobre embarazos reales |
| 5 | Concurrencia con 8 usuarios | **288 operaciones, 0 errores**; 8 escrituras simultáneas al mismo registro → un ganador coherente, resto de campos intactos; 0 ci_hash duplicados, 0 huérfanos |
| 6 | Auditoría + borrados | Soft delete (desaparece de vistas, sigue en BD) y hard delete (sin referencias huérfanas) verificados contra la BD |
| 7 | Reportes e historia clínica | Dashboard cuadra (430/281/149); HC de 4 pacientes con todas las secciones pobladas |

Volumen final en base: 430 pacientes · 437 embarazos · 1328 controles · 528
ecografías · 1021 laboratorios · 260 vacunas · 38 partos · 9293 registros de
auditoría.

### 1.2 Los 16 bugs reales encontrados y corregidos

**Los tres grandes** (los que van a la defensa):

1. **Auditoría clínica apagada en silencio** (`521db2d`, `8978c72`). Cuatro
   causas encadenadas; la de fondo: `AuditoriaConfig.ready()` no importaba los
   signals, que quedaban conectados solo como efecto colateral de importar el
   middleware. Todo lo que no pasa por HTTP —comandos, workers, scripts,
   tests— corría **sin trazabilidad**. Es un requisito legal, no una comodidad.

2. **Controles de otras pacientes en la Historia Clínica** (`30e34f7`).
   `/controles/?embarazo=N` no era un filtro válido; django-filter lo ignoraba
   en silencio y devolvía los 1328 controles de todas. Datos clínicos ajenos
   presentados como propios.

3. **La búsqueda de pacientes no funcionaba en ningún módulo** (`a360a71`,
   `e012e0b`). Los datos identificatorios son `EncryptedCharField` y
   `SearchFilter` hace `icontains` en SQL: LIKE contra texto cifrado. Estaba
   así en **24 viewsets de 13 módulos**. Se resolvió con una implementación
   centralizada (`pacientes/busqueda.py` + `core/filtros.py`), no con 24
   parches.

**Los otros 13:** 404 silencioso del catálogo de vacunas · dashboard mostrando
295 de 430 pacientes (consulta duplicada en dos archivos) · `/vacunas/` y
`/laboratorios/` apuntando a la raíz del router (dos tabs vacías sin error) ·
crash de la HC al hacer `.toLowerCase()` sobre una PK numérica · crash de
`TabVacunas` por nombres de campo desalineados con el serializer · ecografías
mostrando "EG: sem / Peso: g" por leer campos inexistentes · el seed nunca
creaba laboratorios · tres valores inventados por el generador que el modelo
rechaza · contador de CI colisionando entre lotes · filtro con tildes en 13
pantallas del frontend que descartaba "López" al buscar "lopez".

### 1.3 Antes de la ronda de carga

Refactor de *giants* + auth por cookies + pase premium (`338d15a`);
exportables PDF/Excel/CSV en los 5 puntos clínicos; gráficos Recharts con
paleta validada para daltonismo; modo oscuro sin contrastes rotos; flujos
guiados de triaje y confirmación de resultado crítico; 8 bugs del diagnóstico
en vivo (incluida la clave HMAC distinta que hacía que `buscar-por-cedula`
nunca encontrara a nadie).

### 1.4 Estado de las suites

| Suite | Resultado |
|---|---|
| pytest | **394 passed, 6 skipped, 0 failed** |
| pytest con tenants | **4/4** (`TEST_CON_TENANTS=true`, contra PostgreSQL) |
| tsc --noEmit | limpio |
| tests frontend | 20 passed, 4 suites |
| build producción | OK |
| ruff | limpio en el backend |
| qa_scan | 91/100 nominal · **87/100 real** (54.1% cobertura) |

---

## 2. Calidad real de los tests

Clasificación por AST de los 379 tests del backend:

| Categoría | Cantidad | Qué significa |
|---|---|---|
| **Comportamiento** | 146 (38%) | Crea datos y afirma sobre el resultado concreto. Es el que caza bugs. |
| **Contrato** | 211 (55%) | Verifica status HTTP, estructura o permisos. Útil, superficial. |
| **Humo** | 22 (5%) | Solo comprueba que no explote (`isinstance`, "no crashea"). |

Los tests escritos en esta ronda (**32 nuevos**) son todos de comportamiento y
**todos verificados revirtiendo el arreglo** para confirmar que fallan sin él.

---

## 3. Lo que quedó pendiente o fuera de alcance

### 3.1 Cobertura de tests

Cobertura global **54.1%**. Los módulos que más arrastran, ponderados por
tamaño:

| Módulo | Cobertura | LOC |
|---|---|---|
| `reportes` | 35.1% | 9364 |
| `pacientes` | 34.0% | 5252 |
| `laboratorio` | 35.4% | 5246 |
| `ia_medica` | 35.6% | 5020 |
| `ecografias` | 43.6% | 4827 |
| `calculadoras_avanzadas` | 47.8% | 4755 |
| `notifications_websocket` | 18.1% | 997 |
| `cache_utils` | 18.8% | 665 |

Llevar esto al 70% es un esfuerzo aparte, deliberadamente **no** mezclado con
la ronda de carga para no confundir "escribir tests" con "arreglar el sistema".

### 3.2 Deuda conocida

- **`DosisMedicamentos`** — quedó fuera de alcance en su momento.
- **`cardiopatia_congenita`** — sin datos limpios para entrenar/validar.
- **Componentes gigantes en el frontend** — el refactor de *giants* avanzó pero
  no terminó; quedan pantallas grandes (`Pacientes.tsx`, `HistoriaClinica.tsx`).
- **Los 2 tests de `to_char`** (`get_controles_stats`, `get_partos_stats`) no
  corren en ningún lado: la suite fuerza SQLite. Se verificaron **a mano**
  contra PostgreSQL y funcionan, pero siguen sin red automática.
- **Entrenamiento CNN** — pendiente de relanzar en Artemis.

### 3.3 Riesgo estructural: SQLite en los tests

La suite corre sobre SQLite **con `django_tenants` desactivado**. El
aislamiento entre clínicas —la columna vertebral del sistema y su principal
requisito legal— no lo probaba ningún test, y de ahí salió el bug de
auditoría. **Parcialmente cerrado** en esta ronda:
`TEST_CON_TENANTS=true pytest tests/test_aislamiento_tenants.py` corre contra
PostgreSQL real (4/4 en verde). Falta que **toda** la suite pueda correr así en
CI, no solo ese archivo.

---

## 4. Lo que falta en diseño / UX

- **Búsqueda con volumen.** El filtro por nombre es O(n) descifrando en Python
  (~190-380 ms sobre 450 pacientes). Funciona para una clínica; para volumen
  mayor hace falta una **columna de tokens de búsqueda normalizados** (sin
  tildes, minúsculas) que permita LIKE en SQL sin exponer el dato clínico.
  Es una decisión de diseño con impacto en el esquema: documentada, no
  improvisada.
- **La HC tiene 12 pestañas.** Funciona, pero es mucha superficie: conviene
  revisar jerarquía y qué merece estar en el primer nivel.
- **Estados vacíos que dicen por qué.** "Sin notas de evolución" debería
  distinguir "no se registró" de "no corresponde en esta etapa".
- **Impresión / PDF de la historia clínica completa** como ficha única.
- **Accesibilidad** más allá de la paleta: foco visible, navegación por teclado
  en los formularios largos, tamaños táctiles.

---

## 5. Lo que falta en funcionamiento (flujos sin probar de punta a punta)

- **Citas y agenda** — sólo 15 citas de prueba; no se ejercitó el flujo real
  (agendar → recordar → atender → cerrar).
- **Notificaciones** — durante las pruebas aparecieron eventos clínicos *"sin
  destinatario: la notificación NO llegará a nadie"*. Está registrado como
  advertencia en el propio sistema, pero el flujo de destinatarios no se
  validó.
- **Triaje → consulta → evolución** como cadena completa.
- **Microservicio de IA** — los tests de integración fallan por conexión; el
  análisis de ecografías con Grad-CAM no se probó end-to-end en esta ronda.
- **MFA y recuperación de contraseña** — implementados, no ejercitados aquí.
- **Backup y restauración reales** — los tests usan mocks a propósito (nunca
  tocan la base de producción); nunca se probó una restauración de verdad.
- **WebSockets de notificaciones** — 18.1% de cobertura y sin prueba en vivo.

---

## 6. Lo próximo más importante

En este orden:

1. **Probar el flujo de notificaciones y destinatarios.** Es el único punto
   donde el sistema ya está avisando por sí solo de que algo no llega.
2. **Hacer que toda la suite pueda correr con tenants en CI.** La
   infraestructura ya está (`TEST_CON_TENANTS`); falta el pipeline. Es la
   diferencia entre haber tapado *un* agujero y haber cerrado *la clase* de
   agujeros.
3. **Subir cobertura en `reportes`, `pacientes` y `laboratorio`** — los tres
   módulos grandes con ~35%, escribiendo tests de comportamiento, no de humo.
4. **Cerrar el flujo de citas de punta a punta.**
5. **Decidir la estrategia de búsqueda para volumen** (tokens normalizados).

---

## Anexo — Cómo reproducir la evidencia

```bash
# Suite completa
cd Backend && python -m pytest -q --ignore=Microservicio_IA

# Aislamiento multi-tenant (requiere PostgreSQL levantado)
TEST_CON_TENANTS=true python -m pytest tests/test_aislamiento_tenants.py

# Datos de volumen (idempotente, valida todo lo que siembra)
python manage.py seed_carga --completos 250 --editables 250

# Calidad con cobertura real
python quality-assurance/qa_scan.py --coverage

# Frontend
cd Backend/frontend && npx tsc --noEmit && CI=true npx react-scripts test --watchAll=false
```
