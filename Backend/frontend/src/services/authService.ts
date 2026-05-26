/**
 * =============================================================================
 * SERVICIO DE AUTENTICACIÓN — SISTEMA CLÍNICO PERINATAL
 * =============================================================================
 * Tipos corregidos para:
 * - Flujo MFA de dos pasos (mfa_required / mfa_setup_required)
 * - Respuesta de login normalizada (access/refresh en múltiples formatos)
 * - Usuario con mfa_enabled, mfa_obligatorio y rol exhaustivo
 * =============================================================================
 */

import { post, api } from './api';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES Y TIPOS
// ═══════════════════════════════════════════════════════════════════════════

interface ApiError {
  errores?: Record<string, string | string[]>;
  error?: string;
  detail?: string;
  [key: string]: any;
}

export interface LoginCredentials {
  email: string;
  password: string;
  totp_code?: string;
}

/** Roles disponibles en el sistema */
type UserRole = 'medico' | 'enfermera' | 'enfermero' | 'administrador' | 'paciente' | 'recepcion' | 'laboratorista';

interface LoginResponseUser {
  id: number;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  rol: UserRole;
  especialidad?: string;
  telefono?: string;
  foto_perfil?: string;
  mfa_enabled?: boolean;
  mfa_obligatorio?: boolean;
}

/** Respuesta de login exitoso (HTTP 200 con tokens) */
interface LoginSuccessResponse {
  access?: string;
  access_token?: string;
  token?: string;
  refresh?: string;
  refresh_token?: string;
  user?: LoginResponseUser;
  usuario?: LoginResponseUser;
  permisos?: string[];
}

/** Respuesta intermedia: el backend pide el código TOTP */
interface MfaRequiredResponse {
  mfa_required: true;
  mensaje: string;
}

/** Respuesta intermedia: médico/admin sin MFA configurado — debe hacer setup */
interface MfaSetupRequiredResponse {
  mfa_setup_required: true;
  mensaje: string;
}

/** Unión de todos los posibles resultados del endpoint /login/ */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type LoginApiResponse =
  | LoginSuccessResponse
  | MfaRequiredResponse
  | MfaSetupRequiredResponse;

/** Resultado tipado para el flujo de login de la UI */
interface LoginResult {
  success: true;
  user: LoginResponseUser;
}

interface MfaRequiredResult {
  success: false;
  mfaRequired: true;
  setupRequired?: false;
}

interface MfaSetupRequiredResult {
  success: false;
  mfaRequired?: false;
  setupRequired: true;
  mensaje: string;
}

export type LoginFlowResult = LoginResult | MfaRequiredResult | MfaSetupRequiredResult;

export interface Usuario {
  id: number;
  username?: string;
  email: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  rol: UserRole;
  especialidad?: string;
  telefono?: string;
  activo?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  permisos?: string[];
  foto_perfil?: string;
  ultimo_acceso?: string;
  fecha_registro?: string;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
  mfa_enabled?: boolean;
  mfa_obligatorio?: boolean;
}

/** Respuesta del endpoint /mfa/setup/ */
export interface MfaSetupResponse {
  secret: string;
  qr_code: string;
  uri: string;
  mensaje: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// GUARD FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function isMfaRequired(data: any): data is MfaRequiredResponse {
  return data?.mfa_required === true;
}

function isMfaSetupRequired(data: any): data is MfaSetupRequiredResponse {
  return data?.mfa_setup_required === true;
}

// ═══════════════════════════════════════════════════════════════════════════
// AUTH SERVICE CLASS
// ═══════════════════════════════════════════════════════════════════════════

class AuthService {

  // ─────────────────────────────────────────────────────────────────────────
  // MÉTODOS INTERNOS AUXILIARES
  // ─────────────────────────────────────────────────────────────────────────

  private normalizeListResponse<T>(raw: any, label: string): T[] {
    try {
      if (raw && Array.isArray(raw.results)) {
        console.log(`✅ ${label} obtenidos (paginado):`, raw.results.length);
        return raw.results as T[];
      }
      if (raw && Array.isArray(raw.data)) {
        return raw.data as T[];
      }
      if (Array.isArray(raw)) {
        return raw as T[];
      }
      console.warn(`⚠️ Formato inesperado para ${label}:`, raw);
      return [];
    } catch (e) {
      console.error(`❌ Error normalizando respuesta de ${label}:`, e);
      return [];
    }
  }

