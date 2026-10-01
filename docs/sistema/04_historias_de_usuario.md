# 04 · Historias de usuario

Formato: **Como** rol, **quiero** algo, **para** un beneficio. Los criterios de
aceptación están en forma *Dado / Cuando / Entonces* o como condiciones
verificables. Cada historia indica los requisitos que cubre y los casos de
prueba que la verifican.

## Recepción

### HU-01 · Registrar a una paciente nueva
**Como** recepcionista, **quiero** registrar a una paciente nueva con su consentimiento, **para** abrir su historia clínica cumpliendo la Ley 164.
- Dado el asistente de registro, cuando no se marca el consentimiento, entonces no se puede guardar.
- Cuando se guarda, el sistema asigna un ID clínico y ofrece registrar su embarazo con ella ya elegida.

Requisitos: RF-01 · Pruebas: CP-001

### HU-02 · Encontrar a una paciente aunque escriba distinto
**Como** recepcionista, **quiero** encontrar a una paciente escribiendo su apellido sin tilde o con otra grafía, **para** no duplicar registros.
- «lopez» encuentra a «López» y «kispe» a «Quispe».
- Una CI incompleta no devuelve a otra paciente.

Requisitos: RF-02 · Pruebas: CP-002

## Enfermería

### HU-11 · Triaje con prioridad
**Como** enfermera, **quiero** registrar el triaje con su prioridad, **para** que el médico atienda primero lo urgente.
- La prioridad elegida se guarda y se ve en el listado.
- El triaje se puede marcar como completado.

Requisitos: RF-16 · Pruebas: CP-071

### HU-12 · Vacunas pendientes
**Como** enfermera, **quiero** ver las vacunas pendientes y atrasadas, **para** completar los esquemas.
- Las cifras cuentan todas las vacunas, aunque pasen de 200.
- Se puede corregir un registro antiguo aunque su próxima dosis ya haya pasado.

Requisitos: RF-14 · Pruebas: CP-060, CP-061

## Médico/a

### HU-04 · Embarazo y edad gestacional
**Como** médica, **quiero** registrar el embarazo y ver la edad gestacional correcta, **para** planificar los controles.
- No se permite un segundo embarazo activo para la misma paciente.
- Si la ecografía difiere de la FUM más de lo permitido (ACOG), se redata.
- Un embarazo terminado muestra la edad gestacional del parto, no semanas imposibles.

Requisitos: RF-05 · Pruebas: CP-010, CP-011, CP-012

### HU-05 · Control prenatal con alertas
**Como** médica, **quiero** registrar un control prenatal y ver sus alertas, **para** detectar a tiempo la hipertensión o el sufrimiento fetal.
- PA ≥ 140/90, FCF fuera de 110–160, edema severo o proteinuria positiva marcan alerta.
- El filtro «con alertas» coincide con la columna del listado.

Requisitos: RF-06 · Pruebas: CP-020, CP-021

### HU-06 · Ecografía con biometría
**Como** médica, **quiero** registrar la ecografía con su biometría e imágenes, **para** seguir el crecimiento fetal.
- Un feto de término tiene un peso estimado de 2.500 a 3.500 g, nunca 0.
- Las imágenes solo las ven los usuarios autorizados.

Requisitos: RF-07 · Pruebas: CP-030, CP-031, CP-032

### HU-17 · Adjuntos de la ecografía
**Como** médica, **quiero** adjuntar un DICOM o un informe PDF a la ecografía, **para** tener todo el estudio en un lugar.
- El tipo se reconoce por el contenido del archivo.
- Recepción no ve los adjuntos.

Requisitos: RF-08 · Pruebas: CP-037

### HU-07 · Análisis con IA confiable
**Como** médica, **quiero** analizar la imagen con la IA y saber cuánto confiar en ella, **para** apoyar mi decisión sin reemplazarla.
- Reconoce el plano y mide la cabeza con el error medido en madres no vistas.
- La red de anomalías no da alarma en una cabeza normal ni en imágenes que no son cabezas.
- Si el microservicio no está disponible, el mensaje lo dice.

Requisitos: RF-09 · Pruebas: CP-032 a CP-035

### HU-08 · Peso al nacer
**Como** médica, **quiero** estimar el peso al nacer a una semana elegida, **para** anticipar macrosomía o bajo peso.
- Muestra Hadlock al lado y el margen de error.
- Sin modelo, en gemelares o antes de 20 semanas se niega explicando el motivo.

Requisitos: RF-10 · Pruebas: CP-036

### HU-09 · Parto gemelar
**Como** médica, **quiero** registrar un parto gemelar, **para** que consten los dos recién nacidos.
- Se guardan ambos con su peso y Apgar; un Apgar no registrado no aparece como 0.
- Si un recién nacido tiene datos imposibles, no queda un parto a medias.

Requisitos: RF-11 · Pruebas: CP-040, CP-041

### HU-13 · Diabetes gestacional
**Como** médica, **quiero** evaluar la PTOG de 75 g, **para** diagnosticar diabetes gestacional según la norma.
- Un solo valor alterado basta (IADPSG: ayunas ≥ 92, 1 h ≥ 180, 2 h ≥ 153 mg/dL).
- Ayunas ≥ 126 se informa como diabetes manifiesta.

Requisitos: RF-17 · Pruebas: CP-080

### HU-16 · Recordatorios de citas
**Como** médica, **quiero** recibir el recordatorio de mis citas, **para** no perder ninguna consulta.
- Una cita a las 23:00 también recibe su recordatorio (fecha de Bolivia, no UTC).

Requisitos: RF-20 · Pruebas: CP-100

### HU-18 · Notas de evolución
**Como** médica, **quiero** registrar notas de evolución, **para** documentar cada consulta.
- Las antiguas evoluciones del embarazo aparecen como notas, sin perder ninguna.
- Borrar una nota pide confirmación.

Requisitos: RF-15 · Pruebas: CP-070

## Laboratorio

### HU-10 · Carga de resultados por Excel
**Como** laboratorista, **quiero** cargar los resultados desde un Excel, **para** no tipear cada valor.
- La plantilla trae el catálogo de exámenes, parámetros y rangos.
- Cada valor se evalúa contra su rango; reimportar el mismo archivo no duplica.

Requisitos: RF-12, RF-13 · Pruebas: CP-050, CP-051, CP-053

## Administrador/a

### HU-03 · Importar pacientes
**Como** administradora, **quiero** importar pacientes desde un Excel, **para** cargar el padrón sin tipear una por una.
- La vista previa no guarda nada y explica cada error.
- Solo se crean las filas válidas; las CI repetidas se omiten.

Requisitos: RF-03 · Pruebas: CP-003

### HU-14 · Reportes y exportación
**Como** administradora, **quiero** ver reportes y exportar listados a Excel, **para** informar a la dirección del hospital.
- Las cifras «del mes» usan la fecha de Bolivia.
- El Excel trae lo filtrado en pantalla y la exportación queda auditada.

Requisitos: RF-18, RF-19 · Pruebas: CP-105, CP-106

### HU-15 · Accesos y auditoría
**Como** administradora, **quiero** controlar quién ve qué y revisar las sesiones, **para** proteger la información clínica.
- Recepción solo ve pacientes y citas.
- Un médico nuevo ve lo clínico sin configurar nada a mano.
- Las sesiones y exportaciones quedan auditadas.

Requisitos: RF-21, RF-22 · Pruebas: CP-090, CP-091, CP-092
