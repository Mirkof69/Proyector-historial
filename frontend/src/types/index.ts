// ===========================================
// TIPOS TYPESCRIPT - ESPEJO DEL BACKEND
// ===========================================

// ========== USUARIOS ==========
export interface Usuario {
  id: number;
  uuid: string;
  username: string;
  email: string;
  nombre: string;
  apellido: string;
  nombre_completo: string;
  rol: 'administrador' | 'medico' | 'enfermera' | 'recepcionista';
  estado: 'activo' | 'inactivo' | 'bloqueado';
  telefono?: string;
  fecha_ultimo_login?: string;
  intentos_login_fallidos: number;
  fecha_registro: string;
  fecha_actualizacion: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
  user: Usuario;
}

// ========== PACIENTES ==========
export interface Paciente {
  id: number;
  uuid: string;
  id_clinico: string;
  cedula_identidad?: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo: string;
  fecha_nacimiento: string;
  edad: number;
  genero: 'femenino' | 'masculino' | 'otro';
  estado_civil?: 'soltera' | 'casada' | 'divorciada' | 'viuda' | 'union_libre';
  grupo_sanguineo?: string;
  telefono_principal?: string;
  telefono_alternativo?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  contacto_emergencia_nombre?: string;
  contacto_emergencia_telefono?: string;
  contacto_emergencia_relacion?: string;
  activo: boolean;
  fecha_registro: string;
  fecha_ultima_actualizacion: string;
  observaciones?: string;
}

// ========== EMBARAZOS ==========
export interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre?: string;
  numero_gesta: number;
  numero_para: number;
  numero_aborto: number;
  numero_cesarea: number;
  fecha_ultima_menstruacion: string;
  fecha_probable_parto: string;
  semanas_gestacion?: string;
  trimestre?: number;
  tipo_embarazo: 'unico' | 'gemelar' | 'multiple';
  riesgo_embarazo: 'bajo' | 'medio' | 'alto';
  estado: 'activo' | 'finalizado' | 'perdida';
  observaciones?: string;
  fecha_registro: string;
}

// ========== PARTOS ==========
export interface Parto {
  id: number;
  uuid: string;
  embarazo: number;
  paciente: number;
  paciente_nombre?: string;
  medico?: number;
  fecha_parto: string;
  hora_inicio?: string;
  hora_fin?: string;
  tipo_parto: 'eutocico' | 'cesarea' | 'forceps' | 'ventosa' | 'inducido';
  via_parto: 'vaginal' | 'abdominal';
  edad_gestacional_semanas: number;
  edad_gestacional_dias: number;
  duracion_trabajo_parto?: number;
  indicaciones?: string;
  anestesia?: string;
  procedimientos?: string;
  complicaciones: boolean;
  descripcion_complicaciones?: string;
  estado: 'en_curso' | 'finalizado' | 'complicado';
  observaciones?: string;
  fecha_registro: string;
}

export interface RecienNacido {
  id: number;
  parto: number;
  numero_hijo: number;
  sexo: 'M' | 'F' | 'I';
  peso: number;
  talla?: number;
  perimetro_cefalico?: number;
  apgar_1min?: number;
  apgar_5min?: number;
  estado_al_nacer: 'vivo' | 'muerto' | 'mortinato';
  reanimacion: boolean;
  descripcion_reanimacion?: string;
  malformaciones: boolean;
  descripcion_malformaciones?: string;
  observaciones?: string;
  fecha_registro: string;
}

export interface ComplicacionParto {
  id: number;
  parto: number;
  tipo_complicacion: string;
  descripcion: string;
  tratamiento?: string;
  resuelto: boolean;
  fecha_registro: string;
}

// ========== RESPUESTAS API ==========
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  mensaje?: string;
  error?: string;
  errores?: any;
}

export interface PaginatedResponse<T> {
  count: number;
  next?: string;
  previous?: string;
  results: T[];
}

// ========== ESTADÍSTICAS ==========
export interface EstadisticasGenerales {
  total_usuarios?: number;
  total_pacientes?: number;
  total_embarazos?: number;
  total_partos?: number;
  embarazos_activos?: number;
  partos_mes?: number;
}

