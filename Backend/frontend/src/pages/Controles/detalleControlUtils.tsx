import React from 'react';
import {
  HeartOutlined, FileTextOutlined, MedicineBoxOutlined, LineChartOutlined,
  SafetyOutlined, AlertOutlined, MedicineBoxFilled, ExperimentOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { ControlPrenatal } from '../../services/controlesService';

// Hoisted tab labels (static JSX)
export const tabInfoGeneral = (
  <span>
    <FileTextOutlined />
    Información General
  </span>
);
export const tabExamenObstetrico = (
  <span>
    <MedicineBoxOutlined />
    Examen Obstétrico
  </span>
);
export const tabEvolucion = (
  <span>
    <LineChartOutlined />
    Evolución
  </span>
);

export interface ComparacionControl {
  campo: string;
  valorAnterior: string | number;
  valorActual: string | number;
  cambio: 'mejora' | 'empeora' | 'igual';
  importante: boolean;
}

export interface RecomendacionMedica {
  tipo: 'urgente' | 'importante' | 'sugerencia';
  titulo: string;
  descripcion: string;
  icono: React.ReactNode;
}

export interface IndicadorCalidad {
  nombre: string;
  cumple: boolean;
  descripcion: string;
}

// ========== ✅ FIX: CÁLCULO CORRECTO DE IMC ==========
export const calcularIMC = (peso: number | null | undefined, talla: number | null | undefined): number | null => {
  if (!peso || !talla || peso <= 0 || talla <= 0) return null;
  const tallaMts = talla / 100; // ✅ Convertir cm a metros
  const imc = peso / (tallaMts * tallaMts);
  return imc;
};

export const clasificarIMC = (imc: number | null): { texto: string; color: string } => {
  if (!imc) return { texto: '-', color: 'default' };
  if (imc < 18.5) return { texto: 'Bajo peso', color: 'warning' };
  if (imc < 25) return { texto: 'Normal', color: 'success' };
  if (imc < 30) return { texto: 'Sobrepeso', color: 'warning' };
  return { texto: 'Obesidad', color: 'error' };
};

// ========== ✅ FIX: OBTENER EDAD GESTACIONAL FORMATEADA ==========
export const getEdadGestacional = (control: ControlPrenatal): string => {
  // Intentar obtener desde el backend (formato "16+6")
  if ((control as any).edad_gestacional) {
    const eg = (control as any).edad_gestacional;
    const partes = eg.split('+');
    if (partes.length === 2) {
      return `${partes[0]} semanas + ${partes[1]} días`;
    }
  }

  // Fallback: calcular manualmente
  const semanas = control.edad_gestacional_semanas || 0;
  const dias = control.edad_gestacional_dias || 0;
  return `${semanas} semanas + ${dias} días`;
};

// ========== ✅ FIX: OBTENER PRESIÓN ARTERIAL FORMATEADA ==========
export const getPresionArterial = (control: ControlPrenatal): string => {
  // Intentar obtener desde el backend (formato "120/80")
  if ((control as any).presion_arterial) {
    return (control as any).presion_arterial;
  }

  // Fallback: calcular manualmente
  if (control.presion_arterial_sistolica && control.presion_arterial_diastolica) {
    return `${control.presion_arterial_sistolica}/${control.presion_arterial_diastolica}`;
  }

  return '-';
};

// ========== RECOMENDACIONES MÉDICAS ==========
export const buildRecomendaciones = (control: ControlPrenatal | null): RecomendacionMedica[] => {
  if (!control) return [];

  const recomendaciones: RecomendacionMedica[] = [];

  if (
    control.presion_arterial_sistolica &&
    control.presion_arterial_diastolica &&
    (control.presion_arterial_sistolica >= 140 || control.presion_arterial_diastolica >= 90)
  ) {
    recomendaciones.push({
      tipo: 'urgente',
      titulo: 'Hipertensión Arterial Detectada',
      descripcion:
        'Solicitar pruebas de función renal, proteinuria en orina de 24h, perfil hepático. Evaluar preeclampsia. Control en 48-72 horas.',
      icono: <AlertOutlined />,
    });
  }

  if (
    control.frecuencia_cardiaca_fetal &&
    (control.frecuencia_cardiaca_fetal < 110 || control.frecuencia_cardiaca_fetal > 160)
  ) {
    recomendaciones.push({
      tipo: 'urgente',
      titulo: 'FCF Anormal',
      descripcion:
        'Realizar NST (monitoreo fetal no estresante) inmediato. Evaluar bienestar fetal con perfil biofísico. Considerar interconsulta con medicina materno-fetal.',
      icono: <HeartOutlined />,
    });
  }

  if (control.movimientos_fetales === 'disminuidos') {
    recomendaciones.push({
      tipo: 'importante',
      titulo: 'Movimientos Fetales Disminuidos',
      descripcion:
        'Realizar NST en las próximas 24 horas. Instruir a la paciente sobre conteo de movimientos fetales (mínimo 10 en 2 horas). Control en 48 horas.',
      icono: <MedicineBoxFilled />,
    });
  }

  if (control.proteinuria && !['negativa', 'trazas'].includes(control.proteinuria)) {
    recomendaciones.push({
      tipo: 'importante',
      titulo: 'Proteinuria Positiva',
      descripcion:
        'Solicitar proteinuria en orina de 24h, función renal completa, ácido úrico. Evaluar signos de preeclampsia (cefalea, trastornos visuales, epigastralgia).',
      icono: <ExperimentOutlined />,
    });
  }

  if (control.peso_actual && control.peso_pregestacional) {
    const ganancia = control.peso_actual - control.peso_pregestacional;
    const semanas = control.edad_gestacional_semanas || 0;
    if (semanas > 12 && ganancia > (semanas < 28 ? 0.5 * (semanas - 12) : 18)) {
      recomendaciones.push({
        tipo: 'sugerencia',
        titulo: 'Ganancia de Peso Excesiva',
        descripcion:
          'Referir a nutrición para evaluación y plan alimentario. Descartar retención de líquidos, diabetes gestacional. Educar sobre alimentación saludable.',
        icono: <SafetyOutlined />,
      });
    }
  }

  if (control.edad_gestacional_semanas && control.edad_gestacional_semanas > 28 && control.numero_control < 5) {
    recomendaciones.push({
      tipo: 'sugerencia',
      titulo: 'Controles Prenatales Insuficientes',
      descripcion:
        'Programar controles más frecuentes (cada 2 semanas hasta semana 36, luego semanales). Educar sobre importancia del control prenatal regular.',
      icono: <ClockCircleOutlined />,
    });
  }

  return recomendaciones;
};

// ========== INDICADORES DE CALIDAD ==========
export const buildIndicadoresCalidad = (control: ControlPrenatal | null): IndicadorCalidad[] => {
  if (!control) return [];

  return [
    {
      nombre: 'Signos vitales completos',
      cumple: !!(
        control.presion_arterial_sistolica &&
        control.presion_arterial_diastolica &&
        control.frecuencia_cardiaca &&
        control.temperatura
      ),
      descripcion: 'PA, FC y temperatura registrados',
    },
    {
      nombre: 'Evaluación fetal completa',
      cumple: !!(
        control.frecuencia_cardiaca_fetal &&
        control.presentacion_fetal &&
        control.movimientos_fetales
      ),
      descripcion: 'FCF, presentación y movimientos evaluados',
    },
    {
      nombre: 'Mediciones antropométricas',
      cumple: !!(control.peso_actual && control.altura_uterina),
      descripcion: 'Peso y altura uterina registrados',
    },
    {
      nombre: 'Evaluación de riesgos',
      cumple: !!(control.edema && control.proteinuria),
      descripcion: 'Edema y proteinuria evaluados',
    },
    {
      nombre: 'Observaciones clínicas',
      cumple: !!(control.observaciones && control.observaciones.length > 10),
      descripcion: 'Notas médicas detalladas',
    },
  ];
};

// ========== COMPARACIÓN CON CONTROL ANTERIOR ==========
export const buildComparacion = (control: ControlPrenatal | null, controlAnterior: ControlPrenatal | null): ComparacionControl[] => {
  if (!control || !controlAnterior) return [];

  const comparaciones: ComparacionControl[] = [];

  if (control.presion_arterial_sistolica && controlAnterior.presion_arterial_sistolica) {
    const cambio =
      control.presion_arterial_sistolica < controlAnterior.presion_arterial_sistolica
        ? 'mejora'
        : control.presion_arterial_sistolica > controlAnterior.presion_arterial_sistolica
          ? 'empeora'
          : 'igual';
    comparaciones.push({
      campo: 'PA Sistólica',
      valorAnterior: `${controlAnterior.presion_arterial_sistolica} mmHg`,
      valorActual: `${control.presion_arterial_sistolica} mmHg`,
      cambio,
      importante: control.presion_arterial_sistolica >= 140,
    });
  }

  if (control.presion_arterial_diastolica && controlAnterior.presion_arterial_diastolica) {
    const cambio =
      control.presion_arterial_diastolica < controlAnterior.presion_arterial_diastolica
        ? 'mejora'
        : control.presion_arterial_diastolica > controlAnterior.presion_arterial_diastolica
          ? 'empeora'
          : 'igual';
    comparaciones.push({
      campo: 'PA Diastólica',
      valorAnterior: `${controlAnterior.presion_arterial_diastolica} mmHg`,
      valorActual: `${control.presion_arterial_diastolica} mmHg`,
      cambio,
      importante: control.presion_arterial_diastolica >= 90,
    });
  }

  if (control.frecuencia_cardiaca_fetal && controlAnterior.frecuencia_cardiaca_fetal) {
    const normalActual =
      control.frecuencia_cardiaca_fetal >= 110 && control.frecuencia_cardiaca_fetal <= 160;
    const normalAnterior =
      controlAnterior.frecuencia_cardiaca_fetal >= 110 &&
      controlAnterior.frecuencia_cardiaca_fetal <= 160;
    const cambio =
      normalActual && !normalAnterior
        ? 'mejora'
        : !normalActual && normalAnterior
          ? 'empeora'
          : 'igual';

    comparaciones.push({
      campo: 'FCF',
      valorAnterior: `${controlAnterior.frecuencia_cardiaca_fetal} lpm`,
      valorActual: `${control.frecuencia_cardiaca_fetal} lpm`,
      cambio,
      importante: !normalActual,
    });
  }

  if (control.peso_actual && controlAnterior.peso_actual) {
    const diferencia = control.peso_actual - controlAnterior.peso_actual;
    const cambio = diferencia < 0 ? 'mejora' : diferencia > 0 ? 'empeora' : 'igual';
    comparaciones.push({
      campo: 'Peso Materno',
      valorAnterior: `${controlAnterior.peso_actual} kg`,
      valorActual: `${control.peso_actual} kg (${diferencia > 0 ? '+' : ''}${diferencia.toFixed(1)} kg)`,
      cambio,
      importante: Math.abs(diferencia) > 2,
    });
  }

  if (control.altura_uterina && controlAnterior.altura_uterina) {
    const diferencia = control.altura_uterina - controlAnterior.altura_uterina;
    const cambio = diferencia >= 0 ? 'mejora' : 'empeora';
    comparaciones.push({
      campo: 'Altura Uterina',
      valorAnterior: `${controlAnterior.altura_uterina} cm`,
      valorActual: `${control.altura_uterina} cm (${diferencia > 0 ? '+' : ''}${diferencia.toFixed(1)} cm)`,
      cambio,
      importante: diferencia < 0,
    });
  }

  return comparaciones;
};
