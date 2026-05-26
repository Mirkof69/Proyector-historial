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

const API_URL = getApiUrl();
const TIMEOUT = parseInt(process.env.REACT_APP_API_TIMEOUT || '30000', 10);
const IS_DEV = process.env.NODE_ENV === 'development';

const PUBLIC_ROUTES = ['/login/', '/usuarios/login/', '/token/refresh/', '/register/'];

// ═══════════════════════════════════════════════════════════════════════════
// 2. INSTANCIAS DE AXIOS
// ═══════════════════════════════════════════════════════════════════════════

// Header requerido por localtunnel para evitar la página de bypass
const tunnelHeaders = API_URL.includes('.loca.lt')
  ? { 'bypass-tunnel-reminder': 'true' }
  : {};

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...tunnelHeaders,
  },
});

const refreshClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ═══════════════════════════════════════════════════════════════════════════
// 3. GESTIÓN DE TOKENS (LOCAL STORAGE)
// ═══════════════════════════════════════════════════════════════════════════

const getAccessToken = (): string | null =>
  localStorage.getItem('access_token') || localStorage.getItem('token');

const getRefreshToken = (): string | null =>
  localStorage.getItem('refresh_token') || null;

export const saveTokens = (accessToken: string, refreshToken?: string): void => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('token', accessToken);
  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
  if (IS_DEV) {
    console.log('✅ Tokens guardados/actualizados correctamente');
  }
};

const clearAuth = (): void => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('token');
  localStorage.removeItem('user:v1');
  if (IS_DEV) {
    console.log('🧹 Sesión limpiada - Usuario deslogueado');
  }
};

const isAuthenticated = (): boolean => {
  const token = getAccessToken();
  return !!token;
};

// ═══════════════════════════════════════════════════════════════════════════
// 4. INTERCEPTOR DE REQUEST (Salida)
// ═══════════════════════════════════════════════════════════════════════════

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAccessToken();
    const isPublic = PUBLIC_ROUTES.some(route => config.url?.includes(route));
    if (token && config.headers && !isPublic) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (IS_DEV) {
      console.log(`🚀 [REQ] ${config.method?.toUpperCase()} ${config.url}`, {
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

const refreshAccessToken = async (): Promise<string> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  try {
    const response = await refreshClient.post('/token/refresh/', { refresh: refreshToken });
    const newAccessToken = response.data.access;
    if (!newAccessToken) {
      throw new Error('El servidor no devolvió un nuevo access token');
    }
    const newRefreshToken = response.data.refresh;
    saveTokens(newAccessToken, newRefreshToken);
    return newAccessToken;
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
      console.log(`✅ [RES] ${response.status} ${response.config.url}`);
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
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const newToken = await refreshAccessToken();
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        processQueue(null, newToken);
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
      const data = error.response.data as Record<string, any> | { detail?: string };
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
        bodyStyle: { whiteSpace: 'pre-line' }
      });
    }

    return Promise.reject(error);
  }
);

// ═══════════════════════════════════════════════════════════════════════════
// 7. MÉTODOS DE ACCESO A LA API (WRAPPERS)
// ═══════════════════════════════════════════════════════════════════════════

const get = async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
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

const patch = async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
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
    if (IS_DEV) console.log('🔐 Enviando credenciales...');
    const response = await apiClient.post('/usuarios/login/', { email, password });
    const data = response.data;
    const accessToken = data.access || data.token || data.access_token;
    const refreshToken = data.refresh || data.refresh_token;
    const user = data.user || data.usuario || data;

    if (!accessToken) {
      throw new Error('Respuesta de login inválida: No se recibió token de acceso.');
    }

    saveTokens(accessToken, refreshToken);

    if (user) {
      const safeUser = { ...user };
      delete safeUser.access;
      delete safeUser.refresh;
      delete safeUser.token;
      localStorage.setItem('user:v1', JSON.stringify(safeUser));
    }

    if (IS_DEV) console.log('✅ Login exitoso');
    return data;
  } catch (error: any) {
    if (IS_DEV) console.error('❌ Login fallido:', error);
    throw error;
  }
};

const logout = async (): Promise<void> => {
  try {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      await refreshClient.post('/usuarios/logout/', { refresh: refreshToken });
    }
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