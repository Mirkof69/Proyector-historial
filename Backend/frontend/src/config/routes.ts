// ============================================================================
// RUTAS COMPLETAS DEL SISTEMA - BACKEND Y FRONTEND
// ============================================================================
// Configuración centralizada de todas las rutas de la aplicación
// Incluye rutas de API (backend Django) y rutas de navegación (frontend React)
// ============================================================================

// ============================================================================
// RUTAS DE LA API (BACKEND DJANGO)
// ============================================================================
const API_ROUTES = {
  // ========== AUTENTICACIÓN ==========
  AUTH: {
    LOGIN: '/usuarios/login/',
    REFRESH: '/token/refresh/',
    LOGOUT: '/usuarios/logout/',
    REGISTER: '/usuarios/register/',
    VERIFY_EMAIL: '/usuarios/verify-email/',
    RESET_PASSWORD: '/usuarios/reset-password/',
    CHANGE_PASSWORD: '/usuarios/change-password/',
  },

  // ========== USUARIOS ==========
  USUARIOS: {
    LIST: '/usuarios/usuarios/',
    CREATE: '/usuarios/usuarios/',
    DETAIL: (id: number) => `/usuarios/usuarios/${id}/`,
    UPDATE: (id: number) => `/usuarios/usuarios/${id}/`,
    DELETE: (id: number) => `/usuarios/usuarios/${id}/`,
    PROFILE: '/usuarios/usuarios/me/',
    UPDATE_PROFILE: '/usuarios/usuarios/me/',
    CHANGE_PASSWORD: (id: number) => `/usuarios/usuarios/${id}/cambiar_password/`,
    BY_ROL: (rol: string) => `/usuarios/usuarios/?rol=${rol}`,
    ACTIVOS: '/usuarios/usuarios/?activo=true',
    ESTADISTICAS: '/usuarios/estadisticas/',
  },

  // ========== PACIENTES ==========
  PACIENTES: {
    LIST: '/pacientes/',
    CREATE: '/pacientes/',
    DETAIL: (id: number) => `/pacientes/${id}/`,
    UPDATE: (id: number) => `/pacientes/${id}/`,
    DELETE: (id: number) => `/pacientes/${id}/`,
    SEARCH: (query: string) => `/pacientes/?search=${encodeURIComponent(query)}`,
    BY_ID_CLINICO: (idClinico: string) => `/pacientes/?id_clinico=${idClinico}`,
    ESTADISTICAS: '/pacientes/estadisticas/',
    ACTIVOS: '/pacientes/?activo=true',
    HISTORIA_COMPLETA: (id: number) => `/pacientes/${id}/historia-completa/`,
  },

  // ========== EMBARAZOS ==========
  EMBARAZOS: {
    LIST: '/embarazos/',
    CREATE: '/embarazos/',
    DETAIL: (id: number) => `/embarazos/${id}/`,
    UPDATE: (id: number) => `/embarazos/${id}/`,
    DELETE: (id: number) => `/embarazos/${id}/`,
    BY_PACIENTE: (pacienteId: number) => `/pacientes/${pacienteId}/embarazos/`,
    ACTIVOS: '/embarazos/?estado=activo',
    ALTO_RIESGO: '/embarazos/?riesgo_embarazo=alto&estado=activo',
    FINALIZADOS: '/embarazos/?estado=finalizado',
    ESTADISTICAS: '/embarazos/estadisticas/',
    RESUMEN: (id: number) => `/embarazos/${id}/resumen/`,
    TIMELINE: (id: number) => `/embarazos/${id}/timeline/`,
  },

  // ========== CONTROLES PRENATALES ==========
  CONTROLES: {
    LIST: '/controles/',
    CREATE: '/controles/',
    DETAIL: (id: number) => `/controles/${id}/`,
    UPDATE: (id: number) => `/controles/${id}/`,
    DELETE: (id: number) => `/controles/${id}/`,
    BY_EMBARAZO: (embarazoId: number) => `/embarazos/${embarazoId}/controles/`,
    ULTIMO: (embarazoId: number) => `/embarazos/${embarazoId}/ultimo_control/`,
    CON_ALERTAS: '/controles/?tiene_alertas=true',
    RECIENTES: (limit: number = 10) => `/controles/?ordering=-fecha_control&limit=${limit}`,
    ESTADISTICAS: '/controles/estadisticas/',
    GRAFICA_PESO: (embarazoId: number) => `/embarazos/${embarazoId}/grafica_peso/`,
    GRAFICA_PA: (embarazoId: number) => `/embarazos/${embarazoId}/grafica_pa/`,
    EXPORTAR: (embarazoId: number) => `/embarazos/${embarazoId}/controles/exportar/`,
  },

  // ========== ECOGRAFÍAS ==========
  ECOGRAFIAS: {
    LIST: '/ecografias/',
    CREATE: '/ecografias/',
    DETAIL: (id: number) => `/ecografias/${id}/`,
    UPDATE: (id: number) => `/ecografias/${id}/`,
    DELETE: (id: number) => `/ecografias/${id}/`,
    BY_EMBARAZO: (embarazoId: number) => `/embarazos/${embarazoId}/ecografias/`,
    UPLOAD_IMAGE: (id: number) => `/ecografias/${id}/upload_image/`,
    DELETE_IMAGE: (id: number) => `/ecografias/${id}/delete_image/`,
    ESTADISTICAS: '/ecografias/estadisticas/',
    TRIMESTRE: (trimestre: number) => `/ecografias/?trimestre=${trimestre}`,
    TIPO: (tipo: string) => `/ecografias/?tipo_ecografia=${tipo}`,
    RECIENTES: (limit: number = 10) => `/ecografias/?ordering=-fecha_ecografia&limit=${limit}`,
  },

  // ========== LABORATORIO ==========
  LABORATORIO: {
    LIST: '/laboratorios/',
    CREATE: '/laboratorios/',
    DETAIL: (id: number) => `/laboratorios/${id}/`,
    UPDATE: (id: number) => `/laboratorios/${id}/`,
    DELETE: (id: number) => `/laboratorios/${id}/`,
    BY_EMBARAZO: (embarazoId: number) => `/embarazos/${embarazoId}/laboratorios/`,
    TIPO: (tipo: string) => `/laboratorios/?tipo_examen=${tipo}`,
    ESTADISTICAS: '/laboratorios/estadisticas/',
    VALORES_REFERENCIA: '/laboratorios/valores-referencia/',
    PENDIENTES: '/laboratorios/?resultado=pendiente',
    ANORMALES: '/laboratorios/?tiene_alertas=true',
  },

  // ========== CALCULADORAS BÁSICAS ==========
  CALCULADORAS: {
    EDAD_GESTACIONAL: '/calculadoras/edad-gestacional/',
    FPP: '/calculadoras/fpp/',
    IMC: '/calculadoras/imc/',
    BISHOP: '/calculadoras/bishop/',
    APGAR: '/calculadoras/apgar/',
    GANANCIA_PESO: '/calculadoras/ganancia-peso/',
    HISTORIAL: '/calculadoras/historial/',
    TODAS: '/calculadoras/',
  },

  // ========== CALCULADORAS AVANZADAS ==========
  CALCULADORAS_AVANZADAS: {
    PREECLAMPSIA: '/calculadoras-avanzadas/preeclampsia/',
    DIABETES_GESTACIONAL: '/calculadoras-avanzadas/diabetes/',
    PESO_FETAL: '/calculadoras-avanzadas/peso-fetal/',
    LIQUIDO_AMNIOTICO: '/calculadoras-avanzadas/liquido-amniotico/',
    DOPPLER: '/calculadoras-avanzadas/doppler/',
    RIESGO_PARTO_PRETERMINO: '/calculadoras-avanzadas/parto-pretermino/',
    RESTRICCION_CRECIMIENTO: '/calculadoras-avanzadas/restriccion-crecimiento/',
    CROMOSOMOPATIAS: '/calculadoras-avanzadas/cromosomopatias/',
    HISTORIAL: '/calculadoras-avanzadas/historial/',
    TODAS: '/calculadoras-avanzadas/',
  },

  // ========== CITAS ==========
  CITAS: {
    LIST: '/citas/',
    CREATE: '/citas/',
    DETAIL: (id: number) => `/citas/${id}/`,
    UPDATE: (id: number) => `/citas/${id}/`,
    DELETE: (id: number) => `/citas/${id}/`,
    CONFIRMAR: (id: number) => `/citas/${id}/confirmar/`,
    CANCELAR: (id: number) => `/citas/${id}/cancelar/`,
    REPROGRAMAR: (id: number) => `/citas/${id}/reprogramar/`,
    PENDIENTES: '/citas/?estado=pendiente',
    CONFIRMADAS: '/citas/?estado=confirmada',
    CANCELADAS: '/citas/?estado=cancelada',
    HOY: '/citas/hoy/',
    SEMANA: '/citas/semana/',

    // ========== CONFIGURACIÓN ==========
    PERFIL: '/dashboard/perfil',
    CONFIGURACION: '/dashboard/configuracion',
    AYUDA: '/dashboard/ayuda',
    DOCUMENTACION: '/dashboard/documentacion',
  },

  // ========== ERROR PAGES ==========
  NOT_FOUND: '/404',
  UNAUTHORIZED: '/401',
  FORBIDDEN: '/403',
  SERVER_ERROR: '/500',
};

