/**
 * =============================================================================
 * TIPOS Y INTERFACES GLOBALES DEL SISTEMA
 * =============================================================================
 * Sistema de Historial Médico Obstétrico - Fetal Medical Foundation
 * Tipos TypeScript para todas las entidades del sistema
 * =============================================================================
 */

// =============================================================================
// TIPOS DE AUTENTICACIÓN
// =============================================================================

export interface Usuario {
  id: number;
  username: string;
  email: string;
  nombre: string;
  apellido: string;
  rol: 'medico' | 'enfermero' | 'admin' | 'paciente';
  especialidad?: string;
  matricula?: string;
  telefono?: string;
  activo: boolean;
  fecha_creacion: string;
  ultimo_acceso?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: Usuario;
}

// =============================================================================
// TIPO PACIENTE
// =============================================================================

export interface Paciente {
  id: number;
  nombre: string;
  apellido: string;
  dni: string;
  fecha_nacimiento: string;
  edad: number;
  telefono: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  provincia?: string;
  grupo_sanguineo?: string;
  factor_rh?: string;

  // Historia Obstétrica (GPAC)
  gestas?: number;
  partos?: number;
  abortos?: number;
  cesareas?: number;

  // Antecedentes
  antecedentes_personales?: string;
  antecedentes_familiares?: string;
  alergias?: string;
  medicacion_habitual?: string;

  // Metadata
  activo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface PacienteForm extends Omit<Paciente, 'id' | 'edad' | 'fecha_creacion' | 'fecha_modificacion'> {}

// =============================================================================
// TIPO EMBARAZO
// =============================================================================

export interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre?: string;
  paciente_apellido?: string;

  // Datos del embarazo
  fur: string; // Fecha Última Regla
  fpp: string; // Fecha Probable de Parto
  eg_actual?: string; // Edad Gestacional Actual
  semanas_dias?: string;

  // Tipo de embarazo
  embarazo_multiple: boolean;
  numero_fetos?: number;
  tipo_embarazo?: 'unico' | 'gemelar' | 'triple' | 'multiple';

  // Riesgos
  alto_riesgo: boolean;
  factores_riesgo?: string;

  // Complicaciones
  complicaciones?: Complicacion[];

  // Estado
  estado: 'activo' | 'finalizado' | 'perdida';
  fecha_finalizacion?: string;
  tipo_finalizacion?: 'parto' | 'cesarea' | 'aborto' | 'otro';
  resultado?: string;

  // Metadata
  activo: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
}

export interface Complicacion {
  id: number;
  embarazo: number;
  tipo: string;
  descripcion: string;
  fecha_diagnostico: string;
  tratamiento?: string;
  resuelta: boolean;
  fecha_resolucion?: string;
}

export interface EmbarazoForm extends Omit<Embarazo, 'id' | 'eg_actual' | 'semanas_dias' | 'fecha_creacion' | 'fecha_modificacion' | 'complicaciones'> {}

// =============================================================================
// TIPO CONTROL PRENATAL
// =============================================================================

export interface ControlPrenatal {
  id: number;
  embarazo: number;
  numero_control: number;
  fecha_control: string;

  // Edad Gestacional
  eg_semanas: number;
  eg_dias: number;
  trimestre: number;

  // Signos Vitales
  peso: number;
  talla?: number;
  imc?: number;
  presion_arterial_sistolica: number;
  presion_arterial_diastolica: number;
  pam?: number;
  frecuencia_cardiaca?: number;
  temperatura?: number;

  // Examen Obstétrico
  altura_uterina?: number;
  presentacion_fetal?: string;
  fcf?: number; // Frecuencia Cardíaca Fetal
  movimientos_fetales?: boolean;

  // Laboratorio
  hemoglobina?: number;
  hematocrito?: number;
  glucemia?: number;
  proteinuria?: string;

  // Síntomas y Signos
  edema?: boolean;
  cefalea?: boolean;
  vision_borrosa?: boolean;
  epigastralgia?: boolean;
  contracciones?: boolean;
  sangrado?: boolean;
  perdida_liquido?: boolean;

  // Observaciones
  observaciones?: string;
  tratamiento?: string;
  proximo_control?: string;

  // Alertas calculadas
  alertas?: Alert[];
  nivel_riesgo?: 'bajo' | 'moderado' | 'alto' | 'critico';

  // Metadata
  activo: boolean;
  fecha_creacion: string;
}

export interface Alert {
  tipo: string;
  severidad: 'leve' | 'moderada' | 'alta' | 'critica';
  mensaje: string;
  accion?: string;
}

export interface ControlPrenatalForm extends Omit<ControlPrenatal, 'id' | 'numero_control' | 'trimestre' | 'imc' | 'pam' | 'alertas' | 'nivel_riesgo' | 'fecha_creacion'> {}

// =============================================================================
// CALCULADORAS FMF
// =============================================================================

export interface CalculadoraPreeclampsia {
  edad_materna: number;
  peso: number;
  talla: number;
  pam: number;
  ip_uterinas_promedio: number;
  plgf?: number;
  papp_a?: number;
  eg_semanas: number;
  raza?: string;
  antecedente_preeclampsia?: boolean;
  diabetes_pregestacional?: boolean;
  enfermedad_renal?: boolean;
}

export interface ResultadoPreeclampsia {
  riesgo_porcentaje: number;
  clasificacion: string;
  mom_pam: number;
  mom_ip_uterinas: number;
  recomendacion: string;
}

export interface CalculadoraTrisomias {
  edad_materna: number;
  eg_semanas: number;
  nt_mm: number;
  papp_a_mom: number;
  beta_hcg_mom: number;
  hueso_nasal_presente: boolean;
}

export interface ResultadoTrisomias {
  riesgo_t21: string;
  riesgo_t18: string;
  riesgo_t13: string;
  clasificacion: string;
  recomendacion: string;
}

export interface CalculadoraSGA {
  peso_materno: number;
  talla_materna: number;
  pam: number;
  ip_uterinas_promedio: number;
  plgf?: number;
  eg_semanas: number;
  tabaquismo?: boolean;
}

export interface CalculadoraDiabetes {
  edad_materna: number;
  imc: number;
  antecedente_diabetes_familiar: boolean;
  antecedente_macrosomia: boolean;
  sop: boolean;
  glucemia_basal?: number;
}

export interface CalculadoraPartoPretermino {
  edad_materna: number;
  paridad: number;
  parto_pretermino_previo: boolean;
  eg_parto_previo?: number;
  embarazo_multiple: boolean;
  longitud_cervical: number;
  eg_medicion: number;
}

// =============================================================================
// DASHBOARD Y ESTADÍSTICAS
// =============================================================================

export interface EstadisticasGenerales {
  total_pacientes: number;
  total_embarazos: number;
  embarazos_activos: number;
  embarazos_alto_riesgo: number;
  controles_mes_actual: number;
  proximos_controles: number;
}

export interface EstadisticasPorMes {
  mes: string;
  pacientes: number;
  embarazos: number;
  controles: number;
}

export interface AlertaReciente {
  id: number;
  tipo: string;
  severidad: string;
  paciente: string;
  fecha: string;
  mensaje: string;
}

// =============================================================================
// TIPOS AUXILIARES
// =============================================================================

export interface PaginationParams {
  page: number;
  pageSize: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  message: string;
  errors?: Record<string, string[]>;
}

// =============================================================================
// FIN DE TIPOS
// =============================================================================
