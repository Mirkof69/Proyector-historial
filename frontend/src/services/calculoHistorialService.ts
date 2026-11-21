/**
 * =============================================================================
 * SERVICIO: HISTORIAL DE CALCULADORAS SIMPLES
 * =============================================================================
 * Persistencia en backend para las 8 calculadoras simples (Edad Gestacional,
 * Score Bishop, IMC, Riesgo Preeclampsia, Diabetes Gestacional, ILA, Peso
 * Fetal, Score Apgar). Antes solo se guardaban en localStorage.
 * =============================================================================
 */

import apiClient from './api';

export type TipoCalculadora =
  | 'edad_gestacional'
  | 'bishop'
  | 'imc'
  | 'riesgo_preeclampsia'
  | 'diabetes_gestacional'
  | 'ila'
  | 'peso_fetal'
  | 'apgar'
  | 'capurro'
  | 'silverman'
  | 'ballard'
  | 'icc'
  | 'pa_media'
  | 'fc_maxima';

export interface CalculoHistorial {
  id?: number;
  paciente?: number | null;
  paciente_nombre?: string | null;
  embarazo?: number | null;
  tipo_calculadora: TipoCalculadora;
  tipo_calculadora_display?: string;
  inputs_json: any;
  resultado_json: any;
  resultado_resumen?: string;
  fecha_calculo?: string;
  calculado_por?: number | null;
  calculado_por_nombre?: string | null;
}

const BASE_URL = '/calculadoras/historial/';

function normalizeList(data: any): CalculoHistorial[] {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

export const calculoHistorialService = {
  async listar(filtros?: { tipo_calculadora?: TipoCalculadora; paciente?: number }): Promise<CalculoHistorial[]> {
    try {
      const response = await apiClient.get(BASE_URL, { params: filtros });
      return normalizeList(response.data);
    } catch (error) {
      console.error('Error listando historial de calculadoras:', error);
      return [];
    }
  },

  async crear(data: CalculoHistorial): Promise<CalculoHistorial | null> {
    try {
      const response = await apiClient.post<CalculoHistorial>(BASE_URL, data);
      return response.data;
    } catch (error) {
      console.error('Error guardando resultado de calculadora:', error);
      return null;
    }
  },

  async eliminar(id: number): Promise<boolean> {
    try {
      await apiClient.delete(`${BASE_URL}${id}/`);
      return true;
    } catch (error) {
      console.error('Error eliminando resultado de calculadora:', error);
      return false;
    }
  },
};

export default calculoHistorialService;
