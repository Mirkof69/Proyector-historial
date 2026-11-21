/**
 * =============================================================================
 * SERVICIO DE TICKETS DE SOPORTE TÉCNICO
 * =============================================================================
 */
import api from './api';

export interface TicketSoporte {
  id: number;
  usuario?: number;
  usuario_nombre?: string | null;
  asunto: string;
  modulo: 'login' | 'pacientes' | 'controles' | 'reportes' | 'otro';
  modulo_display?: string;
  prioridad: 'baja' | 'media' | 'alta';
  prioridad_display?: string;
  descripcion: string;
  estado: 'abierto' | 'en_proceso' | 'resuelto' | 'cerrado';
  estado_display?: string;
  respuesta_admin?: string;
  fecha_creacion: string;
  fecha_resolucion?: string;
}

function normalizeListResponse<T>(data: any): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data?.results && Array.isArray(data.results)) return data.results as T[];
  return [];
}

export const soporteService = {
  /**
   * Crea un nuevo ticket de soporte (cualquier usuario autenticado)
   */
  async crearTicket(payload: {
    asunto: string;
    modulo: string;
    prioridad: string;
    descripcion: string;
  }): Promise<TicketSoporte> {
    const response = await api.post<TicketSoporte>('/soporte/tickets/', payload);
    return response.data;
  },

  /**
   * Lista los tickets del usuario actual (o todos, si es administrador)
   */
  async listarTickets(): Promise<TicketSoporte[]> {
    const response = await api.get<TicketSoporte[]>('/soporte/tickets/');
    return normalizeListResponse<TicketSoporte>(response.data);
  },
};
