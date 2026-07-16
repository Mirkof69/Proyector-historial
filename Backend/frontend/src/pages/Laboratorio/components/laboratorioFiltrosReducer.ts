import type { Dayjs } from 'dayjs';

export interface FiltrosState {
  busqueda: string;
  filtroCategoria: string | undefined;
  filtroEstado: string | undefined;
  filtroFecha: [Dayjs, Dayjs] | null;
}

export type FiltrosAction =
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_CATEGORIA'; payload: string | undefined }
  | { type: 'SET_ESTADO'; payload: string | undefined }
  | { type: 'SET_FECHA'; payload: [Dayjs, Dayjs] | null }
  | { type: 'LIMPIAR' };

export const filtrosReducer = (state: FiltrosState, action: FiltrosAction): FiltrosState => {
  switch (action.type) {
    case 'SET_BUSQUEDA': return { ...state, busqueda: action.payload };
    case 'SET_CATEGORIA': return { ...state, filtroCategoria: action.payload };
    case 'SET_ESTADO': return { ...state, filtroEstado: action.payload };
    case 'SET_FECHA': return { ...state, filtroFecha: action.payload };
    case 'LIMPIAR': return { busqueda: '', filtroCategoria: undefined, filtroEstado: undefined, filtroFecha: null };
    default: return state;
  }
};
