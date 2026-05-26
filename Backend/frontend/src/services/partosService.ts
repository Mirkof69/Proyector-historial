/**
 * =============================================================================
 * SERVICIO DE PARTOS - VERSIÓN COMPLETA Y EXTENDIDA
 * =============================================================================
 * ✅ MEGA COMPLETO: Sistema integral de gestión de partos
 * 
 * MÓDULOS INCLUIDOS:
 * - Gestión completa de partos (CRUD + búsquedas avanzadas)
 * - Gestión de recién nacidos (múltiples bebés por parto)
 * - Partograma (seguimiento hora a hora del trabajo de parto)
 * - Complicaciones maternas y neonatales
 * - Estadísticas y análisis
 * - Validaciones exhaustivas
 * - Normalización de respuestas del backend
 * - Manejo robusto de errores
 * 
 * ALINEACIÓN: 100% compatible con modelos Django del backend
 * =============================================================================
 */

import api from './api';

// ═══════════════════════════════════════════════════════════════════════════
// TIPOS Y ENUMS
// ═══════════════════════════════════════════════════════════════════════════

type TipoParto =
  | 'vaginal_espontaneo'
  | 'vaginal_instrumentado'
  | 'cesarea_electiva'
  | 'cesarea_urgencia'
  | 'cesarea_emergencia';

type PresentacionFetal =
  | 'cefalica'
  | 'podalica'
  | 'transversa'
  | 'oblicua';

type PosicionFetal =
  | 'oia' | 'oip' | 'oit'  // Occipito Izquierda (Anterior, Posterior, Transversa)
  | 'oda' | 'odp' | 'odt'; // Occipito Derecha (Anterior, Posterior, Transversa)

type EstadoMembranas =
  | 'integras'
  | 'rotas_espontaneas'
  | 'rotas_artificiales';

type GradoDesgarro =
  | 'no'
  | 'primer_grado'
  | 'segundo_grado'
  | 'tercer_grado'
  | 'cuarto_grado';

type TipoAlumbramiento =
  | 'espontaneo'
  | 'dirigido'
  | 'manual';

type SexoRecienNacido =
  | 'masculino'
  | 'femenino'
  | 'indeterminado';

type EstadoNacimiento =
  | 'vivo'
  | 'mortinato'
  | 'muerte_neonatal';

type IntensidadContracciones =
  | 'leve'
  | 'moderada'
  | 'fuerte';

type SeveridadComplicacion =
  | 'leve'
  | 'moderada'
  | 'severa'
  | 'critica';

type MomentoDeteccion =
  | 'ingreso'
  | 'dilatacion'
  | 'expulsivo'
  | 'alumbramiento'
  | 'puerperio_inmediato';

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - MODELO PRINCIPAL: PARTO
// ═══════════════════════════════════════════════════════════════════════════

interface PacienteInfo {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  cedula_identidad?: string;
  id_clinico?: string;
  ci?: string; // Added 'ci' field
  edad?: number;
  fecha_nacimiento?: string;
}

interface MedicoInfo {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  especialidad?: string;
  codigo_profesional?: string;
}

interface EmbarazoInfo {
  id: number;
  numero_embarazo: number;
  fecha_ultimo_periodo?: string;
  fecha_probable_parto?: string;
  semanas_gestacion?: number;
  tipo_embarazo?: string;
}

export interface Parto {
  // Identificación
  id?: number;
  numero_parto?: string;
  _uniqueRowKey?: string;

  // Relaciones básicas
  embarazo: number;
  paciente: number;
  medico_responsable?: number | null;

  // Información del parto
  tipo_parto?: TipoParto;
  presentacion_fetal?: PresentacionFetal;
  posicion_fetal?: PosicionFetal;
  edad_gestacional_parto: string; // Formato "39w+3d"
  edad_gestacional_dias?: number;

  // Membranas y líquido
  estado_membranas?: EstadoMembranas;
  hora_ruptura_membranas?: string;
  caracteristicas_liquido?: string;

  // Duración y fases del parto
  fecha_ingreso?: string;
  fecha_inicio_trabajo_parto?: string;
  fecha_parto?: string;
  duracion_trabajo_parto_horas?: number;
  duracion_periodo_dilatacion_minutos?: number;
  duracion_periodo_expulsivo_minutos?: number;
  duracion_alumbramiento_minutos?: number;

