/**
 * =============================================================================
 * SERVICIO DE CONSULTORIOS - VERSIÓN MEGA COMPLETA Y EXTENDIDA
 * =============================================================================
 * ✅ MEGA COMPLETO: Gestión integral de consultorios y disponibilidad
 * 
 * MÓDULOS INCLUIDOS:
 * - Gestión completa de consultorios (CRUD)
 * - Disponibilidad y horarios
 * - Asignación de consultorios
 * - Ocupación y programación
 * - Reservas y turnos
 * - Equipamiento y recursos
 * - Mantenimiento y limpieza
 * - Estadísticas de uso
 * - Reportes de ocupación
 * - Normalización de respuestas
 * - Validaciones exhaustivas
 * 
 * ALINEACIÓN: 100% compatible con backend Django
 * =============================================================================
 */

import api from './api';

// ═══════════════════════════════════════════════════════════════════════════
// TIPOS Y ENUMS
// ═══════════════════════════════════════════════════════════════════════════

export type TipoConsultorio = 'consulta' | 'procedimientos' | 'emergencia' | 'multifuncional';
export type EstadoConsultorio = 'disponible' | 'ocupado' | 'mantenimiento' | 'limpieza' | 'reservado';
type TipoEquipamiento = 'basico' | 'intermedio' | 'avanzado' | 'quirurgico';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES
// ═══════════════════════════════════════════════════════════════════════════

export interface Consultorio {
  // Identificación
  id?: number;
  codigo: string;
  nombre: string;

  // Características
  tipo: TipoConsultorio;
  piso?: number;
  area?: string;
  capacidad?: number;

  // Estado y disponibilidad
  estado?: EstadoConsultorio;
  activo?: boolean;

  // Equipamiento
  equipamiento?: TipoEquipamiento;
  tiene_camilla?: boolean;
  tiene_escritorio?: boolean;
  tiene_computadora?: boolean;
  tiene_lavamanos?: boolean;
  tiene_oxigeno?: boolean;
  tiene_aspirador?: boolean;

  // Descripción y notas
  descripcion?: string;
  observaciones?: string;

  // Metadata
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  creado_por?: number;

  // Datos poblados
  ocupacion_actual?: OcupacionConsultorio;
  proxima_disponibilidad?: string;
  medicos_asignados?: number[];
  total_citas_hoy?: number;
}

interface HorarioConsultorio {
  id?: number;
  consultorio: number;
  dia_semana: number; // 0=lunes, 6=domingo
  hora_inicio: string; // HH:MM
  hora_fin: string; // HH:MM
  activo?: boolean;
  observaciones?: string;
}

interface OcupacionConsultorio {
  id?: number;
  consultorio: number;
  consultorio_info?: Partial<Consultorio>;

  // Ocupación
  fecha: string;
  hora_inicio: string;
  hora_fin: string;

  // Asignación
  medico?: number;
  medico_nombre?: string;
  paciente?: number;
  paciente_nombre?: string;
  cita?: number;

  // Tipo de uso
  tipo_uso: 'consulta' | 'procedimiento' | 'emergencia' | 'mantenimiento' | 'otro';

  // Estado
  estado: 'programada' | 'en_curso' | 'finalizada' | 'cancelada';

  // Notas
  motivo?: string;
  observaciones?: string;

  // Metadata
  fecha_creacion?: string;
  creado_por?: number;
}

export interface ReservaConsultorio {
  id?: number;
  consultorio: number;
  consultorio_info?: Partial<Consultorio>;

  // Reserva
  fecha_reserva: string;
  hora_inicio: string;
  hora_fin: string;
  duracion_minutos?: number;

  // Solicitante
  solicitado_por: number;
  solicitado_por_nombre?: string;
  medico?: number;
  medico_nombre?: string;

  // Propósito
  motivo: string;
  tipo_actividad: string;
  observaciones?: string;

  // Estado
  estado: 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada' | 'completada';
  aprobada_por?: number;
  fecha_aprobacion?: string;

  // Metadata
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

export interface MantenimientoConsultorio {
  id?: number;
  consultorio: number;
  consultorio_info?: Partial<Consultorio>;

