import type { Dayjs } from 'dayjs';

export interface FiltrosPartosState {
  searchText: string;
  dateRange: [Dayjs, Dayjs] | null;
  tipoPartoFilter: string | null;
}

export type FiltrosPartosAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_DATE_RANGE'; payload: [Dayjs, Dayjs] | null }
  | { type: 'SET_TIPO_PARTO'; payload: string | null }
  | { type: 'LIMPIAR' };

export const filtrosPartosReducer = (state: FiltrosPartosState, action: FiltrosPartosAction): FiltrosPartosState => {
  switch (action.type) {
    case 'SET_SEARCH': return { ...state, searchText: action.payload };
    case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
    case 'SET_TIPO_PARTO': return { ...state, tipoPartoFilter: action.payload };
    case 'LIMPIAR': return { searchText: '', dateRange: null, tipoPartoFilter: null };
    default: return state;
  }
};
