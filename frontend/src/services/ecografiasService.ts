/**
 * =============================================================================
 * SERVICIO DE ECOGRAFÍAS
 * =============================================================================
 * CRUD completo de ecografías obstétricas
 * =============================================================================
 */

import api from './api';
import { PaginatedResponse } from '../types';

export interface Ecografia {
  id: number;
  embarazo: number;
  embarazo_nombre?: string;
  paciente_nombre?: string;
  fecha_ecografia: string;
  tipo_ecografia: string;
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  peso_fetal_estimado?: number;
  longitud_cefalocaudal?: number;
  diametro_biparietal?: number;
  circunferencia_cefalica?: number;
  circunferencia_abdominal?: number;
  longitud_femur?: number;
  placenta_localizacion?: string;
  placenta_grado?: string;
  liquido_amniotico?: string;
  indice_liquido_amniotico?: number;
  numero_fetos: number;
  presentacion_fetal?: string;
  sexo_fetal?: string;
  latidos_cardiacos: boolean;
  frecuencia_cardiaca?: number;
  movimientos_fetales: boolean;
  anatomia_normal: boolean;
  hallazgos?: string;
  observaciones?: string;
  imagen?: string;
  medico: number;
  medico_nombre?: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface EcografiaForm {
  embarazo: number;
  fecha_ecografia: string;
  tipo_ecografia: string;
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  peso_fetal_estimado?: number;
  longitud_cefalocaudal?: number;
  diametro_biparietal?: number;
  circunferencia_cefalica?: number;
  circunferencia_abdominal?: number;
  longitud_femur?: number;
  placenta_localizacion?: string;
  placenta_grado?: string;
  liquido_amniotico?: string;
  indice_liquido_amniotico?: number;
  numero_fetos?: number;
  presentacion_fetal?: string;
  sexo_fetal?: string;
  latidos_cardiacos: boolean;
  frecuencia_cardiaca?: number;
  movimientos_fetales: boolean;
  anatomia_normal: boolean;
  hallazgos?: string;
  observaciones?: string;
  imagen?: File;
}

class EcografiasService {
  /**
   * Listar ecografías con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    embarazo?: number;
    tipo_ecografia?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<Ecografia>> {
    const response = await api.get<PaginatedResponse<Ecografia>>('/ecografias/', { params });
    return response.data;
  }

  /**
   * Obtener una ecografía por ID
   */
  async get(id: number): Promise<Ecografia> {
    const response = await api.get<Ecografia>(`/ecografias/${id}/`);
    return response.data;
  }

  /**
   * Crear nueva ecografía
   */
  async create(data: EcografiaForm): Promise<Ecografia> {
    const formData = new FormData();

    Object.keys(data).forEach(key => {
      const value = (data as any)[key];
      if (value !== null && value !== undefined) {
        if (key === 'imagen' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, String(value));
        }
      }
    });

    const response = await api.post<Ecografia>('/ecografias/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Actualizar ecografía
   */
  async update(id: number, data: Partial<EcografiaForm>): Promise<Ecografia> {
    const formData = new FormData();

    Object.keys(data).forEach(key => {
      const value = (data as any)[key];
      if (value !== null && value !== undefined) {
        if (key === 'imagen' && value instanceof File) {
          formData.append(key, value);
        } else {
          formData.append(key, String(value));
        }
      }
    });

    const response = await api.patch<Ecografia>(`/ecografias/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  /**
   * Eliminar ecografía
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/ecografias/${id}/`);
  }

  /**
   * Obtener ecografías por embarazo
   */
  async getByEmbarazo(embarazoId: number): Promise<Ecografia[]> {
    const response = await api.get<Ecografia[]>(`/ecografias/por-embarazo/${embarazoId}/`);
    return response.data;
  }

  /**
   * Obtener estadísticas de ecografías
   */
  async getEstadisticas(): Promise<any> {
    const response = await api.get('/ecografias/estadisticas/');
    return response.data;
  }

  /**
   * Descargar imagen de ecografía
   */
  async downloadImagen(id: number): Promise<Blob> {
    const response = await api.get(`/ecografias/${id}/imagen/`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const ecografiasService = new EcografiasService();
export default ecografiasService;