// ============================================================================
// RUTAS DEL FRONTEND (REACT ROUTER)
// ============================================================================
export const FRONTEND_ROUTES = {
  // ========== LANDING Y AUTENTICACIÓN ==========
  LANDING: '/',
  LOGIN: '/login',
  SETUP_MFA: '/setup-mfa',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  VERIFY_EMAIL: '/verify-email',


  // ========== DASHBOARD PRINCIPAL ==========
  DASHBOARD: {
    HOME: '/dashboard',
    STATS: '/dashboard/estadisticas',
    ALERTAS: '/dashboard/alertas',

    // ========== USUARIOS ==========
    USUARIOS: '/dashboard/usuarios',
    USUARIOS_NUEVO: '/dashboard/usuarios/nuevo',
    USUARIOS_DETALLE: (id: number | string) => `/dashboard/usuarios/${id}`,
    USUARIOS_EDITAR: (id: number | string) => `/dashboard/usuarios/${id}/editar`,

    // ========== PACIENTES ==========
    PACIENTES: '/dashboard/pacientes',
    PACIENTES_NUEVO: '/dashboard/pacientes/nuevo',
    PACIENTES_DETALLE: (id: number | string) => `/dashboard/pacientes/${id}`,
    PACIENTES_EDITAR: (id: number | string) => `/dashboard/pacientes/${id}/editar`,
    PACIENTES_HISTORIA: (id: number | string) => `/dashboard/pacientes/${id}/historia`,

    // ========== EMBARAZOS ==========
    EMBARAZOS: '/dashboard/embarazos',
    EMBARAZOS_NUEVO: '/dashboard/embarazos/nuevo',
    EMBARAZOS_DETALLE: (id: number | string) => `/dashboard/embarazos/${id}`,
    EMBARAZOS_EDITAR: (id: number | string) => `/dashboard/embarazos/${id}/editar`,
    EMBARAZOS_TIMELINE: (id: number | string) => `/dashboard/embarazos/${id}/timeline`,

    // ========== CONTROLES PRENATALES ==========
    CONTROLES: '/dashboard/controles',
    CONTROLES_NUEVO: '/dashboard/controles/nuevo',
    CONTROLES_DETALLE: (id: number | string) => `/dashboard/controles/${id}`,
    CONTROLES_EDITAR: (id: number | string) => `/dashboard/controles/${id}/editar`,
    CONTROLES_GRAFICAS: (embarazoId: number | string) =>
      `/dashboard/embarazos/${embarazoId}/controles/graficas`,

    // ========== ECOGRAFÍAS ==========
    ECOGRAFIAS: '/dashboard/ecografias',
    ECOGRAFIAS_NUEVO: '/dashboard/ecografias/nuevo',
    ECOGRAFIAS_DETALLE: (id: number | string) => `/dashboard/ecografias/${id}`,
    ECOGRAFIAS_EDITAR: (id: number | string) => `/dashboard/ecografias/${id}/editar`,

    // ========== LABORATORIO ==========
    LABORATORIO: '/dashboard/laboratorio',
    LABORATORIO_NUEVO: '/dashboard/laboratorio/nuevo',
    LABORATORIO_DETALLE: (id: number | string) => `/dashboard/laboratorio/${id}`,
    LABORATORIO_EDITAR: (id: number | string) => `/dashboard/laboratorio/${id}/editar`,
    LABORATORIO_VALORES_REF: '/dashboard/laboratorio/valores-referencia',

    // ========== CALCULADORAS BÁSICAS ==========
    CALCULADORAS: '/dashboard/calculadoras',
    CALCULADORA_FPP: '/dashboard/calculadoras/fpp',
    CALCULADORA_IMC: '/dashboard/calculadoras/imc',
    CALCULADORA_BISHOP: '/dashboard/calculadoras/bishop',
    CALCULADORA_APGAR: '/dashboard/calculadoras/apgar',

    // ========== CALCULADORAS AVANZADAS ==========
    CALCULADORAS_AVANZADAS: '/dashboard/calculadoras-avanzadas',
    CALCULADORA_PREECLAMPSIA: '/dashboard/calculadoras-avanzadas/preeclampsia',
    CALCULADORA_DIABETES: '/dashboard/calculadoras-avanzadas/diabetes',
    CALCULADORA_PESO_FETAL: '/dashboard/calculadoras-avanzadas/peso-fetal',

    // ========== CITAS ==========
    CITAS: '/dashboard/citas',
    CITAS_NUEVO: '/dashboard/citas/nuevo',
    CITAS_DETALLE: (id: number | string) => `/dashboard/citas/${id}`,
    CITAS_EDITAR: (id: number | string) => `/dashboard/citas/${id}/editar`,
    CITAS_CALENDARIO: '/dashboard/citas/calendario',
    CITAS_HOY: '/dashboard/citas/hoy',

    // ========== PARTOS ==========
    PARTOS: '/dashboard/partos',
    PARTOS_NUEVO: '/dashboard/partos/nuevo',
    PARTOS_CREAR: '/dashboard/partos/nuevo', // Alias
    PARTOS_DETALLE: (id: number | string) => `/dashboard/partos/${id}`,
    PARTOS_EDITAR: (id: number | string) => `/dashboard/partos/${id}/editar`,

    // ========== TRIAJE ==========
    TRIAJE: '/dashboard/triaje',
    TRIAJE_NUEVO: '/dashboard/triaje/nuevo',
    TRIAJE_DETALLE: (id: number | string) => `/dashboard/triaje/${id}`,
    TRIAJE_EDITAR: (id: number | string) => `/dashboard/triaje/${id}/editar`,

    // ========== REPORTES ==========
    REPORTES: '/dashboard/reportes',
    REPORTES_GENERAR: '/dashboard/reportes/generar',
    REPORTES_DETALLE: (id: number | string) => `/dashboard/reportes/${id}`,
    REPORTES_HISTORIAL: '/dashboard/reportes/historial',

    // ========== CONFIGURACIÓN ==========
    PERFIL: '/dashboard/perfil',
    CONFIGURACION: '/dashboard/configuracion',
    AYUDA: '/dashboard/ayuda',
    DOCUMENTACION: '/dashboard/documentacion',

    // ========== LOGS Y ESTADÍSTICAS ==========
    ACCESS_LOGS: '/dashboard/access-logs',
    ESTADISTICAS_PAGE: '/dashboard/estadisticas',
  },

  // ========== ERROR PAGES ==========
  NOT_FOUND: '/404',
  UNAUTHORIZED: '/401',
  FORBIDDEN: '/403',
  SERVER_ERROR: '/500',
};


