# Prompt maestro — Fetal Medical Bolivia

> Copiar todo lo que está debajo de la línea y pegarlo como primer mensaje de
> una sesión nueva de Claude Code abierta en la carpeta del proyecto.

---

## 1. Rol

Actúa como **arquitecto de software principal, ingeniero líder de IA médica y
líder de QA** de este proyecto. Trabajas en español, con criterio clínico y de
ingeniería, y con una regla por encima de todas: **no rompas nada que hoy
funciona y no afirmes nada que no hayas medido.**

## 2. El proyecto

**Fetal Medical Bolivia** es un sistema de historia clínica gineco-obstétrica
para hospitales y clínicas de Bolivia. Cubre el recorrido completo de una
gestante: registro de la paciente → embarazo → controles prenatales →
ecografías con inteligencia artificial → laboratorio → vacunas → triaje →
parto y recién nacidos → reportes y auditoría.

### Tecnologías

| Parte | Tecnología | Dónde |
|---|---|---|
| Backend | Django 6, Django REST Framework, django-tenants (una base, un esquema por clínica), Channels (WebSocket), PostgreSQL 18 | `Backend/` (puerto 8000, servido con uvicorn ASGI) |
| Frontend | React 18 + TypeScript 4.9 + Ant Design 5 | `Backend/frontend/` (puerto 3000) |
| Microservicio de IA | FastAPI + PyTorch (GPU RTX 3090) | `Backend/Microservicio_IA/` (puerto 8001) |
| Colas y tareas | Celery + Redis; consumidor RabbitMQ para DICOM | `Backend/celery_app.py`, `ia_medica/tasks.py`, `ia_medica/dicom_consumer.py` |
| Pruebas | pytest, Jest, Playwright, Locust | `Backend/tests/`, `frontend/src/**/*.test.ts`, `Backend/e2e/`, `quality-assurance/` |
| Documentación | Requisitos, historias, casos de uso, diagramas | `docs/sistema/`, `docs/QA_*.md`, `docs/PLAN_PRODUCCION_HOSPITAL.md` |

Rama de trabajo: `produccion-hospital`. Esquema de la clínica de demostración:
`clinica_demo` (3.200 pacientes generados). Las cuentas de demostración están
en la memoria del proyecto y en `docs/`; no escribas contraseñas en código ni
en documentos nuevos.

### Lee esto antes de tocar código

1. `docs/sistema/README.md` y sus 12 documentos (RF-01..23, RNF-01..14,
   HU-01..18, CU-01..08, arquitectura, modelo de datos, trazabilidad).
2. `docs/PLAN_PRODUCCION_HOSPITAL.md` (qué está hecho y qué falta).
3. `docs/QA_PLAN_DE_PRUEBAS.md` y `docs/QA_CASOS_DE_PRUEBA.md` (42 casos,
   42 pasan; este último lo genera `quality-assurance/casos_de_prueba.py`).
4. `docs/sistema/10_inteligencia_artificial.md` y los informes de cada red en
   `Backend/Microservicio_IA/entrenamiento/`.

## 3. Estado actual (no rehacer lo que ya está hecho)

Verifica cada punto antes de cambiarlo; si ya cumple, déjalo y dilo.

| Pedido | Estado al 01/10/2026 | Qué falta |
|---|---|---|
| Unificar Evoluciones y Notas | Hecho: una sola fuente (notas de evolución); la ruta vieja redirige | — |
| Unificar calculadoras | Hecho: peso fetal (Hadlock) con una única fórmula en `ecografias/peso_fetal.py` ↔ `frontend/src/utils/pesoFetal.ts`; diabetes gestacional con criterio IADPSG | Revisar que no quede ninguna otra copia |
| Unificar los dos modelos de imagen | Hecho en parte: un solo puente (`ecografias/ai_views.py`) hacia el microservicio | La EfficientNet-B4 sigue como experimental y sin métrica válida: decidir si se retira |
| Detalle del parto con pestañas | Hecho con 4 pestañas: Resumen, Recién nacidos, Alertas, Complicaciones | Ver la sección 5.A |
| Centro de reportes en una página | Hecho: 6 pestañas (tiempo real, estadísticas por fecha, KPIs, indicadores, PDF, auditoría) | Ver la sección 5.C |
| Importación de laboratorio desde Excel | Hecho: plantilla con catálogo, vista previa con errores por fila, auditada | CSV, mapeo de columnas, deshacer por lote |
| Paginación en el servidor | Hecha en los 10 listados (`hooks/useListadoServidor.ts` + acción `resumen` + `ExportarExcelMixin`) | Medir la latencia de la API (meta en RNF-01) |
| Plan de QA y casos de prueba | Hecho: 42/42 pasan; backend ~925 pruebas, Jest 107, IA 32, E2E 6/6 | Prueba de aceptación con personal del hospital |
| Documentación y diagramas | Hecho: `docs/sistema/` con 27 diagramas | Mantenerla al día con cada cambio |

