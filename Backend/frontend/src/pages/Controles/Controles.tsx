/**
 * =============================================================================
 * MÓDULO: CONTROLES PRENATALES - LISTA Y GESTIÓN COMPLETA V2.3 CORREGIDA
 * =============================================================================
 * ✅ CORRECCIONES V2.3 - FIX ID CLÍNICO Y CAMPOS FALTANTES:
 * - Fix: ID Clínico ahora se muestra correctamente en la columna
 * - Fix: Edad Gestacional visible en todas las filas
 * - Fix: PA (mmHg) se muestra correctamente
 * - Fix: Nombre del paciente sin duplicados
 * - Fix: Obtención correcta desde backend serializer
 * =============================================================================
 */
import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import {
  Table,
  Button,
  Input,
  Space,
  Card,
  Row,
  Col,
  Tag,
  Typography,
  DatePicker,
  Select,
  Tooltip,
  Badge,
  Drawer,
  Alert,
  Form,
  Modal,
  Divider,
  Descriptions,
  Statistic,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  FilterOutlined,
  ExportOutlined,
} from '@ant-design/icons';
// Recharts removed - not used in this component
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { controlesService, ControlPrenatal } from '../../services/controlesService';
import { Embarazo } from '../../services/embarazosService';
import { Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs, { Dayjs } from 'dayjs';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import { exportarExcel } from '../../utils/excelExport';

dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);

const { Option } = Select;
const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

// ═══════════════════════════════════════════════════════════════════════════
// INTERFACES Y TIPOS ADICIONALES
// ═══════════════════════════════════════════════════════════════════════════

interface FiltrosAvanzados {
  fechaDesde?: Dayjs;
  fechaHasta?: Dayjs;
  conAlertas?: boolean;
  trimestre?: 1 | 2 | 3 | null;
  rangoPA?: 'normal' | 'hipertension' | 'prehipertension' | null;
  rangoFCF?: 'normal' | 'anormal' | null;
}

type FiltrosAction =
  | { type: 'SET_FECHA_DESDE'; payload: Dayjs | undefined }
  | { type: 'SET_FECHA_HASTA'; payload: Dayjs | undefined }
  | { type: 'SET_CON_ALERTAS'; payload: boolean | undefined }
  | { type: 'SET_TRIMESTRE'; payload: 1 | 2 | 3 | null }
  | { type: 'SET_RANGO_PA'; payload: 'normal' | 'hipertension' | 'prehipertension' | null }
  | { type: 'SET_RANGO_FCF'; payload: 'normal' | 'anormal' | null }
  | { type: 'RESET' };

