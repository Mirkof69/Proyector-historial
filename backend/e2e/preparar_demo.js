// Copia al Escritorio los archivos de muestra para la demostración en vivo, con la
// misma selección que tests/ia-modelos.spec.js y tests/ginecologia.spec.js
// (imágenes de PRUEBA: pacientes que las redes no vieron al entrenar).
//   node preparar_demo.js
const fs = require('fs');
const path = require('path');

const IA = path.join(__dirname, '..', '..', 'redes-neuronales');
const ENT = path.join(IA, 'entrenamiento');
const DESTINO = path.join(process.env.USERPROFILE, 'Desktop', 'DEMO_Fetal_Medical');

const csv = (ruta) => {
  if (!fs.existsSync(ruta)) return [];
  const [cab, ...filas] = fs.readFileSync(ruta, 'utf8').trim().split(/\r?\n/);
  const col = cab.split(',');
  return filas.map((f) => Object.fromEntries(f.split(',').map((v, i) => [col[i], v])));
};
const campos = (linea) => (linea.match(/("([^"]|"")*"|[^,]*)(,|$)/g) || [])
  .map((c) => c.replace(/,$/, '').replace(/^"|"$/g, '').replace(/""/g, '"'));
const imagenDePrueba = (catalogo, columnaClase, clase) => {
  const ruta = path.join(ENT, 'ginecologia', 'catalogos', catalogo);
  if (!fs.existsSync(ruta)) return null;
  const [cabecera, ...filas] = fs.readFileSync(ruta, 'utf8').trim().split(/\r?\n/);
  const col = campos(cabecera);
  const fila = filas.map(campos).find((f) => f[col.indexOf('particion')] === 'prueba'
    && (!clase || f[col.indexOf(columnaClase)] === clase));
  return fila ? path.join(IA, fila[col.indexOf('imagen')]) : null;
};
const MULTI = path.join(IA, 'datos', 'extraidos', 'obstetricia', 'FetalBiometry-Multicentre-Landmarks-2026', 'images', 'MULTICENTRE');
const conPx = (tarea, carpeta) => {
  const f = csv(path.join(ENT, 'biometria', 'salidas', tarea, 'prueba_medidas.csv'))[0];
  return f ? [path.join(MULTI, carpeta, f.imagen), Number(f.mm_por_px).toFixed(4)] : [null, ''];
};
const torax = csv(path.join(ENT, 'segmentacion', 'catalogos', 'torax.csv')).find((r) => r.particion === 'prueba');
const intra = csv(path.join(ENT, 'segmentacion', 'salidas', 'intraparto', 'prueba_medidas.csv'))[0];
const pco = csv(path.join(ENT, 'ginecologia', 'catalogos', 'ovario_pco.csv')).find((r) => r.clase_nombre === 'poliquistico');
const dirCerebro = path.join(IA, 'datos', 'extraidos', 'fetal_brain_abnormalities', 'test');
const cerebro = fs.existsSync(dirCerebro)
  ? fs.readdirSync(dirCerebro).find((n) => n.includes('ventriculomegaly') && n.endsWith('.jpg')) : null;
const [femur, pxFemur] = conPx('femur', 'Femur');
const [abdomen, pxAbdomen] = conPx('abdomen', 'Abdomen');

const muestras = [
  ['01_cabeza_fetal_HC18', path.join(ENT, 'redes_ecografia_real', 'imagenes', 'hc18', '147_HC.png'),
    'Análisis CNN (IA) → Ecografía. Tamaño de píxel: 0.074836 mm. Circunferencia cefálica de referencia: 88,81 mm.'],
  ['02_torax_fetal', torax && path.join(IA, torax.imagen), 'Análisis CNN (IA) → Ecografía → «Informe completo» (índice cardiotorácico).'],
  ['03_abdomen_fetal', abdomen, `Análisis CNN (IA) → Ecografía → «Informe completo». Tamaño de píxel: ${pxAbdomen} mm.`],
  ['04_femur_fetal', femur, `Análisis CNN (IA) → Ecografía → «Informe completo». Tamaño de píxel: ${pxFemur} mm.`],
  ['05_cerebro_ventriculomegalia', cerebro && path.join(dirCerebro, cerebro),
    'Análisis CNN (IA) → Ecografía → «Analizar» (cribado de anomalías cerebrales).'],
  ['06_intraparto_angulo_progresion', intra && path.join(IA, intra.imagen),
    'Partos → abrir un parto → pestaña Trabajo de parto → Registrar tacto → subir imagen y medir.'],
  ['07_ovario_teratoma', imagenDePrueba('ovario.csv', 'clase_nombre', 'teratoma'),
    'Análisis CNN (IA) → Ecografía ginecológica → Masa ovárica.'],
  ['08_mioma_uterino', imagenDePrueba('mioma.csv', null, null), 'Análisis CNN (IA) → Ecografía ginecológica → Mioma.'],
  ['09_ovario_poliquistico', pco && path.join(IA, pco.ruta), 'Análisis CNN (IA) → Ecografía ginecológica → Ovario poliquístico.'],
];

fs.mkdirSync(DESTINO, { recursive: true });
const leeme = ['ARCHIVOS PARA LA DEMOSTRACIÓN — Fetal Medical Bolivia',
  'Imágenes reales de los conjuntos de PRUEBA (las redes no las vieron al entrenar).', ''];
for (const [nombre, origen, uso] of muestras) {
  if (!origen || !fs.existsSync(origen)) {
    leeme.push(`${nombre}: NO DISPONIBLE (falta el dataset en esta PC)`);
    continue;
  }
  const archivo = nombre + path.extname(origen).toLowerCase();
  fs.copyFileSync(origen, path.join(DESTINO, archivo));
  leeme.push(`${archivo}\n   ${uso}`);
  console.log('ok', archivo);
}
const ctg = csv(path.join(__dirname, '..', 'ia_medica', 'ml', 'datos', 'fetal_health.csv')).find((r) => r.fetal_health === '3.0');
if (ctg) {
  leeme.push('', 'CARDIOTOCOGRAFÍA PATOLÓGICA (registro real, consenso de 3 obstetras)',
    'Análisis CNN (IA) → pestaña Cardiotocografía. Valores a ingresar:');
  // las etiquetas son las de la pantalla (backend/ia_medica/ml/cardiotocografia.py, VARIABLES)
  const ETIQUETA = {
    'baseline value': 'Línea de base de la FCF (lpm)', accelerations: 'Aceleraciones (por segundo)',
    fetal_movement: 'Movimientos fetales (por segundo)', uterine_contractions: 'Contracciones uterinas (por segundo)',
    light_decelerations: 'Desaceleraciones leves (por segundo)', severe_decelerations: 'Desaceleraciones severas (por segundo)',
    prolongued_decelerations: 'Desaceleraciones prolongadas (por segundo)',
    abnormal_short_term_variability: 'Tiempo con variabilidad a corto plazo anormal (%)',
    mean_value_of_short_term_variability: 'Variabilidad a corto plazo media (lpm)',
    percentage_of_time_with_abnormal_long_term_variability: 'Tiempo con variabilidad a largo plazo anormal (%)',
    mean_value_of_long_term_variability: 'Variabilidad a largo plazo media (lpm)',
    histogram_width: 'Histograma: ancho (lpm)', histogram_min: 'Histograma: mínimo (lpm)',
    histogram_max: 'Histograma: máximo (lpm)', histogram_number_of_peaks: 'Histograma: número de picos',
    histogram_number_of_zeroes: 'Histograma: número de ceros', histogram_mode: 'Histograma: moda (lpm)',
    histogram_mean: 'Histograma: media (lpm)', histogram_median: 'Histograma: mediana (lpm)',
    histogram_variance: 'Histograma: varianza', histogram_tendency: 'Histograma: tendencia (−1, 0, 1)',
  };
  for (const [k, v] of Object.entries(ctg)) if (k !== 'fetal_health') leeme.push(`   ${ETIQUETA[k] || k} = ${Number(v)}`);
  leeme.push('   Resultado esperado: «Patológica».');
}
fs.writeFileSync(path.join(DESTINO, 'LEEME_DEMO.txt'), leeme.join('\r\n'), 'utf8');
console.log('Listo:', DESTINO);
