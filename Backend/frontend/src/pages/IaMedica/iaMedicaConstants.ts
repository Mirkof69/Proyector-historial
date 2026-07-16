import { BiometryResult } from '../../services/iaMedicaService';

// ── Tabla de percentiles normales de biometría fetal (referencia OMS) ─────────
export const BIOMETRY_REFERENCE: Record<keyof BiometryResult, { label: string; unit: string; min: number; max: number }> = {
  BPD_mm:          { label: 'Diámetro Biparietal (BPD)', unit: 'mm',  min: 45,   max: 95  },
  HC_mm:           { label: 'Circunferencia Cefálica (HC)', unit: 'mm', min: 170, max: 360 },
  AC_mm:           { label: 'Circunferencia Abdominal (AC)', unit: 'mm', min: 150, max: 350 },
  FL_mm:           { label: 'Longitud Femoral (FL)', unit: 'mm',  min: 30,   max: 80  },
  peso_estimado_g: { label: 'Peso Estimado', unit: 'g',   min: 500,  max: 4000 },
};

export const SHAP_RISK_LABELS: Record<string, string> = {
  riesgo_preeclampsia:        'Riesgo de Preeclampsia',
  riesgo_parto_prematuro:     'Riesgo de Parto Prematuro',
  riesgo_hemorragia:          'Riesgo de Hemorragia',
  riesgo_diabetes_gestacional:'Riesgo de Diabetes Gestacional',
  riesgo_mortalidad_perinatal:'Riesgo de Mortalidad Perinatal',
  riesgo_global:              'Score de Riesgo Global',
};