// ============================================================================
// NOMBRES LEGIBLES PARA INTERFAZ
// ============================================================================
const ROUTE_NAMES = {
  // ========== PRINCIPALES ==========
  DASHBOARD: 'Dashboard',
  HOME: 'Inicio',
  PERFIL: 'Mi Perfil',
  CONFIGURACION: 'Configuración',
  AYUDA: 'Ayuda',
  DOCUMENTACION: 'Documentación',
  ACCESS_LOGS: 'Logs de Acceso',
  ESTADISTICAS: 'Estadísticas',

  // ========== MÓDULOS MÉDICOS ==========
  USUARIOS: 'Usuarios del Sistema',
  PACIENTES: 'Pacientes',
  EMBARAZOS: 'Embarazos',
  CONTROLES: 'Controles Prenatales',
  ECOGRAFIAS: 'Ecografías',
  LABORATORIO: 'Estudios de Laboratorio',
  CALCULADORAS: 'Calculadoras Médicas Básicas',
  CALCULADORAS_AVANZADAS: 'Calculadoras Clínicas Avanzadas',
  CITAS: 'Gestión de Citas',
  PARTOS: 'Registro de Partos',
  REPORTES: 'Reportes y Estadísticas',
  ALERTAS: 'Alertas Médicas',

  // ========== SUBMÓDULOS ==========
  HISTORIA_CLINICA: 'Historia Clínica Completa',
  CALENDARIO: 'Calendario de Citas',
  TIMELINE: 'Línea de Tiempo',
  GRAFICAS: 'Gráficas de Evolución',
  VALORES_REFERENCIA: 'Valores de Referencia',

  // ========== ACCIONES ==========
  NUEVO: 'Nuevo',
  EDITAR: 'Editar',
  VER: 'Ver Detalle',
  ELIMINAR: 'Eliminar',
  GENERAR: 'Generar',
  DESCARGAR: 'Descargar',
  EXPORTAR: 'Exportar',
  IMPRIMIR: 'Imprimir',
};

