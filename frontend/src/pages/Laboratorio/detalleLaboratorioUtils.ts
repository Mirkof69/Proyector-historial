// =============================================================================
// UTILIDADES DE INTERPRETACIÓN — DETALLE DE LABORATORIO
// =============================================================================

// Función para interpretar resultados médicamente
export const interpretarResultado = (record: any): string => {
  if (!record.valor_numerico || !record.rango_referencia) return '';

  // Extraer min y max del rango (ej: "70 -125 mg/dL")
  const match = record.rango_referencia.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
  if (!match) return '';

  const min = parseFloat(match[1]);
  const max = parseFloat(match[2]);
  const valor = record.valor_numerico;

  if (valor < min) {
    const diff = ((min - valor) / min * 100).toFixed(1);
    return `${diff}% por debajo del mínimo`;
  }
  if (valor > max) {
    const diff = ((valor - max) / max * 100).toFixed(1);
    return `${diff}% por encima del máximo`;
  }
  return 'Dentro del rango esperado';
};

// Función para calcular porcentaje en rango
export const calcularPorcentajeEnRango = (record: any): number => {
  if (!record.valor_numerico || !record.rango_referencia) return 0;

  const match = record.rango_referencia.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
  if (!match) return 50;

  const min = parseFloat(match[1]);
  const max = parseFloat(match[2]);
  const valor = record.valor_numerico;

  if (valor < min) return 25;
  if (valor > max) return 75;

  // Dentro del rango: calcular posición
  const posicion = ((valor - min) / (max - min)) * 100;
  return Math.min(100, Math.max(0, posicion));
};
