// ============================================
// INTERFACES Y TIPOS
// ============================================

export interface DatosHemorragia {
  // Signos vitales
  frecuencia_cardiaca: number;
  presion_sistolica: number;
  presion_diastolica: number;
  frecuencia_respiratoria: number;
  temperatura: number;
  saturacion_o2: number;

  // Pérdida sanguínea
  perdida_estimada_ml: number;
  tiempo_minutos: number;

  // Causa (4 T's)
  causa_principal: 'tono' | 'trauma' | 'tejido' | 'trombina';

  // Evaluación obstétrica
  tono_uterino: 'firme' | 'blando' | 'muy_blando';
  placenta_completa: boolean;
  laceraciones: boolean;
  coagulopatia: boolean;

  // Laboratorio
  hemoglobina_inicial: number;
  hemoglobina_actual: number;
  plaquetas: number;
  fibrinogeno: number;
}

export interface ResultadoHemorragia {
  shock_index: number;
  clasificacion_shock: string;
  color_shock: string;
  gravedad: string;
  color_gravedad: string;
  porcentaje_perdida: number;
  volumen_compensar: number;

  // Estados clínicos
  estado_hemodinamico: string;
  riesgo_shock: string;
  requiere_ptm: boolean;

  // Recomendaciones
  medidas_inmediatas: string[];
  protocolo_ptm: {
    globulos_rojos: number;
    plasma: number;
    plaquetas: number;
    crioprecipitado: number;
  };
  intervenciones_sugeridas: string[];

  interpretacion: string;
}

export interface RegistroHemorragia {
  fecha: string;
  shock_index: number;
  perdida_ml: number;
  gravedad: string;
  causa: string;
}

// ============================================
// FUNCIONES DE CÁLCULO
// ============================================

export const calcularShockIndex = (fc: number, pas: number): number => {
  if (pas === 0) return 0;
  return fc / pas;
};

export const clasificarShock = (si: number): { clase: string; color: string } => {
  if (si < 0.7) {
    return { clase: '✅ Normal', color: '#52c41a' };
  } else if (si < 0.9) {
    return { clase: '⚠️ Vigilancia', color: '#faad14' };
  } else if (si < 1.2) {
    return { clase: '🟠 Compensado', color: '#fa8c16' };
  } else if (si < 1.5) {
    return { clase: '🔴 Descompensado', color: '#ff4d4f' };
  } else {
    return { clase: '🚨 CRÍTICO', color: '#a8071a' };
  }
};

export const clasificarGravedad = (perdida_ml: number): { gravedad: string; color: string } => {
  if (perdida_ml < 500) {
    return { gravedad: 'Leve', color: '#52c41a' };
  } else if (perdida_ml < 1000) {
    return { gravedad: 'Moderada', color: '#faad14' };
  } else if (perdida_ml < 1500) {
    return { gravedad: 'Severa', color: '#ff4d4f' };
  } else {
    return { gravedad: 'Masiva', color: '#a8071a' };
  }
};

export const getCausaTexto = (causa: string): string => {
  const causas: { [key: string]: string } = {
    'tono': 'TONO - Atonía uterina (70% de HPP)',
    'trauma': 'TRAUMA - Laceraciones/Desgarros',
    'tejido': 'TEJIDO - Retención placentaria',
    'trombina': 'TROMBINA - Coagulopatía'
  };
  return causas[causa] || causa;
};

