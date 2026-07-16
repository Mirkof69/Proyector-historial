// ==========================================================================
// TIPOS
// ==========================================================================
export interface DatosScreening {
  edad: number;
  semanas: number;
  nt: number;
  pappa: number;
  bhcg_libre: number;
  historia_t21: boolean;
  hallazgos_eco: boolean;
}

export interface ResultadoRiesgo {
  riesgo_t21: number;
  riesgo_t18: number;
  riesgo_t13: number;
  nt_mom: number;
  pappa_mom: number;
  bhcg_mom: number;
  riesgo_edad_t21: number;
  lr_t21: number;
  lr_t18: number;
  lr_t13: number;
  clasificacion_t21: string;
  clasificacion_t18: string;
  clasificacion_t13: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  screening_positivo: boolean;
}

export interface RegistroScreening extends ResultadoRiesgo {
  fecha: string;
  edad: number;
  semanas: number;
}

// ==========================================================================
// REDUCER FOR SCREENING STATE (replaces cascading setState)
// ==========================================================================
export interface ScreeningState {
  resultado: ResultadoRiesgo | null;
  historial: RegistroScreening[];
  usandoDatosEjemplo: boolean;
}

export type ScreeningAction =
  | { type: 'CALCULATE'; payload: { resultado: ResultadoRiesgo; registro: RegistroScreening } };

export function screeningReducer(state: ScreeningState, action: ScreeningAction): ScreeningState {
  switch (action.type) {
    case 'CALCULATE':
      return {
        resultado: action.payload.resultado,
        historial: [action.payload.registro, ...state.historial],
        usandoDatosEjemplo: false,
      };
    default:
      return state;
  }
}

export const initialScreeningState: ScreeningState = {
  resultado: null,
  historial: [],
  usandoDatosEjemplo: false,
};

export const formatMoMTooltip = (value: any) => value ? Number(value).toFixed(2) : '0';
export const renderRiesgoLabel = (props: any) => {
  const { name, riesgoStr } = props;
  return riesgoStr ? `${name}: ${riesgoStr}` : name;
};
export const formatRiesgoTooltip = (value: any) => value ? `${Number(value).toFixed(4)}%` : '0%';
export const formatLRTooltip = (value: any) => value ? `LR: ${Number(value).toFixed(2)}` : '';

// Riesgo basal por edad materna (T21)
export const getRiesgoEdad = (edad: number): number => {
  const riesgos: { [key: number]: number } = {
    20: 1 / 1500, 21: 1 / 1450, 22: 1 / 1400, 23: 1 / 1350, 24: 1 / 1300,
    25: 1 / 1250, 26: 1 / 1200, 27: 1 / 1150, 28: 1 / 1100, 29: 1 / 1050,
    30: 1 / 900, 31: 1 / 800, 32: 1 / 720, 33: 1 / 600, 34: 1 / 450,
    35: 1 / 350, 36: 1 / 280, 37: 1 / 210, 38: 1 / 170, 39: 1 / 130,
    40: 1 / 100, 41: 1 / 80, 42: 1 / 60, 43: 1 / 50, 44: 1 / 40, 45: 1 / 30
  };
  return riesgos[Math.round(edad)] || (edad < 25 ? 1 / 1500 : 1 / 30);
};

// Medianas de NT según semanas (FMF)
export const getMedianaNT = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    11.0: 1.6, 11.5: 1.7, 12.0: 1.8, 12.5: 1.9,
    13.0: 2.0, 13.5: 2.1, 14.0: 2.2
  };
  const sem = Math.round(semanas * 2) / 2; // Redondear a 0.5
  return medianas[sem] || 1.8;
};

// Medianas de PAPP-A según semanas
export const getMedianaPAPPA = (semanas: number): number => {
  if (semanas <= 10) return 0.8;
  if (semanas <= 11) return 1.0;
  if (semanas <= 12) return 1.3;
  if (semanas <= 13) return 1.7;
  return 2.0;
};

// Medianas de βhCG libre según semanas
export const getMedianaBHCG = (semanas: number): number => {
  if (semanas <= 10) return 50;
  if (semanas <= 11) return 45;
  if (semanas <= 12) return 40;
  if (semanas <= 13) return 35;
  return 30;
};

export const calcularMoM = (valor: number, mediana: number): number => {
  return valor / mediana;
};

export const formatRiesgo = (riesgo: number): string => {
  if (riesgo === 0) return '1:>100,000';
  const denominador = Math.round(1 / riesgo);
  return `1:${denominador.toLocaleString()}`;
};