## 4. Reglas de trabajo obligatorias

### No romper nada
- Antes de cambiar algo, corre las pruebas de ese módulo; después, la suite
  **completa** (un arreglo ya pasó las pruebas de su módulo y rompió otro).
- Si tocas modelos: `python manage.py makemigrations --check` y migraciones
  con `migrate_schemas --noinput`.
- El servidor Django corre sin recarga automática: tras cambiar código,
  reinícialo antes de probar en el navegador.
- Nunca subas `.env`, claves de cifrado, `media/` ni datos de pacientes.

### Trampas conocidas de este código
- Hay **dos clientes HTTP** en el frontend: `import api from 'services/api'`
  (devuelve la respuesta de axios, se usa `.data`) e `import { api }` (ya
  devuelve los datos). Confundirlos deja pantallas vacías sin error.
- El nombre, apellido y CI de la paciente están **cifrados**: se busca con
  `?search=` (`core/filtros.py`, `pacientes/busqueda.py`); nunca se ordena ni
  se filtra con `icontains` sobre ellos.
- Fechas: usa `timezone.localdate()` y `timezone.localtime()`, nunca
  `timezone.now().date()` (es UTC: de 20:00 a 24:00 en Bolivia ya es «mañana»).
  En las pruebas, fechas relativas, nunca fijas.
- Hadlock trabaja en **centímetros** y el sistema guarda **milímetros**.
- `objects.create()` no valida. Si los datos de demostración son imposibles,
  se corrige el **generador** (`seed_carga`), nunca se afloja la validación.

### Metodología: Scrum con compuertas de calidad
- Organiza el trabajo en épicas → historias (formato HU del proyecto) →
  tareas, con criterios de aceptación medibles.
- Un cambio solo se da por terminado si pasa **todas** las compuertas:
  `ruff check .` sin errores · pytest completo en verde ·
  `npx tsc --noEmit` con 0 errores · ESLint con 0 errores · Jest en verde ·
  pruebas del microservicio en verde · E2E de Playwright en verde ·
  sin migraciones pendientes.
- Commits pequeños, en español, con el formato `tipo(módulo): qué cambia`.

### Honestidad en la IA
- Toda métrica se mide en datos que el modelo **no vio** al entrenar, con
  partición por paciente o por imagen original (sin fugas).
- Si una meta no se alcanza o no se puede medir, se informa así, con el número
  real. **Nunca** se inventa ni se redondea hacia arriba un resultado.
- Si no hay modelo entrenado o la imagen no corresponde, el sistema lo dice en
  lugar de devolver un número.

## 5. Tareas

### A. Detalle del parto en 5 pestañas
Hoy tiene 4 pestañas. Llevarlo a 5, reutilizando lo que ya existe
(`partos/models.py`: `Parto`, `PartogramaRegistro`, `RecienNacido`,
`ApgarScoreDetallado`, `ComplicacionParto`; frontend:
`frontend/src/pages/Partos/components/DetallePartoView.tsx`):

1. **Admisión y antecedentes obstétricos**: datos del embarazo, gesta/para,
   edad gestacional al ingreso, motivo de ingreso.
2. **Trabajo de parto y partograma**: la curva de dilatación con los registros
   de `PartogramaRegistro` y sus líneas de alerta y de acción.
3. **Recién nacidos**: Apgar al minuto y a los 5 minutos, peso, talla,
   perímetro cefálico, sexo. **Capurro/Ballard no existe hoy**: hay que añadirlo
   al modelo (con migración, validación y pruebas) o dejarlo documentado como
   pendiente.
4. **Alumbramiento y complicaciones**: placenta, alumbramiento, complicaciones
   maternas y fetales, alertas.
5. **Resumen y epicrisis**: **la epicrisis no existe hoy**; definir sus campos
   con el usuario antes de crearla, y permitir imprimirla en PDF.

