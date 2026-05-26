/**
 * =============================================================================
 * SERVICIO DE CONTROLES PRENATALES - VERSIÓN MEGA COMPLETA
 * =============================================================================
 * ✅ MEGA COMPLETO: Sistema integral de controles prenatales
 * 
 * MÓDULOS INCLUIDOS:
 * - CRUD completo de controles prenatales
 * - Cálculo automático de edad gestacional
 * - Evaluación de parámetros clínicos
 * - Generación de alertas automáticas
 * - Seguimiento de curvas de crecimiento
 * - Estimación de peso fetal
 * - Detección de riesgos
 * - Programación de controles
 * - Estadísticas y análisis
 * - Reportes y gráficas
 * - Exportación PDF/Excel
 * - Normalización de respuestas
 * 
 * ALINEACIÓN: 100% compatible con backend Django
 * =============================================================================
 */

import api from './api';

// ═══════════════════════════════════════════════════════════════════════════
// TIPOS Y ENUMS
// ═══════════════════════════════════════════════════════════════════════════

type EstadoControl = 'programado' | 'realizado' | 'cancelado' | 'reprogramado';
type ResultadoControl = 'normal' | 'alterado' | 'critico';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES
// ═══════════════════════════════════════════════════════════════════════════

export interface ControlPrenatal {
  // Identificación
  id?: number;

  // Relaciones
  embarazo: number;
  embarazo_id?: number; // ✅ Alias para compatibilidad con serializer de detalle
  paciente?: number;
  medico?: number;

  // Información poblada
  paciente_info?: {
    id: number;
    nombre_completo: string;
    edad: number;
  };
  medico_info?: {
    id: number;
    nombre_completo: string;
  };
  embarazo_info?: {
    id: number;
    numero_gesta: number;
    fum: string;
  };

  // Control
  numero_control: number;
  fecha_control: string;

  // Edad gestacional
  semanas_gestacion: number;
  dias_gestacion?: number;
  // ✅ ALIAS para compatibilidad con componentes
  edad_gestacional_semanas?: number; // Alias de semanas_gestacion
  edad_gestacional_dias?: number; // Alias de dias_gestacion
  edad_gestacional?: string; // "Xw+Yd"
  trimestre?: number;

  // Signos vitales
  presion_arterial?: string; // "120/80"
  presion_sistolica?: number;
  presion_diastolica?: number;
  // ✅ ALIAS para compatibilidad con componentes
  presion_arterial_sistolica?: number; // Alias de presion_sistolica
  presion_arterial_diastolica?: number; // Alias de presion_diastolica
  frecuencia_cardiaca?: number;
  temperatura?: number;
  saturacion_oxigeno?: number;

  // Medidas antropométricas
  peso_actual: number;
  peso_pregestacional?: number;
  ganancia_peso?: number;
  talla?: number;
  imc_actual?: number;

  // Medidas obstétricas
  altura_uterina?: number;
  circunferencia_abdominal?: number;

  // Evaluación fetal
  frecuencia_cardiaca_fetal?: number;
  movimientos_fetales?: 'presentes' | 'ausentes' | 'disminuidos' | 'aumentados';
  posicion_fetal?: string;
  presentacion_fetal?: 'cefalica' | 'podalica' | 'transversa';

  // Examen físico
  edema?: 'ausente' | 'no' | 'leve' | 'moderado' | 'severo' | 'generalizado';
  varices?: boolean;
  reflejos?: 'normales' | 'aumentados' | 'disminuidos';

  // Síntomas
  sintomas?: string;
  tiene_sintomas_alarma?: boolean;
  sintomas_alarma?: string[];

  // Resultados de laboratorio
  hemoglobina?: number;
  hematocrito?: number;
  grupo_sanguineo?: string;
  rh?: string;
  glicemia?: number;
  proteinuria?: string;

  // Evaluación y plan
  diagnostico?: string;
  plan_manejo?: string;
  indicaciones?: string;
  recetas?: string;
  examenes_solicitados?: string[];
  interconsultas?: string;

  // Próximo control
  fecha_proximo_control?: string;
  observaciones?: string;

  // Alertas y riesgos
  tiene_alertas?: boolean;
  alertas?: string[];
  nivel_riesgo?: 'bajo' | 'medio' | 'alto' | 'critico';

