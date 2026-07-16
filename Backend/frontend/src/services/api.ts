/**
 * =============================================================================
 * CONFIGURACIÓN DE AXIOS - API CLIENT (ENTERPRISE MASTER)
 * =============================================================================
 * Configuración centralizada de Axios con:
 * - Interceptores de autenticación automática
 * - Manejo de cola de peticiones durante el refresco de token (Concurrency)
 * - Soporte para subida de archivos (Multipart/FormData)
 * - Compatibilidad total con Django REST Framework + Simple JWT
 * - Tipado estricto y manejo de errores centralizado con Modal
 * =============================================================================
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
  AxiosRequestConfig
} from 'axios';
import { notification, Modal } from 'antd';
import { logger } from '../utils/logger';

// ═══════════════════════════════════════════════════════════════════════════
// 1. CONFIGURACIÓN BÁSICA Y CONSTANTES
// ═══════════════════════════════════════════════════════════════════════════

// URL de la API:
// - HTTPS (túnel/localtunnel): usa /api relativo → React dev server hace proxy a localhost:8000
// - HTTP local (localhost/IP): apunta directo a localhost:8000/api
const getApiUrl = (): string => {
  const envUrl = process.env.REACT_APP_API_URL;
  if (envUrl) return envUrl;

  if (window.location.protocol === 'https:') return '/api';

  return `http://${window.location.hostname}:8000/api`;
};

export const API_URL = getApiUrl();
const TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT || '30000', 10);
const IS_DEV = process.env.NODE_ENV === 'development';


// ═══════════════════════════════════════════════════════════════════════════
// 2. INSTANCIAS DE AXIOS
// ═══════════════════════════════════════════════════════════════════════════

// Header requerido por localtunnel para evitar la página de bypass
const tunnelHeaders = API_URL.includes('.loca.lt')
  ? { 'bypass-tunnel-reminder': 'true' }
  : {};

// ── SEGURIDAD: JWT en cookies httpOnly ──────────────────────────────────────
// Los tokens ya NO se guardan en localStorage (mitiga XSS). El servidor los
// emite como cookies httpOnly y el navegador las envía solo con
// withCredentials. CSRF: Django emite la cookie `csrftoken` (legible) y
// axios la reenvía como header X-CSRFToken en métodos no-safe.
const CSRF_CONFIG = {
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  withXSRFToken: true, // axios >=1.6: aplicar XSRF también cross-origin
} as const;

// Defaults globales: cubren también los usos de `axios` directo en la app
axios.defaults.withCredentials = true;
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';
(axios.defaults as any).withXSRFToken = true;

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...tunnelHeaders,
  },
  ...CSRF_CONFIG,
});

const refreshClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  ...CSRF_CONFIG,
});

// ═══════════════════════════════════════════════════════════════════════════
// 3. GESTIÓN DE SESIÓN (los tokens viven en cookies httpOnly del servidor)
// ═══════════════════════════════════════════════════════════════════════════

/** Lee la cookie csrftoken (única cookie legible a propósito). */
export const getCsrfToken = (): string | null => {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
};

/**
 * @deprecated Los JWT viven en cookies httpOnly gestionadas por el servidor;
 * ya no hay nada que guardar en el cliente. Se conserva como no-op para
 * compatibilidad con llamadas antiguas.
 */
export const saveTokens = (_accessToken?: string, _refreshToken?: string): void => {
  if (IS_DEV) {
    logger.log('ℹ️ saveTokens(): no-op — los tokens viven en cookies httpOnly');
  }
};

const clearAuth = (): void => {
  // Limpieza de sesión local + restos de la implementación anterior
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user:v1');
  if (IS_DEV) {
    logger.log('🧹 Sesión limpiada - Usuario deslogueado');
  }
};

const isAuthenticated = (): boolean => {
  // Sin acceso al token (httpOnly): la señal de sesión es el usuario cacheado.
  // La autoridad real es el servidor (401 → refresh → login).
  return !!localStorage.getItem('user:v1');
};