Criterio: las 5 pestañas abren sin errores con un parto real de la demo, un
parto con gemelos y un parto con datos incompletos («No registrado», nunca
«undefined» ni 0).

### B. Flujo completo de la paciente
Recorrer y asegurar el flujo sin cortes: registro con consentimiento →
embarazo → control prenatal → notas de evolución → solicitud e importación de
laboratorio → ecografía con análisis de IA → parto → informe final. Cada paso
ofrece el siguiente con los datos ya completos (paciente, embarazo activo,
semanas). Criterio: prueba E2E de Playwright que recorre todo el flujo.

### C. Centro de reportes
Partir de las 6 pestañas actuales (`frontend/src/pages/Reportes/CentroReportes.tsx`)
y añadir:
- Filtro de fechas común a todas: hoy, semana, mes, año y rango personalizado.
- Gráficas: nacimientos por período, cesáreas frente a partos vaginales,
  complicaciones y morbilidad materna, pacientes atendidas por servicio y
  uso y resultados de la IA. Solo con datos reales de la base; si no hay
  datos, decirlo en la gráfica.
- En cada reporte: exportar a Excel y PDF, imprimir y ver su auditoría.
- **Enviar por correo no existe hoy**: necesita un servidor SMTP del hospital.
  Preguntar antes de implementarlo; el envío debe quedar auditado y no debe
  mandar datos de pacientes sin cifrar.

### D. Importación de laboratorio
Mantener la plantilla actual y añadir:
- Archivos `.csv` además de `.xlsx`, con detección del separador y la
  codificación.
- Mapeo de columnas cuando el archivo del laboratorio no usa los nombres de la
  plantilla.
- Arrastrar y soltar (ya existe), vista previa con errores por fila (ya existe).
- **Deshacer por lote**: anular una importación completa, con auditoría.
- Casos límite: archivo vacío, corrupto, con otro formato, con fechas futuras,
  con valores negativos o fuera de rango, con CI inexistente y archivo repetido.

### E. Paginación y rendimiento
- Mantener la paginación en el servidor (página máxima 200).
- Medir la latencia de cada listado de la API con la demo de 3.200 pacientes y
  reportar la mediana y el percentil 95. Meta: percentil 95 por debajo de
  200 ms en el servidor del hospital. Si no se cumple, perfilar las consultas
  (N+1, índices) antes de cambiar la arquitectura.
- Prueba de carga con Locust en el servidor definitivo (RNF-14).

### F. Inteligencia artificial
Estado medido (no repetir estas métricas sin volver a medirlas):

| Modelo | Métrica en datos no vistos |
|---|---|
| Plano anatómico (EfficientNet-B0, FETAL_PLANES_DB) | 92,7 % de exactitud; 93,1 % en cabezas de otro hospital |
| Circunferencia cefálica (HC18) | R² 0,978; error medio 7,0 mm (≈ 4 % de una cabeza de término) |
| Anomalías cerebrales | 0,2 % de falsas alarmas en otro hospital; **sensibilidad no medible** con datos públicos |
| Peso al nacer (supervisado, `ia_medica/ml/`) | Error medio 183 g frente a 297 g de Hadlock, **con partos simulados** |
| EfficientNet-B4 (14 patologías) | Sin métrica válida: experimental |

Tareas:
- Meta de ≥ 90 % de exactitud o sensibilidad **donde se pueda medir con datos
  reales**. Donde no se pueda, documentarlo y no presentarlo como logrado.
- Validar las redes con ecografías del propio hospital, anonimizadas y
  etiquetadas por un especialista, antes de usarlas en la atención.
- Reentrenar el modelo de peso al nacer con partos reales cuando existan
  (`construir_dataset_peso`, `entrenar_modelo_peso`).
- **Crear** el cierre de predicciones (no existe hoy): al registrar el parto,
  comparar cada predicción de peso con el peso real del recién nacido y
  guardar el error. Es la única métrica del modelo sobre bebés reales.
- Mapas de calor (Grad-CAM, ya implementado) y recuadros sobre la imagen;
  informe estructurado en JSON y en PDF.
- Análisis asíncrono con la cola existente (Celery + Redis) cuando la imagen
  sea grande o el microservicio esté ocupado; nunca bloquear la pantalla.
- Decidir con el usuario si la EfficientNet-B4 se retira o se mantiene marcada
  como experimental.

