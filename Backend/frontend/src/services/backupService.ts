/**
 * =============================================================================
 * SERVICIO DE BACKUPS - GESTIÓN DE COPIAS DE SEGURIDAD
 * =============================================================================
 * Cliente API para gestión de backups de base de datos.
 *
 * El backend real (Backend/reportes/services/backup_service.py +
 * views_config.py) solo soporta 5 operaciones: crear, listar, descargar,
 * eliminar y restaurar — todas identificadas por `filename` (no por id).
 * =============================================================================
 */

import api from './api';

export interface Backup {
    filename: string;
    size: number;
    created_at: string;
}

export interface CrearBackupResult {
    success: boolean;
    filename: string;
    filepath: string;
    message: string;
}

export interface RestaurarBackupResult {
    success: boolean;
    filename: string;
    backup_seguridad: string;
    message: string;
}

function normalizeListResponse<T>(data: any): T[] {
    if (Array.isArray(data)) return data as T[];
    if (data?.results && Array.isArray(data.results)) return data.results as T[];
    console.warn('⚠️ backupService: Respuesta no es array:', data);
    return [];
}

export const backupService = {
    /**
     * Listar todos los backups disponibles
     */
    async listar(): Promise<Backup[]> {
        try {
            const response = await api.get<Backup[]>('/reportes/configuracion/backups/');
            return normalizeListResponse<Backup>(response.data);
        } catch (error: any) {
            console.error('❌ Error listando backups:', error);
            throw error;
        }
    },

    /**
     * Crear un nuevo backup real con pg_dump
     */
    async crear(): Promise<CrearBackupResult> {
        try {
            const response = await api.post<CrearBackupResult>('/reportes/configuracion/backups/create/', {});
            return response.data;
        } catch (error: any) {
            console.error('❌ Error creando backup:', error);
            throw error;
        }
    },

    /**
     * Descargar un backup
     */
    async descargar(filename: string): Promise<Blob> {
        try {
            const response = await api.get(`/reportes/configuracion/backups/${filename}/`, {
                responseType: 'blob'
            });
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error descargando backup ${filename}:`, error);
            throw error;
        }
    },

    /**
     * Eliminar un backup
     */
    async eliminar(filename: string): Promise<void> {
        try {
            await api.delete(`/reportes/configuracion/backups/${filename}/delete/`);
        } catch (error: any) {
            console.error(`❌ Error eliminando backup ${filename}:`, error);
            throw error;
        }
    },

    /**
     * Restaurar la base de datos completa desde un backup.
     *
     * ⚠️ Operación destructiva: sobrescribe toda la base de datos actual.
     * El backend crea automáticamente un backup de seguridad de la base
     * actual antes de ejecutar el restore.
     */
    async restaurar(filename: string): Promise<RestaurarBackupResult> {
        try {
            const response = await api.post<RestaurarBackupResult>(
                `/reportes/configuracion/backups/${filename}/restore/`,
                {},
            );
            return response.data;
        } catch (error: any) {
            console.error(`❌ Error restaurando backup ${filename}:`, error);
            throw error;
        }
    },
};
