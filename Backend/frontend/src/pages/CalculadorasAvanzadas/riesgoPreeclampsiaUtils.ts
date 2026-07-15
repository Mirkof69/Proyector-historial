export interface DatosRiesgo {
  edad: number;
  peso: number;
  talla: number;
  semanas: number;
  plgf: number;
  sflt1: number;
  pappa: number;
  map: number;
  uta_pi: number;
  historia_previa: boolean;
  hipertension: boolean;
  diabetes: boolean;
  obesidad: boolean;
  gestacion_multiple: boolean;
  raza_afro: boolean;
}

export interface ResultadoRiesgo {
  riesgo_pe_precoz: number;
  riesgo_pe_tardia: number;
  plgf_mom: number;
  sflt1_mom: number;
  pappa_mom: number;
  map_mom: number;
  uta_pi_mom: number;
  ratio_sflt_plgf: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  aspirina_indicada: boolean;
  seguimiento: string;
}

export interface RegistroRiesgo extends ResultadoRiesgo {
  fecha: string;
  semanas: number;
}

// Medianas según semana gestacional (FMF references)
export const getMedianaPLGF = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    11: 32.5, 12: 39.8, 13: 48.5, 14: 59.0, 15: 71.5,
    16: 86.5, 17: 104.0, 18: 124.5, 19: 148.0, 20: 175.0,
    21: 205.5, 22: 240.0, 23: 278.5, 24: 321.0, 25: 368.0,
    26: 419.5, 27: 476.0, 28: 537.5, 29: 604.5, 30: 677.0,
    31: 755.0, 32: 839.0, 33: 929.0, 34: 1025.5, 35: 1129.0
  };
  return medianas[Math.round(semanas)] || 500;
};

export const getMedianaSflt1 = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    11: 1450, 12: 1520, 13: 1590, 14: 1665, 15: 1740,
    16: 1820, 17: 1900, 18: 1985, 19: 2070, 20: 2160,
    21: 2250, 22: 2345, 23: 2440, 24: 2540, 25: 2640,
    26: 2745, 27: 2850, 28: 2960, 29: 3070, 30: 3185,
    31: 3300, 32: 3420, 33: 3540, 34: 3665, 35: 3790
  };
  return medianas[Math.round(semanas)] || 2500;
};

export const getMedianaPAPPA = (semanas: number): number => {
  if (semanas <= 13) return 1.2 + (semanas - 11) * 0.3;
  return 2.0;
};

export const getMedianaMAP = (edad: number): number => {
  return 90 + (edad - 30) * 0.15;
};

export const getMedianaUtAPI = (semanas: number): number => {
  if (semanas <= 16) return 2.35 - (semanas - 11) * 0.12;
  if (semanas <= 23) return 1.75 - (semanas - 16) * 0.08;
  return 1.2 - (semanas - 23) * 0.02;
};

