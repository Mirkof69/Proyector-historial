# EfficientNet-B4 «14 patologías» — retirada el 01/10/2026

Se conserva solo la historia de esta red, para que quede claro por qué no se usa:

- Sus datos (`datos/legado_b4/`) tenían etiquetas no verificables: clases 100 %
  sintéticas, «signos de preeclampsia» que eran cortes normales de
  FETAL_PLANES_DB, «cardiopatías» que eran corazones normales de FOCUS, y el
  45 % de las imágenes de prueba repetidas en entrenamiento (auditoría en
  `datos/CATALOGO.md`).
- Sus métricas (AUC 0,96–1,00) medían esos atajos, no capacidad diagnóstica.

La reemplazan redes entrenadas con anotaciones de experto y medidas en
pacientes no vistas (ver el README del microservicio). Los informes
`ESTADO_RED_NEURONAL.md` y `OPTIMIZACION_MEDIDA.md` son el registro de lo que se
intentó con ella.
