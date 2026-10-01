# 02 · Requisitos funcionales

Prioridad: **Alta** = sin esto el sistema no sirve en un hospital o pone en
riesgo a la paciente; **Media** = necesario para el uso diario.
La columna «Verificado por» indica los casos de prueba automáticos; su
resultado está en [QA_CASOS_DE_PRUEBA.md](../QA_CASOS_DE_PRUEBA.md).

## Atención y registro

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-01 | Registrar a una paciente con su consentimiento de tratamiento de datos (Ley 164). Sin consentimiento no se registra. Al registrarla, el sistema ofrece iniciar su embarazo. | Alta | CP-001 |
| RF-02 | Buscar pacientes por nombre, apellido o CI aunque estén cifrados en la base, sin importar tildes ni grafías (Quispe / Kispe, López / Lopez). | Alta | CP-002 |
| RF-03 | Importar pacientes desde Excel: plantilla, vista previa fila por fila, detección de CI duplicadas y confirmación. | Media | CP-003 |
| RF-04 | Mostrar cada listado paginado, con búsqueda, filtros, orden y cifras de cabecera calculadas sobre TODOS los registros, no solo la página visible. | Alta | CP-004, CP-020, CP-060 |
| RF-16 | Registrar el triaje de enfermería con signos vitales, prioridad (urgente / alta / normal / baja) y estado (pendiente / completado). | Alta | CP-071 |

## Embarazo y seguimiento

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-05 | Registrar el embarazo (uno activo por paciente), calcular edad gestacional y FPP, y redatar con la ecografía según ACOG. | Alta | CP-010, CP-011, CP-012 |
| RF-06 | Registrar controles prenatales y marcar alertas clínicas: PA ≥ 140/90, FCF fuera de 110–160 lpm, edema severo, proteinuria positiva, movimientos fetales ausentes. | Alta | CP-020, CP-021 |
| RF-07 | Registrar la ecografía con biometría (DBP, CC, CA, LF) e imágenes, y estimar el peso fetal con Hadlock 1985. | Alta | CP-030, CP-032 |
| RF-08 | Adjuntar archivos a una ecografía (imagen, DICOM, PDF, video), reconociendo el tipo por su contenido real. | Media | CP-037 |
| RF-09 | Analizar la imagen con redes entrenadas con ecografías reales: plano anatómico, circunferencia cefálica con edad gestacional y cribado de anomalías cerebrales, mostrando sus métricas. | Alta | CP-032 a CP-035 |
| RF-10 | Predecir el peso al nacer con el modelo supervisado para una semana elegida, mostrando Hadlock al lado, el margen de error y sus advertencias. | Media | CP-036 |
| RF-12 | Mantener el catálogo de exámenes con rangos de referencia y evaluar cada resultado como normal, anormal o crítico. | Alta | CP-050, CP-051, CP-052 |
| RF-13 | Importar resultados de laboratorio desde Excel: plantilla con catálogo, vista previa, evaluación contra rangos y sin duplicados. | Media | CP-053 |
| RF-14 | Registrar vacunas y señalar dosis pendientes, próximas y atrasadas. | Media | CP-060, CP-061 |
| RF-15 | Registrar notas de evolución de cada consulta (incluye las antiguas «evoluciones del embarazo»). | Media | CP-070 |
| RF-11 | Registrar el parto con uno o varios recién nacidos validados (peso, talla, perímetro cefálico, Apgar 1/5/10). | Alta | CP-040, CP-041 |
| RF-23 | Proteger la historia clínica: un registro con datos dependientes no se borra; lo que se borra queda auditado. | Alta | CP-013 |

## Apoyo clínico

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-17 | Calculadoras clínicas: edad gestacional, IMC, Bishop, preeclampsia (odds × LR), ILA, peso fetal, Apgar, Capurro, Silverman, Ballard, diabetes gestacional (IADPSG) y calculadoras especializadas. | Alta | CP-030, CP-080, CP-081, CP-082 |
| RF-20 | Enviar recordatorios de citas y alertas clínicas (alto riesgo, resultado crítico) al médico responsable, por WebSocket. | Media | CP-100 |

## Gestión

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-18 | Centro de reportes con pestañas: panel en tiempo real, estadísticas por fecha, KPIs, indicadores y metas, generador de PDF y auditoría. | Media | CP-105 |
| RF-19 | Exportar cada listado a Excel con los mismos filtros de la pantalla; la exportación queda auditada. | Media | CP-106 |
| RF-21 | Controlar el acceso por rol: cada rol ve y hace solo lo suyo, en la pantalla y en la API. | Alta | CP-090, CP-091 |
| RF-22 | Auditar sesiones (inicio, fin, IP, navegador), exportaciones y acciones sobre datos clínicos. | Alta | CP-092 |
