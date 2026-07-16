/**
 * =================================================================================
 * USUARIOS SERVICE - SERVICIO COMPLETO PARA GESTIÓN DE USUARIOS
 * =================================================================================
 * Gestión completa de usuarios con permisos, horarios, fotos y más
 * =================================================================================
 */

import api from './api';
import { logger } from '../utils/logger';

// =================================================================================
// INTERFACES
// =================================================================================

export interface Permiso {
  id: number;
  name: string;
  codename: string;
  app_label: string;
  model: string;
}

interface Grupo {
  id: number;
  name: string;
}

export interface HorarioAtencion {
  id?: number;
  usuario?: number;
  dia_semana: string;
  dia_semana_display?: string;
  hora_inicio: string;
  hora_fin: string;
  activo: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
}

export interface Usuario {
  id?: number;
  uuid?: string;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  iniciales?: string;
  rol: 'medico' | 'enfermero' | 'enfermera' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';
  rol_display?: string;
  especialidad?: string;
  telefono?: string;
  foto?: File | string | null;
  foto_url?: string | null;
  descripcion?: string;
  activo: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  fecha_creacion?: string;
  fecha_modificacion?: string;
  last_login?: string | null;

  // Relaciones
  horarios_atencion?: HorarioAtencion[];
  permisos?: Permiso[];
  grupos?: Grupo[];
}

export interface UsuarioCreate {
  email: string;
  password: string;
  password_confirm: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  rol: 'medico' | 'enfermero' | 'enfermera' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';
  especialidad?: string;
  telefono?: string;
  foto?: File | null;
  descripcion?: string;
  activo?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  permisos_ids?: number[];
  grupos_ids?: number[];
}

export interface UsuarioUpdate {
  email?: string;
  password?: string;
  password_confirm?: string;
  nombre?: string;
  apellido_paterno?: string;
  apellido_materno?: string;
  rol?: 'medico' | 'enfermero' | 'enfermera' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';
  especialidad?: string;
  telefono?: string;
  foto?: File | null;
  descripcion?: string;
  activo?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  permisos_ids?: number[];
  grupos_ids?: number[];
}

interface CambiarPasswordData {
  password_actual: string;
  password_nueva: string;
  password_nueva_confirm: string;
}

interface AdminCambiarPasswordData {
  password_nueva: string;
  password_nueva_confirm: string;
}

// =================================================================================
// SERVICIO
// =================================================================================