  private handleApiError(error: any, context: string): never {
    console.error(`❌ Error en ${context}:`, error);
    if (error.response?.data) {
      const errorData = error.response.data as ApiError;
      if (errorData.errores) {
        const msgs = Object.entries(errorData.errores)
          .map(([f, m]) => `${f}: ${Array.isArray(m) ? m.join(', ') : m}`)
          .join(' | ');
        error.message = msgs;
      } else if (errorData.error) {
        error.message = errorData.error;
      } else if (errorData.detail) {
        error.message = errorData.detail;
      }
    }
    throw error;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // AUTENTICACIÓN
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Primer paso del login (email + password).
   * Devuelve un LoginFlowResult que puede indicar:
   * - success: true → login completo, tokens guardados
   * - mfaRequired: true → el backend pide el código TOTP (segundo paso)
   * - setupRequired: true → médico/admin sin MFA configurado → ir a /setup-mfa
   */
  async loginStep1(credentials: { email: string; password: string }): Promise<LoginFlowResult> {
    const rawData = await api.login(credentials.email, credentials.password);

    // ── Caso: MFA setup requerido (HTTP 403 con mfa_setup_required) ──────
    if (isMfaSetupRequired(rawData)) {
      return {
        success: false,
        setupRequired: true,
        mensaje: rawData.mensaje,
      };
    }

    // ── Caso: MFA code requerido (HTTP 200 con mfa_required) ─────────────
    if (isMfaRequired(rawData)) {
      // Guardar temp_token en sessionStorage para usarlo en loginStep2
      // sessionStorage se limpia al cerrar pestaña — más seguro que localStorage
      if ((rawData as any).temp_token) {
        sessionStorage.setItem('mfa_temp_token', (rawData as any).temp_token);
      }
      return {
        success: false,
        mfaRequired: true,
      };
    }

    // ── Caso: Login exitoso ───────────────────────────────────────────────
    const user = rawData.user || rawData.usuario || rawData;
    return { success: true, user };
  }

  /**
   * Segundo paso del login: verifica el código TOTP usando el temp_token del paso 1.
   * POST /api/usuarios/mfa-verify/ con {temp_token, totp_code}
   */
  async loginStep2(credentials: LoginCredentials): Promise<LoginResult> {
    try {
      const tempToken = sessionStorage.getItem('mfa_temp_token');
      if (!tempToken) {
        throw new Error('Sesión MFA expirada. Vuelva a iniciar sesión.');
      }

      const response = await api.apiClient.post('/usuarios/mfa-verify/', {
        temp_token: tempToken,
        totp_code: credentials.totp_code,
      });

      // Limpiar temp_token — ya no se necesita
      sessionStorage.removeItem('mfa_temp_token');

      const data = response.data;
      const accessToken = data.access || data.token || data.access_token;
      const refreshToken = data.refresh || data.refresh_token;
      if (accessToken) {
        const { saveTokens } = await import('./api');
        saveTokens(accessToken, refreshToken);
      }
      const user = data.user || data.usuario || data;
      if (user) {
        const safeUser = { ...user };
        delete safeUser.access;
        delete safeUser.refresh;
        localStorage.setItem('user:v1', JSON.stringify(safeUser));
      }
      return { success: true, user };
    } catch (error: any) {
      this.handleApiError(error, 'loginStep2');
    }
  }

  /** Login simple (sin MFA) — mantiene retrocompatibilidad */
  async login(credentials: LoginCredentials): Promise<LoginSuccessResponse> {
    try {
      const response = await api.login(credentials.email, credentials.password);
      return response;
    } catch (error: any) {
      this.handleApiError(error, 'login');
    }
  }

  async logout(): Promise<void> {
    try {
      await api.logout();
    } catch (error: any) {
      console.error('❌ Error al cerrar sesión:', error);
    }
  }

  async refreshToken(): Promise<LoginSuccessResponse> {
    try {
      const refreshToken = this.getRefreshToken();
      if (!refreshToken) throw new Error('No hay refresh token disponible');
      const response = await post<LoginSuccessResponse>('/token/refresh/', { refresh: refreshToken });
      return response;
    } catch (error: any) {
      this.handleApiError(error, 'refresh token');
    }
  }

  /** Envía el código TOTP al backend para completar el setup */
  async confirmMfa(code: string): Promise<{ mfa_enabled: boolean; mensaje: string }> {
    const response = await api.apiClient.post('/usuarios/mfa/confirm/', { code });
    return response.data;
  }

  /** Obtiene QR y secreto para configurar Google Authenticator */
  async setupMfa(): Promise<MfaSetupResponse> {
    const response = await api.apiClient.post('/usuarios/mfa/setup/');
    return response.data;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // TOKEN MANAGEMENT
  // ─────────────────────────────────────────────────────────────────────────

  getToken(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('token');
  }

  getAccessToken(): string | null {
    return this.getToken();
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  isAuthenticated(): boolean {
    return api.isAuthenticated();
  }

  getCurrentUser(): Usuario | null {
    return api.getCurrentUser() as Usuario | null;
  }

  setToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  setRefreshToken(token: string): void {
    localStorage.setItem('refresh_token', token);
  }

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token');
    localStorage.removeItem('user:v1');
  }

  hasPermission(permissionCodename: string): boolean {
    const user = this.getCurrentUser();
    if (!user) return false;
    if (user.rol === 'administrador' || user.is_superuser) return true;
    return user.permisos?.includes(permissionCodename) ?? false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTAR INSTANCIA ÚNICA Y TIPOS
// ═══════════════════════════════════════════════════════════════════════════

export const authService = new AuthService();

