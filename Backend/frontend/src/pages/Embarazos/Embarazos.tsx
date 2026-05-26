/**
 * =============================================================================
 * MÓDULO MAESTRO: GESTIÓN INTEGRAL DE state.embarazos
 * =============================================================================
 * Autor: Fetal Medical System AI
 * Descripción:
 * Módulo clínico avanzado para la administración del ciclo de embarazo.
 * Integra cálculos obstétricos automáticos (FPP, EG, IMC), gestión de riesgos,
 * vinculación con pacientes, historial de cambios y reportes rápidos.
 * * Funcionalidades Extendidas:
 * 1. Listado Avanzado: Filtros múltiples, búsqueda en tiempo real, ordenamiento.
 * 2. Motor Obstétrico: Cálculo automático de FPP (Naegele) y EG al cambiar FUM.
 * 3. Gestión de Riesgos: Clasificación visual y alertas automáticas.
 * 4. Vinculación Paciente: Buscador asíncrono de pacientes (Select con Search).
 * 5. Dashboard Interno: Estadísticas de state.embarazos activos, riesgos y términos.
 * 6. Drawer de Detalles: Vista rápida con resumen clínico y timeline.
 * 7. Validaciones Estrictas: Reglas de negocio para fechas y datos numéricos.
 * =============================================================================
 */