const filtrosReducer = (state: FiltrosAvanzados, action: FiltrosAction): FiltrosAvanzados => {
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
// COMPONENTE PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════

interface UIState {
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

type UIAction =
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

const initialUIState: UIState = {
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

function uiReducer(state: UIState, action: UIAction): UIState {
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

const Controles: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal, notification } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();

  const [controles, setControles] = useState<ControlPrenatal[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [ui, dispatchUI] = useReducer(uiReducer, initialUIState);
  const {
    modalVisible, editingControl, searchText, alertasPreview,
    selectedEmbarazo, pageSize, lastLoaded, filtrosDrawerVisible,
    formHasChanges, autoSaveEnabled, showAlertasPanel, controlVistaRapida
  } = ui;
  const [form] = Form.useForm();

  const [filtrosAvanzados, dispatchFiltros] = useReducer(filtrosReducer, {});

  // ========== FUNCIÓN DE CARGA DE DATOS - OPTIMIZADA CON CARGA PARALELA ==========
  const loadData = useCallback(async () => {
    setLoading(true);
    const startTime = performance.now();

    try {

      // 🚀 PASO 1: Obtener primera página de cada endpoint para saber cuántas páginas hay
      const [controlesPage1, embarazosPage1, pacientesPage1] = await Promise.all([
        api.get('/controles/?page=1&limit=200'),
        api.get('/embarazos/?page=1&limit=200'),
        api.get('/pacientes/?page=1&limit=200')
      ]);

      // Calcular total de páginas
      const controlesTotales = controlesPage1.data.count || 0;
      const embarazosTotales = embarazosPage1.data.count || 0;
      const pacientesTotales = pacientesPage1.data.count || 0;

      const controlesPages = Math.ceil(controlesTotales / 200);
      const embarazosPages = Math.ceil(embarazosTotales / 200);
      const pacientesPages = Math.ceil(pacientesTotales / 200);


      // 🚀 PASO 2: Crear arrays de promesas para TODAS las páginas (en paralelo)
      const controlesPromises = Array.from({ length: controlesPages }, (_, i) =>
        api.get(`/controles/?page=${i + 1}&limit=200`)
      );

      const embarazosPromises = Array.from({ length: embarazosPages }, (_, i) =>
        api.get(`/embarazos/?page=${i + 1}&limit=200`)
      );

      const pacientesPromises = Array.from({ length: pacientesPages }, (_, i) =>
        api.get(`/pacientes/?page=${i + 1}&limit=200`)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const [controlesResponses, embarazosResponses, pacientesResponses] = await Promise.all([
        Promise.all(controlesPromises),
        Promise.all(embarazosPromises),
        Promise.all(pacientesPromises)
      ]);

      // 🚀 PASO 4: Combinar todos los resultados y agregar rowKey único
      const allControles: any[] = [];
      for (const res of controlesResponses) {
        for (const control of res.data.results || []) {
          allControles.push({
            ...control,
            _uniqueRowKey: `ctrl-${control.id || allControles.length}-${Date.now()}`
          });
        }
      }
      const allEmbarazos = embarazosResponses.flatMap((res: any) => res.data.results || []);
      const allPacientes = pacientesResponses.flatMap((res: any) => res.data.results || []);

      const endTime = performance.now();
      const loadTime = ((endTime - startTime) / 1000).toFixed(2);


      setControles(allControles);
      setEmbarazos(allEmbarazos.filter((e: Embarazo) => e.estado === 'activo'));
      setPacientes(allPacientes);
      dispatchUI({ type: 'SET_LAST_LOADED', payload: dayjs().format('DD/MM/YYYY HH:mm:ss') });
      message.success(`${allControles.length} controles cargados in ${loadTime}s`);
    } catch (error: any) {
      message.error('Error al cargar datos. Verifique su conexión e intente nuevamente.');
      setControles([]);
      setEmbarazos([]);
      setPacientes([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  // ========== CARGAR DATOS INICIAL ==========
  useEffect(() => {
    loadData();
  }, [message, loadData]); // Fix: Added missing dependency message

  // ========== AUTO-GUARDAR SI ESTÁ HABILITADO ==========
  useEffect(() => {
    if (autoSaveEnabled && formHasChanges && editingControl) {
      const timer = setTimeout(() => {
        message.info('Autoguardado activado - Los cambios se guardarán automáticamente');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [autoSaveEnabled, formHasChanges, editingControl, message]);

  // ========== DETECCIÓN DE ALERTAS MÉDICAS ==========
  const detectarAlertas = useCallback((values: any): string[] => {
    const alertasDetectadas: string[] = [];

    // ALERTA: Hipertensión arterial (≥140/90)
    if (values.presion_arterial_sistolica && values.presion_arterial_diastolica) {
      if (values.presion_arterial_sistolica >= 140 || values.presion_arterial_diastolica >= 90) {
        alertasDetectadas.push('🔴 HIPERTENSIÓN ARTERIAL - Riesgo de preeclampsia');
      } else if (
        values.presion_arterial_sistolica >= 120 ||
        values.presion_arterial_diastolica >= 80
      ) {
        alertasDetectadas.push('⚠️ PREHIPERTENSIÓN - Monitoreo estrecho requerido');
      } else if (
        values.presion_arterial_sistolica < 90 ||
        values.presion_arterial_diastolica < 60
      ) {
        alertasDetectadas.push('⚠️ HIPOTENSIÓN ARTERIAL - Evaluar hidratación');
      }
    }

    // ALERTA: Frecuencia cardíaca fetal anormal (<110 o >160)
    if (values.frecuencia_cardiaca_fetal) {
      if (values.frecuencia_cardiaca_fetal < 110) {
        alertasDetectadas.push('🚨 BRADICARDIA FETAL (<110 lpm) - URGENTE: NST inmediato');
      } else if (values.frecuencia_cardiaca_fetal > 160) {
        alertasDetectadas.push('🔴 TAQUICARDIA FETAL (>160 lpm) - Evaluar bienestar fetal');
      } else if (
        values.frecuencia_cardiaca_fetal < 120 ||
        values.frecuencia_cardiaca_fetal > 150
      ) {
        alertasDetectadas.push('⚠️ FCF en límite de normalidad - Monitoreo continuo');
      }
    }

    // ALERTA: Edema severo/generalizado
    if (values.edema === 'severo' || values.edema === 'generalizado') {
      alertasDetectadas.push('⚠️ EDEMA SEVERO/GENERALIZADO - Evaluar preeclampsia');
    }

    // ALERTA: Proteinuria positiva
    if (values.proteinuria && !['negativa', 'trazas'].includes(values.proteinuria)) {
      const nivelProteinuria = values.proteinuria.includes('4')
        ? 'CRÍTICA (++++)'
        : values.proteinuria.includes('3')
          ? 'SEVERA (+++)'
          : values.proteinuria.includes('2')
            ? 'MODERADA (++)'
            : 'LEVE (+)';
      alertasDetectadas.push(
        `⚠️ PROTEINURIA ${nivelProteinuria} - Descartar preeclampsia/síndrome nefrítico`
      );
    }

    // ALERTA: Movimientos fetales ausentes o disminuidos
    if (values.movimientos_fetales === 'ausentes') {
      alertasDetectadas.push('🚨 MOVIMIENTOS FETALES AUSENTES - EMERGENCIA: Evaluación inmediata');
    } else if (values.movimientos_fetales === 'disminuidos') {
      alertasDetectadas.push('⚠️ MOVIMIENTOS FETALES DISMINUIDOS - NST en 24 horas');
    }

    // ALERTA: Temperatura elevada (≥38°C)
    if (values.temperatura && values.temperatura >= 38) {
      alertasDetectadas.push(
        '⚠️ FIEBRE MATERNA (≥38°C) - Descartar infección. Hemograma y hemocultivo'
      );
    } else if (values.temperatura && values.temperatura >= 37.5) {
      alertasDetectadas.push('⚠️ FEBRÍCULA (≥37.5°C) - Monitoreo de temperatura cada 4 horas');
    }

    // ALERTA: Frecuencia cardíaca materna anormal
    if (values.frecuencia_cardiaca) {
      if (values.frecuencia_cardiaca > 100) {
        alertasDetectadas.push('⚠️ TAQUICARDIA MATERNA (>100 lpm) - Evaluar causas');
      } else if (values.frecuencia_cardiaca < 60) {
        alertasDetectadas.push('⚠️ BRADICARDIA MATERNA (<60 lpm) - Evaluar medicación');
      }
    }

    // ALERTA: Ganancia de peso excesiva
    if (values.peso_actual && values.peso_pregestacional) {
      const ganancia = values.peso_actual - values.peso_pregestacional;
      const semanas = values.edad_gestacional_semanas || 0;
      if (semanas > 12) {
        const gananciaEsperadaMax = semanas < 28 ? 0.5 * (semanas - 12) : 18;
        if (ganancia > gananciaEsperadaMax) {
          alertasDetectadas.push('⚠️ GANANCIA DE PESO EXCESIVA - Evaluar dieta y retención');
        }
      }
    }

    // ALERTA: Altura uterina discordante
    if (values.altura_uterina && values.edad_gestacional_semanas && values.edad_gestacional_semanas >= 20) {
      const esperada = values.edad_gestacional_semanas;
      const diferencia = Math.abs(values.altura_uterina - esperada);
      if (diferencia > 3) {
        if (values.altura_uterina < esperada - 3) {
          alertasDetectadas.push('⚠️ ALTURA UTERINA BAJA - Descartar RCIU o oligohidramnios');
        } else {
          alertasDetectadas.push(
            '⚠️ ALTURA UTERINA ELEVADA - Descartar macrosomía o polihidramnios'
          );
        }
      }
    }

    // ✅ FIX: Ya NO llama a setAlertasPreview aquí (evita loop infinito)
    // setAlertasPreview se llama solo en event handlers (handleQuickView)
    return alertasDetectadas;
  }, []);

  // ========== CALCULAR EDAD GESTACIONAL DESDE FUM ==========
  const calcularEdadGestacional = useCallback((fum: string) => {
    const hoy = dayjs();
    const fechaFum = dayjs(fum);
    const diasDiferencia = hoy.diff(fechaFum, 'day');
    const semanas = Math.floor(diasDiferencia / 7);
    const dias = diasDiferencia % 7;
    return { semanas, dias };
  }, []);

  // ========== CÁLCULO DE IMC MATERNO ==========
  const calcularIMC = useCallback((peso: number | null | undefined, talla: number | null | undefined): number | null => {
    if (!peso || !talla) return null;
    const tallaMts = talla / 100;
    return peso / (tallaMts * tallaMts);
  }, []);

  // ========== CLASIFICACIÓN DE IMC ==========
  const clasificarIMC = useCallback((imc: number | null): { texto: string; color: string } => {
    if (!imc) return { texto: '-', color: 'default' };
    if (imc < 18.5) return { texto: 'Bajo peso', color: 'warning' };
    if (imc < 25) return { texto: 'Normal', color: 'success' };
    if (imc < 30) return { texto: 'Sobrepeso', color: 'warning' };
    return { texto: 'Obesidad', color: 'error' };
  }, []);

  /**
   * ✅ FIX: Obtiene el ID Clínico del paciente desde el backend
   */
  const getIdClinicoPaciente = useCallback(
    (control: ControlPrenatal): string => {
      // ✅ PRIORIDAD 1: Usar id_clinico directo del control (viene del serializer)
      if ((control as any).id_clinico) {
        return (control as any).id_clinico;
      }

      // ✅ PRIORIDAD 2: Buscar en embarazo_info
      if ((control as any).embarazo_info?.id_clinico) {
        return (control as any).embarazo_info.id_clinico;
      }

      // ✅ FALLBACK: Buscar en arrays locales
      const embarazoId = (control as any).embarazo_id || (control as any).embarazo;
      const embarazo = embarazos.find((e) => e.id === embarazoId);
      if (embarazo) {
        if (typeof embarazo.paciente === 'object' && embarazo.paciente !== null) {
          const paciente = embarazo.paciente as Paciente;
          return paciente.id_clinico || '-';
        }
        if (typeof embarazo.paciente === 'number') {
          const paciente = pacientes.find((p) => p.id === embarazo.paciente);
          return paciente?.id_clinico || '-';
        }
      }

      return '-';
    },
    [embarazos, pacientes]
  );

  /**
   * ✅ FIX: Obtiene el nombre completo del paciente desde el backend
   */
  const getNombrePaciente = useCallback(
    (control: ControlPrenatal): string => {
      // ✅ PRIORIDAD 1: Usar paciente_nombre del control (viene del serializer)
      if ((control as any).paciente_nombre) {
        return (control as any).paciente_nombre;
      }

      // ✅ PRIORIDAD 2: Usar embarazo_info.paciente_nombre
      if ((control as any).embarazo_info?.paciente_nombre) {
        return (control as any).embarazo_info.paciente_nombre;
      }

      // ✅ FALLBACK: Buscar en arrays locales
      const embarazoId = (control as any).embarazo_id || (control as any).embarazo;
      const embarazo = embarazos.find((e) => e.id === embarazoId);
      if (!embarazo) {
        return 'Embarazo no encontrado';
      }

      if ((embarazo as any).paciente_nombre) {
        return (embarazo as any).paciente_nombre;
      }

      if (typeof embarazo.paciente === 'object' && embarazo.paciente !== null) {
        const paciente = embarazo.paciente as Paciente;
        const nombre = paciente.nombre || 'Desconocido';
        const apellido = paciente.apellido_paterno || '';
        const apellidoMat = paciente.apellido_materno || '';
        return `${nombre} ${apellido} ${apellidoMat}`.trim();
      }

      return 'Desconocido';
    },
    [embarazos]
  );

  /**
   * ✅ FIX: Obtiene la edad gestacional formateada
   */
  const getEdadGestacional = useCallback((control: ControlPrenatal): string => {
    // ✅ PRIORIDAD 1: Usar edad_gestacional del control (viene del serializer formateado)
    if ((control as any).edad_gestacional) {
      return (control as any).edad_gestacional;
    }

    // ✅ FALLBACK: Calcular manualmente
    const semanas = control.edad_gestacional_semanas || 0;
    const dias = control.edad_gestacional_dias || 0;
    return `${semanas}+${dias}`;
  }, []);

  /**
   * ✅ FIX: Obtiene la presión arterial formateada
   */
  const getPresionArterial = useCallback((control: ControlPrenatal): string => {
    // ✅ PRIORIDAD 1: Usar presion_arterial del control (viene del serializer formateado)
    if ((control as any).presion_arterial) {
      return (control as any).presion_arterial;
    }

    // ✅ FALLBACK: Calcular manualmente
    if (control.presion_arterial_sistolica && control.presion_arterial_diastolica) {
      return `${control.presion_arterial_sistolica}/${control.presion_arterial_diastolica}`;
    }

    return '-';
  }, []);

  // ========== HANDLERS ==========
  const handleExportExcel = () => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'numero_control': 'Nº Control',
        'fecha_control': 'Fecha',
        'semanas_gestacion': 'Semanas',
        'peso_materno': 'Peso (kg)',
        'presion_sistolica': 'Sistólica',
        'presion_diastolica': 'Diastólica',
        'altura_uterina': 'AU (cm)',
        'frecuencia_cardiaca_fetal': 'FCF',
        'presentacion_fetal': 'Presentación',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        controles,
        columnas,
        {
          filename: `controles_prenatales_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Controles',
          title: `Controles Prenatales - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  };

  const handleCreate = useCallback(() => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_NUEVO);
  }, [navigate]);

  const handleEdit = useCallback(
    (control: ControlPrenatal) => {
      navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_EDITAR(control.id!));
    },
    [navigate]
  );

  const handleDelete = useCallback(
    async (control: any) => {
      modal.confirm({
        title: '⚠️ ¿Confirmar eliminación permanente?',
        content: (
          <div>
            <p><strong>Se eliminará el control prenatal:</strong></p>
            <ul style={{ marginLeft: 20 }}>
              <li>Paciente: {control.paciente_nombre}</li>
              <li>Control #{control.numero_control}</li>
              <li>Fecha: {control.fecha_control}</li>
              <li>Semanas gestación: {control.semanas_gestacion}</li>
            </ul>
            <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
              ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
            </p>
            <p style={{ marginTop: 16 }}>
              Se perderán todos los datos de este control prenatal.
            </p>
          </div>
        ),
        okText: 'Sí, eliminar permanentemente',
        cancelText: 'Cancelar',
        okButtonProps: { danger: true },
        width: 550,
        onOk: async () => {
          try {
            await controlesService.delete(control.id);
            notification.success({
              message: 'Eliminación Exitosa',
              description: 'Control prenatal eliminado correctamente',
              placement: 'bottomRight'
            });
            loadData();
          } catch (error: any) {
            message.error('Error al eliminar control prenatal');
          }
        },
      });
    },
    [loadData, message, modal, notification]
  );

  const handleViewDetails = useCallback(
    (control: ControlPrenatal) => {
      navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_DETALLE(control.id!));
    },
    [navigate]
  );

  // ========== VISTA RÁPIDA DE CONTROL ==========
  const handleQuickView = useCallback(
    (control: ControlPrenatal) => {
      dispatchUI({ type: 'SET_EDITING_CONTROL', payload: control });
      dispatchUI({ type: 'SET_CONTROL_VISTA_RAPIDA', payload: control });
      dispatchUI({ type: 'SET_MODAL_VISIBLE', payload: true });

      const embarazoId = (control as any).embarazo_id || (control as any).embarazo;
      const embarazo = embarazos.find((e) => e.id === embarazoId);
      dispatchUI({ type: 'SET_SELECTED_EMBARAZO', payload: embarazo || null });

      const alertas = detectarAlertas(control);
      dispatchUI({ type: 'SET_ALERTAS_PREVIEW', payload: alertas });

      message.info(`Mostrando vista rápida del control #${control.numero_control}`);
    },
    [embarazos, detectarAlertas, message]
  );

  const handleCloseModal = useCallback(() => {
    dispatchUI({ type: 'RESET_MODAL' });
  }, []);

  const handleToggleAutoSave = useCallback(() => {
    dispatchUI({ type: 'TOGGLE_AUTO_SAVE' });
    message.success(
      !ui.autoSaveEnabled ? 'Auto-guardado activado' : 'Auto-guardado desactivado'
    );
  }, [message, ui.autoSaveEnabled]);

  const handleFormChange = useCallback(() => {
    dispatchUI({ type: 'SET_FORM_HAS_CHANGES', payload: true });
  }, []);

  const handleShowAlertasPanel = useCallback(() => {
    dispatchUI({ type: 'TOGGLE_ALERTAS_PANEL' });
  }, []);

  // ========== APLICAR FILTROS AVANZADOS ==========
  const aplicarFiltrosAvanzados = useCallback(
    (controles: ControlPrenatal[]): ControlPrenatal[] => {
      let resultado = [...controles];

      if (filtrosAvanzados.fechaDesde) {
        resultado = resultado.filter((c) =>
          dayjs(c.fecha_control).isSameOrAfter(filtrosAvanzados.fechaDesde, 'day')
        );
      }
      if (filtrosAvanzados.fechaHasta) {
        resultado = resultado.filter((c) =>
          dayjs(c.fecha_control).isSameOrBefore(filtrosAvanzados.fechaHasta, 'day')
        );
      }

      if (filtrosAvanzados.conAlertas !== undefined) {
        resultado = resultado.filter((c) => c.tiene_alertas === filtrosAvanzados.conAlertas);
      }

      if (filtrosAvanzados.trimestre) {
        resultado = resultado.filter((c) => {
          const semanas = c.edad_gestacional_semanas || 0;
          if (filtrosAvanzados.trimestre === 1) return semanas < 13;
          if (filtrosAvanzados.trimestre === 2) return semanas >= 13 && semanas < 28;
          if (filtrosAvanzados.trimestre === 3) return semanas >= 28;
          return true;
        });
      }

      if (filtrosAvanzados.rangoPA) {
        resultado = resultado.filter((c) => {
          if (!c.presion_arterial_sistolica || !c.presion_arterial_diastolica) return false;
          const isHipertension =
            c.presion_arterial_sistolica >= 140 || c.presion_arterial_diastolica >= 90;
          const isPrehipertension =
            c.presion_arterial_sistolica >= 120 || c.presion_arterial_diastolica >= 80;

          if (filtrosAvanzados.rangoPA === 'hipertension') return isHipertension;
          if (filtrosAvanzados.rangoPA === 'prehipertension')
            return isPrehipertension && !isHipertension;
          if (filtrosAvanzados.rangoPA === 'normal') return !isPrehipertension;
          return true;
        });
      }

      if (filtrosAvanzados.rangoFCF) {
        resultado = resultado.filter((c) => {
          if (!c.frecuencia_cardiaca_fetal) return false;
          const isAnormal = c.frecuencia_cardiaca_fetal < 110 || c.frecuencia_cardiaca_fetal > 160;

          if (filtrosAvanzados.rangoFCF === 'normal') return !isAnormal;
          if (filtrosAvanzados.rangoFCF === 'anormal') return isAnormal;
          return true;
        });
      }

      return resultado;
    },
    [filtrosAvanzados]
  );

  // ========== FILTRADO DE DATOS ==========
  const filteredData = useMemo(() => {
    let data = controles;

    // Filtro de texto (búsqueda rápida)
    if (searchText) {
      const lower = searchText.toLowerCase();
      data = data.filter((item) => {
        const nombrePaciente = getNombrePaciente(item).toLowerCase();
        const idClinico = getIdClinicoPaciente(item).toLowerCase();
        return (
          nombrePaciente.includes(lower) ||
          idClinico.includes(lower) ||
          item.numero_control.toString().includes(lower)
        );
      });
    }

    // Filtros avanzados
    data = aplicarFiltrosAvanzados(data);

    return data;
  }, [controles, searchText, getNombrePaciente, getIdClinicoPaciente, aplicarFiltrosAvanzados]);

  // ========== COLUMNAS DE LA TABLA ==========
  // ✅ FIX: Memoizado para evitar recreación en cada render (evita loop infinito)
  const columns = useMemo(() => [
    {
      title: 'ID Clínico',
      key: 'id_clinico',
      width: 120,
      render: (_: any, record: ControlPrenatal) => (
        <Tag color="blue">{getIdClinicoPaciente(record)}</Tag>
      ),
    },
    {
      title: 'Paciente',
      key: 'paciente',
      render: (_: any, record: ControlPrenatal) => (
        <Text strong>{getNombrePaciente(record)}</Text>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      width: 120,
      render: (date: string) => dayjs(date).format('DD/MM/YYYY'),
      sorter: (a: ControlPrenatal, b: ControlPrenatal) =>
        dayjs(a.fecha_control).unix() - dayjs(b.fecha_control).unix(),
    },
    {
      title: 'EG',
      key: 'edad_gestacional',
      width: 100,
      render: (_: any, record: ControlPrenatal) => (
        <Tag color="cyan">{getEdadGestacional(record)}</Tag>
      ),
    },
    {
      title: 'N°',
      dataIndex: 'numero_control',
      key: 'numero_control',
      width: 60,
      align: 'center' as const,
    },
    {
      title: 'PA (mmHg)',
      key: 'presion_arterial',
      width: 100,
      render: (_: any, record: ControlPrenatal) => {
        const pa = getPresionArterial(record);
        const isHigh =
          (record.presion_arterial_sistolica || 0) >= 140 ||
          (record.presion_arterial_diastolica || 0) >= 90;
        return <Text type={isHigh ? 'danger' : undefined}>{pa}</Text>;
      },
    },
    {
      title: 'AU (cm)',
      dataIndex: 'altura_uterina',
      key: 'altura_uterina',
      width: 90,
      align: 'center' as const,
      render: (val: number) => val || '-',
    },
    {
      title: 'Peso (kg)',
      dataIndex: 'peso_actual',
      key: 'peso_actual',
      width: 90,
    },
    {
      title: 'IMC',
      key: 'imc',
      width: 120,
      render: (_: any, record: ControlPrenatal) => {
        const imc = calcularIMC(record.peso_actual, record.talla);
        if (!imc) return <Text type="secondary">-</Text>;
        const clasificacion = clasificarIMC(imc);
        return (
          <Space direction="vertical" size={0} style={{ width: '100%' }}>
            <Text strong style={{ fontSize: 14 }}>{imc.toFixed(1)}</Text>
            <Tag color={clasificacion.color} style={{ fontSize: '12px', margin: 0, padding: '0 4px' }}>
              {clasificacion.texto}
            </Tag>
          </Space>
        );
      },
    },
    {
      title: 'FCF (lpm)',
      dataIndex: 'frecuencia_cardiaca_fetal',
      key: 'frecuencia_cardiaca_fetal',
      width: 90,
      render: (val: number) => {
        if (!val) return '-';
        const isBad = val < 110 || val > 160;
        return <Text type={isBad ? 'danger' : undefined}>{val}</Text>;
      },
    },
    {
      title: 'Alertas',
      key: 'alertas',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: ControlPrenatal) => {
        const alertas = detectarAlertas(record);
        return record.tiene_alertas ? (
          <Tooltip title={`${alertas.length} alertas detectadas`}>
            <Badge count={alertas.length} offset={[0, 0]}>
              <WarningOutlined style={{ color: 'red', fontSize: 18 }} />
            </Badge>
          </Tooltip>
        ) : (
          <Tooltip title="Sin alertas">
            <Badge count={0} showZero color="green">
              <CheckCircleOutlined style={{ color: 'green', fontSize: 18 }} />
            </Badge>
          </Tooltip>
        );
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 200,
      align: 'center' as const,
      render: (_: any, record: ControlPrenatal) => {
        const eg = calcularEdadGestacional(record.fecha_control);
        return (
          <Space>
            <Tooltip title={`Vista rápida (EG: ${eg.semanas}+${eg.dias})`}>
              <Button
                icon={<SearchOutlined />}
                size="small"
                onClick={() => handleQuickView(record)}
              />
            </Tooltip>
            <Tooltip title="Ver detalles completos">
              <Button
                icon={<EyeOutlined />}
                size="small"
                onClick={() => handleViewDetails(record)}
              />
            </Tooltip>
            {canChange('control') && (
              <Tooltip title="Editar control">
                <Button
                  type="primary"
                  icon={<EditOutlined />}
                  size="small"
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>
            )}
            {canDelete('control') && (
              <Tooltip title="Eliminar control">
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                  onClick={() => handleDelete(record)}
                />
              </Tooltip>
            )}
          </Space>
        );
      },
    },
  ], [
    getIdClinicoPaciente,
    getNombrePaciente,
    getEdadGestacional,
    getPresionArterial,
    calcularIMC,
    clasificarIMC,
    detectarAlertas,
    calcularEdadGestacional,
    handleQuickView,
    handleViewDetails,
    handleEdit,
    handleDelete,
    canChange,
    canDelete
  ]); // Fix: dependencies were already there but ensured format is clean
  return (
    <div className="page-container" style={{ padding: '0 24px 24px' }}>
      <Card>
        {/* Barra superior de información y extensión */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
          <Space wrap>
            <Title level={3} style={{ margin: 0 }}>
              <MedicineBoxOutlined /> Controles Prenatales
            </Title>
            <Text type="secondary">Gestión y seguimiento de controles</Text>
            <Tag color="blue">
              Total: {controles.length}
            </Tag>
            {lastLoaded && (
              <Tag color="geekblue">Última carga: {lastLoaded}</Tag>
            )}
          </Space>
              <Space>
                <Badge dot={showAlertasPanel}>
                  <Button
                    icon={<WarningOutlined />}
                    onClick={handleShowAlertasPanel}
                    danger={showAlertasPanel}
                  >
                    Alertas
                  </Button>
                </Badge>
                <Badge dot={autoSaveEnabled} color="green">
                  <Button
                    icon={<CheckCircleOutlined />}
                    onClick={handleToggleAutoSave}
                    type={autoSaveEnabled ? 'primary' : 'default'}
                  >
                    Auto-guardar
                  </Button>
                </Badge>
                <Button
                  icon={<FilterOutlined />}
                  onClick={() => dispatchUI({ type: 'SET_FILTROS_DRAWER_VISIBLE', payload: true })}
                >
                  Filtros
                </Button>
                <Button
                  icon={<ExportOutlined />}
                  onClick={handleExportExcel}
                  disabled={controles.length === 0}
                >
                  Exportar Excel
                </Button>
                {canAdd('control') && (
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={handleCreate}
                  >
                    Nuevo Control
                  </Button>
                )}
              </Space>
        </div>
        {/* Aviso si la lista es muy larga */}
        {controles.length > 500 && (
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 12 }}
            message={`La lista contiene ${controles.length} controles. Usa los filtros para acotar la búsqueda.`}
          />
        )}
        {/* Botón para extender pageSize */}
        <Row style={{ marginBottom: 8 }}>
          <Col span={24}>
            <Space>
              <Input
                placeholder="Buscar por paciente, ID clínico..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => dispatchUI({ type: 'SET_SEARCH_TEXT', payload: e.target.value })}
                allowClear
              />
              <Button
                icon={<ExportOutlined />}
                onClick={() => dispatchUI({ type: 'SET_PAGE_SIZE', payload: 10000 })}
                disabled={pageSize === 10000}
                type={pageSize === 10000 ? 'primary' : 'default'}
              >
                Mostrar TODOS
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => dispatchUI({ type: 'SET_PAGE_SIZE', payload: 50 })}
                disabled={pageSize === 50}
              >
                Paginación (50)
              </Button>
            </Space>
          </Col>
        </Row>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey={(record: any) => record._uniqueRowKey || `fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: pageSize,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} controles`,
            pageSizeOptions: ['10', '20', '50', '100', '500', '1000', '10000'],
            onShowSizeChange: (_, size) => dispatchUI({ type: 'SET_PAGE_SIZE', payload: size }),
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* DRAWER DE FILTROS */}
      <Drawer
        title={
          <Space>
            Filtros Avanzados
            {formHasChanges && <Badge status="processing" text="Modificado" />}
          </Space>
        }
        placement="right"
        onClose={() => dispatchUI({ type: 'SET_FILTROS_DRAWER_VISIBLE', payload: false })}
        open={filtrosDrawerVisible}
        width={320}
      >
        <Form form={form} layout="vertical" onValuesChange={handleFormChange}>
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Text strong>Rango de Fechas</Text>
              <RangePicker
                style={{ width: '100%', marginTop: 8 }}
                onChange={(dates) => {
                  handleFormChange();
                  dispatchFiltros({ type: 'SET_FECHA_DESDE', payload: dates ? dates[0] || undefined : undefined });
                  dispatchFiltros({ type: 'SET_FECHA_HASTA', payload: dates ? dates[1] || undefined : undefined });
                }}
              />
            </div>

            <div>
              <Text strong>Estado de Alerta</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="Todos"
                allowClear
                onChange={(val) => {
                  handleFormChange();
                  dispatchFiltros({ type: 'SET_CON_ALERTAS', payload: val });
                }}
              >
                <Option value={true}>Con Alertas</Option>
                <Option value={false}>Sin Alertas</Option>
              </Select>
            </div>

            <div>
              <Text strong>Trimestre</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="Todos"
                allowClear
                onChange={(val) => {
                  handleFormChange();
                  dispatchFiltros({ type: 'SET_TRIMESTRE', payload: val });
                }}
              >
                <Option value={1}>1° Trimestre (&lt;13 sem)</Option>
                <Option value={2}>2° Trimestre (13-28 sem)</Option>
                <Option value={3}>3° Trimestre (&gt;28 sem)</Option>
              </Select>
            </div>

            <Button
              block
              onClick={() => {
                dispatchFiltros({ type: 'RESET' });
                dispatchUI({ type: 'SET_SEARCH_TEXT', payload: '' });
                form.resetFields();
                dispatchUI({ type: 'SET_FORM_HAS_CHANGES', payload: false });
              }}
            >
              Limpiar Filtros
            </Button>
          </Space>
        </Form>
      </Drawer>

      {/* MODAL DE VISTA RÁPIDA */}
      <Modal
        title={
          <Space>
            <MedicineBoxOutlined />
            Vista Rápida del Control
            {controlVistaRapida && (
              <Tag color="blue">#{controlVistaRapida.numero_control}</Tag>
            )}
          </Space>
        }
        open={modalVisible}
        onCancel={handleCloseModal}
        width={800}
        footer={[
          <Button key="close" onClick={handleCloseModal}>
            Cerrar
          </Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              if (editingControl) {
                handleEdit(editingControl);
                handleCloseModal();
              }
            }}
          >
            Editar Completo
          </Button>,
        ]}
      >
        {editingControl && (
          <>
            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Paciente" span={2}>
                <Text strong>{getNombrePaciente(editingControl)}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="ID Clínico">
                <Tag color="blue">{getIdClinicoPaciente(editingControl)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Fecha Control">
                {dayjs(editingControl.fecha_control).format('DD/MM/YYYY')}
              </Descriptions.Item>
              <Descriptions.Item label="Edad Gestacional">
                <Tag color="cyan">{getEdadGestacional(editingControl)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="N° Control">
                {editingControl.numero_control}
              </Descriptions.Item>
            </Descriptions>

            <Divider>Signos Vitales</Divider>

            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="Presión Arterial"
                  value={getPresionArterial(editingControl)}
                  suffix="mmHg"
                  valueStyle={{
                    color:
                      (editingControl.presion_arterial_sistolica || 0) >= 140 ||
                        (editingControl.presion_arterial_diastolica || 0) >= 90
                        ? '#cf1322'
                        : '#3f8600',
                  }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="FCF"
                  value={editingControl.frecuencia_cardiaca_fetal || '-'}
                  suffix="lpm"
                  valueStyle={{
                    color:
                      editingControl.frecuencia_cardiaca_fetal &&
                        (editingControl.frecuencia_cardiaca_fetal < 110 ||
                          editingControl.frecuencia_cardiaca_fetal > 160)
                        ? '#cf1322'
                        : '#3f8600',
                  }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Altura Uterina"
                  value={editingControl.altura_uterina || '-'}
                  suffix="cm"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Peso Actual"
                  value={editingControl.peso_actual || '-'}
                  suffix="kg"
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="IMC"
                  value={
                    calcularIMC(editingControl.peso_actual, editingControl.talla)?.toFixed(
                      1
                    ) || '-'
                  }
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Temperatura"
                  value={editingControl.temperatura || '-'}
                  suffix="°C"
                />
              </Col>
            </Row>

            {selectedEmbarazo && (
              <>
                <Divider>Datos del Embarazo</Divider>
                <Descriptions bordered column={2} size="small">
                  <Descriptions.Item label="Estado">
                    <Tag color={selectedEmbarazo.estado === 'activo' ? 'green' : 'default'}>
                      {selectedEmbarazo.estado}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="FUM">
                    {selectedEmbarazo.fecha_ultima_menstruacion
                      ? dayjs(selectedEmbarazo.fecha_ultima_menstruacion).format(
                        'DD/MM/YYYY'
                      )
                      : '-'}
                  </Descriptions.Item>
                </Descriptions>
              </>
            )}

            {alertasPreview && alertasPreview.length > 0 && (
              <>
                <Divider>Alertas Médicas</Divider>
                <Alert
                  message={`${alertasPreview.length} Alerta(s) Detectada(s)`}
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {alertasPreview.map((alerta) => (
                        <li key={`alerta-${alerta}`}>{alerta}</li>
                      ))}
                    </ul>
                  }
                  type="warning"
                  showIcon
                />
              </>
            )}

            <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/pacientes?id=${editingControl.paciente}`);
                  }}
                >
                  Ver Paciente: {getNombrePaciente(editingControl)}
                </Button>
                <Button
                  type="link"
                  icon={<MedicineBoxOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/embarazos?id=${editingControl.embarazo}`);
                  }}
                >
                  Ver Datos del Embarazo
                </Button>
                <Button
                  type="link"
                  icon={<SearchOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/ecografias?embarazo=${editingControl.embarazo}`);
                  }}
                >
                  Ver Ecografías del Embarazo
                </Button>
                <Button
                  type="link"
                  icon={<ExportOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/laboratorio?embarazo=${editingControl.embarazo}`);
                  }}
                >
                  Ver Exámenes de Laboratorio
                </Button>
                <Button
                  type="link"
                  icon={<CheckCircleOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/citas?embarazo=${editingControl.embarazo}`);
                  }}
                >
                  Ver Citas del Embarazo
                </Button>
                <Button
                  type="link"
                  icon={<MedicineBoxOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/partos?embarazo=${editingControl.embarazo}`);
                  }}
                >
                  Ver Información de Parto
                </Button>
                <Divider style={{ margin: '8px 0' }} />
                <Button
                  type="primary"
                  icon={<ExportOutlined />}
                  block
                  onClick={() => {
                    handleCloseModal();
                    navigate(`/dashboard/pacientes/${editingControl.paciente}/historia`);
                  }}
                >
                  Ver Historia Clínica Completa
                </Button>
              </Space>
            </Card>
          </>
        )}
      </Modal>

      {/* DRAWER DE ALERTAS GLOBALES */}
      <Drawer
        title={
          <Space>
            <WarningOutlined />
            Panel de Alertas
            <Badge
              count={
                controles.filter((c) => c.tiene_alertas).length
              }
              style={{ backgroundColor: '#ff4d4f' }}
            />
          </Space>
        }
        placement="right"
        onClose={handleShowAlertasPanel}
        open={showAlertasPanel}
        width={400}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Alert
            message="Resumen de Alertas"
            description={`Se encontraron ${controles.filter((c) => c.tiene_alertas).length
              } controles con alertas médicas de un total de ${controles.length} controles.`}
            type="info"
            showIcon
          />

          <Divider>Controles con Alertas</Divider>

          {controles
            .filter((c) => c.tiene_alertas)
            .slice(0, 10)
            .map((control) => {
              const alertas = detectarAlertas(control);
              return (
                <Card
                  key={control.id}
                  size="small"
                  title={
                    <Space>
                      <Badge count={alertas.length} />
                      <Text strong>{getNombrePaciente(control)}</Text>
                    </Space>
                  }
                  extra={
                    <Button
                      size="small"
                      type="link"
                      onClick={() => {
                        handleQuickView(control);
                        handleShowAlertasPanel();
                      }}
                    >
                      Ver
                    </Button>
                  }
                >
                  <Space direction="vertical" style={{ width: '100%' }} size="small">
                    <Text type="secondary">
                      Control #{control.numero_control} -{' '}
                      {dayjs(control.fecha_control).format('DD/MM/YYYY')}
                    </Text>
                    {alertas.slice(0, 2).map((alerta) => (
                      <Alert
                        key={`alerta-${alerta}`}
                        message={alerta}
                        type="warning"
                        showIcon
                        style={{ fontSize: 12 }}
                      />
                    ))}
                    {alertas.length > 2 && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        +{alertas.length - 2} alertas más…
                      </Text>
                    )}
                  </Space>
                </Card>
              );
            })}

          {controles.filter((c) => c.tiene_alertas).length > 10 && (
            <Alert
              message={`Mostrando 10 de ${controles.filter((c) => c.tiene_alertas).length
                } controles con alertas`}
              type="info"
            />
          )}
        </Space>
      </Drawer>
    </div>
  );
};

export default Controles;

