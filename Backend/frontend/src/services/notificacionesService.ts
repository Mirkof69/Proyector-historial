/**
 * =============================================================================
 * SERVICIO DE NOTIFICACIONES
 * =============================================================================
 * Sistema de notificaciones del sistema
 * =============================================================================
 */

import api from './api';

export interface Notificacion {
  id: number;
  usuario?: number;
  tipo: 'info' | 'warning' | 'success' | 'error';
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
  fecha_lectura?: string;
  url?: string;
  datos_adicionales?: any;
}

// Función de normalización
function normalizeListResponse<T>(data: any): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data?.results && Array.isArray(data.results)) return data.results as T[];
  if (data?.data && Array.isArray(data.data)) return data.data as T[];
  console.warn('⚠️ notificacionesService: Respuesta no es array:', data);
  return [];
}

export const notificacionesService = {
  async listar(): Promise<Notificacion[]> {
    try {
      const response = await api.get<Notificacion[]>('/notificaciones/');
      return normalizeListResponse<Notificacion>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando notificaciones:', error);
      // Devolver array vacío en caso de error
      return [];
    }
  },

  async obtener(id: number) {
    const response = await api.get(`/notificaciones/${id}/`);
    return response.data;
  },

  async crear(data: any) {
    const response = await api.post('/notificaciones/', data);
    return response.data;
  },

  async actualizar(id: number, data: any) {
    const response = await api.put(`/notificaciones/${id}/`, data);
    return response.data;
  },

  async eliminar(id: number) {
    await api.delete(`/notificaciones/${id}/`);
  },

  async marcarLeida(id: number) {
    const response = await api.patch(`/notificaciones/${id}/`, { leida: true });
    return response.data;
  },

  async marcarTidasPorTipo(tipo: string) {
    // Backend does not expose a marcar_leidas_por_tipo endpoint.
    // Filter client-side or use the bulk mark-all endpoint.
    console.warn('marcarTidasPorTipo: endpoint no disponible en backend; se ignora silenciosamente');
    return {};
  },

  async obtenerNoLeidas() {
    // Backend exposes /notificaciones/no_leidas/ (underscore, GET)
    const response = await api.get('/notificaciones/no_leidas/');
    return response.data;
  },

  async enviarAlerta(data: any) {
    // No dedicated /enviar_alerta/ endpoint; use POST /notificaciones/ directly
    const response = await api.post('/notificaciones/', data);
    return response.data;
  },

  async obtenerPorCanal(canal: string) {
    // El modelo Notificacion no tiene campo 'canal'; usar entidad_tipo como sustituto.
    const response = await api.get(`/notificaciones/?entidad_tipo=${canal}`);
    return response.data;
  },

  /**
   * Agrupar notificaciones por tipo — no existe endpoint dedicado,
   * se obtienen todas y se agrupan en cliente.
   */
  async agruparPorTipo(): Promise<Record<string, Notificacion[]>> {
    try {
      const response = await api.get('/notificaciones/');
      const lista: Notificacion[] = normalizeListResponse<Notificacion>(response.data);
      return lista.reduce((acc, n) => {
        if (!acc[n.tipo]) acc[n.tipo] = [];
        acc[n.tipo].push(n);
        return acc;
      }, {} as Record<string, Notificacion[]>);
    } catch (error: any) {
      console.error('Error agrupando notificaciones:', error);
      return {};
    }
  },

  /**
   * Marcar todas las notificaciones como leídas.
   * Backend URL: POST /notificaciones/marcar_todas_leidas/ (underscore)
   */
  async marcarTodasLeidas(): Promise<{ marcadas: number }> {
    try {
      const response = await api.post('/notificaciones/marcar_todas_leidas/');
      return { marcadas: response.data?.count ?? 0 };
    } catch (error: any) {
      console.error('Error marcando todas como leídas:', error);
      throw error;
    }
  },

  /**
   * Obtener preferencias de notificaciones del usuario.
   * Backend URL: GET /configuracion-notificaciones/mi_configuracion/
   */
  async obtenerPreferencias(): Promise<{
    recibir_push: boolean;
    recibir_email: boolean;
    recibir_sms: boolean;
    notificar_citas: boolean;
    notificar_examenes: boolean;
    notificar_alertas: boolean;
    notificar_mensajes: boolean;
    notificar_documentos: boolean;
    recordatorio_citas_horas: number;
    recordatorio_controles: boolean;
    no_molestar_inicio?: string;
    no_molestar_fin?: string;
  }> {
    try {
      const response = await api.get('/configuracion-notificaciones/mi_configuracion/');
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo preferencias:', error);
      throw error;
    }
  },

  /**
   * Actualizar preferencias de notificaciones.
   * Backend URL: PATCH /configuracion-notificaciones/mi_configuracion/
   */
  async actualizarPreferencias(preferencias: any): Promise<any> {
    try {
      const response = await api.patch('/configuracion-notificaciones/mi_configuracion/', preferencias);
      return response.data;
    } catch (error: any) {
      console.error('Error actualizando preferencias:', error);
      throw error;
    }
  },

  /**
   * Obtener estadísticas de notificaciones.
   * Backend URL: GET /notificaciones/estadisticas/
   */
  async obtenerEstadisticas(): Promise<{
    total: number;
    no_leidas: number;
    por_tipo: Record<string, number>;
    por_prioridad: Record<string, number>;
    leidas_hoy: number;
    recibidas_hoy: number;
  }> {
    try {
      const response = await api.get('/notificaciones/estadisticas/');
      return response.data;
    } catch (error: any) {
      console.error('Error obteniendo estadísticas:', error);
      throw error;
    }
  },

  /**
   * Archivar notificación.
   * Backend URL: POST /notificaciones/{id}/archivar/
   */
  async archivar(id: number): Promise<any> {
    try {
      const response = await api.post(`/notificaciones/${id}/archivar/`);
      return response.data;
    } catch (error: any) {
      console.error('Error archivando notificación:', error);
      throw error;
    }
  },

  /**
   * Buscar notificaciones — no existe /notificaciones/buscar/ en backend.
   * Se filtra con el query param `search` que DRF SearchFilter expone.
   */
  async buscar(query: string, filtros?: {
    tipo?: string;
    prioridad?: string;
    desde?: string;
    hasta?: string;
  }): Promise<Notificacion[]> {
    try {
      const response = await api.get('/notificaciones/', {
        params: { search: query, ...filtros }
      });
      return normalizeListResponse<Notificacion>(response.data);
    } catch (error: any) {
      console.error('Error buscando notificaciones:', error);
      return [];
    }
  },
};
