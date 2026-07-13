/**
 * Lógica clínica pura del formulario de parto: cálculo de alertas por edad
 * gestacional y recomendaciones por trimestre. Extraído de FormularioParto para
 * testeo aislado. Sin estado ni efectos — solo entrada (semanas/días) → salida.
 */
import { AlertaParto, Recomendacion } from '../../services/partosService';

export const computarAlertasEdadGestacional = (semanas: number, dias: number): AlertaParto[] => {
  const alertasTemp: AlertaParto[] = [];
  if (semanas < 20) {
    alertasTemp.push({
      tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
      mensaje: `⚠️ ABORTO: Edad gestacional muy temprana (${semanas}+${dias} semanas)`,
      recomendacion: 'Protocolo de aborto. Manejo de duelo. Apoyo psicológico.',
    });
  } else if (semanas < 28) {
    alertasTemp.push({
      tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
      mensaje: `🚨 PREMATURO EXTREMO: ${semanas}+${dias} semanas`,
      recomendacion: 'Requiere UCIN nivel III. Surfactante. Soporte ventilatorio.',
    });
  } else if (semanas < 32) {
    alertasTemp.push({
      tipo: 'critica', nivel: 'error', categoria: 'edad_gestacional',
      mensaje: `⚠️ MUY PREMATURO: ${semanas}+${dias} semanas`,
      recomendacion: 'Requiere UCIN. Monitoreo intensivo neonatal.',
    });
  } else if (semanas < 37) {
    alertasTemp.push({
      tipo: 'moderada', nivel: 'warning', categoria: 'edad_gestacional',
      mensaje: `⚠️ PREMATURO: ${semanas}+${dias} semanas`,
      recomendacion: 'Vigilancia neonatal. Riesgo de SDR. Considerar corticoides.',
    });
  } else if (semanas >= 42) {
    alertasTemp.push({
      tipo: 'moderada', nivel: 'warning', categoria: 'edad_gestacional',
      mensaje: `⚠️ POST-TÉRMINO: ${semanas}+${dias} semanas`,
      recomendacion: 'Evaluación urgente. Considerar inducción. Monitoreo fetal continuo.',
    });
  }
  return alertasTemp;
};

export const computarRecomendacionesPorTrimestre = (semanas: number): Recomendacion[] => {
  const recs: Recomendacion[] = [];
  if (semanas < 14) {
    recs.push({
      tipo: 'informacion', periodo: 'Primer Trimestre', titulo: 'Cuidados del Primer Trimestre',
      recomendaciones: [
        'Iniciar ácido fólico (400-800 mcg/día)', 'Evitar alcohol, tabaco y drogas',
        'Ecografía del primer trimestre (11-13 semanas)', 'Exámenes de laboratorio',
        'Evitar medicamentos no prescritos', 'No levantar objetos pesados',
      ],
    });
  }
  if (semanas >= 14 && semanas < 28) {
    recs.push({
      tipo: 'informacion', periodo: 'Segundo Trimestre', titulo: 'Cuidados del Segundo Trimestre',
      recomendaciones: [
        'Ecografía morfológica (18-22 semanas)', 'Prueba de glucosa (24-28 semanas)',
        'Control de peso y presión arterial', 'Ejercicio moderado regular',
        'Suplemento de hierro si hay anemia', 'Vigilar signos de parto prematuro',
      ],
    });
  }
  if (semanas >= 28) {
    recs.push({
      tipo: 'importante', periodo: 'Tercer Trimestre', titulo: 'Cuidados del Tercer Trimestre',
      recomendaciones: [
        'Monitoreo fetal frecuente', 'Controles prenatales frecuentes',
        'Preparación para el parto', 'Vigilar movimientos fetales',
        'Acudir inmediatamente si hay signos de alarma',
      ],
    });
  }
  return recs;
};