  // Mantenimiento
  tipo_mantenimiento: 'preventivo' | 'correctivo' | 'limpieza_profunda' | 'desinfeccion';
  fecha_programada: string;
  fecha_realizada?: string;

  // Descripción
  descripcion: string;
  trabajo_realizado?: string;

  // Personal
  responsable?: number;
  responsable_nombre?: string;

  // Estado
  estado: 'programado' | 'en_proceso' | 'completado' | 'cancelado';

  // Costos y materiales
  costo?: number;
  materiales_usados?: string;

  // Metadata
  observaciones?: string;
  fecha_creacion?: string;
}

interface EstadisticasConsultorio {
  consultorio_id: number;
  consultorio_nombre: string;
  periodo: {
    inicio: string;
    fin: string;
  };

  // Uso
  horas_totales_disponibles: number;
  horas_ocupadas: number;
  horas_libres: number;
  tasa_ocupacion: number; // porcentaje

  // Actividades
  total_consultas: number;
  total_procedimientos: number;
  total_emergencias: number;

  // Médicos
  medicos_usuarios: number;
  medico_mas_frecuente?: string;

  // Mantenimiento
  total_mantenimientos: number;
  horas_mantenimiento: number;

  // Tendencias
  promedio_ocupacion_dia: number;
  dia_mas_ocupado?: string;
  hora_pico?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE NORMALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════════

function normalizeListResponse<T>(data: any): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data?.results && Array.isArray(data.results)) return data.results as T[];
  if (data?.data && Array.isArray(data.data)) return data.data as T[];
  console.warn('⚠️ consultoriosService: Respuesta no es array:', data);
  return [];
}

