import dayjs from 'dayjs';
import { 
  ProtocoloObstetrico, 
  AlertaClinica 
} from './types';

export const RIESGO_COLORS = { 'BAJO': '#52c41a', 'ALTO': '#fa8c16', 'MUY_ALTO': '#f5222d' };
export const ESTADO_CIVIL_OPTS = ['Soltera', 'Casada', 'Unión Libre', 'Divorciada', 'Viuda'];

export const PROTOCOLOS_EMBARAZO: ProtocoloObstetrico[] = [
  {
    id: 1,
    nombre: 'Primer Control Prenatal',
    semanas_inicio: 0,
    semanas_fin: 12,
    descripcion: 'Evaluación inicial, historia clínica completa, laboratorios de rutina',
    examenes_requeridos: ['Hemograma', 'Grupo Sanguíneo', 'VIH', 'VDRL', 'Toxoplasma IgG/IgM', 'EMO', 'Ecografía Temprana'],
    cumplido: false
  },
  {
    id: 2,
    nombre: 'Ecografía Genética (NT)',
    semanas_inicio: 11,
    semanas_fin: 14,
    descripcion: 'Tamizaje de cromosomopatías - Medición de translucencia nucal',
    examenes_requeridos: ['Ecografía 11-14 semanas con NT', 'PAPP-A y Beta-HCG (si disponible)'],
    cumplido: false
  },
  {
    id: 3,
    nombre: 'Ecografía Morfológica',
    semanas_inicio: 18,
    semanas_fin: 23,
    descripcion: 'Evaluación anatómica detallada del feto',
    examenes_requeridos: ['Ecografía Morfológica Nivel II'],
    cumplido: false
  },
  {
    id: 4,
    nombre: 'Test de O\'Sullivan (Diabetes Gestacional)',
    semanas_inicio: 24,
    semanas_fin: 28,
    descripcion: 'Tamizaje de diabetes gestacional',
    examenes_requeridos: ['Curva de Tolerancia a la Glucosa 75g'],
    cumplido: false
  },
  {
    id: 5,
    nombre: 'Evaluación Tercer Trimestre',
    semanas_inicio: 28,
    semanas_fin: 32,
    descripcion: 'Control de crecimiento fetal y bienestar materno',
    examenes_requeridos: ['Hemograma Control', 'Ecografía Doppler (si riesgo)', 'Cultivo Vaginal/Rectal (Streptococo B)'],
    cumplido: false
  },
  {
    id: 6,
    nombre: 'Preparación al Parto',
    semanas_inicio: 36,
    semanas_fin: 40,
    descripcion: 'Evaluación de condiciones obstétricas para el parto',
    examenes_requeridos: ['Monitoreo Fetal (NST)', 'Evaluación de Pelvis', 'Ecografía de Presentación'],
    cumplido: false
  }
];

export const VACUNAS_EMBARAZO = [
  { nombre: 'Influenza (Gripe)', trimestre: 'Cualquiera', obligatoria: true },
  { nombre: 'Tdap (Tétanos, Difteria, Pertussis)', trimestre: 'Tercer Trimestre (27-36 sem)', obligatoria: true },
  { nombre: 'Hepatitis B (si no inmunizada)', trimestre: 'Cualquiera', obligatoria: false },
  { nombre: 'COVID-19', trimestre: 'Cualquiera', obligatoria: true }
];

export const FACTORES_RIESGO = {
  MUY_ALTO: [
    'Edad < 16 o > 40 años',
    'Preeclampsia severa previa',
    'Diabetes pregestacional',
    'Hipertensión crónica',
    'Cardiopatía',
    'Nefropatía',
    'Cesáreas previas ≥ 2',
    'Muerte fetal o neonatal previa',
    'Placenta previa',
    'RCIU severo',
    'Embarazo gemelar',
    'VIH positivo',
    'Malformación uterina'
  ],
  ALTO: [
    'Edad > 35 años',
    'Obesidad (IMC > 35)',
    'Diabetes gestacional',
    'Preeclampsia leve',
    'Anemia severa (Hb < 9)',
    'Infección urinaria recurrente',
    'Antecedente de parto prematuro',
    '1 cesárea previa',
    'Abortos recurrentes (≥ 3)',
    'Embarazo no deseado',
    'Violencia doméstica',
    'Consumo de sustancias'
  ],
  BAJO: []
};