export const calcularRiesgo = (valores: DatosScreening): ResultadoRiesgo => {
  // Calcular MoMs
  const nt_mom = calcularMoM(valores.nt, getMedianaNT(valores.semanas));
  const pappa_mom = calcularMoM(valores.pappa, getMedianaPAPPA(valores.semanas));
  const bhcg_mom = calcularMoM(valores.bhcg_libre, getMedianaBHCG(valores.semanas));

  // Riesgo basal por edad
  const riesgo_edad_t21 = getRiesgoEdad(valores.edad);

  // Likelihood Ratios (LR) basados en FMF para T21
  let lr_t21 = 1.0;

  // NT (factor más importante)
  if (nt_mom > 2.5) {
    lr_t21 *= 25.0;
  } else if (nt_mom > 2.0) {
    lr_t21 *= 10.0;
  } else if (nt_mom > 1.5) {
    lr_t21 *= 3.5;
  } else if (nt_mom > 1.2) {
    lr_t21 *= 1.5;
  } else if (nt_mom < 0.8) {
    lr_t21 *= 0.3;
  }

  // PAPP-A (bajo es factor de riesgo)
  if (pappa_mom < 0.25) {
    lr_t21 *= 5.0;
  } else if (pappa_mom < 0.5) {
    lr_t21 *= 2.5;
  } else if (pappa_mom < 0.75) {
    lr_t21 *= 1.5;
  } else if (pappa_mom > 1.5) {
    lr_t21 *= 0.6;
  }

  // βhCG libre (alto es factor de riesgo)
  if (bhcg_mom > 2.5) {
    lr_t21 *= 3.5;
  } else if (bhcg_mom > 2.0) {
    lr_t21 *= 2.0;
  } else if (bhcg_mom < 0.5) {
    lr_t21 *= 0.7;
  }

  // Historia previa de T21
  if (valores.historia_t21) {
    lr_t21 *= 3.0;
  }

  // Hallazgos ecográficos adicionales
  if (valores.hallazgos_eco) {
    lr_t21 *= 5.0;
  }

  // Calcular riesgo posterior para T21
  const odds_t21 = riesgo_edad_t21 / (1 - riesgo_edad_t21) * lr_t21;
  const riesgo_t21 = odds_t21 / (1 + odds_t21);

  // Likelihood Ratios para T18
  let lr_t18 = 1.0;

  if (nt_mom > 2.0) lr_t18 *= 15.0;
  else if (nt_mom > 1.5) lr_t18 *= 5.0;

  // En T18: PAPP-A y βhCG AMBOS bajos
  if (pappa_mom < 0.5 && bhcg_mom < 0.5) {
    lr_t18 *= 10.0;
  } else if (pappa_mom < 0.5) {
    lr_t18 *= 3.0;
  }
  if (bhcg_mom < 0.25) {
    lr_t18 *= 2.0;
  }

  if (valores.hallazgos_eco) lr_t18 *= 8.0;

  const riesgo_basal_t18 = 1 / 6000;
  const odds_t18 = riesgo_basal_t18 / (1 - riesgo_basal_t18) * lr_t18;
  const riesgo_t18 = odds_t18 / (1 + odds_t18);

  // Likelihood Ratios para T13
  let lr_t13 = 1.0;

  if (nt_mom > 2.0) lr_t13 *= 12.0;
  else if (nt_mom > 1.5) lr_t13 *= 4.0;

  if (pappa_mom < 0.5) lr_t13 *= 2.5;
  if (valores.hallazgos_eco) lr_t13 *= 10.0;

  const riesgo_basal_t13 = 1 / 10000;
  const odds_t13 = riesgo_basal_t13 / (1 - riesgo_basal_t13) * lr_t13;
  const riesgo_t13 = odds_t13 / (1 + odds_t13);

  // Clasificación de riesgo (punto de corte 1:250)
  const punto_corte = 1 / 250;

  let clasificacion_t21 = '';
  let clasificacion_t18 = '';
  let clasificacion_t13 = '';
  let color = '';
  let interpretacion = '';
  let recomendacion = '';
  let screening_positivo = false;

  // Clasificar T21
  if (riesgo_t21 >= punto_corte) {
    clasificacion_t21 = '🔴 ALTO RIESGO';
    color = '#f5222d';
    screening_positivo = true;
  } else if (riesgo_t21 >= 1 / 1000) {
    clasificacion_t21 = '🟡 RIESGO INTERMEDIO';
    color = '#fa8c16';
  } else {
    clasificacion_t21 = '🟢 BAJO RIESGO';
    color = '#52c41a';
  }

  // Clasificar T18
  if (riesgo_t18 >= 1 / 250) {
    clasificacion_t18 = '🔴 ALTO RIESGO';
    screening_positivo = true;
  } else if (riesgo_t18 >= 1 / 1000) {
    clasificacion_t18 = '🟡 RIESGO INTERMEDIO';
  } else {
    clasificacion_t18 = '🟢 BAJO RIESGO';
  }

  // Clasificar T13
  if (riesgo_t13 >= 1 / 250) {
    clasificacion_t13 = '🔴 ALTO RIESGO';
    screening_positivo = true;
  } else if (riesgo_t13 >= 1 / 1000) {
    clasificacion_t13 = '🟡 RIESGO INTERMEDIO';
  } else {
    clasificacion_t13 = '🟢 BAJO RIESGO';
  }

  // Interpretación global
  if (screening_positivo) {
    interpretacion = `Screening POSITIVO (riesgo ≥1:250). Riesgo elevado de aneuploidía. Se requiere consejo genético y oferta de prueba diagnóstica invasiva.`;
    recomendacion = 'Oferta de estudio genético invasivo (amniocentesis o biopsia corial). Consejo genético especializado. Alternativa: NIPT (Test Prenatal No Invasivo) como segundo screening. Evaluación ecográfica detallada del segundo trimestre.';
  } else if (riesgo_t21 >= 1 / 1000 || riesgo_t18 >= 1 / 1000 || riesgo_t13 >= 1 / 1000) {
    interpretacion = `Screening NEGATIVO pero con riesgo intermedio (1:250-1:1000). Considerar pruebas adicionales.`;
    recomendacion = 'Considerar NIPT (Test Prenatal No Invasivo) como seguimiento. Ecografía detallada a las 18-22 semanas. Seguimiento estrecho. Consejo genético si persisten dudas.';
  } else {
    interpretacion = `Screening NEGATIVO (riesgo <1:1000). Riesgo bajo de aneuploidías con el screening actual.`;
    recomendacion = 'Continuar con seguimiento prenatal habitual. Ecografía morfológica a las 18-22 semanas. Recordar que ningún screening es 100% sensible.';
  }

  return {
    riesgo_t21,
    riesgo_t18,
    riesgo_t13,
    nt_mom,
    pappa_mom,
    bhcg_mom,
    riesgo_edad_t21,
    lr_t21,
    lr_t18,
    lr_t13,
    clasificacion_t21,
    clasificacion_t18,
    clasificacion_t13,
    color,
    interpretacion,
    recomendacion,
    screening_positivo
  };
};