  // Analgesia y medicación
  analgesia_utilizada?: boolean;
  tipo_analgesia?: string;
  dosis_analgesia?: string;
  oxitocina_utilizada?: boolean;
  dosis_oxitocina?: string;
  otros_medicamentos?: string;

  // Intervenciones y complicaciones
  episiotomia?: boolean;
  tipo_episiotomia?: string;
  grado_desgarro?: GradoDesgarro;
  reparacion_desgarro?: string;

  // Alumbramiento y placenta
  tipo_alumbramiento?: TipoAlumbramiento;
  placenta_completa?: boolean;
  peso_placenta?: number; // gramos
  membranas_completas?: boolean;
  retencion_placentaria?: boolean;

  // Pérdida sanguínea
  perdida_sanguinea_estimada?: number; // ml
  hemorragia_postparto?: boolean;
  manejo_hemorragia?: string;

  // Cesárea (si aplica)
  indicaciones_cesarea?: string;
  tipo_incision_uterina?: string;
  tipo_incision_piel?: string;

  // Complicaciones y observaciones
  complicaciones_maternas?: string;
  observaciones_parto?: string;

  // Estado y control
  parto_finalizado?: boolean;
  trabajo_parto_espontaneo?: boolean;
  induccion_parto?: boolean;
  metodo_induccion?: string;
  monitoreo_fetal_continuo?: boolean;

  // Campos deprecated (compatibilidad con código legacy)
  apgar_1min?: number;
  apgar_5min?: number;
  peso_bebe?: number;

  // Metadatos
  fecha_creacion?: string;
  fecha_actualizacion?: string;

  // Información poblada por el backend
  paciente_info?: PacienteInfo;
  medico_info?: MedicoInfo;
  embarazo_info?: EmbarazoInfo;

  // Relaciones anidadas
  recien_nacidos?: RecienNacido[];
  partogramas?: PartogramaRegistro[];
  complicaciones?: ComplicacionParto[];

  // Campos calculados por el backend
  total_recien_nacidos?: number;
  numero_partos_anteriores?: number;
  riesgo_estimado?: string;

  // ✅ NUEVOS: Sistema de alertas médicas
  alertas_parto?: AlertaParto[];
  tiene_alertas?: boolean;
  tiene_alertas_criticas?: boolean;
  alertas_criticas?: AlertaParto[];
  alertas_moderadas?: AlertaParto[];
  tipo_parto_segun_edad?: {
    tipo: string;
    descripcion: string;
  };
  recomendaciones_por_edad?: Recomendacion[];

  // ✅ CAMPOS DE PROTOCOLO DE ABORTO (< 20 semanas)
  tipo_aborto?: string; // espontaneo, inducido, incompleto, completo, diferido, inevitable
  metodo_evacuacion?: string; // aspiracion, legrado, medico, expectante
  apoyo_psicologico_realizado?: boolean;
  protocolo_duelo_aplicado?: boolean;
  observaciones_aborto?: string;
}

// ✅ NUEVA INTERFAZ: Alerta de Parto
export interface AlertaParto {
  tipo: 'critica' | 'moderada';
  nivel: 'error' | 'warning';
  categoria: string;
  mensaje: string;
  recomendacion: string;
}

// ✅ NUEVA INTERFAZ: Recomendación por Edad Gestacional
export interface Recomendacion {
  tipo: 'informacion' | 'importante' | 'atencion' | 'urgente';
  periodo: string;
  titulo: string;
  recomendaciones: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - RECIÉN NACIDO
// ═══════════════════════════════════════════════════════════════════════════

interface RecienNacido {
  id?: number;
  parto?: number;
  parto_id?: number;

  // Identificación
  numero_gemelo: number; // 1, 2, 3... para embarazos múltiples
  nombre_temporal?: string;

  // Características físicas al nacer
  sexo: SexoRecienNacido;
  peso_nacimiento: number; // gramos
  talla_nacimiento: number; // cm
  perimetro_cefalico?: number; // cm
  perimetro_toracico?: number; // cm
  perimetro_abdominal?: number; // cm

  // Evaluación APGAR
  apgar_1_minuto: number; // 0-10
  apgar_5_minutos: number; // 0-10
  apgar_10_minutos?: number; // Solo si hubo complicaciones