export const usuariosService = {
  /**
   * Obtener todos los usuarios activos
   */
  async getAll(params?: {
    rol?: string;
    activo?: boolean;
    search?: string;
  }): Promise<Usuario[]> {
    try {
      const response = await api.get<any>('/usuarios/', { params });
      if (response.data && Array.isArray(response.data.results)) {
        return response.data.results;
      }
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      console.error('Error fetching usuarios:', error);
      throw error;
    }
  },

  /**
   * Obtener TODOS los usuarios (incluyendo inactivos) - Solo admin
   */
  async getTodos(): Promise<Usuario[]> {
    try {
      const response = await api.get<Usuario[]>('/usuarios/todos/');
      return response.data;
    } catch (error) {
      console.error('Error fetching todos los usuarios:', error);
      throw error;
    }
  },

  /**
   * Obtener usuario por ID
   */
  async getById(id: number): Promise<Usuario> {
    try {
      const response = await api.get<Usuario>(`/usuarios/${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener usuario actual (me)
   */
  async getMe(): Promise<Usuario> {
    try {
      const response = await api.get<Usuario>('/usuarios/me/');
      return response.data;
    } catch (error) {
      console.error('Error fetching current user:', error);
      throw error;
    }
  },

  /**
   * Crear nuevo usuario
   */
  async create(data: UsuarioCreate): Promise<Usuario> {
    try {
      // Usar FormData si hay archivo de foto
      let payload: FormData | UsuarioCreate = data;

      if (data.foto instanceof File) {
        const formData = new FormData();
        Object.keys(data).forEach(key => {
          const value = (data as any)[key];
          if (value !== null && value !== undefined) {
            if (key === 'permisos_ids' || key === 'grupos_ids') {
              formData.append(key, JSON.stringify(value));
            } else if (key === 'foto' && value instanceof File) {
              formData.append(key, value);
            } else {
              formData.append(key, String(value));
            }
          }
        });
        payload = formData;
      }

      const response = await api.post<Usuario>('/usuarios/', payload, {
        headers: data.foto instanceof File ? { 'Content-Type': 'multipart/form-data' } : {}
      });
      return response.data;
    } catch (error) {
      console.error('Error creating usuario:', error);
      throw error;
    }
  },

  /**
   * Actualizar usuario
   */
  async update(id: number, data: UsuarioUpdate): Promise<Usuario> {
    try {
      // Usar FormData si hay archivo de foto
      let payload: FormData | UsuarioUpdate = data;

      if (data.foto instanceof File) {
        const formData = new FormData();
        Object.keys(data).forEach(key => {
          const value = (data as any)[key];
          if (value !== null && value !== undefined) {
            if (key === 'permisos_ids' || key === 'grupos_ids') {
              formData.append(key, JSON.stringify(value));
            } else if (key === 'foto' && value instanceof File) {
              formData.append(key, value);
            } else {
              formData.append(key, String(value));
            }
          }
        });
        payload = formData;
      }

      const response = await api.put<Usuario>(`/usuarios/${id}/`, payload, {
        headers: data.foto instanceof File ? { 'Content-Type': 'multipart/form-data' } : {}
      });
      return response.data;
    } catch (error) {
      console.error(`Error updating usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Eliminar usuario (baja lógica)
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/usuarios/${id}/`);
    } catch (error) {
      console.error(`Error deleting usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Activar usuario
   */
  async activar(id: number): Promise<Usuario> {
    try {
      const response = await api.post<Usuario>(`/usuarios/${id}/activar/`);
      return response.data;
    } catch (error) {
      console.error(`Error activando usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Desactivar usuario (baja lógica)
   */
  async desactivar(id: number): Promise<Usuario> {
    try {
      const response = await api.post<Usuario>(`/usuarios/${id}/desactivar/`);
      return response.data;
    } catch (error) {
      console.error(`Error desactivando usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Cambiar contraseña (usuario)
   */
  async cambiarPassword(id: number, data: CambiarPasswordData): Promise<{ mensaje: string }> {
    try {
      const response = await api.post<{ mensaje: string }>(`/usuarios/${id}/cambiar_password/`, data);
      return response.data;
    } catch (error) {
      console.error(`Error cambiando password usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Admin cambia contraseña (sin requerir contraseña actual)
   */
  async adminCambiarPassword(id: number, data: AdminCambiarPasswordData): Promise<{ mensaje: string }> {
    try {
      const response = await api.post<{ mensaje: string }>(`/usuarios/${id}/admin_cambiar_password/`, data);
      return response.data;
    } catch (error) {
      console.error(`Error admin cambiando password usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener permisos del usuario
   */
  async getPermisos(id: number): Promise<Permiso[]> {
    try {
      const response = await api.get<Permiso[]>(`/usuarios/${id}/permisos/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching permisos usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Asignar permisos al usuario
   */
  async asignarPermisos(id: number, permisos_ids: number[]): Promise<{ mensaje: string; permisos: Permiso[] }> {
    try {
      const response = await api.post<{ mensaje: string; permisos: Permiso[] }>(
        `/usuarios/${id}/asignar_permisos/`,
        { permisos_ids }
      );
      return response.data;
    } catch (error) {
      console.error(`Error asignando permisos usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Quitar permisos del usuario
   */
  async quitarPermisos(id: number, permisos_ids: number[]): Promise<{ mensaje: string; permisos: Permiso[] }> {
    try {
      const response = await api.post<{ mensaje: string; permisos: Permiso[] }>(
        `/usuarios/${id}/quitar_permisos/`,
        { permisos_ids }
      );
      return response.data;
    } catch (error) {
      console.error(`Error quitando permisos usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener todos los permisos disponibles
   */
  async getPermisosDisponibles(): Promise<Permiso[]> {
    try {
      const response = await api.get<Permiso[]>('/usuarios/permisos_disponibles/');
      return response.data;
    } catch (error) {
      console.error('Error fetching permisos disponibles:', error);
      throw error;
    }
  },

  /**
   * Obtener horarios del usuario
   */
  async getHorarios(id: number): Promise<HorarioAtencion[]> {
    try {
      const response = await api.get<HorarioAtencion[]>(`/usuarios/${id}/horarios/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching horarios usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Agregar horario al usuario
   */
  async agregarHorario(id: number, horario: Omit<HorarioAtencion, 'id' | 'usuario'>): Promise<HorarioAtencion> {
    try {
      const response = await api.post<HorarioAtencion>(`/usuarios/${id}/agregar_horario/`, horario);
      return response.data;
    } catch (error) {
      console.error(`Error agregando horario usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener actividad del usuario (logs de acciones)
   * NUEVO ENDPOINT - CONECTADO AL BACKEND
   */
  async getActividad(id: number, params?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    accion?: string;
    page?: number;
    page_size?: number;
  }): Promise<any> {
    try {
      const response = await api.get(`/usuarios/${id}/actividad/`, { params });
      logger.log(`✅ Actividad del usuario ${id} obtenida`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        console.warn('⚠️ Endpoint actividad no disponible (404) - retornando datos vacíos');
        return {
          count: 0,
          results: [],
          mensaje: 'No hay actividad registrada'
        };
      }
      console.error(`Error obteniendo actividad usuario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Obtener médicos activos
   */
  async getMedicos(): Promise<Usuario[]> {
    try {
      const response = await api.get<Usuario[]>('/usuarios/medicos/');
      return response.data;
    } catch (error) {
      console.error('Error fetching médicos:', error);
      throw error;
    }
  },

  /**
   * Obtener enfermeros activos
   */
  async getEnfermeros(): Promise<Usuario[]> {
    try {
      const response = await api.get<Usuario[]>('/usuarios/enfermeros/');
      return response.data;
    } catch (error) {
      console.error('Error fetching enfermeros:', error);
      throw error;
    }
  },

  // Aliases para compatibilidad
  async listar(params?: any): Promise<Usuario[]> {
    return this.getAll(params);
  },

  async crear(data: UsuarioCreate): Promise<Usuario> {
    return this.create(data);
  },

  async actualizar(id: number, data: UsuarioUpdate): Promise<Usuario> {
    return this.update(id, data);
  },

  async eliminar(id: number): Promise<void> {
    return this.delete(id);
  },
};

// =================================================================================
// HORARIOS SERVICE
// =================================================================================

export const horariosService = {
  /**
   * Obtener todos los horarios
   */
  async getAll(params?: { usuario_id?: number }): Promise<HorarioAtencion[]> {
    try {
      const response = await api.get<any>('/usuarios/horarios/', { params });
      const data = response.data;
      if (Array.isArray(data)) return data;
      if (data && Array.isArray(data.results)) return data.results;
      return [];
    } catch (error) {
      console.error('Error fetching horarios:', error);
      throw error;
    }
  },

  /**
   * Obtener horario por ID
   */
  async getById(id: number): Promise<HorarioAtencion> {
    try {
      const response = await api.get<HorarioAtencion>(`/usuarios/horarios/${id}/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching horario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Crear horario
   */
  async create(horario: Omit<HorarioAtencion, 'id'>): Promise<HorarioAtencion> {
    try {
      const response = await api.post<HorarioAtencion>('/usuarios/horarios/', horario);
      return response.data;
    } catch (error) {
      console.error('Error creating horario:', error);
      throw error;
    }
  },

  /**
   * Actualizar horario
   */
  async update(id: number, horario: Partial<HorarioAtencion>): Promise<HorarioAtencion> {
    try {
      const response = await api.put<HorarioAtencion>(`/usuarios/horarios/${id}/`, horario);
      return response.data;
    } catch (error) {
      console.error(`Error updating horario ${id}:`, error);
      throw error;
    }
  },

  /**
   * Eliminar horario
   */
  async delete(id: number): Promise<void> {
    try {
      await api.delete(`/usuarios/horarios/${id}/`);
    } catch (error) {
      console.error(`Error deleting horario ${id}:`, error);
      throw error;
    }
  },
};


