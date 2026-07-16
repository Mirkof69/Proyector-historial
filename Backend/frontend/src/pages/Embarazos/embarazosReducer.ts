import dayjs, { Dayjs } from 'dayjs';
import { Embarazo } from '../../services/embarazosService';

// =============================================================================
// TIPOS Y CONSTANTES EXTENDIDOS
// =============================================================================

// Interfaz extendida para visualización y manipulación en frontend
export interface EmbarazoExtendido extends Embarazo {
    paciente_nombre?: string;        // Viene del serializer (backend)
    paciente_info?: any;             // Viene del serializer detail (backend)
    edad_gestacional?: string;       // Calculado backend
    edad_gestacional_semanas_num?: number;  // Calculado frontend para barra progreso
    edad_gestacional_dias_num?: number;     // Calculado frontend
    trimestre_actual?: number;       // Calculado frontend
}

export interface PacienteOption {
    id: number;
    nombre_completo: string;
    ci: string;
    edad: number;
    peso_kg?: number;
    altura_cm?: number;
}

// Colores para riesgos (Semántica Clínica)
export const RISK_COLORS = {
    bajo: 'green',
    medio: 'orange',
    alto: 'red',
};

export const RISK_LABELS = {
    bajo: 'Bajo Riesgo',
    medio: 'Riesgo Medio',
    alto: 'Alto Riesgo Obstétrico',
};

export const STATUS_COLORS = {
    activo: 'processing',
    finalizado: 'default',
    perdida: 'error',
};

export const STATUS_LABELS = {
    activo: 'ACTIVO',
    finalizado: 'FINALIZADO',
    perdida: 'PÉRDIDA / ABORTO',
};

export interface EmbarazosState {
    embarazos: EmbarazoExtendido[];
    pacientesOptions: PacienteOption[];
    loadingPacientes: boolean;
    medicos: any[];
    loadingMedicos: boolean;
    loading: boolean;
    actionLoading: boolean;
    modalVisible: boolean;
    drawerVisible: boolean;
    editingEmbarazo: EmbarazoExtendido | null;
    selectedEmbarazo: EmbarazoExtendido | null;
    imcCalculado: string;
    edadGestacionalCalculada: string;
    searchText: string;
    riskFilter: string | null;
    statusFilter: string | null;
    uploadModalVisible: boolean;
    uploadingFiles: boolean;
    fileList: any[];
    exportLoading: boolean;
    syncLoading: boolean;
    historialModalVisible: boolean;
    filtrosAvanzadosVisible: boolean;
    vistaComparacion: 'tabla' | 'tarjetas';
    mostrarFinalizados: boolean;
    modalAnalisisEvolucionVisible: boolean;
    modalReportesVisible: boolean;
    modalAlertasVisible: boolean;
    drawerPanelControlVisible: boolean;
}