function normalizeSingleResponse<T>(data: any): T {
  if (data?.data && typeof data.data === 'object') return data.data as T;
  return data as T;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════

export const consultoriosService = {

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CRUD BÁSICO - CONSULTORIOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista todos los consultorios
   */
  async listar(filtros?: {
    tipo?: TipoConsultorio;
    estado?: EstadoConsultorio;
    piso?: number;
    activo?: boolean;
  }): Promise<Consultorio[]> {
    try {
      const response = await api.get<Consultorio[]>('/consultorios/', { params: filtros });
      return normalizeListResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando consultorios:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getAll(filtros?: any): Promise<Consultorio[]> {
    return this.listar(filtros);
  },

  /**
   * Obtiene un consultorio por ID
   */
  async obtener(id: number): Promise<Consultorio> {
    try {
      const response = await api.get<Consultorio>(`/consultorios/${id}/`);
      return normalizeSingleResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo consultorio ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getById(id: number): Promise<Consultorio> {
    return this.obtener(id);
  },

  /**
   * Crea un nuevo consultorio
   */
  async crear(data: Partial<Consultorio>): Promise<Consultorio> {
    try {
      const response = await api.post<Consultorio>('/consultorios/', data);
      console.log('✅ Consultorio creado exitosamente');
      return normalizeSingleResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error creando consultorio:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async create(data: Partial<Consultorio>): Promise<Consultorio> {
    return this.crear(data);
  },

  /**
   * Actualiza un consultorio
   */
  async actualizar(id: number, data: Partial<Consultorio>): Promise<Consultorio> {
    try {
      const response = await api.put<Consultorio>(`/consultorios/${id}/`, data);
      console.log(`✅ Consultorio ${id} actualizado`);
      return normalizeSingleResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando consultorio ${id}:`, error);
      throw error;
    }
  },

  /**
   * Actualización parcial
   */
  async actualizarParcial(id: number, data: Partial<Consultorio>): Promise<Consultorio> {
    try {
      const response = await api.patch<Consultorio>(`/consultorios/${id}/`, data);
      console.log(`✅ Consultorio ${id} actualizado parcialmente`);
      return normalizeSingleResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando consultorio ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async update(id: number, data: Partial<Consultorio>): Promise<Consultorio> {
    return this.actualizar(id, data);
  },

  /**
   * Elimina un consultorio
   */
  async eliminar(id: number): Promise<void> {
    try {
      await api.delete(`/consultorios/${id}/`);
      console.log(`✅ Consultorio ${id} eliminado`);
    } catch (error: any) {
      console.error(`❌ Error eliminando consultorio ${id}:`, error);
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
  // DISPONIBILIDAD Y HORARIOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene consultorios disponibles
   */
  async obtenerDisponibles(params?: {
    fecha?: string;
    hora?: string;
    tipo?: TipoConsultorio;
  }): Promise<Consultorio[]> {
    try {
      const response = await api.get<Consultorio[]>('/consultorios/disponibles/', { params });
      return normalizeListResponse<Consultorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo consultorios disponibles:', error);
      throw error;
    }
  },

  /**
   * Verifica disponibilidad de un consultorio específico
   */
  async verificarDisponibilidad(
    consultorioId: number,
    fecha: string,
    horaInicio: string,
    horaFin: string
  ): Promise<{ disponible: boolean; motivo?: string }> {
    try {
      const response = await api.get(`/consultorios/${consultorioId}/verificar-disponibilidad/`, {
        params: { fecha, hora_inicio: horaInicio, hora_fin: horaFin }
      });
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error verificando disponibilidad:`, error);
      throw error;
    }
  },

  /**
   * Obtiene horarios de un consultorio
   */
  async obtenerHorarios(consultorioId: number): Promise<HorarioConsultorio[]> {
    try {
      const response = await api.get<HorarioConsultorio[]>(
        `/consultorios/${consultorioId}/horarios/`
      );
      return normalizeListResponse<HorarioConsultorio>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo horarios:`, error);
      throw error;
    }
  },

  /**
   * Crea horario para consultorio
   */
  async crearHorario(
    consultorioId: number,
    data: Partial<HorarioConsultorio>
  ): Promise<HorarioConsultorio> {
    try {
      const response = await api.post<HorarioConsultorio>(
        `/consultorios/${consultorioId}/horarios/`,
        data
      );
      console.log('✅ Horario creado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error creando horario:', error);
      throw error;
    }
  },

  /**
   * Actualiza horario
   */
  async actualizarHorario(
    consultorioId: number,
    horarioId: number,
    data: Partial<HorarioConsultorio>
  ): Promise<HorarioConsultorio> {
    try {
      const response = await api.patch<HorarioConsultorio>(
        `/consultorios/${consultorioId}/horarios/${horarioId}/`,
        data
      );
      console.log('✅ Horario actualizado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error actualizando horario:', error);
      throw error;
    }
  },

  /**
   * Elimina horario
   */
  async eliminarHorario(consultorioId: number, horarioId: number): Promise<void> {
    try {
      await api.delete(`/consultorios/${consultorioId}/horarios/${horarioId}/`);
      console.log('✅ Horario eliminado');
    } catch (error: any) {
      console.error('❌ Error eliminando horario:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // OCUPACIÓN Y PROGRAMACIÓN
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene ocupaciones de un consultorio
   */
  async obtenerOcupaciones(
    consultorioId: number,
    params?: {
      fecha?: string;
      fecha_inicio?: string;
      fecha_fin?: string;
      estado?: string;
    }
  ): Promise<OcupacionConsultorio[]> {
    try {
      const response = await api.get<OcupacionConsultorio[]>(
        `/consultorios/${consultorioId}/ocupaciones/`,
        { params }
      );
      return normalizeListResponse<OcupacionConsultorio>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo ocupaciones:`, error);
      throw error;
    }
  },

  /**
   * Registra ocupación de consultorio
   */
  async registrarOcupacion(data: Partial<OcupacionConsultorio>): Promise<OcupacionConsultorio> {
    try {
      const response = await api.post<OcupacionConsultorio>('/consultorios/ocupaciones/', data);
      console.log('✅ Ocupación registrada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error registrando ocupación:', error);
      throw error;
    }
  },

  /**
   * Finaliza ocupación
   */
  async finalizarOcupacion(ocupacionId: number): Promise<OcupacionConsultorio> {
    try {
      const response = await api.post<OcupacionConsultorio>(
        `/consultorios/ocupaciones/${ocupacionId}/finalizar/`
      );
      console.log('✅ Ocupación finalizada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error finalizando ocupación:', error);
      throw error;
    }
  },

  /**
   * Obtiene ocupación actual de un consultorio
   */
  async obtenerOcupacionActual(consultorioId: number): Promise<OcupacionConsultorio | null> {
    try {
      const response = await api.get<OcupacionConsultorio>(
        `/consultorios/${consultorioId}/ocupacion-actual/`
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null; // No hay ocupación actual
      }
      console.error('❌ Error obteniendo ocupación actual:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // RESERVAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista reservas de consultorios
   */
  async listarReservas(params?: {
    consultorio?: number;
    fecha?: string;
    estado?: string;
    medico?: number;
  }): Promise<ReservaConsultorio[]> {
    try {
      const response = await api.get<ReservaConsultorio[]>('/consultorios/reservas/', { params });
      return normalizeListResponse<ReservaConsultorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando reservas:', error);
      throw error;
    }
  },

  /**
   * Crea una reserva
   */
  async crearReserva(data: Partial<ReservaConsultorio>): Promise<ReservaConsultorio> {
    try {
      const response = await api.post<ReservaConsultorio>('/consultorios/reservas/', data);
      console.log('✅ Reserva creada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error creando reserva:', error);
      throw error;
    }
  },

  /**
   * Aprueba una reserva
   */
  async aprobarReserva(reservaId: number): Promise<ReservaConsultorio> {
    try {
      const response = await api.post<ReservaConsultorio>(
        `/consultorios/reservas/${reservaId}/aprobar/`
      );
      console.log('✅ Reserva aprobada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error aprobando reserva:', error);
      throw error;
    }
  },

  /**
   * Rechaza una reserva
   */
  async rechazarReserva(reservaId: number, motivo?: string): Promise<ReservaConsultorio> {
    try {
      const response = await api.post<ReservaConsultorio>(
        `/consultorios/reservas/${reservaId}/rechazar/`,
        { motivo }
      );
      console.log('✅ Reserva rechazada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error rechazando reserva:', error);
      throw error;
    }
  },

  /**
   * Cancela una reserva
   */
  async cancelarReserva(reservaId: number, motivo?: string): Promise<ReservaConsultorio> {
    try {
      const response = await api.post<ReservaConsultorio>(
        `/consultorios/reservas/${reservaId}/cancelar/`,
        { motivo }
      );
      console.log('✅ Reserva cancelada');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error cancelando reserva:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // MANTENIMIENTO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista mantenimientos
   */
  async listarMantenimientos(params?: {
    consultorio?: number;
    tipo?: string;
    estado?: string;
  }): Promise<MantenimientoConsultorio[]> {
    try {
      const response = await api.get<MantenimientoConsultorio[]>(
        '/consultorios/mantenimientos/',
        { params }
      );
      return normalizeListResponse<MantenimientoConsultorio>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando mantenimientos:', error);
      throw error;
    }
  },

  /**
   * Programa mantenimiento
   */
  async programarMantenimiento(
    data: Partial<MantenimientoConsultorio>
  ): Promise<MantenimientoConsultorio> {
    try {
      const response = await api.post<MantenimientoConsultorio>(
        '/consultorios/mantenimientos/',
        data
      );
      console.log('✅ Mantenimiento programado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error programando mantenimiento:', error);
      throw error;
    }
  },

  /**
   * Completa mantenimiento
   */
  async completarMantenimiento(
    mantenimientoId: number,
    data: {
      trabajo_realizado: string;
      materiales_usados?: string;
      costo?: number;
      observaciones?: string;
    }
  ): Promise<MantenimientoConsultorio> {
    try {
      const response = await api.post<MantenimientoConsultorio>(
        `/consultorios/mantenimientos/${mantenimientoId}/completar/`,
        data
      );
      console.log('✅ Mantenimiento completado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error completando mantenimiento:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // ESTADÍSTICAS Y REPORTES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene estadísticas de un consultorio
   */
  async obtenerEstadisticas(
    consultorioId: number,
    params?: {
      fecha_inicio?: string;
      fecha_fin?: string;
    }
  ): Promise<EstadisticasConsultorio> {
    try {
      const response = await api.get<EstadisticasConsultorio>(
        `/consultorios/${consultorioId}/estadisticas/`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error obteniendo estadísticas:`, error);
      throw error;
    }
  },

  /**
   * Genera reporte de uso de consultorios
   */
  async generarReporteUso(params?: {
    fecha_inicio?: string;
    fecha_fin?: string;
    consultorio?: number;
  }): Promise<any> {
    try {
      const response = await api.get('/consultorios/reporte-uso/', { params });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error generando reporte:', error);
      throw error;
    }
  },

  /**
   * Exporta reporte a PDF
   */
  async exportarReportePDF(params?: Record<string, any>): Promise<Blob> {
    try {
      const response = await api.get('/consultorios/reporte-pdf/', {
        params,
        responseType: 'blob'
      });
      console.log('✅ Reporte PDF generado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error exportando PDF:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // BÚSQUEDAS Y FILTROS ESPECÍFICOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Buscar consultorio por código
   */
  async buscarPorCodigo(codigo: string): Promise<Consultorio | null> {
    try {
      const consultorios = await this.listar();
      const consultorio = consultorios.find(c => c.codigo === codigo);
      return consultorio || null;
    } catch (error: any) {
      console.error('❌ Error buscando por código:', error);
      throw error;
    }
  },

  /**
   * Obtener consultorios por piso
   */
  async obtenerPorPiso(piso: number): Promise<Consultorio[]> {
    return this.listar({ piso });
  },

  /**
   * Obtener consultorios por tipo
   */
  async obtenerPorTipo(tipo: TipoConsultorio): Promise<Consultorio[]> {
    return this.listar({ tipo });
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CAMBIOS DE ESTADO
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Marca consultorio como disponible
   */
  async marcarDisponible(consultorioId: number): Promise<Consultorio> {
    return this.actualizarParcial(consultorioId, { estado: 'disponible' });
  },

  /**
   * Marca consultorio como ocupado
   */
  async marcarOcupado(consultorioId: number): Promise<Consultorio> {
    return this.actualizarParcial(consultorioId, { estado: 'ocupado' });
  },

  /**
   * Marca consultorio en mantenimiento
   */
  async marcarMantenimiento(consultorioId: number): Promise<Consultorio> {
    return this.actualizarParcial(consultorioId, { estado: 'mantenimiento' });
  },

  /**
   * Marca consultorio en limpieza
   */
  async marcarLimpieza(consultorioId: number): Promise<Consultorio> {
    return this.actualizarParcial(consultorioId, { estado: 'limpieza' });
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // VALIDACIONES Y UTILIDADES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Valida datos de consultorio
   */
  validarDatosConsultorio(data: Partial<Consultorio>): {
    valido: boolean;
    errores: string[];
  } {
    const errores: string[] = [];

    if (!data.codigo) {
      errores.push('El código del consultorio es obligatorio');
    }

    if (!data.nombre) {
      errores.push('El nombre del consultorio es obligatorio');
    }

    if (!data.tipo) {
      errores.push('El tipo de consultorio es obligatorio');
    }

    if (data.capacidad && data.capacidad < 1) {
      errores.push('La capacidad debe ser mayor a 0');
    }

    return {
      valido: errores.length === 0,
      errores
    };
  },

  /**
   * Calcula duración entre horas
   */
  calcularDuracionMinutos(horaInicio: string, horaFin: string): number {
    const [horaI, minI] = horaInicio.split(':').map(Number);
    const [horaF, minF] = horaFin.split(':').map(Number);

    const minutosInicio = horaI * 60 + minI;
    const minutosFin = horaF * 60 + minF;

    return minutosFin - minutosInicio;
  },

  /**
   * Verifica si hay conflicto de horarios
   */
  hayConflictoHorarios(
    hora1Inicio: string,
    hora1Fin: string,
    hora2Inicio: string,
    hora2Fin: string
  ): boolean {
    const [h1i, m1i] = hora1Inicio.split(':').map(Number);
    const [h1f, m1f] = hora1Fin.split(':').map(Number);
    const [h2i, m2i] = hora2Inicio.split(':').map(Number);
    const [h2f, m2f] = hora2Fin.split(':').map(Number);

    const min1i = h1i * 60 + m1i;
    const min1f = h1f * 60 + m1f;
    const min2i = h2i * 60 + m2i;
    const min2f = h2f * 60 + m2f;

    // Hay conflicto si se superponen
    return !(min1f <= min2i || min2f <= min1i);
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTACIONES
// ═══════════════════════════════════════════════════════════════════════════


