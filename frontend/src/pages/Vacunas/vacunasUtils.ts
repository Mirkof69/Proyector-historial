import dayjs from 'dayjs';
import { RegistroVacuna } from '../../services/vacunasService';

// Interfaz extendida con información adicional para display
export interface RegistroVacunaExtended extends RegistroVacuna {
  paciente_info?: { nombre_completo: string; id_clinico: string; edad?: number };
  tipo_vacuna_info?: { nombre: string; descripcion: string; dosis_requeridas: number };
  aplicada_por?: string;
  paciente_nombre?: string;
  tipo_vacuna_nombre?: string;
}

// Series de gráficas del tema (tokens.css): cambian solas con el tema.
export const COLORS = ['var(--grafico-1)', 'var(--grafico-2)', 'var(--grafico-3)', 'var(--grafico-4)', 'var(--grafico-5)', 'var(--grafico-6)'];
export const AXIS_TICK_STYLE = { fill: 'var(--color-texto-2)', fontSize: 12 };
export const BAR_RADIUS: [number, number, number, number] = [4, 4, 0, 0];

// ── Estado de filtros (reducer a nivel de módulo: identidad estable) ─────────
export interface FiltrosVacunasState {
  searchText: string;
  dateRange: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
  filtroVacuna: string;
  filtroEstado: string;
}

export type FiltrosVacunasAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_DATE_RANGE'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null }
  | { type: 'SET_FILTRO_VACUNA'; payload: string }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'LIMPIAR' };

export const filtrosVacunasReducer = (state: FiltrosVacunasState, action: FiltrosVacunasAction): FiltrosVacunasState => {
  switch (action.type) {
    case 'SET_SEARCH': return { ...state, searchText: action.payload };
    case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
    case 'SET_FILTRO_VACUNA': return { ...state, filtroVacuna: action.payload };
    case 'SET_FILTRO_ESTADO': return { ...state, filtroEstado: action.payload };
    case 'LIMPIAR': return { searchText: '', dateRange: null, filtroVacuna: 'todas', filtroEstado: 'todas' };
    default: return state;
  }
};

export const getEstadoDosis = (vacuna: RegistroVacunaExtended) => {
  if (!vacuna.proxima_dosis_fecha) {
    return { tipo: 'completa', color: 'success', texto: 'Esquema Completo' };
  }

  const diasFaltantes = dayjs(vacuna.proxima_dosis_fecha).startOf('day').diff(dayjs().startOf('day'), 'days');

  if (diasFaltantes < 0) {
    return { tipo: 'vencida', color: 'error', texto: `Atrasada (${Math.abs(diasFaltantes)}d)` };
  } else if (diasFaltantes <= 7) {
    return { tipo: 'proxima', color: 'warning', texto: `En ${diasFaltantes} días` };
  }

  return { tipo: 'programada', color: 'processing', texto: 'Programada' };
};
