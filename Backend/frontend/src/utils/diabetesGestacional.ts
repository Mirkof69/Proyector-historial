/**
 * Diabetes gestacional con la PTOG de 75 g, criterios IADPSG / OMS 2013
 * (los que usa la norma boliviana): basta UN valor alterado.
 *
 *   ayunas ≥ 92 mg/dL · 1 hora ≥ 180 mg/dL · 2 horas ≥ 153 mg/dL
 *
 * Ayunas ≥ 126 mg/dL (o 2 h ≥ 200) ya no es diabetes gestacional sino
 * diabetes manifiesta (pregestacional no diagnosticada).
 *
 * Antes la calculadora «avanzada» decía usar Carpenter-Coustan (CTOG de
 * 100 g, que lleva CUATRO valores) con tres, y exigía DOS alterados: con un
 * solo valor alto respondía «no cumple criterios» y se perdía el diagnóstico.
 */

export type ResultadoDG = {
  diagnostico: 'normal' | 'diabetes_gestacional' | 'diabetes_manifiesta';
  titulo: string;
  alterados: string[];
  recomendaciones: string[];
};

export const UMBRALES_IADPSG = { ayunas: 92, h1: 180, h2: 153 } as const;

export const evaluarDiabetesGestacional = (ayunas: number, h1?: number | null, h2?: number | null): ResultadoDG => {
  if (ayunas >= 126 || (h2 !== null && h2 !== undefined && h2 >= 200)) {
    return {
      diagnostico: 'diabetes_manifiesta',
      titulo: 'Diabetes manifiesta (no gestacional)',
      alterados: [ayunas >= 126 ? `Ayunas ${ayunas} ≥ 126` : `2 horas ${h2} ≥ 200`],
      recomendaciones: [
        'Manejo como diabetes pregestacional: control glucémico estricto y evaluación de daño a órgano blanco',
        'Referencia a endocrinología',
        'Ecografía morfológica y ecocardiografía fetal',
      ],
    };
  }
  const alterados: string[] = [];
  if (ayunas >= UMBRALES_IADPSG.ayunas) alterados.push(`Ayunas ${ayunas} ≥ ${UMBRALES_IADPSG.ayunas}`);
  if (h1 !== null && h1 !== undefined && h1 >= UMBRALES_IADPSG.h1) alterados.push(`1 hora ${h1} ≥ ${UMBRALES_IADPSG.h1}`);
  if (h2 !== null && h2 !== undefined && h2 >= UMBRALES_IADPSG.h2) alterados.push(`2 horas ${h2} ≥ ${UMBRALES_IADPSG.h2}`);
  if (alterados.length === 0) {
    return {
      diagnostico: 'normal',
      titulo: 'PTOG normal',
      alterados,
      recomendaciones: ['Dieta saludable y actividad física', 'Repetir tamizaje si aparecen factores de riesgo'],
    };
  }
  return {
    diagnostico: 'diabetes_gestacional',
    titulo: 'Diabetes gestacional',
    alterados,
    recomendaciones: [
      'Plan nutricional y actividad física',
      'Automonitoreo de glucemia (ayunas y posprandial)',
      'Insulina si no se alcanzan las metas con dieta',
      'Ecografías seriadas: crecimiento fetal y líquido amniótico',
    ],
  };
};
