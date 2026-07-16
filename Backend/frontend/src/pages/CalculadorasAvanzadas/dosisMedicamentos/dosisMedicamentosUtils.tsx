/**
 * Lógica pura de la calculadora de dosis obstétricas: cálculo de CLCr, cálculo
 * de dosis por medicamento, catálogo y datos de gráficas. Extraído de
 * DosisMedicamentos.
 *
 * SEGURIDAD CLÍNICA: solo 4 de los 16 medicamentos del catálogo tienen fórmula
 * implementada (oxitocina, misoprostol, metilergonovina, sulfato de magnesio).
 * Los 12 restantes se muestran como "Cálculo no disponible — consulte tablas
 * de referencia" y quedan deshabilitados en el selector hasta que un
 * sub-proyecto con validación médica real implemente sus fórmulas.
 */
export interface DatosPaciente {
  peso: number;
  edad: number;
  creatinina: number;
  semanas: number;
  es_embarazada: boolean;
  medicamento: string;
  via: string;
}

export interface ResultadoDosis {
  medicamento: string;
  dosis_calculada: number;
  unidad: string;
  frecuencia: string;
  via: string;
  dosis_min: number;
  dosis_max: number;
  clcr: number;
  ajuste_renal: string;
  contraindicaciones: string[];
  precauciones: string[];
  interacciones: string[];
  categoria_fda: string;
  interpretacion: string;
  color: string;
}

export interface RegistroDosis extends ResultadoDosis {
  fecha: string;
  peso: number;
}

export const renderAlertasLabel = (props: any) => {
  const { tipo, cantidad } = props;
  return `${tipo}: ${cantidad}`;
};

// Calcular Clearance de Creatinina (Cockcroft-Gault)
export const calcularCLCr = (peso: number, edad: number, creatinina: number, es_mujer: boolean = true): number => {
  const factor_mujer = es_mujer ? 0.85 : 1.0;
  return ((140 - edad) * peso * factor_mujer) / (72 * creatinina);
};

// Medicamentos obstétricos del catálogo.
// SEGURIDAD CLÍNICA: solo los marcados con `disponible: true` tienen fórmula
// de dosificación implementada y revisada. El resto se muestra en el selector
// como "Cálculo no disponible — consulte tablas de referencia" y NO puede
// seleccionarse: implementar sus fórmulas requiere validación médica real
// (sub-proyecto futuro), nunca fórmulas improvisadas.
export const medicamentos = [
  { value: 'oxitocina', label: 'Oxitocina (Inducción/Conducción)', disponible: true },
  { value: 'misoprostol', label: 'Misoprostol (Maduración cervical/HPP)', disponible: true },
  { value: 'metilergonovina', label: 'Metilergonovina (Atonía uterina)', disponible: true },
  { value: 'sulfato_mg', label: 'Sulfato de Magnesio (Eclampsia/Neuroprotección)', disponible: true },
  { value: 'nifedipino', label: 'Nifedipino (Tocolisis/HTA)', disponible: false },
  { value: 'labetalol', label: 'Labetalol (Crisis hipertensiva)', disponible: false },
  { value: 'hidralazina', label: 'Hidralazina (Crisis hipertensiva)', disponible: false },
  { value: 'betametasona', label: 'Betametasona (Maduración pulmonar)', disponible: false },
  { value: 'penicilina_g', label: 'Penicilina G (Profilaxis EGB)', disponible: false },
  { value: 'cefazolina', label: 'Cefazolina (Profilaxis quirúrgica)', disponible: false },
  { value: 'ampicilina', label: 'Ampicilina (Corioamnionitis)', disponible: false },
  { value: 'metronidazol', label: 'Metronidazol (Infección anaerobios)', disponible: false },
  { value: 'heparina', label: 'Heparina (Anticoagulación)', disponible: false },
  { value: 'enoxaparina', label: 'Enoxaparina (Tromboprofilaxis)', disponible: false },
  { value: 'insulina', label: 'Insulina regular (Diabetes gestacional)', disponible: false },
  { value: 'carboprost', label: 'Carboprost (HPP refractaria)', disponible: false }
];

/** true si el medicamento tiene fórmula de cálculo implementada y revisada. */
export const esCalculoDisponible = (value: string): boolean =>
  medicamentos.some((m) => m.value === value && m.disponible);

