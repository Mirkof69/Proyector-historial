/**
 * =============================================================================
 * SERVICIO DE PACIENTES
 * =============================================================================
 * CRUD y gestión de pacientes
 * =============================================================================
 */

import api from './api';
import { Paciente, PacienteForm, PaginatedResponse } from '../types';

class PacientesService {
  /**
   * Listar pacientes con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    activo?: boolean;
  }): Promise<PaginatedResponse<Paciente>> {
    const response = await api.get<PaginatedResponse<Paciente>>('/pacientes/', { params });
    return response.data;
  }

  /**
   * Obtener un paciente por ID
   */
  async get(id: number): Promise<Paciente> {
    const response = await api.get<Paciente>(`/pacientes/${id}/`);
    return response.data;
  }

  /**
   * Crear un nuevo paciente
   */
  async create(data: PacienteForm): Promise<Paciente> {
    const response = await api.post<Paciente>('/pacientes/', data);
    return response.data;
  }

  /**
   * Actualizar paciente
   */
  async update(id: number, data: Partial<PacienteForm>): Promise<Paciente> {
    const response = await api.patch<Paciente>(`/pacientes/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar paciente (soft delete)
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/pacientes/${id}/`);
  }

  /**
   * Eliminar paciente - Alias para compatibilidad
   */
  async deletePaciente(id: number): Promise<any> {
    await api.delete(`/pacientes/${id}/`);
    return { success: true, message: 'Paciente eliminado correctamente' };
  }

  /**
   * Buscar pacientes
   */
  async search(query: string): Promise<Paciente[]> {
    const response = await api.get<Paciente[]>('/pacientes/buscar/', { params: { q: query } });
    return response.data;
  }

  /**
   * Obtener historia obstétrica del paciente
   */
  async getHistoriaObstetrica(id: number): Promise<any> {
    const response = await api.get(`/pacientes/${id}/historia-obstetrica/`);
    return response.data;
  }

  /**
   * Estadísticas de pacientes
   */
  async statistics(): Promise<any> {
    const response = await api.get('/pacientes/estadisticas/');
    return response.data;
  }

  /**
   * Exportar pacientes a CSV
   */
  async exportCSV(params?: any): Promise<Blob> {
    const response = await api.get('/pacientes/exportar-csv/', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }
}

export const pacientesService = new PacientesService();
export default pacientesService;