// ============================================================================
// BREADCRUMB LABELS
// ============================================================================
const BREADCRUMB_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  usuarios: 'Usuarios',
  pacientes: 'Pacientes',
  embarazos: 'Embarazos',
  controles: 'Controles',
  ecografias: 'Ecografías',
  laboratorio: 'Laboratorio',
  calculadoras: 'Calculadoras',
  'calculadoras-avanzadas': 'Calculadoras Avanzadas',
  citas: 'Citas',
  partos: 'Partos',
  reportes: 'Reportes',
  perfil: 'Perfil',
  configuracion: 'Configuración',
  nuevo: 'Nuevo',
  editar: 'Editar',
  detalle: 'Detalle',
  historia: 'Historia Clínica',
  calendario: 'Calendario',
  timeline: 'Línea de Tiempo',
  graficas: 'Gráficas',
  estadisticas: 'Estadísticas',
};

// ============================================================================
// HELPERS
// ============================================================================

/**
 * Obtiene el nombre legible de una ruta
 */
const getRouteName = (path: string): string => {
  // Normalizar path
  const normalizedPath = path.toLowerCase().replace(/\/$/, '');

  // Buscar coincidencias exactas
  if (normalizedPath === '/dashboard' || normalizedPath === '') return ROUTE_NAMES.DASHBOARD;
  if (normalizedPath.includes('/usuarios')) return ROUTE_NAMES.USUARIOS;
  if (normalizedPath.includes('/pacientes')) return ROUTE_NAMES.PACIENTES;
  if (normalizedPath.includes('/embarazos')) return ROUTE_NAMES.EMBARAZOS;
  if (normalizedPath.includes('/controles')) return ROUTE_NAMES.CONTROLES;
  if (normalizedPath.includes('/ecografias')) return ROUTE_NAMES.ECOGRAFIAS;
  if (normalizedPath.includes('/laboratorio')) return ROUTE_NAMES.LABORATORIO;
  if (normalizedPath.includes('/calculadoras-avanzadas')) return ROUTE_NAMES.CALCULADORAS_AVANZADAS;
  if (normalizedPath.includes('/calculadoras')) return ROUTE_NAMES.CALCULADORAS;
  if (normalizedPath.includes('/citas')) return ROUTE_NAMES.CITAS;
  if (normalizedPath.includes('/partos')) return ROUTE_NAMES.PARTOS;
  if (normalizedPath.includes('/reportes')) return ROUTE_NAMES.REPORTES;
  if (normalizedPath.includes('/perfil')) return ROUTE_NAMES.PERFIL;
  if (normalizedPath.includes('/configuracion')) return ROUTE_NAMES.CONFIGURACION;
  if (normalizedPath.includes('/alertas')) return ROUTE_NAMES.ALERTAS;

  return ROUTE_NAMES.DASHBOARD;
};