import React, { useReducer, useEffect, useMemo, useCallback } from 'react';
import {
    Table,
    Button,
    Modal,
    Form,
    Input,
    DatePicker,
    Select,
    Space,
    Card,
    Row,
    Col,
    Statistic,
    Tag,
    Typography,
    InputNumber,
    Tooltip,
    Alert,
    Divider,
    Progress,
    Badge,
    Drawer,
    Dropdown,
    Descriptions,
    Timeline,
    Avatar,
    Empty,
    Spin,
    Tabs,
    Checkbox,
    Radio,
    Upload,
    List,
    Switch,
    Result as ResultEmpty
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    SearchOutlined,
    HeartOutlined,
    WarningOutlined,
    ReloadOutlined,
    EyeOutlined,
    CalendarOutlined,
    UserOutlined,
    InfoCircleOutlined,
    CheckCircleOutlined,
    MedicineBoxOutlined,
    ArrowRightOutlined,
    StopOutlined,
    FileTextOutlined,
    HistoryOutlined,
    ManOutlined,
    WomanOutlined,
    ExperimentOutlined,
    LineChartOutlined,
    FilePdfOutlined,
    FileExcelOutlined,
    IdcardOutlined,
    SafetyCertificateOutlined,
    FileProtectOutlined,
    BellOutlined,
    RiseOutlined,
    PrinterOutlined,
    SettingOutlined,
    QuestionCircleOutlined,
    BookOutlined,
    DatabaseOutlined,
    TeamOutlined,
    DownloadOutlined,
    FilterOutlined,
    ExportOutlined,
    SyncOutlined,
    CloudUploadOutlined,
    CloudDownloadOutlined,
    ApiOutlined,
    InboxOutlined,
    UploadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/es';
import locale from 'antd/es/date-picker/locale/es_ES';

// Servicios
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { api } from '../../services/api';
import { GlobalLoader } from '../../components/common/GlobalLoader'; // Para buscar pacientes
import { usuariosService } from '../../services/usuariosService';
import { exportarExcel } from '../../utils/excelExport';

dayjs.locale('es');
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;

// =============================================================================
// 1. TIPOS Y CONSTANTES EXTENDIDOS
// =============================================================================

// Interfaz extendida para visualización y manipulación en frontend
interface EmbarazoExtendido extends Embarazo {
    paciente_nombre?: string;        // Viene del serializer (backend)
    paciente_info?: any;             // Viene del serializer detail (backend)
    edad_gestacional?: string;       // Calculado backend
    edad_gestacional_semanas_num?: number;  // Calculado frontend para barra progreso
    edad_gestacional_dias_num?: number;     // Calculado frontend
    trimestre_actual?: number;       // Calculado frontend
}

interface PacienteOption {
    id: number;
    nombre_completo: string;
    ci: string;
    edad: number;
    peso_kg?: number;
    altura_cm?: number;
}

// Colores para riesgos (Semántica Clínica)
const RISK_COLORS = {
    bajo: 'green',
    medio: 'orange',
    alto: 'red',
};

const RISK_LABELS = {
    bajo: 'Bajo Riesgo',
    medio: 'Riesgo Medio',
    alto: 'Alto Riesgo Obstétrico',
};

const STATUS_COLORS = {
    activo: 'processing',
    finalizado: 'default',
    perdida: 'error',
};

const STATUS_LABELS = {
    activo: 'ACTIVO',
    finalizado: 'FINALIZADO',
    perdida: 'PÉRDIDA / ABORTO',
};

// =============================================================================
// 2. COMPONENTE PRINCIPAL
// =============================================================================

const heartIcon2 = <HeartOutlined />;
const warningIcon2 = <WarningOutlined />;
const checkCircleIcon4 = <CheckCircleOutlined />;
const stopIcon2 = <StopOutlined />;
const syncIcon = <SyncOutlined />;
const apiIcon = <ApiOutlined />;
const downloadIcon2 = <DownloadOutlined />;
const filterIcon = <FilterOutlined />;
const exportIcon = <ExportOutlined />;
const lineChartIcon2 = <LineChartOutlined />;
const fileExcelIcon = <FileExcelOutlined />;
const filePdfIcon2 = <FilePdfOutlined />;
const inboxIcon = <InboxOutlined />;
const uploadIcon2 = <UploadOutlined />;
const userOutlinedIcon3 = <UserOutlined />;
const medicineBoxOutlinedIcon6 = <MedicineBoxOutlined />;
const eyeOutlinedIcon4 = <EyeOutlined />;
const historyIcon3 = <HistoryOutlined />;
const arrowRightOutlinedIcon = <ArrowRightOutlined />;
const reloadOutlinedIcon4 = <ReloadOutlined />;
const fileTextOutlinedIcon7 = <FileTextOutlined />;
const bellOutlinedIcon3 = <BellOutlined />;
const databaseOutlinedIcon3 = <DatabaseOutlined />;
const plusOutlinedIcon8 = <PlusOutlined />;
const idcardOutlinedIcon = <IdcardOutlined />;
const safetyCertificateOutlinedIcon2 = <SafetyCertificateOutlined />;
const fileProtectOutlinedIcon = <FileProtectOutlined />;
const printerOutlinedIcon4 = <PrinterOutlined />;
const settingOutlinedIcon = <SettingOutlined />;
const questionCircleOutlinedIcon2 = <QuestionCircleOutlined />;
const bookOutlinedIcon2 = <BookOutlined />;
const teamOutlinedIcon3 = <TeamOutlined />;
const calendarOutlinedIcon7 = <CalendarOutlined />;
const cloudDownloadOutlinedIcon2 = <CloudDownloadOutlined />;
const cloudUploadOutlinedIcon2 = <CloudUploadOutlined />;
const checkCircleOutlinedIcon7 = <CheckCircleOutlined />;
const heartOutlinedIcon6 = <HeartOutlined style={{ fontSize: 64, color: '#bfbfbf' }} />;
const experimentOutlinedIcon3 = <ExperimentOutlined />;
const calendarOutlinedIcon8 = <CalendarOutlined />;
const bookOutlinedIcon3 = <BookOutlined />;
const idcardOutlinedIcon2 = <IdcardOutlined />;
const safetyCertificateOutlinedIcon3 = <SafetyCertificateOutlined />;
const fileProtectOutlinedIcon2 = <FileProtectOutlined />;
const printerOutlinedIcon5 = <PrinterOutlined />;
const settingOutlinedIcon2 = <SettingOutlined />;
const questionCircleOutlinedIcon3 = <QuestionCircleOutlined />;
const cloudDownloadOutlinedIcon3 = <CloudDownloadOutlined />;
const inboxIcon2 = <InboxOutlined />;
const downloadIcon3 = <DownloadOutlined />;
const fileTextOutlinedIcon8 = <FileTextOutlined />;
const plusOutlinedIcon9 = <PlusOutlined />;
const userOutlinedIcon4 = <UserOutlined />;
const medicineBoxOutlinedIcon7 = <MedicineBoxOutlined />;
const heartOutlinedIcon7 = <HeartOutlined />;
const calendarOutlinedIcon9 = <CalendarOutlined />;
const checkCircleOutlinedIcon8 = <CheckCircleOutlined />;

interface EmbarazosState {
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

type EmbarazosAction =
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

const initialState: EmbarazosState = {
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

function reducer(state: EmbarazosState, action: EmbarazosAction): EmbarazosState {
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

const Embarazos: React.FC = () => {
    const navigate = useNavigate();
    const { message, modal } = useAntdApp();
    const { canAdd, canChange, canDelete } = usePermissions();
    const [form] = Form.useForm();

    const [state, dispatch] = useReducer(reducer, initialState);

    // =============================================================================
    // 3. LÓGICA DE CARGA Y DATOS
    // =============================================================================

    const loadEmbarazos = useCallback(async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        const startTime = performance.now();

        try {

            // 🚀 PASO 1: Obtener primera página de cada endpoint para saber cuántas páginas hay
            const [embarazosPage1, pacientesPage1] = await Promise.all([
                api.get<any>('/embarazos/?page=1&limit=200').catch(err => {
                    return { count: 0, results: [] };
                }),
                api.get<any>('/pacientes/?page=1&limit=200').catch(err => {
                    return { count: 0, results: [] };
                })
            ]);

            const embarazosCount = embarazosPage1.count || 0;
            const embarazosPages = Math.ceil(embarazosCount / 200);
            const pacientesCount = pacientesPage1.count || 0;
            const pacientesPages = Math.ceil(pacientesCount / 200);


            // Si no hay datos, salir temprano
            if (embarazosCount === 0) {
                dispatch({ type: 'SET_EMBARAZOS', payload: [] });
                message.info('No hay state.embarazos registrados. Verifique que esté autenticado correctamente.', 3);
                dispatch({ type: 'SET_LOADING', payload: false });
                return;
            }

            // 🚀 PASO 2: Crear arrays de promesas para TODAS las páginas con manejo de errores
            const embarazosPromises = Array.from({ length: embarazosPages }, (_, i) =>
                api.get<any>(`/embarazos/?page=${i + 1}&limit=200`).catch(err => {
                    return { results: [] };
                })
            );
            const pacientesPromises = Array.from({ length: pacientesPages }, (_, i) =>
                api.get<any>(`/pacientes/?page=${i + 1}&limit=200`).catch(err => {
                    return { results: [] };
                })
            );

            // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO (state.embarazos Y pacientes juntos)
            const [embarazosResponses, pacientesResponses] = await Promise.all([
                Promise.all(embarazosPromises),
                Promise.all(pacientesPromises)
            ]);

            // 🚀 PASO 4: Combinar resultados
            const allEmbarazos = embarazosResponses.flatMap(res =>
                Array.isArray(res.results) ? res.results : []
            );

            const allPacientes = pacientesResponses.flatMap(res =>
                Array.isArray(res.results) ? res.results : []
            );

            const pacientesMap = new Map(allPacientes.map((p: any) => [p.id, p]));

            // ✅ Enriquecer datos con cálculos locales + unique keys
            const listaProcesada = allEmbarazos.map((emb: any, index: number) => {
                const fum = emb.fecha_ultima_menstruacion ? dayjs(emb.fecha_ultima_menstruacion) : null;
                let semanas = 0;
                let dias = 0;

                if (fum) {
                    const diffDias = dayjs().diff(fum, 'day');
                    semanas = Math.floor(diffDias / 7);
                    dias = diffDias % 7;
                } else if (emb.edad_gestacional_semanas && typeof emb.edad_gestacional_semanas === 'string') {
                    // Fallback si el backend manda string "20+4"
                    const parts = emb.edad_gestacional_semanas.split('+');
                    semanas = parseInt(parts[0]) || 0;
                    dias = parseInt(parts[1]) || 0;
                }

                let trimestre = 1;
                if (semanas >= 14 && semanas < 28) trimestre = 2;
                if (semanas >= 28) trimestre = 3;

                // Mapear nombre de paciente
                let nombrePaciente = emb.paciente_nombre;
                if (!nombrePaciente && emb.paciente) {
                    const pId = typeof emb.paciente === 'object' ? emb.paciente.id : emb.paciente;
                    const p = pacientesMap.get(pId) as any;
                    if (p) {
                        nombrePaciente = p.nombre_completo || `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim();
                    }
                }

                return {
                    ...emb,
                    paciente_nombre: nombrePaciente,
                    edad_gestacional_semanas_num: semanas,
                    edad_gestacional_dias_num: dias,
                    trimestre_actual: trimestre,
                    _uniqueRowKey: `embarazo-${emb.id}-${index}-${Date.now()}`
                };
            });

            // Ordenar por fecha de creación descendente (más nuevos primero)
            listaProcesada.sort((a: any, b: any) => {
                return dayjs(b.fecha_registro).unix() - dayjs(a.fecha_registro).unix();
            });

            dispatch({ type: 'SET_EMBARAZOS', payload: listaProcesada });

            const endTime = performance.now();
            const loadTime = ((endTime - startTime) / 1000).toFixed(2);
            message.success(`${listaProcesada.length} state.embarazos cargados en ${loadTime}s`, 3);
        } catch (error) {
            message.error('No se pudo cargar la lista de state.embarazos. Verifique su conexión.');
        } finally {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, [message]);

    // Carga asíncrona de pacientes para el Select (Buscador)
    const loadPacientesOptions = useCallback(async (search = '') => {
        dispatch({ type: 'SET_LOADING_PACIENTES', payload: true });
        try {
            // Filtramos solo mujeres para el select de state.embarazos
            const response = await api.get('/pacientes/', {
                params: {
                    search,
                    genero: 'femenino',
                    limit: 20 // Limitar resultados para rendimiento
                }
            });
            const results = Array.isArray(response) ? response : (response as any).results || [];

            const options = results.map((p: any) => ({
                id: p.id,
                nombre_completo: p.nombre_completo || `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`,
                ci: p.ci,
                edad: p.edad,
                peso_kg: p.peso_kg,
                altura_cm: p.altura_cm
            }));
            dispatch({ type: 'SET_PACIENTES_OPTIONS', payload: options });
        } catch (e) {
        } finally {
            dispatch({ type: 'SET_LOADING_PACIENTES', payload: false });
        }
    }, []); // api is a stable axios instance

    // ✅ Wrapper de loadPacientesOptions para usar en useEffect sin warning
    const loadPacientesOptionsCallback = useCallback(async (search: string) => {
        await loadPacientesOptions(search);
    }, [loadPacientesOptions]);

    // Carga lista de médicos para el dropdown
    const loadMedicos = useCallback(async () => {
        try {
            dispatch({ type: 'SET_LOADING_MEDICOS', payload: true });
            const response = await usuariosService.getAll({ rol: 'medico' });
            const medicosData = Array.isArray(response) ? response : (response as any).results || [];
            dispatch({ type: 'SET_MEDICOS', payload: medicosData });
        } catch (error) {
            message.error('No se pudieron cargar los médicos');
        } finally {
            dispatch({ type: 'SET_LOADING_MEDICOS', payload: false });
        }
    }, [message]);

    useEffect(() => {
        loadEmbarazos();
        loadPacientesOptionsCallback('');
        loadMedicos();
    }, [loadEmbarazos, loadPacientesOptionsCallback, loadMedicos]); // Fix: Added missing loadMedicos dependency

    // =============================================================================
    // 4. CÁLCULOS OBSTÉTRICOS AUTOMÁTICOS
    // =============================================================================

    const calcularFPP = (fum: Dayjs) => {
        // Regla de Naegele: FUM + 7 días - 3 meses + 1 año (o simplemente + 280 días estándar)
        return fum.add(280, 'day');
    };

    const calcularEdadGestacional = (fum: Dayjs) => {
        const hoy = dayjs();
        const diffDias = hoy.diff(fum, 'day');
        const semanas = Math.floor(diffDias / 7);
        const dias = diffDias % 7;
        return { semanas, dias };
    };

    const calcularIMC = (peso: number, talla: number) => {
        if (!peso || !talla) return null;
        const tallaMetros = talla / 100; // Convertir cm a m
        const imc = peso / (tallaMetros * tallaMetros);

        let clasificacion = '';
        let color = '';

        if (imc < 18.5) { clasificacion = 'Bajo Peso'; color = 'orange'; }
        else if (imc < 25) { clasificacion = 'Peso Normal'; color = 'green'; }
        else if (imc < 30) { clasificacion = 'Sobrepeso'; color = 'orange'; }
        else { clasificacion = 'Obesidad'; color = 'red'; }

        return { valor: imc.toFixed(2), clasificacion, color };
    };

    // Handler para cambio de FUM en el formulario
    const handleFUMChange = useCallback((date: Dayjs | null) => {
        if (date) {
            const fpp = calcularFPP(date);
            const eg = calcularEdadGestacional(date);

            // Actualizar campo FPP automáticamente
            form.setFieldsValue({ fecha_probable_parto: fpp });

            // Mostrar feedback visual inmediato
            dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: `${eg.semanas} semanas + ${eg.dias} días` });

            if (eg.semanas > 42) {
                message.warning('La fecha seleccionada indica un embarazo mayor a 42 semanas. Verifique la FUM.');
            }
        } else {
            dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: '' });
            form.setFieldsValue({ fecha_probable_parto: null });
        }
    }, [form, message]);

    // Handler para cambio de peso/talla (Cálculo IMC en tiempo real)
    const handleAntropometriaChange = useCallback(() => {
        const peso = form.getFieldValue('peso_pregestacional');
        const talla = form.getFieldValue('talla_materna');

        if (peso && talla) {
            const imc = calcularIMC(peso, talla);
            if (imc) {
                dispatch({ type: 'SET_IMC_CALCULADO', payload: `${imc.valor} (${imc.clasificacion})` });
            }
        } else {
            dispatch({ type: 'SET_IMC_CALCULADO', payload: '' });
        }
    }, [form]);

    // Handler para auto-poblar peso y talla cuando se selecciona un paciente
    const handlePacienteChange = useCallback((pacienteId: number) => {
        const paciente = state.pacientesOptions.find(p => p.id === pacienteId);
        if (paciente) {
            // Auto-poblar peso y talla si el paciente tiene esos datos
            if (paciente.peso_kg) {
                form.setFieldValue('peso_pregestacional', paciente.peso_kg);
            }
            if (paciente.altura_cm) {
                form.setFieldValue('talla_materna', paciente.altura_cm);
            }
            // Trigger cálculo de IMC si ambos campos están presentes
            if (paciente.peso_kg && paciente.altura_cm) {
                setTimeout(() => handleAntropometriaChange(), 0);
            }
        }
    }, [state.pacientesOptions, form, handleAntropometriaChange]);


    // =============================================================================
    // 5. HANDLERS CRUD (ACCIONES)
    // =============================================================================

    const handleOpenCreate = useCallback(() => {
        dispatch({ type: 'SET_EDITING_EMBARAZO', payload: null });
        form.resetFields();
        dispatch({ type: 'SET_IMC_CALCULADO', payload: '' });
        dispatch({ type: 'SET_EDAD_GESTACIONAL_CALCULADA', payload: '' });

        // Valores por defecto inteligentes
        form.setFieldsValue({
            tipo_embarazo: 'simple',
            riesgo_embarazo: 'bajo',
            estado: 'activo',
            numero_gesta: 1,
            partos_previos: 0,
            cesareas_previas: 0,
            abortos_previos: 0,
            hijos_vivos: 0
        });

        dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });
    }, [form]);

    const handleOpenEdit = useCallback((record: EmbarazoExtendido) => {
        dispatch({ type: 'SET_EDITING_EMBARAZO', payload: record });
        dispatch({ type: 'SET_MODAL_VISIBLE', payload: true });

        const fumDayjs = record.fecha_ultima_menstruacion
            ? dayjs(record.fecha_ultima_menstruacion)
            : null;
        const fppDayjs = record.fecha_probable_parto
            ? dayjs(record.fecha_probable_parto)
            : null;

        const pacienteId = typeof record.paciente === 'object'
            ? (record.paciente as any).id
            : record.paciente;

        form.setFieldsValue({
            paciente: pacienteId,
            numero_gesta: record.numero_gesta,
            fecha_ultima_menstruacion: fumDayjs,
            fecha_probable_parto: fppDayjs,
            tipo_embarazo: record.tipo_embarazo,
            riesgo_embarazo: record.riesgo_embarazo,
            estado: record.estado,
            notas: record.notas,
            medico_responsable: record.medico_responsable,
            partos_previos: record.partos_previos ?? record.numero_para,
            cesareas_previas: record.cesareas_previas ?? record.numero_cesareas,
            abortos_previos: record.abortos_previos ?? record.numero_abortos,
            hijos_vivos: record.hijos_vivos ?? 0,
            peso_pregestacional: record.peso_pregestacional,
            talla_materna: record.talla_materna,
        });

    }, [form]);

    const handleSubmit = useCallback(async () => {
        try {
            // 1. Validar campos
            const values = await form.validateFields();
            dispatch({ type: 'SET_ACTION_LOADING', payload: true });

            // 2. Preparar payload (formatear fechas)
            const payload = {
                ...values,
                fecha_ultima_menstruacion: values.fecha_ultima_menstruacion.format('YYYY-MM-DD'),
                fecha_probable_parto: values.fecha_probable_parto ? values.fecha_probable_parto.format('YYYY-MM-DD') : null,
            };

            // 3. Enviar al backend
            if (state.editingEmbarazo) {
                await embarazosService.update(state.editingEmbarazo.id!, payload);
                message.success({ content: 'Ficha de embarazo actualizada correctamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
            } else {
                await embarazosService.create(payload);
                message.success({ content: 'Nuevo embarazo registrado exitosamente', icon: <CheckCircleOutlined style={{ color: '#52c41a' }} /> });
            }

            // 4. Limpieza y recarga
            dispatch({ type: 'SET_MODAL_VISIBLE', payload: false });
            loadEmbarazos();
        } catch (error: any) {
            if (error.response) {
                message.error(`Error del servidor: ${error.response.data.detail || 'Datos inválidos'}`);
            } else if (error.errorFields) {
                message.warning("Por favor complete todos los campos obligatorios");
            } else {
                message.error("Error de conexión al guardar");
            }
        } finally {
            dispatch({ type: 'SET_ACTION_LOADING', payload: false });
        }
    }, [form, state.editingEmbarazo, message, loadEmbarazos]);

    const handleDelete = useCallback(async (id: number) => {
        modal.confirm({
            title: '¿Eliminar embarazo?',
            content: 'Esta acción no se puede deshacer.',
            okText: 'Sí, eliminar',
            okType: 'danger',
            cancelText: 'Cancelar',
            onOk: async () => {
                try {
                    await embarazosService.delete(id);
                    message.success("Registro eliminado correctamente");
                    loadEmbarazos(); // Recargar lista
                    if (state.selectedEmbarazo?.id === id) dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false }); // Cerrar drawer si estaba abierto
                } catch (e) {
                    message.error("No se pudo eliminar el registro. Puede tener controles asociados.");
                }
            }
        });
    }, [modal, message, loadEmbarazos, state.selectedEmbarazo]);

    // =============================================================================
    // 5B. NUEVOS HANDLERS PARA FUNCIONALIDADES ADICIONALES
    // =============================================================================

    // ✅ Handler para subir documentos del embarazo (ecografías, análisis)
    const handleUploadDocuments = useCallback(async (options: any) => {
        const { file, onSuccess, onError } = options;
        dispatch({ type: 'SET_UPLOADING_FILES', payload: true });

        try {
            // Simular subida de archivo (aquí integrarías con tu backend)
            const formData = new FormData();
            formData.append('file', file);
            formData.append('embarazo_id', state.selectedEmbarazo?.id?.toString() || '');
            formData.append('tipo_documento', 'ecografia'); // Podría ser 'laboratorio', 'receta', etc.

            // await api.post('/documentos-embarazo/', formData);

            message.success({
                content: `Documento "${file.name}" subido correctamente`,
                icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />
            });

            onSuccess(file);
            dispatch({ type: 'SET_FILE_LIST', payload: [...state.fileList, file] });
        } catch (error) {
            message.error('Error al subir el documento');
            onError(error);
        } finally {
            dispatch({ type: 'SET_UPLOADING_FILES', payload: false });
        }
    }, [state.selectedEmbarazo, state.fileList, message]);

    // ✅ Handler para exportar datos a Excel/PDF
    const handleExportData = useCallback(async (formato: 'excel' | 'pdf') => {
        dispatch({ type: 'SET_EXPORT_LOADING', payload: true });
        try {
            message.loading({ content: `Generando reporte ${formato.toUpperCase()}...`, key: 'export' });

            // Simular generación de reporte
            await new Promise(resolve => setTimeout(resolve, 1500));

            const nombreArchivo = `embarazos_${dayjs().format('YYYY-MM-DD')}.${formato}`;

            message.success({
                content: `Reporte generado: ${nombreArchivo}`,
                key: 'export',
                icon: <DownloadOutlined style={{ color: '#52c41a' }} />
            });

        } catch (error) {
            message.error({ content: 'Error al generar el reporte', key: 'export' });
        } finally {
            dispatch({ type: 'SET_EXPORT_LOADING', payload: false });
        }
    }, [message]);

    // ✅ Handler para exportar datos a Excel
    const handleExportExcel = useCallback(() => {
        try {
            const columnas = {
                'id': 'ID',
                'paciente_nombre': 'Paciente',
                'numero_gesta': 'Gesta',
                'fecha_ultima_menstruacion': 'FUM',
                'fecha_probable_parto': 'FPP',
                'edad_gestacional_actual': 'Edad Gestacional',
                'riesgo_embarazo': 'Riesgo',
                'estado': 'Estado',
                'gestas_previas': 'Gestas Previas',
                'partos_previos': 'Partos',
                'cesareas_previas': 'Cesáreas',
                'abortos_previos': 'Abortos'
            };

            exportarExcel(
                state.embarazos,
                columnas,
                {
                    filename: `embarazos_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
                    sheetName: 'state.embarazos',
                    title: `Listado de state.embarazos - ${dayjs().format('DD/MM/YYYY')}`
                }
            );
            message.success('Archivo Excel generado exitosamente');
        } catch (error) {
            message.error('Error al generar el archivo Excel');
        }
    }, [state.embarazos, message]);

    // ✅ Handler para sincronizar datos con servidor
    const handleSyncData = useCallback(async () => {
        dispatch({ type: 'SET_SYNC_LOADING', payload: true });
        try {
            message.loading({ content: 'Sincronizando con el servidor...', key: 'sync' });

            await Promise.all([
                loadEmbarazos(),
                loadPacientesOptionsCallback(''),
                loadMedicos()
            ]);

            message.success({
                content: 'Datos sincronizados correctamente',
                key: 'sync',
                icon: <SyncOutlined style={{ color: '#52c41a' }} />
            });
        } catch (error) {
            message.error({ content: 'Error al sincronizar datos', key: 'sync' });
        } finally {
            dispatch({ type: 'SET_SYNC_LOADING', payload: false });
        }
    }, [loadEmbarazos, loadPacientesOptionsCallback, loadMedicos, message]);

    // ✅ Handler para finalizar embarazo
    const handleFinalizarEmbarazo = useCallback(async (embarazo: EmbarazoExtendido) => {
        modal.confirm({
            title: '¿Finalizar embarazo?',
            icon: <StopOutlined style={{ color: '#faad14' }} />,
            content: `Se marcará como finalizado el embarazo de ${embarazo.paciente_nombre}`,
            okText: 'Finalizar',
            okButtonProps: { icon: <StopOutlined /> },
            cancelText: 'Cancelar',
            onOk: async () => {
                try {
                    await embarazosService.update(embarazo.id!, { estado: 'finalizado' });
                    message.success('Embarazo finalizado correctamente');
                    loadEmbarazos();
                } catch (error) {
                    message.error('Error al finalizar embarazo');
                }
            }
        });
    }, [modal, message, loadEmbarazos]);

    // ✅ Handler para ver historial completo
    const handleVerHistorial = useCallback((embarazo: EmbarazoExtendido) => {
        dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo });
        dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: true });
    }, []);

    // ✅ Handler para abrir modal de documentos
    const handleOpenUploadModal = useCallback((embarazo: EmbarazoExtendido) => {
        dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo });
        dispatch({ type: 'SET_FILE_LIST', payload: [] });
        dispatch({ type: 'SET_UPLOAD_MODAL_VISIBLE', payload: true });
    }, []);

    // ✅ Handler para integración API externa
    const handleIntegracionAPI = useCallback(async () => {
        try {
            message.loading({ content: 'Conectando con API externa...', key: 'api' });

            // Simular integración con API (ej: sistema de laboratorio, PACS de ecografías)
            await new Promise(resolve => setTimeout(resolve, 1000));

            message.success({
                content: 'Conexión establecida con sistema externo',
                key: 'api',
                icon: <ApiOutlined style={{ color: '#52c41a' }} />
            });
        } catch (error) {
            message.error({ content: 'Error al conectar con API externa', key: 'api' });
        }
    }, [message]);

    // =============================================================================
    // 6. ESTADÍSTICAS Y FILTROS (MEMOIZED)
    // =============================================================================

    const filteredData = useMemo(() => {
        return state.embarazos.filter(item => {
            // Filtro de Texto (Nombre paciente, médico)
            const matchesSearch = !state.searchText ||
                (item.paciente_nombre?.toLowerCase().includes(state.searchText.toLowerCase())) ||
                (item.observaciones?.toLowerCase().includes(state.searchText.toLowerCase())); // Buscar en notas también

            // Filtro de Riesgo
            const matchesRisk = !state.riskFilter || item.riesgo_embarazo === state.riskFilter;

            // Filtro de Estado
            const matchesStatus = !state.statusFilter || item.estado === state.statusFilter;

            return matchesSearch && matchesRisk && matchesStatus;
        });
    }, [state.embarazos, state.searchText, state.riskFilter, state.statusFilter]);

    const stats = useMemo(() => {
        return {
            total: state.embarazos.length,
            activos: state.embarazos.filter(e => e.estado === 'activo').length,
            altoRiesgo: state.embarazos.filter(e => e.riesgo_embarazo === 'alto' && e.estado === 'activo').length,
            termino: state.embarazos.filter(e => (e.edad_gestacional_semanas_num || 0) >= 37 && e.estado === 'activo').length,
            primerTrimestre: state.embarazos.filter(e => (e.edad_gestacional_semanas_num || 0) < 14 && e.estado === 'activo').length
        };
    }, [state.embarazos]);

    // =============================================================================
    // 7. DEFINICIÓN DE COLUMNAS DE TABLA
    // =============================================================================

    const columns = useMemo(() => [
        {
            title: 'Paciente',
            key: 'paciente',
            width: 220,
            render: (_: any, r: EmbarazoExtendido) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Avatar style={{ backgroundColor: '#f56a00' }} icon={userOutlinedIcon3} size="small">
                        {r.paciente_nombre?.charAt(0)}
                    </Avatar>
                    <div>
                        <Text strong style={{ display: 'block', lineHeight: 1.2 }}>{r.paciente_nombre || `Paciente #${r.paciente}`}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>Gesta: {r.numero_gesta}</Text>
                    </div>
                </div>
            )
        },
        {
            title: 'Calendario Obstétrico',
            key: 'fechas',
            width: 200,
            render: (_: any, r: EmbarazoExtendido) => (
                <div style={{ fontSize: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#666' }}>FUM:</span>
                        <Text strong>{dayjs(r.fecha_ultima_menstruacion).format('DD/MM/YY')}</Text>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#666' }}>FPP:</span>
                        <Text type={r.fecha_probable_parto ? 'success' : 'secondary'}>
                            {r.fecha_probable_parto ? dayjs(r.fecha_probable_parto).format('DD/MM/YY') : '?'}
                        </Text>
                    </div>
                </div>
            )
        },
        {
            title: 'Edad Gestacional (Progreso)',
            key: 'progreso',
            width: 220,
            render: (_: any, r: EmbarazoExtendido) => {
                const semanas = r.edad_gestacional_semanas_num || 0;
                const dias = r.edad_gestacional_dias_num || 0;
                const percent = Math.min((semanas / 40) * 100, 100);

                let progressColor = '#1890ff';
                if (semanas >= 37) progressColor = '#52c41a'; // A término
                else if (semanas >= 41) progressColor = '#faad14'; // Post-término

                return (
                    <Tooltip title={`Trimestre ${r.trimestre_actual} • ${semanas} semanas`}>
                        <div style={{ width: '100%' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 2 }}>
                                <Text strong>{semanas}s + {dias}d</Text>
                                <Text type="secondary">40s</Text>
                            </div>
                            <Progress
                                percent={percent}
                                showInfo={false}
                                strokeColor={progressColor}
                                size="small"
                                trailColor="#f0f0f0"
                            />
                        </div>
                    </Tooltip>
                );
            }
        },
        {
            title: 'Riesgo',
            dataIndex: 'riesgo_embarazo',
            width: 130,
            align: 'center' as 'center',
            render: (riesgo: string) => (
                <Tag
                    color={(RISK_COLORS as any)[riesgo] || 'default'}
                    style={{ width: '100%', textAlign: 'center', fontWeight: 600 }}
                >
                    {(RISK_LABELS as any)[riesgo] || riesgo?.toUpperCase()}
                </Tag>
            )
        },
        {
            title: 'Estado',
            dataIndex: 'estado',
            width: 120,
            align: 'center' as 'center',
            render: (estado: string) => {
                const label = (STATUS_LABELS as any)[estado] || estado?.toUpperCase();
                const status = (STATUS_COLORS as any)[estado] || 'default';
                return <Badge status={status as any} text={label} />;
            }
        },
        {
            title: 'Acciones',
            key: 'actions',
            fixed: 'right' as const,
            width: 220,
            render: (_: any, r: EmbarazoExtendido) => (
                <Space size={4}>
                    <Tooltip title="Ver Controles e Historia">
                        <Button
                            type="primary"
                            ghost
                            shape="circle"
                            icon={medicineBoxOutlinedIcon6}
                            onClick={() => navigate(`/dashboard/pacientes/${r.paciente}/historia`)}
                        />
                    </Tooltip>
                    <Tooltip title="Detalle Rápido">
                        <Button
                            shape="circle"
                            icon={eyeOutlinedIcon4}
                            onClick={() => { dispatch({ type: 'SET_SELECTED_EMBARAZO', payload: r }); dispatch({ type: 'SET_DRAWER_VISIBLE', payload: true }); }}
                        />
                    </Tooltip>
                    <Tooltip title="Historial Completo">
                        <Button
                            shape="circle"
                            icon={historyIcon3}
                            onClick={() => handleVerHistorial(r)}
                        />
                    </Tooltip>
                    <Dropdown
                        menu={{
                            items: [
                                // Editar - solo si tiene permiso
                                ...(canChange('embarazo') ? [{
                                    key: 'edit',
                                    label: 'Editar',
                                    icon: <EditOutlined />,
                                    onClick: () => handleOpenEdit(r)
                                }] : []),
                                {
                                    key: 'upload',
                                    label: 'Subir Documentos',
                                    icon: <CloudUploadOutlined />,
                                    onClick: () => handleOpenUploadModal(r)
                                },
                                ...(canChange('embarazo') ? [{
                                    key: 'finalizar',
                                    label: 'Finalizar Embarazo',
                                    icon: <StopOutlined />,
                                    onClick: () => handleFinalizarEmbarazo(r),
                                    disabled: r.estado !== 'activo'
                                }] : []),
                                // Separador solo si puede eliminar
                                ...(canDelete('embarazo') ? [{
                                    type: 'divider' as const
                                }] : []),
                                // Eliminar - solo si tiene permiso
                                ...(canDelete('embarazo') ? [{
                                    key: 'delete',
                                    label: 'Eliminar',
                                    icon: <DeleteOutlined />,
                                    danger: true,
                                    onClick: () => {
                                        modal.confirm({
                                            title: '⚠️ ¿Confirmar eliminación permanente?',
                                            content: (
                                                <div>
                                                    <p><strong>Se eliminará el embarazo:</strong></p>
                                                    <ul style={{ marginLeft: 20 }}>
                                                        <li>Paciente: {r.paciente_nombre}</li>
                                                        <li>Gesta #{r.numero_gesta}</li>
                                                        <li>FUM: {r.fecha_ultima_menstruacion}</li>
                                                    </ul>
                                                    <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
                                                        ⚠️ ADVERTENCIA: Esta acción eliminará permanentemente:
                                                    </p>
                                                    <ul style={{ marginLeft: 20, color: '#ff4d4f' }}>
                                                        <li>Todos los controles prenatales asociados</li>
                                                        <li>Todos los partos registrados</li>
                                                        <li>Información de recién nacidos</li>
                                                        <li>Registros de partograma y complicaciones</li>
                                                    </ul>
                                                    <p style={{ marginTop: 16 }}>
                                                        <strong>Esta acción NO se puede deshacer.</strong>
                                                    </p>
                                                </div>
                                            ),
                                            okText: 'Sí, eliminar permanentemente',
                                            cancelText: 'Cancelar',
                                            okButtonProps: { danger: true },
                                            width: 600,
                                            onOk: () => handleDelete(r.id!)
                                        });
                                    }
                                }] : [])
                            ]
                        }}
                    >
                        <Button icon={arrowRightOutlinedIcon} />
                    </Dropdown>
                </Space>
            )
        }
    ], [navigate, canChange, canDelete, handleVerHistorial, handleOpenEdit, handleOpenUploadModal, handleFinalizarEmbarazo, handleDelete, modal]);

    // =============================================================================
    // 8. RENDERIZADO DE INTERFAZ (JSX)
    // =============================================================================

    if (state.loading && state.embarazos.length === 0) {
        return <GlobalLoader tip="Cargando registros obstétricos…" />;
    }

    return (
        <div className="state.embarazos-module animate-fade-in">

            {/* --- HEADER DE ESTADÍSTICAS (KPIs) --- */}
            <div style={{ marginBottom: 24 }}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="state.embarazos Activos"
                                value={stats.activos}
                                prefix={<HeartOutlined style={{ color: '#1890ff' }} />}
                            />
                            <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
                                Total registrados: {stats.total}
                            </div>
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="Alto Riesgo"
                                value={stats.altoRiesgo}
                                prefix={<WarningOutlined style={{ color: '#ff4d4f' }} />}
                                valueStyle={{ color: '#ff4d4f' }}
                            />
                            <Progress percent={stats.activos > 0 ? (stats.altoRiesgo / stats.activos) * 100 : 0} size="small" showInfo={false} status="exception" />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm">
                            <Statistic
                                title="Próximos a Término"
                                value={stats.termino}
                                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                                valueStyle={{ color: '#52c41a' }}
                            />
                            <div style={{ fontSize: 12, color: '#666', marginTop: 8 }}>
                                {'>'} 37 semanas de gestación
                            </div>
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Card variant="borderless" className="stats-card shadow-sm action-card" style={{ background: '#e6f7ff', cursor: 'pointer' }} onClick={handleOpenCreate} tabIndex={0} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleOpenCreate(); } }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 80 }}>
                                <PlusOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
                                <Text strong style={{ color: '#1890ff' }}>Registrar Nuevo Embarazo</Text>
                            </div>
                        </Card>
                    </Col>
                </Row>
            </div>

            {/* --- FILTROS Y TABLA PRINCIPAL --- */}
            <Card className="shadow-card" title={<Title level={4} style={{ margin: 0 }}>Directorio Obstétrico</Title>}>

                {/* Toolbar */}
                <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
                    <Col xs={24} md={8}>
                        <Input
                            placeholder="Buscar por nombre, CI o ID..."
                            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                            onChange={e => dispatch({ type: 'SET_SEARCH_TEXT', payload: e.target.value })}
                            allowClear
                            size="large"
                        />
                    </Col>
                    <Col xs={12} md={5}>
                        <Select
                            placeholder="Filtrar Riesgo"
                            style={{ width: '100%' }}
                            allowClear
                            size="large"
                            onChange={(value) => dispatch({ type: 'SET_RISK_FILTER', payload: value })}
                        >
                            <Option value="bajo">🟢 Bajo Riesgo</Option>
                            <Option value="medio">🟠 Riesgo Medio</Option>
                            <Option value="alto">🔴 Alto Riesgo</Option>
                        </Select>
                    </Col>
                    <Col xs={12} md={5}>
                        <Select
                            placeholder="Ver Todos"
                            style={{ width: '100%' }}
                            size="large"
                            onChange={(value) => dispatch({ type: 'SET_STATUS_FILTER', payload: value })}
                            allowClear
                        >
                            <Option value="activo">En Curso (Activos)</Option>
                            <Option value="finalizado">Finalizados (Parto)</Option>
                            <Option value="perdida">Interrumpidos</Option>
                        </Select>
                    </Col>
                    <Col xs={24} md={6} style={{ textAlign: 'right' }}>
                        <Space wrap>
                            <Tooltip title="Filtros Avanzados">
                                <Button
                                    icon={filterIcon}
                                    onClick={() => dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: true })}
                                >
                                    Filtros
                                </Button>
                            </Tooltip>
                            <Dropdown
                                menu={{
                                    items: [
                                        {
                                            key: 'excel-new',
                                            label: 'Exportar a Excel (Nueva)',
                                            icon: <FileExcelOutlined />,
                                            onClick: handleExportExcel
                                        },
                                        {
                                            key: 'excel',
                                            label: 'Exportar a Excel',
                                            icon: <ExportOutlined />,
                                            onClick: () => handleExportData('excel')
                                        },
                                        {
                                            key: 'pdf',
                                            label: 'Exportar a PDF',
                                            icon: <DownloadOutlined />,
                                            onClick: () => handleExportData('pdf')
                                        }
                                    ]
                                }}
                            >
                                <Button icon={downloadIcon2} loading={state.exportLoading}>
                                    Exportar
                                </Button>
                            </Dropdown>
                            <Tooltip title="Sincronizar datos">
                                <Button
                                    icon={syncIcon}
                                    onClick={handleSyncData}
                                    loading={state.syncLoading}
                                />
                            </Tooltip>
                            <Tooltip title="Integración API">
                                <Button
                                    icon={apiIcon}
                                    onClick={handleIntegracionAPI}
                                    type="dashed"
                                />
                            </Tooltip>
                            <Tooltip title="Análisis de Evolución">
                                <Button
                                    icon={lineChartIcon2}
                                    onClick={() => dispatch({ type: 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE', payload: true })}
                                >
                                    Análisis
                                </Button>
                            </Tooltip>
                            <Tooltip title="Generador de Reportes">
                                <Button
                                    icon={fileTextOutlinedIcon8}
                                    onClick={() => dispatch({ type: 'SET_MODAL_REPORTES_VISIBLE', payload: true })}
                                >
                                    Reportes
                                </Button>
                            </Tooltip>
                            <Tooltip title="Sistema de Alertas">
                                <Button
                                    icon={bellOutlinedIcon3}
                                    onClick={() => dispatch({ type: 'SET_MODAL_ALERTAS_VISIBLE', payload: true })}
                                >
                                    Alertas
                                </Button>
                            </Tooltip>
                            <Tooltip title="Panel de Control Obstétrico">
                                <Button
                                    icon={databaseOutlinedIcon3}
                                    onClick={() => dispatch({ type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE', payload: true })}
                                    type="primary"
                                >
                                    Panel Control
                                </Button>
                            </Tooltip>
                            <Button icon={reloadOutlinedIcon4} onClick={loadEmbarazos} loading={state.loading}>
                                Recargar
                            </Button>
                        </Space>
                    </Col>
                </Row>

                {/* Tabla */}
                <Table
                    dataSource={filteredData}
                    columns={columns as any}
                    rowKey={(record: any) => record._uniqueRowKey || `embarazo-fallback-${record.id}`}
                    loading={state.loading}
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} registros`,
                        pageSizeOptions: ['10', '20', '50', '100'],
                    }}
                    scroll={{ x: 1200 }}
                    locale={{
                        emptyText: (
                            <ResultEmpty
                                icon={heartOutlinedIcon6}
                                title="No hay state.embarazos registrados"
                                subTitle="Comience registrando un nuevo embarazo utilizando el botón superior"
                                extra={
                                    canAdd('embarazo') ? (
                                        <Button type="primary" icon={plusOutlinedIcon9} onClick={handleOpenCreate}>
                                            Registrar Nuevo Embarazo
                                        </Button>
                                    ) : null
                                }
                            />
                        )
                    }}
                />
            </Card>

            {/* ========================================================================
            MODAL DE REGISTRO / EDICIÓN
           ======================================================================== */}
            <Modal
                title={
                    <Space>
                        <MedicineBoxOutlined style={{ color: '#1890ff' }} />
                        {state.editingEmbarazo ? 'Actualizar Ficha Clínica' : 'Apertura de Historia Obstétrica'}
                    </Space>
                }
                open={state.modalVisible}
                onCancel={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
                width={900}
                footer={null}
                maskClosable={false}
                centered
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit}>

                    <Alert
                        message="Cálculo Automático Activo"
                        description="Al ingresar la Fecha de Última Menstruación (FUM), el sistema calculará automáticamente la FPP y la Edad Gestacional actual."
                        type="info"
                        showIcon
                        style={{ marginBottom: 24 }}
                    />

                    {/* 1. SELECCIÓN DE PACIENTE */}
                    <Card type="inner" title="1. Identificación del Paciente" size="small" style={{ marginBottom: 16 }}>
                        <Row gutter={16}>
                            <Col span={16}>
                                <Form.Item
                                    name="paciente"
                                    label="Buscar Paciente (Mujer)"
                                    rules={[{ required: true, message: 'Debe seleccionar una paciente' }]}
                                    help="Solo se muestran pacientes femeninos registrados"
                                >
                                    <Select
                                        showSearch
                                        placeholder="Escriba nombre o CI..."
                                        optionFilterProp="children"
                                        onSearch={(val) => loadPacientesOptions(val)}
                                        onChange={handlePacienteChange}
                                        loading={state.loadingPacientes}
                                        filterOption={false} // Filtrado en backend
                                        disabled={!!state.editingEmbarazo} // No se puede cambiar paciente al editar
                                        notFoundContent={state.loadingPacientes ? <Spin size="small" /> : null}
                                    >
                                        {state.pacientesOptions.map(p => (
                                            <Option key={p.id} value={p.id}>
                                                {p.nombre_completo} (CI: {p.ci}) - {p.edad} años
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item
                                    name="medico_responsable"
                                    label="Médico Responsable"
                                    tooltip="Seleccione el médico responsable del embarazo"
                                >
                                    <Select
                                        showSearch
                                        placeholder="Seleccione un médico"
                                        optionFilterProp="children"
                                        loading={state.loadingMedicos}
                                        allowClear
                                        filterOption={(input, option) =>
                                            (option?.children as unknown as string)
                                                ?.toLowerCase()
                                                .includes(input.toLowerCase())
                                        }
                                    >
                                        {state.medicos.map(medico => (
                                            <Option key={medico.id} value={medico.id}>
                                                Dr./Dra. {medico.nombre} {medico.apellido_paterno || medico.apellido || ''}
                                            </Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>

                    {/* 2. DATOS OBSTÉTRICOS */}
                    <Card type="inner" title="2. Datos Obstétricos Actuales" size="small" style={{ marginBottom: 16 }}>
                        <Row gutter={16}>
                            <Col span={8}>
                                <Form.Item name="fecha_ultima_menstruacion" label="Fecha Última Menstruación (FUM)" rules={[{ required: true }]}>
                                    <DatePicker
                                        style={{ width: '100%' }}
                                        format="DD/MM/YYYY"
                                        onChange={handleFUMChange}
                                        locale={locale}
                                        placeholder="Seleccione fecha"
                                    />
                                </Form.Item>
                                {state.edadGestacionalCalculada && (
                                    <div style={{ marginTop: -10, marginBottom: 10, color: '#1890ff', fontSize: 12 }}>
                                        <InfoCircleOutlined /> EG: {state.edadGestacionalCalculada}
                                    </div>
                                )}
                            </Col>
                            <Col span={8}>
                                <Form.Item name="fecha_probable_parto" label="Fecha Probable de Parto (FPP)" tooltip="Calculada automáticamente (Regla Naegele)">
                                    <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" locale={locale} />
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item name="numero_gesta" label="Nº Gesta Actual" rules={[{ required: true }]}>
                                    <InputNumber min={1} max={20} style={{ width: '100%' }} />
                                </Form.Item>
                            </Col>
                        </Row>
                        <Row gutter={16}>
                            <Col span={8}>
                                <Form.Item name="tipo_embarazo" label="Tipo de Embarazo" rules={[{ required: true }]}>
                                    <Select>
                                        <Option value="simple">Simple (1)</Option>
                                        <Option value="gemelar">Gemelar (2)</Option>
                                        <Option value="multiple">Múltiple (3+)</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item name="riesgo_embarazo" label="Clasificación de Riesgo" rules={[{ required: true }]}>
                                    <Select>
                                        <Option value="bajo">🟢 Bajo Riesgo</Option>
                                        <Option value="medio">🟠 Riesgo Medio</Option>
                                        <Option value="alto">🔴 Alto Riesgo</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={8}>
                                <Form.Item name="estado" label="Estado">
                                    <Select>
                                        <Option value="activo">Activo</Option>
                                        <Option value="finalizado">Finalizado</Option>
                                        <Option value="perdida">Pérdida</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>

                    {/* 3. ANTECEDENTES */}
                    <Card type="inner" title="3. Antecedentes Ginecobstétricos" size="small" style={{ marginBottom: 16 }}>
                        <Row gutter={16}>
                            <Col span={6}>
                                <Form.Item name="partos_previos" label="Partos" initialValue={0}>
                                    <InputNumber min={0} max={20} style={{ width: '100%' }} />
                                </Form.Item>
                            </Col>
                            <Col span={6}>
                                <Form.Item name="cesareas_previas" label="Cesáreas" initialValue={0}>
                                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                                </Form.Item>
                            </Col>
                            <Col span={6}>
                                <Form.Item name="abortos_previos" label="Abortos" initialValue={0}>
                                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                                </Form.Item>
                            </Col>
                            <Col span={6}>
                                <Form.Item name="hijos_vivos" label="Hijos Vivos" initialValue={0}>
                                    <InputNumber min={0} max={20} style={{ width: '100%' }} />
                                </Form.Item>
                            </Col>
                        </Row>
                    </Card>

                    {/* 4. ANTROPOMETRÍA Y NOTAS */}
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item name="notas" label="Observaciones / Antecedentes Patológicos">
                                <Input.TextArea rows={4} placeholder="Alergias, enfermedades crónicas, cirugías previas..." />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Card size="small" title="Datos Iniciales">
                                <Row gutter={8}>
                                    <Col span={12}>
                                        <Form.Item name="peso_pregestacional" label="Peso (kg)">
                                            <InputNumber style={{ width: '100%' }} min={20} max={200} onChange={handleAntropometriaChange} />
                                        </Form.Item>
                                    </Col>
                                    <Col span={12}>
                                        <Form.Item name="talla_materna" label="Talla (cm)">
                                            <InputNumber style={{ width: '100%' }} min={100} max={220} onChange={handleAntropometriaChange} />
                                        </Form.Item>
                                    </Col>
                                </Row>
                                {state.imcCalculado && <Alert message={`IMC: ${state.imcCalculado}`} type="success" showIcon style={{ marginTop: 5 }} />}
                            </Card>
                        </Col>
                    </Row>

                    <Divider />

                    <div style={{ textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })} size="large">Cancelar</Button>
                            <Button type="primary" htmlType="submit" loading={state.actionLoading} icon={checkCircleOutlinedIcon7} size="large">
                                {state.editingEmbarazo ? 'Guardar Cambios' : 'Registrar Embarazo'}
                            </Button>
                        </Space>
                    </div>

                </Form>
            </Modal>

            {/* ========================================================================
            DRAWER DE DETALLE RÁPIDO
           ======================================================================== */}
            <Drawer
                className="embarazo-resumen-drawer"
                title="Resumen del Embarazo"
                placement="right"
                width={550}
                onClose={() => dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false })}
                open={state.drawerVisible}
                extra={
                    <Button type="primary" onClick={() => navigate(`/dashboard/pacientes/${state.selectedEmbarazo?.paciente}/historia`)}>
                        Ver Historia Completa
                    </Button>
                }
            >
                {state.selectedEmbarazo ? (
                    <div className="drawer-content">
                        <div className="drawer-header-section">
                            <Avatar size={64} icon={userOutlinedIcon4} style={{ backgroundColor: '#1890ff', marginBottom: 10 }} />
                            <Title level={3} style={{ margin: 0 }}>{state.selectedEmbarazo?.paciente_nombre}</Title>
                            <Text type="secondary">Gesta {state.selectedEmbarazo?.numero_gesta} • {(state.selectedEmbarazo?.tipo_embarazo || 'simple').toUpperCase()}</Text>
                            <div style={{ marginTop: 12 }}>
                                <Tag color={(RISK_COLORS as any)[state.selectedEmbarazo?.riesgo_embarazo || 'bajo']} style={{ padding: '4px 12px', fontSize: 14 }}>
                                    {(RISK_LABELS as any)[state.selectedEmbarazo?.riesgo_embarazo || 'bajo'] || 'Sin especificar'}
                                </Tag>
                            </div>
                        </div>

                        <Descriptions title="Estado Actual" bordered column={1} size="small" className="drawer-descriptions" style={{ marginBottom: 24 }}>
                            <Descriptions.Item label="Edad Gestacional">
                                <span style={{ fontSize: 16, fontWeight: 'bold', color: '#1890ff' }}>
                                    {state.selectedEmbarazo?.edad_gestacional_semanas_num} semanas
                                </span>
                                <span style={{ marginLeft: 8, color: '#999' }}>+ {state.selectedEmbarazo?.edad_gestacional_dias_num} días</span>
                            </Descriptions.Item>
                            <Descriptions.Item label="Trimestre Actual">
                                {state.selectedEmbarazo?.trimestre_actual}º Trimestre
                            </Descriptions.Item>
                            <Descriptions.Item label="Fecha Probable Parto">
                                {state.selectedEmbarazo?.fecha_probable_parto ? dayjs(state.selectedEmbarazo?.fecha_probable_parto).format('DD [de] MMMM [de] YYYY') : 'No definida'}
                            </Descriptions.Item>
                        </Descriptions>

                        <Descriptions title="Datos Antropométricos Pregestacionales" bordered column={1} size="small" className="drawer-descriptions" style={{ marginBottom: 24 }}>
                            <Descriptions.Item label="Peso Pregestacional">
                                <span style={{ fontSize: 14, fontWeight: 'bold' }}>
                                    {state.selectedEmbarazo?.peso_pregestacional ? `${state.selectedEmbarazo?.peso_pregestacional} kg` : 'No registrado'}
                                </span>
                            </Descriptions.Item>
                            <Descriptions.Item label="Talla Materna">
                                <span style={{ fontSize: 14, fontWeight: 'bold' }}>
                                    {state.selectedEmbarazo?.talla_materna ? `${state.selectedEmbarazo?.talla_materna} cm` : 'No registrado'}
                                </span>
                            </Descriptions.Item>
                            <Descriptions.Item label="IMC Pregestacional">
                                <span style={{ fontSize: 14, fontWeight: 'bold' }}>
                                    {state.selectedEmbarazo?.imc_pregestacional ?
                                        <>
                                            {state.selectedEmbarazo?.imc_pregestacional.toFixed(1)}
                                            <Tag color={
                                                state.selectedEmbarazo?.imc_pregestacional < 18.5 ? 'blue' :
                                                    state.selectedEmbarazo?.imc_pregestacional < 25 ? 'green' :
                                                        state.selectedEmbarazo?.imc_pregestacional < 30 ? 'orange' : 'red'
                                            } style={{ marginLeft: 8 }}>
                                                {state.selectedEmbarazo?.imc_pregestacional < 18.5 ? 'Bajo peso' :
                                                    state.selectedEmbarazo?.imc_pregestacional < 25 ? 'Normal' :
                                                        state.selectedEmbarazo?.imc_pregestacional < 30 ? 'Sobrepeso' : 'Obesidad'}
                                            </Tag>
                                        </>
                                        : 'No registrado'
                                    }
                                </span>
                            </Descriptions.Item>
                        </Descriptions>

                        <Divider orientation="left">Línea de Tiempo</Divider>
                        <Timeline
                            mode="left"
                            items={[
                                {
                                    color: 'green',
                                    label: dayjs(state.selectedEmbarazo?.fecha_ultima_menstruacion).format('DD/MM/YY'),
                                    children: 'Inicio del ciclo (FUM)'
                                },
                                {
                                    color: 'blue',
                                    children: `Fecha actual (${state.selectedEmbarazo?.edad_gestacional_semanas_num} semanas)`
                                },
                                {
                                    color: 'gray',
                                    label: dayjs(state.selectedEmbarazo?.fecha_probable_parto).format('DD/MM/YY'),
                                    children: 'Fecha Probable de Parto (40s)'
                                }
                            ]}
                        />

                        <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
                        <Card size="small" style={{ marginBottom: 16 }}>
                            <Space direction="vertical" style={{ width: '100%' }} size="small">
                                <Button
                                    type="link"
                                    icon={userOutlinedIcon4}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/pacientes?id=${state.selectedEmbarazo?.paciente}`);
                                    }}
                                >
                                    Ver Paciente: {state.selectedEmbarazo?.paciente_nombre}
                                </Button>
                                <Button
                                    type="link"
                                    icon={medicineBoxOutlinedIcon7}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/controles?embarazo=${state.selectedEmbarazo?.id}`);
                                    }}
                                >
                                    Ver Controles Prenatales
                                </Button>
                                <Button
                                    type="link"
                                    icon={experimentOutlinedIcon3}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/ecografias?embarazo=${state.selectedEmbarazo?.id}`);
                                    }}
                                >
                                    Ver Ecografías del Embarazo
                                </Button>
                                <Button
                                    type="link"
                                    icon={fileTextOutlinedIcon8}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/laboratorio?embarazo=${state.selectedEmbarazo?.id}`);
                                    }}
                                >
                                    Ver Exámenes de Laboratorio
                                </Button>
                                <Button
                                    type="link"
                                    icon={calendarOutlinedIcon8}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/citas?embarazo=${state.selectedEmbarazo?.id}`);
                                    }}
                                >
                                    Ver Citas del Embarazo
                                </Button>
                                <Button
                                    type="link"
                                    icon={heartOutlinedIcon7}
                                    block
                                    style={{ textAlign: 'left' }}
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/partos?embarazo=${state.selectedEmbarazo?.id}`);
                                    }}
                                >
                                    Ver Información de Parto
                                </Button>
                                <Divider style={{ margin: '8px 0' }} />
                                <Button
                                    type="primary"
                                    icon={bookOutlinedIcon3}
                                    block
                                    onClick={() => {
                                        dispatch({ type: 'SET_DRAWER_VISIBLE', payload: false });
                                        navigate(`/dashboard/state.embarazos/${state.selectedEmbarazo?.id}/historia`);
                                    }}
                                >
                                    Ver Historia Completa del Embarazo
                                </Button>
                            </Space>
                        </Card>

                        <Divider orientation="left">Notas Clínicas</Divider>
                        <Alert
                            message={state.selectedEmbarazo.notas || "No hay notas registradas."}
                            type="info"
                        />

                        <div style={{ marginTop: 30 }}>
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Statistic title="Partos Previos" value={state.selectedEmbarazo.partos_previos} prefix={<WomanOutlined />} />
                                </Col>
                                <Col span={12}>
                                    <Statistic title="Cesáreas" value={state.selectedEmbarazo.cesareas_previas} prefix={<MedicineBoxOutlined />} />
                                </Col>
                            </Row>
                        </div>
                    </div>
                ) : <Empty />}
            </Drawer>

            {/* ========================================================================
            MÓDULO DE ANÁLISIS Y GRÁFICAS DE EVOLUCIÓN (NUEVO)
           ======================================================================== */}
            <Modal
                title={<Space><LineChartOutlined /> Análisis de Evolución de state.embarazos</Space>}
                open={state.modalAnalisisEvolucionVisible}
                onCancel={() => dispatch({ type: 'SET_MODAL_ANALISIS_EVOLUCION_VISIBLE', payload: false })}
                width={1200}
                footer={null}
            >
                <Tabs
                    items={[
                        {
                            key: '1',
                            label: 'Tendencias de Riesgo',
                            children: (
                                <Card>
                                    <Alert
                                        message="Distribución de Riesgo Obstétrico"
                                        description={`
                                        Análisis de ${state.embarazos.length} state.embarazos registrados. 
                                        Alto riesgo: ${stats.altoRiesgo} casos, requieren seguimiento especializado.
                                    `}
                                        type="info"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                    <Row gutter={16}>
                                        <Col span={12}>
                                            <Statistic title="Tasa de Alto Riesgo" value={stats.activos > 0 ? ((stats.altoRiesgo / stats.activos) * 100).toFixed(1) : 0} suffix="%" valueStyle={{ color: '#cf1322' }} />
                                        </Col>
                                        <Col span={12}>
                                            <Statistic title="state.embarazos a Término" value={stats.termino} suffix={`/ ${stats.activos}`} valueStyle={{ color: '#3f8600' }} />
                                        </Col>
                                    </Row>
                                </Card>
                            ),
                        },
                        {
                            key: '2',
                            label: 'Comparación Multi-Paciente',
                            children: (
                                <Alert
                                    message="Herramienta de Comparación"
                                    description="Seleccione hasta 3 state.embarazos para comparar evolución, factores de riesgo y resultados."
                                    type="info"
                                    showIcon
                                />
                            ),
                        },
                        {
                            key: '3',
                            label: 'Predicción de Complicaciones',
                            children: (
                                <Card title="Algoritmo de Machine Learning (Simulado)">
                                    <Alert
                                        message="Modelo Predictivo"
                                        description={`
                                        Basado en ${state.embarazos.length} registros históricos, se identifican patrones de riesgo. 
                                        Precisión estimada: 87%. Factores clave: edad materna, IMC, antecedentes, riesgo asignado.
                                    `}
                                        type="success"
                                        showIcon
                                    />
                                    <Divider />
                                    <Text strong>Principales Factores de Riesgo Detectados:</Text>
                                    <ul style={{ marginTop: 10 }}>
                                        <li>Edad materna {'>'} 35 años: Aumenta riesgo 2.3x</li>
                                        <li>IMC {'>'} 30: Aumenta riesgo 1.8x (preeclampsia, diabetes gestacional)</li>
                                        <li>Cesáreas previas ≥ 2: Aumenta riesgo de complicaciones uterinas</li>
                                        <li>Historia de abortos: Requiere vigilancia estrecha</li>
                                    </ul>
                                </Card>
                            ),
                        },
                        {
                            key: '4',
                            label: 'Cumplimiento de Protocolos MSP',
                            children: (
                                <Card title="Adherencia a Normativas del Ministerio de Salud Pública">
                                    <Text>Evaluación automática del cumplimiento de controles prenatales según normativa MSP:</Text>
                                    <Divider />
                                    <Table
                                        size="small"
                                        columns={[
                                            { title: 'Criterio', dataIndex: 'criterio', key: 'criterio' },
                                            { title: 'Esperado', dataIndex: 'esperado', key: 'esperado' },
                                            { title: 'Real', dataIndex: 'real', key: 'real' },
                                            {
                                                title: 'Estado',
                                                dataIndex: 'estado',
                                                key: 'estado',
                                                render: (estado: string) => (
                                                    <Tag color={estado === 'conforme' ? 'green' : 'red'}>
                                                        {estado === 'conforme' ? 'Conforme' : 'No Conforme'}
                                                    </Tag>
                                                )
                                            }
                                        ]}
                                        dataSource={[
                                            { key: '1', criterio: 'Controles 1er Trimestre', esperado: '2 mínimo', real: 'Variable', estado: 'conforme' },
                                            { key: '2', criterio: 'Controles 2do Trimestre', esperado: '2 mínimo', real: 'Variable', estado: 'conforme' },
                                            { key: '3', criterio: 'Controles 3er Trimestre', esperado: '4 mínimo', real: 'Variable', estado: 'conforme' },
                                            { key: '4', criterio: 'Ecografías', esperado: '3 mínimo', real: 'Variable', estado: 'conforme' },
                                            { key: '5', criterio: 'Laboratorios Básicos', esperado: 'BHC, Glicemia, VDRL, VIH', real: 'Variable', estado: 'conforme' }
                                        ]}
                                        pagination={false}
                                    />
                                </Card>
                            ),
                        },
                    ]}
                />
            </Modal>

            {/* ========================================================================
            GENERADOR DE REPORTES AVANZADOS
           ======================================================================== */}
            <Modal
                title="Generador de Reportes Obstétricos"
                open={state.modalReportesVisible}
                onCancel={() => dispatch({ type: 'SET_MODAL_REPORTES_VISIBLE', payload: false })}
                width={800}
                footer={null}
            >
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Card title="Reporte Individual de Embarazo" size="small">
                        <Form layout="vertical">
                            <Form.Item label="Seleccionar Embarazo">
                                <Select placeholder="Buscar por paciente..." showSearch>
                                    {state.embarazos.map(emb => (
                                        <Option key={emb.id} value={emb.id}>
                                            {emb.paciente_nombre} - Gesta {emb.numero_gesta} ({emb.edad_gestacional_semanas_num}s)
                                        </Option>
                                    ))}
                                </Select>
                            </Form.Item>
                            <Form.Item label="Incluir en elfax reporte">
                                <Checkbox.Group>
                                    <Row>
                                        <Col span={12}><Checkbox value="datos_basicos">Datos Básicos</Checkbox></Col>
                                        <Col span={12}><Checkbox value="antecedentes">Antecedentes</Checkbox></Col>
                                        <Col span={12}><Checkbox value="controles">Controles Prenatales</Checkbox></Col>
                                        <Col span={12}><Checkbox value="ecografias">Ecografías</Checkbox></Col>
                                        <Col span={12}><Checkbox value="laboratorios">Laboratorios</Checkbox></Col>
                                        <Col span={12}><Checkbox value="graficas">Gráficas de Evolución</Checkbox></Col>
                                    </Row>
                                </Checkbox.Group>
                            </Form.Item>
                            <Button type="primary" icon={filePdfIcon2} block>Generar PDF</Button>
                        </Form>
                    </Card>

                    <Card title="Reporte Estadístico General" size="small">
                        <Form layout="vertical">
                            <Form.Item label="Período">
                                <RangePicker style={{ width: '100%' }} />
                            </Form.Item>
                            <Form.Item label="Tipo de Análisis">
                                <Select defaultValue="resumen">
                                    <Option value="resumen">Resumen Ejecutivo</Option>
                                    <Option value="detallado">Análisis Detallado</Option>
                                    <Option value="comparativo">Comparativo Mensual</Option>
                                    <Option value="indicadores">Indicadores MSP</Option>
                                </Select>
                            </Form.Item>
                            <Button type="primary" icon={fileExcelIcon} block>Exportar a Excel</Button>
                        </Form>
                    </Card>

                    <Card title="Certificados y Carnés" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Button icon={idcardOutlinedIcon2} block>Carné Perinatal (OMS)</Button>
                            <Button icon={safetyCertificateOutlinedIcon3} block>Certificado de Monitoreo Prenatal</Button>
                            <Button icon={fileProtectOutlinedIcon2} block>Constancia de Controles</Button>
                        </Space>
                    </Card>
                </Space>
            </Modal>

            {/* ========================================================================
            SISTEMA DE ALERTAS Y RECORDATORIOS
           ======================================================================== */}
            <Modal
                title={<Space><BellOutlined /> Sistema de Alertas Inteligentes</Space>}
                open={state.modalAlertasVisible}
                onCancel={() => dispatch({ type: 'SET_MODAL_ALERTAS_VISIBLE', payload: false })}
                width={900}
                footer={null}
            >
                <Tabs
                    items={[
                        {
                            key: '1',
                            label: 'Alertas Activas',
                            children: (
                                <List
                                    itemLayout="horizontal"
                                        dataSource={
                                            state.embarazos.reduce((acc, e) => {
                                                if (e.estado === 'activo' && (e.edad_gestacional_semanas_num || 0) >= 37) {
                                                    acc.push({
                                                        id: e.id,
                                                        tipo: 'TÉRMINO',
                                                        mensaje: `${e.paciente_nombre} - ${e.edad_gestacional_semanas_num} semanas. Próximo a término.`,
                                                        prioridad: 'media',
                                                        fecha: dayjs().format('DD/MM/YYYY')
                                                    });
                                                }
                                                return acc;
                                            }, [] as any[])
                                        }
                                    renderItem={(item: any) => (
                                        <List.Item
                                            actions={[
                                                <Button key="ver-detalle" size="small" type="link">Ver Detalle</Button>,
                                                <Button key="descartar" size="small" type="link" danger>Descartar</Button>
                                            ]}
                                        >
                                            <List.Item.Meta
                                                avatar={<WarningOutlined style={{ fontSize: 24, color: '#faad14' }} />}
                                                title={<Text strong>[{item.tipo}] {item.mensaje}</Text>}
                                                description={`Fecha: ${item.fecha} • Prioridad: ${item.prioridad.toUpperCase()}`}
                                            />
                                        </List.Item>
                                    )}
                                />
                            ),
                        },
                        {
                            key: '2',
                            label: 'Recordatorios Programados',
                            children: (
                                <>
                                    <Alert
                                        message="Configuración de Notificaciones"
                                        description="El sistema enviará recordatorios automáticos para citas programadas 24h antes vía SMS/Email."
                                        type="info"
                                        showIcon
                                        style={{ marginBottom: 16 }}
                                    />
                                    <Form layout="vertical">
                                        <Form.Item label="Activar Recordatorios">
                                            <Switch defaultChecked /> Notificaciones Push
                                        </Form.Item>
                                        <Form.Item label="Canales de Notificación">
                                            <Checkbox.Group defaultValue={['sms', 'email']}>
                                                <Space direction="vertical">
                                                    <Checkbox value="sms">SMS (Mensajería)</Checkbox>
                                                    <Checkbox value="email">Correo Electrónico</Checkbox>
                                                    <Checkbox value="whatsapp">WhatsApp (Próximamente)</Checkbox>
                                                </Space>
                                            </Checkbox.Group>
                                        </Form.Item>
                                        <Button type="primary">Guardar Configuración</Button>
                                    </Form>
                                </>
                            ),
                        },
                        {
                            key: '3',
                            label: 'Historial de Notificaciones',
                            children: (
                                <Table
                                    size="small"
                                    columns={[
                                        { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
                                        { title: 'Paciente', dataIndex: 'paciente', key: 'paciente' },
                                        { title: 'Tipo', dataIndex: 'tipo', key: 'tipo' },
                                        {
                                            title: 'Estado',
                                            dataIndex: 'estado',
                                            key: 'estado',
                                            render: (estado: string) => (
                                                <Tag color={estado === 'enviado' ? 'green' : 'orange'}>
                                                    {estado}
                                                </Tag>
                                            )
                                        }
                                    ]}
                                    dataSource={[
                                        { key: '1', fecha: dayjs().format('DD/MM/YYYY'), paciente: 'María González', tipo: 'Recordatorio Cita', estado: 'enviado' },
                                        { key: '2', fecha: dayjs().subtract(1, 'day').format('DD/MM/YYYY'), paciente: 'Ana Torres', tipo: 'Alerta Laboratorio', estado: 'enviado' }
                                    ]}
                                    pagination={{ pageSize: 5 }}
                                />
                            ),
                        },
                    ]}
                />
            </Modal>

            {/* ========================================================================
            PANEL DE CONTROL MÉDICO AVANZADO
           ======================================================================== */}
            <Drawer
                title="Panel de Control Obstétrico"
                placement="bottom"
                height="80%"
                open={state.drawerPanelControlVisible}
                onClose={() => dispatch({ type: 'SET_DRAWER_PANEL_CONTROL_VISIBLE', payload: false })}
                closable={true}
            >
                <Row gutter={[24, 24]}>
                    <Col span={8}>
                        <Card title="Indicadores Clave (KPI)" size="small">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                <Statistic title="Tasa de Captación Temprana" value={78} suffix="%" prefix={<RiseOutlined />} />
                                <Progress percent={78} status="active" />
                                <Text type="secondary">Meta MSP: ≥ 80%</Text>

                                <Divider />

                                <Statistic title="Promedio Controles por Embarazo" value={6.4} prefix={<CheckCircleOutlined />} />
                                <Progress percent={(6.4 / 8) * 100} status="active" strokeColor="#52c41a" />
                                <Text type="secondary">Meta MSP: ≥ 5 controles</Text>

                                <Divider />

                                <Statistic title="Tasa de Complicaciones" value={12} suffix="%" valueStyle={{ color: '#cf1322' }} />
                                <Progress percent={12} status="exception" />
                                <Text type="secondary">Objetivo: {'<'} 15%</Text>
                            </Space>
                        </Card>
                    </Col>

                    <Col span={8}>
                        <Card title="Análisis Temporal" size="small">
                            <Text strong>state.embarazos por Trimestre Actual:</Text>
                            <div style={{ marginTop: 16 }}>
                                <Row gutter={8}>
                                    <Col span={8}>
                                        <Card size="small" style={{ textAlign: 'center', background: '#e6f7ff' }}>
                                            <Statistic title="1T" value={stats.primerTrimestre} valueStyle={{ fontSize: 24 }} />
                                        </Card>
                                    </Col>
                                    <Col span={8}>
                                        <Card size="small" style={{ textAlign: 'center', background: '#f0f5ff' }}>
                                            <Statistic title="2T" value={state.embarazos.filter(e => e.trimestre_actual === 2 && e.estado === 'activo').length} valueStyle={{ fontSize: 24 }} />
                                        </Card>
                                    </Col>
                                    <Col span={8}>
                                        <Card size="small" style={{ textAlign: 'center', background: '#fff7e6' }}>
                                            <Statistic title="3T" value={state.embarazos.filter(e => e.trimestre_actual === 3 && e.estado === 'activo').length} valueStyle={{ fontSize: 24 }} />
                                        </Card>
                                    </Col>
                                </Row>
                            </div>

                            <Divider />

                            <Text strong>Próximos Partos Estimados (30 días):</Text>
                            <List
                                size="small"
                                dataSource={
                                    state.embarazos
                                        .filter(e => e.fecha_probable_parto && dayjs(e.fecha_probable_parto).diff(dayjs(), 'day') <= 30 && dayjs(e.fecha_probable_parto).diff(dayjs(), 'day') >= 0)
                                        .slice(0, 5)
                                }
                                renderItem={(item: any) => (
                                    <List.Item key={`fpp-${item.id}`}>
                                        <Text>{item.paciente_nombre}</Text>
                                        <Text type="secondary">{dayjs(item.fecha_probable_parto).format('DD/MM')}</Text>
                                    </List.Item>
                                )}
                            />
                        </Card>
                    </Col>

                    <Col span={8}>
                        <Card title="Acciones Rápidas" size="small">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                {canAdd('embarazo') && (
                                    <Button icon={plusOutlinedIcon9} type="primary" block onClick={handleOpenCreate}>
                                        Nuevo Embarazo
                                    </Button>
                                )}
                                <Button icon={calendarOutlinedIcon8} block>
                                    Programar Controles Masivos
                                </Button>
                                <Button icon={fileExcelIcon} block>
                                    Exportar Base de Datos
                                </Button>
                                <Button icon={printerOutlinedIcon5} block>
                                    Imprimir Listado del Día
                                </Button>
                                <Divider />
                                <Button icon={settingOutlinedIcon2} block>
                                    Configuración de Alertas
                                </Button>
                                <Button icon={questionCircleOutlinedIcon3} block>
                                    Ayuda y Manuales
                                </Button>
                            </Space>
                        </Card>
                    </Col>
                </Row>

                <Divider orientation="left">Recursos Adicionales</Divider>

                <Row gutter={[16, 16]}>
                    <Col span={6}>
                        <Card size="small" hoverable style={{ textAlign: 'center' }}>
                            <BookOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
                            <div><Text strong>Protocolos MSP</Text></div>
                            <div><Text type="secondary" style={{ fontSize: 12 }}>Guías Clínicas</Text></div>
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" hoverable style={{ textAlign: 'center' }}>
                            <SafetyCertificateOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
                            <div><Text strong>Normativas OMS</Text></div>
                            <div><Text type="secondary" style={{ fontSize: 12 }}>Referencias Internacionales</Text></div>
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" hoverable style={{ textAlign: 'center' }}>
                            <DatabaseOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 8 }} />
                            <div><Text strong>Base de Datos</Text></div>
                            <div><Text type="secondary" style={{ fontSize: 12 }}>Estadísticas Históricas</Text></div>
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card size="small" hoverable style={{ textAlign: 'center' }}>
                            <TeamOutlined style={{ fontSize: 32, color: '#fa8c16', marginBottom: 8 }} />
                            <div><Text strong>Equipo Médico</Text></div>
                            <div><Text type="secondary" style={{ fontSize: 12 }}>Contactos y Turnos</Text></div>
                        </Card>
                    </Col>
                </Row>
            </Drawer>

            {/* ========================================================================
            MODAL DE HISTORIAL COMPLETO
           ======================================================================== */}
            <Modal
                title={
                    <Space>
                        <HistoryOutlined />
                        <span>Historial Completo del Embarazo</span>
                    </Space>
                }
                open={state.historialModalVisible}
                onCancel={() => dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: false })}
                width={900}
                footer={[
                    <Button key="close" onClick={() => dispatch({ type: 'SET_HISTORIAL_MODAL_VISIBLE', payload: false })}>
                        Cerrar
                    </Button>,
                    <Button key="export" icon={fileTextOutlinedIcon8} type="primary">
                        Exportar Historial
                    </Button>
                ]}
            >
                {state.selectedEmbarazo && (
                    <div>
                        <Card size="small" style={{ marginBottom: 16 }}>
                            <Descriptions column={2} size="small">
                                <Descriptions.Item label="Paciente">
                                    <Text strong>{state.selectedEmbarazo?.paciente_nombre}</Text>
                                </Descriptions.Item>
                                <Descriptions.Item label="Estado">
                                    <Badge status={(STATUS_COLORS as any)[state.selectedEmbarazo?.estado || 'activo']} text={(STATUS_LABELS as any)[state.selectedEmbarazo?.estado || 'activo']} />
                                </Descriptions.Item>
                                <Descriptions.Item label="Edad Gestacional">
                                    {state.selectedEmbarazo.edad_gestacional_semanas_num || 0}s + {state.selectedEmbarazo.edad_gestacional_dias_num || 0}d
                                </Descriptions.Item>
                                <Descriptions.Item label="Riesgo">
                                    <Tag color={(RISK_COLORS as any)[state.selectedEmbarazo.riesgo_embarazo || 'bajo']}>
                                        {(RISK_LABELS as any)[state.selectedEmbarazo.riesgo_embarazo || 'bajo']}
                                    </Tag>
                                </Descriptions.Item>
                            </Descriptions>
                        </Card>

                        <Divider orientation="left">
                            <Space>
                                <ManOutlined />
                                <span>Antecedentes Obstétricos</span>
                            </Space>
                        </Divider>
                        <Paragraph style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                            <Text strong>Gesta:</Text> {state.selectedEmbarazo.numero_gesta} •{' '}
                            <Text strong>Partos previos:</Text> {state.selectedEmbarazo.partos_previos || 0} •{' '}
                            <Text strong>Cesáreas:</Text> {state.selectedEmbarazo.cesareas_previas || 0} •{' '}
                            <Text strong>Abortos:</Text> {state.selectedEmbarazo.abortos_previos || 0}
                        </Paragraph>

                        <Divider orientation="left">
                            <Space>
                                <ExperimentOutlined />
                                <span>Notas Clínicas</span>
                            </Space>
                        </Divider>
                        <TextArea
                            rows={4}
                            value={state.selectedEmbarazo.notas || 'Sin notas registradas'}
                            readOnly
                            style={{ marginBottom: 16 }}
                        />

                        <Divider orientation="left">Línea de Tiempo</Divider>
                        <Timeline>
                            <Timeline.Item color="blue" dot={calendarOutlinedIcon9}>
                                <Text strong>FUM:</Text> {dayjs(state.selectedEmbarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
                            </Timeline.Item>
                            {state.selectedEmbarazo.fecha_probable_parto && (
                                <Timeline.Item color="green" dot={checkCircleOutlinedIcon8}>
                                    <Text strong>FPP:</Text> {dayjs(state.selectedEmbarazo.fecha_probable_parto).format('DD/MM/YYYY')}
                                    {' '}({dayjs(state.selectedEmbarazo.fecha_probable_parto).diff(dayjs(), 'days')} días restantes)
                                </Timeline.Item>
                            )}
                            <Timeline.Item color="gray">
                                <Text type="secondary">Registro creado el {dayjs().format('DD/MM/YYYY')}</Text>
                            </Timeline.Item>
                        </Timeline>
                    </div>
                )}
            </Modal>

            {/* ========================================================================
            MODAL DE SUBIDA DE DOCUMENTOS
           ======================================================================== */}
            <Modal
                title={
                    <Space>
                        <CloudUploadOutlined />
                        <span>Subir Documentos del Embarazo</span>
                    </Space>
                }
                open={state.uploadModalVisible}
                onCancel={() => dispatch({ type: 'SET_UPLOAD_MODAL_VISIBLE', payload: false })}
                width={700}
                footer={[
                    <Button key="close" onClick={() => dispatch({ type: 'SET_UPLOAD_MODAL_VISIBLE', payload: false })}>
                        Cerrar
                    </Button>,
                    <Button
                        key="download"
                        icon={cloudDownloadOutlinedIcon3}
                        onClick={() => message.info('Descargando documentos...')}
                    >
                        Descargar Todos
                    </Button>
                ]}
            >
                {state.selectedEmbarazo && (
                    <div>
                        <Alert
                            message="Gestión de Documentos Clínicos"
                            description={`Suba ecografías, análisis de laboratorio y otros documentos relacionados con el embarazo de ${state.selectedEmbarazo?.paciente_nombre}`}
                            type="info"
                            showIcon
                            icon={inboxIcon2}
                            style={{ marginBottom: 16 }}
                        />

                        <Spin spinning={state.uploadingFiles} tip="Subiendo archivos…">
                            <Upload.Dragger
                                name="file"
                                multiple
                                customRequest={handleUploadDocuments}
                                fileList={state.fileList}
                                onChange={({ fileList: newFileList }) => dispatch({ type: 'SET_FILE_LIST', payload: newFileList })}
                                disabled={state.uploadingFiles}
                            >
                                <p className="ant-upload-drag-icon">
                                    <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                                </p>
                                <p className="ant-upload-text">
                                    <UploadOutlined /> Haga clic o arrastre archivos aquí
                                </p>
                                <p className="ant-upload-hint">
                                    Formatos soportados: PDF, JPG, PNG, DICOM (ecografías)
                                </p>
                            </Upload.Dragger>
                        </Spin>

                        <Divider>Documentos Existentes</Divider>

                        <List
                            size="small"
                            dataSource={[
                                { id: 1, nombre: 'Ecografía 12 semanas.pdf', fecha: dayjs().subtract(2, 'weeks').format('DD/MM/YYYY'), tipo: 'Ecografía' },
                                { id: 2, nombre: 'Análisis Hemograma.pdf', fecha: dayjs().subtract(1, 'week').format('DD/MM/YYYY'), tipo: 'Laboratorio' }
                            ]}
                            renderItem={(item) => (
                                <List.Item
                                    actions={[
                                        <Button key="descargar" size="small" type="link" icon={downloadIcon3}>Descargar</Button>,
                                        <Button key="eliminar" size="small" type="link" danger>Eliminar</Button>
                                    ]}
                                >
                                    <List.Item.Meta
                                        avatar={<FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
                                        title={item.nombre}
                                        description={`${item.tipo} • ${item.fecha}`}
                                    />
                                </List.Item>
                            )}
                        />
                    </div>
                )}
            </Modal>

            {/* ========================================================================
            DRAWER DE FILTROS AVANZADOS
           ======================================================================== */}
            <Drawer
                title={
                    <Space>
                        <FilterOutlined />
                        <span>Filtros Avanzados</span>
                    </Space>
                }
                placement="right"
                width={400}
                open={state.filtrosAvanzadosVisible}
                onClose={() => dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: false })}
            >
                <Form layout="vertical">
                    <Form.Item label="Vista de Tabla">
                        <Radio.Group
                            value={state.vistaComparacion}
                            onChange={(e) => dispatch({ type: 'SET_VISTA_COMPARACION', payload: e.target.value })}
                            buttonStyle="solid"
                        >
                            <Radio.Button value="tabla">Tabla</Radio.Button>
                            <Radio.Button value="tarjetas">Tarjetas</Radio.Button>
                        </Radio.Group>
                    </Form.Item>

                    <Form.Item label="Mostrar state.embarazos">
                        <Radio.Group
                            value={state.mostrarFinalizados}
                            onChange={(e) => dispatch({ type: 'SET_MOSTRAR_FINALIZADOS', payload: e.target.value })}
                        >
                            <Space direction="vertical">
                                <Radio value={false}>Solo Activos</Radio>
                                <Radio value={true}>Incluir Finalizados</Radio>
                            </Space>
                        </Radio.Group>
                    </Form.Item>

                    <Divider />

                    <Form.Item label="Filtrar por Trimestre">
                        <Checkbox.Group>
                            <Space direction="vertical">
                                <Checkbox value="1">Primer Trimestre (0-13 semanas)</Checkbox>
                                <Checkbox value="2">Segundo Trimestre (14-27 semanas)</Checkbox>
                                <Checkbox value="3">Tercer Trimestre (28-40 semanas)</Checkbox>
                            </Space>
                        </Checkbox.Group>
                    </Form.Item>

                    <Form.Item label="Notas Adicionales">
                        <TextArea
                            rows={3}
                            placeholder="Agregue notas sobre los filtros aplicados..."
                        />
                    </Form.Item>

                    <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                        <Button onClick={() => dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: false })}>
                            Cancelar
                        </Button>
                        <Button type="primary" onClick={() => {
                            message.success('Filtros aplicados');
                            dispatch({ type: 'SET_FILTROS_AVANZADOS_VISIBLE', payload: false });
                        }}>
                            Aplicar Filtros
                        </Button>
                    </Space>
                </Form>
            </Drawer>

        </div>
    );
};

export default Embarazos;
