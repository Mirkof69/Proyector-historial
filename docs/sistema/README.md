# Documentación del sistema — Fetal Medical Bolivia

Sistema de historia clínica gineco-obstétrica para hospitales y clínicas de
Bolivia: registro de pacientes, embarazo, controles prenatales, ecografías con
inteligencia artificial, laboratorio, vacunas, triaje, parto, reportes y
auditoría.

Versión del 01/10/2026 (rama `produccion-hospital`). Los diagramas están en
[Mermaid](https://mermaid.js.org/): se ven directamente en GitHub y en VS Code
con la extensión «Markdown Preview Mermaid Support». La carpeta
[`diagramas/`](diagramas/) tiene además cada diagrama exportado como imagen
SVG (28), con el nombre `<documento>_<n>.svg`. Si se cambia un diagrama, se
vuelven a exportar con `python docs/sistema/exportar_diagramas.py` (necesita
mermaid-cli; ver el encabezado del script).

## Contenido

| Documento | Qué contiene |
|---|---|
| [01 · Visión general](01_vision_general.md) | Propósito, alcance, roles, módulos y glosario |
| [02 · Requisitos funcionales](02_requisitos_funcionales.md) | RF-01 a RF-31, con prioridad y cómo se verifica cada uno |
| [03 · Requisitos no funcionales](03_requisitos_no_funcionales.md) | RNF-01 a RNF-16 con criterio medible y valor medido |
| [04 · Historias de usuario](04_historias_de_usuario.md) | HU-01 a HU-26 por rol, con criterios de aceptación |
| [05 · Casos de uso](05_casos_de_uso.md) | Diagrama de casos de uso y CU-01 a CU-08 detallados |
| [06 · Arquitectura](06_arquitectura.md) | Microservicios, componentes, multi-clínica, tecnologías |
| [07 · Modelo de datos](07_modelo_de_datos.md) | Diagrama entidad-relación de las entidades clínicas |
| [08 · Diagramas de secuencia](08_diagramas_de_secuencia.md) | Inicio de sesión, flujo clínico, análisis con IA, importación Excel, listados, notificaciones |
| [09 · Diagramas de estados y actividad](09_diagramas_de_estados.md) | Ciclo de vida de embarazo, cita, examen, triaje; actividad de la atención |
| [10 · Inteligencia artificial](10_inteligencia_artificial.md) | Redes con ecografías reales (plano, segmentación de cabeza, tórax, abdomen e intraparto, anomalías cerebrales), modelos supervisados (cardiotocografía y peso al nacer), métricas y límites |
| [11 · Despliegue y operación](11_despliegue_y_operacion.md) | Diagrama de despliegue, puertos, arranque, respaldo, seguridad |
| [12 · Trazabilidad](12_trazabilidad.md) | Matriz requisito → historia → caso de uso → caso de prueba |

Documentos relacionados fuera de esta carpeta:
[plan de producción](../PLAN_PRODUCCION_HOSPITAL.md) ·
[plan de QA y de pruebas](../QA_PLAN_DE_PRUEBAS.md) ·
[casos de prueba con resultado obtenido](../QA_CASOS_DE_PRUEBA.md).

## Convenciones

- **RF / RNF**: requisito funcional / no funcional.
- **HU**: historia de usuario. **CU**: caso de uso.
- **CP**: caso de prueba; el resultado real de cada uno está en
  [QA_CASOS_DE_PRUEBA.md](../QA_CASOS_DE_PRUEBA.md), que se genera ejecutando
  las pruebas.
