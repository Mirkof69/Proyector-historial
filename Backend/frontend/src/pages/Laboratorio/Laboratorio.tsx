/**
 * =============================================================================
 * LABORATORIO - LISTA COMPLETA
 * =============================================================================
 * Lista de todos los exámenes de laboratorio registrados
 * Con filtros avanzados, estadísticas y alertas
 * =============================================================================
 */

import React, { useRef, useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  Badge,
  Typography,
} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  ExclamationCircleOutlined,
  CalendarOutlined,
  UserOutlined,
  WarningOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { laboratorioService, ExamenLaboratorio } from '../../services/laboratorioService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { exportarExcel } from '../../utils/excelExport';
import { useAntdApp } from '../../hooks/useMessage';
import { GlobalLoader } from '../../components/common/GlobalLoader';

const { Text } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

interface FiltrosState {
  busqueda: string;
  filtroCategoria: string | undefined;
  filtroEstado: string | undefined;
  filtroFecha: [dayjs.Dayjs, dayjs.Dayjs] | null;
}

type FiltrosAction =
  | { type: 'SET_BUSQUEDA'; payload: string }
  | { type: 'SET_CATEGORIA'; payload: string | undefined }
  | { type: 'SET_ESTADO'; payload: string | undefined }
  | { type: 'SET_FECHA'; payload: [dayjs.Dayjs, dayjs.Dayjs] | null }
  | { type: 'LIMPIAR' };

const filtrosReducer = (state: FiltrosState, action: FiltrosAction): FiltrosState => {
  switch (action.type) {
    case 'SET_BUSQUEDA': return { ...state, busqueda: action.payload };
    case 'SET_CATEGORIA': return { ...state, filtroCategoria: action.payload };
    case 'SET_ESTADO': return { ...state, filtroEstado: action.payload };
    case 'SET_FECHA': return { ...state, filtroFecha: action.payload };
    case 'LIMPIAR': return { busqueda: '', filtroCategoria: undefined, filtroEstado: undefined, filtroFecha: null };
    default: return state;
  }
};