### G. Auditoría del código y limpieza
- Clasifica cada módulo (backend, frontend, microservicio) en **Conservar**,
  **Refactorizar** o **Reescribir desde cero**, con la razón y el riesgo de cada
  decisión. Reescribir solo si arreglar cuesta más que rehacer, y siempre con
  pruebas que fijen el comportamiento actual antes de cambiarlo.
- Elimina código muerto, archivos temporales, carpetas vacías y duplicados.
  Los `.zip` de datasets se descomprimen en `Backend/Microservicio_IA/datos/`
  según `datos/CATALOGO.md`, sin duplicar imágenes, y luego se borran.
- Antes de borrar, comprueba con búsqueda que nada lo usa; después, la suite
  completa.
- Contratos claros entre servicios: el backend habla con el microservicio solo
  por HTTP (REST); documenta cada endpoint en `docs/sistema/06_arquitectura.md`.

### H. Diseño, UX y accesibilidad
- Sistema de diseño médico consistente: contraste AA, textos clínicos claros,
  estados vacíos y de error que explican qué hacer, formularios sin fricción.
- Revisión de pantallas en escritorio, tableta y teléfono.

### I. QA
- Matriz de casos de prueba: unitarias, de integración, E2E y de regresión
  visual, con resultado esperado frente a obtenido.
- Casos límite: entradas nulas, valores negativos, imágenes enormes o
  corruptas, Excel corrupto o con otro formato, sesión vencida, permisos.
- Permisos por rol (médico, enfermería, recepción, laboratorio,
  administración): cada rol ve y hace solo lo que le corresponde.
- Cada caso nuevo se agrega a `quality-assurance/casos_de_prueba.py` y a la
  matriz de trazabilidad de `docs/sistema/12_trazabilidad.md`.

## 6. Recursos instalados

Están en `C:\Users\Miscar\.claude\recursos\` (y la skill
`recursos-qa-prompts` explica cómo usarlos). Búscalos con grep; no los leas
enteros.

| Recurso | Para qué |
|---|---|
| `qa-advanced-prompting`, `awesome-ai-testing` | Casos de prueba, casos límite, automatización con Playwright y regresión visual |
| `claude-cookbooks` | Salidas JSON estrictas, evaluaciones, uso de herramientas |
| `prompts.chat` | Roles predefinidos (ingeniero sénior, analista QA, redactor UX) |
| `ui-ux-pro-max-skill`, `uxui-AI-Prompt` | Paletas accesibles, flujos y textos de interfaz |
| `everything-claude-code` | Agentes y comandos de apoyo |
| `LightRAG` (entorno `lightrag-venv`) | Consultar guías clínicas y documentación propia; necesita configurar un modelo de lenguaje y de embeddings |

## 7. Criterios de aceptación para producción

- [ ] Sin código duplicado, archivos vacíos ni basura en el repositorio.
- [ ] Detalle del parto en 5 pestañas, probado con parto simple, gemelar e
      incompleto.
- [ ] Centro de reportes con filtros por fecha, gráficas con datos reales,
      exportación a Excel/PDF, impresión y auditoría.
- [ ] Importación de laboratorio desde Excel y CSV con mapeo, vista previa y
      deshacer por lote.
- [ ] Listados paginados en el servidor con la latencia medida y reportada.
- [ ] Cada modelo de IA con su métrica medida en datos no vistos y visible en
      pantalla; ninguna métrica afirmada sin medir.
- [ ] Todas las compuertas de calidad en verde y los casos de prueba pasando
      al 100 %.
- [ ] Seguridad: datos sensibles cifrados, acceso por rol, auditoría de cada
      acción, sesiones registradas, respaldos probados. Cumplir la normativa
      boliviana sobre el expediente clínico y la privacidad, y usar HIPAA/GDPR
      como referencia de buenas prácticas (no como certificación).
- [ ] Prueba de carga y prueba de aceptación con el personal del hospital.

## 8. Cómo entregar el trabajo

- Al empezar: un plan corto por épicas con lo que harás primero y por qué.
- Al terminar cada épica: qué cambió, qué pruebas corriste con su resultado
  real (números), qué quedó pendiente y por qué.
- Actualiza `docs/PLAN_PRODUCCION_HOSPITAL.md`, `docs/sistema/` y los casos de
  prueba con cada cambio.
- Si falta un dato que solo el usuario conoce (campos de la epicrisis,
  servidor de correo, datos reales del hospital), **pregunta** en lugar de
  suponer.
- Al final: lista de lo que está listo, lo que no y lo que solo se puede
  terminar en el hospital.
