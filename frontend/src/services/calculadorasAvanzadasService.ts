/**
 * =============================================================================
 * SERVICIO DE CALCULADORAS AVANZADAS
 * =============================================================================
 * Calculadoras médicas avanzadas y especializadas
 * =============================================================================
 */

import api from './api';

export interface CalculoRiesgoCardiovascular {
  edad: number;
  presion_sistolica: number;
  presion_diastolica: number;
  colesterol_total?: number;
  colesterol_hdl?: number;
  diabetes: boolean;
  fumadora: boolean;
  imc?: number;
}

export interface CalculoRiesgoTromboembolia {
  edad: number;
  imc: number;
  embarazo_multiple: boolean;
  reposo_prolongado: boolean;
  historia_trombosis: boolean;
  trombofilias: boolean;
  cesarea_programada: boolean;
}

export interface CalculoDosisMedicamento {
  medicamento: string;
  peso_kg: number;
  edad_gestacional_semanas: number;
  funcion_renal?: string;
  funcion_hepatica?: string;
}

export interface CalculoRiesgoPrematuro {
  edad_materna: number;
  gestas_previas: number;
  partos_prematuros_previos: number;
  longitud_cervical_mm: number;
  edad_gestacional_semanas: number;
  embarazo_multiple: boolean;
  infeccion_urinaria: boolean;
}

export interface CalculoCrecimientoFetal {
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  peso_estimado_gramos: number;
  circunferencia_abdominal_mm: number;
  diametro_biparietal_mm: number;
  longitud_femur_mm: number;
}

export interface CalculoIndiceResistencia {
  velocidad_sistolica: number;
  velocidad_diastolica: number;
  arteria: string;
}

class CalculadorasAvanzadasService {
  /**
   * Calcular riesgo cardiovascular en embarazo
   */
  async calcularRiesgoCardiovascular(data: CalculoRiesgoCardiovascular): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/riesgo-cardiovascular/', data);
    return response.data;
  }

  /**
   * Calcular riesgo de tromboembolia
   */
  async calcularRiesgoTromboembolia(data: CalculoRiesgoTromboembolia): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/riesgo-tromboembolia/', data);
    return response.data;
  }

  /**
   * Calcular dosis de medicamento
   */
  async calcularDosisMedicamento(data: CalculoDosisMedicamento): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/dosis-medicamento/', data);
    return response.data;
  }

  /**
   * Calcular riesgo de parto prematuro avanzado
   */
  async calcularRiesgoPrematuro(data: CalculoRiesgoPrematuro): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/riesgo-prematuro/', data);
    return response.data;
  }

  /**
   * Evaluar crecimiento fetal
   */
  async evaluarCrecimientoFetal(data: CalculoCrecimientoFetal): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/crecimiento-fetal/', data);
    return response.data;
  }

  /**
   * Calcular índice de resistencia Doppler
   */
  async calcularIndiceResistencia(data: CalculoIndiceResistencia): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/indice-resistencia/', data);
    return response.data;
  }

  /**
   * Calcular edad gestacional por múltiples parámetros
   */
  async calcularEdadGestacionalAvanzada(data: {
    fur?: string;
    lcc_mm?: number;
    dbp_mm?: number;
    cc_mm?: number;
    ca_mm?: number;
    lf_mm?: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/edad-gestacional/', data);
    return response.data;
  }

  /**
   * Calcular percentiles biométricos
   */
  async calcularPercentiles(data: {
    edad_gestacional_semanas: number;
    parametro: string;
    valor: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/percentiles/', data);
    return response.data;
  }

  /**
   * Evaluar perfil biofísico fetal
   */
  async evaluarPerfilBiofisico(data: {
    movimientos_fetales: number;
    tono_fetal: number;
    movimientos_respiratorios: number;
    volumen_liquido: number;
    nst: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/perfil-biofisico/', data);
    return response.data;
  }

  /**
   * Calcular índice de masa corporal ajustado
   */
  async calcularIMCAjustado(data: {
    peso_kg: number;
    talla_cm: number;
    edad_gestacional_semanas: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/imc-ajustado/', data);
    return response.data;
  }

  /**
   * Calcular ganancia de peso recomendada
   */
  async calcularGananciaPeso(data: {
    peso_pregestacional_kg: number;
    talla_cm: number;
    edad_gestacional_semanas: number;
    peso_actual_kg: number;
  }): Promise<any> {
    const response = await api.post('/calculadoras-avanzadas/ganancia-peso/', data);
    return response.data;
  }

  /**
   * Listar todas las calculadoras disponibles
   */
  async listarCalculadoras(): Promise<any> {
    const response = await api.get('/calculadoras-avanzadas/');
    return response.data;
  }
}

export const calculadorasAvanzadasService = new CalculadorasAvanzadasService();
export default calculadorasAvanzadasService;
