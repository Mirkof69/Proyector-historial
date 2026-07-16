export interface DicomMetadata {
  patientName?: string;
  patientID?: string;
  studyDate?: string;
  modality?: string;
  studyDescription?: string;
  seriesDescription?: string;
  institutionName?: string;
  rows?: number;
  columns?: number;
  pixelSpacing?: number[];
  sliceThickness?: number;
  manufacturer?: string;
  model?: string;
}

export interface ViewerState {
  loading: boolean;
  ecografia: any;
  zoom: number;
  rotation: number;
  windowLevel: number;
  windowWidth: number;
  brightness: number;
  contrast: number;
  invert: boolean;
  fullscreen: boolean;
  activeTool: string;
  measurements: any[];
  annotations: any[];
  showMeasurements: boolean;
  showAnnotations: boolean;
  metadata: DicomMetadata;
  showMetadata: boolean;
  currentImageIndex: number;
  totalImages: number;
  playingCine: boolean;
  settingsVisible: boolean;
  exportModalVisible: boolean;
  showGradCam: boolean;
  nitidezDetectada: number;
  calidadImagen: number;
}

export type ViewerAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ECOGRAFIA'; payload: { ecografia: any; metadata: DicomMetadata; totalImages: number; nitidez: number; calidad: number } }
  | { type: 'SET_ZOOM'; payload: number }
  | { type: 'SET_ROTATION'; payload: number }
  | { type: 'SET_WINDOW_LEVEL'; payload: number }
  | { type: 'SET_WINDOW_WIDTH'; payload: number }
  | { type: 'SET_BRIGHTNESS'; payload: number }
  | { type: 'SET_CONTRAST'; payload: number }
  | { type: 'SET_INVERT'; payload: boolean }
  | { type: 'SET_FULLSCREEN'; payload: boolean }
  | { type: 'SET_ACTIVE_TOOL'; payload: string }
  | { type: 'ADD_MEASUREMENT'; payload: any }
  | { type: 'DELETE_MEASUREMENT'; payload: number }
  | { type: 'ADD_ANNOTATION'; payload: any }
  | { type: 'DELETE_ANNOTATION'; payload: number }
  | { type: 'TOGGLE_METADATA' }
  | { type: 'SET_IMAGE_INDEX'; payload: number }
  | { type: 'SET_PLAYING_CINE'; payload: boolean }
  | { type: 'SET_SETTINGS_VISIBLE'; payload: boolean }
  | { type: 'SET_EXPORT_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_SHOW_GRADCAM'; payload: boolean }
  | { type: 'SET_SHOW_MEASUREMENTS'; payload: boolean }
  | { type: 'SET_SHOW_ANNOTATIONS'; payload: boolean }
  | { type: 'RESET_VIEW' };

export const initialState: ViewerState = {
  loading: true,
  ecografia: null,
  zoom: 100,
  rotation: 0,
  windowLevel: 50,
  windowWidth: 100,
  brightness: 100,
  contrast: 100,
  invert: false,
  fullscreen: false,
  activeTool: 'pan',
  measurements: [],
  annotations: [],
  showMeasurements: true,
  showAnnotations: true,
  metadata: {},
  showMetadata: false,
  currentImageIndex: 0,
  totalImages: 1,
  playingCine: false,
  settingsVisible: false,
  exportModalVisible: false,
  showGradCam: false,
  nitidezDetectada: 85,
  calidadImagen: 92,
};

export function viewerReducer(state: ViewerState, action: ViewerAction): ViewerState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ECOGRAFIA':
      return {
        ...state,
        loading: false,
        ecografia: action.payload.ecografia,
        metadata: action.payload.metadata,
        totalImages: action.payload.totalImages,
        nitidezDetectada: action.payload.nitidez,
        calidadImagen: action.payload.calidad,
      };
    case 'SET_ZOOM':
      return { ...state, zoom: action.payload };
    case 'SET_ROTATION':
      return { ...state, rotation: action.payload };
    case 'SET_WINDOW_LEVEL':
      return { ...state, windowLevel: action.payload };
    case 'SET_WINDOW_WIDTH':
      return { ...state, windowWidth: action.payload };
    case 'SET_BRIGHTNESS':
      return { ...state, brightness: action.payload };
    case 'SET_CONTRAST':
      return { ...state, contrast: action.payload };
    case 'SET_INVERT':
      return { ...state, invert: action.payload };
    case 'SET_FULLSCREEN':
      return { ...state, fullscreen: action.payload };
    case 'SET_ACTIVE_TOOL':
      return { ...state, activeTool: action.payload };
    case 'ADD_MEASUREMENT':
      return { ...state, measurements: [...state.measurements, action.payload] };
    case 'DELETE_MEASUREMENT':
      return { ...state, measurements: state.measurements.filter(m => m.id !== action.payload) };
    case 'ADD_ANNOTATION':
      return { ...state, annotations: [...state.annotations, action.payload] };
    case 'DELETE_ANNOTATION':
      return { ...state, annotations: state.annotations.filter(a => a.id !== action.payload) };
    case 'TOGGLE_METADATA':
      return { ...state, showMetadata: !state.showMetadata };
    case 'SET_IMAGE_INDEX':
      return { ...state, currentImageIndex: action.payload };
    case 'SET_PLAYING_CINE':
      return { ...state, playingCine: action.payload };
    case 'SET_SETTINGS_VISIBLE':
      return { ...state, settingsVisible: action.payload };
    case 'SET_EXPORT_MODAL_VISIBLE':
      return { ...state, exportModalVisible: action.payload };
    case 'SET_SHOW_GRADCAM':
      return { ...state, showGradCam: action.payload };
    case 'SET_SHOW_MEASUREMENTS':
      return { ...state, showMeasurements: action.payload };
    case 'SET_SHOW_ANNOTATIONS':
      return { ...state, showAnnotations: action.payload };
    case 'RESET_VIEW':
      return {
        ...state,
        zoom: 100,
        rotation: 0,
        windowLevel: 50,
        windowWidth: 100,
        brightness: 100,
        contrast: 100,
        invert: false,
      };
    default:
      return state;
  }
}
