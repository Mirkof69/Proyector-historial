// ==========================================================================
// TIPOS
// ==========================================================================
export interface DatosBiometria {
  semanas: number;
  bpd: number;
  hc: number;
  ac: number;
  fl: number;
  formula: 'hadlock1' | 'hadlock2' | 'hadlock3' | 'hadlock4';
}

export interface ResultadoCrecimiento {
  efw: number;
  percentil: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  zscore: number;
  desviacion_estandar: number;
  bpd_percentil: number;
  hc_percentil: number;
  ac_percentil: number;
  fl_percentil: number;
  categoria: 'RCIU' | 'PEG' | 'NORMAL' | 'GEG' | 'MACROSOMIA';
}

export interface RegistroCrecimiento extends ResultadoCrecimiento {
  fecha: string;
  semanas: number;
  bpd: number;
  hc: number;
  ac: number;
  fl: number;
}

// ==========================================================================
// REDUCER FOR GROWTH STATE (replaces cascading setState)
// ==========================================================================
export interface GrowthState {
  resultado: ResultadoCrecimiento | null;
  historial: RegistroCrecimiento[];
  datosBiometria: DatosBiometria | null;
  usandoDatosEjemplo: boolean;
}

export type GrowthAction =
  | { type: 'CALCULATE'; payload: { datos: DatosBiometria; resultado: ResultadoCrecimiento; registro: RegistroCrecimiento } }
  | { type: 'RESET' };

export function growthReducer(state: GrowthState, action: GrowthAction): GrowthState {
  switch (action.type) {
    case 'CALCULATE':
      return {
        resultado: action.payload.resultado,
        historial: [action.payload.registro, ...state.historial],
        datosBiometria: action.payload.datos,
        usandoDatosEjemplo: false,
      };
    case 'RESET':
      return {
        resultado: null,
        historial: [],
        datosBiometria: null,
        usandoDatosEjemplo: false,
      };
    default:
      return state;
  }
}

export const initialGrowthState: GrowthState = {
  resultado: null,
  historial: [],
  datosBiometria: null,
  usandoDatosEjemplo: false,
};

export const PROPORCIONES_DOMAIN = [0, 1.5];
export const formatPesoTooltip = (value: any) => value ? `${Number(value).toFixed(0)}g` : '';
export const formatRatioTooltip = (value: any) => value ? Number(value).toFixed(3) : '';
export const renderPercentilLabel = ({ name, value }: { name: string; value: number }) => `${name}: p${(value || 0).toFixed(0)}`;
export const formatPercentilTooltip = (value: any) => value ? `p${Number(value).toFixed(1)}` : '';

// Fórmulas de Hadlock para EFW
export const calcularEFW = (valores: DatosBiometria): number => {
  const { bpd, hc, ac, fl, formula } = valores;
  let efw = 0;

  switch (formula) {
    case 'hadlock1':
      const log_efw1 = 1.3596 + 0.0064 * hc + 0.0424 * ac + 0.174 * fl + 0.00061 * bpd * ac - 0.00386 * ac * fl;
      efw = Math.pow(10, log_efw1);
      break;
    case 'hadlock2':
      const log_efw2 = 1.304 + 0.05281 * ac + 0.1938 * fl - 0.004 * ac * fl;
      efw = Math.pow(10, log_efw2);
      break;
    case 'hadlock3':
      const log_efw3 = 1.335 - 0.0034 * ac * fl + 0.0316 * bpd + 0.0457 * ac + 0.1623 * fl;
      efw = Math.pow(10, log_efw3);
      break;
    case 'hadlock4':
      const log_efw4 = 1.326 - 0.00326 * ac * fl + 0.0107 * hc + 0.0438 * ac + 0.158 * fl;
      efw = Math.pow(10, log_efw4);
      break;
    default:
      efw = 0;
  }

  return efw;
};

// Percentiles de EFW según edad gestacional (basado en curvas Intergrowth-21st)
export const getMedianaEFW = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    20: 300, 21: 360, 22: 430, 23: 501, 24: 600, 25: 660, 26: 760,
    27: 875, 28: 1005, 29: 1153, 30: 1319, 31: 1502, 32: 1702,
    33: 1918, 34: 2146, 35: 2383, 36: 2622, 37: 2859, 38: 3083,
    39: 3288, 40: 3462, 41: 3597, 42: 3685
  };
  const semana_int = Math.round(semanas);
  return medianas[semana_int] || 2500;
};

export const getSDEFW = (semanas: number): number => {
  return getMedianaEFW(semanas) * 0.15;
};