export const calcularDosis = (valores: DatosPaciente): ResultadoDosis => {
  const clcr = calcularCLCr(valores.peso, valores.edad, valores.creatinina, true);
  let dosis_calculada = 0;
  let unidad = '';
  let frecuencia = '';
  let via = valores.via;
  let dosis_min = 0;
  let dosis_max = 0;
  let ajuste_renal = '';
  let contraindicaciones: string[] = [];
  let precauciones: string[] = [];
  let interacciones: string[] = [];
  let categoria_fda = '';
  let interpretacion = '';
  let color = '#52c41a';

  switch (valores.medicamento) {
    case 'oxitocina':
      dosis_calculada = 10; // UI
      unidad = 'UI';
      if (via === 'IV') {
        frecuencia = 'Iniciar 1-2 mU/min, aumentar 1-2 mU/min cada 30 min. Máx 20-40 mU/min';
        dosis_min = 1;
        dosis_max = 40;
      } else if (via === 'IM') {
        frecuencia = '10 UI IM dosis única tras alumbramiento';
        dosis_calculada = 10;
      }
      categoria_fda = 'No clasificada';
      contraindicaciones = ['Desproporción cefalopélvica', 'Presentación anómala', 'Placenta previa', 'Vasa previa', 'Prolapso de cordón'];
      precauciones = ['Monitoreo continuo FCF', 'Control de contractilidad', 'Riesgo de taquisistolia', 'Hiponatremia por dilución'];
      interacciones = ['Misoprostol (aumenta riesgo rotura uterina)', 'Anestésicos volátiles (potencian efecto)'];
      interpretacion = 'Oxitocina: Uterotónico de elección. Vida media 3-10 min. Monitoreo estricto requerido.';
      break;

    case 'misoprostol':
      if (via === 'vaginal') {
        dosis_calculada = 25;
        unidad = 'mcg';
        frecuencia = '25 mcg vaginal cada 3-6 horas';
        dosis_min = 25;
        dosis_max = 50;
      } else if (via === 'sublingual') {
        dosis_calculada = 400;
        unidad = 'mcg';
        frecuencia = '400-600 mcg sublingual dosis única (HPP)';
        dosis_max = 600;
      } else {
        dosis_calculada = 400;
        unidad = 'mcg';
        frecuencia = '400 mcg rectal dosis única (HPP)';
      }
      categoria_fda = 'X (contraindicado en embarazo para otras indicaciones)';
      contraindicaciones = ['Cesárea previa', 'Cirugía uterina previa', 'Miomectomía transmural', 'Gran multiparidad'];
      precauciones = ['Riesgo rotura uterina', 'Taquisistolia', 'Sufrimiento fetal', 'Fiebre', 'Escalofríos'];
      interacciones = ['Oxitocina (NO usar simultáneamente)', 'NSAIDs (reducen efecto)'];
      interpretacion = 'Misoprostol: Prostaglandina E1. Efectivo para inducción y HPP. NUNCA con oxitocina simultánea.';
      color = '#fa8c16';
      break;

    case 'metilergonovina':
      dosis_calculada = 0.2;
      unidad = 'mg';
      if (via === 'IM') {
        frecuencia = '0.2 mg IM cada 2-4 horas (máx 5 dosis)';
        dosis_max = 1.0;
      } else {
        frecuencia = '0.2 mg VO cada 6-8 horas por 2-7 días';
      }
      categoria_fda = 'C';
      contraindicaciones = ['HIPERTENSIÓN (contraindicación absoluta)', 'Preeclampsia', 'Enfermedad cardiovascular', 'Enfermedad vascular periférica'];
      precauciones = ['Monitoreo PA', 'Riesgo crisis hipertensiva', 'Vasoespasmo coronario', 'Náuseas/vómitos'];
      interacciones = ['Inhibidores CYP3A4 (aumentan toxicidad)', 'Vasoconstrictores (potencian efecto)'];
      interpretacion = 'Metilergonovina: Ergotamina. CONTRAINDICADA EN HIPERTENSIÓN. Solo usar tras alumbramiento.';
      color = '#f5222d';
      break;

    case 'sulfato_mg':
      // Dosis de carga: 4-6 g IV en 15-20 min, luego 1-2 g/h
      dosis_calculada = 4;
      unidad = 'g';
      frecuencia = 'Carga: 4-6g IV en 15-20 min. Mantenimiento: 1-2 g/h';
      dosis_min = 4;
      dosis_max = 6;
      via = 'IV';
      categoria_fda = 'A (para eclampsia) / D (uso prolongado)';

      if (clcr < 20) {
        ajuste_renal = 'CONTRAINDICADO si CLCr <20 mL/min. Riesgo toxicidad severa.';
        color = '#f5222d';
      } else if (clcr < 50) {
        ajuste_renal = 'Reducir dosis 50%. Monitoreo estricto niveles séricos y reflejos.';
        color = '#fa8c16';
      } else {
        ajuste_renal = 'Sin ajuste necesario. Monitoreo de reflejos, FR, diuresis.';
      }

      contraindicaciones = ['Insuficiencia renal severa', 'Bloqueo cardíaco', 'Miastenia gravis'];
      precauciones = ['Monitoreo reflejos patelares', 'FR >12/min', 'Diuresis >25 mL/h', 'Tener gluconato de calcio disponible'];
      interacciones = ['Bloqueadores neuromusculares (potencian bloqueo)', 'Nifedipino (hipotensión severa)', 'Digoxina'];
      interpretacion = 'Sulfato de Magnesio: Anticonvulsivante de elección en eclampsia. Neuroprotector fetal <32sem. Monitoreo estricto.';
      break;

    default:
      // Medicamentos del catálogo SIN fórmula implementada/validada: mensaje
      // honesto en lugar de un cálculo inventado. (El selector ya los
      // deshabilita; esto es el blindaje de última línea.)
      interpretacion =
        'Cálculo no disponible para este medicamento — consulte tablas de '
        + 'referencia oficiales (protocolos MSP/OMS). La dosificación '
        + 'automática de este fármaco requiere validación médica pendiente.';
      color = '#999';
  }

  // Agregar alertas según CLCr
  if (clcr < 60 && !ajuste_renal) {
    ajuste_renal = 'Función renal limítrofe. Monitoreo recomendado.';
    precauciones.push('CLCr reducido - vigilar acumulación');
  }

  // Alerta embarazo
  if (valores.es_embarazada && categoria_fda === 'X') {
    color = '#f5222d';
    contraindicaciones.push('CONTRAINDICADO EN EMBARAZO (FDA X)');
  } else if (valores.es_embarazada && categoria_fda === 'D') {
    color = '#fa8c16';
    precauciones.push('Categoría FDA D - usar solo si beneficio supera riesgo');
  }

  return {
    medicamento: valores.medicamento,
    dosis_calculada,
    unidad,
    frecuencia,
    via,
    dosis_min,
    dosis_max,
    clcr,
    ajuste_renal: ajuste_renal || 'No requiere ajuste',
    contraindicaciones,
    precauciones,
    interacciones,
    categoria_fda,
    interpretacion,
    color
  };
};

