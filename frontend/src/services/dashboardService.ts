/**
 * =============================================================================
 * SERVICIO DE DASHBOARD Y ESTADÍSTICAS
 * =============================================================================
 * Obtiene datos estadísticos y métricas en tiempo real del sistema
 * =============================================================================
 */

import api from './api';
import {
  EstadisticasGenerales,
  EstadisticasPorMes,
  AlertaReciente,
} from '../types';

class DashboardService {
  /**
   * Obtener estadísticas generales del dashboard
   */
  async getEstadisticasGenerales(): Promise<EstadisticasGenerales> {
    // Hacer múltiples llamadas en paralelo para obtener todas las estadísticas
    const [pacientes, embarazos, controles] = await Promise.all([
      api.get('/pacientes/estadisticas/'),
      api.get('/embarazos/estadisticas/'),
      api.get('/controles/estadisticas/'),
    ]);

    return {
      total_pacientes: pacientes.data.total || 0,
      total_embarazos: embarazos.data.total || 0,
      embarazos_activos: embarazos.data.activos || 0,
      embarazos_alto_riesgo: embarazos.data.alto_riesgo || 0,
      controles_mes_actual: controles.data.mes_actual || 0,
      proximos_controles: controles.data.proximos || 0,
    };
  }

  /**
   * Obtener estadísticas por mes (últimos 6 meses)
   */
  async getEstadisticasPorMes(): Promise<EstadisticasPorMes[]> {
    const response = await api.get('/dashboard/estadisticas-mensuales/');
    return response.data;
  }

  /**
   * Obtener alertas recientes
   */
  async getAlertasRecientes(limit: number = 10): Promise<AlertaReciente[]> {
    const response = await api.get('/controles/con-alertas/', {
      params: { limit },
    });

    // Transformar los controles con alertas en AlertaReciente
    return response.data.map((control: any) => {
      const alerta = control.alertas?.[0];
      return {
        id: control.id,
        tipo: alerta?.tipo || 'general',
        severidad: alerta?.severidad || 'leve',
        paciente: control.paciente_nombre || 'Desconocido',
        fecha: control.fecha_control,
        mensaje: alerta?.mensaje || 'Alerta médica',
      };
    });
  }

  /**
   * Obtener próximos controles
   */
  async getProximosControles(dias: number = 7): Promise<any[]> {
    const response = await api.get('/controles/proximos-controles/', {
      params: { dias },
    });
    return response.data;
  }

  /**
   * Obtener distribución de embarazos por trimestre
   */
  async getDistribucionPorTrimestre(): Promise<any> {
    const response = await api.get('/embarazos/estadisticas/');
    return response.data.por_trimestre || {};
  }

  /**
   * Obtener embarazos de alto riesgo
   */
  async getEmbarazosAltoRiesgo(): Promise<any[]> {
    const response = await api.get('/embarazos/alto-riesgo/');
    return response.data;
  }

  /**
   * Obtener métricas de calidad de atención
   */
  async getMetricasCalidad(): Promise<any> {
    const [controles, embarazos] = await Promise.all([
      api.get('/controles/estadisticas/'),
      api.get('/embarazos/estadisticas/'),
    ]);

    return {
      promedio_controles_por_embarazo: controles.data.promedio_por_embarazo || 0,
      controles_primer_trimestre: controles.data.primer_trimestre || 0,
      controles_segundo_trimestre: controles.data.segundo_trimestre || 0,
      controles_tercer_trimestre: controles.data.tercer_trimestre || 0,
      tasa_alto_riesgo: embarazos.data.tasa_alto_riesgo || 0,
    };
  }

  /**
   * Obtener resumen de actividad reciente
   */
  async getActividadReciente(): Promise<any[]> {
    const response = await api.get('/dashboard/actividad-reciente/');
    return response.data;
  }

  /**
   * Obtener datos para gráficos
   */
  async getDatosGraficos(tipo: string, params?: any): Promise<any> {
    const response = await api.get(`/dashboard/graficos/${tipo}/`, { params });
    return response.data;
  }

  /**
   * Obtener estadísticas por usuario
   */
  async getEstadisticasPorUsuario(usuarioId?: number): Promise<any> {
    const response = await api.get('/dashboard/estadisticas-usuario/', {
      params: { usuario_id: usuarioId },
    });
    return response.data;
  }
}

export const dashboardService = new DashboardService();
export default dashboardService;