/**
 * Genera breadcrumbs a partir de una ruta
 */
const generateBreadcrumbs = (path: string): Array<{ label: string; path: string }> => {
  const segments = path.split('/').filter(Boolean);
  const breadcrumbs: Array<{ label: string; path: string }> = [];

  let currentPath = '';
  segments.forEach((segment) => {
    currentPath += `/${segment}`;

    // Omitir IDs numéricos
    if (!isNaN(Number(segment))) {
      return;
    }

    const label = BREADCRUMB_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
    breadcrumbs.push({ label, path: currentPath });
  });

  return breadcrumbs;
};

/**
 * Verifica si una ruta es pública (no requiere autenticación)
 */
const isPublicRoute = (path: string): boolean => {
  const publicRoutes = [
    FRONTEND_ROUTES.LANDING,
    FRONTEND_ROUTES.LOGIN,
    FRONTEND_ROUTES.REGISTER,
    FRONTEND_ROUTES.FORGOT_PASSWORD,
    FRONTEND_ROUTES.RESET_PASSWORD,
    FRONTEND_ROUTES.VERIFY_EMAIL,
    FRONTEND_ROUTES.SETUP_MFA,
  ];

  return publicRoutes.includes(path);
};

/**
 * Verifica si una ruta requiere permisos especiales
 */
