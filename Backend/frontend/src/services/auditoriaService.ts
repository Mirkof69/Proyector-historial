/**
 * =============================================================================
 * SERVICIO: AUDITORÍA Y TRAZABILIDAD
 * =============================================================================
 * Servicio para gestionar todas las operaciones relacionadas con la auditoría
 * del sistema, incluyendo consultas de cambios, filtros y reportes.
 * =============================================================================
 */

import apiClient from './api';

interface AuditRecord {
    id: number;
    modulo: string;
    accion: 'crear' | 'actualizar' | 'eliminar';
    registro_id: number;
    usuario: {
        id: number;
        username: string;
        nombre_completo: string;
    };
    fecha: string;
    datos_anteriores?: any;
    datos_nuevos?: any;
    ip_address?: string;
    user_agent?: string;
}

interface AuditFilters {
    modulo?: string;
    accion?: string;
    usuario_id?: number;
    fecha_inicio?: string;
    fecha_fin?: string;
    registro_id?: number;
    search?: string;
}

interface ModuleStats {
    modulo: string;
    total: number;
    creates: number;
    updates: number;
    deletes: number;
}

interface AuditResponse {
    count: number;
    next: string | null;
    previous: string | null;
    results: AuditRecord[];
}

class AuditoriaService {
    /**
     * Obtener todos los registros de auditoría con filtros opcionales
     */
    async getAuditRecords(filters?: AuditFilters, page: number = 1, pageSize: number = 20): Promise<AuditResponse> {
        const params = new URLSearchParams();

        if (filters) {
            if (filters.modulo) params.append('modulo', filters.modulo);
            if (filters.accion) params.append('accion', filters.accion);
            if (filters.usuario_id) params.append('usuario_id', filters.usuario_id.toString());
            if (filters.fecha_inicio) params.append('fecha_inicio', filters.fecha_inicio);
            if (filters.fecha_fin) params.append('fecha_fin', filters.fecha_fin);
            if (filters.registro_id) params.append('registro_id', filters.registro_id.toString());
            if (filters.search) params.append('search', filters.search);
        }

        params.append('page', page.toString());
        params.append('page_size', pageSize.toString());

        const response = await apiClient.get(`/auditoria/?${params.toString()}`);
        return response.data;
    }

    /**
     * Obtener un registro de auditoría específico
     */
    async getAuditRecord(id: number): Promise<AuditRecord> {
        const response = await apiClient.get(`/auditoria/${id}/`);
        return response.data;
    }

    /**
     * Obtener estadísticas por módulo
     */
    async getModuleStats(): Promise<ModuleStats[]> {
        const response = await apiClient.get('/auditoria/estadisticas-modulos/');
        return response.data;
    }

    /**
     * Obtener estadísticas generales
     */
    async getGeneralStats(): Promise<{
        total_registros: number;
        ultimas_24h: number;
        usuarios_activos: number;
        modulos_activos: number;
    }> {
        const response = await apiClient.get('/auditoria/estadisticas-generales/');
        return response.data;
    }

    /**
     * Obtener registros de un módulo específico
     */
    async getModuleRecords(modulo: string, page: number = 1, pageSize: number = 20): Promise<AuditResponse> {
        const response = await apiClient.get(`/auditoria/${modulo}/`, {
            params: { page, page_size: pageSize }
        });
        return response.data;
    }

    /**
     * Obtener registros de un usuario específico
     */
    async getUserRecords(userId: number, page: number = 1, pageSize: number = 20): Promise<AuditResponse> {
        const response = await apiClient.get(`/auditoria/usuario/${userId}/`, {
            params: { page, page_size: pageSize }
        });
        return response.data;
    }

    /**
     * Obtener registros de un registro específico en cualquier módulo
     */
    async getRecordHistory(modulo: string, registroId: number): Promise<AuditRecord[]> {
        const response = await apiClient.get(`/auditoria/${modulo}/${registroId}/historial/`);
        return response.data;
    }

    /**
     * Exportar registros de auditoría a CSV
     */
    async exportToCSV(filters?: AuditFilters): Promise<Blob> {
        const params = new URLSearchParams();

        if (filters) {
            if (filters.modulo) params.append('modulo', filters.modulo);
            if (filters.accion) params.append('accion', filters.accion);
            if (filters.usuario_id) params.append('usuario_id', filters.usuario_id.toString());
            if (filters.fecha_inicio) params.append('fecha_inicio', filters.fecha_inicio);
            if (filters.fecha_fin) params.append('fecha_fin', filters.fecha_fin);
        }

        const response = await apiClient.get(`/auditoria/exportar-csv/?${params.toString()}`, {
            responseType: 'blob'
        });
        return response.data;
    }

    /**
     * Exportar registros de auditoría a PDF
     */
    async exportToPDF(filters?: AuditFilters): Promise<Blob> {
        const params = new URLSearchParams();

        if (filters) {
            if (filters.modulo) params.append('modulo', filters.modulo);
            if (filters.accion) params.append('accion', filters.accion);
            if (filters.usuario_id) params.append('usuario_id', filters.usuario_id.toString());
            if (filters.fecha_inicio) params.append('fecha_inicio', filters.fecha_inicio);
            if (filters.fecha_fin) params.append('fecha_fin', filters.fecha_fin);
        }

        const response = await apiClient.get(`/auditoria/exportar-pdf/?${params.toString()}`, {
            responseType: 'blob'
        });
        return response.data;
    }

    /**
     * Obtener comparación entre dos versiones de un registro
     */
    async compareVersions(auditId1: number, auditId2: number): Promise<{
        cambios: any[];
        diferencias: string[];
    }> {
        const response = await apiClient.get(`/auditoria/comparar/${auditId1}/${auditId2}/`);
        return response.data;
    }

    /**
     * Obtener línea de tiempo de cambios para un registro
     */
    async getTimeline(modulo: string, registroId: number): Promise<AuditRecord[]> {
        const response = await apiClient.get(`/auditoria/${modulo}/${registroId}/timeline/`);
        return response.data;
    }

    /**
     * Obtener registros de trazabilidad para display (created_by, updated_by)
     */
    async getTrazabilidadDisplay(modulo: string, registroId: number): Promise<{
        created_by: {
            id: number;
            username: string;
            nombre_completo: string;
            fecha: string;
        } | null;
        updated_by: {
            id: number;
            username: string;
            nombre_completo: string;
            fecha: string;
        } | null;
    }> {
        const response = await apiClient.get(`/auditoria/${modulo}/${registroId}/trazabilidad/`);
        return response.data;
    }

    /**
     * Obtener cambios detallados a nivel de campo de un registro de auditoría
     */
    async getCambiosDetallados(auditId: number): Promise<{
        accion: string;
        cambios: Array<{
            campo: string;
            tipo: 'creado' | 'modificado' | 'eliminado';
            valor_anterior: any;
            valor_nuevo: any;
            cambio_tipo: 'add' | 'modify' | 'remove';
        }>;
        total_cambios: number;
    }> {
        const response = await apiClient.get(`/auditoria/${auditId}/cambios-detallados/`);
        return response.data;
    }
}

// Exportar instancia única del servicio
const auditoriaService = new AuditoriaService();
export default auditoriaService;
