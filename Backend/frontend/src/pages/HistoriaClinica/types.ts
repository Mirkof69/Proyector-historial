import { Dayjs } from 'dayjs';

export interface Usuario {
  id: number;
  username: string;
  nombre_completo: string;
  nombre?: string;
  especialidad?: string;
}

export interface Paciente {
  id: number;
  id_clinico?: string;
  // Campos reales del API (pacientesService)
  nombre: string;
  apellido_paterno: string;
  apellido_materno?: string;
  nombre_completo?: string;
  // Alias legacy — mantenidos para compatibilidad con código antiguo
  nombres?: string;
  apellidos?: string;
  edad_actual?: number;
  grupo_sanguineo?: string;
  // Campos actuales
  edad?: number;
  tipo_sangre?: string;
  factor_rh?: string;
  fecha_nacimiento: string;
  ci: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  email?: string;
  estado_civil?: string;
  ocupacion?: string;
  nivel_educativo?: string;
  peso_kg?: number;
  altura_cm?: number;
  imc?: number;
  nombre_contacto_emergencia?: string;
  telefono_contacto_emergencia?: string;
  contacto_emergencia_nombre?: string;
  contacto_emergencia_telefono?: string;
  alergias?: string;
  antecedentes_patologicos?: string;
  antecedentes_quirurgicos?: string;
  antecedentes_familiares?: string;
  habitos_toxicos?: string;
  foto_perfil?: string;
  foto?: string;
  seguro_medico?: string;
  activo?: boolean;
  estado_paciente?: string;
  fecha_registro?: string;
  embarazos_activos?: number;
  embarazo_activo?: boolean;
}

export interface Embarazo {
  id: number;
  estado: string;
  fecha_ultima_menstruacion: string;
  fecha_probable_parto: string;
  fecha_probable_parto_eco?: string;
  edad_gestacional_ingreso?: number;
  numero_gesta: number;
  gestas_previas?: number;
  partos_previos: number;
  cesareas_previas: number;
  abortos_previos: number;
  numero_para?: number;
  numero_cesareas?: number;
  numero_abortos?: number;
  ectopicos?: number;
  molares?: number;
  peso_pregestacional?: number;
  talla_materna?: number;
  riesgo: 'BAJO' | 'ALTO' | 'MUY_ALTO';
  riesgo_embarazo?: string;
  observaciones?: string;
  notas?: string;
  creado_por?: Usuario;
  created_by?: Usuario;
}

export interface ControlPrenatal {
  id: number;
  numero_control: number;
  fecha_control: string;
  fecha?: string;
  semanas_gestacion: number;
  dias_gestacion?: number;
  edad_gestacional_semanas?: number;
  peso_actual: number;
  peso_pregestacional?: number;
  talla?: number;
  imc?: number;
  imc_actual?: number;
  ganancia_peso?: number;
  presion_arterial_sistolica: number;
  presion_arterial_diastolica: number;
  presion_arterial?: string;
  frecuencia_cardiaca?: number;
  temperatura?: number;
  altura_uterina?: number;
  frecuencia_cardiaca_fetal?: number;
  presentacion_fetal?: string;
  movimientos_fetales?: string | boolean;
  edema?: string | boolean;
  proteinuria?: string;
  observaciones?: string;
  medico_id?: number;
  medico?: Usuario;
  alertas?: any[];
  tiene_alertas?: boolean;
  proximo_control?: string;
}

export interface Ecografia {
  id: number;
  fecha: string;
  tipo: string;
  /**
   * Nombres REALES del serializer de la API (EcografiaListSerializer).
   * El tipo declaraba `edad_gestacional_calculada`, que la API nunca manda:
   * la tabla y las tarjetas mostraban "EG: sem" vacio en toda la lista.
   * `edad_gestacional` viene ya formateada ("32+4").
   */
  edad_gestacional?: string;
  edad_gestacional_semanas?: number;
  edad_gestacional_dias?: number;
  edad_gestacional_calculada?: number;
  /** Vive en la biometria; el serializer la expone aplanada. */
  peso_fetal_estimado?: number;
  percentil?: number;
  placenta_posicion: string;
  liquido_amniotico: string;
  longitud_cervical?: number;
  conclusion: string;
  imagenes_count: number;
  archivo_reporte?: string;
}

export interface Laboratorio {
  id: number;
  fecha_toma: string;
  categoria: string;
  /** La API manda la PK numerica en `tipo_examen` y el nombre aparte. */
  tipo_examen: string | number;
  tipo_examen_nombre?: string;
  resultado: string;
  valores_referencia: string;
  es_anormal: boolean;
  observaciones_medicas?: string;
  archivo_adjunto?: string;
}