  // Estado y reanimación
  estado_nacimiento: EstadoNacimiento;
  requirio_reanimacion?: boolean;
  tipo_reanimacion?: string;
  tiempo_reanimacion_minutos?: number;

  // Malformaciones y condiciones
  malformaciones_congenitas?: boolean;
  descripcion_malformaciones?: string;
  trastornos_geneticos?: string;

  // Signos vitales iniciales
  frecuencia_cardiaca_inicial?: number;
  frecuencia_respiratoria_inicial?: number;
  temperatura_inicial?: number;
  saturacion_oxigeno_inicial?: number;

  // Procedimientos neonatales
  profilaxis_oftalmica?: boolean;
  vitamina_k?: boolean;
  aspiracion_vias_aereas?: boolean;
  pinzamiento_cordon?: string; // "inmediato" | "tardío"

  // Lactancia y alimentación
  inicio_lactancia?: boolean;
  tiempo_primera_lactancia_minutos?: number;
  tipo_alimentacion?: string;

  // Complicaciones neonatales
  complicaciones_neonatales?: string;
  sindrome_distres_respiratorio?: boolean;
  hipoglucemia?: boolean;
  ictericia?: boolean;

  // Destino y observaciones
  destino_rn?: string; // "alojamiento_conjunto" | "ucin" | "neonatologia"
  motivo_ingreso_ucin?: string;
  observaciones_rn?: string;

  // Metadatos
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - PARTOGRAMA
// ═══════════════════════════════════════════════════════════════════════════

interface PartogramaRegistro {
  id?: number;
  parto?: number;
  parto_id?: number;

  // Tiempo
  hora_registro: string; // ISO datetime
  horas_trabajo_parto: number; // Horas desde inicio del trabajo de parto
  minutos_desde_ingreso?: number;

  // Evaluación cervical
  dilatacion_cervical: number; // cm (0-10)
  borramiento_cervical?: number; // % (0-100)
  consistencia_cervical?: 'firme' | 'intermedia' | 'blanda';
  posicion_cervical?: 'posterior' | 'central' | 'anterior';

  // Descenso fetal
  estacion_fetal: string; // Planos de Hodge: "-5" a "+5"
  variedad_posicion?: string;
  caput?: boolean;
  moldeamiento?: 'no' | 'leve' | 'moderado' | 'severo';

  // Contracciones uterinas
  contracciones_10min: number;
  duracion_contracciones?: number; // segundos
  intensidad_contracciones?: IntensidadContracciones;
  tono_uterino?: 'normal' | 'hipertonia' | 'hipotonia';

  // Monitoreo fetal
  frecuencia_cardiaca_fetal?: number; // lpm
  variabilidad_fcf?: 'ausente' | 'minima' | 'moderada' | 'marcada';
  aceleraciones?: boolean;
  desaceleraciones?: 'no' | 'tempranas' | 'tardias' | 'variables';
  patron_fcf?: 'normal' | 'sospechoso' | 'patologico';

  // Signos vitales maternos
  presion_arterial_sistolica?: number;
  presion_arterial_diastolica?: number;
  presion_arterial_media?: number;
  temperatura?: number;
  pulso_materno?: number;
  frecuencia_respiratoria_materna?: number;
  saturacion_oxigeno_materna?: number;

  // Medicación y fluidos
  oxitocina_dosis?: string;
  velocidad_infusion_oxitocina?: number; // mU/min
  otros_medicamentos?: string;
  volumen_fluidos_iv?: number; // ml

  // Estado de membranas y líquido
  membranas?: 'integras' | 'rotas';
  caracteristicas_liquido_amniotico?: string;

  // Exámenes y procedimientos
  glucosa_capilar?: number;
  ph_cuero_cabelludo_fetal?: number;
  tacto_vaginal_numero?: number;

  // Observaciones y alertas
  observaciones?: string;
  alertas?: string;
  requiere_intervencion?: boolean;

  // Metadatos
  registrado_por?: number;
  fecha_creacion?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - COMPLICACIONES
// ═══════════════════════════════════════════════════════════════════════════

interface ComplicacionParto {
  id?: number;
  parto?: number;
  parto_id?: number;