export const zscoreToPercentile = (zscore: number): number => {
  const t = 1 / (1 + 0.2316419 * Math.abs(zscore));
  const d = 0.3989423 * Math.exp(-zscore * zscore / 2);
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));

  if (zscore > 0) {
    return (1 - p) * 100;
  } else {
    return p * 100;
  }
};

export const calcularPercentil = (efw: number, semanas: number): number => {
  const mediana = getMedianaEFW(semanas);
  const sd = getSDEFW(semanas);
  const zscore = (efw - mediana) / sd;
  return zscoreToPercentile(zscore);
};

// Percentiles de biometría individual (BPD, HC, AC, FL)
export const calcularPercentilBiometria = (valor: number, tipo: 'bpd' | 'hc' | 'ac' | 'fl', semanas: number): number => {
  const medianas: { [key: string]: { [key: number]: number } } = {
    bpd: { 20: 47, 22: 54, 24: 61, 26: 67, 28: 73, 30: 78, 32: 83, 34: 87, 36: 90, 38: 93, 40: 95 },
    hc: { 20: 175, 22: 200, 24: 224, 26: 247, 28: 269, 30: 289, 32: 307, 34: 323, 36: 336, 38: 347, 40: 355 },
    ac: { 20: 150, 22: 175, 24: 201, 26: 227, 28: 253, 30: 279, 32: 304, 34: 327, 36: 348, 38: 366, 40: 381 },
    fl: { 20: 33, 22: 39, 24: 45, 26: 51, 28: 56, 30: 61, 32: 65, 34: 69, 36: 72, 38: 75, 40: 77 }
  };

  const semana_int = Math.round(semanas);
  const mediana = medianas[tipo][semana_int] || medianas[tipo][Math.min(...Object.keys(medianas[tipo]).reduce<number[]>((acc, k) => { const n = Number(k); if (n <= semana_int) acc.push(n); return acc; }, []))];
  const sd = mediana * 0.1;
  const zscore = (valor - mediana) / sd;

  return zscoreToPercentile(zscore);
};

export const calcularCrecimiento = (valores: DatosBiometria): ResultadoCrecimiento => {
  const efw = calcularEFW(valores);
  const percentil = calcularPercentil(efw, valores.semanas);
  const mediana = getMedianaEFW(valores.semanas);
  const sd = getSDEFW(valores.semanas);
  const zscore = (efw - mediana) / sd;

  const bpd_percentil = calcularPercentilBiometria(valores.bpd, 'bpd', valores.semanas);
  const hc_percentil = calcularPercentilBiometria(valores.hc, 'hc', valores.semanas);
  const ac_percentil = calcularPercentilBiometria(valores.ac, 'ac', valores.semanas);
  const fl_percentil = calcularPercentilBiometria(valores.fl, 'fl', valores.semanas);

  let clasificacion = '';
  let color = '';
  let interpretacion = '';
  let recomendacion = '';
  let categoria: 'RCIU' | 'PEG' | 'NORMAL' | 'GEG' | 'MACROSOMIA' = 'NORMAL';

  if (percentil < 3) {
    clasificacion = '🔴 RCIU (Restricción del Crecimiento Intrauterino)';
    color = '#f5222d';
    categoria = 'RCIU';
    interpretacion = `Peso fetal estimado <p3 (${percentil.toFixed(1)}). Restricción severa del crecimiento intrauterino. Requiere evaluación urgente.`;
    recomendacion = 'Doppler de arterias umbilical, cerebral media y ductus venoso. Evaluación del líquido amniótico. Considerar monitoreo fetal intensivo y posible interrupción según edad gestacional y hallazgos Doppler.';
  } else if (percentil < 10) {
    clasificacion = '🟠 PEG (Pequeño para Edad Gestacional)';
    color = '#fa8c16';
    categoria = 'PEG';
    interpretacion = `Peso fetal estimado entre p3-p10 (${percentil.toFixed(1)}). Pequeño para edad gestacional. Riesgo intermedio.`;
    recomendacion = 'Doppler umbilical y seguimiento semanal. Evaluar diferencial entre constitucional y patológico mediante Doppler y líquido amniótico. Controles cada 7-14 días.';
  } else if (percentil >= 10 && percentil <= 90) {
    clasificacion = '🟢 NORMAL';
    color = '#52c41a';
    categoria = 'NORMAL';
    interpretacion = `Peso fetal estimado dentro de rango normal (p${percentil.toFixed(1)}). Crecimiento adecuado para edad gestacional.`;
    recomendacion = 'Continuar con seguimiento prenatal habitual. Próxima ecografía según protocolo estándar.';
  } else if (percentil > 90 && percentil < 97) {
    clasificacion = '🟡 GEG (Grande para Edad Gestacional)';
    color = '#faad14';
    categoria = 'GEG';
    interpretacion = `Peso fetal estimado entre p90-p97 (${percentil.toFixed(1)}). Grande para edad gestacional.`;
    recomendacion = 'Descartar diabetes gestacional (curva de glucosa si no se ha realizado). Seguimiento ecográfico cada 3-4 semanas. Evaluar vía de parto según evolución y estimación de peso al término.';
  } else {
    clasificacion = '🔴 MACROSOMÍA';
    color = '#f5222d';
    categoria = 'MACROSOMIA';
    interpretacion = `Peso fetal estimado >p97 (${percentil.toFixed(1)}). Macrosomía fetal. Riesgo de complicaciones al parto.`;
    recomendacion = 'Optimizar control glucémico si diabetes gestacional. Seguimiento ecográfico cada 2-3 semanas. Discutir vía de parto (cesárea electiva si EFW >4500g o >4000g con diabetes). Prevenir distocia de hombros.';
  }

  return {
    efw,
    percentil,
    clasificacion,
    color,
    interpretacion,
    recomendacion,
    zscore,
    desviacion_estandar: sd,
    bpd_percentil,
    hc_percentil,
    ac_percentil,
    fl_percentil,
    categoria
  };
};

