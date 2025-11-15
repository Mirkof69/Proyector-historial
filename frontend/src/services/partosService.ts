/**
 * =============================================================================
 * SERVICIO DE PARTOS
 * =============================================================================
 * CRUD completo de registros de partos
 * =============================================================================
 */

import api from './api';
import { PaginatedResponse } from '../types';

export interface Parto {
  id: number;
  embarazo: number;
  embarazo_nombre?: string;
  paciente_nombre?: string;
  fecha_hora_parto: string;
  tipo_parto: string;
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  presentacion: string;
  duracion_trabajo_parto_horas?: number;
  ruptura_membranas?: string;
  tiempo_ruptura_membranas_horas?: number;
  liquido_amniotico_caracteristicas?: string;
  anestesia?: string;
  episiotomia: boolean;
  desgarros: boolean;
  grado_desgarro?: string;
  alumbramiento: string;
  sangrado_ml?: number;
  complicaciones: boolean;
  descripcion_complicaciones?: string;
  apgar_1_min?: number;
  apgar_5_min?: number;
  peso_rn_gramos?: number;
  talla_rn_cm?: number;
  perimetro_cefalico_cm?: number;
  sexo_rn?: string;
  condicion_rn?: string;
  reanimacion_neonatal: boolean;
  tipo_reanimacion?: string;
  medico_atiende: number;
  medico_nombre?: string;
  personal_asistente?: string;
  hospital?: string;
  observaciones?: string;
  fecha_alta_madre?: string;
  fecha_alta_rn?: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface PartoForm {
  embarazo: number;
  fecha_hora_parto: string;
  tipo_parto: string;
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  presentacion: string;
  duracion_trabajo_parto_horas?: number;
  ruptura_membranas?: string;
  tiempo_ruptura_membranas_horas?: number;
  liquido_amniotico_caracteristicas?: string;
  anestesia?: string;
  episiotomia: boolean;
  desgarros: boolean;
  grado_desgarro?: string;
  alumbramiento: string;
  sangrado_ml?: number;
  complicaciones: boolean;
  descripcion_complicaciones?: string;
  apgar_1_min?: number;
  apgar_5_min?: number;
  peso_rn_gramos?: number;
  talla_rn_cm?: number;
  perimetro_cefalico_cm?: number;
  sexo_rn?: string;
  condicion_rn?: string;
  reanimacion_neonatal: boolean;
  tipo_reanimacion?: string;
  personal_asistente?: string;
  hospital?: string;
  observaciones?: string;
  fecha_alta_madre?: string;
  fecha_alta_rn?: string;
}

class PartosService {
  /**
   * Listar partos con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    embarazo?: number;
    tipo_parto?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<Parto>> {
    const response = await api.get<PaginatedResponse<Parto>>('/partos/', { params });
    return response.data;
  }

  /**
   * Obtener todos los partos (alias de list)
   */
  async getAll(params?: any): Promise<Parto[]> {
    const response = await this.list(params);
    return response.results;
  }

  /**
   * Obtener un parto por ID
   */
  async get(id: number): Promise<Parto> {
    const response = await api.get<Parto>(`/partos/${id}/`);
    return response.data;
  }

  /**
   * Crear nuevo registro de parto
   */
  async create(data: PartoForm): Promise<Parto> {
    const response = await api.post<Parto>('/partos/', data);
    return response.data;
  }

  /**
   * Actualizar registro de parto
   */
  async update(id: number, data: Partial<PartoForm>): Promise<Parto> {
    const response = await api.patch<Parto>(`/partos/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar registro de parto
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/partos/${id}/`);
  }

  /**
   * Obtener parto por embarazo
   */
  async getByEmbarazo(embarazoId: number): Promise<Parto | null> {
    try {
      const response = await api.get<Parto>(`/partos/por-embarazo/${embarazoId}/`);
      return response.data;
    } catch (error) {
      return null;
    }
  }

  /**
   * Obtener estadísticas de partos
   */
  async getEstadisticas(): Promise<any> {
    const response = await api.get('/partos/estadisticas/');
    return response.data;
  }

  /**
   * Generar reporte de parto en PDF
   */
  async generarReportePDF(id: number): Promise<Blob> {
    const response = await api.get(`/partos/${id}/reporte-pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Obtener partos recientes
   */
  async getRecientes(limit: number = 10): Promise<Parto[]> {
    const response = await api.get<Parto[]>('/partos/recientes/', {
      params: { limit },
    });
    return response.data;
  }
}

export const partosService = new PartosService();
export default partosService;
