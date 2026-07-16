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

export const calcularEstadisticas = (ecografias: any[]) => ({
  total: ecografias.length,
  primerTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) < 14).length,
  segundoTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) >= 14 && (e.edad_gestacional_semanas || 0) < 28).length,
  tercerTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) >= 28).length,
  conAlertas: ecografias.filter((e: any) => e.alertas && e.alertas.length > 0).length,
});
