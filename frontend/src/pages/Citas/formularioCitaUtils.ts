import dayjs from 'dayjs';
import { Cita, HorarioDisponible } from '../../services/citasService';

export interface FormularioCitaState {
  loading: boolean;
  loadingHorarios: boolean;
  pacientes: any[];
  medicos: any[];
  consultorios: any[];
  horariosDisponibles: HorarioDisponible[];
  medicoSeleccionado: number | null;
  fechaSeleccionada: dayjs.Dayjs | null;
  horaSeleccionada: dayjs.Dayjs | null;
  modalFichaVisible: boolean;
  citaCreada: Cita | null;
  currentStep: number;
}

export type FormularioCitaAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_LOADING_HORARIOS'; payload: boolean }
  | { type: 'SET_PACIENTES'; payload: any[] }
  | { type: 'SET_MEDICOS'; payload: any[] }
  | { type: 'SET_CONSULTORIOS'; payload: any[] }
  | { type: 'SET_HORARIOS_DISPONIBLES'; payload: HorarioDisponible[] }
  | { type: 'SET_MEDICO_SELECCIONADO'; payload: number | null }
  | { type: 'SET_FECHA_SELECCIONADA'; payload: dayjs.Dayjs | null }
  | { type: 'SET_HORA_SELECCIONADA'; payload: dayjs.Dayjs | null }
  | { type: 'SET_MODAL_FICHA_VISIBLE'; payload: boolean }
  | { type: 'SET_CITA_CREADA'; payload: Cita | null }
  | { type: 'SET_CURRENT_STEP'; payload: number }
  | { type: 'SET_INITIAL_DATA'; payload: { pacientes: any[]; medicos: any[]; consultorios: any[] } };

export const initialState: FormularioCitaState = {
  loading: false,
  loadingHorarios: false,
  pacientes: [],
  medicos: [],
  consultorios: [],
  horariosDisponibles: [],
  medicoSeleccionado: null,
  fechaSeleccionada: null,
  horaSeleccionada: null,
  modalFichaVisible: false,
  citaCreada: null,
  currentStep: 0,
};

export function reducer(state: FormularioCitaState, action: FormularioCitaAction): FormularioCitaState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_LOADING_HORARIOS':
      return { ...state, loadingHorarios: action.payload };
    case 'SET_PACIENTES':
      return { ...state, pacientes: action.payload };
    case 'SET_MEDICOS':
      return { ...state, medicos: action.payload };
    case 'SET_CONSULTORIOS':
      return { ...state, consultorios: action.payload };
    case 'SET_HORARIOS_DISPONIBLES':
      return { ...state, horariosDisponibles: action.payload };
    case 'SET_MEDICO_SELECCIONADO':
      return { ...state, medicoSeleccionado: action.payload };
    case 'SET_FECHA_SELECCIONADA':
      return { ...state, fechaSeleccionada: action.payload };
    case 'SET_HORA_SELECCIONADA':
      return { ...state, horaSeleccionada: action.payload };
    case 'SET_MODAL_FICHA_VISIBLE':
      return { ...state, modalFichaVisible: action.payload };
    case 'SET_CITA_CREADA':
      return { ...state, citaCreada: action.payload };
    case 'SET_CURRENT_STEP':
      return { ...state, currentStep: action.payload };
    case 'SET_INITIAL_DATA':
      return {
        ...state,
        pacientes: action.payload.pacientes,
        medicos: action.payload.medicos,
        consultorios: action.payload.consultorios,
      };
    default:
      return state;
  }
}

export const steps = [
  {
    title: 'Paciente y Médico',
    description: 'Seleccione el paciente y el médico',
  },
  {
    title: 'Fecha y Hora',
    description: 'Programe la cita',
  },
  {
    title: 'Detalles',
    description: 'Complete la información',
  },
];
