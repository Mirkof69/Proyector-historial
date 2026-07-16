import {
  ImagenEcografica,
  AnalisisCNN,
  AnalisisCNNCompleto,
  ReporteNarrativoIA,
  EstadisticasIA,
} from '../../services/iaMedicaService';

export interface IaMedicaState {
  imagenes: ImagenEcografica[];
  estadisticas: EstadisticasIA | null;
  loading: boolean;
  uploading: boolean;
  analyzingId: number | null;
  isModalVisible: boolean;
  selectedAnalysis: {imagen?: ImagenEcografica, analisis: AnalisisCNN} | null;
  isCnnModalVisible: boolean;
  cnnAnalysis: AnalisisCNNCompleto | null;
  cnnImageUrl: string;
  cnnImageId: number | null;
  analyzingCnnId: number | null;
  narrativeReport: ReporteNarrativoIA | null;
  loadingNarrative: boolean;
}

export type IaMedicaAction =
  | { type: 'SET_IMAGENES'; payload: ImagenEcografica[] }
  | { type: 'SET_ESTADISTICAS'; payload: EstadisticasIA | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_UPLOADING'; payload: boolean }
  | { type: 'SET_ANALYZING_ID'; payload: number | null }
  | { type: 'SET_IS_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_SELECTED_ANALYSIS'; payload: {imagen?: ImagenEcografica, analisis: AnalisisCNN} | null }
  | { type: 'SET_IS_CNN_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_CNN_ANALYSIS'; payload: AnalisisCNNCompleto | null }
  | { type: 'SET_CNN_IMAGE_URL'; payload: string }
  | { type: 'SET_CNN_IMAGE_ID'; payload: number | null }
  | { type: 'SET_ANALYZING_CNN_ID'; payload: number | null }
  | { type: 'SET_NARRATIVE_REPORT'; payload: ReporteNarrativoIA | null }
  | { type: 'SET_LOADING_NARRATIVE'; payload: boolean };

export const initialState: IaMedicaState = {
  imagenes: [],
  estadisticas: null,
  loading: true,
  uploading: false,
  analyzingId: null,
  isModalVisible: false,
  selectedAnalysis: null,
  isCnnModalVisible: false,
  cnnAnalysis: null,
  cnnImageUrl: '',
  cnnImageId: null,
  analyzingCnnId: null,
  narrativeReport: null,
  loadingNarrative: false,
};

export function reducer(state: IaMedicaState, action: IaMedicaAction): IaMedicaState {
  switch (action.type) {
    case 'SET_IMAGENES':
      return { ...state, imagenes: action.payload };
    case 'SET_ESTADISTICAS':
      return { ...state, estadisticas: action.payload };
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_UPLOADING':
      return { ...state, uploading: action.payload };
    case 'SET_ANALYZING_ID':
      return { ...state, analyzingId: action.payload };
    case 'SET_IS_MODAL_VISIBLE':
      return { ...state, isModalVisible: action.payload };
    case 'SET_SELECTED_ANALYSIS':
      return { ...state, selectedAnalysis: action.payload };
    case 'SET_IS_CNN_MODAL_VISIBLE':
      return { ...state, isCnnModalVisible: action.payload };
    case 'SET_CNN_ANALYSIS':
      return { ...state, cnnAnalysis: action.payload };
    case 'SET_CNN_IMAGE_URL':
      return { ...state, cnnImageUrl: action.payload };
    case 'SET_CNN_IMAGE_ID':
      return { ...state, cnnImageId: action.payload };
    case 'SET_ANALYZING_CNN_ID':
      return { ...state, analyzingCnnId: action.payload };
    case 'SET_NARRATIVE_REPORT':
      return { ...state, narrativeReport: action.payload };
    case 'SET_LOADING_NARRATIVE':
      return { ...state, loadingNarrative: action.payload };
    default:
      return state;
  }
}
