/**
 * =============================================================================
 * SERVICIO DE REPORTES Y ESTADÍSTICAS - VERSIÓN MEGA COMPLETA Y EXTENDIDA
 * =============================================================================
 * ✅ MEGA COMPLETO: Sistema integral de reportes, estadísticas y análisis
 * 
 * MÓDULOS INCLUIDOS:
 * - Reportes de pacientes (completos, embarazos, historiales)
 * - Reportes de partos (estadísticas, tendencias, complicaciones)
 * - Reportes de controles prenatales
 * - Reportes de laboratorio (exámenes, resultados)
 * - Reportes de citas (agendamiento, asistencia, cancelaciones)
 * - Reportes financieros y administrativos
 * - Estadísticas generales del sistema
 * - Análisis de tendencias y patrones
 * - Exportación a múltiples formatos (PDF, Excel, CSV)
 * - Dashboards y KPIs
 * - Normalización de respuestas del backend
 * - Manejo robusto de errores
 * 
 * ALINEACIÓN: 100% compatible con backend Django
 * =============================================================================
 */

import api from './api';
import { logger } from '../utils/logger';

// ═══════════════════════════════════════════════════════════════════════════
// TIPOS Y ENUMS
// ═══════════════════════════════════════════════════════════════════════════

type TipoReporte =
  | 'pacientes'
  | 'embarazos'
  | 'partos'
  | 'controles'
  | 'ecografias'
  | 'laboratorio'
  | 'citas'
  | 'financiero'
  | 'administrativa';

type FormatoExportacion = 'pdf' | 'excel' | 'csv' | 'json';

// El backend usa el código interno "pd" (no "pdf") para PDF en
// ReporteGenerado.FORMATO_CHOICES y TipoReporte.get_formatos_disponibles().
export const formatoAlBackend = (formato: string): string => (formato === 'pdf' ? 'pd' : formato);
export const formatoDelBackend = (formato: string): string => (formato === 'pd' ? 'pdf' : formato);

export interface TipoReporteConfig {
  id: number;
  nombre: string;
  codigo: string;
  descripcion?: string;
  categoria: 'estadistico' | 'paciente' | 'institucional' | 'regulatorio' | 'clinico' | 'financiero';
  categoria_display?: string;
  frecuencia?: string;
  frecuencia_display?: string;
  automatico?: boolean;
  confidencial?: boolean;
  activo: boolean;
  incluir_fecha_inicio?: boolean;
  incluir_fecha_fin?: boolean;
  incluir_paciente?: boolean;
  incluir_medico?: boolean;
  incluir_servicio?: boolean;
  formato_pdf?: boolean;
  formato_excel?: boolean;
  formato_csv?: boolean;
  formato_json?: boolean;
}

type PeriodoReporte = 'dia' | 'semana' | 'mes' | 'trimestre' | 'semestre' | 'anio' | 'personalizado';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - ESTADÍSTICAS GENERALES
// ═══════════════════════════════════════════════════════════════════════════

interface EstadisticasGenerales {
  // Pacientes
  total_pacientes: number;
  pacientes_activos: number;
  pacientes_nuevos_mes: number;
  promedio_edad_pacientes: number;

  // Embarazos
  total_embarazos: number;
  embarazos_activos: number;
  embarazos_alto_riesgo: number;
  embarazos_finalizados_mes: number;

  // Partos
  total_partos: number;
  partos_mes: number;
  partos_vaginales: number;
  cesareas: number;
  tasa_cesareas: number;

  // Controles
  total_controles: number;
  controles_mes: number;
  promedio_controles_embarazo: number;

  // Citas
  total_citas: number;
  citas_hoy: number;
  citas_pendientes: number;
  tasa_asistencia: number;

  // Laboratorio
  total_examenes: number;
  examenes_pendientes: number;
  examenes_completados_mes: number;

  // Periodo de análisis
  fecha_inicio: string;
  fecha_fin: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES DE PACIENTES
// ═══════════════════════════════════════════════════════════════════════════

interface ReportePacientes {
  total: number;
  pacientes: Array<{
    id: number;
    nombre_completo: string;
    id_clinico: string;
    edad: number;
    grupo_sanguineo?: string;
    embarazos_totales: number;
    embarazo_activo: boolean;
    ultimo_control?: string;
    proxima_cita?: string;
  }>;
  distribucion_edad: {
    menores_18: number;
    entre_18_35: number;
    mayores_35: number;
  };
  distribucion_grupo_sanguineo: Record<string, number>;
}

interface ReporteEmbarazos {
  total: number;
  activos: number;
  finalizados: number;
  por_trimestre: {
    primer_trimestre: number;
    segundo_trimestre: number;
    tercer_trimestre: number;
  };
  por_riesgo: {
    bajo: number;
    medio: number;
    alto: number;
    muy_alto: number;
  };
  por_tipo: {
    simple: number;
    gemelar: number;
    multiple: number;
  };
  complicaciones: number;
  promedio_controles: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES DE PARTOS
// ═══════════════════════════════════════════════════════════════════════════

interface ReportePartos {
  total_partos: number;
  periodo: {
    inicio: string;
    fin: string;
  };

