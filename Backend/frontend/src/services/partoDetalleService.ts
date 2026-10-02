/**
 * API del detalle del parto: partograma, edad gestacional del recién nacido
 * (Capurro / Ballard) y epicrisis. Los tipos son los campos REALES del backend
 * (partos/models.py, partos/models_epicrisis.py); el tipo PartogramaRegistro de
 * partosService tenía nombres que la API no envía (frecuencia_cardiaca_fetal…).
 */
import api from './api';

export interface RegistroPartograma {
  id: number;
  parto: number;
  hora_registro: string;
  horas_trabajo_parto: number;
  dilatacion_cervical: number;
  borramiento_cervical?: number | null;
  angulo_progresion?: string | number | null;
  estacion_fetal: string;
  contracciones_10min: number;
  duracion_contracciones?: number | null;
  intensidad_contracciones?: string;
  fcf_baseline?: number | null;
  variabilidad_fcf?: string;
  desaceleraciones?: string;
  presion_arterial_sistolica?: number | null;
  presion_arterial_diastolica?: number | null;
  temperatura?: string | number | null;
  pulso_materno?: number | null;
  oxitocina_dosis?: string;
  observaciones?: string;
  alerta_progreso_lento?: boolean;
  alerta_fcf_anormal?: boolean;
  alerta_signos_vitales?: boolean;
}

export interface Epicrisis {
  id: number;
  parto: number;
  fecha_ingreso: string | null;
  fecha_egreso: string;
  dias_internacion: number | null;
  diagnostico_ingreso: string;
  cie10_ingreso: string;
  diagnostico_egreso: string;
  cie10_egreso: string;
  resumen_clinico: string;
  examenes_relevantes: string;
  tratamiento_recibido: string;
  procedimientos: string;
  complicaciones: string;
  condicion_materna_egreso: 'sana' | 'con_patologia' | 'traslado' | 'fallecida';
  tipo_egreso: 'alta_medica' | 'alta_solicitada' | 'referencia' | 'fuga' | 'fallecimiento';
  establecimiento_referencia: string;
  consejeria_anticoncepcion: boolean;
  metodo_anticonceptivo: string;
  lactancia_materna_exclusiva: boolean;
  indicaciones_alta: string;
  signos_alarma_explicados: boolean;
  proximo_control: string | null;
  lugar_proximo_control: string;
  pronostico: 'bueno' | 'reservado' | 'malo';
  matricula_profesional: string;
  campos_adicionales: Record<string, unknown>;
  estado: 'borrador' | 'firmada';
  fecha_firma: string | null;
  medico_nombre: string | null;
  paciente_nombre: string;
}

export interface CampoAdicionalEpicrisis {
  id: number;
  clave: string;
  etiqueta: string;
  tipo: 'texto' | 'parrafo' | 'numero' | 'fecha' | 'si_no' | 'opcion';
  opciones: string[];
  obligatorio: boolean;
  ayuda: string;
  orden: number;
  activo: boolean;
}

export interface MedidaAnguloProgresion {
  medidas: { angulo_progresion_grados?: number; margen_grados?: number; interpretacion?: string };
  avisos: string[];
  superposicion_url?: string;
  modelo: { metricas_prueba?: { angulo_progresion_prueba?: { sensibilidad_aop_120?: number; especificidad_aop_120?: number } } };
}

export interface OpcionEscala { puntos: number; descripcion: string }
export interface TablasEdadGestacional {
  capurro: Record<string, { etiqueta: string; opciones: OpcionEscala[] }>;
  capurro_constante_dias: number;
  ballard: { minimo: number; maximo: number; formula: string };
}

const lista = <T,>(data: any): T[] => (Array.isArray(data) ? data : data?.results ?? []);

export const partoDetalleService = {
  async partograma(partoId: number): Promise<RegistroPartograma[]> {
    const r = await api.get('/partos/partograma/', { params: { parto: partoId, page_size: 200, ordering: 'hora_registro' } });
    return lista<RegistroPartograma>(r.data);
  },
  async crearRegistroPartograma(datos: Partial<RegistroPartograma>): Promise<RegistroPartograma> {
    return (await api.post('/partos/partograma/', datos)).data;
  },

  /** Ángulo de progresión medido por la red de IUGC sobre una ecografía intraparto. */
  async medirAnguloProgresion(archivo: File): Promise<MedidaAnguloProgresion> {
    const datos = new FormData();
    datos.append('file', archivo);
    return (await api.post('/partos/angulo-progresion/', datos, {
      headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000,
    })).data;
  },

  async tablasEdadGestacional(): Promise<TablasEdadGestacional> {
    return (await api.get('/partos/edad-gestacional-rn/')).data;
  },
  async actualizarRecienNacido(id: number, datos: Record<string, unknown>) {
    return (await api.patch(`/partos/recien-nacidos/${id}/`, datos)).data;
  },

  async epicrisisDelParto(partoId: number): Promise<Epicrisis | null> {
    const r = await api.get('/partos/epicrisis/', { params: { parto: partoId } });
    return lista<Epicrisis>(r.data)[0] ?? null;
  },
  async sugerenciaEpicrisis(partoId: number): Promise<Partial<Epicrisis>> {
    return (await api.get('/partos/epicrisis/sugerencia/', { params: { parto: partoId } })).data;
  },
  async guardarEpicrisis(datos: Partial<Epicrisis>, id?: number): Promise<Epicrisis> {
    return id ? (await api.patch(`/partos/epicrisis/${id}/`, datos)).data : (await api.post('/partos/epicrisis/', datos)).data;
  },
  async firmarEpicrisis(id: number, matricula: string): Promise<Epicrisis> {
    return (await api.post(`/partos/epicrisis/${id}/firmar/`, { matricula_profesional: matricula })).data;
  },
  async camposAdicionales(): Promise<CampoAdicionalEpicrisis[]> {
    return lista<CampoAdicionalEpicrisis>((await api.get('/partos/epicrisis-campos/', { params: { page_size: 200 } })).data)
      .filter((c) => c.activo)
      .sort((a, b) => a.orden - b.orden);
  },
};

/** Primer mensaje legible de un error de validación de DRF. */
export const mensajeDeError = (error: any, porDefecto: string): string => {
  const datos = error?.response?.data;
  if (!datos) return porDefecto;
  if (typeof datos === 'string') return datos;
  if (datos.error || datos.detail) return datos.error || datos.detail;
  const primero = Object.entries(datos)[0];
  if (!primero) return porDefecto;
  const [, valor] = primero;
  return Array.isArray(valor) ? String(valor[0]) : String(valor);
};
