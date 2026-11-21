import { TipoCalculadora } from '../../services/calculoHistorialService';

// Mapea las etiquetas usadas en esta pantalla al slug que espera el backend
export const TIPO_CALCULADORA_SLUG: Record<string, TipoCalculadora | undefined> = {
  'Edad Gestacional': 'edad_gestacional',
  'IMC y Peso': 'imc',
  'Score de Bishop': 'bishop',
  'Riesgo Preeclampsia': 'riesgo_preeclampsia',
  'ILA': 'ila',
  'Peso Fetal': 'peso_fetal',
  'Score de Apgar': 'apgar',
  'Capurro': 'capurro',
  'ICC': 'icc',
  'PA Media': 'pa_media',
  'FC Máxima': 'fc_maxima',
};

export interface ResultadoCalculo {
  id: string;
  tipo: string;
  fecha: string;
  datos: any;
  resultado: any;
}

export interface ResultadosState {
  resultadoEG: any;
  resultadoIMC: any;
  resultadoBishop: any;
  resultadoPreeclampsia: any;
  resultadoILA: any;
  resultadoPesoFetal: any;
  resultadoApgar: any;
  resultadoCapurro: any;
  resultadoSilverman: any;
  resultadoBallard: any;
  resultadoICC: any;
  resultadoPA: any;
  resultadoFCMax: any;
}

export type ResultadosAction =
  | { type: 'SET_EG'; payload: any }
  | { type: 'SET_IMC'; payload: any }
  | { type: 'SET_BISHOP'; payload: any }
  | { type: 'SET_PREECLAMPSIA'; payload: any }
  | { type: 'SET_ILA'; payload: any }
  | { type: 'SET_PESO_FETAL'; payload: any }
  | { type: 'SET_APAGAR'; payload: any }
  | { type: 'SET_CAPURRO'; payload: any }
  | { type: 'SET_SILVERMAN'; payload: any }
  | { type: 'SET_BALLARD'; payload: any }
  | { type: 'SET_ICC'; payload: any }
  | { type: 'SET_PA'; payload: any }
  | { type: 'SET_FC_MAX'; payload: any };

export const initialResultados: ResultadosState = {
  resultadoEG: null, resultadoIMC: null, resultadoBishop: null,
  resultadoPreeclampsia: null, resultadoILA: null, resultadoPesoFetal: null,
  resultadoApgar: null, resultadoCapurro: null, resultadoSilverman: null,
  resultadoBallard: null, resultadoICC: null, resultadoPA: null, resultadoFCMax: null,
};

export function resultadosReducer(state: ResultadosState, action: ResultadosAction): ResultadosState {
  switch (action.type) {
    case 'SET_EG': return { ...state, resultadoEG: action.payload };
    case 'SET_IMC': return { ...state, resultadoIMC: action.payload };
    case 'SET_BISHOP': return { ...state, resultadoBishop: action.payload };
    case 'SET_PREECLAMPSIA': return { ...state, resultadoPreeclampsia: action.payload };
    case 'SET_ILA': return { ...state, resultadoILA: action.payload };
    case 'SET_PESO_FETAL': return { ...state, resultadoPesoFetal: action.payload };
    case 'SET_APAGAR': return { ...state, resultadoApgar: action.payload };
    case 'SET_CAPURRO': return { ...state, resultadoCapurro: action.payload };
    case 'SET_SILVERMAN': return { ...state, resultadoSilverman: action.payload };
    case 'SET_BALLARD': return { ...state, resultadoBallard: action.payload };
    case 'SET_ICC': return { ...state, resultadoICC: action.payload };
    case 'SET_PA': return { ...state, resultadoPA: action.payload };
    case 'SET_FC_MAX': return { ...state, resultadoFCMax: action.payload };
    default: return state;
  }
}