export const safeNum = (value: any): number => {
  if (value === null || value === undefined) return 0;
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  return isNaN(num) ? 0 : num;
};

export const getReferenceAU = (semanas: number) => {
  if (semanas < 13) return { p10: 0, p50: 0, p90: 0 };
  const p50 = semanas * 0.95 - 2;
  return { p10: p50 * 0.9, p50: p50, p90: p50 * 1.1 };
};

export const calcularEG = (fum: string): { semanas: number; dias: number; texto: string } => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasDiff = hoy.diff(fechaFum, 'days');
  const semanas = Math.floor(diasDiff / 7);
  const dias = diasDiff % 7;
  return { semanas, dias, texto: `${semanas}s ${dias}d` };
};

export const calcularFPP = (fum: string): string => {
  const fechaFum = dayjs(fum);
  return fechaFum.add(280, 'days').format('YYYY-MM-DD');
};

export const calcularIMC = (peso: number, talla: number): number => {
  return peso / ((talla / 100) ** 2);
};

export const calcularGananciaPesoRecomendada = (imcPregestacional: number, semanasEG: number): { minimo: number; maximo: number; total: { min: number; max: number } } => {
  let gananciaTotal = { min: 11.5, max: 16 };
  if (imcPregestacional < 18.5) gananciaTotal = { min: 12.5, max: 18 };
  else if (imcPregestacional >= 25 && imcPregestacional < 30) gananciaTotal = { min: 7, max: 11.5 };
  else if (imcPregestacional >= 30) gananciaTotal = { min: 5, max: 9 };

  const gananciaPromedio = (gananciaTotal.min + gananciaTotal.max) / 2;
  const gananciaActual = (gananciaPromedio / 40) * semanasEG;

  return {
    minimo: gananciaActual * 0.85,
    maximo: gananciaActual * 1.15,
    total: gananciaTotal
  };
};

export const interpretarLaboratorio = (examen: string, valor: number, unidad: string, semanasEG: number): { normal: boolean; interpretacion: string } => {
  const referencias: { [key: string]: { min: number; max: number; unidad: string } } = {
    'HEMOGLOBINA': { min: 11, max: 14, unidad: 'g/dL' },
    'HEMATOCRITO': { min: 33, max: 44, unidad: '%' },
    'LEUCOCITOS': { min: 6000, max: 17000, unidad: '/mm³' },
    'PLAQUETAS': { min: 150000, max: 400000, unidad: '/mm³' },
    'GLUCOSA': { min: 70, max: 105, unidad: 'mg/dL' },
    'CREATININA': { min: 0.4, max: 0.9, unidad: 'mg/dL' },
    'UREA': { min: 13, max: 35, unidad: 'mg/dL' },
    'TGO': { min: 0, max: 40, unidad: 'U/L' },
    'TGP': { min: 0, max: 40, unidad: 'U/L' },
    'PROTEINAS_ORINA': { min: 0, max: 150, unidad: 'mg/24h' }
  };

  const ref = referencias[examen.toUpperCase()];
  if (!ref) return { normal: true, interpretacion: 'Sin referencia disponible' };

  const normal = valor >= ref.min && valor <= ref.max;
  let interpretacion = normal ? 'NORMAL' : 'ANORMAL';
  if (!normal) {
    if (valor < ref.min) interpretacion += ' - BAJO';
    if (valor > ref.max) interpretacion += ' - ELEVADO';
  }
  return { normal, interpretacion };
};

