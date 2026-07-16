import { Dayjs } from 'dayjs';
import { ControlPrenatal } from '../../services/controlesService';
import { Embarazo } from '../../services/embarazosService';

// ═══════════════════════════════════════════════════════════════════════════
// FILTROS AVANZADOS
// ═══════════════════════════════════════════════════════════════════════════

export interface FiltrosAvanzados {
  fechaDesde?: Dayjs;
  fechaHasta?: Dayjs;
  conAlertas?: boolean;
  trimestre?: 1 | 2 | 3 | null;
  rangoPA?: 'normal' | 'hipertension' | 'prehipertension' | null;
  rangoFCF?: 'normal' | 'anormal' | null;
}

export type FiltrosAction =
  | { type: 'SET_FECHA_DESDE'; payload: Dayjs | undefined }
  | { type: 'SET_FECHA_HASTA'; payload: Dayjs | undefined }
  | { type: 'SET_CON_ALERTAS'; payload: boolean | undefined }
  | { type: 'SET_TRIMESTRE'; payload: 1 | 2 | 3 | null }
  | { type: 'SET_RANGO_PA'; payload: 'normal' | 'hipertension' | 'prehipertension' | null }
  | { type: 'SET_RANGO_FCF'; payload: 'normal' | 'anormal' | null }
  | { type: 'RESET' };

export const filtrosReducer = (state: FiltrosAvanzados, action: FiltrosAction): FiltrosAvanzados => {
  switch (action.type) {
    case 'SET_FECHA_DESDE':
      return { ...state, fechaDesde: action.payload };
    case 'SET_FECHA_HASTA':
      return { ...state, fechaHasta: action.payload };
    case 'SET_CON_ALERTAS':
      return { ...state, conAlertas: action.payload };
    case 'SET_TRIMESTRE':
      return { ...state, trimestre: action.payload };
    case 'SET_RANGO_PA':
      return { ...state, rangoPA: action.payload };
    case 'SET_RANGO_FCF':
      return { ...state, rangoFCF: action.payload };
    case 'RESET':
      return {};
    default:
      return state;
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// ESTADO DE UI
// ═══════════════════════════════════════════════════════════════════════════

export interface UIState {
  modalVisible: boolean;
  editingControl: ControlPrenatal | null;
  searchText: string;
  alertasPreview: string[];
  selectedEmbarazo: Embarazo | null;
  pageSize: number;
  lastLoaded: string | null;
  filtrosDrawerVisible: boolean;
  formHasChanges: boolean;
  autoSaveEnabled: boolean;
  showAlertasPanel: boolean;
  controlVistaRapida: ControlPrenatal | null;
}

export type UIAction =
  | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_EDITING_CONTROL'; payload: ControlPrenatal | null }
  | { type: 'SET_SEARCH_TEXT'; payload: string }
  | { type: 'SET_ALERTAS_PREVIEW'; payload: string[] }
  | { type: 'SET_SELECTED_EMBARAZO'; payload: Embarazo | null }
  | { type: 'SET_PAGE_SIZE'; payload: number }
  | { type: 'SET_LAST_LOADED'; payload: string | null }
  | { type: 'SET_FILTROS_DRAWER_VISIBLE'; payload: boolean }
  | { type: 'SET_FORM_HAS_CHANGES'; payload: boolean }
  | { type: 'TOGGLE_AUTO_SAVE' }
  | { type: 'TOGGLE_ALERTAS_PANEL' }
  | { type: 'SET_CONTROL_VISTA_RAPIDA'; payload: ControlPrenatal | null }
  | { type: 'RESET_MODAL' };

export const initialUIState: UIState = {
  modalVisible: false,
  editingControl: null,
  searchText: '',
  alertasPreview: [],
  selectedEmbarazo: null,
  pageSize: 50,
  lastLoaded: null,
  filtrosDrawerVisible: false,
  formHasChanges: false,
  autoSaveEnabled: false,
  showAlertasPanel: false,
  controlVistaRapida: null,
};

export function uiReducer(state: UIState, action: UIAction): UIState {
  switch (action.type) {
    case 'SET_MODAL_VISIBLE':
      return { ...state, modalVisible: action.payload };
    case 'SET_EDITING_CONTROL':
      return { ...state, editingControl: action.payload };
    case 'SET_SEARCH_TEXT':
      return { ...state, searchText: action.payload };
    case 'SET_ALERTAS_PREVIEW':
      return { ...state, alertasPreview: action.payload };
    case 'SET_SELECTED_EMBARAZO':
      return { ...state, selectedEmbarazo: action.payload };
    case 'SET_PAGE_SIZE':
      return { ...state, pageSize: action.payload };
    case 'SET_LAST_LOADED':
      return { ...state, lastLoaded: action.payload };
    case 'SET_FILTROS_DRAWER_VISIBLE':
      return { ...state, filtrosDrawerVisible: action.payload };
    case 'SET_FORM_HAS_CHANGES':
      return { ...state, formHasChanges: action.payload };
    case 'TOGGLE_AUTO_SAVE':
      return { ...state, autoSaveEnabled: !state.autoSaveEnabled };
    case 'TOGGLE_ALERTAS_PANEL':
      return { ...state, showAlertasPanel: !state.showAlertasPanel };
    case 'SET_CONTROL_VISTA_RAPIDA':
      return { ...state, controlVistaRapida: action.payload };
    case 'RESET_MODAL':
      return { ...state, modalVisible: false, editingControl: null, controlVistaRapida: null, selectedEmbarazo: null, alertasPreview: [] };
    default:
      return state;
  }
}
