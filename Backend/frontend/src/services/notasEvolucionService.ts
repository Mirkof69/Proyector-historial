/**
 * =============================================================================
 * SERVICIO DE NOTAS DE EVOLUCIÓN MÉDICA
 * =============================================================================
 * Gestión completa de notas de evolución y consultas médicas
 * =============================================================================
 */

import api, { PaginatedResponse } from './api';
import { logger } from '../utils/logger';

// ═════════════════════════════════════════════════════════════════════════
// TIPOS E INTERFACES
// ═════════════════════════════════════════════════════════════════════════

export interface NotaEvolucion {
    id: number;
    paciente: number;
    paciente_nombre?: string;
    embarazo?: number;
    embarazo_info?: string;
    control_prenatal?: number;
    medico: number;
    medico_nombre?: string;
    revisado_por?: number;
    revisado_por_nombre?: string;

    // Información de consulta
    fecha_consulta: string;
    tipo_consulta: 'control_prenatal' | 'urgencia' | 'seguimiento' | 'interconsulta' | 'puerperio' | 'otro';
    motivo_consulta: string;

    // Signos vitales
    presion_arterial_sistolica?: number;
    presion_arterial_diastolica?: number;
    presion_arterial?: string;
    frecuencia_cardiaca?: number;
    frecuencia_respiratoria?: number;
    temperatura?: number;
    saturacion_oxigeno?: number;

    // Datos obstétricos
    edad_gestacional_semanas?: number;
    edad_gestacional_dias?: number;
    edad_gestacional?: string;
    altura_uterina?: number;
    frecuencia_cardiaca_fetal?: number;
    presentacion_fetal?: string;
    movimientos_fetales?: string;

    // Examen y diagnóstico
    examen_fisico: string;
    examen_obstetrico?: string;
    diagnosticos: string;
    plan_tratamiento: string;
    indicaciones?: string;
    observaciones?: string;

    // Auditoría
    fecha_revision?: string;
    fecha_creacion: string;
    fecha_modificacion: string;
    activo: boolean;
}

export interface NotaEvolucionCreate {
    paciente: number;
    embarazo?: number;
    control_prenatal?: number;
    medico?: number;
    fecha_consulta: string;
    tipo_consulta: string;
    motivo_consulta: string;
    presion_arterial_sistolica?: number;
    presion_arterial_diastolica?: number;
    frecuencia_cardiaca?: number;
    frecuencia_respiratoria?: number;
    temperatura?: number;
    saturacion_oxigeno?: number;
    edad_gestacional_semanas?: number;
    edad_gestacional_dias?: number;
    altura_uterina?: number;
    frecuencia_cardiaca_fetal?: number;
    presentacion_fetal?: string;
    movimientos_fetales?: string;
    examen_fisico: string;
    examen_obstetrico?: string;
    diagnosticos: string;
    plan_tratamiento: string;
    indicaciones?: string;
    observaciones?: string;
}

interface EstadisticasNotas {
    total: number;
    por_tipo: { [key: string]: number };
    por_mes: { mes: string; cantidad: number }[];
    promedios: {
        presion_arterial_sistolica: number;
        presion_arterial_diastolica: number;
        frecuencia_cardiaca: number;
        temperatura: number;
    };
}

class NotasEvolucionService {
    private baseUrl = '/notas-evolucion';

    // ═════════════════════════════════════════════════════════════════════
    // CRUD BÁSICO
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener todas las notas de evolución (paginado)
     */
    async getNotas(params?: {
        page?: number;
        page_size?: number;
        tipo_consulta?: string;
        fecha_desde?: string;
        fecha_hasta?: string;
    }): Promise<PaginatedResponse<NotaEvolucion>> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
            if (params?.tipo_consulta) queryParams.append('tipo_consulta', params.tipo_consulta);
            if (params?.fecha_desde) queryParams.append('fecha_desde', params.fecha_desde);
            if (params?.fecha_hasta) queryParams.append('fecha_hasta', params.fecha_hasta);