const Laboratorio: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [loading, setLoading] = useState(false);
  const examenesRef = useRef<ExamenLaboratorio[]>([]);
  const [filtros, dispatchFiltros] = useReducer(filtrosReducer, {
    busqueda: '',
    filtroCategoria: undefined,
    filtroEstado: undefined,
    filtroFecha: null,
  });

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================

  const calcularEstadisticas = useCallback((data: ExamenLaboratorio[]) => {
    return {
      total: data.length,
      solicitados: data.filter((e) => e.estado === 'solicitado').length,
      en_proceso: data.filter((e) => e.estado === 'en_proceso').length,
      completados: data.filter((e) => e.estado === 'completado').length,
      con_anormales: data.filter((e) => e.resultados_anormales && e.resultados_anormales > 0).length,
      con_criticos: data.filter((e) => e.resumen && e.resumen.criticos > 0).length,
    };
  }, []);

  const estadisticas = useMemo(() => calcularEstadisticas(examenesRef.current), [calcularEstadisticas]);

  const cargarExamenes = useCallback(async () => {
    setLoading(true);

    try {

      // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
      const firstPage = await laboratorioService.api.get('/laboratorios/examenes/?page=1&limit=200');

      const totalCount = firstPage.data.count || 0;
      const totalPages = Math.ceil(totalCount / 200);


      // 🚀 PASO 2: Crear array de promesas para TODAS las páginas
      const promises = Array.from({ length: totalPages }, (_, i) =>
        laboratorioService.api.get(`/laboratorios/examenes/?page=${i + 1}&limit=200`)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const responses = await Promise.all(promises);

      // 🚀 PASO 4: Combinar todos los resultados y agregar rowKey único
      let index = 0;
      const allExamenes = [];
      for (const res of responses) {
        const results = res.data.results || [];
        for (const item of results) {
          allExamenes.push({
            ...item,
            _uniqueRowKey: `laboratorio-${item.id}-${index}-${Date.now()}`
          });
          index++;
        }
      }

      examenesRef.current = allExamenes;
    } catch (error) {
      message.error('Error al cargar los exámenes de laboratorio');
      examenesRef.current = [];
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarExamenes();
  }, [cargarExamenes]);

  // ==========================================================================
  // FILTROS
  // ==========================================================================
  const examenesFiltrados = useMemo(() => {
    let resultado = [...examenesRef.current];

    if (filtros.busqueda) {
      resultado = resultado.filter(
        (examen) =>
          examen.paciente_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          examen.tipo_examen_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          examen.indicaciones?.toLowerCase().includes(filtros.busqueda.toLowerCase())
      );
    }

    if (filtros.filtroCategoria) {
      resultado = resultado.filter((examen) => examen.categoria === filtros.filtroCategoria);
    }

    if (filtros.filtroEstado) {
      resultado = resultado.filter((examen) => examen.estado === filtros.filtroEstado);
    }

    if (filtros.filtroFecha) {
      resultado = resultado.filter((examen) => {
        const fecha = dayjs(examen.fecha_solicitud);
        return fecha.isAfter(filtros.filtroFecha![0]) && fecha.isBefore(filtros.filtroFecha![1]);
      });
    }

    return resultado;
  }, [filtros]);

  const limpiarFiltros = useCallback(() => {
    dispatchFiltros({ type: 'LIMPIAR' });
  }, []);

  // ==========================================================================
  // ACCIONES
  // ==========================================================================
  const handleNuevo = useCallback(() => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_NUEVO);
  }, [navigate]);

  const handleVer = useCallback((id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_DETALLE(id));
  }, [navigate]);

  const handleEditar = useCallback((id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_EDITAR(id));
  }, [navigate]);

  const handleEliminar = useCallback((examen: any) => {
    modal.confirm({
      title: '⚠️ ¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará el examen de laboratorio:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {examen.paciente_nombre || 'No especificado'}</li>
            <li>Tipo de Examen: {examen.tipo_examen_nombre || 'No especificado'}</li>
            <li>Fecha Solicitud: {examen.fecha_solicitud ? dayjs(examen.fecha_solicitud).format('DD/MM/YYYY') : 'No especificado'}</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p style={{ marginTop: 16 }}>
            Se perderán todos los datos de este examen de laboratorio, incluyendo resultados, valores de referencia e interpretaciones.
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await laboratorioService.delete(examen.id);
          message.success('Examen eliminado correctamente');
          cargarExamenes();
        } catch (error) {
          message.error('Error al eliminar el examen');
        }
      },
    });
  }, [modal, message, cargarExamenes]);

  const handleExportExcel = useCallback(() => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'tipo_examen_nombre': 'Tipo Examen',
        'fecha_solicitud': 'Fecha Solicitud',
        'hemoglobina': 'Hemoglobina',
        'hematocrito': 'Hematocrito',
        'glucosa': 'Glucosa',
        'grupo_sanguineo': 'Grupo Sang.',
        'factor_rh': 'RH',
        'vih': 'VIH',
        'vdrl': 'VDRL',
        'orina_proteinas': 'Proteínas',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        examenesFiltrados,
        columnas,
        {
          filename: `laboratorio_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Laboratorio',
          title: `Exámenes de Laboratorio - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  }, [examenesFiltrados, message]);

  // ==========================================================================
  // COLUMNAS DE LA TABLA
  // ==========================================================================
  const columns = useMemo(() => [
    {
      title: 'Paciente',
      key: 'paciente',
      width: 200,
      render: (_: any, record: ExamenLaboratorio) => (
        <Space direction="vertical" size={0}>
          <Space>
            <UserOutlined style={{ color: '#1890ff' }} />
            <span style={{ fontWeight: 500 }}>{record.paciente_nombre || 'No especificado'}</span>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Tipo de Examen',
      dataIndex: 'tipo_examen_nombre',
      key: 'tipo_examen',
      render: (text: string, record: ExamenLaboratorio) => (
        <Space direction="vertical" size={0}>
          <Text>{text || '-'}</Text>
          {record.categoria && (
            <Tag color="purple">
              {record.categoria}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Fecha Solicitud',
      dataIndex: 'fecha_solicitud',
      key: 'fecha_solicitud',
      width: 140,
      sorter: (a: ExamenLaboratorio, b: ExamenLaboratorio) =>
        dayjs(a.fecha_solicitud).unix() - dayjs(b.fecha_solicitud).unix(),
      render: (fecha: string) => (
        <Space>
          <CalendarOutlined />
          {dayjs(fecha).format('DD/MM/YYYY')}
        </Space>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 120,
      render: (estado: string) => {
        const colors = {
          solicitado: 'orange',
          en_proceso: 'blue',
          completado: 'green',
          cancelado: 'red',
        };
        return <Tag color={colors[estado as keyof typeof colors] || 'default'}>{estado?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Prioridad',
      dataIndex: 'prioridad',
      key: 'prioridad',
      width: 100,
      render: (prioridad: string) => {
        const colors = {
          normal: 'default',
          urgente: 'orange',
          stat: 'red',
        };
        return <Tag color={colors[prioridad as keyof typeof colors] || 'default'}>{prioridad?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Resultados',
      key: 'resultados',
      width: 120,
      render: (_: any, record: ExamenLaboratorio) => {
        if (record.resumen) {
          const { criticos, anormales } = record.resumen;
          if (criticos > 0) {
            return (
              <Tooltip title={`${criticos} crítico(s)`}>
                <Badge count={criticos} showZero>
                  <Tag color="red" icon={<WarningOutlined />}>
                    CRÍTICOS
                  </Tag>
                </Badge>
              </Tooltip>
            );
          }
          if (anormales > 0) {
            return (
              <Tooltip title={`${anormales} anormal(es)`}>
                <Badge count={anormales}>
                  <Tag color="orange">ANORMALES</Tag>
                </Badge>
              </Tooltip>
            );
          }
          return <Tag color="green">NORMALES</Tag>;
        }
        return <Text type="secondary">Sin resultados</Text>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: ExamenLaboratorio) => (
        <Space size="small">
          <Tooltip title="Ver detalle">
            <Button type="link" icon={<EyeOutlined />} onClick={() => handleVer(record.id!)} />
          </Tooltip>
          {canChange('examen') && (
            <Tooltip title="Editar">
              <Button type="link" icon={<EditOutlined />} onClick={() => handleEditar(record.id!)} />
            </Tooltip>
          )}
          {canDelete('examen') && (
            <Tooltip title="Eliminar">
              <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleEliminar(record)} />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ], [canChange, canDelete, handleVer, handleEditar, handleEliminar]);

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading && examenesRef.current.length === 0) {
    return <GlobalLoader tip="Cargando exámenes de laboratorio…" />;
  }

  return (
    <div className="laboratorio-container animate-fade-in">
      {/* ESTADÍSTICAS */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Total Exámenes"
              value={estadisticas.total}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Solicitados"
              value={estadisticas.solicitados}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="En Proceso"
              value={estadisticas.en_proceso}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Completados"
              value={estadisticas.completados}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Con Anormales"
              value={estadisticas.con_anormales}
              valueStyle={{ color: '#faad14' }}
              prefix={<ExclamationCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6} lg={4}>
          <Card>
            <Statistic
              title="Con Críticos"
              value={estadisticas.con_criticos}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* TABLA */}
      <Card
        title={
          <Space>
            <ExperimentOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <span>Exámenes de Laboratorio</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={cargarExamenes}>
              Actualizar
            </Button>
            <Button icon={<FileExcelOutlined />} onClick={handleExportExcel}>
              Exportar Excel
            </Button>
            {canAdd('examen') && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
                Nuevo Examen
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
                placeholder="Buscar paciente o examen..."
                prefix={<SearchOutlined />}
                value={filtros.busqueda}
                onChange={(e) => dispatchFiltros({ type: 'SET_BUSQUEDA', payload: e.target.value })}
                allowClear
              />
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Select
                placeholder="Categoría"
                style={{ width: '100%' }}
                value={filtros.filtroCategoria}
                onChange={(val) => dispatchFiltros({ type: 'SET_CATEGORIA', payload: val })}
                allowClear
              >
                <Option value="hematologia">Hematología</Option>
                <Option value="bioquimica">Bioquímica</Option>
                <Option value="inmunologia">Inmunología</Option>
                <Option value="microbiologia">Microbiología</Option>
                <Option value="urinalisis">Urianálisis</Option>
                <Option value="serologia">Serología</Option>
                <Option value="hormonal">Hormonal</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <Select
                placeholder="Estado"
                style={{ width: '100%' }}
                value={filtros.filtroEstado}
                onChange={(val) => dispatchFiltros({ type: 'SET_ESTADO', payload: val })}
                allowClear
              >
                <Option value="solicitado">Solicitado</Option>
                <Option value="en_proceso">En Proceso</Option>
                <Option value="completado">Completado</Option>
                <Option value="cancelado">Cancelado</Option>
              </Select>
            </Col>
            <Col xs={24} sm={12} md={5}>
              <RangePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                value={filtros.filtroFecha}
                onChange={(dates) => dispatchFiltros({ type: 'SET_FECHA', payload: dates as [dayjs.Dayjs, dayjs.Dayjs] })}
              />
            </Col>
            <Col xs={24} sm={12} md={1}>
              <Button icon={<FilterOutlined />} onClick={limpiarFiltros} block>
                Limpiar
              </Button>
            </Col>
          </Row>
        </Space>

        <Table
          columns={columns}
          dataSource={examenesFiltrados}
          rowKey={(record: any) => record._uniqueRowKey || `laboratorio-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} exámenes`,
          }}
          scroll={{ x: 1300 }}
          bordered
        />
      </Card>
    </div>
  );
};

export default Laboratorio;
