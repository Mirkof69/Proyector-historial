/**
 * ============================================================================= 
 * CONFIGURATION SERVICE
 * =============================================================================
 * Servicio para gestionar la configuración del sistema, horarios y backups
 */

import api from './api';

interface SistemaConfig {
    id: number;
    nombre_clinica: string;
    direccion: string;
    telefono_contacto: string;
    email_contacto: string;
    logo?: string;
    modo_mantenimiento: boolean;
    permitir_registro_publico: boolean;
    dias_retencion_logs: number;
    smtp_host: string;
    smtp_port: number;
    smtp_user: string;
    smtp_secure: boolean;
    fecha_actualizacion: string;
}

interface HorarioAtencion {
    id: number;
    dia: string;
    dia_display: string;
    activo: boolean;
    hora_inicio: string; // "HH:MM"
    hora_fin: string; // "HH:MM"
    fecha_actualizacion: string;
}

interface BackupInfo {
    filename: string;
    path: string;
    size: number;
    size_formatted: string;
    created_at: string;
    created_timestamp: string;
    type: 'manual' | 'automatic';
}

interface BackupCreateResponse {
    success: boolean;
    filename?: string;
    path?: string;
    size?: number;
    size_formatted?: string;
    message: string;
}

// =============================================================================
// CONFIGURACIÓN GENERAL
// =============================================================================

const getConfiguracion = async (): Promise<SistemaConfig> => {
    const response = await api.get('/reportes/configuracion/general/');
    return response.data;
};

const updateConfiguracion = async (data: FormData): Promise<SistemaConfig> => {
    // Usar FormData para soportar subida de archivos (logo)
    const response = await api.post('/reportes/configuracion/general/', data, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};

// =============================================================================
// HORARIOS DE ATENCIÓN
// =============================================================================

const getHorarios = async (): Promise<HorarioAtencion[]> => {
    const response = await api.get('/reportes/configuracion/horarios/');
    return response.data;
};

const updateHorarios = async (horarios: Partial<HorarioAtencion>[]): Promise<HorarioAtencion[]> => {
    const response = await api.post('/reportes/configuracion/horarios/', horarios);
    return response.data;
};

// =============================================================================
// BACKUPS DE BASE DE DATOS
// =============================================================================

const crearBackup = async (): Promise<BackupCreateResponse> => {
    const response = await api.post('/reportes/configuracion/backups/create/');
    return response.data;
};

const listarBackups = async (): Promise<BackupInfo[]> => {
    const response = await api.get('/reportes/configuracion/backups/');
    return response.data;
};

const descargarBackup = async (filename: string): Promise<Blob> => {
    const response = await api.get(`/reportes/configuracion/backups/${filename}/`, {
        responseType: 'blob',
    });

    // Crear un objeto URL para descargar el archivo
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    return response.data;
};

const eliminarBackup = async (filename: string): Promise<void> => {
    await api.delete(`/reportes/configuracion/backups/${filename}/delete/`);
};

// =============================================================================
// OBJETO EXPORTADO POR DEFECTO
// =============================================================================

const configService = {
    // Configuración
    getConfiguracion,
    updateConfiguracion,

    // Horarios
    getHorarios,
    updateHorarios,

    // Backups
    crearBackup,
    listarBackups,
    descargarBackup,
    eliminarBackup,
};

export default configService;
