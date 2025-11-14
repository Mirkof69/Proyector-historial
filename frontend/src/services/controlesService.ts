/**
 * =============================================================================
 * SERVICIO DE CONTROLES PRENATALES
 * =============================================================================
 * CRUD y gestión de controles prenatales con sistema de alertas
 * =============================================================================
 */

import api from './api';
import { ControlPrenatal, ControlPrenatalForm, PaginatedResponse } from '../types';

class ControlesService {
  /**
   * Listar controles con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    embarazo?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<ControlPrenatal>> {
    const response = await api.get<PaginatedResponse<ControlPrenatal>>('/controles/', { params });
    return response.data;
  }

  /**
   * Obtener un control por ID
   */
  async get(id: number): Promise<ControlPrenatal> {
    const response = await api.get<ControlPrenatal>(`/controles/${id}/`);
    return response.data;
  }

  /**
   * Crear un nuevo control
   */
  async create(data: ControlPrenatalForm): Promise<ControlPrenatal> {
    const response = await api.post<ControlPrenatal>('/controles/', data);
    return response.data;
  }

  /**
   * Actualizar control
   */
  async update(id: number, data: Partial<ControlPrenatalForm>): Promise<ControlPrenatal> {
    const response = await api.patch<ControlPrenatal>(`/controles/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar control (soft delete)
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/controles/${id}/`);
  }

  /**
   * Obtener controles por embarazo
   */
  async getByEmbarazo(embarazoId: number): Promise<ControlPrenatal[]> {
    const response = await api.get<ControlPrenatal[]>('/controles/por-embarazo/', {
      params: { embarazo_id: embarazoId },
    });
    return response.data;
  }

  /**
   * Obtener controles con alertas
   */
  async getConAlertas(params?: {
    severidad?: string;
    embarazo?: number;
  }): Promise<ControlPrenatal[]> {
    const response = await api.get<ControlPrenatal[]>('/controles/con-alertas/', { params });
    return response.data;
  }

  /**
   * Obtener alertas de un control específico
   */
  async getAlertas(controlId: number): Promise<any> {
    const response = await api.get(`/controles/${controlId}/alertas/`);
    return response.data;
  }

  /**
   * Obtener evolución de parámetros
   */
  async getEvolucion(embarazoId: number): Promise<any> {
    const response = await api.get('/controles/evolucion/', {
      params: { embarazo_id: embarazoId },
    });
    return response.data;
  }

  /**
   * Comparar dos controles
   */
  async comparar(controlId1: number, controlId2: number): Promise<any> {
    const response = await api.get('/controles/comparar/', {
      params: {
        control_id_1: controlId1,
        control_id_2: controlId2,
      },
    });
    return response.data;
  }

  /**
   * Obtener estadísticas de controles
   */
  async getEstadisticas(params?: {
    embarazo?: number;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<any> {
    const response = await api.get('/controles/estadisticas/', { params });
    return response.data;
  }

  /**
   * Obtener tendencias
   */
  async getTendencias(embarazoId: number): Promise<any> {
    const response = await api.get('/controles/tendencias/', {
      params: { embarazo_id: embarazoId },
    });
    return response.data;
  }

  /**
   * Obtener próximos controles
   */
  async getProximosControles(params?: {
    dias?: number;
  }): Promise<any[]> {
    const response = await api.get('/controles/proximos-controles/', { params });
    return response.data;
  }

  /**
   * Obtener historial completo
   */
  async getHistorialCompleto(embarazoId: number): Promise<any> {
    const response = await api.get('/controles/historial-completo/', {
      params: { embarazo_id: embarazoId },
    });
    return response.data;
  }

  /**
   * Generar reporte de paciente
   */
  async getReportePaciente(pacienteId: number): Promise<any> {
    const response = await api.get('/controles/reporte-paciente/', {
      params: { paciente_id: pacienteId },
    });
    return response.data;
  }

  /**
   * Exportar a CSV
   */
  async exportCSV(params?: any): Promise<Blob> {
    const response = await api.get('/controles/exportar-csv/', {
      params,
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Crear múltiples controles (batch)
   */
  async batchCreate(data: ControlPrenatalForm[]): Promise<ControlPrenatal[]> {
    const response = await api.post<ControlPrenatal[]>('/controles/batch-create/', data);
    return response.data;
  }
}

export const controlesService = new ControlesService();
export default controlesService;
