/**
 * =============================================================================
 * SERVICIO DE EMBARAZOS
 * =============================================================================
 * CRUD y gestión de embarazos
 * =============================================================================
 */

import api from './api';
import { Embarazo, EmbarazoForm, Complicacion, PaginatedResponse } from '../types';

class EmbarazosService {
  /**
   * Listar embarazos con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    paciente?: number;
    estado?: string;
    alto_riesgo?: boolean;
  }): Promise<PaginatedResponse<Embarazo>> {
    const response = await api.get<PaginatedResponse<Embarazo>>('/embarazos/', { params });
    return response.data;
  }

  /**
   * Obtener un embarazo por ID
   */
  async get(id: number): Promise<Embarazo> {
    const response = await api.get<Embarazo>(`/embarazos/${id}/`);
    return response.data;
  }

  /**
   * Crear un nuevo embarazo
   */
  async create(data: EmbarazoForm): Promise<Embarazo> {
    const response = await api.post<Embarazo>('/embarazos/', data);
    return response.data;
  }

  /**
   * Actualizar embarazo
   */
  async update(id: number, data: Partial<EmbarazoForm>): Promise<Embarazo> {
    const response = await api.patch<Embarazo>(`/embarazos/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar embarazo (soft delete)
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/embarazos/${id}/`);
  }

  /**
   * Listar embarazos activos
   */
  async listActivos(): Promise<Embarazo[]> {
    const response = await api.get<Embarazo[]>('/embarazos/activos/');
    return response.data;
  }

  /**
   * Listar embarazos de alto riesgo
   */
  async listAltoRiesgo(): Promise<Embarazo[]> {
    const response = await api.get<Embarazo[]>('/embarazos/alto-riesgo/');
    return response.data;
  }

  /**
   * Obtener embarazos por paciente
   */
  async getByPaciente(pacienteId: number): Promise<Embarazo[]> {
    const response = await api.get<Embarazo[]>(`/embarazos/por-paciente/${pacienteId}/`);
    return response.data;
  }

  /**
   * Finalizar embarazo
   */
  async finalizar(id: number, data: {
    tipo_finalizacion: string;
    fecha_finalizacion: string;
    resultado?: string;
  }): Promise<Embarazo> {
    const response = await api.post<Embarazo>(`/embarazos/${id}/finalizar/`, data);
    return response.data;
  }

  /**
   * Marcar como alto riesgo
   */
  async marcarAltoRiesgo(id: number, factoresRiesgo: string): Promise<Embarazo> {
    const response = await api.post<Embarazo>(`/embarazos/${id}/marcar-alto-riesgo/`, {
      factores_riesgo: factoresRiesgo,
    });
    return response.data;
  }

  /**
   * Agregar complicación
   */
  async addComplicacion(embarazoId: number, data: Partial<Complicacion>): Promise<Complicacion> {
    const response = await api.post<Complicacion>('/complicaciones/', {
      ...data,
      embarazo: embarazoId,
    });
    return response.data;
  }

  /**
   * Actualizar complicación
   */
  async updateComplicacion(id: number, data: Partial<Complicacion>): Promise<Complicacion> {
    const response = await api.patch<Complicacion>(`/complicaciones/${id}/`, data);
    return response.data;
  }

  /**
   * Resolver complicación
   */
  async resolverComplicacion(id: number): Promise<Complicacion> {
    const response = await api.post<Complicacion>(`/complicaciones/${id}/resolver/`);
    return response.data;
  }

  /**
   * Estadísticas de embarazos
   */
  async statistics(): Promise<any> {
    const response = await api.get('/embarazos/estadisticas/');
    return response.data;
  }

  /**
   * Exportar a CSV
   */
  async exportCSV(params?: any): Promise<Blob> {
    const response = await api.get('/embarazos/exportar-csv/', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }
}

export const embarazosService = new EmbarazosService();
export default embarazosService;
