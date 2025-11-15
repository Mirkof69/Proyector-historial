// ===========================================
// SERVICIOS API - CONEXIÓN CON BACKEND DJANGO
// ===========================================

import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

// URL base del backend Django
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Crear instancia de axios
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token JWT a cada petición
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar errores y refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el token expiró, intentar renovarlo
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Si falla el refresh, limpiar tokens y redirigir al login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// ===========================================
// SERVICIO DE AUTENTICACIÓN
// ===========================================

export const AuthService = {
  // Login
  login: async (username: string, password: string) => {
    const response = await api.post('/usuarios/login/', { username, password });
    const { access, refresh, user } = response.data;

    // Guardar tokens y usuario en localStorage
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user', JSON.stringify(user));

    return response.data;
  },

  // Logout
  logout: async () => {
    try {
      await api.post('/usuarios/logout/');
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  // Registro
  register: async (userData: any) => {
    const response = await api.post('/usuarios/register/', userData);
    return response.data;
  },

  // Obtener usuario actual
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  // Verificar si está autenticado
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
};

// ===========================================
// SERVICIO DE PACIENTES
// ===========================================

export const PacientesService = {
  // Listar todos los pacientes
  getAll: (params?: any) => api.get('/pacientes/', { params }),

  // Obtener un paciente por ID
  getById: (id: number) => api.get(`/pacientes/${id}/`),

  // Crear paciente
  create: (data: any) => api.post('/pacientes/', data),

  // Actualizar paciente
  update: (id: number, data: any) => api.put(`/pacientes/${id}/`, data),

  // Actualizar parcialmente
  patch: (id: number, data: any) => api.patch(`/pacientes/${id}/`, data),

  // Eliminar (soft delete)
  delete: (id: number) => api.delete(`/pacientes/${id}/`),

  // Reactivar
  reactivar: (id: number) => api.post(`/pacientes/${id}/reactivar/`),

  // Historial completo
  getHistorial: (id: number) => api.get(`/pacientes/${id}/historial_completo/`),

  // Perfil de riesgo
  getPerfilRiesgo: (id: number) => api.get(`/pacientes/${id}/perfil_riesgo/`),

  // Estadísticas
  getEstadisticas: () => api.get('/pacientes/estadisticas/'),

  // Búsqueda avanzada
  busquedaAvanzada: (params: any) => api.get('/pacientes/busqueda_avanzada/', { params }),

  // Buscar por cédula
  buscarPorCI: (ci: string) => api.get('/pacientes/buscar_por_ci/', { params: { ci } }),

  // Buscar por nombre
  buscarPorNombre: (nombre: string) => api.get('/pacientes/buscar_por_nombre/', { params: { nombre } }),
};

// ===========================================
// SERVICIO DE EMBARAZOS
// ===========================================

export const EmbarazosService = {
  getAll: (params?: any) => api.get('/embarazos/', { params }),
  getById: (id: number) => api.get(`/embarazos/${id}/`),
  create: (data: any) => api.post('/embarazos/', data),
  update: (id: number, data: any) => api.put(`/embarazos/${id}/`, data),
  patch: (id: number, data: any) => api.patch(`/embarazos/${id}/`, data),
  delete: (id: number) => api.delete(`/embarazos/${id}/`),

  // Acciones personalizadas
  cambiarEstado: (id: number, estado: string) => 
    api.post(`/embarazos/${id}/cambiar_estado/`, { estado }),
  finalizar: (id: number) => api.post(`/embarazos/${id}/finalizar/`),
  marcarPerdida: (id: number, motivo: string) => 
    api.post(`/embarazos/${id}/marcar_perdida/`, { motivo }),
  getCalculosObstetricos: (id: number) => api.get(`/embarazos/${id}/calculos_obstetricos/`),
  getProximosControles: (id: number) => api.get(`/embarazos/${id}/proximos_controles/`),
  getEstadisticas: () => api.get('/embarazos/estadisticas/'),
  getActivos: () => api.get('/embarazos/activos/'),
  getAltoRiesgo: () => api.get('/embarazos/alto_riesgo/'),
};

// ===========================================
// SERVICIO DE PARTOS
// ===========================================

export const PartosService = {
  getAll: (params?: any) => api.get('/partos/', { params }),
  getById: (id: number) => api.get(`/partos/${id}/`),
  create: (data: any) => api.post('/partos/', data),
  update: (id: number, data: any) => api.put(`/partos/${id}/`, data),
  patch: (id: number, data: any) => api.patch(`/partos/${id}/`, data),
  delete: (id: number) => api.delete(`/partos/${id}/`),

  // Acciones personalizadas
  finalizar: (id: number) => api.post(`/partos/${id}/finalizar/`),
  registrarComplicacion: (id: number, data: any) =>
    api.post(`/partos/${id}/registrar_complicacion/`, data),
  getCertificadoNacimiento: (id: number) => api.get(`/partos/${id}/certificado_nacimiento/`),
  getResumenCompleto: (id: number) => api.get(`/partos/${id}/resumen_completo/`),
  getEstadisticas: () => api.get('/partos/estadisticas/'),
  getCesareaRate: () => api.get('/partos/cesarea_rate/'),
  getApgarPromedio: () => api.get('/partos/apgar_promedio/'),
  getPorTipo: () => api.get('/partos/por_tipo/'),
  getPorVia: () => api.get('/partos/por_via/'),
};

// ===========================================
// SERVICIO DE USUARIOS
// ===========================================

export const UsuariosService = {
  getAll: (params?: any) => api.get('/usuarios/', { params }),
  getById: (id: number) => api.get(`/usuarios/${id}/`),
  create: (data: any) => api.post('/usuarios/', data),
  update: (id: number, data: any) => api.put(`/usuarios/${id}/`, data),
  patch: (id: number, data: any) => api.patch(`/usuarios/${id}/`, data),
  delete: (id: number) => api.delete(`/usuarios/${id}/`),

  // Acciones personalizadas
  cambiarPassword: (id: number, data: any) => 
    api.post(`/usuarios/${id}/cambiar_password/`, data),
  bloquear: (id: number) => api.post(`/usuarios/${id}/bloquear/`),
  desbloquear: (id: number) => api.post(`/usuarios/${id}/desbloquear/`),
  activar: (id: number) => api.post(`/usuarios/${id}/activar/`),
  desactivar: (id: number) => api.post(`/usuarios/${id}/desactivar/`),
  getEstadisticas: () => api.get('/usuarios/estadisticas/'),
  getPorRol: () => api.get('/usuarios/por_rol/'),
};

