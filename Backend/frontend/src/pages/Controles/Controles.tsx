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
  Empty,
  Table,
  Button,
  Input,
  Space,
  Card,
  Tag,
  Typography,
  Badge,
  Alert,
  Form,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import {
  PlusOutlined,
  SearchOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  FilterOutlined,
  ExportOutlined,
} from '@ant-design/icons';
// Recharts removed - not used in this component
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { controlesService, ControlPrenatal } from '../../services/controlesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import {
  filtrosReducer, uiReducer, initialUIState,
} from './controlesReducers';
import {
  detectarAlertas as detectarAlertasUtil,
  calcularEdadGestacional as calcularEdadGestacionalUtil,
  calcularIMC as calcularIMCUtil,
  clasificarIMC as clasificarIMCUtil,
} from './controlesUtils';
import { buildControlesColumns } from './controlesColumns';
import FiltrosDrawer from './components/FiltrosDrawer';
import VistaRapidaModal from './components/VistaRapidaModal';
import AlertasPanelDrawer from './components/AlertasPanelDrawer';
import '../Embarazos/paginaClinica.css';
import './Controles.css';


const { Title } = Typography;

const Controles: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal, notification } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();

  const [ui, dispatchUI] = useReducer(uiReducer, initialUIState);
  const {
    modalVisible, editingControl, searchText, alertasPreview,
    selectedEmbarazo, lastLoaded, filtrosDrawerVisible,
    formHasChanges, autoSaveEnabled, showAlertasPanel, controlVistaRapida
  } = ui;
  const [form] = Form.useForm();

  const [filtrosAvanzados, dispatchFiltros] = useReducer(filtrosReducer, {});

  // Búsqueda, filtros y cifras los resuelve el SERVIDOR. Antes se bajaban
  // TODOS los controles, embarazos y pacientes (una petición por cada 200 de
  // cada uno) y se filtraba en el navegador; «Mostrar TODOS» pedía 10.000 filas.
  const filtrosServidor = useMemo(() => {
    const t = filtrosAvanzados.trimestre;
    return {
      fecha_control__gte: filtrosAvanzados.fechaDesde?.format('YYYY-MM-DD'),
      fecha_control__lte: filtrosAvanzados.fechaHasta?.format('YYYY-MM-DD'),
      alerta_critica: filtrosAvanzados.conAlertas === undefined || filtrosAvanzados.conAlertas === null
        ? undefined : String(filtrosAvanzados.conAlertas),
      // Mismos cortes que el filtro: 1.º hasta la 13, 2.º 14-27, 3.º desde 28.
      semanas_min: t === 2 ? 14 : t === 3 ? 28 : undefined,
      semanas_max: t === 1 ? 13 : t === 2 ? 27 : undefined,
    };
  }, [filtrosAvanzados]);
  const listado = useListadoServidor<ControlPrenatal>('/controles/', {
    filtros: filtrosServidor, busqueda: searchText, ordenInicial: '-fecha_control',
  });
  const { parametros, recargar } = listado;
  const loading = listado.cargando;
  const [resumen, setResumen] = useState<{ total: number; con_alertas: number; alertas_recientes: ControlPrenatal[] }>(
    { total: 0, con_alertas: 0, alertas_recientes: [] });
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get('/controles/resumen/', { params: parametros() });
      setResumen(r.data);
      dispatchUI({ type: 'SET_LAST_LOADED', payload: dayjs().format('DD/MM/YYYY HH:mm:ss') });
    } catch {
      setResumen({ total: 0, con_alertas: 0, alertas_recientes: [] });
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);
  const loadData = useCallback(() => { recargar(); cargarResumen(); }, [recargar, cargarResumen]);

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
  const detectarAlertas = useCallback((values: any): string[] => detectarAlertasUtil(values), []);

  // ========== CALCULAR EDAD GESTACIONAL DESDE FUM ==========
  const calcularEdadGestacional = useCallback((fum: string) => calcularEdadGestacionalUtil(fum), []);

  // ========== CÁLCULO DE IMC MATERNO ==========
  const calcularIMC = useCallback(
    (peso: number | null | undefined, talla: number | null | undefined): number | null =>
      calcularIMCUtil(peso, talla),
    []
  );

  // ========== CLASIFICACIÓN DE IMC ==========
  const clasificarIMC = useCallback(
    (imc: number | null): { texto: string; color: string } => clasificarIMCUtil(imc),
    []
  );

  // El serializer trae `id_clinico`, `paciente_nombre` y `embarazo_info`.
  const getIdClinicoPaciente = useCallback(
    (control: ControlPrenatal): string =>
      (control as any).id_clinico || (control as any).embarazo_info?.id_clinico || '-',
    [],
  );
  const getNombrePaciente = useCallback(
    (control: ControlPrenatal): string =>
      (control as any).paciente_nombre || (control as any).embarazo_info?.paciente_nombre || 'Paciente no disponible',
    [],
  );

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
  // Excel desde el SERVIDOR con todos los controles filtrados (y auditado).
  const handleExportExcel = () => {
    descargarArchivo(`/controles/exportar-excel/${aQuery(parametros())}`, `controles_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`)
      .catch(() => message.error('No se pudo generar el Excel de controles'));
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
        className: 'capa-clinica',
        title: '⚠️ ¿Confirmar eliminación permanente?',
        content: (
          <div>
            <p><strong>Se eliminará el control prenatal:</strong></p>
            <ul className="u-ml-5">
              <li>Paciente: {control.paciente_nombre}</li>
              <li>Control #{control.numero_control}</li>
              <li>Fecha: {control.fecha_control}</li>
              <li>Semanas gestación: {control.semanas_gestacion}</li>
            </ul>
            <p className="u-c-peligro u-fuerte u-mt-4">
              ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
            </p>
            <p className="u-mt-4">
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

      dispatchUI({ type: 'SET_SELECTED_EMBARAZO', payload: (control as any).embarazo_info || null });

      const alertas = detectarAlertas(control);
      dispatchUI({ type: 'SET_ALERTAS_PREVIEW', payload: alertas });

      message.info(`Mostrando vista rápida del control #${control.numero_control}`);
    },
    [detectarAlertas, message]
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

  // ========== COLUMNAS DE LA TABLA ==========
  // ✅ FIX: Memoizado para evitar recreación en cada render (evita loop infinito)
  const columns = useMemo(() => buildControlesColumns({
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
    canDelete,
  }), [
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
    <div className="pagina-clinica controles-page page-container">
      {/* Encabezado de página */}
      <div className="pc-cabecera">
        <div className="pc-cabecera__texto">
          <Title level={2} className="pc-cabecera__titulo">
            <MedicineBoxOutlined className="pc-cabecera__icono" /> Controles Prenatales
          </Title>
          <p className="pc-cabecera__descripcion">Gestión y seguimiento de controles</p>
        </div>
        <div className="pc-cabecera__acciones">
          <Badge dot={showAlertasPanel}>
            <Button
              icon={<WarningOutlined />}
              onClick={handleShowAlertasPanel}
              danger={showAlertasPanel}
            >
              Alertas
            </Button>
          </Badge>
          <Badge dot={autoSaveEnabled} color="var(--color-exito)">
            <Button
              icon={<CheckCircleOutlined />}
              onClick={handleToggleAutoSave}
              aria-pressed={autoSaveEnabled}
              className={autoSaveEnabled ? 'controles-autoguardado--activo' : undefined}
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
            disabled={resumen.total === 0}
          >
            Exportar Excel
          </Button>
          {canAdd('controlprenatal') && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Nuevo Control
            </Button>
          )}
        </div>
      </div>

      <Card>
        <div className="pc-barra">
          <div className="pc-barra__filtros">
            <Input
              className="pc-barra__buscar controles-buscar"
              placeholder="Buscar por paciente (nombre o CI), ID clínico..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => dispatchUI({ type: 'SET_SEARCH_TEXT', payload: e.target.value })}
              allowClear
            />
          </div>
          <Space wrap size={[8, 8]}>
            <Tag className="cifra">
              Total: {resumen.total.toLocaleString('es-BO')}
            </Tag>
            {resumen.con_alertas > 0 && <Tag color="error" className="cifra">Con alertas: {resumen.con_alertas.toLocaleString('es-BO')}</Tag>}
            {lastLoaded && (
              <Tag>Última carga: {lastLoaded}</Tag>
            )}
          </Space>
        </div>
        {listado.error && <Alert type="error" showIcon message={listado.error} className="u-mb-3" />}
        <Table
          columns={columns}
          dataSource={listado.datos}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay controles prenatales registrados" /> }}
          rowKey="id"
          loading={loading}
          pagination={listado.paginacion}
          onChange={listado.onChange}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* DRAWER DE FILTROS */}
      <FiltrosDrawer
        filtrosDrawerVisible={filtrosDrawerVisible}
        formHasChanges={formHasChanges}
        form={form}
        onClose={() => dispatchUI({ type: 'SET_FILTROS_DRAWER_VISIBLE', payload: false })}
        handleFormChange={handleFormChange}
        dispatchFiltros={dispatchFiltros}
        dispatchUI={dispatchUI}
      />

      {/* MODAL DE VISTA RÁPIDA */}
      <VistaRapidaModal
        modalVisible={modalVisible}
        editingControl={editingControl}
        controlVistaRapida={controlVistaRapida}
        selectedEmbarazo={selectedEmbarazo}
        alertasPreview={alertasPreview}
        handleCloseModal={handleCloseModal}
        handleEdit={handleEdit}
        navigate={navigate}
        getNombrePaciente={getNombrePaciente}
        getIdClinicoPaciente={getIdClinicoPaciente}
        getEdadGestacional={getEdadGestacional}
        getPresionArterial={getPresionArterial}
        calcularIMC={calcularIMC}
      />

      {/* DRAWER DE ALERTAS GLOBALES */}
      <AlertasPanelDrawer
        showAlertasPanel={showAlertasPanel}
        onClose={handleShowAlertasPanel}
        total={resumen.total}
        totalConAlertas={resumen.con_alertas}
        controlesConAlertas={resumen.alertas_recientes}
        detectarAlertas={detectarAlertas}
        getNombrePaciente={getNombrePaciente}
        handleQuickView={handleQuickView}
      />
    </div>
  );
};

export default Controles;