export const calcularHemorragia = (valores: DatosHemorragia): ResultadoHemorragia => {
  // Calcular Shock Index
  const shock_index = calcularShockIndex(valores.frecuencia_cardiaca, valores.presion_sistolica);
  const { clase: clasificacion_shock, color: color_shock } = clasificarShock(shock_index);

  // Clasificar gravedad por volumen
  const { gravedad, color: color_gravedad } = clasificarGravedad(valores.perdida_estimada_ml);

  // Estimar volemia total (aproximadamente 70 ml/kg en mujeres, asumiendo 60 kg promedio)
  const volemia_total = 4200; // ml
  const porcentaje_perdida = (valores.perdida_estimada_ml / volemia_total) * 100;

  // Volumen a compensar (1.5-3x la pérdida dependiendo severidad)
  let factor_reemplazo = 1.5;
  if (valores.perdida_estimada_ml > 1500) factor_reemplazo = 3.0;
  else if (valores.perdida_estimada_ml > 1000) factor_reemplazo = 2.5;
  else if (valores.perdida_estimada_ml > 500) factor_reemplazo = 2.0;

  const volumen_compensar = valores.perdida_estimada_ml * factor_reemplazo;

  // Evaluar estado hemodinámico
  let estado_hemodinamico = 'Estable';
  if (shock_index > 1.2 || valores.presion_sistolica < 90) {
    estado_hemodinamico = 'Inestable - CRÍTICO';
  } else if (shock_index > 0.9 || valores.presion_sistolica < 100) {
    estado_hemodinamico = 'Compensado';
  }

  // Evaluar riesgo de shock
  let riesgo_shock = 'Bajo';
  if (shock_index > 1.5 || porcentaje_perdida > 40) {
    riesgo_shock = 'Shock Hemorrágico ESTABLECIDO';
  } else if (shock_index > 1.2 || porcentaje_perdida > 30) {
    riesgo_shock = 'Alto - Inminente';
  } else if (shock_index > 0.9 || porcentaje_perdida > 20) {
    riesgo_shock = 'Moderado';
  }

  // Determinar si requiere Protocolo de Transfusión Masiva (PTM)
  const requiere_ptm = valores.perdida_estimada_ml > 1500 ||
                       shock_index > 1.5 ||
                       porcentaje_perdida > 30 ||
                       (valores.coagulopatia && valores.perdida_estimada_ml > 1000);

  // Protocolo PTM - Ratio 1:1:1 (GR:PFC:Plaq)
  let protocolo_ptm = {
    globulos_rojos: 0,
    plasma: 0,
    plaquetas: 0,
    crioprecipitado: 0
  };

  if (requiere_ptm) {
    // Unidades estimadas basadas en pérdida
    const unidades_base = Math.ceil(valores.perdida_estimada_ml / 500);
    protocolo_ptm = {
      globulos_rojos: unidades_base * 2, // Concentrados eritrocitarios
      plasma: unidades_base * 2, // Plasma fresco congelado
      plaquetas: unidades_base, // Unidades de plaquetas
      crioprecipitado: valores.fibrinogeno < 150 ? 10 : 0 // Si fibrinógeno bajo
    };
  }

  // Medidas inmediatas según 4 T's
  const medidas_inmediatas: string[] = [];

  // Medidas generales
  medidas_inmediatas.push('🔴 ACTIVAR CÓDIGO ROJO - Equipo multidisciplinario');
  medidas_inmediatas.push('💉 Dos accesos IV calibre 14-16G');
  medidas_inmediatas.push('📊 Laboratorios STAT: BHC, TP/TPT, Fibrinógeno, Gasometría');

  // Específicas por causa (4 T's)
  switch (valores.causa_principal) {
    case 'tono':
      medidas_inmediatas.push('🤲 TONO: Masaje uterino bimanual vigoroso');
      medidas_inmediatas.push('💊 Oxitocina 20-40 UI en 1000ml SSN a goteo rápido');
      if (valores.tono_uterino === 'muy_blando') {
        medidas_inmediatas.push('💉 Metilergonovina 0.2mg IM (si no HTA)');
        medidas_inmediatas.push('🧪 Misoprostol 800-1000 mcg rectal');
        medidas_inmediatas.push('⚠️ Considerar: Carboprost 250mcg IM c/15min (máx 8 dosis)');
      }
      break;

    case 'trauma':
      medidas_inmediatas.push('🔍 TRAUMA: Inspección cervical/vaginal/perineal minuciosa');
      medidas_inmediatas.push('🪡 Sutura inmediata de laceraciones identificadas');
      if (valores.laceraciones) {
        medidas_inmediatas.push('⚠️ Evaluar lesiones de tracto genital alto');
        medidas_inmediatas.push('🏥 Considerar revisión quirúrgica si sangrado persiste');
      }
      break;

    case 'tejido':
      medidas_inmediatas.push('🧪 TEJIDO: Revisión de cavidad uterina');
      if (!valores.placenta_completa) {
        medidas_inmediatas.push('🤚 Extracción manual de restos placentarios');
        medidas_inmediatas.push('💊 Antibióticos profilácticos');
        medidas_inmediatas.push('📋 Enviar placenta a patología si anormal');
      }
      medidas_inmediatas.push('🔍 Descartar acretismo placentario');
      break;

    case 'trombina':
      medidas_inmediatas.push('🩸 TROMBINA: Manejo de coagulopatía');
      if (valores.coagulopatia) {
        medidas_inmediatas.push('💉 Ácido tranexámico 1g IV en 10 min, luego 1g en 8h');
        medidas_inmediatas.push('🧊 Crioprecipitado 10 U si fibrinógeno <150 mg/dL');
        medidas_inmediatas.push('🩸 PFC 4 unidades si TP/TPT >1.5x normal');
      }
      medidas_inmediatas.push('🔬 Laboratorios cada 30-60 min');
      break;
  }

  // Medidas según gravedad
  if (valores.perdida_estimada_ml > 1000) {
    medidas_inmediatas.push('🩸 Transfusión: Iniciar GR O negativo si no tipificada');
  }

  if (requiere_ptm) {
    medidas_inmediatas.push('🚨 ACTIVAR PROTOCOLO DE TRANSFUSIÓN MASIVA');
    medidas_inmediatas.push('🏥 Avisar a Banco de Sangre - Transfusión continua');
  }

  // Intervenciones sugeridas (escalonadas)
  const intervenciones_sugeridas: string[] = [];

  if (valores.perdida_estimada_ml < 1000) {
    intervenciones_sugeridas.push('1️⃣ Medidas médicas (uterotónicos, ácido tranexámico)');
    intervenciones_sugeridas.push('2️⃣ Reposición con cristaloides');
  } else if (valores.perdida_estimada_ml < 1500) {
    intervenciones_sugeridas.push('1️⃣ Uterotónicos en dosis máximas');
    intervenciones_sugeridas.push('2️⃣ Taponamiento con balón intrauterino (Bakri)');
    intervenciones_sugeridas.push('3️⃣ Considerar suturas hemostáticas (B-Lynch, Cho)');
    intervenciones_sugeridas.push('4️⃣ Transfusión según protocolo');
  } else {
    intervenciones_sugeridas.push('1️⃣ MÁXIMAS medidas médicas');
    intervenciones_sugeridas.push('2️⃣ Taponamiento Bakri + Suturas compresivas');
    intervenciones_sugeridas.push('3️⃣ Embolización arterial selectiva si disponible');
    intervenciones_sugeridas.push('4️⃣ Ligadura arterias uterinas/hipogástricas');
    intervenciones_sugeridas.push('5️⃣ Histerectomía obstétrica si falla lo anterior');
    intervenciones_sugeridas.push('⚠️ LLAMAR A CIRUGÍA GENERAL Y RADIOLOGÍA INTERVENCIONISTA');
  }

  // Interpretación
  let interpretacion = `Hemorragia obstétrica ${gravedad.toUpperCase()} con pérdida estimada de ${valores.perdida_estimada_ml} ml `;
  interpretacion += `(${porcentaje_perdida.toFixed(1)}% de volemia). `;
  interpretacion += `Shock Index: ${shock_index.toFixed(2)} (${clasificacion_shock}). `;
  interpretacion += `Estado hemodinámico: ${estado_hemodinamico}. `;

  if (requiere_ptm) {
    interpretacion += `\n\n🚨 CUMPLE CRITERIOS PARA PROTOCOLO DE TRANSFUSIÓN MASIVA. `;
    interpretacion += `Se requiere transfusión agresiva con ratio 1:1:1 y manejo multidisciplinario urgente.`;
  }

  interpretacion += `\n\nCausa principal identificada: ${getCausaTexto(valores.causa_principal)}. `;
  interpretacion += `Se recomienda manejo escalonado según respuesta clínica.`;

  if (shock_index > 1.5) {
    interpretacion += `\n\n⚠️ PACIENTE EN ESTADO CRÍTICO - Shock hemorrágico establecido. Requiere reanimación agresiva inmediata.`;
  }

  return {
    shock_index,
    clasificacion_shock,
    color_shock,
    gravedad,
    color_gravedad,
    porcentaje_perdida,
    volumen_compensar,
    estado_hemodinamico,
    riesgo_shock,
    requiere_ptm,
    medidas_inmediatas,
    protocolo_ptm,
    intervenciones_sugeridas,
    interpretacion
  };
};

