/**
 * ==================================================================================
 * CITAS SERVICE - SERVICIO COMPLETO PARA GESTIÓN DE CITAS MÉDICAS
 * ==================================================================================
 * Alineado 100% con backend Django: citas/models.py, citas/serializers.py
 * Estados: agendada, confirmada, en_espera, en_consulta, completada, cancelada, no_asistio
 * Campos: fecha_cita + hora_cita (NO fecha_hora)
 * ==================================================================================
 */

import api from './api';

// =====================================================================================
// INTERFACES - EXACTAMENTE COMO BACKEND
// =====================================================================================

interface PacienteInfo {
    id: number;
    nombre_completo: string;
    id_clinico: string;
    ci?: string;
    telefono: string;
    email: string;
    edad: number;
}

interface MedicoInfo {
    id: number;
    nombre: string;
    especialidad: string | null;
    email: string;
}

interface HistorialCita {
    id: number;
    accion: string;
    usuario_nombre: string;
    fecha: string;
    observacion: string;
}

export type EstadoCita = 'agendada' | 'confirmada' | 'en_espera' | 'en_consulta' | 'completada' | 'cancelada' | 'no_asistio';
export type TipoCita = 'primera_vez' | 'control' | 'urgencia' | 'seguimiento';

export interface Cita {
    // IDs y relaciones
    id?: number;
    paciente: number;
    paciente_info?: PacienteInfo;
    medico: number;
    medico_info?: MedicoInfo;
    consultorio?: number | null;
    _uniqueRowKey?: string;

    // Fecha y hora (SEPARADOSí, como en el backend)
    fecha_cita: string; // YYYY-MM-DD
    hora_cita: string;  // HH:MM:SS
    fecha_hora_cita?: string; // Read-only computed field del backend
    duracion?: number; // minutos, default 30
    consultorio_info?: { id: number; nombre: string; ubicacion: string };


    // Tipo y estado
    tipo_cita: TipoCita;
    tipo_cita_display?: string;
    estado: EstadoCita;
    estado_display?: string;

    // Detalles
    motivo: string;
    observaciones?: string;

    // Confirmación y seguimiento
    confirmada_por?: number | null;
    confirmada_por_nombre?: string;
    fecha_confirmacion?: string | null;
    recordatorio_enviado?: boolean;
    fecha_recordatorio?: string | null;

    //  Metadata
    creado_por?: number;
    creado_por_nombre?: string;
    fecha_creacion?: string;
    fecha_actualizacion?: string;

    // Computed fields (read-only del backend)
    esta_pendiente?: boolean;
    dias_hasta_cita?: number;
    requiere_recordatorio?: boolean;

    // Historial
    historial?: HistorialCita[];
}

export interface HorarioDisponible {
    hora: string;
    disponible: boolean;
    motivo?: string;
}

interface DisponibilidadMedico {
    fecha: string;
    medico: number;
    horarios: HorarioDisponible[];
}

// =====================================================================================
// UTILIDADES DE NORMALIZACIÓN
// =====================================================================================

/**
 * Normaliza respuestas del backend que pueden venir como array directo
 * o envueltas en un objeto con 'results', 'data', etc.
 */
function normalizeListResponse<T>(data: any): T[] {
    // Si ya es un array, retornar directo
    if (Array.isArray(data)) {
        return data as T[];
    }

    // Si tiene propiedad 'results' (paginación DRF)
    if (data?.results && Array.isArray(data.results)) {
        return data.results as T[];
    }

    // Si tiene propiedad 'data'
    if (data?.data && Array.isArray(data.data)) {
        return data.data as T[];
    }

    // Si no es ninguno de los anteriores, advertir y retornar array vacío
    console.warn('⚠️ citasService: Respuesta no es array ni tiene results/data:', data);
    return [];
}

// =====================================================================================
// API CALLS
// =====================================================================================

