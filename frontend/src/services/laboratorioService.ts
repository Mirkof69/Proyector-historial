/**
 * =============================================================================
 * SERVICIO DE LABORATORIO
 * =============================================================================
 * CRUD completo de exámenes de laboratorio
 * =============================================================================
 */

import api from './api';
import { PaginatedResponse } from '../types';

export interface ExamenLaboratorio {
  id: number;
  embarazo: number;
  embarazo_nombre?: string;
  paciente_nombre?: string;
  fecha_solicitud: string;
  fecha_resultado?: string;
  tipo_examen: string;
  estado: string;
  hemoglobina?: number;
  hematocrito?: number;
  leucocitos?: number;
  plaquetas?: number;
  glucosa?: number;
  grupo_sanguineo?: string;
  factor_rh?: string;
  vdrl?: string;
  vih?: string;
  hepatitis_b?: string;
  toxoplasmosis?: string;
  rubeola?: string;
  urea?: number;
  creatinina?: number;
  acido_urico?: number;
  proteinas_totales?: number;
  albumina?: number;
  tgo?: number;
  tgp?: number;
  orina_color?: string;
  orina_aspecto?: string;
  orina_ph?: number;
  orina_densidad?: number;
  orina_glucosa?: string;
  orina_proteinas?: string;
  orina_leucocitos?: string;
  orina_hematies?: string;
  cultivo_resultado?: string;
  cultivo_germen?: string;
  cultivo_antibiograma?: string;
  observaciones?: string;
  archivo_resultado?: string;
  medico_solicitante: number;
  medico_nombre?: string;
  laboratorio?: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface ExamenLaboratorioForm {
  embarazo: number;
  fecha_solicitud: string;
  fecha_resultado?: string;
  tipo_examen: string;
  estado?: string;
  hemoglobina?: number;
  hematocrito?: number;
  leucocitos?: number;
  plaquetas?: number;
  glucosa?: number;
  grupo_sanguineo?: string;
  factor_rh?: string;
  vdrl?: string;
  vih?: string;
  hepatitis_b?: string;
  toxoplasmosis?: string;
  rubeola?: string;
  urea?: number;
  creatinina?: number;
  acido_urico?: number;
  proteinas_totales?: number;
  albumina?: number;
  tgo?: number;
  tgp?: number;
  orina_color?: string;
  orina_aspecto?: string;
  orina_ph?: number;
  orina_densidad?: number;
  orina_glucosa?: string;
  orina_proteinas?: string;
  orina_leucocitos?: string;
  orina_hematies?: string;
  cultivo_resultado?: string;
  cultivo_germen?: string;
  cultivo_antibiograma?: string;
  observaciones?: string;
  archivo_resultado?: File;
  laboratorio?: string;
}

class LaboratorioService {
  /**
   * Listar exámenes con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    embarazo?: number;
    tipo_examen?: string;
    estado?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<ExamenLaboratorio>> {
    const response = await api.get<PaginatedResponse<ExamenLaboratorio>>('/laboratorio/', { params });
    return response.data;
  }

  /**
   * Obtener un examen por ID
   */
  async get(id: number): Promise<ExamenLaboratorio> {
    const response = await api.get<ExamenLaboratorio>(`/laboratorio/${id}/`);
    return response.data;
  }

  /**
   * Crear nuevo examen
   */
  async create(data: ExamenLaboratorioForm): Promise<ExamenLaboratorio> {
    const formData = new FormData();

    Object.keys(data).forEach(key => {
      const value = (data as any)[key];
      if (value !== null && value !== undefined) {
        if (key === 'archivo_resultado' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, String(value));
        }
      }
    });

    const response = await api.post<ExamenLaboratorio>('/laboratorio/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Actualizar examen
   */
  async update(id: number, data: Partial<ExamenLaboratorioForm>): Promise<ExamenLaboratorio> {
    const formData = new FormData();

    Object.keys(data).forEach(key => {
      const value = (data as any)[key];
      if (value !== null && value !== undefined) {
        if (key === 'archivo_resultado' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, String(value));
        }
      }
    });

    const response = await api.patch<ExamenLaboratorio>(`/laboratorio/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Eliminar examen
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/laboratorio/${id}/`);
  }

  /**
   * Obtener exámenes por embarazo
   */
  async getByEmbarazo(embarazoId: number): Promise<ExamenLaboratorio[]> {
    const response = await api.get<ExamenLaboratorio[]>(`/laboratorio/por-embarazo/${embarazoId}/`);
    return response.data;
  }

  /**
   * Obtener estadísticas
   */
  async getEstadisticas(): Promise<any> {
    const response = await api.get('/laboratorio/estadisticas/');
    return response.data;
  }

  /**
   * Descargar archivo de resultado
   */
  async downloadResultado(id: number): Promise<Blob> {
    const response = await api.get(`/laboratorio/${id}/archivo/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Marcar como completado
   */
  async marcarCompletado(id: number, data: { fecha_resultado: string }): Promise<ExamenLaboratorio> {
    const response = await api.post<ExamenLaboratorio>(`/laboratorio/${id}/completar/`, data);
    return response.data;
  }
}

export const laboratorioService = new LaboratorioService();
export default laboratorioService;