export const renderVolemiaLabel = (props: any) => {
  const { name, value } = props;
  return `${name}: ${value.toFixed(1)}%`;
};
export const HISTORIAL_TICK = { fontSize: 12 };
export const SHOCK_INDEX_LABEL = { value: 'Shock Index', angle: -90, position: 'insideLeft' };
export const PERDIDA_LABEL = { value: 'Pérdida (ml)', angle: 90, position: 'insideRight' };

export const getDataCausas4T = () => [
  { causa: 'TONO\nAtonía', porcentaje: 70, color: '#ff4d4f' },
  { causa: 'TRAUMA\nLaceraciones', porcentaje: 20, color: '#fa8c16' },
  { causa: 'TEJIDO\nRetención', porcentaje: 8, color: '#faad14' },
  { causa: 'TROMBINA\nCoagulopatía', porcentaje: 2, color: '#722ed1' },
];

export const getDataDistribucion = (resultado: ResultadoHemorragia | null) => {
  if (!resultado) return [];

  return [
    { name: 'Pérdida Actual', value: resultado.porcentaje_perdida, color: resultado.color_gravedad },
    { name: 'Volemia Restante', value: 100 - resultado.porcentaje_perdida, color: '#95de64' }
  ];
};

export const getDataSignosVitales = (valores: any) => {
  return [
    {
      parametro: 'FC',
      valor: valores.frecuencia_cardiaca || 0,
      normal_min: 60,
      normal_max: 100,
      referencia: 80
    },
    {
      parametro: 'PAS',
      valor: valores.presion_sistolica || 0,
      normal_min: 90,
      normal_max: 140,
      referencia: 120
    },
    {
      parametro: 'PAD',
      valor: valores.presion_diastolica || 0,
      normal_min: 60,
      normal_max: 90,
      referencia: 80
    },
    {
      parametro: 'FR',
      valor: valores.frecuencia_respiratoria || 0,
      normal_min: 12,
      normal_max: 20,
      referencia: 16
    }
  ];
};

export const getDataPTM = (resultado: ResultadoHemorragia | null) => {
  if (!resultado || !resultado.requiere_ptm) return [];

  return [
    { componente: 'GR', unidades: resultado.protocolo_ptm.globulos_rojos, color: '#ff4d4f' },
    { componente: 'PFC', unidades: resultado.protocolo_ptm.plasma, color: '#faad14' },
    { componente: 'Plaq', unidades: resultado.protocolo_ptm.plaquetas, color: '#1890ff' },
    { componente: 'Crio', unidades: resultado.protocolo_ptm.crioprecipitado, color: '#722ed1' }
  ];
};
