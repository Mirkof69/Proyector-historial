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
  Row,
  Col,
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
  ReloadOutlined,
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
import dayjs from 'dayjs';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import { exportarExcel } from '../../utils/excelExport';
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

dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);

const { Title, Text } = Typography;

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

      setControles(allControles);
      setEmbarazos(allEmbarazos.filter((e: Embarazo) => e.estado === 'activo'));
      setPacientes(allPacientes);
      dispatchUI({ type: 'SET_LAST_LOADED', payload: dayjs().format('DD/MM/YYYY HH:mm:ss') });
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
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay controles prenatales registrados" /> }}
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
        controles={controles}
        detectarAlertas={detectarAlertas}
        getNombrePaciente={getNombrePaciente}
        handleQuickView={handleQuickView}
      />
    </div>
  );
};

export default Controles;
