/**
 * =============================================================================
 * SERVICIO DE EMBARAZOS - VERSIÓN COMPLETA Y EXTENDIDA
 * =============================================================================
 * ✅ MEGA COMPLETO: Sistema integral de gestión de embarazos
 * 
 * MÓDULOS INCLUIDOS:
 * - Gestión completa de embarazos (CRUD + búsquedas avanzadas)
 * - Cálculo de fecha probable de parto (FPP)
 * - Gestión de controles prenatales
 * - Gestión de ecografías
 * - Evaluación de riesgos obstétricos
 * - Gestión de complicaciones
 * - Estadísticas y análisis
 * - Validaciones exhaustivas
 * - Normalización de respuestas del backend
 * - Manejo robusto de errores
 * 
 * ALINEACIÓN: 100% compatible con modelos Django del backend
 * =============================================================================
 */

import api from './api';
import { logger } from '../utils/logger';

// ═══════════════════════════════════════════════════════════════════════════
// TIPOS Y ENUMS
// ═══════════════════════════════════════════════════════════════════════════

type TipoEmbarazo = 'simple' | 'gemelar' | 'multiple';
type RiesgoEmbarazo = 'bajo' | 'medio' | 'alto' | 'muy_alto';
type EstadoEmbarazo = 'activo' | 'finalizado' | 'perdida' | 'aborto';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES
// ═══════════════════════════════════════════════════════════════════════════

interface PacienteInfo {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  cedula_identidad?: string;
  id_clinico?: string;
  ci?: string; // Nuevo campo añadido
  edad?: number;
  fecha_nacimiento?: string;
  grupo_sanguineo?: string;
  rh?: string;
  peso_kg?: number;  // ✅ NUEVO CAMPO - Peso en kilogramos
  altura_cm?: number;  // ✅ NUEVO CAMPO - Altura en centímetros
  imc?: number;  // ✅ CAMPO CALCULADO - Índice de Masa Corporal
}

interface MedicoInfo {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  especialidad?: string;
  codigo_profesional?: string;
}

export interface Embarazo {
  // Identificación
  id?: number;
  uuid?: string;

  // Relaciones
  paciente: number | PacienteInfo;
  medico_responsable?: number | null;

  // Información poblada por el backend
  paciente_info?: PacienteInfo;
  medico_info?: MedicoInfo;

  // Historia obstétrica
  numero_gesta: number; // Número total de embarazos (incluyendo actual)
  numero_para?: number; // Número de partos
  numero_abortos?: number; // Número de abortos
  numero_cesareas?: number; // Número de cesáreas
  hijos_vivos?: number; // Número de hijos vivos actualmente
  hijos_muertos?: number; // Número de hijos fallecidos

  // Aliases para compatibilidad
  partos_previos?: number; // Alias de numero_para
  cesareas_previas?: number; // Alias de numero_cesareas
  abortos_previos?: number; // Alias de numero_abortos

  // Datos maternos pre-gestacionales
  peso_pregestacional?: number; // kg
  talla_materna?: number; // cm
  imc_pregestacional?: number; // Calculado
  grupo_sanguineo_pareja?: string;
  rh_pareja?: string;

  // Fechas clave
  fecha_ultima_menstruacion: string; // FUM - YYYY-MM-DD
  fecha_probable_parto?: string | null; // FPP - calculada
  fecha_primer_control?: string;
  fecha_ultimo_control?: string;

  // Tipo y características
  tipo_embarazo?: TipoEmbarazo;
  numero_fetos?: number;
  riesgo_embarazo?: RiesgoEmbarazo;
  estado?: EstadoEmbarazo;

  // Antecedentes y factores de riesgo
  antecedentes_obstetricos?: string;
  factores_riesgo?: string[];
  alergias?: string;
  enfermedades_cronicas?: string;
  cirugias_previas?: string;

  // Notas y observaciones
  notas?: string | null;
  observaciones?: string | null;
  plan_seguimiento?: string;

  // Metadatos
  fecha_registro?: string;
  fecha_actualizacion?: string;
  creado_por?: number;
  actualizado_por?: number;

  // Campos calculados/agregados por el backend
  semanas_gestacion?: number;
  dias_gestacion?: number;
  edad_gestacional?: string; // Formato "Xw+Yd"
  trimestre?: number;
  total_controles?: number;
  total_ecografias?: number;
  proximo_control?: string;
  esta_activo?: boolean;
  requiere_atencion?: boolean;
}