export const calcularRiesgoPreeclampsia = (
  edad: number,
  imc: number,
  presionSistolica: number,
  presionDiastolica: number,
  antecedentes: { hipertension: boolean; preeclampsiaPrevias: number; diabetes: boolean }
): { nivel: 'BAJO' | 'MODERADO' | 'ALTO'; score: number; recomendaciones: string[] } => {
  let score = 0;
  const recomendaciones: string[] = [];
  if (edad >= 40) score += 3; else if (edad >= 35) score += 2; else if (edad < 18) score += 2;
  if (imc >= 35) score += 3; else if (imc >= 30) score += 2;
  if (presionSistolica >= 140 || presionDiastolica >= 90) {
    score += 5;
    recomendaciones.push('Control estricto de presión arterial cada 48-72 horas');
    recomendaciones.push('Considerar inicio de antihipertensivos');
  } else if (presionSistolica >= 130 || presionDiastolica >= 85) {
    score += 3;
    recomendaciones.push('Monitoreo de presión arterial semanal');
  }
  if (antecedentes.preeclampsiaPrevias > 0) {
    score += 4;
    recomendaciones.push('ASA 100mg/día desde semana 12 hasta el parto');
  }
  if (antecedentes.hipertension) { score += 3; recomendaciones.push('Evaluación por medicina interna'); }
  if (antecedentes.diabetes) { score += 2; recomendaciones.push('Control estricto de glicemia'); }

  let nivel: 'BAJO' | 'MODERADO' | 'ALTO' = 'BAJO';
  if (score >= 8) {
    nivel = 'ALTO';
    recomendaciones.push('Doppler de arterias uterinas en segundo trimestre');
    recomendaciones.push('Monitoreo fetal semanal desde semana 28');
  } else if (score >= 4) {
    nivel = 'MODERADO';
    recomendaciones.push('Control prenatal cada 2 semanas');
  }
  return { nivel, score, recomendaciones };
};

export const calcularPesoFetalEstimado = (dbt: number, ca: number, lf: number): number => {
  const logPeso = 1.335 - 0.0034 * ca * lf + 0.0316 * dbt + 0.0457 * ca + 0.1623 * lf;
  return Math.exp(logPeso);
};

export const calcularPercentilFetal = (pesoEstimado: number, semanasEG: number): { percentil: number; clasificacion: string } => {
  const tablaPesos: { [key: number]: { p10: number; p50: number; p90: number } } = {
    20: { p10: 275, p50: 330, p90: 380 },
    24: { p10: 550, p50: 660, p90: 770 },
    28: { p10: 950, p50: 1150, p90: 1350 },
    32: { p10: 1550, p50: 1900, p90: 2250 },
    36: { p10: 2350, p50: 2850, p90: 3400 },
    40: { p10: 2900, p50: 3500, p90: 4150 }
  };
  const semanaRef = Math.floor(semanasEG / 4) * 4;
  const ref = tablaPesos[semanaRef] || tablaPesos[40];
  let percentil = 50;
  if (pesoEstimado < ref.p10) percentil = 5;
  else if (pesoEstimado < ref.p50) percentil = 25;
  else if (pesoEstimado < ref.p90) percentil = 75;
  else percentil = 95;

  let clasificacion = 'Adecuado para edad gestacional';
  if (percentil < 10) clasificacion = 'RCIU (Restricción del Crecimiento Intrauterino)';
  if (percentil > 90) clasificacion = 'Grande para edad gestacional';
  return { percentil, clasificacion };
};