export const citasService = {
    /**
     * Obtener todas las citas con filtros opcionales
     */
    async getAll(params?: {
        paciente?: number;
        medico?: number;
        estado?: EstadoCita;
        fecha_desde?: string;
        fecha_hasta?: string;
        tipo_cita?: TipoCita;
    }): Promise<Cita[]> {
        try {
            const response = await api.get<Cita[] | { results: Cita[] }>('/citas/citas/', { params });
            return normalizeListResponse<Cita>(response.data);
        } catch (error) {
            console.error('Error fetching citas:', error);
            throw error;
        }
    },

    /**
     * Alias para listar (compatibilidad)
     */
    async listar(params?: any): Promise<Cita[]> {
        return this.getAll(params);
    },

    /**
     * Obtener cita por ID (con detalles completos)
     */
    async getById(id: number): Promise<Cita> {
        try {
            const response = await api.get<Cita>(`/citas/citas/${id}/`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Crear nueva cita
     */
    async create(data: Partial<Cita>): Promise<Cita> {
        try {
            const response = await api.post<Cita>('/citas/citas/', data);
            return response.data;
        } catch (error) {
            console.error('Error creating cita:', error);
            throw error;
        }
    },

    /**
     * Actualizar cita existente
     */
    async update(id: number, data: Partial<Cita>): Promise<Cita> {
        try {
            const response = await api.put<Cita>(`/citas/citas/${id}/`, data);
            return response.data;
        } catch (error) {
            console.error(`Error updating cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Eliminar cita
     */
    async delete(id: number): Promise<void> {
        try {
            await api.delete(`/citas/citas/${id}/`);
        } catch (error) {
            console.error(`Error deleting cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Confirmar cita
     */
    async confirmar(id: number): Promise<Cita> {
        try {
            const response = await api.patch<Cita>(`/citas/citas/${id}/confirmar/`, {});
            return response.data;
        } catch (error) {
            console.error(`Error confirmando cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Cancelar cita
     */
    async cancelar(id: number): Promise<Cita> {
        try {
            const response = await api.patch<Cita>(`/citas/citas/${id}/cancelar/`, {});
            return response.data;
        } catch (error) {
            console.error(`Error cancelando cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Marcar paciente presente (cambiar a en_espera)
     */
    async marcarPresente(id: number): Promise<Cita> {
        try {
            const response = await api.patch<Cita>(`/citas/citas/${id}/marcar-presente/`, {});
            return response.data;
        } catch (error) {
            console.error(`Error marcando presente cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Pasar paciente a consulta (cambiar a en_consulta)
     */
    async pasarConsulta(id: number): Promise<Cita> {
        try {
            const response = await api.post<Cita>(`/citas/citas/${id}/pasar-consulta/`);
            return response.data;
        } catch (error) {
            console.error(`Error pasando a consulta cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Completar cita
     */
    async completar(id: number): Promise<Cita> {
        try {
            const response = await api.post<Cita>(`/citas/citas/${id}/completar/`);
            return response.data;
        } catch (error) {
            console.error(`Error completando cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Obtener horarios disponibles de un médico en una fecha específica
     */
    async getHorariosDisponibles(medico: number, fecha: string): Promise<HorarioDisponible[]> {
        try {
            const response = await api.get<HorarioDisponible[]>(
                `/citas/disponibilidades/horarios-disponibles/`,
                { params: { medico_id: medico, fecha } }
            );
            return response.data;
        } catch (error) {
            console.error('Error fetching horarios disponibles:', error);
            return []; // Retornar array vacío en caso de error
        }
    },

    /**
     * Obtener disponibilidad semanal de un médico
     */
    async getDisponibilidadSemanal(medico: number, semana_inicio: string): Promise<DisponibilidadMedico[]> {
        try {
            const response = await api.get<DisponibilidadMedico[]>(
                `/citas/disponibilidades/por-medico/`,
                { params: { medico_id: medico } }
            );
            return response.data;
        } catch (error) {
            console.error('Error fetching disponibilidad semanal:', error);
            return [];
        }
    },

    /**
     * Obtener citas de hoy
     */
    async getCitasHoy(medico?: number): Promise<Cita[]> {
        try {
            const response = await api.get<Cita[]>(`/citas/citas/hoy/`, {
                params: medico ? { medico } : undefined
            });
            return response.data;
        } catch (error) {
            console.error('Error fetching citas hoy:', error);
            return [];
        }
    },

    /**
     * Obtener citas pendientes de confirmación
     */
    async getCitasPendientesConfirmacion(): Promise<Cita[]> {
        try {
            const response = await api.get<Cita[]>(`/citas/citas/pendientes/`);
            return response.data;
        } catch (error) {
            console.error('Error fetching citas pendientes:', error);
            return [];
        }
    },

    /**
     * Enviar recordatorio de cita
     */
    async enviarRecordatorio(id: number): Promise<{ success: boolean; message: string }> {
        try {
            const response = await api.post<{ success: boolean; message: string }>(
                `/citas/citas/${id}/enviar-recordatorio/`
            );
            return response.data;
        } catch (error) {
            console.error(`Error enviando recordatorio cita ${id}:`, error);
            throw error;
        }
    },

    /**
     * Reprogramar cita
     */
    async reprogramar(id: number, nueva_fecha: string, nueva_hora: string): Promise<Cita> {
        try {
            const response = await api.post<Cita>(
                `/citas/citas/${id}/reprogramar/`,
                { fecha_cita: nueva_fecha, hora_cita: nueva_hora }
            );
            return response.data;
        } catch (error) {
            console.error(`Error reprogramando cita ${id}:`, error);
            throw error;
        }
    }
};


