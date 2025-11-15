/**
 * =============================================================================
 * SERVICIO DE AUTENTICACIÓN
 * =============================================================================
 * Maneja login, logout, registro y gestión de tokens JWT
 * =============================================================================
 */

import api from './api';
import { LoginCredentials, LoginResponse, Usuario } from '../types';

class AuthService {
  /**
   * Iniciar sesión
   */
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await api.post<LoginResponse>('/usuarios/login/', credentials);
      const { access, refresh, user } = response.data;

      // Guardar tokens y usuario en localStorage
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user', JSON.stringify(user));

      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.message ||
        error.response?.data?.detail ||
        'Error al iniciar sesión'
      );
    }
  }

  /**
   * Cerrar sesión
   */
  async logout(): Promise<void> {
    try {
      await api.post('/usuarios/logout/');
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    } finally {
      // Limpiar localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  }

  /**
   * Verificar si el usuario está autenticado
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  /**
   * Obtener usuario actual
   */
  getCurrentUser(): Usuario | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch (error) {
        return null;
      }
    }
    return null;
  }

  /**
   * Obtener perfil del usuario actual
   */
  async getProfile(): Promise<Usuario> {
    const response = await api.get<Usuario>('/usuarios/perfil/');
    const user = response.data;
    localStorage.setItem('user', JSON.stringify(user));
    return user;
  }

  /**
   * Actualizar perfil
   */
  async updateProfile(data: Partial<Usuario>): Promise<Usuario> {
    const response = await api.patch<Usuario>('/usuarios/perfil/', data);
    const user = response.data;
    localStorage.setItem('user', JSON.stringify(user));
    return user;
  }

  /**
   * Cambiar contraseña
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/usuarios/cambiar-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  }

  /**
   * Solicitar recuperación de contraseña
   */
  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/usuarios/solicitar-recuperacion-password/', { email });
  }

  /**
   * Recuperar contraseña con token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/usuarios/recuperar-password/', {
      token,
      new_password: newPassword,
    });
  }

  /**
   * Registro público (para pacientes)
   */
  async register(data: {
    username: string;
    email: string;
    password: string;
    nombre: string;
    apellido: string;
    telefono?: string;
  }): Promise<Usuario> {
    const response = await api.post<Usuario>('/usuarios/registro/', data);
    return response.data;
  }

  /**
   * Obtener token de acceso
   */
  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Obtener refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Verificar si hay token válido
   */
  hasToken(): boolean {
    const token = this.getToken();
    return token !== null && token !== '';
  }
}

export const authService = new AuthService();
export default authService;
