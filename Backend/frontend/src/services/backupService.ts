/**
 * =============================================================================
 * SERVICIO DE BACKUPS - GESTIÓN DE COPIAS DE SEGURIDAD
 * =============================================================================
 * Cliente API para gestión de backups de base de datos
 * =============================================================================
 */

import api from './api';

export interface Backup {
    id?: number;
    filename: string;
    type: 'daily' | 'weekly' | 'monthly' | 'manual';
    created_at: string;
    size: number;
    size_mb: number;
    compressed: boolean;
    hash: string;
    database: string;
    verified?: boolean;
    can_restore?: boolean;
}

export interface BackupStats {
    total_backups: number;
    total_size_mb: number;
    por_tipo: {
        daily: number;
        weekly: number;
        monthly: number;
        manual: number;
    };
    ultimo_backup: string;
    proximo_backup_programado?: string;
}

export interface CreateBackupParams {
    type?: 'daily' | 'weekly' | 'monthly' | 'manual';
    compress?: boolean;
    description?: string;
}

/**
 * Normaliza respuestas del backend
 */
function normalizeListResponse<T>(data: any): T[] {
    if (Array.isArray(data)) return data as T[];
    if (data?.results && Array.isArray(data.results)) return data.results as T[];
    if (data?.data && Array.isArray(data.data)) return data.data as T[];
    console.warn('⚠️ backupService: Respuesta no es array:', data);
    return [];
}

function normalizeSingleResponse<T>(data: any): T {
    if (data?.data && typeof data.data === 'object') return data.data as T;
    return data as T;
}

export const backupService = {
    /**
     * Listar todos los backups disponibles
     */
    async listar(params?: {
        type?: string;
        desde?: string;
        hasta?: string;
    }): Promise<Backup[]> {
        try {
            const response = await api.get<Backup[]>('/backups/', { params });
            return normalizeListResponse<Backup>(response.data);
        } catch (error: any) {
            console.error('❌ Error listando backups:', error);
            throw error;
        }
    },

    /**
     * Obtener detalles de un backup específico
     */
    async obtener(id: number): Promise<Backup> {
        try {
            const response = await api.get<Backup>(`/backups/${id}/`);
            return normalizeSingleResponse<Backup>(response.data);
        } catch (error: any) {
            console.error(`❌ Error obteniendo backup ${id}:`, error);
            throw error;
        }
    },

    /**
     * Crear un nuevo backup
     */
    async crear(params?: CreateBackupParams): Promise<Backup> {
        try {
            const response = await api.post<Backup>('/backups/crear/', params || {});
            return normalizeSingleResponse<Backup>(response.data);
        } catch (error: any) {
            console.error('❌ Error creando backup:', error);
            throw error;
        }
    },

    /**
     * Verificar integridad de un backup
     */
    async verificar(id: number): Promise<{
        valido: boolean;
        mensaje: string;
        hash_verificado: boolean;
    }> {
        try {
            const response = await api.post(`/backups/${id}/verificar/`);
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error verificando backup ${id}:`, error);
            throw error;
        }
    },

    /**
     * Restaurar base de datos desde un backup
     * 
     * ⚠️ CUIDADO: Esta operación sobrescribirá la base de datos actual
     */
    async restaurar(id: number, confirmar: boolean = false): Promise<{
        exitoso: boolean;
        mensaje: string;
    }> {
        if (!confirmar) {
            throw new Error('Debe confirmar explícitamente la restauración');
        }

        try {
            const response = await api.post(`/backups/${id}/restaurar/`, {
                confirmar: true
            });
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error restaurando backup ${id}:`, error);
            throw error;
        }
    },

    /**
     * Eliminar un backup
     */
    async eliminar(id: number): Promise<void> {
        try {
            await api.delete(`/backups/${id}/`);
        } catch (error: any) {
            console.error(`❌ Error eliminando backup ${id}:`, error);
            throw error;
        }
    },

    /**
     * Descargar un backup
     */
    async descargar(id: number): Promise<Blob> {
        try {
            const response = await api.get(`/backups/${id}/descargar/`, {
                responseType: 'blob'
            });
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error descargando backup ${id}:`, error);
            throw error;
        }
    },

    /**
     * Obtener estadísticas de backups
     */
    async obtenerEstadisticas(): Promise<BackupStats> {
        try {
            const response = await api.get<BackupStats>('/backups/estadisticas/');
            return normalizeSingleResponse<BackupStats>(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo estadísticas de backups:', error);
            throw error;
        }
    },

    /**
     * Programar backup automático
     */
    async programar(params: {
        type: 'daily' | 'weekly' | 'monthly';
        hora: string; // HH:MM format
        activo: boolean;
    }): Promise<{
        exitoso: boolean;
        mensaje: string;
        proximo_backup: string;
    }> {
        try {
            const response = await api.post('/backups/programar/', params);
            return response.data;
        } catch (error: any) {
            console.error('❌ Error programando backup:', error);
            throw error;
        }
    },

    /**
     * Obtener configuración de backups programados
     */
    async obtenerProgramacion(): Promise<{
        daily: { activo: boolean; hora: string };
        weekly: { activo: boolean; hora: string; dia_semana: number };
        monthly: { activo: boolean; hora: string; dia_mes: number };
    }> {
        try {
            const response = await api.get('/backups/programacion/');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error obteniendo programación de backups:', error);
            throw error;
        }
    },

    /**
     * Exportar historial de backups
     */
    async exportarHistorial(formato: 'pdf' | 'excel'): Promise<Blob> {
        try {
            const response = await api.get(`/backups/exportar-historial/`, {
                params: { formato },
                responseType: 'blob'
            });
            return response.data;
        } catch (error: any) {
            console.error('❌ Error exportando historial:', error);
            throw error;
        }
    },

    /**
     * Validar espacio disponible en disco
     */
    async validarEspacio(): Promise<{
        espacio_total_gb: number;
        espacio_usado_gb: number;
        espacio_disponible_gb: number;
        porcentaje_usado: number;
        backups_espacio_gb: number;
        puede_crear_backup: boolean;
    }> {
        try {
            const response = await api.get('/backups/espacio-disco/');
            return response.data;
        } catch (error: any) {
            console.error('❌ Error validando espacio:', error);
            throw error;
        }
    },

    /**
     * Obtener logs de backups
     */
    async obtenerLogs(params?: {
        desde?: string;
        hasta?: string;
        tipo?: string;
        limite?: number;
    }): Promise<Array<{
        fecha: string;
        tipo: string;
        mensaje: string;
        nivel: 'info' | 'warning' | 'error';
        detalles?: any;
    }>> {
        try {
            const response = await api.get('/backups/logs/', { params });
            return normalizeListResponse(response.data);
        } catch (error: any) {
            console.error('❌ Error obteniendo logs:', error);
            throw error;
        }
    },
};
