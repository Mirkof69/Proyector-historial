/**
 * Lógica pura del Score de Bishop: cálculo, datos de gráficas e historial mock.
 * Extraído de ScoreBishop para testeo aislado.
 */
import dayjs from 'dayjs';

export interface BishopScore {
  dilatacion: number;
  borramiento: number;
  estacion: number;
  consistencia: number;
  posicion: number;
}

export interface ResultadoBishop {
  puntaje: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  probabilidadExito: number;
}

export interface HistorialBishop {
  id: number;
  fecha: string;
  paciente: string;
  edadGestacional: number;
  puntaje: number;
  resultado: string;
}

export const BISHOP_DOMAIN = [0, 3];
export const TENDENCIA_DOMAIN = [0, 13];

export const calcularBishop = (values: BishopScore): ResultadoBishop => {
  const puntaje =
    values.dilatacion +
    values.borramiento +
    values.estacion +
    values.consistencia +
    values.posicion;

  let clasificacion = '';
  let color = '';
  let interpretacion = '';
  let recomendacion = '';
  let probabilidadExito = 0;

  if (puntaje >= 8) {
    clasificacion = 'FAVORABLE';
    color = 'success';
    interpretacion =
      'Cérvix favorable para inducción. Alta probabilidad de parto vaginal exitoso (>90%).';
    recomendacion =
      'Proceder con inducción según indicación clínica. Oxitocina IV o amniotomía. Monitoreo materno-fetal continuo.';
    probabilidadExito = 90 + puntaje;
  } else if (puntaje >= 6) {
    clasificacion = 'INTERMEDIO';
    color = 'warning';
    interpretacion =
      'Cérvix moderadamente favorable. Probabilidad intermedia de éxito (70-85%).';
    recomendacion =
      'Considerar maduración cervical con prostaglandinas (misoprostol 25 µg vaginal cada 3-6h o dinoprostona gel). Reevaluar Bishop en 12-24h antes de proceder con oxitocina.';
    probabilidadExito = 65 + puntaje * 2;
  } else {
    clasificacion = 'DESFAVORABLE';
    color = 'error';
    interpretacion =
      'Cérvix desfavorable. Alta probabilidad de falla de inducción y necesidad de cesárea (>40%).';
    recomendacion =
      'Maduración cervical obligatoria: prostaglandinas vaginales (misoprostol, dinoprostona) o sonda Foley. NO iniciar oxitocina. Reevaluar Bishop cada 24h. Considerar cesárea electiva según indicación.';
    probabilidadExito = 30 + puntaje * 5;
  }

  return {
    puntaje,
    clasificacion,
    color,
    interpretacion,
    recomendacion,
    probabilidadExito: Math.min(probabilidadExito, 99),
  };
};

export const getHistogramaData = (historial: HistorialBishop[]) => [
  { rango: '0-2', cantidad: historial.filter(h => h.puntaje <= 2).length, color: '#f5222d' },
  { rango: '3-5', cantidad: historial.filter(h => h.puntaje >= 3 && h.puntaje <= 5).length, color: '#fa8c16' },
  { rango: '6-7', cantidad: historial.filter(h => h.puntaje >= 6 && h.puntaje <= 7).length, color: '#faad14' },
  { rango: '8-10', cantidad: historial.filter(h => h.puntaje >= 8 && h.puntaje <= 10).length, color: '#52c41a' },
  { rango: '11-13', cantidad: historial.filter(h => h.puntaje >= 11).length, color: '#1890ff' },
];

export const getDistribucionPie = (historial: HistorialBishop[]) => {
  const favorable = historial.filter(h => h.puntaje >= 8).length;
  const intermedio = historial.filter(h => h.puntaje >= 6 && h.puntaje < 8).length;
  const desfavorable = historial.filter(h => h.puntaje < 6).length;

  return [
    { name: 'Favorable', value: favorable, color: '#52c41a' },
    { name: 'Intermedio', value: intermedio, color: '#faad14' },
    { name: 'Desfavorable', value: desfavorable, color: '#f5222d' },
  ];
};

export const getTendenciaData = (historial: HistorialBishop[]) =>
  historial.slice(0, 10).reverse().map((item) => ({
    fecha: dayjs(item.fecha).format('DD/MM HH:mm'),
    puntaje: item.puntaje,
    egSemanas: item.edadGestacional,
  }));

export const HISTORIAL_INICIAL: HistorialBishop[] = [
  { id: 1, fecha: '2024-12-18 10:30', paciente: 'María García', edadGestacional: 40, puntaje: 9, resultado: 'Favorable' },
  { id: 2, fecha: '2024-12-18 09:15', paciente: 'Carmen López', edadGestacional: 39, puntaje: 4, resultado: 'Desfavorable' },
  { id: 3, fecha: '2024-12-17 16:20', paciente: 'Ana Martínez', edadGestacional: 41, puntaje: 7, resultado: 'Intermedio' },
  { id: 4, fecha: '2024-12-17 14:10', paciente: 'Laura Fernández', edadGestacional: 40, puntaje: 10, resultado: 'Favorable' },
  { id: 5, fecha: '2024-12-16 11:45', paciente: 'Rosa Sánchez', edadGestacional: 38, puntaje: 3, resultado: 'Desfavorable' },
];
