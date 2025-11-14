/**
 * =============================================================================
 * SERVICIO DE USUARIOS
 * =============================================================================
 * CRUD y gestión de usuarios del sistema
 * =============================================================================
 */

import api from './api';
import { Usuario, PaginatedResponse } from '../types';

class UsuariosService {
  /**
   * Listar usuarios con paginación y filtros
   */
  async list(params?: {
    page?: number;
    pageSize?: number;
    rol?: string;
    activo?: boolean;
    search?: string;
  }): Promise<PaginatedResponse<Usuario>> {
    const response = await api.get<PaginatedResponse<Usuario>>('/usuarios/', { params });
    return response.data;
  }

  /**
   * Obtener un usuario por ID
   */
  async get(id: number): Promise<Usuario> {
    const response = await api.get<Usuario>(`/usuarios/${id}/`);
    return response.data;
  }

  /**
   * Crear un nuevo usuario
   */
  async create(data: Partial<Usuario> & { password: string }): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/', data);
    return response.data;
  }

  /**
   * Actualizar usuario
   */
  async update(id: number, data: Partial<Usuario>): Promise<Usuario> {
    const response = await api.patch<Usuario>(`/usuarios/${id}/`, data);
    return response.data;
  }

  /**
   * Eliminar usuario (soft delete)
   */
  async delete(id: number): Promise<void> {
    await api.delete(`/usuarios/${id}/`);
  }

  /**
   * Activar usuario
   */
  async activate(id: number): Promise<Usuario> {
    const response = await api.post<Usuario>(`/usuarios/${id}/activar/`);
    return response.data;
  }

  /**
   * Desactivar usuario
   */
  async deactivate(id: number): Promise<Usuario> {
    const response = await api.post<Usuario>(`/usuarios/${id}/desactivar/`);
    return response.data;
  }

  /**
   * Bloquear usuario
   */
  async block(userId: number): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/bloquear/', { user_id: userId });
    return response.data;
  }

  /**
   * Desbloquear usuario
   */
  async unblock(userId: number): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/desbloquear/', { user_id: userId });
    return response.data;
  }

  /**
   * Listar médicos
   */
  async listMedicos(): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/medicos/');
    return response.data;
  }

  /**
   * Listar enfermeros
   */
  async listEnfermeros(): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/enfermeros/');
    return response.data;
  }

  /**
   * Estadísticas de usuarios
   */
  async statistics(): Promise<any> {
    const response = await api.get('/usuarios/estadisticas/');
    return response.data;
  }

  /**
   * Buscar usuarios
   */
  async search(query: string): Promise<Usuario[]> {
    const response = await api.get<Usuario[]>('/usuarios/buscar/', { params: { q: query } });
    return response.data;
  }

  /**
   * Restablecer contraseña (admin)
   */
  async resetPasswordAdmin(userId: number, newPassword: string): Promise<void> {
    await api.post('/usuarios/restablecer-password-admin/', {
      user_id: userId,
      new_password: newPassword,
    });
  }
}

export const usuariosService = new UsuariosService();
export default usuariosService;