  // Por tipo de parto
  por_tipo: {
    vaginal_espontaneo: number;
    vaginal_instrumentado: number;
    cesarea_electiva: number;
    cesarea_urgencia: number;
    cesarea_emergencia: number;
  };

  // Tasas importantes
  tasa_cesareas: number;
  tasa_partos_vaginales: number;
  tasa_complicaciones: number;

  // Resultados neonatales
  recien_nacidos: {
    total: number;
    vivos: number;
    mortinatos: number;
    muertes_neonatales: number;
    apgar_promedio_1min: number;
    apgar_promedio_5min: number;
    peso_promedio: number;
  };

  // Complicaciones
  complicaciones_maternas: number;
  complicaciones_fetales: number;
  complicaciones_neonatales: number;

  // Distribución por edad gestacional
  por_edad_gestacional: {
    pretermino: number;  // < 37 semanas
    termino: number;     // 37-42 semanas
    postermino: number;  // > 42 semanas
  };

  // Tendencias mensuales
  tendencia_mensual?: Array<{
    mes: string;
    total: number;
    cesareas: number;
    vaginales: number;
  }>;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES DE CONTROLES
// ═══════════════════════════════════════════════════════════════════════════

interface ReporteControles {
  total_controles: number;
  periodo: {
    inicio: string;
    fin: string;
  };

  // Distribución
  por_trimestre: {
    primer_trimestre: number;
    segundo_trimestre: number;
    tercer_trimestre: number;
  };

  // Promedios
  promedio_por_embarazo: number;
  intervalo_promedio_dias: number;

  // Parámetros clínicos
  promedios_clinicos: {
    peso_promedio: number;
    presion_arterial_promedio: string;
    altura_uterina_promedio: number;
    frecuencia_cardiaca_fetal_promedio: number;
  };

  // Alertas y hallazgos
  controles_con_alertas: number;
  embarazos_riesgo_detectado: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES DE LABORATORIO
// ═══════════════════════════════════════════════════════════════════════════

interface ReporteLaboratorio {
  total_examenes: number;
  periodo: {
    inicio: string;
    fin: string;
  };

  // Por estado
  por_estado: {
    solicitados: number;
    en_proceso: number;
    completados: number;
    cancelados: number;
  };

  // Por categoría
  por_categoria: Record<string, number>;

  // Por prioridad
  por_prioridad: {
    normal: number;
    urgente: number;
    stat: number;
  };

  // Resultados
  resultados: {
    normales: number;
    anormales: number;
    criticos: number;
    porcentaje_normalidad: number;
  };

  // Tiempos
  tiempo_promedio_resultados_horas: number;
  examenes_pendientes_mas_48h: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES DE CITAS
// ═══════════════════════════════════════════════════════════════════════════

interface ReporteCitas {
  total_citas: number;
  periodo: {
    inicio: string;
    fin: string;
  };

  // Por estado
  por_estado: {
    agendadas: number;
    confirmadas: number;
    en_espera: number;
    completadas: number;
    canceladas: number;
    no_asistio: number;
  };

  // Por tipo
  por_tipo: {
    primera_vez: number;
    control: number;
    urgencia: number;
    seguimiento: number;
  };

  // Métricas de calidad
  tasa_asistencia: number;
  tasa_cancelacion: number;
  tasa_no_asistencia: number;

  // Distribución por médico
  por_medico: Array<{
    medico_id: number;
    medico_nombre: string;
    total_citas: number;
    completadas: number;
    canceladas: number;
  }>;