  // Clasificación de la complicación
  tipo_complicacion: string;
  categoria?: 'materna' | 'fetal' | 'neonatal' | 'quirurgica';
  severidad: SeveridadComplicacion;
  momento_deteccion: MomentoDeteccion;

  // Descripción detallada
  descripcion_detallada: string;
  signos_sintomas?: string;
  hallazgos_clinicos?: string;

  // Diagnóstico
  diagnostico_principal?: string;
  diagnosticos_secundarios?: string;
  codigo_cie10?: string;

  // Manejo y tratamiento
  tratamiento_realizado: string;
  medicamentos_utilizados?: string;
  dosis_medicamentos?: string;
  procedimientos_realizados?: string;

  // Intervenciones quirúrgicas
  requirio_cirugia?: boolean;
  tipo_cirugia?: string;
  duracion_cirugia_minutos?: number;
  hallazgos_quirurgicos?: string;

  // Evolución
  tiempo_resolucion_minutos?: number;
  resolucion_complicacion?: string;
  secuelas?: string;

  // Transfusiones (si aplica)
  requirio_transfusion?: boolean;
  tipo_hemoderivado?: string;
  unidades_transfundidas?: number;

  // Traslado y derivación
  requirio_traslado?: boolean;
  destino_traslado?: string;
  motivo_traslado?: string;

  // Observaciones y seguimiento
  observaciones?: string;
  plan_seguimiento?: string;

  // Metadatos
  reportado_por?: number;
  fecha_creacion?: string;
  fecha_actualizacion?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES - ESTADÍSTICAS Y ANÁLISIS
// ═══════════════════════════════════════════════════════════════════════════

interface EstadisticasPartos {
  total_partos: number;
  partos_vaginales: number;
  cesareas: number;
  tasa_cesareas: number;

  // Por tipo específico
  vaginal_espontaneo: number;
  vaginal_instrumentado: number;
  cesarea_electiva: number;
  cesarea_urgencia: number;
  cesarea_emergencia: number;

  // Complicaciones
  total_complicaciones: number;
  complicaciones_maternas: number;
  complicaciones_fetales: number;
  complicaciones_neonatales: number;
  tasa_complicaciones: number;

  // Recién nacidos
  total_recien_nacidos: number;
  recien_nacidos_vivos: number;
  mortinatos: number;
  muertes_neonatales: number;
  tasa_mortalidad_perinatal: number;

  // APGAR
  apgar_1min_promedio: number;
  apgar_5min_promedio: number;
  apgar_bajo: number; // APGAR < 7

  // Pesos
  peso_promedio_recien_nacidos: number;
  bajo_peso: number; // < 2500g
  muy_bajo_peso: number; // < 1500g
  macrosomia: number; // > 4000g

