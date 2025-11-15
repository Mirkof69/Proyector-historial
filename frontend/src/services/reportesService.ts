/**
 * =============================================================================
 * SERVICIO DE REPORTES
 * =============================================================================
 * Generación y gestión de reportes médicos
 * =============================================================================
 */

import api from './api';
import { PaginatedResponse } from '../types';

export interface Reporte {
  id: number;
  tipo_reporte: string;
  titulo: string;
  descripcion?: string;
  fecha_generacion: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  parametros?: any;
  archivo?: string;
  formato: string;
  estado: string;
  generado_por: number;
  generado_por_nombre?: string;
  paciente?: number;
  paciente_nombre?: string;
  embarazo?: number;
  embarazo_nombre?: string;
  tamano_bytes?: number;
  activo: boolean;
  fecha_creacion?: string;
}

export interface ReporteForm {
  tipo_reporte: string;
  titulo: string;
  descripcion?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  parametros?: any;
  formato?: string;
  paciente?: number;
  embarazo?: number;
}

export interface ParametrosReporteEstadistico {
  fecha_desde: string;
  fecha_hasta: string;
  tipo_estadistica: string;
  incluir_graficos?: boolean;
}

export interface ParametrosReporteHistorialPaciente {
  paciente_id: number;
  incluir_embarazos?: boolean;
  incluir_controles?: boolean;
  incluir_laboratorios?: boolean;
  incluir_ecografias?: boolean;
  incluir_partos?: boolean;
}

export interface ParametrosReporteEmbarazo {
  embarazo_id: number;
  incluir_evolucion?: boolean;
  incluir_estudios?: boolean;
  incluir_calculadoras?: boolean;
}

class ReportesService {
  /**
   * Listar reportes con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    tipo_reporte?: string;
    estado?: string;
    fecha_desde?: string;
    fecha_hasta?: string;
  }): Promise<PaginatedResponse<Reporte>> {
    const response = await api.get<PaginatedResponse<Reporte>>('/reportes/', { params });
    return response.data;
  }

  /**
   * Obtener un reporte por ID
   */
  async get(id: number): Promise<Reporte> {
    const response = await api.get<Reporte>(`/reportes/${id}/`);
    return response.data;
  }

  /**
   * Crear nuevo reporte
   */
  async create(data: ReporteForm): Promise<Reporte> {
    const response = await api.post<Reporte>('/reportes/', data);
    return response.data;
  }

  /**
   * Eliminar reporte
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/reportes/${id}/`);
  }

  /**
   * Descargar archivo de reporte
   */
  async download(id: number): Promise<Blob> {
    const response = await api.get(`/reportes/${id}/descargar/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte estadístico
   */
  async generarReporteEstadistico(params: ParametrosReporteEstadistico): Promise<Blob> {
    const response = await api.post('/reportes/estadistico/', params, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar historial completo de paciente
   */
  async generarHistorialPaciente(params: ParametrosReporteHistorialPaciente): Promise<Blob> {
    const response = await api.post('/reportes/historial-paciente/', params, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte de embarazo
   */
  async generarReporteEmbarazo(params: ParametrosReporteEmbarazo): Promise<Blob> {
    const response = await api.post('/reportes/embarazo/', params, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte de controles prenatales
   */
  async generarReporteControles(embarazoId: number): Promise<Blob> {
    const response = await api.get(`/reportes/controles/${embarazoId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte de laboratorios
   */
  async generarReporteLaboratorios(embarazoId: number): Promise<Blob> {
    const response = await api.get(`/reportes/laboratorios/${embarazoId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte de ecografías
   */
  async generarReporteEcografias(embarazoId: number): Promise<Blob> {
    const response = await api.get(`/reportes/ecografias/${embarazoId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar carnét perinatal
   */
  async generarCarnetPerinatal(embarazoId: number): Promise<Blob> {
    const response = await api.get(`/reportes/carnet-perinatal/${embarazoId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar certificado de nacimiento
   */
  async generarCertificadoNacimiento(partoId: number): Promise<Blob> {
    const response = await api.get(`/reportes/certificado-nacimiento/${partoId}/`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar reporte de alta médica
   */
  async generarAltaMedica(data: {
    paciente_id?: number;
    embarazo_id?: number;
    parto_id?: number;
    diagnosticos: string;
    tratamiento: string;
    recomendaciones: string;
  }): Promise<Blob> {
    const response = await api.post('/reportes/alta-medica/', data, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Generar planilla de citas
   */
  async generarPlanillaCitas(fecha: string, medicoId?: number): Promise<Blob> {
    const response = await api.get('/reportes/planilla-citas/', {
      params: { fecha, medico: medicoId },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Obtener estadísticas de reportes
   */
  async getEstadisticas(): Promise<any> {
    const response = await api.get('/reportes/estadisticas/');
    return response.data;
  }

  /**
   * Obtener tipos de reportes disponibles
   */
  async getTiposReportes(): Promise<any[]> {
    const response = await api.get('/reportes/tipos/');
    return response.data;
  }
}

export const reportesService = new ReportesService();
export default reportesService;
