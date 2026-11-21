/**
 * Cribado de preeclampsia por factores clínicos (ACOG 2021 / USPSTF 2021).
 *
 * Sustituye a dos cálculos por puntos distintos, uno en cada calculadora:
 * uno sumaba la PA ≥140/90 y la proteinuria (eso ya es preeclampsia, no un
 * factor de riesgo) y el otro llamaba «moderado» a una preeclampsia previa,
 * que por sí sola ya indica aspirina.
 *
 *   1 factor alto              → riesgo alto: aspirina recomendada
 *   ≥2 factores moderados      → riesgo moderado: considerar aspirina
 *   si no                      → riesgo bajo
 */
export interface FactoresPreeclampsia {
  preeclampsiaPrevia?: boolean;
  embarazoMultiple?: boolean;
  hipertensionCronica?: boolean;
  diabetesPregestacional?: boolean;
  enfermedadRenal?: boolean;
  enfermedadAutoinmune?: boolean;
  nuliparidad?: boolean;
  obesidad?: boolean;
  edadMaterna?: number;
  intervaloMayor10Anios?: boolean;
  /** PA actual: no es factor de riesgo, pero si es alta se avisa aparte. */
  presionSistolica?: number;
  presionDiastolica?: number;
  proteinuria?: boolean;
}

export interface EvaluacionPreeclampsia {
  nivel: 'bajo' | 'moderado' | 'alto';
  texto: string;
  color: 'green' | 'orange' | 'red';
  factoresAltos: string[];
  factoresModerados: string[];
  aspirina: string;
  recomendaciones: string[];
  /** Presente si la PA ya es de hipertensión: requiere evaluación, no cribado. */
  alertaHipertension?: string;
}

export function evaluarRiesgoPreeclampsia(f: FactoresPreeclampsia): EvaluacionPreeclampsia {
  const altos: string[] = [];
  if (f.preeclampsiaPrevia) altos.push('Preeclampsia previa');
  if (f.embarazoMultiple) altos.push('Embarazo múltiple');
  if (f.hipertensionCronica) altos.push('Hipertensión crónica');
  if (f.diabetesPregestacional) altos.push('Diabetes pregestacional');
  if (f.enfermedadRenal) altos.push('Enfermedad renal');
  if (f.enfermedadAutoinmune) altos.push('Enfermedad autoinmune (LES, SAF)');

  const moderados: string[] = [];
  if (f.nuliparidad) moderados.push('Nuliparidad');
  if (f.obesidad) moderados.push('Obesidad (IMC > 30)');
  if (f.edadMaterna !== undefined && f.edadMaterna >= 35) moderados.push('Edad ≥ 35 años');
  if (f.intervaloMayor10Anios) moderados.push('Intervalo intergenésico > 10 años');

  let alertaHipertension: string | undefined;
  if ((f.presionSistolica ?? 0) >= 140 || (f.presionDiastolica ?? 0) >= 90) {
    alertaHipertension = f.proteinuria
      ? 'PA ≥ 140/90 con proteinuria: criterios de preeclampsia. Evaluación inmediata, no es un cribado.'
      : 'PA ≥ 140/90: hipertensión. Confirmar con una segunda toma y evaluar preeclampsia.';
  }

  if (altos.length > 0) {
    return {
      nivel: 'alto', texto: 'Riesgo alto', color: 'red', factoresAltos: altos, factoresModerados: moderados,
      aspirina: 'Aspirina 150 mg por la noche desde las 12 semanas (antes de las 16) hasta las 36 semanas.',
      recomendaciones: ['Control prenatal cada 2-3 semanas', 'PA y proteinuria en cada visita',
        'Doppler de arterias uterinas', 'Vigilancia del crecimiento fetal'],
      alertaHipertension,
    };
  }
  if (moderados.length >= 2) {
    return {
      nivel: 'moderado', texto: 'Riesgo moderado', color: 'orange', factoresAltos: altos, factoresModerados: moderados,
      aspirina: 'Considerar aspirina 150 mg por la noche desde las 12 semanas.',
      recomendaciones: ['Control prenatal cada 3-4 semanas', 'Automonitoreo de la PA', 'Educación en signos de alarma'],
      alertaHipertension,
    };
  }
  return {
    nivel: 'bajo', texto: 'Riesgo bajo', color: 'green', factoresAltos: altos, factoresModerados: moderados,
    aspirina: 'No indicada por factores clínicos.',
    recomendaciones: ['Control prenatal habitual', 'Vigilancia estándar de la PA'],
    alertaHipertension,
  };
}
