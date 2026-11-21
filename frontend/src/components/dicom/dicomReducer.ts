/**
 * Estado y helpers puros del visor DICOM. Extraído de DICOMViewer.
 */
export interface DICOMState {
  zoom: number;
  brightness: number;
  contrast: number;
  rotation: number;
  tool: 'none' | 'line' | 'circle' | 'arrow';
  annotations: any[];
  isDrawing: boolean;
  modalInfoVisible: boolean;
  measurements: any[];
  stableSeriesId: string;
  stableStudyId: string;
}

export type DICOMAction =
  | { type: 'INIT_IDS' }
  | { type: 'SET_ZOOM'; payload: number }
  | { type: 'SET_BRIGHTNESS'; payload: number }
  | { type: 'SET_CONTRAST'; payload: number }
  | { type: 'SET_ROTATION'; payload: number }
  | { type: 'SET_TOOL'; payload: 'none' | 'line' | 'circle' | 'arrow' }
  | { type: 'SET_DRAWING'; payload: boolean }
  | { type: 'TOGGLE_MODAL'; payload: boolean }
  | { type: 'ADD_MEASUREMENT'; payload: any }
  | { type: 'ADD_ANNOTATION'; payload: any }
  | { type: 'RESET' };

export function generateId(): string {
  return Math.random().toString(36).substring(7).toUpperCase();
}

export const initialDICOMState: DICOMState = {
  zoom: 100,
  brightness: 100,
  contrast: 100,
  rotation: 0,
  tool: 'none',
  annotations: [],
  isDrawing: false,
  modalInfoVisible: false,
  measurements: [],
  stableSeriesId: '',
  stableStudyId: '',
};

export function dicomReducer(state: DICOMState, action: DICOMAction): DICOMState {
  switch (action.type) {
    case 'INIT_IDS':
      return { ...state, stableSeriesId: generateId(), stableStudyId: generateId() };
    case 'SET_ZOOM':
      return { ...state, zoom: action.payload };
    case 'SET_BRIGHTNESS':
      return { ...state, brightness: action.payload };
    case 'SET_CONTRAST':
      return { ...state, contrast: action.payload };
    case 'SET_ROTATION':
      return { ...state, rotation: action.payload };
    case 'SET_TOOL':
      return { ...state, tool: action.payload };
    case 'SET_DRAWING':
      return { ...state, isDrawing: action.payload };
    case 'TOGGLE_MODAL':
      return { ...state, modalInfoVisible: action.payload };
    case 'ADD_MEASUREMENT':
      return { ...state, measurements: [...state.measurements, action.payload] };
    case 'ADD_ANNOTATION':
      return { ...state, annotations: [...state.annotations, action.payload] };
    case 'RESET':
      return {
        ...initialDICOMState,
        stableSeriesId: state.stableSeriesId,
        stableStudyId: state.stableStudyId,
      };
    default:
      return state;
  }
}

export const formatDate = (dateStr: string): string => {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    const year = d.getFullYear();
    return `${day}/${month}/${year}`;
  } catch {
    return dateStr;
  }
};
