/**
 * =============================================================================
 * SERVICIO DE LABORATORIO
 * =============================================================================
 * Completo: Interfaces basadas en los serializers del backend Django
 * - TipoExamen (catálogo de exámenes)
 * - ValorReferencia (rangos normales)
 * - ExamenLaboratorio (examen solicitado)
 * - ResultadoLaboratorio (resultados individuales)
 * =============================================================================
 */

import api from './api';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES (Basadas en los serializers del backend)
// ═══════════════════════════════════════════════════════════════════════════

export interface TipoExamen {
  id: number;
  nombre: string;
  codigo: string;
  categoria: 'hematologia' | 'bioquimica' | 'inmunologia' | 'microbiologia' | 'urinalisis' | 'serologia' | 'hormonal' | 'genetica';
  descripcion?: string;
  preparacion?: string;
  tiempo_resultado: number; // en horas
  precio: number;
  activo: boolean;
  total_examenes?: number;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

export interface ValorReferencia {
  id: number;
  tipo_examen: number;
  tipo_examen_nombre?: string;
  parametro: string;
  valor_minimo?: number;
  valor_maximo?: number;
  valor_normal?: string;
  unidad: string;
  condicion?: string;
  es_critico_bajo?: number;
  es_critico_alto?: number;
  rango_normal?: string;
}

export interface ResultadoLaboratorio {
  id?: number;
  examen: number;
  valor_referencia: number;
  parametro_nombre?: string;
  valor_numerico?: number;
  valor_texto?: string;
  unidad?: string;
  rango_referencia?: string;
  es_normal: boolean;
  es_critico: boolean;
  estado?: string; // 'CRÍTICO' | 'ANORMAL' | 'NORMAL'
  observaciones?: string;
  fecha_registro?: string;
}

export interface ExamenLaboratorio {
  id?: number;
  paciente: number;
  paciente_nombre?: string;
  paciente_info?: {
    id: number;
    nombre_completo: string;
    id_clinico: string;
    edad: number;
  };
  control_prenatal?: number;
  control_prenatal_info?: {
    id: number;
    numero_control: number;
    fecha_control: string;
    semanas_gestacion: number;
  };
  tipo_examen: number;
  tipo_examen_nombre?: string;
  tipo_examen_info?: {
    id: number;
    nombre: string;
    codigo: string;
    categoria: string;
    preparacion?: string;
    tiempo_resultado: number;
  };
  categoria?: string;
  medico_solicitante?: number;
  medico_nombre?: string;
  medico_info?: {
    id: number;
    nombre: string;
    especialidad: string;
  };
  fecha_solicitud: string;
  fecha_muestra?: string;
  fecha_resultado?: string;
  estado: 'solicitado' | 'en_proceso' | 'completado' | 'cancelado';
  prioridad: 'normal' | 'urgente' | 'stat';
  indicaciones?: string;
  observaciones?: string;
  resultados?: ResultadoLaboratorio[];
  resumen?: {
    total_parametros: number;
    normales: number;
    anormales: number;
    criticos: number;
    porcentaje_normalidad: number;
  };
  dias_desde_solicitud?: number;
  esta_pendiente?: boolean;
  esta_vencido?: boolean;
  tiene_resultados?: boolean;
  resultados_anormales?: number;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  _uniqueRowKey?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO
// ═══════════════════════════════════════════════════════════════════════════

export const laboratorioService = {
  api: api,
  // ─────────────────────────────────────────────────────────────────────────
  // TIPOS DE EXAMEN
  // ─────────────────────────────────────────────────────────────────────────

  getTiposExamen: async () => {
    const response = await api.get('/laboratorios/tipos-examenes/');
    return response.data?.results || response.data || response;
  },

  getTipoExamenById: async (id: number) => {
    const response = await api.get<TipoExamen>(`/laboratorios/tipos-examenes/${id}/`);
    return response.data;
  },

  // ─────────────────────────────────────────────────────────────────────────
  // VALORES DE REFERENCIA
  // ─────────────────────────────────────────────────────────────────────────

  getValoresReferencia: async (tipoExamenId?: number) => {
    const params = tipoExamenId ? { tipo_examen: tipoExamenId } : {};
    const response = await api.get('/laboratorios/valores-referencia/', { params });
    return response.data?.results || response.data || response;
  },

  getValorReferenciaById: async (id: number) => {
    const response = await api.get<ValorReferencia>(`/laboratorios/valores-referencia/${id}/`);
    return response.data;
  },

  // ─────────────────────────────────────────────────────────────────────────
  // EXÁMENES DE LABORATORIO
  // ─────────────────────────────────────────────────────────────────────────

  /** Lista todos los exámenes */
  getAll: async () => {
    const response = await api.get('/laboratorios/examenes/');
    return response.data?.results || response.data || response;
  },

  /** Lista exámenes de una paciente */
  getByPaciente: async (pacienteId: number) => {
    const response = await api.get('/laboratorios/examenes/', {
      params: { paciente: pacienteId }
    });
    return response.data?.results || response.data || response;
  },

  /** Obtiene un examen por ID */
  getById: async (id: number) => {
    const response = await api.get<ExamenLaboratorio>(`/laboratorios/examenes/${id}/`);
    return response.data;
  },

  /** Crear examen */
  create: async (data: Partial<ExamenLaboratorio>) => {
    return await api.post('/laboratorios/examenes/', data);
  },

  /** Actualizar examen */
  update: async (id: number, data: Partial<ExamenLaboratorio>) => {
    return await api.patch(`/laboratorios/examenes/${id}/`, data);
  },

  /** Eliminar examen */
  delete: async (id: number) => {
    return await api.delete(`/laboratorios/examenes/${id}/`);
  },

  // ─────────────────────────────────────────────────────────────────────────
  // RESULTADOS
  // ─────────────────────────────────────────────────────────────────────────

  /** Agregar resultado a un examen — usa endpoint plano /resultados/ */
  addResultado: async (examenId: number, resultado: Partial<ResultadoLaboratorio>) => {
    return await api.post('/laboratorios/resultados/', { ...resultado, examen: examenId });
  },

  /** Actualizar resultado */
  updateResultado: async (_examenId: number, resultadoId: number, data: Partial<ResultadoLaboratorio>) => {
    return await api.patch(`/laboratorios/resultados/${resultadoId}/`, data);
  },

  /** Eliminar resultado */
  deleteResultado: async (_examenId: number, resultadoId: number) => {
    return await api.delete(`/laboratorios/resultados/${resultadoId}/`);
  },

  async listar() {
    const response = await api.get('/laboratorios/examenes/');
    return response.data;
  },

  async obtener(id: number) {
    const response = await api.get(`/laboratorios/examenes/${id}/`);
    return response.data;
  },

  async crear(data: any) {
    const response = await api.post('/laboratorios/examenes/', data);
    return response.data;
  },

  async actualizar(id: number, data: any) {
    const response = await api.put(`/laboratorios/examenes/${id}/`, data);
    return response.data;
  },

  async eliminar(id: number) {
    await api.delete(`/laboratorios/examenes/${id}/`);
  },

  async obtenerPorPaciente(paciente_id: number) {
    const response = await api.get(`/laboratorios/examenes/?paciente_id=${paciente_id}`);
    return response.data;
  },

  async obtenerPorEmbarazo(embarazo_id: number) {
    const response = await api.get(`/laboratorios/examenes/?embarazo_id=${embarazo_id}`);
    return response.data;
  },

  async obtenerPorTipo(tipo_examen: string) {
    const response = await api.get(`/laboratorios/examenes/?tipo_examen=${tipo_examen}`);
    return response.data;
  },

  async obtenerResultados(laboratorio_id: number) {
    // Usa endpoint plano con filtro por examen
    const response = await api.get(`/laboratorios/resultados/?examen=${laboratorio_id}`);
    return response.data;
  },

  async interpretarResultado(resultado_id: number) {
    // No existe endpoint /interpretacion/ — retorna el resultado base
    const response = await api.get(`/laboratorios/resultados/${resultado_id}/`);
    return response.data;
  },

  async obtenerValoresReferencia(tipo_examen_id: number | string, semanas_gestacion?: number) {
    const params: Record<string, any> = { tipo_examen: tipo_examen_id };
    if (semanas_gestacion) params.semanas_gestacion = semanas_gestacion;
    const response = await api.get('/laboratorios/valores-referencia/', { params });
    return response.data;
  },

  // ─────────────────────────────────────────────────────────────────────────
  // NUEVOS MÉTODOS PARA SISTEMA COMPLETO
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Obtener valores de referencia para un tipo de examen específico
   * Conecta con: GET /api/laboratorios/examenes/valores-referencia-por-tipo/?tipo_examen_id=X
   */
  getValoresReferenciaPorTipo: async (tipoExamenId: number) => {
    const response = await api.get('/laboratorios/examenes/valores-referencia-por-tipo/', {
      params: { tipo_examen_id: tipoExamenId }
    });
    return response.data;
  },

  /**
   * Obtener estadísticas e histórico de resultados de un paciente
   * Para mostrar gráficos de evolución temporal
   * Conecta con: GET /api/laboratorios/examenes/{id}/estadisticas-paciente/?limite=10
   */
  getEstadisticasPaciente: async (examenId: number, limite: number = 10) => {
    const response = await api.get(`/laboratorios/examenes/${examenId}/estadisticas-paciente/`, {
      params: { limite }
    });
    return response.data;
  },

  /**
   * Crear múltiples resultados de laboratorio en una sola petición
   * Conecta con: POST /api/laboratorios/examenes/{id}/crear-resultado-multiple/
   */
  crearResultadoMultiple: async (examenId: number, resultados: Array<{
    valor_referencia: number;
    valor_numerico?: number;
    valor_texto?: string;
    unidad?: string;
    observaciones?: string;
  }>, completarExamen: boolean = false) => {
    const response = await api.post(`/laboratorios/examenes/${examenId}/crear-resultado-multiple/`, {
      resultados,
      completar_examen: completarExamen
    });
    return response.data;
  },

  /**
   * Obtener todos los resultados de un examen (usando endpoint de resultados)
   */
  getResultadosPorExamen: async (examenId: number) => {
    const response = await api.get('/laboratorios/resultados/por-examen/', {
      params: { examen_id: examenId }
    });
    return response.data;
  },

  /**
   * Marcar examen como completado
   */
  completarExamen: async (examenId: number) => {
    const response = await api.post(`/laboratorios/examenes/${examenId}/cambiar-estado/`, {
      estado: 'completado'
    });
    return response.data;
  },
};
