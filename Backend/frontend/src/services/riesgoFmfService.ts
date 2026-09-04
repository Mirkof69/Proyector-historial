/**
 * Cálculo de riesgo con el modelo de la Fetal Medicine Foundation, en el servidor.
 *
 * Por qué existe este servicio
 * ----------------------------
 * El backend tenía 543 líneas implementando el modelo bayesiano de la FMF
 * —preeclampsia y cribado de trisomías— y **ninguna pantalla podía llegar a
 * ellas**: ningún módulo importaba ese servicio. Mientras tanto, el frontend
 * calculaba el riesgo de preeclampsia por su cuenta en el navegador.
 *
 * Los dos modelos no son equivalentes, y esa es la razón de conectar el del
 * servidor en vez de borrarlo: el del navegador **exige todos los
 * biomarcadores** (PlGF, sFlt-1, PAPP-A, MAP, Doppler uterino), que muchas
 * clínicas bolivianas no tienen. El del servidor da un riesgo solo con la
 * historia clínica y lo refina si los marcadores llegan.
 *
 * Además, el cálculo en el servidor queda auditado: un riesgo de preeclampsia
 * orienta la decisión de dar aspirina profiláctica, y hay que poder
 * reconstruir quién lo calculó y con qué datos.
 */

import apiClient from './api';

/** Datos del cribado de preeclampsia. Solo los cuatro primeros son obligatorios. */
export interface DatosPreeclampsiaFMF {
  edad_materna: number;
  peso_kg: number;
  talla_cm: number;
  semanas: number;

  origen_etnico?: string;
  metodo_concepcion?: string;
  fumadora?: boolean;
  hipertension_cronica?: boolean;
  diabetes_tipo1?: boolean;
  diabetes_tipo2?: boolean;
  lupus?: boolean;
  sindrome_antifosfolipidos?: boolean;
  historia_preeclampsia?: boolean;
  intervalo_embarazo_meses?: number | null;

  /** Biomarcadores. Opcionales: sin ellos se calcula por historia clínica. */
  pas_mmhg?: number | null;
  pad_mmhg?: number | null;
  utap_ip_promedio?: number | null;
  plgf_pg_ml?: number | null;
}

export interface ResultadoPreeclampsiaFMF {
  riesgo_basal: number;
  riesgo_ajustado_historia: number;
  riesgo_ajustado_biomarcadores: number;
  riesgo_final: number;
  clasificacion_riesgo: string;
  /** Si es true, corresponde aspirina profiláctica antes de la semana 16. */
  requiere_aspirina: boolean;
  factores_riesgo_presentes: string[];
  recomendaciones: string[];
}

/** Cribado combinado del primer trimestre. La translucencia nucal es obligatoria. */
export interface DatosTrisomiasFMF {
  edad_materna: number;
  semanas: number;
  translucencia_nucal_mm: number;

  papp_a_mom?: number | null;
  free_bhcg_mom?: number | null;
  hueso_nasal_presente?: boolean | null;
  flujo_ductus_venoso?: 'normal' | 'anormal' | null;
  regurgitacion_tricuspidea?: boolean;
}

export interface ResultadoTrisomiasFMF {
  riesgo_t21_basal: number;
  riesgo_t21_ajustado: number;
  riesgo_t18_basal: number;
  riesgo_t18_ajustado: number;
  riesgo_t13_basal: number;
  riesgo_t13_ajustado: number;
  clasificacion_t21: string;
  clasificacion_t18: string;
  clasificacion_t13?: string;
  recomendaciones?: string[];
}

/** Paneles de laboratorio que el servidor sabe interpretar. */
export interface PanelesLaboratorio {
  hemograma?: Record<string, number>;
  glucosa?: Record<string, number>;
  funcion_hepatica?: Record<string, number>;
  funcion_renal?: Record<string, number>;
}

export interface AnalisisPanel {
  valores_anormales: Record<string, unknown>[] | string[];
  patologias_detectadas: string[];
  alertas: string[];
  recomendaciones: string[];
  riesgo?: string;
  error?: string;
}

export type ResultadoLaboratorio = Partial<Record<keyof PanelesLaboratorio, AnalisisPanel>>;

export const riesgoFmfService = {
  /**
   * Riesgo de preeclampsia con el modelo completo de la FMF.
   *
   * Funciona sin biomarcadores: en ese caso devuelve el riesgo por historia
   * clínica, que es lo único disponible en una clínica sin laboratorio
   * especializado, y sigue sirviendo para decidir la aspirina.
   */
  async calcularPreeclampsia(datos: DatosPreeclampsiaFMF): Promise<ResultadoPreeclampsiaFMF> {
    const { data } = await apiClient.post<ResultadoPreeclampsiaFMF>(
      '/calculadoras-avanzadas/fmf/preeclampsia/',
      datos,
    );
    return data;
  },

  /** Cribado de trisomías 21, 18 y 13 del primer trimestre. */
  async calcularTrisomias(datos: DatosTrisomiasFMF): Promise<ResultadoTrisomiasFMF> {
    const { data } = await apiClient.post<ResultadoTrisomiasFMF>(
      '/calculadoras-avanzadas/fmf/trisomias/',
      datos,
    );
    return data;
  },

  /**
   * Interpreta paneles de laboratorio con los rangos propios del embarazo.
   *
   * Se envían solo los paneles que se tengan; el servidor devuelve un bloque
   * por cada uno. Si un panel falla, los demás siguen llegando.
   */
  async analizarLaboratorio(paneles: PanelesLaboratorio): Promise<ResultadoLaboratorio> {
    const { data } = await apiClient.post<ResultadoLaboratorio>(
      '/ia/laboratorio/analizar/',
      paneles,
    );
    return data;
  },
};

export default riesgoFmfService;