            const url = `${this.baseUrl}/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<NotaEvolucion>>(url);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo notas de evolución:', error);
            throw error;
        }
    }

    /**
     * Obtener una nota de evolución por ID
     */
    async getNotaById(id: number): Promise<NotaEvolucion> {
        try {
            const response = await api.get<NotaEvolucion>(`${this.baseUrl}/${id}/`);
            logger.log('✅ Nota de evolución obtenida:', id);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo nota ${id}:`, error);
            throw error;
        }
    }

    /**
     * Crear nueva nota de evolución
     */
    async crearNota(data: NotaEvolucionCreate): Promise<NotaEvolucion> {
        try {
            const response = await api.post<NotaEvolucion>(`${this.baseUrl}/`, data);
            logger.log('✅ Nota de evolución creada');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando nota de evolución:', error);
            throw error;
        }
    }

    /**
     * Actualizar nota de evolución
     */
    async actualizarNota(id: number, data: Partial<NotaEvolucionCreate>): Promise<NotaEvolucion> {
        try {
            const response = await api.patch<NotaEvolucion>(`${this.baseUrl}/${id}/`, data);
            logger.log('✅ Nota de evolución actualizada:', id);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error actualizando nota ${id}:`, error);
            throw error;
        }
    }

    /**
     * Eliminar (desactivar) nota de evolución
     */
    async eliminarNota(id: number): Promise<void> {
        try {
            await api.delete(`${this.baseUrl}/${id}/`);
            logger.log('✅ Nota de evolución eliminada:', id);
        } catch (error: any) {
            console.error(`❌ Error eliminando nota ${id}:`, error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // ACCIONES PERSONALIZADAS
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener notas por paciente
     */
    async getNotasPorPaciente(pacienteId: number, params?: {
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<NotaEvolucion>> {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('paciente_id', pacienteId.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.baseUrl}/por-paciente/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<NotaEvolucion>>(url);
            logger.log(`✅ Notas del paciente ${pacienteId} obtenidas`);
            return response.data;
        } catch (error: any) {
            // Suprimir error si es 404 (es normal que un paciente no tenga notas aún)
            if (error.response?.status !== 404) {
                console.error(`❌ Error obteniendo notas del paciente ${pacienteId}:`, error);
            }
            throw error;
        }
    }

    /**
     * Obtener notas por embarazo
     */
    async getNotasPorEmbarazo(embarazoId: number, params?: {
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<NotaEvolucion>> {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('embarazo_id', embarazoId.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.baseUrl}/por_embarazo/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<NotaEvolucion>>(url);
            logger.log(`✅ Notas del embarazo ${embarazoId} obtenidas`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo notas del embarazo ${embarazoId}:`, error);
            throw error;
        }
    }

    /**
     * Obtener mis notas (del médico autenticado)
     */
    async getMisNotas(params?: {
        page?: number;
        page_size?: number;
        tipo_consulta?: string;
    }): Promise<PaginatedResponse<NotaEvolucion>> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
            if (params?.tipo_consulta) queryParams.append('tipo_consulta', params.tipo_consulta);

            const url = `${this.baseUrl}/mis-notas/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<NotaEvolucion>>(url);
            logger.log('✅ Mis notas obtenidas');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo mis notas:', error);
            throw error;
        }
    }

    /**
     * Revisar nota (marcar como revisada por supervisor)
     */
    async revisarNota(id: number): Promise<NotaEvolucion> {
        try {
            const response = await api.post<NotaEvolucion>(`${this.baseUrl}/${id}/revisar/`);
            logger.log(`✅ Nota ${id} revisada`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error revisando nota ${id}:`, error);
            throw error;
        }
    }

    /**
     * Obtener estadísticas de notas
     */
    async getEstadisticas(params?: {
        medico_id?: number;
        paciente_id?: number;
        fecha_desde?: string;
        fecha_hasta?: string;
    }): Promise<EstadisticasNotas> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.medico_id) queryParams.append('medico_id', params.medico_id.toString());
            if (params?.paciente_id) queryParams.append('paciente_id', params.paciente_id.toString());
            if (params?.fecha_desde) queryParams.append('fecha_desde', params.fecha_desde);
            if (params?.fecha_hasta) queryParams.append('fecha_hasta', params.fecha_hasta);

            const url = `${this.baseUrl}/estadisticas/?${queryParams.toString()}`;
            const response = await api.get<EstadisticasNotas>(url);
            logger.log('✅ Estadísticas de notas obtenidas');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo estadísticas:', error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener tipos de consulta disponibles
     */
    getTiposConsulta(): Array<{ value: string; label: string }> {
        return [
            { value: 'control_prenatal', label: 'Control Prenatal' },
            { value: 'urgencia', label: 'Consulta de Urgencia' },
            { value: 'seguimiento', label: 'Seguimiento' },
            { value: 'interconsulta', label: 'Interconsulta' },
            { value: 'puerperio', label: 'Control Puerperio' },
            { value: 'otro', label: 'Otro' },
        ];
    }

    /**
     * Validar signos vitales
     */
    validarSignosVitales(data: Partial<NotaEvolucionCreate>): { valido: boolean; errores: string[] } {
        const errores: string[] = [];

        if (data.presion_arterial_sistolica && (data.presion_arterial_sistolica < 50 || data.presion_arterial_sistolica > 250)) {
            errores.push('Presión arterial sistólica fuera de rango (50-250 mmHg)');
        }

        if (data.presion_arterial_diastolica && (data.presion_arterial_diastolica < 30 || data.presion_arterial_diastolica > 150)) {
            errores.push('Presión arterial diastólica fuera de rango (30-150 mmHg)');
        }

        if (data.frecuencia_cardiaca && (data.frecuencia_cardiaca < 40 || data.frecuencia_cardiaca > 200)) {
            errores.push('Frecuencia cardíaca fuera de rango (40-200 lpm)');
        }

        if (data.temperatura && (data.temperatura < 35 || data.temperatura > 42)) {
            errores.push('Temperatura fuera de rango (35-42°C)');
        }

        if (data.saturacion_oxigeno && (data.saturacion_oxigeno < 70 || data.saturacion_oxigeno > 100)) {
            errores.push('Saturación de oxígeno fuera de rango (70-100%)');
        }

        if (data.frecuencia_cardiaca_fetal && (data.frecuencia_cardiaca_fetal < 100 || data.frecuencia_cardiaca_fetal > 180)) {
            errores.push('Frecuencia cardíaca fetal fuera de rango (100-180 lpm)');
        }

        return {
            valido: errores.length === 0,
            errores
        };
    }

    /**
     * Formatear nota para impresión/PDF
     */
    formatearNotaParaImpresion(nota: NotaEvolucion): string {
        return `
NOTA DE EVOLUCIÓN MÉDICA
========================

Fecha de Consulta: ${new Date(nota.fecha_consulta).toLocaleString('es-MX')}
Tipo de Consulta: ${nota.tipo_consulta}
Médico: ${nota.medico_nombre || 'No especificado'}

MOTIVO DE CONSULTA
------------------
${nota.motivo_consulta}

SIGNOS VITALES
--------------
Presión Arterial: ${nota.presion_arterial || 'No registrada'}
Frecuencia Cardíaca: ${nota.frecuencia_cardiaca || '-'} lpm
Frecuencia Respiratoria: ${nota.frecuencia_respiratoria || '-'} rpm
Temperatura: ${nota.temperatura || '-'}°C
Saturación O2: ${nota.saturacion_oxigeno || '-'}%

${nota.edad_gestacional ? `
DATOS OBSTÉTRICOS
-----------------
Edad Gestacional: ${nota.edad_gestacional}
Altura Uterina: ${nota.altura_uterina || '-'} cm
FCF: ${nota.frecuencia_cardiaca_fetal || '-'} lpm
Presentación: ${nota.presentacion_fetal || '-'}
Movimientos Fetales: ${nota.movimientos_fetales || '-'}
` : ''}

EXAMEN FÍSICO
-------------
${nota.examen_fisico}

${nota.examen_obstetrico ? `
EXAMEN OBSTÉTRICO
-----------------
${nota.examen_obstetrico}
` : ''}

IMPRESIÓN DIAGNÓSTICA
---------------------
${nota.diagnosticos}

PLAN DE TRATAMIENTO
-------------------
${nota.plan_tratamiento}

${nota.indicaciones ? `
INDICACIONES AL PACIENTE
------------------------
${nota.indicaciones}
` : ''}

${nota.observaciones ? `
OBSERVACIONES
-------------
${nota.observaciones}
` : ''}

---
Registrado: ${new Date(nota.fecha_creacion).toLocaleString('es-MX')}
${nota.revisado_por_nombre ? `Revisado por: ${nota.revisado_por_nombre}` : ''}
        `.trim();
    }
}

export const notasEvolucionService = new NotasEvolucionService();