export interface NotaEvolucion {
  id: number;
  fecha_hora: string;
  tipo: 'CONSULTA' | 'URGENCIA' | 'JUNTA_MEDICA' | 'TELECONSULTA' | 'EVOLUCION' | 'INGRESO';
  subjetivo: string;
  objetivo: string;
  analisis: string;
  plan: string;
  autor: Usuario;
  presion_arterial?: string;
  frecuencia_cardiaca?: number;
  temperatura?: number;
  peso?: number;
  diagnostico_cie10?: string;
  observaciones_adicionales?: string;
  examenes_solicitados?: string;
  fecha_modificacion?: string;
  semanas_gestacion?: number;
  dias_gestacion?: number;
  numero_consulta?: number;
}

export interface Tratamiento {
  id: number;
  medicamento: string;
  dosis: string;
  frecuencia: string;
  duracion: string;
  fecha_inicio: string;
  activo: boolean;
  via_administracion?: string;
  fecha_fin?: string;
  indicaciones?: string;
  motivo?: string;
  efectos_secundarios?: string;
  observaciones?: string;
  motivo_suspension?: string;
  medico?: Usuario;
  fecha_prescripcion?: string;
  fecha_modificacion?: string;
  fecha_suspension?: string;
}

export interface Vacuna {
  id: number;
  nombre: string;
  fecha_aplicacion: string;
  dosis: number;
  lote?: string;
  via_administracion?: string;
  fabricante?: string;
  sitio_aplicacion?: string;
  fecha_proxima_dosis?: string;
  reacciones_adversas?: string;
  observaciones?: string;
  aplicada_por?: Usuario;
  fecha_registro?: string;
  fecha_modificacion?: string;
  semanas_gestacion?: number;
}

export interface Cita {
  id: number;
  fecha_hora: string;
  motivo: string;
  estado: 'PROGRAMADA' | 'COMPLETADA' | 'CANCELADA' | 'REPROGRAMADA';
  tipo: 'CONTROL_PRENATAL' | 'ECOGRAFIA' | 'LABORATORIO' | 'EMERGENCIA' | 'CONSULTA_GENERAL';
  notas?: string;
  medico?: Usuario;
}

interface RecienNacido {
  id: number;
  sexo: 'masculino' | 'femenino';
  peso_nacimiento: number;
  talla_nacimiento: number;
  apgar_1_minuto: number;
  apgar_5_minutos: number;
  perimetro_cefalico?: number;
  estado_nacimiento?: string;
  destino_rn?: string;
}

export interface Parto {
  id: number;
  fecha_parto: string;
  fecha_inicio_trabajo_parto: string;
  fecha_hora_inicio?: string;
  fecha_hora_fin?: string;
  tipo_parto: 'eutocico' | 'cesarea' | 'instrumentado';
  tipo?: string;
  duracion_trabajo_parto_horas?: number;
  duracion_periodo_expulsivo_minutos?: number;
  recien_nacidos: RecienNacido[];
  sexo_recien_nacido?: 'M' | 'F';
  peso_recien_nacido?: number;
  talla_recien_nacido?: number;
  apgar_1min?: number;
  apgar_5min?: number;
  complicaciones_maternas?: string;
  complicaciones?: string;
  observaciones_parto?: string;
  observaciones?: string;
}

export interface AlertaClinica {
  id: string;
  tipo: 'ERROR' | 'WARNING' | 'INFO';
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
  mensaje: string;
  categoria: string;
  fecha_generacion: string;
  resuelta: boolean;
  acciones_recomendadas?: string[];
}

export interface CalculadoraResultado {
  nombre: string;
  valor: number | string;
  unidad?: string;
  interpretacion?: string;
  rango_normal?: string;
  alerta?: boolean;
}

export interface ProtocoloObstetrico {
  id: number;
  nombre: string;
  semanas_inicio: number;
  semanas_fin: number;
  descripcion: string;
  examenes_requeridos: string[];
  cumplido: boolean;
}

interface TendenciaLaboratorio {
  examen: string;
  valores: Array<{ fecha: string; valor: number; referencia: string }>;
  tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE';
}

export interface EstadisticaGlobal {
  total_controles: number;
  total_ecografias: number;
  total_laboratorios: number;
  total_notas: number;
  total_registros: number;
  ultimo_control?: string;
  proxima_cita?: string;
  edad_gestacional_semanas_actual: number;
  dias_hasta_fpp: number;
  adherencia_tratamiento: number;
  porcentaje_protocolos_cumplidos: number;
}

export interface ExportConfig {
  formato: 'PDF' | 'EXCEL' | 'JSON';
  secciones: string[];
  incluir_graficas: boolean;
  periodo_inicio?: string;
  periodo_fin?: string;
}

export interface BusquedaFiltro {
  texto: string;
  categoria: 'TODO' | 'CONTROLES' | 'ECOGRAFIAS' | 'LABORATORIOS' | 'NOTAS';
  fecha_inicio?: string;
  fecha_fin?: string;
  solo_anormales?: boolean;
}

export interface RecordatorioClinico {
  id: string;
  tipo: 'CONTROL' | 'EXAMEN' | 'VACUNA' | 'TRATAMIENTO';
  titulo: string;
  descripcion: string;
  fecha_programada: string;
  dias_restantes: number;
  completado: boolean;
  prioridad: 'ALTA' | 'MEDIA' | 'BAJA';
}
