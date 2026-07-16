import React from 'react';
import {
  BellOutlined, WarningOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, FireOutlined, AlertOutlined, InfoCircleOutlined,
  SyncOutlined, CloseCircleOutlined,
} from '@ant-design/icons';
import { AlertaMedica as AlertaMedicaReal } from '../../services/reportesService';
import type dayjs from 'dayjs';

// Tipo de vista usado por esta pantalla: misma forma que el modelo real
// AlertaMedica del backend (reportes/models.py), con "tipo" reutilizado
// para el filtro de prioridad y "categoria"/"notas" derivados de campos reales.
export interface AlertaMedica {
  id: number;
  titulo: string;
  descripcion: string;
  tipo: 'critica' | 'alta' | 'media' | 'baja' | 'info';
  prioridad: string;
  paciente_id?: number;
  paciente_nombre?: string | null;
  estado: 'activa' | 'en_proceso' | 'resuelta' | 'descartada';
  fecha_creacion: string;
  fecha_resolucion?: string;
  categoria: string;
  asignado_a?: string;
  notas?: string;
}

export const mapEstadoReal = (estado: AlertaMedicaReal['estado']): AlertaMedica['estado'] => {
  if (estado === 'revisada' || estado === 'escalada') return 'en_proceso';
  if (estado === 'resuelta') return 'resuelta';
  if (estado === 'descartada') return 'descartada';
  return 'activa';
};

export const mapEstadoVistaABackend = (estado: AlertaMedica['estado']): AlertaMedicaReal['estado'] | '' => {
  if (estado === 'en_proceso') return 'revisada';
  return estado || '';
};

export const mapTipoReal = (prioridad: AlertaMedicaReal['prioridad']): AlertaMedica['tipo'] => {
  if (prioridad === 'critica' || prioridad === 'emergencia') return 'critica';
  if (prioridad === 'alta') return 'alta';
  if (prioridad === 'media') return 'media';
  return 'baja';
};

export const mapAlertaReal = (alerta: AlertaMedicaReal): AlertaMedica => ({
  id: alerta.id,
  titulo: alerta.titulo,
  descripcion: alerta.descripcion || '',
  tipo: mapTipoReal(alerta.prioridad),
  prioridad: alerta.prioridad_display || alerta.prioridad,
  paciente_id: alerta.paciente_id,
  paciente_nombre: alerta.paciente_nombre,
  estado: mapEstadoReal(alerta.estado),
  fecha_creacion: alerta.fecha_creacion,
  fecha_resolucion: alerta.fecha_resolucion,
  categoria: alerta.modulo_origen_display || alerta.modulo_origen,
  notas: alerta.comentario_resolucion || alerta.comentario_revision || undefined,
});

export interface AlertState {
  alertas: AlertaMedica[];
  loading: boolean;
  filtroTipo: string;
  filtroEstado: string;
  busqueda: string;
  alertaSeleccionada: AlertaMedica | null;
  modalVisible: boolean;
  rangoFechas: [dayjs.Dayjs | null, dayjs.Dayjs | null];
  vistaActiva: string;
}

export type AlertAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ALERTAS'; payload: AlertaMedica[] }
  | { type: 'SET_FILTRO_TIPO'; payload: string }
  | { type: 'SET_FILTRO_ESTADO'; payload: string }
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_ALERTA_SELECCIONADA'; payload: AlertaMedica | null }
  | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_RANGO_FECHAS'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] }
  | { type: 'SET_VISTA_ACTIVA'; payload: string }
  | { type: 'CLEAR_FILTERS' };

export const initialAlertState: AlertState = {
  alertas: [],
  loading: false,
  filtroTipo: '',
  filtroEstado: 'activa',
  busqueda: '',
  alertaSeleccionada: null,
  modalVisible: false,
  rangoFechas: [null, null],
  vistaActiva: 'todas',
};

export function alertReducer(state: AlertState, action: AlertAction): AlertState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ALERTAS':
      return { ...state, alertas: action.payload, loading: false };
    case 'SET_FILTRO_TIPO':
      return { ...state, filtroTipo: action.payload };
    case 'SET_FILTRO_ESTADO':
      return { ...state, filtroEstado: action.payload };
    case 'SET_BUSQUEDA':
      return { ...state, busqueda: action.payload };
    case 'SET_ALERTA_SELECCIONADA':
      return { ...state, alertaSeleccionada: action.payload };
    case 'SET_MODAL_VISIBLE':
      return { ...state, modalVisible: action.payload };
    case 'SET_RANGO_FECHAS':
      return { ...state, rangoFechas: action.payload };
    case 'SET_VISTA_ACTIVA':
      return { ...state, vistaActiva: action.payload };
    case 'CLEAR_FILTERS':
      return { ...state, filtroTipo: '', filtroEstado: '', busqueda: '', rangoFechas: [null, null] };
    default:
      return state;
  }
}

export const getTipoConfig = (tipo: string) => {
  const configs: Record<string, { icon: React.ReactElement; color: string; text: string }> = {
    'critica': { icon: <FireOutlined />, color: '#f5222d', text: 'Crítica' },
    'alta': { icon: <WarningOutlined />, color: '#fa8c16', text: 'Alta' },
    'media': { icon: <ExclamationCircleOutlined />, color: '#faad14', text: 'Media' },
    'baja': { icon: <InfoCircleOutlined />, color: '#1890ff', text: 'Baja' },
    'info': { icon: <BellOutlined />, color: '#52c41a', text: 'Información' },
  };
  return configs[tipo] || configs['info'];
};

export const getEstadoConfig = (estado: string) => {
  const configs: Record<string, { icon: React.ReactElement; color: string; text: string }> = {
    'activa': { icon: <AlertOutlined />, color: 'error', text: 'Activa' },
    'en_proceso': { icon: <SyncOutlined spin />, color: 'processing', text: 'En Proceso' },
    'resuelta': { icon: <CheckCircleOutlined />, color: 'success', text: 'Resuelta' },
    'descartada': { icon: <CloseCircleOutlined />, color: 'default', text: 'Descartada' },
  };
  return configs[estado] || configs['activa'];
};
