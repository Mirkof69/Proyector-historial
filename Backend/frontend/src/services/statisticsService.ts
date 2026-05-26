/**
 * =============================================================================
 * STATISTICS SERVICE - SERVICIO DE ESTADÍSTICAS
 * =============================================================================
 * Servicio para obtener estadísticas del sistema médico
 * =============================================================================
 */

import apiClient from './api';

export interface DashboardStats {
  total_pacientes: number;
  nuevos_pacientes: number;
  embarazos_activos: number;
  embarazos_alto_riesgo: number;
  controles_mes: number;
  citas_pendientes: number;
  citas_hoy: number;
  partos_mes: number;
}

interface EmbarazosStats {
  total_embarazos: number;
  por_riesgo: Array<{ clasificacion_riesgo: string; total: number }>;
  por_trimestre: {
    primer_trimestre: number;
    segundo_trimestre: number;
    tercer_trimestre: number;
  };
  edad_promedio: number;
  semanas_promedio?: number;
}

interface ControlesStats {
  total_controles: number;
  por_medico: Array<{ medico__nombre: string | null; medico__apellido_paterno: string | null; total: number }>;
  promedios: {
    peso_promedio: number | null;
    presion_sistolica_promedio: number | null;
    presion_diastolica_promedio: number | null;
  };
  controles_diarios: Array<{ fecha: string; total: number }>;
}

interface CitasStats {
  total_citas: number;
  por_estado: Array<{ estado: string; total: number }>;
  por_tipo: Array<{ tipo_cita: string; total: number }>;
  completadas: number;
  canceladas: number;
  no_asistidas: number;
  tasa_asistencia: number;
  tasa_cancelacion: number;
}

interface PartosStats {
  total_partos: number;
  por_tipo: Array<{ tipo_parto: string; total: number }>;
  por_atencion: Array<{ tipo_atencion: string; total: number }>;
  con_complicaciones: number;
  sin_complicaciones: number;
  promedios: {
    peso_promedio: number | null;
    talla_promedio: number | null;
    apgar_1_promedio: number | null;
    apgar_5_promedio: number | null;
  };
  partos_mensuales: Array<{ mes: string; total: number }>;
}

interface AllStatistics {
  dashboard: DashboardStats;
  embarazos: EmbarazosStats;
  controles: ControlesStats;
  citas: CitasStats;
  partos: PartosStats;
}

interface StatisticsFilters {
  start_date?: string;
  end_date?: string;
}

class StatisticsService {
  private baseURL = '/reportes/statistics/';

  async getDashboardStatistics(filters?: StatisticsFilters): Promise<DashboardStats> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<DashboardStats>(
      `${this.baseURL}dashboard/?${params.toString()}`
    );
    return response.data;
  }

  async getEmbarazosStatistics(filters?: StatisticsFilters): Promise<EmbarazosStats> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<EmbarazosStats>(
      `${this.baseURL}embarazos/?${params.toString()}`
    );
    return response.data;
  }

  async getControlesStatistics(filters?: StatisticsFilters): Promise<ControlesStats> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<ControlesStats>(
      `${this.baseURL}controles/?${params.toString()}`
    );
    return response.data;
  }

  async getCitasStatistics(filters?: StatisticsFilters): Promise<CitasStats> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<CitasStats>(
      `${this.baseURL}citas/?${params.toString()}`
    );
    return response.data;
  }

  async getPartosStatistics(filters?: StatisticsFilters): Promise<PartosStats> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<PartosStats>(
      `${this.baseURL}partos/?${params.toString()}`
    );
    return response.data;
  }

  async getAllStatistics(filters?: StatisticsFilters): Promise<AllStatistics> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get<AllStatistics>(
      `${this.baseURL}all/?${params.toString()}`
    );
    return response.data;
  }

  async downloadPDF(filters?: StatisticsFilters): Promise<Blob> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);

    const response = await apiClient.get(
      `${this.baseURL}download-pdf/?${params.toString()}`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }
}

const statisticsService = new StatisticsService();

export default statisticsService;