// ==========================================================================
// CHART DATA BUILDERS
// ==========================================================================
export const getDataBiometria = (datosBiometria: DatosBiometria | null, resultado: ResultadoCrecimiento | null) => {
  if (!datosBiometria) return [];
  return [
    { parametro: 'BPD', valor: datosBiometria.bpd, unidad: 'mm', percentil: resultado?.bpd_percentil || 0 },
    { parametro: 'HC', valor: datosBiometria.hc, unidad: 'mm', percentil: resultado?.hc_percentil || 0 },
    { parametro: 'AC', valor: datosBiometria.ac, unidad: 'mm', percentil: resultado?.ac_percentil || 0 },
    { parametro: 'FL', valor: datosBiometria.fl, unidad: 'mm', percentil: resultado?.fl_percentil || 0 }
  ];
};

export const getDataCurvasCrecimiento = (datosBiometria: DatosBiometria | null, resultado: ResultadoCrecimiento | null) => {
  if (!datosBiometria) return [];
  const semanaInicio = Math.max(20, datosBiometria.semanas - 5);
  const semanaFin = Math.min(42, datosBiometria.semanas + 5);
  const curva = [];

  for (let s = semanaInicio; s <= semanaFin; s += 1) {
    const mediana = getMedianaEFW(s);
    const sd = getSDEFW(s);

    curva.push({
      semana: s,
      p3: mediana - 1.88 * sd,
      p10: mediana - 1.28 * sd,
      p50: mediana,
      p90: mediana + 1.28 * sd,
      p97: mediana + 1.88 * sd,
      actual: s === Math.round(datosBiometria.semanas) ? resultado?.efw : null
    });
  }

  return curva;
};

export const getDataDistribucionPercentiles = (resultado: ResultadoCrecimiento | null) => {
  if (!resultado) return [];

  const percentiles = [
    { name: 'BPD', value: resultado.bpd_percentil },
    { name: 'HC', value: resultado.hc_percentil },
    { name: 'AC', value: resultado.ac_percentil },
    { name: 'FL', value: resultado.fl_percentil }
  ];

  return percentiles;
};

export const getDataProporcionesFetales = (datosBiometria: DatosBiometria | null) => {
  if (!datosBiometria) return [];

  // Ratios útiles clínicamente
  const hc_ac = datosBiometria.hc / datosBiometria.ac;
  const fl_ac = datosBiometria.fl / datosBiometria.ac;
  const fl_hc = datosBiometria.fl / datosBiometria.hc;

  return [
    { ratio: 'HC/AC', valor: hc_ac, normal_min: 0.95, normal_max: 1.15, color: hc_ac >= 0.95 && hc_ac <= 1.15 ? '#52c41a' : '#faad14' },
    { ratio: 'FL/AC', valor: fl_ac, normal_min: 0.20, normal_max: 0.24, color: fl_ac >= 0.20 && fl_ac <= 0.24 ? '#52c41a' : '#faad14' },
    { ratio: 'FL/HC', valor: fl_hc, normal_min: 0.18, normal_max: 0.22, color: fl_hc >= 0.18 && fl_hc <= 0.22 ? '#52c41a' : '#faad14' }
  ];
};

export const getDataEvolucion = (historial: RegistroCrecimiento[]) => {
  return historial.slice().reverse().map((item, index) => ({
    evaluacion: `${item.semanas.toFixed(1)}s`,
    efw: item.efw,
    percentil: item.percentil,
    p50: getMedianaEFW(item.semanas)
  }));
};