const requiresAdmin = (path: string): boolean => {
  return path.includes('/usuarios') || path.includes('/configuracion');
};

/**
 * Construye URL de API con parámetros
 */
const buildApiUrl = (
  baseUrl: string,
  params?: Record<string, string | number | boolean>
): string => {
  if (!params || Object.keys(params).length === 0) {
    return baseUrl;
  }

  const queryString = Object.entries(params)
    .reduce((acc, [key, value]) => {
      if (value !== undefined && value !== null) {
        acc.push(`${key}=${encodeURIComponent(String(value))}`);
      }
      return acc;
    }, [] as string[])
    .join('&');

  return `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}${queryString}`;
};

/**
 * Obtiene el módulo principal de una ruta
 */
const getMainModule = (path: string): string => {
  const segments = path.split('/').filter(Boolean);
  if (segments.length >= 2) {
    return segments[1]; // Retorna el segmento después de /dashboard
  }
  return 'dashboard';
};

// ============================================================================
// EXPORTACIONES ADICIONALES
// ============================================================================
const routesConfig = {
  API_ROUTES,
  FRONTEND_ROUTES,
  ROUTE_NAMES,
  BREADCRUMB_LABELS,
  getRouteName,
  generateBreadcrumbs,
  isPublicRoute,
  requiresAdmin,
  buildApiUrl,
  getMainModule,
};

export default routesConfig;