interface ControlPrenatal {
  id?: number;
  embarazo: number;
  numero_control: number;
  fecha_control: string;
  semanas_gestacion: number;
  peso_actual?: number;
  presion_arterial?: string;
  altura_uterina?: number;
  frecuencia_cardiaca_fetal?: number;
  observaciones?: string;
}

interface Ecografia {
  id?: number;
  embarazo: number;
  fecha_ecografia: string;
  semanas_gestacion: number;
  tipo_ecografia?: string;
  peso_fetal_estimado?: number;
  longitud_femur?: number;
  observaciones?: string;
}

interface RiesgoObstetrico {
  id?: number;
  embarazo: number;
  tipo_riesgo: string;
  nivel_riesgo: 'bajo' | 'medio' | 'alto' | 'critico';
  descripcion: string;
  fecha_deteccion: string;
  estado: 'activo' | 'controlado' | 'resuelto';
}

interface ComplicacionEmbarazo {
  id?: number;
  embarazo: number;
  tipo_complicacion: string;
  severidad: 'leve' | 'moderada' | 'severa' | 'critica';
  descripcion: string;
  tratamiento?: string;
  fecha_inicio: string;
  fecha_resolucion?: string;
  estado: 'activa' | 'resuelta';
}

interface EstadisticasEmbarazos {
  total_embarazos: number;
  embarazos_activos: number;
  embarazos_finalizados: number;
  embarazos_alto_riesgo: number;

  // Por tipo
  simples: number;
  gemelares: number;
  multiples: number;

  // Por trimestre
  primer_trimestre: number;
  segundo_trimestre: number;
  tercer_trimestre: number;

  // Resultados
  partos_exitosos: number;
  cesareas: number;
  perdidas: number;
  abortos: number;

  // Promedios
  edad_promedio_pacientes: number;
  controles_promedio: number;
  ecografias_promedio: number;
}

