/**
 * ==================================================================================
 * TRIAJE SERVICE - SERVICIO COMPLETO PARA TRIAJE DE ENFERMERÍA
 * ==================================================================================
 * Alineado 100% con backend Django: triaje/models.py, triaje/serializers.py
 * Incluye: antropometría, signos vitales, evaluación inicial, alertas automáticas
 * ==================================================================================
 */

import api from './api';

// =====================================================================================
// INTERFACES - EXACTAMENTE COMO BACKEND
// =====================================================================================

interface PacienteInfo {
    id: number;
    nombre_completo: string;
    id_clinico?: string;
    ci?: string;
}

interface EnfermeraInfo {
    id: number;
    nombre: string;
}

type NivelConciencia = 'alerta' | 'somnoliento' | 'estuporoso' | 'inconsciente';

export interface TriajeEnfermeria {
    id?: number;
    paciente: number;
    paciente_info?: PacienteInfo;
    cita?: number | null;
    enfermera?: number | null;
    enfermera_info?: EnfermeraInfo;

    // Antropometría
    peso_kg: number;
    talla_cm: number;
    imc?: number;
    perimetro_abdominal_cm?: number | null;

    // Signos vitales
    presion_sistolica: number;
    presion_diastolica: number;
    temperatura: number;
    frecuencia_cardiaca: number;
    frecuencia_respiratoria: number;
    saturacion_oxigeno?: number | null;

    // Evaluación inicial
    motivo_visita: string;
    dolor_escala?: number | null;
    nivel_conciencia?: NivelConciencia;
    observaciones?: string | null;

    // Alertas automáticas (calculadas por backend)
    alerta_presion_alta?: boolean;
    alerta_fiebre?: boolean;
    alerta_taquicardia?: boolean;
    alerta_bradicardia?: boolean;
    alerta_hipertension_gestacional?: boolean;
    alerta_hipoglucemia?: boolean;

    // Campos adicionales para vista (compatibilidad con TriajeRecord)
    paciente_nombre?: string;
    estado?: 'pendiente' | 'completado' | 'cancelado';
    prioridad?: 'urgente' | 'alto' | 'normal' | 'bajo';
    fecha_hora?: string;
    motivo_consulta?: string; // Alias para motivo_visita
    presion_arterial?: string; // Formato "120/80"
    peso?: number; // Alias para peso_kg
    talla?: number; // Alias para talla_cm
    alertas?: string[];
    creado_por?: string;

    // Metadatos
    fecha_registro?: string;
    fecha_creacion?: string;
    fecha_actualizacion?: string;
}

// =====================================================================================
// UTILIDADES
// =====================================================================================

/**
 * Normaliza respuesta de lista (puede venir paginada o no)
 */
function normalizeListResponse<T>(data: any): T[] {
    if (!data) {
        return [];
    }
    if (Array.isArray(data)) {
        return data;
    }
    if (data.results && Array.isArray(data.results)) {
        return data.results;
    }
    return [];
}

// =====================================================================================
// API CALLS
// =====================================================================================

