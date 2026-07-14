export interface DatosPaciente {
  peso_pregestacional: number;
  talla: number;
  peso_actual: number;
  semanas_gestacion: number;
}

export interface ResultadoIMC {
  imc_pregestacional: number;
  clasificacion_imc: string;
  color_imc: string;
  ganancia_actual: number;
  ganancia_recomendada_min: number;
  ganancia_recomendada_max: number;
  ganancia_ideal_semana: number;
  ganancia_total_esperada: number;
  percentil_ganancia: number;
  estado_nutricional: string;
  recomendaciones: string[];
  alertas: string[];
}

export interface RegistroIMC {
  id: number;
  fecha: string;
  semanas: number;
  peso: number;
  ganancia: number;
  imc: number;
  estado: string;
}

export const renderIMCLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`;
export const formatPesoTooltip = (value: any) => value ? `${Number(value).toFixed(2)} kg` : '0 kg';

// Función para clasificar IMC según OMS
export const clasificarIMC = (imc: number): { clasificacion: string; color: string } => {
  if (imc < 18.5) return { clasificacion: 'BAJO PESO', color: '#faad14' };
  if (imc < 25) return { clasificacion: 'NORMAL', color: '#52c41a' };
  if (imc < 30) return { clasificacion: 'SOBREPESO', color: '#fa8c16' };
  if (imc < 35) return { clasificacion: 'OBESIDAD I', color: '#f5222d' };
  if (imc < 40) return { clasificacion: 'OBESIDAD II', color: '#cf1322' };
  return { clasificacion: 'OBESIDAD III', color: '#a8071a' };
};

// Función para obtener ganancia recomendada según IOM (Institute of Medicine)
export const getGananciaRecomendada = (imc: number): { min: number; max: number; semanal: number } => {
  if (imc < 18.5) return { min: 12.5, max: 18, semanal: 0.5 };
  if (imc < 25) return { min: 11.5, max: 16, semanal: 0.4 };
  if (imc < 30) return { min: 7, max: 11.5, semanal: 0.3 };
  return { min: 5, max: 9, semanal: 0.2 };
};

// Función para calcular percentil de ganancia
export const calcularPercentil = (imc: number, semanas: number, ganancia: number): number => {
  const gananciaRecomendada = getGananciaRecomendada(imc);
  const gananciaEsperada = gananciaRecomendada.semanal * semanas;
  const desviacion = (ganancia - gananciaEsperada) / gananciaEsperada;
  if (desviacion < -0.3) return 10;
  if (desviacion < -0.1) return 25;
  if (desviacion < 0.1) return 50;
  if (desviacion < 0.3) return 75;
  return 90;
};

export const calcularIMC = (values: DatosPaciente): ResultadoIMC => {
  const imc_pregestacional = values.peso_pregestacional / Math.pow(values.talla / 100, 2);
  const { clasificacion, color } = clasificarIMC(imc_pregestacional);
  const gananciaRecomendada = getGananciaRecomendada(imc_pregestacional);
  const ganancia_actual = values.peso_actual - values.peso_pregestacional;
  const ganancia_esperada_semana = gananciaRecomendada.semanal * values.semanas_gestacion;
  const percentil = calcularPercentil(imc_pregestacional, values.semanas_gestacion, ganancia_actual);

  let estado_nutricional = '';
  let alertas: string[] = [];
  let recomendaciones: string[] = [];

  if (ganancia_actual < gananciaRecomendada.min) {
    estado_nutricional = '⚠️ GANANCIA INSUFICIENTE';
    alertas.push('Ganancia de peso por debajo del rango recomendado');
    recomendaciones.push('Aumentar ingesta calórica en 300-500 kcal/día');
    recomendaciones.push('Consulta nutricional especializada');
    recomendaciones.push('Monitoreo de crecimiento fetal con ecografía');
  } else if (ganancia_actual > gananciaRecomendada.max) {
    estado_nutricional = '⚠️ GANANCIA EXCESIVA';
    alertas.push('Ganancia de peso por encima del rango recomendado');
    recomendaciones.push('Control dietético y actividad física moderada');
      recomendaciones.push('Evaluar retención de líquidos y descartar preeclampsia');
      recomendaciones.push('Screening de diabetes gestacional');
    } else {
      estado_nutricional = '✅ GANANCIA ADECUADA';
      recomendaciones.push('Mantener alimentación balanceada actual');
      recomendaciones.push('Continuar con actividad física regular');
      recomendaciones.push('Controles prenatales según protocolo');
    }

    if (imc_pregestacional < 18.5) {
      recomendaciones.push('🔹 Bajo peso: Dieta hipercalórica (2200-2400 kcal/día)');
      recomendaciones.push('Suplementación con ácidos grasos omega-3');
    } else if (imc_pregestacional >= 30) {
      recomendaciones.push('🔹 Obesidad: Control estricto de ganancia ponderal');
      recomendaciones.push('Evaluación para riesgo de diabetes gestacional y preeclampsia');
      recomendaciones.push('Dieta balanceada normocalórica (1800-2000 kcal/día)');
    }

    return {
      imc_pregestacional,
      clasificacion_imc: clasificacion,
      color_imc: color,
      ganancia_actual,
      ganancia_recomendada_min: gananciaRecomendada.min,
      ganancia_recomendada_max: gananciaRecomendada.max,
      ganancia_ideal_semana: gananciaRecomendada.semanal,
      ganancia_total_esperada: ganancia_esperada_semana,
      percentil_ganancia: percentil,
      estado_nutricional,
      recomendaciones,
      alertas
    };
  };

// Datos para gráfica de curvas de ganancia ponderal (P10, P50, P90)
export const getCurvasGanancia = (values: DatosPaciente, resultado: ResultadoIMC | null) => {
  const semanas = Array.from({ length: 40 }, (_, i) => i + 1);
  const gananciaRecomendada = getGananciaRecomendada(values.peso_pregestacional / Math.pow(values.talla / 100, 2));

  return semanas.map(semana => {
    const gananciaP50 = gananciaRecomendada.semanal * semana;
    const gananciaP10 = gananciaP50 * 0.6;
    const gananciaP90 = gananciaP50 * 1.4;
    const gananciaActual = semana === values.semanas_gestacion ? resultado?.ganancia_actual : null;

    return {
      semana,
      P10: gananciaP10,
      P50: gananciaP50,
      P90: gananciaP90,
      Actual: gananciaActual
    };
  });
};

// Datos para gráfica de distribución de componentes del peso
export const getComponentesPeso = (resultado: ResultadoIMC | null) => {
  const gananciaTotal = resultado?.ganancia_actual || 0;

  return [
    { name: 'Feto', value: gananciaTotal * 0.25, porcentaje: 25, color: '#1890ff' },
    { name: 'Placenta', value: gananciaTotal * 0.05, porcentaje: 5, color: '#13c2c2' },
    { name: 'Líquido Amniótico', value: gananciaTotal * 0.06, porcentaje: 6, color: '#52c41a' },
    { name: 'Útero + Mamas', value: gananciaTotal * 0.10, porcentaje: 10, color: '#722ed1' },
    { name: 'Sangre', value: gananciaTotal * 0.12, porcentaje: 12, color: '#eb2f96' },
    { name: 'Líquidos Extracelulares', value: gananciaTotal * 0.17, porcentaje: 17, color: '#fa8c16' },
    { name: 'Reservas Grasas', value: gananciaTotal * 0.25, porcentaje: 25, color: '#faad14' }
  ];
};

// Datos para gráfica de comparación por trimestre
export const getComparacionTrimestre = (values: DatosPaciente, resultado: ResultadoIMC | null) => {
  const imc = values.peso_pregestacional / Math.pow(values.talla / 100, 2);
  const gananciaRecomendada = getGananciaRecomendada(imc);

  return [
    {
      trimestre: '1er Trimestre',
      Actual: values.semanas_gestacion >= 13 ? gananciaRecomendada.semanal * 13 * 0.3 : resultado?.ganancia_actual || 0,
      Recomendada: gananciaRecomendada.semanal * 13 * 0.3,
      Min: gananciaRecomendada.min * 0.1,
      Max: gananciaRecomendada.max * 0.1
    },
    {
      trimestre: '2do Trimestre',
      Actual: values.semanas_gestacion >= 27 ? gananciaRecomendada.semanal * 14 * 1.2 : (values.semanas_gestacion > 13 ? resultado?.ganancia_actual || 0 : 0),
      Recomendada: gananciaRecomendada.semanal * 14 * 1.2,
      Min: gananciaRecomendada.min * 0.35,
      Max: gananciaRecomendada.max * 0.35
    },
    {
      trimestre: '3er Trimestre',
      Actual: values.semanas_gestacion > 27 ? resultado?.ganancia_actual || 0 : 0,
      Recomendada: gananciaRecomendada.semanal * 13 * 1.5,
      Min: gananciaRecomendada.min * 0.55,
      Max: gananciaRecomendada.max * 0.55
    }
  ];
};

// Datos para evolución temporal del IMC
export const getEvolucionIMC = (historial: RegistroIMC[]) => {
  return historial.slice().reverse().map(registro => ({
    fecha: registro.fecha,
    semanas: registro.semanas,
    imc: registro.imc.toFixed(1),
    peso: registro.peso
  }));
};
