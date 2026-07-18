/**
 * =============================================================================
 * SERVICIO DE VACUNAS
 * =============================================================================
 * Gestión completa del esquema de vacunación y registros de aplicación
 * =============================================================================
 */

import api, { PaginatedResponse } from './api';
import { logger } from '../utils/logger';

// ═════════════════════════════════════════════════════════════════════════
// TIPOS E INTERFACES
// ═════════════════════════════════════════════════════════════════════════

export interface TipoVacuna {
    id: number;
    nombre: string;
    descripcion: string;
    dosis_requeridas: number;
    intervalo_dosis_dias?: number;
    edad_minima_aplicacion?: number;
    contraindicaciones?: string;
    efectos_secundarios?: string;
    obligatoria_embarazo: boolean;
    activo: boolean;
    fecha_creacion: string;
    fecha_modificacion: string;
}

interface TipoVacunaCreate {
    nombre: string;
    descripcion: string;
    dosis_requeridas: number;
    intervalo_dosis_dias?: number;
    edad_minima_aplicacion?: number;
    contraindicaciones?: string;
    efectos_secundarios?: string;
    obligatoria_embarazo?: boolean;
    activo?: boolean;
}

export interface RegistroVacuna {
    id: number;
    paciente: number;
    paciente_nombre?: string;
    embarazo?: number;
    embarazo_info?: string;
    tipo_vacuna: number;
    tipo_vacuna_nombre?: string;
    aplicado_por?: number;
    aplicado_por_nombre?: string;

    // Datos de aplicación
    fecha_aplicacion: string;
    numero_dosis: number;
    lote: string;
    laboratorio: string;
    via_administracion: 'intramuscular' | 'subcutanea' | 'oral' | 'intradermica';
    sitio_aplicacion: string;
    proxima_dosis_fecha?: string;
    reacciones_adversas?: string;
    observaciones?: string;

    // Auditoría
    activo: boolean;
    fecha_creacion: string;
    fecha_modificacion: string;
}

export interface RegistroVacunaCreate {
    paciente: number;
    embarazo?: number;
    tipo_vacuna: number;
    aplicado_por?: number;
    fecha_aplicacion: string;
    numero_dosis: number;
    lote: string;
    laboratorio: string;
    via_administracion: string;
    sitio_aplicacion: string;
    proxima_dosis_fecha?: string;
    reacciones_adversas?: string;
    observaciones?: string;
}

interface EsquemaVacunacion {
    paciente_id: number;
    paciente_nombre: string;
    embarazo_id?: number;
    esquemas: {
        tipo_vacuna: TipoVacuna;
        dosis_aplicadas: number;
        dosis_requeridas: number;
        completo: boolean;
        proxima_dosis?: string;
        registros: RegistroVacuna[];
    }[];
}

interface ProximaDosis {
    paciente_id: number;
    paciente_nombre: string;
    tipo_vacuna: number;
    tipo_vacuna_nombre: string;
    numero_dosis: number;
    fecha_proxima: string;
    dias_restantes: number;
    vencida: boolean;
}

interface EstadisticasVacunas {
    total_registros: number;
    total_pacientes: number;
    esquemas_completos: number;
    esquemas_incompletos: number;
    por_tipo_vacuna: { [key: string]: number };
    por_mes: { mes: string; cantidad: number }[];
    reacciones_adversas: number;
}

class VacunasService {
    private baseUrl = '/vacunas';
    // El router del backend registra "tipos-vacunas" (vacunas/urls.py). Con
    // "/tipos" TODAS las llamadas daban 404 y el catch de abajo las tragaba
    // devolviendo lista vacía: el catálogo de tipos nunca cargaba y el 404
    // pasaba desapercibido.
    private tiposUrl = `${this.baseUrl}/tipos-vacunas`;
    private registrosUrl = `${this.baseUrl}/registros`;