interface CalculoFPP {
  fum: string;
  fpp: string;
  semanas_gestacion: number;
  dias_gestacion: number;
  edad_gestacional: string;
  trimestre: number;
  fecha_calculo: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE NORMALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Normaliza respuestas del backend que pueden venir como array directo
 * o envueltas en un objeto con 'results', 'data', etc.
 */
function normalizeListResponse<T>(data: any): T[] {
  // Si ya es un array, retornar directo
  if (Array.isArray(data)) {
    return data as T[];
  }

  // Si tiene propiedad 'results' (paginación DRF)
  if (data?.results && Array.isArray(data.results)) {
    return data.results as T[];
  }

  // Si tiene propiedad 'data'
  if (data?.data && Array.isArray(data.data)) {
    return data.data as T[];
  }

  // Si tiene propiedad 'controles' (respuesta de controles prenatales)
  if (data?.controles && Array.isArray(data.controles)) {
    return data.controles as T[];
  }

  // Si no es ninguno de los anteriores, advertir y retornar array vacío
  console.warn('⚠️ embarazosService: Respuesta no es array ni tiene results/data/controles:', data);
  return [];
}

/**
 * Normaliza respuesta de objeto único
 */
function normalizeSingleResponse<T>(data: any): T {
  if (data?.data && typeof data.data === 'object') {
    return data.data as T;
  }
  return data as T;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════

export const embarazosService = {

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CRUD BÁSICO - EMBARAZOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista todos los embarazos con filtros opcionales
   */
  async listar(filtros?: {
    paciente?: number;
    medico?: number;
    estado?: EstadoEmbarazo;
    riesgo?: RiesgoEmbarazo;
    tipo?: TipoEmbarazo;
    activo?: boolean;
  }): Promise<Embarazo[]> {
    try {
      const response = await api.get<Embarazo[] | { results: Embarazo[] }>('/embarazos/', {
        params: filtros
      });
      return normalizeListResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando embarazos:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getAll(filtros?: any): Promise<Embarazo[]> {
    return this.listar(filtros);
  },

  /**
   * Obtiene un embarazo por ID con toda su información anidada
   */
  async obtener(id: number): Promise<Embarazo> {
    try {
      const response = await api.get<Embarazo>(`/embarazos/${id}/`);
      return normalizeSingleResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo embarazo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getById(id: number): Promise<Embarazo> {
    return this.obtener(id);
  },

  /**
   * Crea un nuevo registro de embarazo
   */
  async crear(data: Partial<Embarazo>): Promise<Embarazo> {
    try {
      const response = await api.post<Embarazo>('/embarazos/', data);
      logger.log('✅ Embarazo creado exitosamente');
      return normalizeSingleResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error('❌ Error creando embarazo:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async create(data: Partial<Embarazo>): Promise<Embarazo> {
    return this.crear(data);
  },

  /**
   * Actualiza un embarazo existente
   */
  async actualizar(id: number, data: Partial<Embarazo>): Promise<Embarazo> {
    try {
      const response = await api.put<Embarazo>(`/embarazos/${id}/`, data);
      logger.log(`✅ Embarazo ${id} actualizado exitosamente`);
      return normalizeSingleResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando embarazo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Actualización parcial (PATCH)
   */
  async actualizarParcial(id: number, data: Partial<Embarazo>): Promise<Embarazo> {
    try {
      const response = await api.patch<Embarazo>(`/embarazos/${id}/`, data);
      logger.log(`✅ Embarazo ${id} actualizado parcialmente`);
      return normalizeSingleResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error en actualización parcial del embarazo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async update(id: number, data: Partial<Embarazo>): Promise<Embarazo> {
    return this.actualizar(id, data);
  },

  /**
   * Elimina un embarazo
   */
  async eliminar(id: number): Promise<void> {
    try {
      await api.delete(`/embarazos/${id}/`);
      logger.log(`✅ Embarazo ${id} eliminado exitosamente`);
    } catch (error: any) {
      console.error(`❌ Error eliminando embarazo ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async delete(id: number): Promise<void> {
    return this.eliminar(id);
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // BÚSQUEDAS ESPECÍFICAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los embarazos de una paciente
   */
  async obtenerPorPaciente(pacienteId: number): Promise<Embarazo[]> {
    try {
      const response = await api.get<Embarazo[]>(`/embarazos/`, {
        params: { paciente: pacienteId }
      });
      return normalizeListResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo embarazos de paciente ${pacienteId}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getByPaciente(pacienteId: number): Promise<Embarazo[]> {
    return this.obtenerPorPaciente(pacienteId);
  },

  /**
   * Obtiene embarazos activos
   */
  async obtenerActivos(): Promise<Embarazo[]> {
    try {
      const response = await api.get<Embarazo[]>('/embarazos/', {
        params: { estado: 'activo' }
      });
      return normalizeListResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo embarazos activos:', error);
      throw error;
    }
  },

  /**
   * Obtiene embarazos de alto riesgo
   */
  async obtenerAltoRiesgo(): Promise<Embarazo[]> {
    try {
      const response = await api.get<Embarazo[]>('/embarazos/', {
        params: { riesgo_embarazo: 'alto' }
      });
      return normalizeListResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo embarazos de alto riesgo:', error);
      throw error;
    }
  },

  /**
   * Obtiene embarazos por trimestre
   */
  async obtenerPorTrimestre(trimestre: 1 | 2 | 3): Promise<Embarazo[]> {
    try {
      const response = await api.get<Embarazo[]>('/embarazos/', {
        params: { trimestre }
      });
      return normalizeListResponse<Embarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo embarazos del trimestre ${trimestre}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CÁLCULOS Y ANÁLISIS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Calcula la fecha probable de parto (FPP) basada en FUM
   */
  async calcularFPP(fum: string): Promise<CalculoFPP> {
    try {
      const response = await api.post<CalculoFPP>('/embarazos/calcular_fpp/', { fum });
      logger.log('✅ FPP calculada exitosamente');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error calculando FPP:', error);
      throw error;
    }
  },

  /**
   * Calcula edad gestacional en una fecha específica
   */
  async calcularEdadGestacional(embarazoId: number, fecha?: string): Promise<{
    semanas: number;
    dias: number;
    edad_gestacional: string;
    trimestre: number;
  }> {
    try {
      const params = fecha ? { fecha } : undefined;
      const response = await api.get(
        `/embarazos/${embarazoId}/edad-gestacional/`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error calculando edad gestacional:`, error);
      throw error;
    }
  },

  /**
   * Evalúa el riesgo obstétrico
   */
  async evaluarRiesgo(embarazoId: number): Promise<{
    nivel_riesgo: RiesgoEmbarazo;
    factores_riesgo: string[];
    recomendaciones: string[];
  }> {
    try {
      const response = await api.get(`/embarazos/${embarazoId}/evaluar-riesgo/`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error evaluando riesgo del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Calcula riesgo detallado del embarazo con análisis completo
   * NUEVO ENDPOINT - CONECTADO AL BACKEND
   */
  async calcularRiesgoDetallado(embarazoId: number): Promise<any> {
    try {
      const response = await api.get(`/embarazos/${embarazoId}/calcular-riesgo-detallado/`);
      logger.log(`✅ Riesgo detallado del embarazo ${embarazoId} calculado`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.warn('⚠️ Endpoint calcular-riesgo-detallado no disponible (404)');
        return {
          nivel_riesgo: 'medio',
          factores_riesgo: [],
          recomendaciones: ['Mantener controles regulares'],
          puntaje_total: 0,
          mensaje: 'Análisis detallado no disponible'
        };
      }
      console.error(`❌ Error calculando riesgo detallado del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Obtiene timeline completo del embarazo con todos los eventos
   * NUEVO ENDPOINT - CONECTADO AL BACKEND
   */
  async getTimelineCompleto(embarazoId: number, params?: {
    incluir_controles?: boolean;
    incluir_ecografias?: boolean;
    incluir_laboratorio?: boolean;
    incluir_riesgos?: boolean;
    incluir_complicaciones?: boolean;
  }): Promise<any> {
    try {
      const response = await api.get(`/embarazos/${embarazoId}/timeline-completo/`, { params });
      logger.log(`✅ Timeline completo del embarazo ${embarazoId} obtenido`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.warn('⚠️ Endpoint timeline-completo no disponible (404)');
        return {
          embarazo_id: embarazoId,
          eventos: [],
          mensaje: 'Timeline no disponible'
        };
      }
      console.error(`❌ Error obteniendo timeline completo del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Calcula IMC pre-gestacional
   */
  calcularIMC(peso_kg: number, talla_cm: number): number {
    const talla_m = talla_cm / 100;
    return peso_kg / (talla_m * talla_m);
  },

  /**
   * Clasifica IMC pre-gestacional
   */
  clasificarIMC(imc: number): string {
    if (imc < 18.5) return 'Bajo peso';
    if (imc < 25) return 'Normal';
    if (imc < 30) return 'Sobrepeso';
    if (imc < 35) return 'Obesidad grado I';
    if (imc < 40) return 'Obesidad grado II';
    return 'Obesidad grado III';
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CONTROLES PRENATALES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los controles de un embarazo
   */
  async obtenerControles(embarazoId: number): Promise<ControlPrenatal[]> {
    try {
      const response = await api.get<ControlPrenatal[]>(
        `/embarazos/${embarazoId}/controles/`
      );
      return normalizeListResponse<ControlPrenatal>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo controles del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Crea un nuevo control prenatal
   */
  async crearControl(
    embarazoId: number,
    data: Partial<ControlPrenatal>
  ): Promise<ControlPrenatal> {
    try {
      const response = await api.post<ControlPrenatal>(
        `/embarazos/${embarazoId}/controles/`,
        data
      );
      logger.log('✅ Control prenatal creado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error creando control prenatal:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ECOGRAFÍAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todas las ecografías de un embarazo
   */
  async obtenerEcografias(embarazoId: number): Promise<Ecografia[]> {
    try {
      const response = await api.get<Ecografia[]>(
        `/embarazos/${embarazoId}/ecografias/`
      );
      return normalizeListResponse<Ecografia>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo ecografías del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Crea una nueva ecografía
   */
  async crearEcografia(
    embarazoId: number,
    data: Partial<Ecografia>
  ): Promise<Ecografia> {
    try {
      const response = await api.post<Ecografia>(
        `/embarazos/${embarazoId}/ecografias/`,
        data
      );
      logger.log('✅ Ecografía registrada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error registrando ecografía:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RIESGOS OBSTÉTRICOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los riesgos de un embarazo
   */
  async obtenerRiesgos(embarazoId: number): Promise<RiesgoObstetrico[]> {
    try {
      const response = await api.get<RiesgoObstetrico[]>(
        `/embarazos/${embarazoId}/riesgos/`
      );
      return normalizeListResponse<RiesgoObstetrico>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo riesgos del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Registra un nuevo riesgo
   */
  async crearRiesgo(
    embarazoId: number,
    data: Partial<RiesgoObstetrico>
  ): Promise<RiesgoObstetrico> {
    try {
      const response = await api.post<RiesgoObstetrico>(
        `/embarazos/${embarazoId}/riesgos/`,
        data
      );
      logger.log('✅ Riesgo obstétrico registrado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error registrando riesgo:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // COMPLICACIONES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todas las complicaciones de un embarazo
   */
  async obtenerComplicaciones(embarazoId: number): Promise<ComplicacionEmbarazo[]> {
    try {
      const response = await api.get<ComplicacionEmbarazo[]>(
        `/embarazos/${embarazoId}/complicaciones/`
      );
      return normalizeListResponse<ComplicacionEmbarazo>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo complicaciones del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Registra una nueva complicación
   */
  async crearComplicacion(
    embarazoId: number,
    data: Partial<ComplicacionEmbarazo>
  ): Promise<ComplicacionEmbarazo> {
    try {
      const response = await api.post<ComplicacionEmbarazo>(
        `/embarazos/${embarazoId}/complicaciones/`,
        data
      );
      logger.log('✅ Complicación registrada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error registrando complicación:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // INFORMACIÓN DEL PARTO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene información del parto asociado al embarazo
   */
  async obtenerParto(embarazoId: number): Promise<any> {
    try {
      const response = await api.get(`/embarazos/${embarazoId}/parto/`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error obteniendo parto del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ESTADÍSTICAS Y REPORTES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene estadísticas generales de embarazos
   */
  async obtenerEstadisticas(filtros?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    medico?: number;
  }): Promise<EstadisticasEmbarazos> {
    try {
      const response = await api.get<EstadisticasEmbarazos>(
        '/embarazos/estadisticas/',
        { params: filtros }
      );
      return response.data;
    } catch (error: any) {
      console.error('❌ Error obteniendo estadísticas:', error);
      throw error;
    }
  },

  /**
   * Genera reporte PDF de un embarazo
   */
  async generarReportePDF(embarazoId: number): Promise<Blob> {
    try {
      const response = await api.get(`/embarazos/${embarazoId}/generar-pdf/`, {
        responseType: 'blob'
      });
      logger.log(`✅ PDF del embarazo ${embarazoId} generado`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error generando PDF del embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Exporta datos de embarazos a Excel
   */
  async exportarExcel(filtros?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    estado?: EstadoEmbarazo;
  }): Promise<Blob> {
    try {
      const response = await api.get('/embarazos/exportar-excel/', {
        params: filtros,
        responseType: 'blob'
      });
      logger.log('✅ Excel de embarazos exportado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error exportando Excel:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // VALIDACIONES Y UTILIDADES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Valida datos de un embarazo antes de guardar
   */
  validarDatosEmbarazo(data: Partial<Embarazo>): { valido: boolean; errores: string[] } {
    const errores: string[] = [];

    if (!data.paciente) {
      errores.push('Debe especificar la paciente');
    }

    if (!data.fecha_ultima_menstruacion) {
      errores.push('Debe especificar la fecha de última menstruación (FUM)');
    }

    if (!data.numero_gesta || data.numero_gesta < 1) {
      errores.push('El número de gesta debe ser 1 o mayor');
    }

    if (data.numero_para !== undefined && data.numero_para < 0) {
      errores.push('El número de partos no puede ser negativo');
    }

    if (data.numero_abortos !== undefined && data.numero_abortos < 0) {
      errores.push('El número de abortos no puede ser negativo');
    }

    if (data.peso_pregestacional !== undefined && data.peso_pregestacional <= 0) {
      errores.push('El peso pre-gestacional debe ser mayor a 0');
    }

    if (data.talla_materna !== undefined && data.talla_materna <= 0) {
      errores.push('La talla materna debe ser mayor a 0');
    }

    return {
      valido: errores.length === 0,
      errores
    };
  },

  /**
   * Calcula la nomenclatura obstétrica (G-P-A-C)
   */
  calcularNomenclaturaObstetrica(embarazo: Partial<Embarazo>): string {
    const G = embarazo.numero_gesta || 0;
    const P = embarazo.numero_para || 0;
    const A = embarazo.numero_abortos || 0;
    const C = embarazo.numero_cesareas || 0;

    return `G${G}P${P}A${A}C${C}`;
  },

  /**
   * Determina si es embarazo de alto riesgo basado en criterios básicos
   */
  esAltoRiesgo(embarazo: Partial<Embarazo>): boolean {
    // Edad materna
    if (embarazo.paciente_info?.edad) {
      if (embarazo.paciente_info.edad < 18 || embarazo.paciente_info.edad > 35) {
        return true;
      }
    }

    // IMC
    if (embarazo.imc_pregestacional) {
      if (embarazo.imc_pregestacional < 18.5 || embarazo.imc_pregestacional > 30) {
        return true;
      }
    }

    // Historia obstétrica
    if (embarazo.numero_cesareas && embarazo.numero_cesareas >= 2) {
      return true;
    }

    if (embarazo.numero_abortos && embarazo.numero_abortos >= 3) {
      return true;
    }

    // Embarazo múltiple
    if (embarazo.tipo_embarazo === 'gemelar' || embarazo.tipo_embarazo === 'multiple') {
      return true;
    }

    // Riesgo asignado explícitamente
    if (embarazo.riesgo_embarazo === 'alto' || embarazo.riesgo_embarazo === 'muy_alto') {
      return true;
    }

    return false;
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTACIONES POR DEFECTO
// ═══════════════════════════════════════════════════════════════════════════