export const getDataDosisRango = (resultado: ResultadoDosis | null) => {
  if (!resultado) return [];
  return [
    { categoria: 'Dosis Mínima', valor: resultado.dosis_min, color: '#52c41a' },
    { categoria: 'Dosis Calculada', valor: resultado.dosis_calculada, color: '#1890ff' },
    { categoria: 'Dosis Máxima', valor: resultado.dosis_max, color: '#f5222d' }
  ].filter(item => item.valor > 0);
};

export const getDataAlertas = (resultado: ResultadoDosis | null) => {
  if (!resultado) return [];
  return [
    { tipo: 'Contraindicaciones', cantidad: resultado.contraindicaciones.length, color: '#f5222d' },
    { tipo: 'Precauciones', cantidad: resultado.precauciones.length, color: '#fa8c16' },
    { tipo: 'Interacciones', cantidad: resultado.interacciones.length, color: '#faad14' }
  ];
};

export const getDataFuncionRenal = (resultado: ResultadoDosis | null) => {
  if (!resultado) return [];
  const clcr = resultado.clcr;
  return [
    { etapa: 'Normal', min: 90, max: 150, actual: clcr >= 90 ? clcr : null },
    { etapa: 'Leve', min: 60, max: 89, actual: clcr >= 60 && clcr < 90 ? clcr : null },
    { etapa: 'Moderada', min: 30, max: 59, actual: clcr >= 30 && clcr < 60 ? clcr : null },
    { etapa: 'Severa', min: 15, max: 29, actual: clcr >= 15 && clcr < 30 ? clcr : null },
    { etapa: 'Terminal', min: 0, max: 14, actual: clcr < 15 ? clcr : null }
  ];
};

export const getDataHistorico = (historial: RegistroDosis[]) =>
  historial.slice(0, 10).reverse().map((item, index) => ({
    numero: index + 1,
    medicamento: item.medicamento,
    dosis: item.dosis_calculada,
    clcr: item.clcr
  }));