// ═══════════════════════════════════════════════════════════════════════════
// 4. INTERCEPTOR DE REQUEST (Salida)
// ═══════════════════════════════════════════════════════════════════════════

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // La autenticación viaja en la cookie httpOnly (withCredentials);
    // no se inyecta header Authorization desde el cliente.
    if (IS_DEV) {
      logger.log(`🚀 [REQ] ${config.method?.toUpperCase()} ${config.url}`, {
        headers: config.headers,
        data: config.data,
        params: config.params
      });
    }
    return config;
  },
  (error: AxiosError) => {
    console.error('❌ Error en request interceptor:', error);
    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// 5. LÓGICA DE CONCURRENCIA (REFRESH TOKEN QUEUE)
// ═══════════════════════════════════════════════════════════════════════════

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

const refreshAccessToken = async (): Promise<void> => {
  try {
    // El refresh token viaja en la cookie httpOnly; el servidor rota los
    // tokens y responde seteando las nuevas cookies (body sin JWT).
    await refreshClient.post('/token/refresh/', {});
  } catch (error) {
    clearAuth();
    throw error;
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// 6. INTERCEPTOR DE RESPONSE (Llegada + Manejo de Errores)
// ═══════════════════════════════════════════════════════════════════════════

apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    if (IS_DEV) {
      logger.log(`✅ [RES] ${response.status} ${response.config.url}`);
    }
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Endpoints que pueden no existir (esperados 404s)
    const expectedMissingEndpoints = [
      '/antecedentes-personales/',
      '/antecedentes-obstetricos/',
      '/antecedentes-familiares/',
      '/notas-evolucion/por_paciente/'
    ];

    const isExpected404 = error.response?.status === 404 &&
      expectedMissingEndpoints.some(endpoint => originalRequest?.url?.includes(endpoint));

    if (IS_DEV && !isExpected404) {
      console.error(`❌ [ERR] ${error.response?.status} en ${originalRequest?.url}`, error.response?.data);
    }

    // --- CASO CRÍTICO: 401 (Token Expirado) ---
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (originalRequest.url?.includes('/token/refresh/') || originalRequest.url?.includes('/login/')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(() => apiClient(originalRequest))
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await refreshAccessToken();
        // La nueva cookie de access ya viaja con el retry
        processQueue(null, null);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        notification.error({
          message: 'Sesión Expirada',
          description: 'Tu sesión ha caducado por seguridad. Serás redirigido al login.',
          key: 'session_expired_key',
          duration: 4
        });
        clearAuth();
        setTimeout(() => window.location.href = '/login', 1500);
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // --- MANEJO DE OTROS ERRORES (400, 403, 404, 500) ---
    const status = error.response?.status;

    if (status === 403) {
      Modal.error({
        title: '⛔ Acceso Denegado',
        content: 'No tienes permisos suficientes para realizar esta acción.',
      });
    } else if (status === 404 && !isExpected404) {
      console.warn('Recurso no encontrado:', originalRequest.url);
    } else if (status === 500) {
      Modal.error({
        title: '🔥 Error del Servidor',
        content: 'Ocurrió un error interno en el servidor. Por favor, contacte a soporte técnico.',
      });
    } else if (!error.response) {
      Modal.error({
        title: '📡 Error de Conexión',
        content: 'No se pudo conectar con el servidor. Verifique su conexión a internet.',
      });
    } else if (status === 400) {
      const data = error.response?.data as Record<string, any> | { detail?: string };
      let content: string = 'Solicitud incorrecta.';

      if (data && typeof data === 'object' && 'detail' in data && data.detail) {
        content = data.detail;
      } else if (data && typeof data === 'object' && !Array.isArray(data)) {
        const errorList = Object.entries(data).map(([key, value]) => {
          const msg = Array.isArray(value) ? value[0] : value;
          return `${key}: ${msg}`;
        }).join('\n');
        content = errorList;
      }

      Modal.error({
        title: '⚠️ Datos Inválidos',
        content: content,
        styles: { body: { whiteSpace: 'pre-line' } }
      });
    }

    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// 7. MÉTODOS DE ACCESO A LA API (WRAPPERS)
// ═══════════════════════════════════════════════════════════════════════════

export const get = async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.get<T>(url, config);
  return response.data;
};

export const post = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
};

export const put = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
};

export const patch = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.patch<T>(url, data, config);
  return response.data;
};

const del = async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
};

export const postFormData = async <T = any>(url: string, formData: FormData, config: AxiosRequestConfig = {}): Promise<T> => {
  const response = await apiClient.post<T>(url, formData, {
    ...config,
    headers: {
      ...config.headers,
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// ═══════════════════════════════════════════════════════════════════════════
// 8. SERVICIO DE AUTENTICACIÓN (LÓGICA DE NEGOCIO)
// ═══════════════════════════════════════════════════════════════════════════

const login = async (email: string, password: string): Promise<any> => {
  try {
    if (IS_DEV) logger.log('🔐 Enviando credenciales...');
    const response = await apiClient.post('/usuarios/login/', { email, password });
    const data = response.data;

    // Flujo MFA de 2 pasos: la respuesta intermedia no trae usuario todavía
    if (data?.mfa_required || data?.mfa_setup_required) {
      return data;
    }

    // Los JWT llegan como cookies httpOnly (Set-Cookie); el body trae el user.
    const user = data.user || data.usuario;
    if (!user) {
      throw new Error('Respuesta de login inválida: no se recibió el usuario.');
    }

    const safeUser = { ...user };
    delete safeUser.access;
    delete safeUser.refresh;
    delete safeUser.token;
    localStorage.setItem('user:v1', JSON.stringify(safeUser));

    if (IS_DEV) logger.log('✅ Login exitoso (sesión por cookies httpOnly)');
    return data;
  } catch (error: any) {
    if (IS_DEV) console.error('❌ Login fallido:', error);
    throw error;
  }
};

const logout = async (): Promise<void> => {
  try {
    // El refresh viaja en la cookie httpOnly; el servidor blacklistea y
    // limpia las cookies JWT.
    await refreshClient.post('/usuarios/logout/', {});
  } catch (e) {
    console.warn('Logout local (servidor no respondió o token inválido)');
  } finally {
    clearAuth();
    window.location.href = '/login';
  }
};

const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('user:v1');
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch (e) {
      console.error('Error parseando usuario local');
      return null;
    }
  }
  return null;
};

// ═══════════════════════════════════════════════════════════════════════════
// 9. TIPOS Y EXPORTACIÓN
// ═══════════════════════════════════════════════════════════════════════════

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface User {
  id: number;
  email: string;
  username: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  rol: 'medico' | 'enfermero' | 'administrador' | 'recepcion' | 'paciente';
  especialidad?: string;
  telefono?: string;
  foto_perfil?: string;
  activo?: boolean;
}

export const api = {
  get,
  post,
  put,
  patch,
  delete: del,
  postFormData,
  login,
  logout,
  isAuthenticated,
  getCurrentUser,
  saveTokens,
  clearAuth,
  apiClient
};

export default apiClient;