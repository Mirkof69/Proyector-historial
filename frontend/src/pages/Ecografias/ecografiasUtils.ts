import dayjs from 'dayjs';

export interface FiltrosEcografiaState {
  busqueda: string;
  filtroTipo: string;
  filtroFecha: [dayjs.Dayjs, dayjs.Dayjs] | null;
}

export type FiltrosEcografiaAction =
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_TIPO'; payload: string }
  | { type: 'SET_FECHA'; payload: [dayjs.Dayjs, dayjs.Dayjs] | null }
  | { type: 'LIMPIAR' };

export const filtrosEcografiaReducer = (state: FiltrosEcografiaState, action: FiltrosEcografiaAction): FiltrosEcografiaState => {
  switch (action.type) {
    case 'SET_BUSQUEDA': return { ...state, busqueda: action.payload };
    case 'SET_TIPO': return { ...state, filtroTipo: action.payload };
    case 'SET_FECHA': return { ...state, filtroFecha: action.payload };
    case 'LIMPIAR': return { busqueda: '', filtroTipo: '', filtroFecha: null };
    default: return state;
  }
};

// Las cifras por trimestre las calcula ahora el servidor
// (GET /ecografias/resumen/) sobre TODAS las ecografías filtradas.
