/**
 * =============================================================================
 * ECOGRAFÍAS - LISTA COMPLETA
 * =============================================================================
 * Lista de todas las ecografías registradas en el sistema.
 * - Filtros por tipo, trimestre, fecha
 * - Búsqueda por paciente
 * - Paginación y ordenamiento
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import { exportarExcel } from '../../utils/excelExport';
import {Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Modal,
  Row,
  Col,
  Statistic,
  Badge,
  Typography,
  Drawer,
  Descriptions,
  Alert,
  Divider} from "antd";
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  FileImageOutlined,
  ExclamationCircleOutlined,
  CalendarOutlined,
  UserOutlined,
  FileExcelOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import DICOMViewer from '../../components/DICOMViewer';
import PDFGenerator from '../../components/PDFGenerator';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../services/api';
import './Ecografias.css';

const { Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface FiltrosEcografiaState {
  busqueda: string;
  filtroTipo: string;
  filtroFecha: [dayjs.Dayjs, dayjs.Dayjs] | null;
}

type FiltrosEcografiaAction =
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_TIPO'; payload: string }
  | { type: 'SET_FECHA'; payload: [dayjs.Dayjs, dayjs.Dayjs] | null }
  | { type: 'LIMPIAR' };

const filtrosEcografiaReducer = (state: FiltrosEcografiaState, action: FiltrosEcografiaAction): FiltrosEcografiaState => {
  switch (action.type) {
    case 'SET_BUSQUEDA': return { ...state, busqueda: action.payload };
    case 'SET_TIPO': return { ...state, filtroTipo: action.payload };
    case 'SET_FECHA': return { ...state, filtroFecha: action.payload };
    case 'LIMPIAR': return { busqueda: '', filtroTipo: '', filtroFecha: null };
    default: return state;
  }
};

const calcularEstadisticas = (ecografias: any[]) => ({
  total: ecografias.length,
  primerTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) < 14).length,
  segundoTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) >= 14 && (e.edad_gestacional_semanas || 0) < 28).length,
  tercerTrimestre: ecografias.filter((e: any) => (e.edad_gestacional_semanas || 0) >= 28).length,
  conAlertas: ecografias.filter((e: any) => e.alertas && e.alertas.length > 0).length,
});

const Ecografias: React.FC = () => {
  const { message, modal } = useAntdApp();
  const navigate = useNavigate();
  const { canAdd, canChange, canDelete } = usePermissions();
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ecografias, setEcografias] = useState<Ecografia[]>([]);
  const [filtros, dispatchFiltros] = useReducer(filtrosEcografiaReducer, {
    busqueda: '',
    filtroTipo: '',
    filtroFecha: null,
  });
  const [drawerVistaRapidaVisible, setDrawerVistaRapidaVisible] = useState(false);
  const [ecografiaSeleccionada, setEcografiaSeleccionada] = useState<Ecografia | null>(null);
  const [dicomViewerVisible, setDicomViewerVisible] = useState(false);
  const [pdfGeneratorVisible, setPdfGeneratorVisible] = useState(false);


  const estadisticas = useMemo(() => calcularEstadisticas(ecografias), [ecografias]);

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarEcografias = useCallback(async () => {
    setLoading(true);
    try {

      // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
      const firstPageResponse = await apiClient.get('/ecografias/', { params: { page: 1, limit: 200 } });
      const firstPageData = firstPageResponse.data;
      const totalEcografias = firstPageData.count || 0;
      const totalPages = Math.ceil(totalEcografias / 200);


      // 🚀 PASO 2: Crear array de promesas para TODAS las páginas
      const ecografiasPromises = Array.from({ length: totalPages }, (_, i) =>
        apiClient.get('/ecografias/', { params: { page: i + 1, limit: 200 } }).then(res => res.data)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const allResponses = await Promise.all(ecografiasPromises);

      // 🚀 PASO 4: Combinar todos los resultados y agregar _uniqueRowKey
      const allEcografias: any[] = [];
      for (const res of allResponses) {
        for (const item of res.results || []) {
          allEcografias.push({
            ...item,
            _uniqueRowKey: `ecografia-${item.id}-${allEcografias.length}-${Date.now()}`
          });
        }
      }

      setEcografias(allEcografias);
      setLoadError(null);
    } catch (error) {
      setLoadError('No se pudieron cargar las ecografías. Verifique su conexión e intente nuevamente.');
      setEcografias([]);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    cargarEcografias();
  }, [cargarEcografias]);

  const ecografiasFiltradas = useMemo(() => {
    let resultado = [...ecografias];

    if (filtros.busqueda) {
      resultado = resultado.filter(
        (eco) =>
          eco.tipo_ecografia?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.paciente_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.diagnostico?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.observaciones?.toLowerCase().includes(filtros.busqueda.toLowerCase())
      );
    }

    if (filtros.filtroTipo) {
      resultado = resultado.filter((eco) => eco.tipo_ecografia === filtros.filtroTipo);
    }

    if (filtros.filtroFecha) {
      resultado = resultado.filter((eco) => {
        const fecha = dayjs(eco.fecha_ecografia);
        return fecha.isAfter(filtros.filtroFecha![0]) && fecha.isBefore(filtros.filtroFecha![1]);
      });
    }

    return resultado;
  }, [filtros, ecografias]);

  const limpiarFiltros = () => {
    dispatchFiltros({ type: 'LIMPIAR' });
  };

  // ==========================================================================
  // ACCIONES
  // ==========================================================================
  const handleNuevo = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_NUEVO);
  };

  const handleVer = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_DETALLE(id));
  };

  // ✨ NUEVA FUNCIÓN PARA VISTA RÁPIDA CON DRAWER
  const handleVerVistaRapida = (ecografia: Ecografia) => {
    setEcografiaSeleccionada(ecografia);
    setDrawerVistaRapidaVisible(true);
  };

  const handleEditar = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(id));
  };

  const handleEliminar = (ecografia: any) => {
    modal.confirm({
      title: '⚠️ ¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará la ecografía:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {ecografia.paciente_nombre || 'No especificado'}</li>
            <li>Fecha: {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}</li>
            <li>Tipo: {ecografia.tipo_ecografia || 'No especificado'}</li>
            <li>Edad Gestacional: {ecografia.edad_gestacional_semanas || 0}+{ecografia.edad_gestacional_dias || 0} semanas</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p style={{ marginTop: 16 }}>
            Se perderán todos los datos de esta ecografía obstétrica, incluyendo mediciones fetales, diagnósticos y observaciones.
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await ecografiasService.delete(ecografia.id);
          message.success('Ecografía eliminada correctamente');
          cargarEcografias();
        } catch (error) {
          message.error('Error al eliminar la ecografía');
        }
      },
    });
  };

  const handleExportExcel = () => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'fecha_ecografia': 'Fecha',
        'tipo_ecografia': 'Tipo',
        'edad_gestacional_semanas': 'Semanas',
        'edad_gestacional_dias': 'Días',
        'peso_fetal_estimado': 'Peso Est. (g)',
        'biometria_dbp': 'DBP (mm)',
        'biometria_cc': 'CC (mm)',
        'biometria_ca': 'CA (mm)',
        'biometria_lf': 'LF (mm)',
        'liquido_amniotico': 'Líquido',
        'placenta_localizacion': 'Placenta',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        ecografias,
        columnas,
        {
          filename: `ecografias_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Ecografías',
          title: `Ecografías Obstétricas - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  };

  // ==========================================================================
  // COLUMNAS DE LA TABLA
  // ==========================================================================
  const columns = [
    {
      title: 'Paciente',
      key: 'paciente',
      width: 200,
      render: (_: any, record: Ecografia) => (
        <Space direction="vertical" size={0}>
          <Space>
            <UserOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontWeight: 500 }}>{record.paciente_nombre || 'No especificado'}</span>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_ecografia',
      key: 'fecha_ecografia',
      width: 120,
      sorter: (a: Ecografia, b: Ecografia) =>
        dayjs(a.fecha_ecografia).unix() - dayjs(b.fecha_ecografia).unix(),
      render: (fecha: string) => (
        <Space>
          <CalendarOutlined />
          {dayjs(fecha).format('DD/MM/YYYY')}
        </Space>
      ),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_ecografia',
      key: 'tipo_ecografia',
      width: 150,
      render: (tipo: string) => {
        const colores: Record<string, string> = {
          primer_trimestre: 'cyan',
          segundo_trimestre: 'blue',
          tercer_trimestre: 'purple',
          morfologica: 'green',
          doppler: 'orange',
          genetica: 'gold',
          '4d': 'magenta',
        };
        return <Tag color={colores[tipo] || 'default'}>{tipo?.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Edad Gestacional',
      key: 'edad_gestacional',
      width: 130,
      render: (_: any, record: Ecografia) => (
        <Text>
          {record.edad_gestacional_texto ||
            `${record.edad_gestacional_semanas || 0}+${record.edad_gestacional_dias || 0}`}
        </Text>
      ),
    },
    {
      title: 'Diagnóstico',
      dataIndex: 'diagnostico',
      key: 'diagnostico',
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <Text ellipsis>{text || '-'}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      width: 100,
      render: (_: any, record: Ecografia) => {
        // Determinar si hay alertas basado en FCF y vitalidad
        const tieneAlertas = !record.vitalidad_fetal ||
          (record.frecuencia_cardiaca_fetal && (record.frecuencia_cardiaca_fetal < 110 || record.frecuencia_cardiaca_fetal > 160));

        if (tieneAlertas) {
          return <Badge status="error" text="Con alertas" />;
        }
        return <Badge status="success" text="Normal" />;
      },
    },
    {
      title: 'IA',
      key: 'tiene_analisis_ia',
      width: 60,
      align: 'center' as const,
      render: (_: any, record: Ecografia) => {
        if ((record as any).tiene_analisis_ia) {
          return (
            <Tooltip title="Tiene análisis IA">
              <RobotOutlined style={{ color: '#722ed1', fontSize: 18 }} />
            </Tooltip>
          );
        }
        return null;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: Ecografia) => (
        <Space size="small">
          <Tooltip title="Ver detalle">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => handleVerVistaRapida(record)}
            />
          </Tooltip>
          {canChange('ecografia') && (
            <Tooltip title="Editar">
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEditar(record.id!)}
              />
            </Tooltip>
          )}
          {canDelete('ecografia') && (
            <Tooltip title="Eliminar">
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleEliminar(record)}
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="ecografias-container page-container">
      {/* ESTADÍSTICAS */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Ecografías"
              value={estadisticas.total}
              prefix={<FileImageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Primer Trimestre"
              value={estadisticas.primerTrimestre}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Segundo Trimestre"
              value={estadisticas.segundoTrimestre}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Tercer Trimestre"
              value={estadisticas.tercerTrimestre}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* TABLA */}
      <Card
        title={
          <Space>
            <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span>Ecografías Registradas</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={cargarEcografias}>
              Actualizar
            </Button>
            <Button
              icon={<FileExcelOutlined />}
              onClick={handleExportExcel}
              style={{ backgroundColor: '#52c41a', color: 'white', borderColor: '#52c41a' }}
            >
              Exportar Excel
            </Button>
            <Button
              icon={<FileImageOutlined />}
              onClick={() => setDicomViewerVisible(true)}
              style={{ backgroundColor: '#722ed1', color: 'white', borderColor: '#722ed1' }}
            >
              🔬 Visor DICOM
            </Button>
            <Button
              icon={<FileImageOutlined />}
              onClick={() => setPdfGeneratorVisible(true)}
              style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
            >
              📄 Generar PDF
            </Button>
            {canAdd('ecografia') && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
                Nueva Ecografía
              </Button>
            )}
          </Space>
        }
      >
        {/* FILTROS */}
        <Space direction="vertical" size="middle" style={{ width: '100%', marginBottom: 16 }}>
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="Buscar..."
                prefix={<SearchOutlined />}
                value={filtros.busqueda}
                onChange={(e) => dispatchFiltros({ type: 'SET_BUSQUEDA', payload: e.target.value })}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Select
                placeholder="Filtrar por tipo"
                style={{ width: '100%' }}
                value={filtros.filtroTipo}
                onChange={(val) => dispatchFiltros({ type: 'SET_TIPO', payload: val })}
                allowClear
              >
                <Option value="primer_trimestre">Primer Trimestre</Option>
                <Option value="segundo_trimestre">Segundo Trimestre</Option>
                <Option value="tercer_trimestre">Tercer Trimestre</Option>
                <Option value="morfologica">Morfológica</Option>
                <Option value="doppler">Doppler</Option>
                <Option value="genetica">Genética</Option>
                <Option value="4d">4D</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <RangePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                value={filtros.filtroFecha}
                onChange={(dates) => dispatchFiltros({ type: 'SET_FECHA', payload: dates as [dayjs.Dayjs, dayjs.Dayjs] })}
              />
            </Col>
            <Col xs={24} sm={12} md={2}>
              <Button icon={<FilterOutlined />} onClick={limpiarFiltros} block>
                Limpiar
              </Button>
            </Col>
          </Row>
        </Space>

        {loadError && (
          <Alert
            type="error"
            showIcon
            message="Error al cargar las ecografías"
            description={loadError}
            action={
              <Button size="small" icon={<ReloadOutlined />} onClick={cargarEcografias}>
                Reintentar
              </Button>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        <Table
          columns={columns}
          dataSource={ecografiasFiltradas}
          rowKey={(record: any) => record._uniqueRowKey || `ecografia-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} ecografías`,
          }}
          scroll={{ x: 1200 }}
          bordered
        />
      </Card>

      {/* ========================================================================
          DRAWER DE VISTA RÁPIDA CON NAVEGACIÓN CROSS-MODULE
         ======================================================================== */}
      <Drawer
        title={
          <Space>
            <FileImageOutlined />
            Vista Rápida de Ecografía
            {ecografiaSeleccionada && (
              <Tag color="blue">{ecografiaSeleccionada.tipo_ecografia}</Tag>
            )}
          </Space>
        }
        placement="right"
        width={600}
        onClose={() => setDrawerVistaRapidaVisible(false)}
        open={drawerVistaRapidaVisible}
        extra={
          <Space>
            <Button
              icon={<EyeOutlined />}
              onClick={() => {
                if (ecografiaSeleccionada) {
                  setDrawerVistaRapidaVisible(false);
                  handleVer(ecografiaSeleccionada.id!);
                }
              }}
            >
              Ver Página Completa
            </Button>
            {canChange('ecografia') && (
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => {
                  if (ecografiaSeleccionada) {
                    setDrawerVistaRapidaVisible(false);
                    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(ecografiaSeleccionada.id!));
                  }
                }}
              >
                Editar Completo
              </Button>
            )}
          </Space>
        }
      >
        {ecografiaSeleccionada && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Descriptions title="Información de la Ecografía" bordered column={1} size="small">
              <Descriptions.Item label="Paciente">
                <strong>{ecografiaSeleccionada.paciente_nombre || 'No especificado'}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="Fecha">
                {dayjs(ecografiaSeleccionada.fecha_ecografia).format('DD/MM/YYYY')}
              </Descriptions.Item>
              <Descriptions.Item label="Tipo">
                <Tag color="blue">{ecografiaSeleccionada.tipo_ecografia}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Edad Gestacional">
                {ecografiaSeleccionada.edad_gestacional_semanas} semanas
              </Descriptions.Item>
              {ecografiaSeleccionada.observaciones && (
                <Descriptions.Item label="Observaciones">
                  {ecografiaSeleccionada.observaciones}
                </Descriptions.Item>
              )}
            </Descriptions>

            <Divider orientation="left">🔗 Acceso Rápido a Módulos</Divider>
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <Button
                  type="link"
                  icon={<UserOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/pacientes?id=${ecografiaSeleccionada.paciente}`);
                  }}
                >
                  Ver Paciente: {ecografiaSeleccionada.paciente_nombre}
                </Button>
                <Button
                  type="link"
                  icon={<FileImageOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/embarazos?id=${ecografiaSeleccionada.embarazo}`);
                  }}
                >
                  Ver Datos del Embarazo
                </Button>
                <Button
                  type="link"
                  icon={<FileImageOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/controles?embarazo=${ecografiaSeleccionada.embarazo}`);
                  }}
                >
                  Ver Controles Prenatales
                </Button>
                <Button
                  type="link"
                  icon={<CalendarOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/citas?embarazo=${ecografiaSeleccionada.embarazo}`);
                  }}
                >
                  Ver Citas del Embarazo
                </Button>
                <Button
                  type="link"
                  icon={<FileImageOutlined />}
                  block
                  style={{ textAlign: 'left' }}
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/laboratorio?embarazo=${ecografiaSeleccionada.embarazo}`);
                  }}
                >
                  Ver Exámenes de Laboratorio
                </Button>
                <Divider style={{ margin: '8px 0' }} />
                <Button
                  type="primary"
                  icon={<UserOutlined />}
                  block
                  onClick={() => {
                    setDrawerVistaRapidaVisible(false);
                    navigate(`/dashboard/pacientes/${ecografiaSeleccionada.paciente}/historia`);
                  }}
                >
                  Ver Historia Clínica Completa
                </Button>
              </Space>
            </Card>
          </Space>
        )}
      </Drawer>

      {/* ✨ MODAL CON VISOR DICOM */}
      <Modal
        title="Visor de Imágenes DICOM"
        open={dicomViewerVisible}
        onCancel={() => setDicomViewerVisible(false)}
        width={1400}
        footer={null}
        style={{ top: 20 }}
      >
        {ecografiaSeleccionada && (
          <DICOMViewer
            patientName={`Paciente ID: ${ecografiaSeleccionada.paciente}`}
            studyDate={ecografiaSeleccionada.fecha_ecografia}
            modality="US"
            imageUrl="/path-to-ultrasound-image.jpg"
          />
        )}
      </Modal>

      {/* ✨ MODAL CON GENERADOR DE PDF */}
      <PDFGenerator
        open={pdfGeneratorVisible}
        onCancel={() => setPdfGeneratorVisible(false)}
        pacienteData={ecografiaSeleccionada ? { id: ecografiaSeleccionada.paciente } : null}
        embarazoData={ecografiaSeleccionada ? { id: ecografiaSeleccionada.embarazo } : null}
        moduloOrigen="ecografias"
      />
    </div>
  );
};

export default Ecografias;
