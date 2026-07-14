import React from 'react';
import {
  CheckOutlined,
  WarningOutlined,
  MessageOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type dayjs from 'dayjs';

// ── Estado de filtros (reducer a nivel de módulo: identidad estable) ─────────
export interface FiltrosNotifState {
  searchText: string;
  filterType: string | undefined;
  filterRead: string | undefined;
  dateRange: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
}

export type FiltrosNotifAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_TYPE'; payload: string | undefined }
  | { type: 'SET_READ'; payload: string | undefined }
  | { type: 'SET_DATE_RANGE'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null }
  | { type: 'LIMPIAR' };

export const filtrosNotifReducer = (state: FiltrosNotifState, action: FiltrosNotifAction): FiltrosNotifState => {
  switch (action.type) {
    case 'SET_SEARCH': return { ...state, searchText: action.payload };
    case 'SET_TYPE': return { ...state, filterType: action.payload };
    case 'SET_READ': return { ...state, filterRead: action.payload };
    case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
    case 'LIMPIAR': return { searchText: '', filterType: undefined, filterRead: 'todas', dateRange: null };
    default: return state;
  }
};

// Mapeadores puros de tipo → icono/etiqueta/clase (nivel de módulo).
export const getTypeIcon = (type: string) => {
  switch (type) {
    case 'error': return <WarningOutlined />;
    case 'warning': return <WarningOutlined />;
    case 'success': return <CheckOutlined />;
    case 'cita': return <CalendarOutlined />;
    case 'examen': return <MedicineBoxOutlined />;
    case 'documento': return <FileTextOutlined />;
    case 'info':
    default: return <MessageOutlined />;
  }
};

export const getTypeLabel = (type: string) => {
  switch (type) {
    case 'error': return 'Alerta';
    case 'warning': return 'Advertencia';
    case 'success': return 'Éxito';
    case 'cita': return 'Cita';
    case 'examen': return 'Examen';
    case 'documento': return 'Documento';
    case 'info': return 'Información';
    default: return type;
  }
};

export const getTypeClass = (type: string) => {
  switch (type) {
    case 'error': return 'alerta';
    case 'warning': return 'alerta';
    case 'success': return 'mensaje';
    case 'cita': return 'cita';
    case 'examen': return 'examen';
    case 'documento': return 'recordatorio';
    case 'info': return 'mensaje';
    default: return 'default';
  }
};