  // Disponibilidad
  horas_disponibles: number;
  horas_ocupadas: number;
  tasa_ocupacion: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - REPORTES Y ALERTAS
// ═══════════════════════════════════════════════════════════════════════════

export interface Reporte {
  id: number;
  tipo_reporte: number;
  tipo_reporte_nombre?: string;
  formato: FormatoExportacion;
  estado: 'pendiente' | 'procesando' | 'completado' | 'error' | 'expirado';
  estado_display?: string;
  fecha_solicitud: string;
  fecha_completado?: string;
  usuario_solicitante?: number;
  parametros?: Record<string, any>;
  ruta_archivo?: string;
  total_registros?: number;
  mensaje_error?: string;
}

export interface AlertaMedica {
  id: number;
  titulo: string;
  descripcion?: string;
  tipo: string;
  tipo_display?: string;
  prioridad: 'baja' | 'media' | 'alta' | 'critica' | 'emergencia';
  prioridad_display?: string;
  estado: 'activa' | 'revisada' | 'resuelta' | 'descartada' | 'escalada';
  estado_display?: string;
  paciente_id?: number;
  paciente_nombre?: string | null;
  embarazo_id?: number;
  medico_responsable_id?: number;
  modulo_origen: string;
  modulo_origen_display?: string;
  registro_origen_id?: number;
  valor_actual?: string;
  valor_umbral?: string;
  accion_recomendada?: string;
  protocolo_seguimiento?: string;
  fecha_creacion: string;
  fecha_vencimiento?: string;
  fecha_revision?: string;
  fecha_resolucion?: string;
  usuario_revision_id?: number;
  usuario_resolucion_id?: number;
  comentario_revision?: string;
  comentario_resolucion?: string;
  color_prioridad?: string;
  es_vencida?: boolean;
  tiempo_transcurrido?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - DASHBOARDS Y KPIs
// ═══════════════════════════════════════════════════════════════════════════

export interface DashboardKPIs {
  fecha_actualizacion: string;

  // KPIs principales
  kpis: {
    pacientes_activos: {
      valor: number;
      variacion_mes: number; // porcentaje
      tendencia: 'up' | 'down' | 'stable';
    };
    embarazos_activos: {
      valor: number;
      variacion_mes: number;
      tendencia: 'up' | 'down' | 'stable';
    };
    citas_dia: {
      valor: number;
      completadas: number;
      pendientes: number;
    };
    tasa_ocupacion: {
      valor: number; // porcentaje
      variacion_semana: number;
    };
  };

  // Gráficos de tendencias
  tendencias: {
    partos_ultimo_anio: Array<{
      mes: string;
      total: number;
      cesareas: number;
      vaginales: number;
    }>;
    controles_ultimo_trimestre: Array<{
      semana: string;
      total: number;
    }>;
    citas_ultima_semana: Array<{
      dia: string;
      total: number;
      completadas: number;
      canceladas: number;
    }>;
  };

