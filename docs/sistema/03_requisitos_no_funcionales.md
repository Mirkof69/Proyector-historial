# 03 · Requisitos no funcionales

Cada requisito tiene un criterio que se puede medir. «Valor medido» es lo que
se obtuvo el 01/10/2026 con la demo de 3.200 pacientes.

| ID | Categoría | Requisito | Criterio medible | Valor medido | Verificado por |
|---|---|---|---|---|---|
| RNF-01 | Rendimiento | Los listados responden rápido aun con miles de registros, también en redes lentas. | Pantalla < 5 s y ≤ 15 peticiones; API p95 < 200 ms | Pantalla ≈ 2 s y 6–12 peticiones. API con waitress (producción): 16/16 rutas con p95 < 200 ms, mediana 5–53 ms; búsqueda de pacientes 367 → 31 ms | CP-110, CP-111 |
| RNF-02 | Robustez | Ninguna pantalla falla con error interno; si la IA está caída, el mensaje es claro y el resto sigue funcionando. | 0 respuestas 500 en ≈330 rutas GET; IA apagada → 503 con texto | 0 errores 500 | CP-102, CP-035 |
| RNF-03 | Seguridad | Archivos clínicos solo para usuarios autorizados; el tipo de archivo se valida por su contenido. | Sin sesión o recepción → denegado; HTML disfrazado de PDF → rechazado | Cumple | CP-031, CP-037 |
| RNF-04 | Privacidad | Nombre, apellidos, CI, teléfono, correo y dirección van cifrados; la búsqueda no los expone. | Búsqueda por hash o descifrado controlado; nunca se ordena por campos cifrados | Cumple | CP-002, CP-004 |
| RNF-05 | Trazabilidad | Toda acción sensible queda registrada en una auditoría que no se puede alterar (trigger en la base). | Inicio/fin de sesión, exportaciones y acciones masivas auditadas | Cumple | CP-092 |
| RNF-06 | Exactitud clínica | Cada cálculo tiene una sola implementación; pantalla y servidor dan el mismo número. | Mismos valores de prueba en backend y frontend | Peso fetal 2.959 g (caso de término) en ambos lados | CP-030, CP-051, CP-080, CP-081, CP-082 |
| RNF-07 | Honestidad de la IA | La IA no inventa resultados y muestra cuánto se puede confiar en ella. | Métricas medidas en datos no vistos; sin modelo → 503/409; advertencias visibles; la API reproduce lo medido al entrenar | Plano 92,7 %; HC por segmentación en otro hospital 4,4 mm (92 % dentro del 5 %); tórax Dice 0,93; CTG 96,0 % en 423 registros; AoP 6,7°; B4 sin métrica válida retirada | CP-033, CP-034, CP-036, CP-038, CP-083 |
| RNF-08 | Localización | Fechas y horas en la zona horaria de Bolivia (UTC−4); interfaz en español. | Recordatorios y cifras «del mes» correctos entre 20:00 y 24:00 | Cumple | CP-100 |
| RNF-09 | Operabilidad | Arranca con doble clic; respaldo diario restaurable. | Lanzadores con comandos y opciones válidos; restauración probada | Cumple | CP-101 |
| RNF-10 | Calidad de datos | Los datos de demostración son realistas y válidos. | Pasan las validaciones del modelo; ninguna fecha futura | 0 registros inválidos | CP-103 |
| RNF-11 | Usabilidad y accesibilidad | Botones de icono con etiqueta accesible; confirmación antes de borrar; mensajes de error que explican qué corregir. | Revisión de pantallas | Aplicado en las pantallas modificadas | Revisión manual |
| RNF-12 | Mantenibilidad | Puertas de calidad en cada cambio. | CI: ruff, pytest con cobertura ≥ 55 %, tsc, eslint sin errores, tests de IA | Backend 999 (6 omitidas), Jest 124, microservicio 30, E2E 13 en verde; 57/57 casos de prueba (02/10/2026) | CI |
| RNF-13 | Escalabilidad | Varias clínicas en una instalación, con datos separados. | Un esquema de PostgreSQL por clínica (django-tenants) | Cumple | Arquitectura |
| RNF-14 | Disponibilidad | Atender carga real del hospital (100 pacientes al día ≈ 0,05 peticiones/s). | 40 usuarios simultáneos con pausas reales sin errores | 9 peticiones/s, mediana 49 ms, p95 252 ms, 0 errores (`quality-assurance/prueba_concurrencia.py`); repetir en el servidor definitivo | Prueba de carga |
| RNF-15 | Extensibilidad | El hospital agrega datos propios sin programar. | Campos adicionales de epicrisis definidos por el administrador | Cumple (texto, número, fecha, sí/no, lista; validados) | CP-042 |
| RNF-16 | Fiabilidad de las alertas | Una notificación creada por la API llega en vivo aunque los WebSockets corran en otro proceso. | Redis como canal entre procesos; aviso `notifications_websocket.W001` si falta en producción | 0,16 s con Redis; sin Redis no llegaba nunca (01/10/2026) | CP-108 |