export const generarAlertas = (controles: any[], laboratorios: any[], embarazo: any): AlertaClinica[] => {
  const alertas: AlertaClinica[] = [];
  controles.forEach((control, idx) => {
    if (control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90) {
      alertas.push({
        id: `alerta-pa-${idx}`,
        tipo: 'ERROR',
        prioridad: 'ALTA',
        mensaje: `Hipertensión detectada: PA ${control.presion_arterial_sistolica}/${control.presion_arterial_diastolica} mmHg`,
        categoria: 'Signos Vitales',
        fecha_generacion: control.fecha,
        resuelta: false,
        acciones_recomendadas: ['Repetir toma de PA', 'Evaluación médica urgente', 'Descartar preeclampsia']
      });
    }
  });
  laboratorios.forEach((lab, idx) => {
    const tipoExamen = typeof lab.tipo_examen === 'string' ? lab.tipo_examen : String(lab.tipo_examen || '');
    if (tipoExamen.toLowerCase().includes('hemoglobina')) {
      const hbValue = parseFloat(lab.resultado);
      if (!isNaN(hbValue) && hbValue < 11) {
        alertas.push({
          id: `alerta-hb-${idx}`,
          tipo: 'WARNING',
          prioridad: 'MEDIA',
          mensaje: `Anemia detectada: Hemoglobina ${hbValue} g/dL`,
          categoria: 'Laboratorio',
          fecha_generacion: lab.fecha_toma,
          resuelta: false,
          acciones_recomendadas: ['Suplementación con hierro', 'Control en 4 semanas']
        });
      }
    }
  });
  return alertas;
};
export const interpretarNST = (
  fcfBasal: number,
  aceleraciones: number,
  deceleraciones: number,
  variabilidad: 'AUSENTE' | 'MINIMA' | 'MODERADA' | 'MARCADA'
): { reactivo: boolean; interpretacion: string; conducta: string } => {
  let reactivo = false;
  let interpretacion = '';
  let conducta = '';

  const fcfNormal = fcfBasal >= 110 && fcfBasal <= 160;
  const variabilidadNormal = variabilidad === 'MODERADA';
  const aceleracionesAdecuadas = aceleraciones >= 2;
  const sinDeceleraciones = deceleraciones === 0;

  if (fcfNormal && variabilidadNormal && aceleracionesAdecuadas && sinDeceleraciones) {
    reactivo = true;
    interpretacion = 'NST REACTIVO - Feto en buen estado';
    conducta = 'Continuar controles según protocolo';
  } else {
    interpretacion = 'NST NO REACTIVO';
    conducta = 'Valorar: ';
    if (!fcfNormal) conducta += 'FCF anormal - ';
    if (!variabilidadNormal) conducta += 'Variabilidad alterada - ';
    if (!aceleracionesAdecuadas) conducta += 'Pocas aceleraciones - ';
    if (!sinDeceleraciones) conducta += 'Presencia de deceleraciones - ';
    conducta += 'Considerar perfil biofísico o evaluación inmediata';
  }
  return { reactivo, interpretacion, conducta };
};

export const actualizarProtocolos = (controles: any[], ecografias: any[], laboratorios: any[]): ProtocoloObstetrico[] => {
  return PROTOCOLOS_EMBARAZO.map(protocolo => {
    const cumplido = controles.length > 0 || ecografias.length > 0 || laboratorios.length > 0;
    return { ...protocolo, cumplido };
  });
};

type TendenciaLab = { examen: string; valores: Array<{ fecha: string; valor: number; referencia: string }>; tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' };

  export const calcularTendencias = (laboratorios: any[]): TendenciaLab[] => {
  if (laboratorios.length < 2) return [];
  const tendencias: TendenciaLab[] = [];
  const parametros = new Set(['hemoglobina', 'hematocrito', 'leucocitos', 'plaquetas']);

  for (const param of parametros) {
    const valores: Array<{ fecha: string; valor: number; referencia: string }> = [];
    for (const lab of laboratorios) {
      const tipoLower = (lab.tipo_examen || '').toLowerCase();
      if (tipoLower.includes(param)) {
        const valor = parseFloat(lab.resultado);
        if (!isNaN(valor)) {
          valores.push({
            fecha: lab.fecha_toma,
            valor,
            referencia: lab.valores_referencia
          });
        }
      }
    }
    valores.sort((a, b) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime());

    if (valores.length >= 2) {
      const v1 = valores[valores.length - 2].valor;
      const v2 = valores[valores.length - 1].valor;
      let tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' = 'ESTABLE';
      
      if (param === 'hemoglobina' || param === 'hematocrito') {
        if (v2 > v1) tendencia = 'MEJORANDO';
        else if (v2 < v1) tendencia = 'EMPEORANDO';
      }
      
      tendencias.push({ examen: param.toUpperCase(), valores, tendencia });
    }
  }
  return tendencias;
};
