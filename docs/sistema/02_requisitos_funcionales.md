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
| RF-09 | Analizar la imagen con redes entrenadas con ecografías reales, en un solo flujo: plano anatómico → segmentación de su plano (cabeza: HC, DBP y edad gestacional; tórax: índice cardiotorácico; abdomen: corte adecuado para la CA) → cribado de anomalías cerebrales. Devuelve un informe estructurado (JSON) con la imagen y las estructuras dibujadas, y la métrica medida de cada red usada. | Alta | CP-032 a CP-035, CP-038, CP-039 |
| RF-10 | Predecir el peso al nacer con el modelo supervisado para una semana elegida, mostrando Hadlock al lado, el margen de error y sus advertencias. Cada predicción se guarda y se cierra sola con el peso real del recién nacido, para medir el error con nacimientos reales. | Media | CP-036, CP-084 |
| RF-12 | Mantener el catálogo de exámenes con rangos de referencia y evaluar cada resultado como normal, anormal o crítico. | Alta | CP-050, CP-051, CP-052 |
| RF-13 | Importar resultados de laboratorio desde Excel o CSV (coma, punto y coma o tabulador; UTF-8 o Latin-1): plantilla con catálogo, reconocimiento de encabezados por sinónimos y mapeo manual si hace falta, vista previa, evaluación contra rangos y sin duplicados. Cada lote se puede deshacer entero, con motivo y auditoría. | Media | CP-053, CP-054, CP-055 |
| RF-14 | Registrar vacunas y señalar dosis pendientes, próximas y atrasadas. | Media | CP-060, CP-061 |
| RF-15 | Registrar notas de evolución de cada consulta (incluye las antiguas «evoluciones del embarazo»). | Media | CP-070 |
| RF-11 | Registrar el parto con uno o varios recién nacidos validados (peso, talla, perímetro cefálico, Apgar 1/5/10) y verlo en cinco pestañas: admisión, trabajo de parto, recién nacidos, alumbramiento y complicaciones, epicrisis. | Alta | CP-040, CP-041 |
| RF-24 | Partograma: registrar tactos (dilatación, estación, contracciones, FCF, signos vitales, ángulo de progresión) y ver la curva de dilatación con las líneas de alerta y acción de la OMS; avisar si se cruzan. PDF del partograma. | Alta | CP-044 |
| RF-25 | Edad gestacional del recién nacido por examen físico: Capurro somático (204 + puntos) o nuevo Ballard ((2 × puntaje + 120) / 5), con su clasificación (pretérmino, a término, postérmino). | Media | CP-043 |
| RF-26 | Epicrisis del parto según el expediente clínico (Norma Técnica del Ministerio de Salud) y la HCP CLAP: diagnósticos con CIE-10, egreso, anticoncepción post evento, indicaciones y próximo control; firma con matrícula (firmada no se edita; solo el administrador la reabre, con motivo); PDF. | Alta | CP-042 |
| RF-27 | Campos propios del establecimiento en la epicrisis: el administrador los define (texto, número, fecha, sí/no, lista) y el formulario los muestra y valida sin cambiar el código. | Media | CP-042 |
| RF-28 | Ángulo de progresión intraparto: medir el AoP sobre una ecografía transperineal con la red de IUGC 2024, con su margen y el ángulo dibujado; el médico lo confirma antes de guardarlo en el tacto. | Media | CP-045 |
| RF-23 | Proteger la historia clínica: un registro con datos dependientes no se borra; lo que se borra queda auditado. | Alta | CP-013 |

## Apoyo clínico

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-17 | Calculadoras clínicas: edad gestacional, IMC, Bishop, preeclampsia (odds × LR), ILA, peso fetal, Apgar, Capurro, Silverman, Ballard, diabetes gestacional (IADPSG) y calculadoras especializadas. | Alta | CP-030, CP-080, CP-081, CP-082 |
| RF-20 | Enviar recordatorios de citas y alertas clínicas (alto riesgo, resultado crítico) al médico responsable, por WebSocket, dentro de la clínica que corresponde al dominio. | Media | CP-100 |
| RF-29 | Clasificar una cardiotocografía (normal, sospechosa, patológica) con el modelo supervisado entrenado con 2.126 registros reales, mostrando su fiabilidad medida y sus límites. | Media | CP-083 |
| RF-31 | Ecografía ginecológica con IA: (a) masa ovárica → contorno de la lesión, tipo probable entre 8 (con informe de anatomía patológica) y alarma de carcinoma seroso de alto grado; (b) mioma uterino → ubicación; (c) ovario normal, folículo dominante o poliquístico. Cada resultado muestra su fiabilidad medida y sus límites (una alarma ausente no descarta malignidad; la ubicación del mioma no descarta su presencia; SOP requiere los criterios de Rotterdam) y queda auditado. | Media | CP-085, CP-086, CP-087 |

## Gestión

| ID | Requisito | Prioridad | Verificado por |
|---|---|---|---|
| RF-18 | Centro de reportes con pestañas y un período común (hoy, 7 días, mes, año o rango): panel en tiempo real, estadísticas por fecha, natalidad y morbilidad, inteligencia artificial (uso, resultados y fiabilidad de cada modelo), KPIs, indicadores y metas, generador de PDF y auditoría; impresión de la pestaña abierta. | Media | CP-105, CP-107 |
| RF-19 | Exportar cada listado a Excel con los mismos filtros de la pantalla; la exportación queda auditada. | Media | CP-106 |
| RF-21 | Controlar el acceso por rol: cada rol ve y hace solo lo suyo, en la pantalla y en la API; todo permiso que pide la pantalla existe en el sistema. | Alta | CP-090, CP-091, CP-093 |
| RF-22 | Auditar sesiones (inicio, fin, IP, navegador), exportaciones y acciones sobre datos clínicos. | Alta | CP-092 |
| RF-30 | Cargos del hospital sin programar: el administrador crea un cargo (obstetriz, nutricionista…) sobre un rol y elige qué módulos de ese rol usa. Solo puede quitar módulos, nunca agregar; lo quitado desaparece del menú y la API lo rechaza (403). Cada alta, cambio y baja queda auditada; un cargo con usuarios no se borra. | Media | CP-112 |