  // Alertas y notificaciones
  alertas: {
    embarazos_alto_riesgo: number;
    examenes_pendientes: number;
    citas_sin_confirmar: number;
    controles_atrasados: number;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE NORMALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Normaliza respuestas del backend que pueden venir como array directo
 * o envueltas en un objeto con 'results', 'data', etc.
 */
export function normalizeListResponse<T>(data: any): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (data?.results && Array.isArray(data.results)) {
    return data.results as T[];
  }

  if (data?.data && Array.isArray(data.data)) {
    return data.data as T[];
  }

  console.warn('⚠️ reportesService: Respuesta no es array ni tiene results/data:', data);
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

export const reportesService = {

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ESTADÍSTICAS GENERALES DEL SISTEMA
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene estadísticas generales del sistema
   */
  async obtenerEstadisticasGenerales(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<EstadisticasGenerales> {
    try {
      const response = await api.get<EstadisticasGenerales>(
        '/reportes/estadisticas-generales/',
        { params }
      );
      return normalizeSingleResponse<EstadisticasGenerales>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo estadísticas generales:', error);
      throw error;
    }
  },

  /**
   * Obtiene KPIs principales para el dashboard
   */
  async obtenerDashboardKPIs(): Promise<DashboardKPIs> {
    try {
      const response = await api.get<DashboardKPIs>('/reportes/dashboard-kpis/');
      return normalizeSingleResponse<DashboardKPIs>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo KPIs del dashboard:', error);
      throw error;
    }
  },

  /**
   * Obtiene estadísticas básicas para el dashboard (accesible a todos)
   */
  async obtenerStatsBasicas(): Promise<any> {
    try {
      const response = await api.get('/reportes/dashboard/');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error obteniendo stats básicas:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getDashboardKPIs(): Promise<DashboardKPIs> {
    return this.obtenerDashboardKPIs();
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE PACIENTES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte general de pacientes
   */
  async generarReportePacientes(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    activos?: boolean;
    grupo_sanguineo?: string;
  }): Promise<ReportePacientes> {
    try {
      const response = await api.get<ReportePacientes>(
        '/reportes/pacientes/',
        { params }
      );
      return normalizeSingleResponse<ReportePacientes>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de pacientes:', error);
      throw error;
    }
  },

  /**
   * Genera reporte de pacientes con embarazo activo
   */
  async reportePacientesEmbarazadas(params?: {
    trimestre?: number;
    riesgo?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/pacientes-embarazadas/', { params });
      return normalizeSingleResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de pacientes embarazadas:', error);
      throw error;
    }
  },

  /**
   * Reporte de nuevos pacientes registrados
   */
  async reporteNuevosPacientes(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/nuevos-pacientes/', { params });
      return normalizeSingleResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de nuevos pacientes:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE EMBARAZOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte general de embarazos
   */
  async generarReporteEmbarazos(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    estado?: string;
    riesgo?: string;
  }): Promise<ReporteEmbarazos> {
    try {
      const response = await api.get<ReporteEmbarazos>(
        '/reportes/embarazos/',
        { params }
      );
      return normalizeSingleResponse<ReporteEmbarazos>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de embarazos:', error);
      throw error;
    }
  },

  /**
   * Reporte de embarazos de alto riesgo
   */
  async reporteEmbarazosAltoRiesgo(): Promise<any> {
    try {
      const response = await api.get('/reportes/embarazos-alto-riesgo/');
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de embarazos alto riesgo:', error);
      throw error;
    }
  },

  /**
   * Reporte de embarazos por trimestre
   */
  async reporteEmbarazosPorTrimestre(trimestre: 1 | 2 | 3): Promise<any> {
    try {
      const response = await api.get('/reportes/embarazos-trimestre/', {
        params: { trimestre }
      });
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error(`❌ Error generando reporte de embarazos trimestre ${trimestre}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE PARTOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte completo de partos
   */
  async generarReportePartos(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    tipo_parto?: string;
    con_complicaciones?: boolean;
  }): Promise<ReportePartos> {
    try {
      const response = await api.get<ReportePartos>(
        '/reportes/partos/',
        { params }
      );
      return normalizeSingleResponse<ReportePartos>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de partos:', error);
      throw error;
    }
  },

  /**
   * Reporte de tasas de cesáreas
   */
  async reporteTasaCesareas(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    medico?: number;
  }): Promise<{
    total_partos: number;
    total_cesareas: number;
    tasa_cesareas: number;
    por_mes: Array<{ mes: string; tasa: number }>;
  }> {
    try {
      const response = await api.get('/reportes/tasa-cesareas/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte de tasa de cesáreas:', error);
      throw error;
    }
  },

  /**
   * Reporte de complicaciones en partos
   */
  async reporteComplicacionesPartos(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    severidad?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/complicaciones-partos/', { params });
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de complicaciones:', error);
      throw error;
    }
  },

  /**
   * Reporte de resultados neonatales
   */
  async reporteResultadosNeonatales(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/resultados-neonatales/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte neonatal:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE CONTROLES PRENATALES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte de controles prenatales
   */
  async generarReporteControles(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    medico?: number;
  }): Promise<ReporteControles> {
    try {
      const response = await api.get<ReporteControles>(
        '/reportes/controles/',
        { params }
      );
      return normalizeSingleResponse<ReporteControles>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de controles:', error);
      throw error;
    }
  },

  /**
   * Reporte de adherencia a controles
   */
  async reporteAdherenciaControles(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<{
    embarazos_totales: number;
    con_controles_adecuados: number;
    con_controles_insuficientes: number;
    sin_controles: number;
    tasa_adherencia: number;
  }> {
    try {
      const response = await api.get('/reportes/adherencia-controles/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte de adherencia:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE LABORATORIO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte de exámenes de laboratorio
   */
  async generarReporteLaboratorio(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    categoria?: string;
    estado?: string;
  }): Promise<ReporteLaboratorio> {
    try {
      const response = await api.get<ReporteLaboratorio>(
        '/reportes/laboratorios/',
        { params }
      );
      return normalizeSingleResponse<ReporteLaboratorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de laboratorio:', error);
      throw error;
    }
  },

  /**
   * Reporte de exámenes pendientes
   */
  async reporteExamenesPendientes(): Promise<any> {
    try {
      const response = await api.get('/reportes/examenes-pendientes/');
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de exámenes pendientes:', error);
      throw error;
    }
  },

  /**
   * Reporte de resultados críticos
   */
  async reporteResultadosCriticos(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/resultados-criticos/', { params });
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de resultados críticos:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES DE CITAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte de citas médicas
   */
  async generarReporteCitas(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    estado?: string;
    medico?: number;
  }): Promise<ReporteCitas> {
    try {
      const response = await api.get<ReporteCitas>(
        '/reportes/citas/',
        { params }
      );
      return normalizeSingleResponse<ReporteCitas>(response.data);
    } catch (error: any) {
      console.error('❌ Error generando reporte de citas:', error);
      throw error;
    }
  },

  /**
   * Reporte de asistencia a citas
   */
  async reporteAsistenciaCitas(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    medico?: number;
  }): Promise<{
    total_citas: number;
    asistieron: number;
    no_asistieron: number;
    canceladas: number;
    tasa_asistencia: number;
    tasa_inasistencia: number;
  }> {
    try {
      const response = await api.get('/reportes/asistencia-citas/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte de asistencia:', error);
      throw error;
    }
  },

  /**
   * Reporte de ocupación de agenda
   */
  async reporteOcupacionAgenda(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    medico?: number;
  }): Promise<{
    horas_disponibles: number;
    horas_ocupadas: number;
    horas_libres: number;
    tasa_ocupacion: number;
  }> {
    try {
      const response = await api.get('/reportes/ocupacion-agenda/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte de ocupación:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // EXPORTACIÓN DE REPORTES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Exporta reporte a PDF
   */
  async exportarReportePDF(
    tipoReporte: TipoReporte,
    params?: Record<string, any>
  ): Promise<Blob> {
    try {
      const response = await api.get(`/reportes/${tipoReporte}/pdf/`, {
        params,
        responseType: 'blob'
      });
      logger.log(`✅ Reporte ${tipoReporte} exportado a PDF`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error exportando reporte ${tipoReporte} a PDF:`, error);
      throw error;
    }
  },

  /**
   * Exporta reporte a Excel
   */
  async exportarReporteExcel(
    tipoReporte: TipoReporte,
    params?: Record<string, any>
  ): Promise<Blob> {
    try {
      const response = await api.get(`/reportes/${tipoReporte}/excel/`, {
        params,
        responseType: 'blob'
      });
      logger.log(`✅ Reporte ${tipoReporte} exportado a Excel`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error exportando reporte ${tipoReporte} a Excel:`, error);
      throw error;
    }
  },

  /**
   * Exporta reporte a CSV
   */
  async exportarReporteCSV(
    tipoReporte: TipoReporte,
    params?: Record<string, any>
  ): Promise<Blob> {
    try {
      const response = await api.get(`/reportes/${tipoReporte}/csv/`, {
        params,
        responseType: 'blob'
      });
      logger.log(`✅ Reporte ${tipoReporte} exportado a CSV`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error exportando reporte ${tipoReporte} a CSV:`, error);
      throw error;
    }
  },

  /**
   * Descarga reporte en formato especificado
   */
  async descargarReporte(
    tipoReporte: TipoReporte,
    formato: FormatoExportacion,
    params?: Record<string, any>
  ): Promise<Blob> {
    switch (formato) {
      case 'pdf':
        return this.exportarReportePDF(tipoReporte, params);
      case 'excel':
        return this.exportarReporteExcel(tipoReporte, params);
      case 'csv':
        return this.exportarReporteCSV(tipoReporte, params);
      case 'json':
        const response = await api.get(`/reportes/${tipoReporte}/json/`, { params });
        const blob = new Blob([JSON.stringify(response.data, null, 2)], {
          type: 'application/json'
        });
        return blob;
      default:
        throw new Error(`Formato de exportación no soportado: ${formato}`);
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ANÁLISIS Y TENDENCIAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Analiza tendencias de partos
   */
  async analizarTendenciasPartos(params?: {
    periodo?: PeriodoReporte;
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<{
    tendencia_general: 'creciente' | 'decreciente' | 'estable';
    porcentaje_cambio: number;
    datos_periodo: Array<{
      periodo: string;
      total: number;
      cesareas: number;
      vaginales: number;
    }>;
    prediccion_proximo_periodo?: number;
  }> {
    try {
      const response = await api.get('/reportes/tendencias-partos/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error analizando tendencias de partos:', error);
      throw error;
    }
  },

  /**
   * Analiza patrones de asistencia a citas
   */
  async analizarPatronesAsistencia(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<{
    patrones_dia_semana: Record<string, number>;
    patrones_hora: Record<string, number>;
    factores_inasistencia: Array<{
      factor: string;
      porcentaje: number;
    }>;
  }> {
    try {
      const response = await api.get('/reportes/patrones-asistencia/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error analizando patrones de asistencia:', error);
      throw error;
    }
  },

  /**
   * Análisis de riesgos obstétricos
   */
  async analizarRiesgosObstetricos(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
  }): Promise<{
    total_embarazos: number;
    distribucion_riesgo: Record<string, number>;
    factores_riesgo_frecuentes: Array<{
      factor: string;
      frecuencia: number;
      porcentaje: number;
    }>;
    complicaciones_asociadas: Record<string, number>;
  }> {
    try {
      const response = await api.get('/reportes/analisis-riesgos/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error analizando riesgos obstétricos:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES PERSONALIZADOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte personalizado
   */
  async generarReportePersonalizado(config: {
    nombre: string;
    descripcion?: string;
    tipo: TipoReporte;
    filtros: Record<string, any>;
    campos: string[];
    agrupacion?: string;
    ordenamiento?: string;
  }): Promise<any> {
    try {
      const response = await api.post('/reportes/personalizado/', config);
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte personalizado:', error);
      throw error;
    }
  },

  /**
   * Guarda configuración de reporte para uso posterior
   */
  async guardarConfiguracionReporte(config: {
    nombre: string;
    descripcion?: string;
    configuracion: Record<string, any>;
  }): Promise<{ id: number; nombre: string }> {
    try {
      const response = await api.post('/reportes/guardar-configuracion/', config);
      logger.log('✅ Configuración de reporte guardada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error guardando configuración:', error);
      throw error;
    }
  },

  /**
   * Lista configuraciones guardadas de reportes
   */
  async listarConfiguracionesGuardadas(): Promise<Array<{
    id: number;
    nombre: string;
    descripcion?: string;
    tipo: TipoReporte;
    fecha_creacion: string;
  }>> {
    try {
      const response = await api.get('/reportes/configuraciones/');
      return normalizeListResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error listando configuraciones:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // UTILIDADES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Calcula rango de fechas para un período
   */
  calcularRangoPeriodo(periodo: PeriodoReporte): {
    fecha_inicio: string;
    fecha_fin: string;
  } {
    const hoy = new Date();
    let fecha_inicio: Date;

    switch (periodo) {
      case 'dia':
        fecha_inicio = new Date(hoy);
        break;
      case 'semana':
        fecha_inicio = new Date(hoy);
        fecha_inicio.setDate(hoy.getDate() - 7);
        break;
      case 'mes':
        fecha_inicio = new Date(hoy);
        fecha_inicio.setMonth(hoy.getMonth() - 1);
        break;
      case 'trimestre':
        fecha_inicio = new Date(hoy);
        fecha_inicio.setMonth(hoy.getMonth() - 3);
        break;
      case 'semestre':
        fecha_inicio = new Date(hoy);
        fecha_inicio.setMonth(hoy.getMonth() - 6);
        break;
      case 'anio':
        fecha_inicio = new Date(hoy);
        fecha_inicio.setFullYear(hoy.getFullYear() - 1);
        break;
      default:
        fecha_inicio = new Date(hoy);
        fecha_inicio.setMonth(hoy.getMonth() - 1);
    }

    return {
      fecha_inicio: fecha_inicio.toISOString().split('T')[0],
      fecha_fin: hoy.toISOString().split('T')[0]
    };
  },

  /**
   * Descarga un blob como archivo
   */
  descargarArchivo(blob: Blob, nombreArchivo: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nombreArchivo;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // GESTIÓN DE REPORTES Y ALERTAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene lista de reportes generados
   */
  async getReportes(params?: {
    tipo?: TipoReporte;
    estado?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
    ordering?: string;
    page_size?: number;
  }): Promise<Reporte[]> {
    try {
      const response = await api.get<Reporte[]>('/reportes/reportes-generados/', { params });
      return normalizeListResponse<Reporte>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo lista de reportes:', error);
      throw error;
    }
  },

  /**
   * Obtiene alertas médicas activas
   */
  async getAlertasActivas(params?: {
    tipo?: string;
    paciente?: number;
    embarazo?: number;
  }): Promise<AlertaMedica[]> {
    try {
      const response = await api.get<AlertaMedica[]>('/reportes/alertas-medicas/activas/', { params });
      return normalizeListResponse<AlertaMedica>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo alertas activas:', error);
      throw error;
    }
  },

  /**
   * Lista los tipos de reporte configurados (activos por defecto)
   */
  async listarTiposReporte(soloActivos: boolean = true): Promise<TipoReporteConfig[]> {
    const response = await api.get<any>('/reportes/tipos-reporte/', {
      params: soloActivos ? { activo: true } : undefined,
    });
    return normalizeListResponse<TipoReporteConfig>(response.data);
  },

  /**
   * Obtiene el detalle completo de un tipo de reporte (incluye filtros y formatos disponibles)
   */
  async obtenerTipoReporte(id: number): Promise<TipoReporteConfig> {
    const response = await api.get<TipoReporteConfig>(`/reportes/tipos-reporte/${id}/`);
    return normalizeSingleResponse<TipoReporteConfig>(response.data);
  },

  /**
   * Obtiene una alerta médica por ID
   */
  async obtenerAlerta(id: number): Promise<AlertaMedica> {
    const response = await api.get<AlertaMedica>(`/reportes/alertas-medicas/${id}/`);
    return normalizeSingleResponse<AlertaMedica>(response.data);
  },

  /**
   * Lista todas las alertas médicas (paginadas en el backend)
   */
  async listarAlertas(params?: {
    tipo?: string;
    prioridad?: string;
    estado?: string;
    paciente_id?: number;
    embarazo_id?: number;
    search?: string;
  }): Promise<AlertaMedica[]> {
    try {
      const response = await api.get<any>('/reportes/alertas-medicas/', { params });
      return normalizeListResponse<AlertaMedica>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando alertas médicas:', error);
      throw error;
    }
  },

  /**
   * Crea una nueva alerta médica
   */
  async crearAlerta(payload: Partial<AlertaMedica>): Promise<AlertaMedica> {
    const response = await api.post<AlertaMedica>('/reportes/alertas-medicas/', payload);
    return normalizeSingleResponse<AlertaMedica>(response.data);
  },

  /**
   * Marca una alerta como revisada
   */
  async marcarAlertaRevisada(id: number, comentario?: string): Promise<AlertaMedica> {
    const response = await api.post<AlertaMedica>(
      `/reportes/alertas-medicas/${id}/marcar_revisada/`,
      { comentario },
    );
    return normalizeSingleResponse<AlertaMedica>(response.data);
  },

  /**
   * Marca una alerta como resuelta
   */
  async marcarAlertaResuelta(id: number, comentario?: string): Promise<AlertaMedica> {
    const response = await api.post<AlertaMedica>(
      `/reportes/alertas-medicas/${id}/marcar_resuelta/`,
      { comentario },
    );
    return normalizeSingleResponse<AlertaMedica>(response.data);
  },

  /**
   * Descarta una alerta
   */
  async descartarAlerta(id: number, comentario?: string): Promise<AlertaMedica> {
    const response = await api.post<AlertaMedica>(
      `/reportes/alertas-medicas/${id}/descartar/`,
      { comentario },
    );
    return normalizeSingleResponse<AlertaMedica>(response.data);
  },

  /**
   * Estadísticas agregadas de alertas médicas (cacheadas 60s en el backend)
   */
  async getEstadisticasAlertas(): Promise<{
    total_alertas: number;
    alertas_activas: number;
    alertas_criticas_activas: number;
    por_tipo: Array<{ tipo: string; count: number }>;
    por_prioridad: Array<{ prioridad: string; count: number }>;
    por_estado: Array<{ estado: string; count: number }>;
  }> {
    const response = await api.get<any>('/reportes/alertas-medicas/estadisticas/');
    return normalizeSingleResponse(response.data);
  },

  /**
   * Obtiene vista previa real de un reporte (sin generarlo), contando
   * registros reales que entrarían según el tipo y rango de fechas.
   */
  async getReportePreview(parametros: any): Promise<{
    tipo_nombre: string;
    formato: string;
    fecha_inicio: string | null;
    fecha_fin: string | null;
    total_registros: number;
    tamanio_estimado_kb: number;
  }> {
    const fechaInicio = parametros.rango_fechas ? parametros.rango_fechas[0].format('YYYY-MM-DD') : null;
    const fechaFin = parametros.rango_fechas ? parametros.rango_fechas[1].format('YYYY-MM-DD') : null;
    const response = await api.post<any>('/reportes/reportes-generados/preview/', {
      tipo_reporte: parametros.tipo_reporte,
      formato: parametros.formato || 'pdf',
      fecha_inicio: fechaInicio,
      fecha_fin: fechaFin,
    });
    return normalizeSingleResponse(response.data);
  },

  /**
   * Solicita la generación de un nuevo reporte. Crea un ReporteGenerado real
   * en estado "pendiente" — el procesamiento real (armado del archivo) ocurre
   * por separado; esta llamada no devuelve un archivo inmediato.
   */
  async generateReporte(
    tipoReporteId: number,
    parametros: {
      fecha_inicio?: string;
      fecha_fin?: string;
      filtro_paciente?: number;
      filtro_medico?: number;
      filtro_servicio?: string;
      [key: string]: any;
    },
    formato: FormatoExportacion
  ): Promise<Reporte> {
    try {
      const { fecha_inicio, fecha_fin, filtro_paciente, filtro_medico, filtro_servicio, ...resto } = parametros;
      const response = await api.post<Reporte>('/reportes/reportes-generados/solicitar/', {
        tipo_reporte: tipoReporteId,
        formato: formatoAlBackend(formato),
        fecha_inicio,
        fecha_fin,
        filtro_paciente,
        filtro_medico,
        filtro_servicio,
        parametros: resto,
      });
      logger.log(`✅ Solicitud de reporte ${tipoReporteId} creada`);
      const reporte = normalizeSingleResponse<Reporte>(response.data);
      return { ...reporte, formato: formatoDelBackend(reporte.formato as string) as FormatoExportacion };
    } catch (error: any) {
      console.error(`❌ Error solicitando reporte ${tipoReporteId}:`, error);
      throw error;
    }
  },

  /**
   * Descarga un reporte previamente generado
   */
  async downloadReporte(reporteId: number): Promise<Blob> {
    try {
      const response = await api.get(`/reportes/reportes-generados/${reporteId}/descargar/`, {
        responseType: 'blob'
      });
      logger.log(`✅ Reporte ${reporteId} descargado`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error descargando reporte ${reporteId}:`, error);
      throw error;
    }
  },

  /**
   * Comparte un reporte por email
   * NUEVO ENDPOINT - CONECTADO AL BACKEND
   */
  async compartirEmail(reporteId: number, emails: string[], mensaje?: string): Promise<any> {
    try {
      const response = await api.post(`/reportes/${reporteId}/compartir-email/`, {
        emails,
        mensaje
      });
      logger.log(`✅ Reporte ${reporteId} compartido por email a ${emails.length} destinatarios`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.warn('⚠️ Endpoint compartir-email no disponible (404)');
        return {
          success: false,
          mensaje: 'Función de compartir por email no disponible'
        };
      }
      console.error(`❌ Error compartiendo reporte ${reporteId} por email:`, error);
      throw error;
    }
  },

  /**
   * Resuelve una alerta médica
   */
  async resolverAlerta(alertaId: number, notasResolucion?: string): Promise<AlertaMedica> {
    try {
      const response = await api.post<AlertaMedica>(`/reportes/alertas/${alertaId}/resolver/`, {
        notas_resolucion: notasResolucion
      });
      logger.log(`✅ Alerta ${alertaId} resuelta`);
      return normalizeSingleResponse<AlertaMedica>(response.data);
    } catch (error: any) {
      console.error(`❌ Error resolviendo alerta ${alertaId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ENHANCED EXPORTS - PDF/EXCEL CON GRÁFICOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Descarga PDF mejorado con gráficos embebidos
   */
  async downloadStatisticsPDFEnhanced(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    try {
      const response = await api.get('/reportes/statistics/download-pdf-enhanced/', {
        params,
        responseType: 'blob'
      });
      logger.log('✅ PDF mejorado descargado exitosamente');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error descargando PDF mejorado:', error);
      throw error;
    }
  },

  /**
   * Descarga Excel con gráficos y múltiples hojas
   */
  async downloadStatisticsExcel(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> {
    try {
      const response = await api.get('/reportes/statistics/download-excel/', {
        params,
        responseType: 'blob'
      });
      logger.log('✅ Excel descargado exitosamente');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error descargando Excel:', error);
      throw error;
    }
  },

  /**
   * Obtiene estadísticas por período
   */
  async getStatisticsByPeriod(params: {
    period_type: 'day' | 'week' | 'month' | 'year';
    start_date?: string;
    end_date?: string;
    module?: 'all' | 'pacientes' | 'embarazos' | 'controles' | 'partos' | 'citas';
  }): Promise<any> {
    try {
      const response = await api.get('/reportes/statistics/by-period/', { params });
      return normalizeSingleResponse(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo estadísticas por período:', error);
      throw error;
    }
  },

  /**
   * Helper: Descarga PDF mejorado y guarda archivo
   */
  async downloadAndSavePDFEnhanced(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<void> {
    try {
      const blob = await this.downloadStatisticsPDFEnhanced(params);
      const fecha = new Date().toISOString().split('T')[0];
      this.descargarArchivo(blob, `estadisticas_${fecha}.pdf`);
    } catch (error) {
      console.error('Error descargando PDF:', error);
      throw error;
    }
  },

  /**
   * Helper: Descarga Excel y guarda archivo
   */
  async downloadAndSaveExcel(params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<void> {
    try {
      const blob = await this.downloadStatisticsExcel(params);
      const fecha = new Date().toISOString().split('T')[0];
      this.descargarArchivo(blob, `estadisticas_${fecha}.xlsx`);
    } catch (error) {
      console.error('Error descargando Excel:', error);
      throw error;
    }
  },

  /**
   * Obtiene datos para gráfico de composición (donut chart)
   */
  async obtenerCompositionChart(): Promise<any> {
    try {
      const response = await api.get('/reportes/charts/composition/');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo composition chart:', error);
      return [];
    }
  },

  /**
   * Obtiene datos para gráfico de barras apiladas
   */
  async obtenerStackedBarChart(months: number = 12): Promise<any> {
    try {
      const response = await api.get('/reportes/charts/stacked-bar/', {
        params: { months }
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo stacked bar chart:', error);
      return [];
    }
  },

  /**
   * Obtiene datos para gráfico de distribución
   */
  async obtenerDistributionChart(): Promise<any> {
    try {
      const response = await api.get('/reportes/charts/distribution/');
      return response.data;
    } catch (error) {
      console.error('Error obteniendo distribution chart:', error);
      return { data: [], stats: {} };
    }
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTACIONES POR DEFECTO
// ═══════════════════════════════════════════════════════════════════════════