  // Estado
  estado?: EstadoControl;
  resultado?: ResultadoControl;

  // Metadata
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  creado_por?: number;
  actualizado_por?: number;
}

interface ProgramacionControl {
  embarazo_id: number;
  fecha_sugerida: string;
  semanas_gestacion: number;
  es_obligatorio: boolean;
  motivo: string;
}

interface AlertaControl {
  tipo: string;
  severidad: 'baja' | 'media' | 'alta' | 'critica';
  mensaje: string;
  requiere_accion_inmediata: boolean;
}

interface EstadisticasControles {
  total_controles: number;
  controles_normales: number;
  controles_alterados: number;
  controles_criticos: number;
  promedio_controles_embarazo: number;
  adherencia_controles: number; // porcentaje
  controles_pendientes: number;
}

interface CurvaCrecimiento {
  semana: number;
  peso: number;
  altura_uterina: number;
  percentil_peso: number;
  percentil_altura: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE NORMALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════════

function normalizeListResponse<T>(data: any): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data?.results && Array.isArray(data.results)) return data.results as T[];
  if (data?.data && Array.isArray(data.data)) return data.data as T[];
  console.warn('⚠️ controlesService: Respuesta no es array:', data);
  return [];
}

function normalizeSingleResponse<T>(data: any): T {
  if (data?.data && typeof data.data === 'object') return data.data as T;
  return data as T;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════

export const controlesService = {

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CRUD BÁSICO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista todos los controles prenatales
   */
  async listar(filtros?: {
    embarazo?: number;
    paciente?: number;
    medico?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
    trimestre?: number;
    estado?: EstadoControl;
  }): Promise<ControlPrenatal[]> {
    try {
      const response = await api.get<ControlPrenatal[]>('/controles/', { params: filtros });
      return normalizeListResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando controles:', error);
      throw error;
    }
  },

  async getAll(filtros?: any): Promise<ControlPrenatal[]> {
    return this.listar(filtros);
  },

  /**
   * Obtiene un control por ID
   */
  async obtener(id: number): Promise<ControlPrenatal> {
    try {
      const response = await api.get<ControlPrenatal>(`/controles/${id}/`);
      return normalizeSingleResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo control ${id}:`, error);
      throw error;
    }
  },

  async getById(id: number): Promise<ControlPrenatal> {
    return this.obtener(id);
  },

  /**
   * Crea un nuevo control prenatal
   */
  async crear(data: Partial<ControlPrenatal>): Promise<ControlPrenatal> {
    try {
      const response = await api.post<ControlPrenatal>('/controles/', data);
      console.log('✅ Control prenatal creado');
      return normalizeSingleResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error('❌ Error creando control:', error);
      throw error;
    }
  },

  async create(data: Partial<ControlPrenatal>): Promise<ControlPrenatal> {
    return this.crear(data);
  },

  /**
   * Actualiza un control
   */
  async actualizar(id: number, data: Partial<ControlPrenatal>): Promise<ControlPrenatal> {
    try {
      const response = await api.put<ControlPrenatal>(`/controles/${id}/`, data);
      console.log(`✅ Control ${id} actualizado`);
      return normalizeSingleResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando control ${id}:`, error);
      throw error;
    }
  },

  async actualizarParcial(id: number, data: Partial<ControlPrenatal>): Promise<ControlPrenatal> {
    try {
      const response = await api.patch<ControlPrenatal>(`/controles/${id}/`, data);
      console.log(`✅ Control ${id} actualizado parcialmente`);
      return normalizeSingleResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando control ${id}:`, error);
      throw error;
    }
  },

  async update(id: number, data: Partial<ControlPrenatal>): Promise<ControlPrenatal> {
    return this.actualizar(id, data);
  },

  /**
   * Elimina un control
   */
  async eliminar(id: number): Promise<void> {
    try {
      await api.delete(`/controles/${id}/`);
      console.log(`✅ Control ${id} eliminado`);
    } catch (error: any) {
      console.error(`❌ Error eliminando control ${id}:`, error);
      throw error;
    }
  },

  async delete(id: number): Promise<void> {
    return this.eliminar(id);
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // BÚSQUEDAS ESPECÍFICAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene controles de un embarazo específico
   */
  async obtenerPorEmbarazo(embarazoId: number): Promise<ControlPrenatal[]> {
    return this.listar({ embarazo: embarazoId });
  },

  /**
   * Alias para compatibilidad
   */
  async getByEmbarazo(embarazoId: number): Promise<ControlPrenatal[]> {
    return this.obtenerPorEmbarazo(embarazoId);
  },

  /**
   * Obtiene controles de una paciente
   */
  async obtenerPorPaciente(pacienteId: number): Promise<ControlPrenatal[]> {
    return this.listar({ paciente: pacienteId });
  },

  /**
   * Obtiene último control de un embarazo
   */
  async obtenerUltimoControl(embarazoId: number): Promise<ControlPrenatal | null> {
    try {
      const response = await api.get<ControlPrenatal>(
        `/controles/ultimo-control/`,
        { params: { embarazo: embarazoId } }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      console.error('❌ Error obteniendo último control:', error);
      throw error;
    }
  },

  /**
   * Obtiene controles pendientes
   */
  async obtenerPendientes(): Promise<ControlPrenatal[]> {
    return this.listar({ estado: 'programado' });
  },

  /**
   * Obtiene controles con alertas
   */
  async obtenerConAlertas(): Promise<ControlPrenatal[]> {
    try {
      const response = await api.get<ControlPrenatal[]>('/controles/con-alertas/');
      return normalizeListResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo controles con alertas:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // PROGRAMACIÓN Y SEGUIMIENTO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Programar próximo control
   */
  async programarProximoControl(
    embarazoId: number,
    fechaControl: string
  ): Promise<ControlPrenatal> {
    try {
      const response = await api.post<ControlPrenatal>(
        '/controles/programar/',
        { embarazo: embarazoId, fecha_control: fechaControl }
      );
      console.log('✅ Control programado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error programando control:', error);
      throw error;
    }
  },

  /**
   * Obtener sugerencias de próximos controles
   */
  async obtenerSugerenciasControles(embarazoId: number): Promise<ProgramacionControl[]> {
    try {
      const response = await api.get<ProgramacionControl[]>(
        `/controles/sugerencias-controles/`,
        { params: { embarazo: embarazoId } }
      );
      return normalizeListResponse<ProgramacionControl>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo sugerencias:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // EVALUACIÓN Y ALERTAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Evaluar parámetros del control y generar alertas
   */
  async evaluarControl(controlId: number): Promise<AlertaControl[]> {
    try {
      const response = await api.post<AlertaControl[]>(
        `/controles/${controlId}/evaluar/`
      );
      return normalizeListResponse<AlertaControl>(response.data);
    } catch (error: any) {
      console.error(`❌ Error evaluando control ${controlId}:`, error);
      throw error;
    }
  },

  /**
   * Detectar factores de riesgo
   */
  async detectarRiesgos(controlId: number): Promise<{
    nivel_riesgo: string;
    factores: string[];
    recomendaciones: string[];
  }> {
    try {
      const response = await api.get(`/controles/${controlId}/detectar-riesgos/`);
      return response.data;
    } catch (error: any) {
      console.error('❌ Error detectando riesgos:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CÁLCULOS Y ANÁLISIS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Calcula IMC
   */
  calcularIMC(peso_kg: number, talla_m: number): number {
    return peso_kg / (talla_m * talla_m);
  },

  /**
   * Calcula ganancia de peso esperada
   */
  calcularGananciaPesoEsperada(
    imc_pregestacional: number,
    semanas: number
  ): { min: number; max: number } {
    // Según IMC pregestacional
    let gananciaTotal: { min: number; max: number };

    if (imc_pregestacional < 18.5) {
      // Bajo peso: 12.5-18 kg
      gananciaTotal = { min: 12.5, max: 18 };
    } else if (imc_pregestacional < 25) {
      // Peso normal: 11.5-16 kg
      gananciaTotal = { min: 11.5, max: 16 };
    } else if (imc_pregestacional < 30) {
      // Sobrepeso: 7-11.5 kg
      gananciaTotal = { min: 7, max: 11.5 };
    } else {
      // Obesidad: 5-9 kg
      gananciaTotal = { min: 5, max: 9 };
    }

    // Proporcional a las semanas (40 semanas total)
    const proporcion = semanas / 40;

    return {
      min: gananciaTotal.min * proporcion,
      max: gananciaTotal.max * proporcion
    };
  },

  /**
   * Estima peso fetal por altura uterina
   */
  estimarPesoFetal(alturaUterina_cm: number): number {
    // Fórmula simplificada: Peso (g) = (AU - 12) * 155
    return (alturaUterina_cm - 12) * 155;
  },

  /**
   * Obtener curva de crecimiento
   */
  async obtenerCurvaCrecimiento(embarazoId: number): Promise<CurvaCrecimiento[]> {
    try {
      const response = await api.get<CurvaCrecimiento[]>(
        `/controles/curva-crecimiento/`,
        { params: { embarazo: embarazoId } }
      );
      return normalizeListResponse<CurvaCrecimiento>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo curva de crecimiento:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ESTADÍSTICAS Y REPORTES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtener estadísticas de controles
   */
  async obtenerEstadisticas(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    medico?: number;
  }): Promise<EstadisticasControles> {
    try {
      const response = await api.get<EstadisticasControles>(
        '/controles/estadisticas/',
        { params }
      );
      return response.data;
    } catch (error: any) {
      console.error('❌ Error obteniendo estadísticas:', error);
      throw error;
    }
  },

  /**
   * Generar reporte PDF de control
   */
  async generarReportePDF(controlId: number): Promise<Blob> {
    try {
      const response = await api.get(`/controles/${controlId}/generar-pdf/`, {
        responseType: 'blob'
      });
      console.log(`✅ PDF del control ${controlId} generado`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error generando PDF:`, error);
      throw error;
    }
  },

  /**
   * Exportar controles a Excel
   */
  async exportarExcel(filtros?: any): Promise<Blob> {
    try {
      const response = await api.get('/controles/exportar-excel/', {
        params: filtros,
        responseType: 'blob'
      });
      console.log('✅ Excel exportado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error exportando Excel:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // VALIDACIONES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Valida datos del control
   */
  validarDatosControl(data: Partial<ControlPrenatal>): {
    valido: boolean;
    errores: string[];
    advertencias: string[];
  } {
    const errores: string[] = [];
    const advertencias: string[] = [];

    if (!data.embarazo) {
      errores.push('Debe especificar el embarazo');
    }

    if (!data.fecha_control) {
      errores.push('Debe especificar la fecha del control');
    }

    if (!data.peso_actual || data.peso_actual <= 0) {
      errores.push('El peso debe ser mayor a 0');
    }

    if (data.presion_sistolica && data.presion_diastolica) {
      if (data.presion_sistolica >= 140 || data.presion_diastolica >= 90) {
        advertencias.push('Presión arterial elevada - posible hipertensión');
      }
      if (data.presion_sistolica < 90 || data.presion_diastolica < 60) {
        advertencias.push('Presión arterial baja - hipotensión');
      }
    }

    if (data.frecuencia_cardiaca_fetal) {
      if (data.frecuencia_cardiaca_fetal < 110 || data.frecuencia_cardiaca_fetal > 160) {
        advertencias.push('Frecuencia cardíaca fetal fuera del rango normal (110-160 lpm)');
      }
    }

    if (data.temperatura && data.temperatura >= 37.5) {
      advertencias.push('Temperatura elevada - posible infección');
    }

    return {
      valido: errores.length === 0,
      errores,
      advertencias
    };
  },

  /**
   * Valida presión arterial
   */
  validarPresionArterial(sistolica: number, diastolica: number): {
    normal: boolean;
    categoria: string;
    requiere_atencion: boolean;
  } {
    if (sistolica < 90 || diastolica < 60) {
      return {
        normal: false,
        categoria: 'Hipotensión',
        requiere_atencion: true
      };
    }

    if (sistolica >= 160 || diastolica >= 110) {
      return {
        normal: false,
        categoria: 'Hipertensión severa',
        requiere_atencion: true
      };
    }

    if (sistolica >= 140 || diastolica >= 90) {
      return {
        normal: false,
        categoria: 'Hipertensión leve/moderada',
        requiere_atencion: true
      };
    }

    return {
      normal: true,
      categoria: 'Normal',
      requiere_atencion: false
    };
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTACIONES
// ═══════════════════════════════════════════════════════════════════════════

