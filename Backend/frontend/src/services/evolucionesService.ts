/**
 * =============================================================================
 * SERVICIO DE EVOLUCIONES
 * =============================================================================
 * Timeline de eventos del embarazo
 * =============================================================================
 */

import api from './api';
import { logger } from '../utils/logger';

export interface EvolucionEmbarazo {
    id?: number;
    embarazo: number;
    embarazo_info?: string;
    paciente: number;
    paciente_info?: {
        id: number;
        nombre: string;
    };
    paciente_nombre?: string;
    fecha_evento: string;
    fecha?: string; // Alias de fecha_evento
    tipo_evento: 'cita' | 'control' | 'ecografia' | 'laboratorio' | 'urgencia' | 'otro';
    tipo?: string; // Alias de tipo_evento
    estado?: 'programado' | 'realizado' | 'cancelado' | 'pendiente';
    descripcion: string;
    medico?: number;
    medico_nombre?: string;
    resumen?: string;
    diagnostico?: string;
    tratamiento?: string;
    plan?: string;
    observaciones?: string;
    signos_vitales?: any;
    examenes?: any[];
    es_urgente?: boolean;
    fecha_registro?: string;
    fecha_creacion?: string;
    fecha_actualizacion?: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface EvolucionRecord {
    id: number;
    paciente_nombre: string;
    fecha: string;
    tipo: string;
    estado: string;
    embarazo?: number;
    embarazo_info?: string;
    medico_nombre?: string;
    resumen?: string;
    diagnostico?: string;
    tratamiento?: string;
    plan?: string;
    descripcion?: string;
    signos_vitales?: any;
    examenes?: any[];
}

// Función de normalización
function normalizeListResponse<T>(data: any): T[] {
    if (Array.isArray(data)) return data as T[];
    if (data?.results && Array.isArray(data.results)) return data.results as T[];
    if (data?.data && Array.isArray(data.data)) return data.data as T[];
    console.warn('⚠️ evolucionesService: Respuesta no es array:', data);
    return [];
}

function normalizeSingleResponse<T>(data: any): T {
    if (data?.data && typeof data.data === 'object') return data.data as T;
    return data as T;
}

export const evolucionesService = {
    async listar(): Promise<EvolucionEmbarazo[]> {
        try {
            const response = await api.get<EvolucionEmbarazo[]>('/evoluciones/');
            return normalizeListResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error('❌ Error listando evoluciones:', error);
            throw error;
        }
    },

    async getAll(): Promise<EvolucionEmbarazo[]> {
        return this.listar();
    },

    async obtener(id: number): Promise<EvolucionEmbarazo> {
        try {
            const response = await api.get<EvolucionEmbarazo>(`/evoluciones/${id}/`);
            return normalizeSingleResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo evolución ${id}:`, error);
            throw error;
        }
    },

    async getById(id: number): Promise<EvolucionEmbarazo> {
        return this.obtener(id);
    },

    async crear(data: Partial<EvolucionEmbarazo>): Promise<EvolucionEmbarazo> {
        try {
            const response = await api.post<EvolucionEmbarazo>('/evoluciones/', data);
            logger.log('✅ Evolución creada');
            return normalizeSingleResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error('❌ Error creando evolución:', error);
            throw error;
        }
    },

    async create(data: Partial<EvolucionEmbarazo>): Promise<EvolucionEmbarazo> {
        return this.crear(data);
    },

    async actualizar(id: number, data: Partial<EvolucionEmbarazo>): Promise<EvolucionEmbarazo> {
        try {
            const response = await api.put<EvolucionEmbarazo>(`/evoluciones/${id}/`, data);
            logger.log(`✅ Evolución ${id} actualizada`);
            return normalizeSingleResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error actualizando evolución ${id}:`, error);
            throw error;
        }
    },

    async update(id: number, data: Partial<EvolucionEmbarazo>): Promise<EvolucionEmbarazo> {
        return this.actualizar(id, data);
    },

    async eliminar(id: number): Promise<void> {
        try {
            await api.delete(`/evoluciones/${id}/`);
            logger.log(`✅ Evolución ${id} eliminada`);
        } catch (error: any) {
            console.error(`❌ Error eliminando evolución ${id}:`, error);
            throw error;
        }
    },

    async delete(id: number): Promise<void> {
        return this.eliminar(id);
    },

    async obtenerPorPaciente(paciente_id: number): Promise<EvolucionEmbarazo[]> {
        try {
            const response = await api.get<EvolucionEmbarazo[]>(`/evoluciones/?paciente_id=${paciente_id}`);
            return normalizeListResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo evoluciones del paciente ${paciente_id}:`, error);
            throw error;
        }
    },

    async obtenerPorEmbarazo(embarazo_id: number): Promise<EvolucionEmbarazo[]> {
        try {
            const response = await api.get<EvolucionEmbarazo[]>(`/evoluciones/?embarazo_id=${embarazo_id}`);
            return normalizeListResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo evoluciones del embarazo ${embarazo_id}:`, error);
            throw error;
        }
    },

    async obtenerPorTipo(tipo: string): Promise<EvolucionEmbarazo[]> {
        try {
            const response = await api.get<EvolucionEmbarazo[]>(`/evoluciones/?tipo=${tipo}`);
            return normalizeListResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo evoluciones por tipo ${tipo}:`, error);
            throw error;
        }
    },

    async obtenerHistorial(paciente_id: number): Promise<EvolucionEmbarazo[]> {
        try {
            const response = await api.get<EvolucionEmbarazo[]>(`/evoluciones/historial/?paciente_id=${paciente_id}`);
            return normalizeListResponse<EvolucionEmbarazo>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo historial del paciente ${paciente_id}:`, error);
            throw error;
        }
    },
};