export const calcularRiesgo = (valores: DatosRiesgo): ResultadoRiesgo => {
    // Calcular MoMs
    const plgf_mom = valores.plgf / getMedianaPLGF(valores.semanas);
    const sflt1_mom = valores.sflt1 / getMedianaSflt1(valores.semanas);
    const pappa_mom = valores.pappa / getMedianaPAPPA(valores.semanas);
    const map_mom = valores.map / getMedianaMAP(valores.edad);
    const uta_pi_mom = valores.uta_pi / getMedianaUtAPI(valores.semanas);
    const ratio_sflt_plgf = valores.sflt1 / valores.plgf;

    // Modelo Bayesiano FMF - Likelihood Ratios
    let lr_precoz = 1.0;
    let lr_tardia = 1.0;

    // PlGF (factor protector más importante)
    if (plgf_mom < 0.4) {
      lr_precoz *= 15.0;
      lr_tardia *= 8.0;
    } else if (plgf_mom < 0.7) {
      lr_precoz *= 5.0;
      lr_tardia *= 3.0;
    } else if (plgf_mom > 1.5) {
      lr_precoz *= 0.3;
      lr_tardia *= 0.5;
    }

    // Ratio sFlt-1/PlGF (Verlohren rule)
    if (ratio_sflt_plgf > 85) {
      lr_precoz *= 12.0;
      lr_tardia *= 6.0;
    } else if (ratio_sflt_plgf > 38) {
      lr_precoz *= 4.0;
      lr_tardia *= 2.5;
    }

    // MAP
    if (map_mom > 1.15) {
      lr_precoz *= 3.5;
      lr_tardia *= 2.0;
    } else if (map_mom > 1.08) {
      lr_precoz *= 1.8;
      lr_tardia *= 1.3;
    }

    // UtA-PI
    if (uta_pi_mom > 1.5) {
      lr_precoz *= 4.0;
      lr_tardia *= 2.2;
    } else if (uta_pi_mom > 1.2) {
      lr_precoz *= 2.0;
      lr_tardia *= 1.5;
    }

    // PAPP-A (solo para precoz)
    if (pappa_mom < 0.4) {
      lr_precoz *= 2.5;
    } else if (pappa_mom < 0.6) {
      lr_precoz *= 1.5;
    }

    // Factores de riesgo maternos
    if (valores.historia_previa) {
      lr_precoz *= 8.0;
      lr_tardia *= 4.0;
    }
    if (valores.hipertension) {
      lr_precoz *= 3.5;
      lr_tardia *= 2.5;
    }
    if (valores.diabetes) {
      lr_precoz *= 2.0;
      lr_tardia *= 1.8;
    }
    if (valores.obesidad) {
      lr_precoz *= 2.2;
      lr_tardia *= 1.6;
    }
    if (valores.gestacion_multiple) {
      lr_precoz *= 3.0;
      lr_tardia *= 2.0;
    }
    if (valores.raza_afro) {
      lr_precoz *= 1.8;
      lr_tardia *= 1.4;
    }
    if (valores.edad >= 40) {
      lr_precoz *= 1.7;
      lr_tardia *= 1.5;
    } else if (valores.edad >= 35) {
      lr_precoz *= 1.3;
      lr_tardia *= 1.2;
    }

    // Riesgo basal según edad y paridad
    const riesgo_basal_precoz = 0.005; // 0.5%
    const riesgo_basal_tardia = 0.025; // 2.5%

    // Calcular riesgo posterior
    const odds_precoz = (riesgo_basal_precoz / (1 - riesgo_basal_precoz)) * lr_precoz;
    const riesgo_pe_precoz = (odds_precoz / (1 + odds_precoz)) * 100;

    const odds_tardia = (riesgo_basal_tardia / (1 - riesgo_basal_tardia)) * lr_tardia;
    const riesgo_pe_tardia = (odds_tardia / (1 + odds_tardia)) * 100;

    // Clasificación de riesgo (según FMF)
    let clasificacion = '';
    let color = '';
    let interpretacion = '';
    let recomendacion = '';
    let aspirina_indicada = false;
    let seguimiento = '';

    if (riesgo_pe_precoz >= 10) {
      clasificacion = '🔴 ALTO RIESGO';
      color = '#f5222d';
      interpretacion = 'Riesgo elevado de preeclampsia precoz (<34 semanas). Requiere monitoreo intensivo y profilaxis farmacológica.';
      recomendacion = 'Aspirina 150mg/día desde las 12 semanas hasta las 36 semanas. Vigilancia estrecha cada 2-3 semanas con biomarcadores y Doppler.';
      aspirina_indicada = true;
      seguimiento = 'Control cada 2-3 semanas con PlGF, sFlt-1, MAP, UtA-PI y biometría fetal.';
    } else if (riesgo_pe_precoz >= 5 || riesgo_pe_tardia >= 15) {
      clasificacion = '🟡 RIESGO INTERMEDIO';
      color = '#fa8c16';
      interpretacion = 'Riesgo moderado de preeclampsia. Se recomienda profilaxis y seguimiento cercano.';
      recomendacion = 'Aspirina 150mg/día desde las 12 semanas. Considerar suplementación con calcio 1.5g/día si ingesta dietética baja.';
      aspirina_indicada = true;
      seguimiento = 'Control cada 3-4 semanas con biomarcadores y evaluación clínica.';
    } else if (riesgo_pe_precoz >= 1 || riesgo_pe_tardia >= 5) {
      clasificacion = '🟢 BAJO RIESGO';
      color = '#52c41a';
      interpretacion = 'Riesgo bajo de preeclampsia. Continuar con seguimiento prenatal habitual.';
      recomendacion = 'Seguimiento prenatal estándar. Educación sobre signos de alarma. Dieta saludable y actividad física regular.';
      aspirina_indicada = false;
      seguimiento = 'Control prenatal estándar según protocolo. Vigilancia de signos de alarma.';
    } else {
      clasificacion = '🟢 RIESGO MUY BAJO';
      color = '#389e0d';
      interpretacion = 'Riesgo muy bajo de preeclampsia. Biomarcadores protectores.';
      recomendacion = 'Continuar con controles prenatales de rutina. Mantener estilo de vida saludable.';
      aspirina_indicada = false;
      seguimiento = 'Control prenatal estándar.';
    }

    return {
      riesgo_pe_precoz,
      riesgo_pe_tardia,
      plgf_mom,
      sflt1_mom,
      pappa_mom,
      map_mom,
      uta_pi_mom,
      ratio_sflt_plgf,
      clasificacion,
      color,
      interpretacion,
      recomendacion,
      aspirina_indicada,
      seguimiento
    };
};