    // ═════════════════════════════════════════════════════════════════════
    // TIPOS DE VACUNAS (CATÁLOGO)
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener todos los tipos de vacunas
     */
    async getTiposVacunas(params?: {
        page?: number;
        page_size?: number;
        activo?: boolean;
        obligatoria_embarazo?: boolean;
    }): Promise<PaginatedResponse<TipoVacuna>> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
            if (params?.activo !== undefined) queryParams.append('activo', params.activo.toString());
            if (params?.obligatoria_embarazo !== undefined) queryParams.append('obligatoria_embarazo', params.obligatoria_embarazo.toString());

            const url = `${this.tiposUrl}/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<TipoVacuna>>(url);
            return response.data;
        } catch (error: any) {
            // Manejar 404 gracefully - endpoint no disponible
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint de tipos de vacunas no disponible (404)');
                return {
                    count: 0,
                    next: null,
                    previous: null,
                    results: []
                };
            }
            console.error('❌ Error obteniendo tipos de vacunas:', error);
            throw error;
        }
    }

    /**
     * Obtener tipo de vacuna por ID
     */
    async getTipoVacunaById(id: number): Promise<TipoVacuna | null> {
        try {
            const response = await api.get<TipoVacuna>(`${this.tiposUrl}/${id}/`);
            logger.log('✅ Tipo de vacuna obtenido:', id);
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn(`⚠️ Tipo de vacuna ${id} no encontrado (404)`);
                return null;
            }
            console.error(`❌ Error obteniendo tipo de vacuna ${id}:`, error);
            throw error;
        }
    }

    /**
     * Crear nuevo tipo de vacuna
     */
    async crearTipoVacuna(data: TipoVacunaCreate): Promise<TipoVacuna> {
        try {
            const response = await api.post<TipoVacuna>(`${this.tiposUrl}/`, data);
            logger.log('✅ Tipo de vacuna creado');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando tipo de vacuna:', error);
            throw error;
        }
    }

    /**
     * Actualizar tipo de vacuna
     */
    async actualizarTipoVacuna(id: number, data: Partial<TipoVacunaCreate>): Promise<TipoVacuna> {
        try {
            const response = await api.patch<TipoVacuna>(`${this.tiposUrl}/${id}/`, data);
            logger.log('✅ Tipo de vacuna actualizado:', id);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error actualizando tipo de vacuna ${id}:`, error);
            throw error;
        }
    }

    /**
     * Eliminar (desactivar) tipo de vacuna
     */
    async eliminarTipoVacuna(id: number): Promise<void> {
        try {
            await api.delete(`${this.tiposUrl}/${id}/`);
            logger.log('✅ Tipo de vacuna eliminado:', id);
        } catch (error: any) {
            console.error(`❌ Error eliminando tipo de vacuna ${id}:`, error);
            throw error;
        }
    }

    /**
     * Obtener vacunas activas
     */
    async getVacunasActivas(): Promise<TipoVacuna[]> {
        try {
            const response = await api.get<TipoVacuna[]>(`${this.tiposUrl}/activas/`);
            logger.log('✅ Vacunas activas obtenidas');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint de vacunas activas no disponible (404)');
                return [];
            }
            console.error('❌ Error obteniendo vacunas activas:', error);
            throw error;
        }
    }

    /**
     * Obtener vacunas obligatorias en embarazo
     */
    async getVacunasObligatoriasEmbarazo(): Promise<TipoVacuna[]> {
        try {
            const response = await api.get<TipoVacuna[]>(`${this.tiposUrl}/obligatorias_embarazo/`);
            logger.log('✅ Vacunas obligatorias en embarazo obtenidas');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint de vacunas obligatorias no disponible (404)');
                return [];
            }
            console.error('❌ Error obteniendo vacunas obligatorias:', error);
            throw error;
        }
    }

    /**
     * Obtener estadísticas de tipos de vacunas
     */
    async getEstadisticasTipos(): Promise<any> {
        try {
            const response = await api.get<any>(`${this.tiposUrl}/estadisticas/`);
            logger.log('✅ Estadísticas de tipos de vacunas obtenidas');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint de estadísticas de vacunas no disponible (404)');
                return {
                    total: 0,
                    activas: 0,
                    obligatorias_embarazo: 0
                };
            }
            console.error('❌ Error obteniendo estadísticas:', error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // REGISTROS DE VACUNACIÓN
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener todos los registros de vacunas
     */
    async getRegistros(params?: {
        page?: number;
        page_size?: number;
        paciente?: number;
        embarazo?: number;
        tipo_vacuna?: number;
        fecha_desde?: string;
        fecha_hasta?: string;
    }): Promise<PaginatedResponse<RegistroVacuna>> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
            if (params?.paciente) queryParams.append('paciente', params.paciente.toString());
            if (params?.embarazo) queryParams.append('embarazo', params.embarazo.toString());
            if (params?.tipo_vacuna) queryParams.append('tipo_vacuna', params.tipo_vacuna.toString());
            if (params?.fecha_desde) queryParams.append('fecha_desde', params.fecha_desde);
            if (params?.fecha_hasta) queryParams.append('fecha_hasta', params.fecha_hasta);

            const url = `${this.registrosUrl}/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<RegistroVacuna>>(url);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo registros de vacunas:', error);
            throw error;
        }
    }

    /**
     * Obtener registro de vacuna por ID
     */
    async getRegistroById(id: number): Promise<RegistroVacuna> {
        try {
            const response = await api.get<RegistroVacuna>(`${this.registrosUrl}/${id}/`);
            logger.log('✅ Registro de vacuna obtenido:', id);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo registro ${id}:`, error);
            throw error;
        }
    }

    /**
     * Crear nuevo registro de vacuna
     */
    async crearRegistro(data: RegistroVacunaCreate): Promise<RegistroVacuna> {
        try {
            const response = await api.post<RegistroVacuna>(`${this.registrosUrl}/`, data);
            logger.log('✅ Registro de vacuna creado');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando registro de vacuna:', error);
            throw error;
        }
    }

    /**
     * Actualizar registro de vacuna
     */
    async actualizarRegistro(id: number, data: Partial<RegistroVacunaCreate>): Promise<RegistroVacuna> {
        try {
            const response = await api.patch<RegistroVacuna>(`${this.registrosUrl}/${id}/`, data);
            logger.log('✅ Registro de vacuna actualizado:', id);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error actualizando registro ${id}:`, error);
            throw error;
        }
    }

    /**
     * Eliminar (desactivar) registro de vacuna
     */
    async eliminarRegistro(id: number): Promise<void> {
        try {
            await api.delete(`${this.registrosUrl}/${id}/`);
            logger.log('✅ Registro de vacuna eliminado:', id);
        } catch (error: any) {
            console.error(`❌ Error eliminando registro ${id}:`, error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // ACCIONES PERSONALIZADAS
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener registros por paciente
     */
    async getRegistrosPorPaciente(pacienteId: number, params?: {
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<RegistroVacuna>> {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('paciente_id', pacienteId.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/por_paciente/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<RegistroVacuna>>(url);
            logger.log(`✅ Registros del paciente ${pacienteId} obtenidos`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo registros del paciente ${pacienteId}:`, error);
            throw error;
        }
    }

    /**
     * Obtener registros por embarazo
     */
    async getRegistrosPorEmbarazo(embarazoId: number, params?: {
        page?: number;
        page_size?: number;
    }): Promise<PaginatedResponse<RegistroVacuna>> {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('embarazo_id', embarazoId.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/por_embarazo/?${queryParams.toString()}`;
            const response = await api.get<PaginatedResponse<RegistroVacuna>>(url);
            logger.log(`✅ Registros del embarazo ${embarazoId} obtenidos`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo registros del embarazo ${embarazoId}:`, error);
            throw error;
        }
    }

    /**
     * Obtener próximas dosis programadas
     */
    async getProximasDosis(params?: {
        dias_adelante?: number;
        solo_vencidas?: boolean;
    }): Promise<ProximaDosis[]> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.dias_adelante) queryParams.append('dias_adelante', params.dias_adelante.toString());
            if (params?.solo_vencidas) queryParams.append('solo_vencidas', params.solo_vencidas.toString());

            const url = `${this.registrosUrl}/proximas_dosis/?${queryParams.toString()}`;
            const response = await api.get<ProximaDosis[]>(url);
            logger.log('✅ Próximas dosis obtenidas');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo próximas dosis:', error);
            throw error;
        }
    }

    /**
     * Obtener esquema de vacunación de un paciente
     */
    async getEsquemaVacunacion(pacienteId: number, embarazoId?: number): Promise<EsquemaVacunacion> {
        try {
            const queryParams = new URLSearchParams();
            queryParams.append('paciente_id', pacienteId.toString());
            if (embarazoId) queryParams.append('embarazo_id', embarazoId.toString());

            const url = `${this.registrosUrl}/esquema_vacunacion/?${queryParams.toString()}`;
            const response = await api.get<EsquemaVacunacion>(url);
            logger.log(`✅ Esquema de vacunación del paciente ${pacienteId} obtenido`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error obteniendo esquema del paciente ${pacienteId}:`, error);
            throw error;
        }
    }

    /**
     * Obtener esquemas incompletos
     */
    async getEsquemasIncompletos(params?: {
        page?: number;
        page_size?: number;
    }): Promise<any> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/esquemas_incompletos/?${queryParams.toString()}`;
            const response = await api.get<any>(url);
            logger.log('✅ Esquemas incompletos obtenidos');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo esquemas incompletos:', error);
            throw error;
        }
    }

    /**
     * Obtener esquema completo de vacunación de todos los pacientes
     * NUEVO ENDPOINT - CONECTADO AL BACKEND
     */
    async getEsquemaCompleto(params?: {
        activos?: boolean;
        completos?: boolean;
        incompletos?: boolean;
        page?: number;
        page_size?: number;
    }): Promise<any> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.activos !== undefined) queryParams.append('activos', params.activos.toString());
            if (params?.completos !== undefined) queryParams.append('completos', params.completos.toString());
            if (params?.incompletos !== undefined) queryParams.append('incompletos', params.incompletos.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/esquema-completo/?${queryParams.toString()}`;
            const response = await api.get<any>(url);
            logger.log('✅ Esquema completo de vacunación obtenido');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint esquema-completo no disponible (404) - retornando datos mock');
                // Retornar datos simulados si el endpoint no está disponible
                return {
                    count: 0,
                    results: [],
                    estadisticas: {
                        total_pacientes: 0,
                        esquemas_completos: 0,
                        esquemas_incompletos: 0,
                        cobertura_promedio: 0
                    }
                };
            }
            console.error('❌ Error obteniendo esquema completo:', error);
            throw error;
        }
    }

    /**
     * Obtener estadísticas de vacunación
     */
    async getEstadisticasVacunacion(params?: {
        fecha_desde?: string;
        fecha_hasta?: string;
        paciente_id?: number;
    }): Promise<EstadisticasVacunas> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.fecha_desde) queryParams.append('fecha_desde', params.fecha_desde);
            if (params?.fecha_hasta) queryParams.append('fecha_hasta', params.fecha_hasta);
            if (params?.paciente_id) queryParams.append('paciente_id', params.paciente_id.toString());

            const url = `${this.registrosUrl}/estadisticas/?${queryParams.toString()}`;
            const response = await api.get<EstadisticasVacunas>(url);
            logger.log('✅ Estadísticas de vacunación obtenidas');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo estadísticas:', error);
            throw error;
        }
    }

    /**
     * Obtener vacunas pendientes de aplicación
     * NUEVO ENDPOINT - CONECTADO AL BACKEND
     */
    async getPendientes(params?: {
        paciente_id?: number;
        embarazo_id?: number;
        page?: number;
        page_size?: number;
    }): Promise<any> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.paciente_id) queryParams.append('paciente_id', params.paciente_id.toString());
            if (params?.embarazo_id) queryParams.append('embarazo_id', params.embarazo_id.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/pendientes/?${queryParams.toString()}`;
            const response = await api.get<any>(url);
            logger.log('✅ Vacunas pendientes obtenidas');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint pendientes no disponible (404) - retornando datos vacíos');
                return {
                    count: 0,
                    results: [],
                    mensaje: 'No hay vacunas pendientes'
                };
            }
            console.error('❌ Error obteniendo vacunas pendientes:', error);
            throw error;
        }
    }

    /**
     * Obtener próximas vacunas programadas
     * NUEVO ENDPOINT - CONECTADO AL BACKEND
     */
    async getProximas(params?: {
        dias_adelante?: number;
        paciente_id?: number;
        embarazo_id?: number;
        page?: number;
        page_size?: number;
    }): Promise<any> {
        try {
            const queryParams = new URLSearchParams();
            if (params?.dias_adelante) queryParams.append('dias_adelante', params.dias_adelante.toString());
            if (params?.paciente_id) queryParams.append('paciente_id', params.paciente_id.toString());
            if (params?.embarazo_id) queryParams.append('embarazo_id', params.embarazo_id.toString());
            if (params?.page) queryParams.append('page', params.page.toString());
            if (params?.page_size) queryParams.append('page_size', params.page_size.toString());

            const url = `${this.registrosUrl}/proximas/?${queryParams.toString()}`;
            const response = await api.get<any>(url);
            logger.log('✅ Próximas vacunas obtenidas');
            return response.data;
        } catch (error: any) {
            if (error.response?.status === 404) {
                console.warn('⚠️ Endpoint proximas no disponible (404) - retornando datos vacíos');
                return {
                    count: 0,
                    results: [],
                    mensaje: 'No hay próximas vacunas programadas'
                };
            }
            console.error('❌ Error obteniendo próximas vacunas:', error);
            throw error;
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // UTILIDADES
    // ═════════════════════════════════════════════════════════════════════

    /**
     * Obtener vías de administración disponibles
     */
    getViasAdministracion(): Array<{ value: string; label: string }> {
        return [
            { value: 'intramuscular', label: 'Intramuscular' },
            { value: 'subcutanea', label: 'Subcutánea' },
            { value: 'oral', label: 'Oral' },
            { value: 'intradermica', label: 'Intradérmica' },
        ];
    }

    /**
     * Calcular próxima dosis fecha
     */
    calcularProximaDosis(fechaAplicacion: string, intervalo_dias?: number): string | null {
        if (!intervalo_dias) return null;

        const fecha = new Date(fechaAplicacion);
        fecha.setDate(fecha.getDate() + intervalo_dias);
        return fecha.toISOString().split('T')[0];
    }

    /**
     * Validar número de dosis
     */
    validarNumeroDosis(numero_dosis: number, dosis_requeridas: number): { valido: boolean; mensaje?: string } {
        if (numero_dosis < 1) {
            return { valido: false, mensaje: 'El número de dosis debe ser mayor a 0' };
        }

        if (numero_dosis > dosis_requeridas) {
            return { valido: false, mensaje: `El número de dosis no puede exceder ${dosis_requeridas}` };
        }

        return { valido: true };
    }

    /**
     * Formatear esquema de vacunación para impresión
     */
    formatearEsquemaParaImpresion(esquema: EsquemaVacunacion): string {
        return `
ESQUEMA DE VACUNACIÓN
=====================

Paciente: ${esquema.paciente_nombre}
${esquema.embarazo_id ? `Embarazo ID: ${esquema.embarazo_id}` : ''}

${esquema.esquemas.map((e, index) => `
${index + 1}. ${e.tipo_vacuna.nombre}
   Dosis aplicadas: ${e.dosis_aplicadas} de ${e.dosis_requeridas}
   Estado: ${e.completo ? '✅ COMPLETO' : '⚠️ INCOMPLETO'}
   ${e.proxima_dosis ? `Próxima dosis: ${e.proxima_dosis}` : ''}

   Registros:
   ${e.registros.map(r => `
      • Dosis ${r.numero_dosis} - ${new Date(r.fecha_aplicacion).toLocaleDateString('es-MX')}
        Lote: ${r.lote} | Lab: ${r.laboratorio}
        Vía: ${r.via_administracion} | Sitio: ${r.sitio_aplicacion}
        ${r.reacciones_adversas ? `⚠️ Reacciones: ${r.reacciones_adversas}` : ''}
   `).join('\n')}
`).join('\n')}

---
Generado: ${new Date().toLocaleString('es-MX')}
        `.trim();
    }
}

export const vacunasService = new VacunasService();