// ==========================================================================
// CHART DATA BUILDERS
// ==========================================================================
export const getDataEdadVsRiesgo = () => {
  const curva = [];
  for (let edad = 20; edad <= 45; edad += 1) {
    const riesgo = getRiesgoEdad(edad);
    curva.push({
      edad,
      riesgo_basal: riesgo * 100,
      punto_corte: (1 / 250) * 100,
    });
  }
  return curva;
};

export const getDataBiomarcadores = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  return [
    { name: 'NT', mom: resultado.nt_mom, referencia: 1.0, color: '#1890ff' },
    { name: 'PAPP-A', mom: resultado.pappa_mom, referencia: 1.0, color: '#52c41a' },
    { name: 'βhCG libre', mom: resultado.bhcg_mom, referencia: 1.0, color: '#fa8c16' }
  ];
};

export const getDataDistribucionRiesgo = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  return [
    { name: 'T21 (Down)', value: resultado.riesgo_t21 * 100, color: '#f5222d', riesgoStr: formatRiesgo(resultado.riesgo_t21) },
    { name: 'T18 (Edwards)', value: resultado.riesgo_t18 * 100, color: '#fa8c16', riesgoStr: formatRiesgo(resultado.riesgo_t18) },
    { name: 'T13 (Patau)', value: resultado.riesgo_t13 * 100, color: '#722ed1', riesgoStr: formatRiesgo(resultado.riesgo_t13) },
    { name: 'Normal', value: Math.max(0, 100 - (resultado.riesgo_t21 + resultado.riesgo_t18 + resultado.riesgo_t13) * 100), color: '#52c41a', riesgoStr: '' }
  ];
};

export const getDataLikelihoodRatios = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  return [
    { aneuplodia: 'T21', lr: resultado.lr_t21, color: '#1890ff' },
    { aneuplodia: 'T18', lr: resultado.lr_t18, color: '#fa8c16' },
    { aneuplodia: 'T13', lr: resultado.lr_t13, color: '#722ed1' }
  ];
};

export const getDataEvolucion = (historial: RegistroScreening[]) => {
  return historial.slice().reverse().map((item, index) => ({
    evaluacion: `${item.edad}a-${item.semanas.toFixed(1)}s`,
    riesgo_t21_pct: item.riesgo_t21 * 100,
    riesgo_t18_pct: item.riesgo_t18 * 100,
    riesgo_t13_pct: item.riesgo_t13 * 100
  }));
};
