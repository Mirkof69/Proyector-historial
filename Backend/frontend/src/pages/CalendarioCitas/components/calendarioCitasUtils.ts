import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import type { BadgeProps } from 'antd';
import { Cita } from '../../../services/citasService';

export interface CitaDelDia {
  id: number;
  hora: string;
  paciente: string;
  tipo: string;
  estado: string;
  motivo: string;
}

export interface CalendarioState {
  loading: boolean;
  citas: Cita[];
  citasFiltradas: Cita[];
  modalVisible: boolean;
  citasDelDiaSeleccionado: CitaDelDia[];
  diaSeleccionado: Dayjs;
  filtroEstado: string;
  filtroTipo: string;
  mesActual: Dayjs;
}

export type CalendarioAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_CITAS'; payload: Cita[] }
  | { type: 'SET_CITAS_FILTRADAS'; payload: Cita[] }
  | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_DIA_SELECCIONADO'; payload: CitaDelDia[] }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'SET_FILTRO_TIPO'; payload: string }
  | { type: 'SET_MES_ACTUAL'; payload: Dayjs }
  | { type: 'CLEAR_FILTERS' };

export const initialCalendarioState: CalendarioState = {
  loading: false,
  citas: [],
  citasFiltradas: [],
  modalVisible: false,
  citasDelDiaSeleccionado: [],
  diaSeleccionado: dayjs(),
  filtroEstado: '',
  filtroTipo: '',
  mesActual: dayjs(),
};

export function calendarioReducer(state: CalendarioState, action: CalendarioAction): CalendarioState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_CITAS':
      return { ...state, citas: action.payload, loading: false };
    case 'SET_CITAS_FILTRADAS':
      return { ...state, citasFiltradas: action.payload };
    case 'SET_MODAL_VISIBLE':
      return { ...state, modalVisible: action.payload };
    case 'SET_DIA_SELECCIONADO':
      return { ...state, citasDelDiaSeleccionado: action.payload };
    case 'SET_FILTRO_ESTADO':
      return { ...state, filtroEstado: action.payload };
    case 'SET_FILTRO_TIPO':
      return { ...state, filtroTipo: action.payload };
    case 'SET_MES_ACTUAL':
      return { ...state, mesActual: action.payload };
    case 'CLEAR_FILTERS':
      return { ...state, filtroEstado: '', filtroTipo: '' };
    default:
      return state;
  }
}

export const getEstadoBadge = (estado: string): BadgeProps['status'] => {
  const estados: Record<string, BadgeProps['status']> = {
    pendiente: 'warning',
    confirmada: 'processing',
    completada: 'success',
    cancelada: 'error',
  };
  return estados[estado] || 'default';
};

export const getEstadoColor = (estado: string): string => {
  const colores: Record<string, string> = {
    pendiente: '#faad14',
    confirmada: '#1890ff',
    completada: '#52c41a',
    cancelada: '#ff4d4f',
  };
  return colores[estado] || '#d9d9d9';
};

export const getTipoColor = (tipo: string): string => {
  const colores: Record<string, string> = {
    control_prenatal: '#1890ff',
    ecografia: '#722ed1',
    consulta_general: '#13c2c2',
    emergencia: '#ff4d4f',
    seguimiento: '#52c41a',
    laboratorio: '#fa8c16',
    procedimiento: '#eb2f96',
  };
  return colores[tipo] || '#d9d9d9';
};

export const esAtrasada = (fechaHora: string, estado: string): boolean => (
  dayjs(fechaHora).isBefore(dayjs()) &&
  (estado === 'pendiente' || estado === 'confirmada')
);
