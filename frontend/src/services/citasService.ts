/**
 * =============================================================================
 * SERVICIO DE CITAS
 * =============================================================================
 * CRUD completo de citas médicas
 * =============================================================================
 */

import api from './api';
import { PaginatedResponse } from '../types';

export interface Cita {
  id: number;
  paciente: number;
  paciente_nombre?: string;
  embarazo?: number;
  embarazo_nombre?: string;
  medico: number;
  medico_nombre?: string;
  fecha_hora: string;
  duracion_minutos: number;
  tipo_cita: string;
  motivo: string;
  estado: string;
  observaciones?: string;
  sala?: string;
  confirmada: boolean;
  fecha_confirmacion?: string;
  recordatorio_enviado: boolean;
  notas_medicas?: string;
  proxima_cita?: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface CitaForm {
  paciente: number;
  embarazo?: number;
  medico: number;
  fecha_hora: string;
  duracion_minutos?: number;
  tipo_cita: string;
  motivo: string;
  estado?: string;
  observaciones?: string;
  sala?: string;
  notas_medicas?: string;
  proxima_cita?: string;
}

class CitasService {
  /**
   * Listar citas con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    paciente?: number;
    medico?: number;
    estado?: string;
    tipo_cita?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<Cita>> {
    const response = await api.get<PaginatedResponse<Cita>>('/citas/', { params });
    return response.data;
  }

  /**
   * Obtener una cita por ID
   */
  async get(id: number): Promise<Cita> {
    const response = await api.get<Cita>(`/citas/${id}/`);
    return response.data;
  }

  /**
   * Crear nueva cita
   */
  async create(data: CitaForm): Promise<Cita> {
    const response = await api.post<Cita>('/citas/', data);
    return response.data;
  }

  /**
   * Actualizar cita
   */
  async update(id: number, data: Partial<CitaForm>): Promise<Cita> {
    const response = await api.patch<Cita>(`/citas/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar cita
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/citas/${id}/`);
  }

  /**
   * Confirmar cita
   */
  async confirmar(id: number): Promise<Cita> {
    const response = await api.post<Cita>(`/citas/${id}/confirmar/`);
    return response.data;
  }

  /**
   * Cancelar cita
   */
  async cancelar(id: number, motivo?: string): Promise<Cita> {
    const response = await api.post<Cita>(`/citas/${id}/cancelar/`, { motivo });
    return response.data;
  }

  /**
   * Completar cita
   */
  async completar(id: number, notas?: string): Promise<Cita> {
    const response = await api.post<Cita>(`/citas/${id}/completar/`, { notas_medicas: notas });
    return response.data;
  }

  /**
   * Obtener citas del día
   */
  async getCitasHoy(): Promise<Cita[]> {
    const response = await api.get<Cita[]>('/citas/hoy/');
    return response.data;
  }

  /**
   * Obtener citas pendientes
   */
  async getCitasPendientes(): Promise<Cita[]> {
    const response = await api.get<Cita[]>('/citas/pendientes/');
    return response.data;
  }

  /**
   * Obtener disponibilidad de médico
   */
  async getDisponibilidad(medicoId: number, fecha: string): Promise<any> {
    const response = await api.get(`/citas/disponibilidad/`, {
      params: { medico: medicoId, fecha },
    });
    return response.data;
  }

  /**
   * Enviar recordatorio
   */
  async enviarRecordatorio(id: number): Promise<void> {
    await api.post(`/citas/${id}/enviar-recordatorio/`);
  }

  /**
   * Obtener estadísticas
   */
  async getEstadisticas(): Promise<any> {
    const response = await api.get('/citas/estadisticas/');
    return response.data;
  }

  /**
   * Obtener citas por paciente
   */
  async getByPaciente(pacienteId: number): Promise<Cita[]> {
    const response = await api.get<Cita[]>(`/citas/por-paciente/${pacienteId}/`);
    return response.data;
  }

  /**
   * Obtener citas por médico
   */
  async getByMedico(medicoId: number, fecha?: string): Promise<Cita[]> {
    const response = await api.get<Cita[]>(`/citas/por-medico/${medicoId}/`, {
      params: { fecha },
    });
    return response.data;
  }
}

export const citasService = new CitasService();
export default citasService;