export const triajeService = {
    /**
     * Obtener todos los triajes con filtros opcionales
     */
    async listar(params?: {
        paciente?: number;
        enfermera?: number;
        fecha_desde?: string;
        fecha_hasta?: string;
    }): Promise<TriajeEnfermeria[]> {
        try {
            const response = await api.get('/triaje/triajes/', { params });
            return normalizeListResponse<TriajeEnfermeria>(response.data);
        } catch (error) {
            console.error('Error fetching triajes:', error);
            throw error;
        }
    },

    /**
     * Obtener triaje por ID (con detalles completos)
     */
    async obtener(id: number): Promise<TriajeEnfermeria> {
        try {
            const response = await api.get<TriajeEnfermeria>(`/triaje/triajes/${id}/`);
            return response.data;
        } catch (error) {
            console.error(`Error fetching triaje ${id}:`, error);
            throw error;
        }
    },

    /**
     * Crear nuevo triaje
     */
    async crear(data: Partial<TriajeEnfermeria>): Promise<TriajeEnfermeria> {
        try {
            const response = await api.post<TriajeEnfermeria>('/triaje/triajes/', data);
            return response.data;
        } catch (error) {
            console.error('Error creating triaje:', error);
            throw error;
        }
    },

    /**
     * Actualizar triaje existente
     */
    async actualizar(id: number, data: Partial<TriajeEnfermeria>): Promise<TriajeEnfermeria> {
        try {
            const response = await api.put<TriajeEnfermeria>(`/triaje/triajes/${id}/`, data);
            return response.data;
        } catch (error) {
            console.error(`Error updating triaje ${id}:`, error);
            throw error;
        }
    },

    /**
     * Eliminar triaje
     */
    async eliminar(id: number): Promise<void> {
        try {
            await api.delete(`/triaje/triajes/${id}/`);
        } catch (error) {
            console.error(`Error deleting triaje ${id}:`, error);
            throw error;
        }
    },

    /**
     * Obtener triajes por paciente
     */
    async obtenerPorPaciente(paciente_id: number): Promise<TriajeEnfermeria[]> {
        try {
            const response = await api.get(`/triaje/triajes/?paciente_id=${paciente_id}`);
            return normalizeListResponse<TriajeEnfermeria>(response.data);
        } catch (error) {
            console.error(`Error fetching triajes for paciente ${paciente_id}:`, error);
            return [];
        }
    },

    /**
     * Obtener último triaje de un paciente
     */
    async getUltimoTriajePaciente(pacienteId: number): Promise<TriajeEnfermeria | null> {
        try {
            const triajes = await this.obtenerPorPaciente(pacienteId);
            if (triajes.length === 0) return null;
            const latest = triajes.reduce((a, b) =>
                new Date(b.fecha_registro!).getTime() - new Date(a.fecha_registro!).getTime() > 0 ? b : a
            );
            return latest;
        } catch (error) {
            console.error(`Error fetching ultimo triaje for paciente ${pacienteId}:`, error);
            return null;
        }
    },

    /**
     * Calcular IMC manualmente (útil para preview antes de guardar)
     */
    calcularIMC(peso_kg: number, talla_cm: number): number {
        const tallaMetros = talla_cm / 100;
        return parseFloat((peso_kg / (tallaMetros * tallaMetros)).toFixed(2));
    },

    /**
     * Obtener clasificación de IMC
     */
    getClasificacionIMC(imc: number): string {
        if (imc < 18.5) return 'Bajo peso';
        if (imc < 25) return 'Normal';
        if (imc < 30) return 'Sobrepeso';
        if (imc < 35) return 'Obesidad I';
        if (imc < 40) return 'Obesidad II';
        return 'Obesidad III';
    },

    /**
     * Obtener clasificación de presión arterial
     */
    getClasificacionPresion(sistolica: number, diastolica: number): string {
        if (sistolica >= 180 || diastolica >= 120) return 'Crisis Hipertensiva';
        if (sistolica >= 140 || diastolica >= 90) return 'Hipertensión';
        if (sistolica >= 120 || diastolica >= 80) return 'Elevada';
        return 'Normal';
    },

    /**
     * Detectar alertas (útil para validación en frontend antes de guardar)
     */
    detectarAlertas(triaje: Partial<TriajeEnfermeria>): {
        presion_alta: boolean;
        fiebre: boolean;
        taquicardia: boolean;
        saturacion_baja: boolean;
    } {
        return {
            presion_alta: (triaje.presion_sistolica || 0) >= 140 || (triaje.presion_diastolica || 0) >= 90,
            fiebre: (triaje.temperatura || 0) >= 38,
            taquicardia: (triaje.frecuencia_cardiaca || 0) > 100,
            saturacion_baja: (triaje.saturacion_oxigeno || 100) < 95,
        };
    },

    // ─────────────────────────────────────────────────────────────────────────
    // ALIASES (para compatibilidad con código que usa nombres en inglés)
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Alias para obtener
     */
    async getById(id: number): Promise<TriajeEnfermeria> {
        return this.obtener(id);
    },

    /**
     * Alias para actualizar
     */
    async update(id: number, data: Partial<TriajeEnfermeria>): Promise<TriajeEnfermeria> {
        return this.actualizar(id, data);
    },

    /**
     * Alias para crear
     */
    async create(data: Partial<TriajeEnfermeria>): Promise<TriajeEnfermeria> {
        return this.crear(data);
    },
};