export type EmbarazosAction =
    | { type: 'SET_EMBARAZOS'; payload: EmbarazoExtendido[] }
    | { type: 'SET_PACIENTES_OPTIONS'; payload: PacienteOption[] }
    | { type: 'SET_LOADING_PACIENTES'; payload: boolean }
    | { type: 'SET_MEDICOS'; payload: any[] }
    | { type: 'SET_LOADING_MEDICOS'; payload: boolean }
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_ACTION_LOADING'; payload: boolean }
    | { type: 'SET_MODAL_VISIBLE'; payload: boolean }
    | { type: 'SET_DRAWER_VISIBLE'; payload: boolean }
    | { type: 'SET_EDITING_EMBARAZO'; payload: EmbarazoExtendido | null }
    | { type: 'SET_SELECTED_EMBARAZO'; payload: EmbarazoExtendido | null }
    | { type: 'SET_IMC_CALCULADO'; payload: string }
    | { type: 'SET_EDAD_GESTACIONAL_CALCULADA'; payload: string }
    | { type: 'SET_SEARCH_TEXT'; payload: string }
    | { type: 'SET_RISK_FILTER'; payload: string | null }
    | { type: 'SET_STATUS_FILTER'; payload: string | null }
    | { type: 'SET_UPLOAD_MODAL_VISIBLE'; payload: boolean }
    | { type: 'SET_UPLOADING_FILES'; payload: boolean }
    | { type: 'SET_FILE_LIST'; payload: any[] }
    | { type: 'SET_EXPORT_LOADING'; payload: boolean }
    | { type: 'SET_SYNC_LOADING'; payload: boolean }
    | { type: 'SET_HISTORIAL_MODAL_VISIBLE'; payload: boolean }
    | { type: 'SET_FILTROS_AVANZADOS_VISIBLE'; payload: boolean }
    | { type: 'SET_VISTA_COMPARACION'; payload: 'tabla' | 'tarjetas' }
    | { type: 'SET_MOSTRAR_FINALIZADOS'; payload: boolean }
    | { type: 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE'; payload: boolean }
    | { type: 'SET_MODAL_REPORTES_VISIBLE'; payload: boolean }
    | { type: 'SET_MODAL_ALERTAS_VISIBLE'; payload: boolean }
    | { type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE'; payload: boolean };

export const initialState: EmbarazosState = {
    embarazos: [],
    pacientesOptions: [],
    loadingPacientes: false,
    medicos: [],
    loadingMedicos: false,
    loading: false,
    actionLoading: false,
    modalVisible: false,
    drawerVisible: false,
    editingEmbarazo: null,
    selectedEmbarazo: null,
    imcCalculado: '',
    edadGestacionalCalculada: '',
    searchText: '',
    riskFilter: null,
    statusFilter: null,
    uploadModalVisible: false,
    uploadingFiles: false,
    fileList: [],
    exportLoading: false,
    syncLoading: false,
    historialModalVisible: false,
    filtrosAvanzadosVisible: false,
    vistaComparacion: 'tabla',
    mostrarFinalizados: false,
    modalAnalisisEvolucionVisible: false,
    modalReportesVisible: false,
    modalAlertasVisible: false,
    drawerPanelControlVisible: false,
};

export function reducer(state: EmbarazosState, action: EmbarazosAction): EmbarazosState {
    switch (action.type) {
        case 'SET_EMBARAZOS':
            return { ...state, embarazos: action.payload };
        case 'SET_PACIENTES_OPTIONS':
            return { ...state, pacientesOptions: action.payload };
        case 'SET_LOADING_PACIENTES':
            return { ...state, loadingPacientes: action.payload };
        case 'SET_MEDICOS':
            return { ...state, medicos: action.payload };
        case 'SET_LOADING_MEDICOS':
            return { ...state, loadingMedicos: action.payload };
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        case 'SET_ACTION_LOADING':
            return { ...state, actionLoading: action.payload };
        case 'SET_MODAL_VISIBLE':
            return { ...state, modalVisible: action.payload };
        case 'SET_DRAWER_VISIBLE':
            return { ...state, drawerVisible: action.payload };
        case 'SET_EDITING_EMBARAZO':
            return { ...state, editingEmbarazo: action.payload };
        case 'SET_SELECTED_EMBARAZO':
            return { ...state, selectedEmbarazo: action.payload };
        case 'SET_IMC_CALCULADO':
            return { ...state, imcCalculado: action.payload };
        case 'SET_EDAD_GESTACIONAL_CALCULADA':
            return { ...state, edadGestacionalCalculada: action.payload };
        case 'SET_SEARCH_TEXT':
            return { ...state, searchText: action.payload };
        case 'SET_RISK_FILTER':
            return { ...state, riskFilter: action.payload };
        case 'SET_STATUS_FILTER':
            return { ...state, statusFilter: action.payload };
        case 'SET_UPLOAD_MODAL_VISIBLE':
            return { ...state, uploadModalVisible: action.payload };
        case 'SET_UPLOADING_FILES':
            return { ...state, uploadingFiles: action.payload };
        case 'SET_FILE_LIST':
            return { ...state, fileList: action.payload };
        case 'SET_EXPORT_LOADING':
            return { ...state, exportLoading: action.payload };
        case 'SET_SYNC_LOADING':
            return { ...state, syncLoading: action.payload };
        case 'SET_HISTORIAL_MODAL_VISIBLE':
            return { ...state, historialModalVisible: action.payload };
        case 'SET_FILTROS_AVANZADOS_VISIBLE':
            return { ...state, filtrosAvanzadosVisible: action.payload };
        case 'SET_VISTA_COMPARACION':
            return { ...state, vistaComparacion: action.payload };
        case 'SET_MOSTRAR_FINALIZADOS':
            return { ...state, mostrarFinalizados: action.payload };
        case 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE':
            return { ...state, modalAnalisisEvolucionVisible: action.payload };
        case 'SET_MODAL_REPORTES_VISIBLE':
            return { ...state, modalReportesVisible: action.payload };
        case 'SET_MODAL_ALERTAS_VISIBLE':
            return { ...state, modalAlertasVisible: action.payload };
        case 'SET_DRAWER_PANEL_CONTROL_VISIBLE':
            return { ...state, drawerPanelControlVisible: action.payload };
        default:
            return state;
    }
}

// ── Cálculos obstétricos puros (nivel de módulo: identidad estable) ──────────
export const calcularFPP = (fum: Dayjs) => {
  // Regla de Naegele: FUM + 280 días estándar
  return fum.add(280, 'day');
};

export const calcularEdadGestacional = (fum: Dayjs) => {
  const hoy = dayjs();
  const diffDias = hoy.diff(fum, 'day');
  const semanas = Math.floor(diffDias / 7);
  const dias = diffDias % 7;
  return { semanas, dias };
};

export const calcularIMC = (peso: number, talla: number) => {
  if (!peso || !talla) return null;
  const tallaMetros = talla / 100; // cm a m
  const imc = peso / (tallaMetros * tallaMetros);

  let clasificacion = '';
  let color = '';

  if (imc < 18.5) { clasificacion = 'Bajo Peso'; color = 'orange'; }
  else if (imc < 25) { clasificacion = 'Peso Normal'; color = 'green'; }
  else if (imc < 30) { clasificacion = 'Sobrepeso'; color = 'orange'; }
  else { clasificacion = 'Obesidad'; color = 'red'; }

  return { valor: imc.toFixed(2), clasificacion, color };
};
