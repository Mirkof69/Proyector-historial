/**
 * Utilidades puras de clasificación clínica del triaje.
 * Extraídas de DetalleTriaje para reutilización y testeo aislado.
 */
import { TriajeEnfermeria } from '../../../services/triajeService';

export interface Clasificacion {
  text: string;
  color: string;
}

export const getClasificacionIMC = (imc: number): Clasificacion => {
  if (imc < 18.5) return { text: 'Bajo peso', color: 'processing' };
  if (imc < 25) return { text: 'Normal', color: 'success' };
  if (imc < 30) return { text: 'Sobrepeso', color: 'warning' };
  if (imc < 35) return { text: 'Obesidad I', color: 'warning' };
  if (imc < 40) return { text: 'Obesidad II', color: 'error' };
  return { text: 'Obesidad III', color: 'red-inverse' };
};

export const getClasificacionPresion = (sistolica: number, diastolica: number): Clasificacion => {
  if (sistolica >= 180 || diastolica >= 120) return { text: 'Crisis Hipertensiva', color: 'red-inverse' };
  if (sistolica >= 140 || diastolica >= 90) return { text: 'Hipertensión Stage 2', color: 'error' };
  if (sistolica >= 130 || diastolica >= 80) return { text: 'Hipertensión Stage 1', color: 'warning' };
  if (sistolica >= 120 && diastolica < 80) return { text: 'Elevada', color: 'warning' };
  return { text: 'Normal', color: 'success' };
};

export const computarAlertasTriaje = (triaje: TriajeEnfermeria): string[] => {
  const items: string[] = [];

  if (triaje.presion_sistolica >= 140 || triaje.presion_diastolica >= 90) {
    items.push('Presión arterial elevada (Riesgo de Preeclampsia si es gestante)');
  }
  if (triaje.temperatura >= 38) {
    items.push('Proceso febril detectado');
  }
  if (triaje.frecuencia_cardiaca > 100) {
    items.push('Taquicardia sinusal');
  } else if (triaje.frecuencia_cardiaca < 60 && triaje.frecuencia_cardiaca > 0) {
    items.push('Bradicardia');
  }
  if (triaje.saturacion_oxigeno && triaje.saturacion_oxigeno < 95) {
    items.push('Saturación de oxígeno por debajo del rango normal');
  }
  if (triaje.alertas && Array.isArray(triaje.alertas)) {
    items.push(...triaje.alertas);
  }

  return items;
};
