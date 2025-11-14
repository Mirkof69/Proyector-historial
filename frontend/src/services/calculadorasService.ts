/**
 * =============================================================================
 * SERVICIO DE CALCULADORAS FMF
 * =============================================================================
 * Acceso a las 15 calculadoras de la Fetal Medicine Foundation
 * =============================================================================
 */

import api from './api';
import {
  CalculadoraPreeclampsia,
  ResultadoPreeclampsia,
  CalculadoraTrisomias,
  ResultadoTrisomias,
  CalculadoraSGA,
  CalculadoraDiabetes,
  CalculadoraPartoPretermino,
} from '../types';

class CalculadorasService {
  /**
   * Listar todas las calculadoras disponibles
   */
  async list(): Promise<any[]> {
    const response = await api.get('/calculadoras/lista/');
    return response.data;
  }

  /**
   * 1. Predicción de Preeclampsia
   */
  async preeclampsia(data: CalculadoraPreeclampsia): Promise<ResultadoPreeclampsia> {
    const response = await api.post<{ resultado: ResultadoPreeclampsia }>(
      '/calculadoras/preeclampsia/',
      data
    );
    return response.data.resultado;
  }

  /**
   * 2. Screening de Trisomías (21, 18, 13)
   */
  async trisomias(data: CalculadoraTrisomias): Promise<ResultadoTrisomias> {
    const response = await api.post<{ resultado: ResultadoTrisomias }>(
      '/calculadoras/trisomias/',
      data
    );
    return response.data.resultado;
  }

  /**
   * 3. Predicción de SGA (Small for Gestational Age)
   */
  async sga(data: CalculadoraSGA): Promise<any> {
    const response = await api.post('/calculadoras/sga/', data);
    return response.data.resultado;
  }

  /**
   * 4. Predicción de Diabetes Gestacional
   */
  async diabetesGestacional(data: CalculadoraDiabetes): Promise<any> {
    const response = await api.post('/calculadoras/diabetes_gestacional/', data);
    return response.data.resultado;
  }

  /**
   * 5. Predicción de Parto Pretérmino
   */
  async partoPretermino(data: CalculadoraPartoPretermino): Promise<any> {
    const response = await api.post('/calculadoras/parto_pretermino/', data);
    return response.data.resultado;
  }

  /**
   * 6. Peso Fetal Estimado
   */
  async pesoFetal(data: {
    dbp: number;
    ca: number;
    fl: number;
    hc?: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/peso_fetal/', data);
    return response.data.resultado;
  }

  /**
   * 7. Evaluación de Crecimiento Fetal
   */
  async crecimientoFetal(data: {
    peso_fetal: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/crecimiento_fetal/', data);
    return response.data.resultado;
  }

  /**
   * 8. Translucencia Nucal
   */
  async translucenciaNucal(data: {
    nt_mm: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/translucencia_nucal/', data);
    return response.data.resultado;
  }

  /**
   * 9. Doppler Fetal
   */
  async dopplerFetal(data: {
    tipo: 'arteria_umbilical' | 'arteria_cerebral_media';
    ip: number;
    ir?: number;
    psv?: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/doppler_fetal/', data);
    return response.data.resultado;
  }

  /**
   * 10. Índice de Pulsatilidad Arterias Uterinas
   */
  async ipUterinas(data: {
    ip_promedio: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/ip_uterinas/', data);
    return response.data.resultado;
  }

  /**
   * 11. Presión Arterial Media (PAM)
   */
  async presionArterialMedia(data: {
    pas: number;
    pad: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/presion_arterial_media/', data);
    return response.data.resultado;
  }

  /**
   * 12. Biomarcadores (sFlt-1/PlGF ratio)
   */
  async biomarcadores(data: {
    sflt1: number;
    plgf: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/biomarcadores/', data);
    return response.data.resultado;
  }

  /**
   * 13. Índice de Shock
   */
  async indiceShock(data: {
    fc: number;
    pas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/indice_shock/', data);
    return response.data.resultado;
  }

  /**
   * 14. Test No Estresante (NST)
   */
  async testNoEstresante(data: {
    fcf_basal: number;
    aceleraciones: number;
    desaceleraciones: string;
    variabilidad: number;
    duracion_minutos: number;
    eg_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras/test_no_estresante/', data);
    return response.data.resultado;
  }
}

export const calculadorasService = new CalculadorasService();
export default calculadorasService;