  // Por período
  por_mes?: { [key: string]: number };
  por_trimestre?: { [key: string]: number };
  tendencia?: string;
}

interface AnalisisPartoPaciente {
  numero_partos_totales: number;
  numero_partos_vaginales: number;
  numero_cesareas: number;
  complicaciones_previas: string[];
  riesgo_actual: 'bajo' | 'moderado' | 'alto';
  recomendaciones: string[];
}

// ═══════════════════════════════════════════════════════════════════════════
// UTILIDADES DE NORMALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Normaliza respuestas del backend que pueden venir como array directo
 * o envueltas en un objeto con 'results', 'data', etc.
 */
function normalizeListResponse<T>(data: any): T[] {
  // Si ya es un array, retornar directo
  if (Array.isArray(data)) {
    return data as T[];
  }

  // Si tiene propiedad 'results' (paginación DRF)
  if (data?.results && Array.isArray(data.results)) {
    return data.results as T[];
  }

  // Si tiene propiedad 'data'
  if (data?.data && Array.isArray(data.data)) {
    return data.data as T[];
  }

  // Si no es ninguno de los anteriores, advertir y retornar array vacío
  console.warn('⚠️ partosService: Respuesta no es array ni tiene results/data:', data);
  return [];
}

/**
 * Normaliza respuesta de objeto único
 */
function normalizeSingleResponse<T>(data: any): T {
  if (data?.data && typeof data.data === 'object') {
    return data.data as T;
  }
  return data as T;
}

// ═══════════════════════════════════════════════════════════════════════════
// SERVICIO PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════

export const partosService = {

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CRUD BÁSICO - PARTOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Lista todos los partos con filtros opcionales
   */
  async listar(filtros?: {
    paciente?: number;
    embarazo?: number;
    medico?: number;
    tipo_parto?: TipoParto;
    fecha_desde?: string;
    fecha_hasta?: string;
    tiene_complicaciones?: boolean;
  }): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[] | { results: Parto[] }>('/partos/', {
        params: filtros
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error('❌ Error listando partos:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getAll(filtros?: any): Promise<Parto[]> {
    return this.listar(filtros);
  },

  /**
   * Obtiene un parto por ID con toda su información anidada
   */
  async obtener(id: number): Promise<Parto> {
    try {
      const response = await api.get<Parto>(`/partos/${id}/`);
      return normalizeSingleResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo parto ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async getById(id: number): Promise<Parto> {
    return this.obtener(id);
  },

  /**
   * Crea un nuevo registro de parto
   */
  async crear(data: Partial<Parto>): Promise<Parto> {
    try {
      const response = await api.post<Parto>('/partos/', data);
      console.log('✅ Parto creado exitosamente');
      return normalizeSingleResponse<Parto>(response.data);
    } catch (error: any) {
      console.error('❌ Error creando parto:', error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async create(data: Partial<Parto>): Promise<Parto> {
    return this.crear(data);
  },

  /**
   * Actualiza un parto existente
   */
  async actualizar(id: number, data: Partial<Parto>): Promise<Parto> {
    try {
      const response = await api.put<Parto>(`/partos/${id}/`, data);
      console.log(`✅ Parto ${id} actualizado exitosamente`);
      return normalizeSingleResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando parto ${id}:`, error);
      throw error;
    }
  },

  /**
   * Actualización parcial (PATCH)
   */
  async actualizarParcial(id: number, data: Partial<Parto>): Promise<Parto> {
    try {
      const response = await api.patch<Parto>(`/partos/${id}/`, data);
      console.log(`✅ Parto ${id} actualizado parcialmente`);
      return normalizeSingleResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error en actualización parcial del parto ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async update(id: number, data: Partial<Parto>): Promise<Parto> {
    return this.actualizar(id, data);
  },

  /**
   * Elimina un parto
   */
  async eliminar(id: number): Promise<void> {
    try {
      await api.delete(`/partos/${id}/`);
      console.log(`✅ Parto ${id} eliminado exitosamente`);
    } catch (error: any) {
      console.error(`❌ Error eliminando parto ${id}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad
   */
  async delete(id: number): Promise<void> {
    return this.eliminar(id);
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // BÚSQUEDAS ESPECÍFICAS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los partos de una paciente
   */
  async obtenerPorPaciente(pacienteId: number): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[]>(`/partos/`, {
        params: { paciente: pacienteId }
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo partos de paciente ${pacienteId}:`, error);
      throw error;
    }
  },

  /**
   * Obtiene partos de un embarazo específico
   */
  async obtenerPorEmbarazo(embarazoId: number): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[]>(`/partos/`, {
        params: { embarazo: embarazoId }
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo partos de embarazo ${embarazoId}:`, error);
      throw error;
    }
  },

  /**
   * Obtiene partos por tipo
   */
  async obtenerPorTipo(tipoParto: TipoParto): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[]>(`/partos/`, {
        params: { tipo_parto: tipoParto }
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo partos tipo ${tipoParto}:`, error);
      throw error;
    }
  },

  /**
   * Obtiene partos por rango de fechas
   */
  async obtenerPorFechas(fechaDesde: string, fechaHasta: string): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[]>(`/partos/`, {
        params: {
          fecha_desde: fechaDesde,
          fecha_hasta: fechaHasta
        }
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo partos por fechas:', error);
      throw error;
    }
  },

  /**
   * Obtiene partos con complicaciones
   */
  async obtenerConComplicaciones(): Promise<Parto[]> {
    try {
      const response = await api.get<Parto[]>(`/partos/`, {
        params: { tiene_complicaciones: true }
      });
      return normalizeListResponse<Parto>(response.data);
    } catch (error: any) {
      console.error('❌ Error obteniendo partos con complicaciones:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // GESTIÓN DE RECIÉN NACIDOS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los recién nacidos de un parto
   */
  async obtenerRecienNacidos(partoId: number): Promise<RecienNacido[]> {
    try {
      const response = await api.get<RecienNacido[]>(`/partos/${partoId}/recien-nacidos/`);
      return normalizeListResponse<RecienNacido>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo recién nacidos del parto ${partoId}:`, error);
      throw error;
    }
  },

  /**
   * Alias para compatibilidad (singular)
   */
  async obtenerRecienNacido(partoId: number): Promise<RecienNacido[]> {
    return this.obtenerRecienNacidos(partoId);
  },

  /**
   * Crea un registro de recién nacido
   */
  async crearRecienNacido(partoId: number, data: Partial<RecienNacido>): Promise<RecienNacido> {
    try {
      const response = await api.post<RecienNacido>(`/partos/${partoId}/recien-nacidos/`, data);
      console.log('✅ Recién nacido registrado exitosamente');
      return normalizeSingleResponse<RecienNacido>(response.data);
    } catch (error: any) {
      console.error('❌ Error registrando recién nacido:', error);
      throw error;
    }
  },

  /**
   * Actualiza información de un recién nacido
   */
  async actualizarRecienNacido(
    partoId: number,
    recienNacidoId: number,
    data: Partial<RecienNacido>
  ): Promise<RecienNacido> {
    try {
      const response = await api.put<RecienNacido>(
        `/partos/${partoId}/recien-nacidos/${recienNacidoId}/`,
        data
      );
      console.log(`✅ Recién nacido ${recienNacidoId} actualizado`);
      return normalizeSingleResponse<RecienNacido>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando recién nacido ${recienNacidoId}:`, error);
      throw error;
    }
  },

  /**
   * Elimina un registro de recién nacido
   */
  async eliminarRecienNacido(partoId: number, recienNacidoId: number): Promise<void> {
    try {
      await api.delete(`/partos/${partoId}/recien-nacidos/${recienNacidoId}/`);
      console.log(`✅ Recién nacido ${recienNacidoId} eliminado`);
    } catch (error: any) {
      console.error(`❌ Error eliminando recién nacido ${recienNacidoId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // GESTIÓN DE PARTOGRAMA
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todos los registros del partograma de un parto
   */
  async obtenerPartogramas(partoId: number): Promise<PartogramaRegistro[]> {
    try {
      const response = await api.get<PartogramaRegistro[]>(`/partos/${partoId}/partogramas/`);
      return normalizeListResponse<PartogramaRegistro>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo partogramas del parto ${partoId}:`, error);
      throw error;
    }
  },

  /**
   * Crea un nuevo registro en el partograma
   */
  async crearRegistroPartograma(
    partoId: number,
    data: Partial<PartogramaRegistro>
  ): Promise<PartogramaRegistro> {
    try {
      const response = await api.post<PartogramaRegistro>(
        `/partos/${partoId}/partogramas/`,
        data
      );
      console.log('✅ Registro de partograma creado');
      return normalizeSingleResponse<PartogramaRegistro>(response.data);
    } catch (error: any) {
      console.error('❌ Error creando registro de partograma:', error);
      throw error;
    }
  },

  /**
   * Actualiza un registro del partograma
   */
  async actualizarRegistroPartograma(
    partoId: number,
    registroId: number,
    data: Partial<PartogramaRegistro>
  ): Promise<PartogramaRegistro> {
    try {
      const response = await api.put<PartogramaRegistro>(
        `/partos/${partoId}/partogramas/${registroId}/`,
        data
      );
      console.log(`✅ Registro de partograma ${registroId} actualizado`);
      return normalizeSingleResponse<PartogramaRegistro>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando registro de partograma ${registroId}:`, error);
      throw error;
    }
  },

  /**
   * Elimina un registro del partograma
   */
  async eliminarRegistroPartograma(partoId: number, registroId: number): Promise<void> {
    try {
      await api.delete(`/partos/${partoId}/partogramas/${registroId}/`);
      console.log(`✅ Registro de partograma ${registroId} eliminado`);
    } catch (error: any) {
      console.error(`❌ Error eliminando registro de partograma ${registroId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // GESTIÓN DE COMPLICACIONES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Obtiene todas las complicaciones de un parto
   */
  async obtenerComplicaciones(partoId: number): Promise<ComplicacionParto[]> {
    try {
      const response = await api.get<ComplicacionParto[]>(
        `/partos/${partoId}/complicaciones/`
      );
      return normalizeListResponse<ComplicacionParto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error obteniendo complicaciones del parto ${partoId}:`, error);
      throw error;
    }
  },

  /**
   * Registra una nueva complicación
   */
  async crearComplicacion(
    partoId: number,
    data: Partial<ComplicacionParto>
  ): Promise<ComplicacionParto> {
    try {
      const response = await api.post<ComplicacionParto>(
        `/partos/${partoId}/complicaciones/`,
        data
      );
      console.log('✅ Complicación registrada');
      return normalizeSingleResponse<ComplicacionParto>(response.data);
    } catch (error: any) {
      console.error('❌ Error registrando complicación:', error);
      throw error;
    }
  },

  /**
   * Actualiza una complicación
   */
  async actualizarComplicacion(
    partoId: number,
    complicacionId: number,
    data: Partial<ComplicacionParto>
  ): Promise<ComplicacionParto> {
    try {
      const response = await api.put<ComplicacionParto>(
        `/partos/${partoId}/complicaciones/${complicacionId}/`,
        data
      );
      console.log(`✅ Complicación ${complicacionId} actualizada`);
      return normalizeSingleResponse<ComplicacionParto>(response.data);
    } catch (error: any) {
      console.error(`❌ Error actualizando complicación ${complicacionId}:`, error);
      throw error;
    }
  },

  /**
   * Elimina una complicación
   */
  async eliminarComplicacion(partoId: number, complicacionId: number): Promise<void> {
    try {
      await api.delete(`/partos/${partoId}/complicaciones/${complicacionId}/`);
      console.log(`✅ Complicación ${complicacionId} eliminada`);
    } catch (error: any) {
      console.error(`❌ Error eliminando complicación ${complicacionId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // CÁLCULOS Y ANÁLISIS
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Calcula puntuación APGAR
   */
  async calcularAPGAR(params: {
    frecuencia_cardiaca: number; // 0-2
    esfuerzo_respiratorio: number; // 0-2
    tono_muscular: number; // 0-2
    respuesta_reflejos: number; // 0-2
    coloracion: number; // 0-2
  }): Promise<{ puntuacion: number; interpretacion: string }> {
    try {
      const response = await api.post('/partos/calcular-apgar/', params);
      return response.data;
    } catch (error: any) {
      console.error('❌ Error calculando APGAR:', error);
      throw error;
    }
  },

  /**
   * Obtiene estadísticas generales de partos
   */
  async obtenerEstadisticas(filtros?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    medico?: number;
  }): Promise<EstadisticasPartos> {
    try {
      const response = await api.get<EstadisticasPartos>('/partos/estadisticas/', {
        params: filtros
      });
      return response.data;
    } catch (error: any) {
      console.error('❌ Error obteniendo estadísticas:', error);
      throw error;
    }
  },

  /**
   * Analiza historial de partos de una paciente
   */
  async analizarHistorialPaciente(pacienteId: number): Promise<AnalisisPartoPaciente> {
    try {
      const response = await api.get<AnalisisPartoPaciente>(
        `/partos/analizar-paciente/${pacienteId}/`
      );
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error analizando historial de paciente ${pacienteId}:`, error);
      throw error;
    }
  },

  /**
   * Calcula riesgo obstétrico
   */
  async calcularRiesgoObstetrico(partoId: number): Promise<{
    nivel_riesgo: 'bajo' | 'moderado' | 'alto' | 'muy_alto';
    factores_riesgo: string[];
    recomendaciones: string[];
  }> {
    try {
      const response = await api.get(`/partos/${partoId}/calcular-riesgo/`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error calculando riesgo obstétrico del parto ${partoId}:`, error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // REPORTES Y EXPORTACIÓN
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Genera reporte PDF de un parto
   */
  async generarReportePDF(partoId: number): Promise<Blob> {
    try {
      const response = await api.get(`/partos/${partoId}/generar-pdf/`, {
        responseType: 'blob'
      });
      console.log(`✅ PDF del parto ${partoId} generado`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error generando PDF del parto ${partoId}:`, error);
      throw error;
    }
  },

  /**
   * Genera partograma en PDF
   */
  async generarPartogramaPDF(partoId: number): Promise<Blob> {
    try {
      const response = await api.get(`/partos/${partoId}/partograma-pdf/`, {
        responseType: 'blob'
      });
      console.log(`✅ PDF del partograma ${partoId} generado`);
      return response.data;
    } catch (error: any) {
      console.error(`❌ Error generando PDF del partograma ${partoId}:`, error);
      throw error;
    }
  },

  /**
   * Exporta datos de partos a Excel
   */
  async exportarExcel(filtros?: {
    fecha_desde?: string;
    fecha_hasta?: string;
    tipo_parto?: TipoParto;
  }): Promise<Blob> {
    try {
      const response = await api.get('/partos/exportar-excel/', {
        params: filtros,
        responseType: 'blob'
      });
      console.log('✅ Excel de partos exportado');
      return response.data;
    } catch (error: any) {
      console.error('❌ Error exportando Excel:', error);
      throw error;
    }
  },

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  // VALIDACIONES Y UTILIDADES
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /**
   * Valida datos de un parto antes de guardar
   */
  validarDatosParto(data: Partial<Parto>): { valido: boolean; errores: string[] } {
    const errores: string[] = [];

    if (!data.embarazo) {
      errores.push('El parto debe estar asociado a un embarazo');
    }

    if (!data.paciente) {
      errores.push('El parto debe estar asociado a una paciente');
    }

    if (!data.tipo_parto) {
      errores.push('Debe especificar el tipo de parto');
    }

    if (!data.edad_gestacional_parto) {
      errores.push('Debe especificar la edad gestacional al momento del parto');
    }

    if (data.tipo_parto?.includes('cesarea') && !data.indicaciones_cesarea) {
      errores.push('Para cesáreas es obligatorio especificar las indicaciones');
    }

    return {
      valido: errores.length === 0,
      errores
    };
  },

  /**
   * Valida datos de un recién nacido
   */
  validarDatosRecienNacido(data: Partial<RecienNacido>): { valido: boolean; errores: string[] } {
    const errores: string[] = [];

    if (!data.numero_gemelo) {
      errores.push('Debe especificar el número de gemelo (1 para único)');
    }

    if (!data.sexo) {
      errores.push('Debe especificar el sexo del recién nacido');
    }

    if (!data.peso_nacimiento || data.peso_nacimiento <= 0) {
      errores.push('Debe especificar un peso válido al nacimiento');
    }

    if (!data.talla_nacimiento || data.talla_nacimiento <= 0) {
      errores.push('Debe especificar una talla válida al nacimiento');
    }

    if (data.apgar_1_minuto === undefined || data.apgar_1_minuto < 0 || data.apgar_1_minuto > 10) {
      errores.push('APGAR al minuto debe estar entre 0 y 10');
    }

    if (data.apgar_5_minutos === undefined || data.apgar_5_minutos < 0 || data.apgar_5_minutos > 10) {
      errores.push('APGAR a los 5 minutos debe estar entre 0 y 10');
    }

    if (!data.estado_nacimiento) {
      errores.push('Debe especificar el estado al nacimiento');
    }

    return {
      valido: errores.length === 0,
      errores
    };
  },

  /**
   * Calcula IMC del recién nacido
   */
  calcularIMCRecienNacido(peso_gramos: number, talla_cm: number): number {
    const peso_kg = peso_gramos / 1000;
    const talla_m = talla_cm / 100;
    return peso_kg / (talla_m * talla_m);
  },

  /**
   * Clasifica peso del recién nacido
   */
  clasificarPesoRecienNacido(peso_gramos: number): string {
    if (peso_gramos < 1000) return 'Extremadamente bajo peso';
    if (peso_gramos < 1500) return 'Muy bajo peso';
    if (peso_gramos < 2500) return 'Bajo peso';
    if (peso_gramos <= 4000) return 'Peso adecuado';
    if (peso_gramos <= 4500) return 'Macrosómico';
    return 'Macrosómico severo';
  },

  /**
   * Interpreta puntuación APGAR
   */
  interpretarAPGAR(puntuacion: number): string {
    if (puntuacion >= 7) return 'Normal';
    if (puntuacion >= 4) return 'Asfixia moderada';
    return 'Asfixia severa';
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// EXPORTACIONES POR DEFECTO
// ═══════════════════════════════════════════════════════════════════════════