export const formatMoMTooltip = (value: any) => value ? Number(value).toFixed(2) : '0';
export const renderRiesgoLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(1)}%`;
export const formatRiesgoTooltip = (value: any) => value ? `${Number(value).toFixed(2)}%` : '0%';
export const formatRatioTooltip = (value: any) => value ? Number(value).toFixed(1) : '0';

export const getDataBiomarcadores = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  return [
    { name: 'PlGF', mom: resultado.plgf_mom, referencia: 1.0, color: '#1890ff' },
    { name: 'sFlt-1', mom: resultado.sflt1_mom, referencia: 1.0, color: '#f5222d' },
    { name: 'PAPP-A', mom: resultado.pappa_mom, referencia: 1.0, color: '#52c41a' },
    { name: 'MAP', mom: resultado.map_mom, referencia: 1.0, color: '#fa8c16' },
    { name: 'UtA-PI', mom: resultado.uta_pi_mom, referencia: 1.0, color: '#722ed1' }
  ];
};

export const getDataDistribucionRiesgo = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  return [
    { name: 'PE Precoz', value: resultado.riesgo_pe_precoz, color: '#f5222d' },
    { name: 'PE Tardía', value: resultado.riesgo_pe_tardia, color: '#fa8c16' },
    { name: 'Sin PE', value: Math.max(0, 100 - resultado.riesgo_pe_precoz - resultado.riesgo_pe_tardia), color: '#52c41a' }
  ];
};

export const getDataEvolucionTemporal = (historial: RegistroRiesgo[]) => {
  return historial.slice().reverse().map((item, index) => ({
    evaluacion: `Ev ${index + 1}`,
    semanas: item.semanas,
    riesgo_precoz: item.riesgo_pe_precoz,
    riesgo_tardia: item.riesgo_pe_tardia,
    plgf_mom: item.plgf_mom
  }));
};

export const getDataRatioSfltPlgf = (resultado: ResultadoRiesgo | null) => {
  if (!resultado) return [];
  const ratioActual = resultado.ratio_sflt_plgf;
  return [
    { semana: '12-16', ratio: ratioActual * 0.6, limite_normal: 38, limite_pe: 85 },
    { semana: '17-20', ratio: ratioActual * 0.75, limite_normal: 38, limite_pe: 85 },
    { semana: '21-24', ratio: ratioActual * 0.85, limite_normal: 38, limite_pe: 85 },
    { semana: '25-28', ratio: ratioActual * 0.95, limite_normal: 38, limite_pe: 85 },
    { semana: '29-32', ratio: ratioActual, limite_normal: 38, limite_pe: 85 },
    { semana: '33-36', ratio: ratioActual * 1.1, limite_normal: 38, limite_pe: 85 }
  ];
};
