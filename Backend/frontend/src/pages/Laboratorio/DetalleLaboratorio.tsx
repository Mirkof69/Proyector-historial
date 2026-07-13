/**
 * =============================================================================
 * DETALLE DE EXAMEN DE LABORATORIO
 * =============================================================================
 * Vista completa de un examen de laboratorio con todos sus resultados
 * y evaluaciones médicas automáticas
 * =============================================================================
 */

import React, { useState, useRef, useMemo, useCallback, useEffect } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Divider,
  Spin,
  Typography,
  Badge,
  Modal,
  Table,
  Progress,
  Tooltip,
  Statistic,
  Tabs,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  UserOutlined,
  CalendarOutlined,
  LineChartOutlined,
  FormOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { laboratorioService, ExamenLaboratorio } from '../../services/laboratorioService';
import { FRONTEND_ROUTES } from '../../config/routes';
import FormularioResultados from './FormularioResultados';
import GraficoTendenciaLaboratorio from '../../components/GraficoTendenciaLaboratorio';

const { Title, Text, Paragraph } = Typography;

const tabResultadosDetallados = (
  <span>
    <ExperimentOutlined />
    Resultados Detallados
  </span>
);

const TabEstadisticasLabel = React.memo(({ count }: { count: number }) => (
  <span>
    <LineChartOutlined />
    Análisis Estadístico ({count} exámenes previos)
  </span>
));

// Función para interpretar resultados médicamente
const interpretarResultado = (record: any): string => {
  if (!record.valor_numerico || !record.rango_referencia) return '';

  // Extraer min y max del rango (ej: "70 -125 mg/dL")
  const match = record.rango_referencia.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
  if (!match) return '';

  const min = parseFloat(match[1]);
  const max = parseFloat(match[2]);
  const valor = record.valor_numerico;

  if (valor < min) {
    const diff = ((min - valor) / min * 100).toFixed(1);
    return `${diff}% por debajo del mínimo`;
  }
  if (valor > max) {
    const diff = ((valor - max) / max * 100).toFixed(1);
    return `${diff}% por encima del máximo`;
  }
  return 'Dentro del rango esperado';
};

// Función para calcular porcentaje en rango
const calcularPorcentajeEnRango = (record: any): number => {
  if (!record.valor_numerico || !record.rango_referencia) return 0;

  const match = record.rango_referencia.match(/(\d+\.?\d*)\s*-\s*(\d+\.?\d*)/);
  if (!match) return 50;

  const min = parseFloat(match[1]);
  const max = parseFloat(match[2]);
  const valor = record.valor_numerico;

  if (valor < min) return 25;
  if (valor > max) return 75;

  // Dentro del rango: calcular posición
  const posicion = ((valor - min) / (max - min)) * 100;
  return Math.min(100, Math.max(0, posicion));
};

const DetalleLaboratorio: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const loadingRef = useRef(true);
  const [examen, setExamen] = useState<ExamenLaboratorio | null>(null);
  const [estadisticas, setEstadisticas] = useState<any | null>(null);
  const [loadingEstadisticas, setLoadingEstadisticas] = useState(false);


  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    loadingRef.current = true;
    try {
      const data = await laboratorioService.getById(Number(id));
      setExamen(data);
      message.success('Datos cargados correctamente');
    } catch (error) {
      message.error('Error al cargar el examen de laboratorio');
    } finally {
      loadingRef.current = false;
    }
  }, [id, message]);

  // Cargar estadísticas del paciente
  const cargarEstadisticas = async () => {
    if (!id) return;

    setLoadingEstadisticas(true);
    try {
      const data = await laboratorioService.getEstadisticasPaciente(Number(id), 10);
      setEstadisticas(data);
    } catch (error) {
    } finally {
      setLoadingEstadisticas(false);
    }
  };

  useEffect(() => {
    if (id) cargarDatos();
  }, [id, cargarDatos]);

  // Estadísticas: cargar recién cuando el examen ya está completado. Antes se
  // evaluaba examen?.estado en el render de carga (aún null) → nunca cargaba.
  useEffect(() => {
    if (examen?.estado === 'completado') cargarEstadisticas();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examen?.estado]);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    modal.confirm({
      title: '¿Eliminar este examen?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await laboratorioService.delete(Number(id));
          message.success('Examen eliminado correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO);
        } catch (error) {
          message.error('Error al eliminar el examen');
        }
      },
    });
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loadingRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Cargando datos del examen…</div>
      </div>
    );
  }

  if (!examen) {
    return (
      <Card>
        <Alert
          message="Examen no encontrado"
          description="No se encontró el examen solicitado."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver al listado
        </Button>
      </Card>
    );
  }

  const columnsResultados = [
    {
      title: 'Parámetro',
      dataIndex: 'parametro_nombre',
      key: 'parametro',
      width: 180,
    },
    {
      title: 'Valor Obtenido',
      key: 'valor',
      width: 150,
      render: (record: any) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ fontSize: 16 }}>
            {record.valor_numerico || record.valor_texto}{' '}
            {record.unidad && record.unidad !== 'cualitativo' && `${record.unidad}`}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Rango de Referencia',
      key: 'rango',
      width: 200,
      render: (record: any) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          <Text type="secondary">{record.rango_referencia || 'N/A'}</Text>
          {record.valor_numerico && record.rango_referencia && (
            <Progress
              percent={calcularPorcentajeEnRango(record)}
              size="small"
              status={record.es_normal ? 'success' : record.es_critico ? 'exception' : 'normal'}
              showInfo={false}
            />
          )}
        </Space>
      ),
    },
    {
      title: 'Interpretación',
      key: 'interpretacion',
      width: 250,
      render: (record: any) => (
        <Space direction="vertical" size={0}>
          {record.es_critico && (
            <>
              <Tag color="red" icon={<WarningOutlined />}>CRÍTICO</Tag>
              <Text type="danger" style={{ fontSize: 12 }}>
                Requiere atención inmediata
              </Text>
            </>
          )}
          {!record.es_critico && !record.es_normal && (
            <>
              <Tag color="orange" icon={<ExclamationCircleOutlined />}>ANORMAL</Tag>
              <Text type="warning" style={{ fontSize: 12 }}>
                {interpretarResultado(record)}
              </Text>
            </>
          )}
          {record.es_normal && (
            <>
              <Tag color="green" icon={<CheckCircleOutlined />}>NORMAL</Tag>
              <Text style={{ fontSize: 12, color: '#52c41a' }}>
                Dentro del rango esperado
              </Text>
            </>
          )}
        </Space>
      ),
    },
    {
      title: 'Observaciones',
      dataIndex: 'observaciones',
      key: 'observaciones',
      render: (text: string) => text || '-',
    },
  ];


  return (
    <div className="detalle-laboratorio-container">
      {/* HEADER */}
      <Card className="header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
                Volver
              </Button>
              <Divider type="vertical" />
              <ExperimentOutlined style={{ fontSize: 24, color: '#722ed1' }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  Detalle de Examen de Laboratorio
                </Title>
                <Text type="secondary">
                  {examen.tipo_examen_info?.nombre || `Examen #${examen.id}`}
                </Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Tooltip title="Imprimir el reporte del examen de laboratorio">
                <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                  Imprimir
                </Button>
              </Tooltip>
              <Tooltip title="Editar los datos del examen">
                <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
                  Editar
                </Button>
              </Tooltip>
              <Tooltip title="Eliminar permanentemente este examen">
                <Button danger icon={<DeleteOutlined />} onClick={handleEliminar}>
                  Eliminar
                </Button>
              </Tooltip>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* ALERTAS CRÍTICAS */}
          {examen.resumen && examen.resumen.criticos > 0 && (
            <Alert
              message={`⚠️ ${examen.resumen.criticos} RESULTADO(S) CRÍTICO(S) DETECTADO(S)`}
              description="Requiere atención médica inmediata. Consulte con el médico tratante."
              type="error"
              showIcon
              icon={<WarningOutlined />}
              style={{ marginBottom: 16 }}
            />
          )}

          {/* INFORMACIÓN DEL PACIENTE */}
          <Card
            title={
              <Space>
                <UserOutlined />
                Información del Paciente
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {examen.paciente_info && (
              <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                <Descriptions.Item label="Nombre Completo">
                  {examen.paciente_info.nombre_completo}
                </Descriptions.Item>
                <Descriptions.Item label="ID Clínico">
                  {examen.paciente_info.id_clinico}
                </Descriptions.Item>
                <Descriptions.Item label="Edad">
                  {examen.paciente_info.edad} años
                </Descriptions.Item>
              </Descriptions>
            )}
          </Card>

          {/* DATOS DEL EXAMEN */}
          <Card
            title={
              <Space>
                <ExperimentOutlined />
                Datos del Examen
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
              <Descriptions.Item label="Tipo de Examen">
                {examen.tipo_examen_info?.nombre || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Código">
                {examen.tipo_examen_info?.codigo || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Categoría">
                <Tag color="blue">{examen.categoria || examen.tipo_examen_info?.categoria}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={examen.estado === 'completado' ? 'green' : examen.estado === 'en_proceso' ? 'blue' : 'orange'}>
                  {examen.estado?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Prioridad">
                <Tag color={examen.prioridad === 'stat' ? 'red' : examen.prioridad === 'urgente' ? 'orange' : 'default'}>
                  {examen.prioridad?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Fecha de Solicitud">
                <Space>
                  <CalendarOutlined />
                  {dayjs(examen.fecha_solicitud).format('DD/MM/YYYY HH:mm')}
                </Space>
              </Descriptions.Item>
              {examen.fecha_muestra && (
                <Descriptions.Item label="Fecha de Muestra">
                  {dayjs(examen.fecha_muestra).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {examen.fecha_resultado && (
                <Descriptions.Item label="Fecha de Resultado">
                  {dayjs(examen.fecha_resultado).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {examen.medico_info && (
                <Descriptions.Item label="Médico Solicitante">
                  {examen.medico_info.nombre} - {examen.medico_info.especialidad}
                </Descriptions.Item>
              )}
              {examen.indicaciones && (
                <Descriptions.Item label="Indicaciones Clínicas" span={2}>
                  <Paragraph>{examen.indicaciones}</Paragraph>
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>

          {/* RESUMEN DE RESULTADOS */}
          {examen.resumen && (
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  Resumen de Resultados
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Total Parámetros"
                      value={examen.resumen.total_parametros}
                      prefix={<ExperimentOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Normales"
                      value={examen.resumen.normales}
                      valueStyle={{ color: '#52c41a' }}
                      prefix={<CheckCircleOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Anormales"
                      value={examen.resumen.anormales}
                      valueStyle={{ color: '#faad14' }}
                      prefix={<ExclamationCircleOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Críticos"
                      value={examen.resumen.criticos}
                      valueStyle={{ color: '#ff4d4f' }}
                      prefix={<WarningOutlined />}
                    />
                  </Card>
                </Col>
              </Row>
              <Divider />
              <Progress
                percent={examen.resumen.porcentaje_normalidad}
                status={examen.resumen.porcentaje_normalidad >= 80 ? 'success' : examen.resumen.porcentaje_normalidad >= 50 ? 'normal' : 'exception'}
                format={(percent) => `${percent}% de normalidad`}
              />
            </Card>
          )}

          {/* RESULTADOS DETALLADOS O FORMULARIO DE INGRESO */}
          {examen.resultados && examen.resultados.length > 0 ? (
            <Card style={{ marginBottom: 16 }}>
              <Tabs defaultActiveKey="resultados" items={[
                {
                  key: "resultados",
                  label: tabResultadosDetallados,
                  children: (
                    <Table
                      columns={columnsResultados}
                      dataSource={examen.resultados}
                      rowKey="id"
                      pagination={false}
                      bordered
                    />
                  )
                },
                ...(estadisticas && estadisticas.examenes_historicos && estadisticas.examenes_historicos.length > 0 ? [{
                  key: "estadisticas",
                  label: <TabEstadisticasLabel count={estadisticas?.total_historicos ?? 0} />,
                  children: loadingEstadisticas ? (
                    <div style={{ textAlign: 'center', padding: '50px 0' }}>
                      <Spin tip="Cargando estadísticas…"><div /></Spin>
                    </div>
                  ) : (
                    <Tabs tabPosition="left" items={
                      examen.resultados.reduce((items: any[], resultado) => {
                        const historicoParametro = estadisticas.examenes_historicos.reduce((acc: any[], exHist: any) => {
                          const resultadoHist = exHist.resultados.find(
                            (r: any) => r.parametro === resultado.parametro_nombre
                          );
                          if (resultadoHist && resultadoHist.valor_numerico !== null) {
                            acc.push({
                              fecha: exHist.fecha_resultado,
                              valor: resultadoHist.valor_numerico,
                            });
                          }
                          return acc;
                        }, []);

                        if (historicoParametro.length === 0) return items;

                        const match = resultado.rango_referencia?.match(/(\\d+\\.?\\d*)\\s*-\\s*(\\d+\\.?\\d*)/);
                        const valorMin = match ? parseFloat(match[1]) : undefined;
                        const valorMax = match ? parseFloat(match[2]) : undefined;

                        items.push({
                          key: resultado.parametro_nombre,
                          label: resultado.parametro_nombre,
                          children: (
                            <GraficoTendenciaLaboratorio
                              parametro={resultado.parametro_nombre || ''}
                              historico={historicoParametro}
                              valorMinimo={valorMin}
                              valorMaximo={valorMax}
                              unidad={resultado.unidad}
                            />
                          )
                        });
                        return items;
                      }, [])
                    } />
                  )
                }] : [])
              ]} />
            </Card>
          ) : examen.estado !== 'completado' ? (
            /* FORMULARIO PARA INGRESAR RESULTADOS */
            <Card
              title={
                <Space>
                  <FormOutlined />
                  Ingresar Resultados del Examen
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Alert
                message="Este examen aún no tiene resultados"
                description="Complete el formulario a continuació n para ingresar los resultados de laboratorio."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <FormularioResultados
                examenId={examen.id!}
                tipoExamenId={examen.tipo_examen}
                tipoExamenNombre={examen.tipo_examen_info?.nombre || 'Examen'}
                onResultadosGuardados={cargarDatos}
              />
            </Card>
          ) : (
            <Card style={{ marginBottom: 16 }}>
              <Alert
                message="Sin Resultados"
                description="Este examen fue marcado como completado pero no tiene resultados registrados."
                type="warning"
                showIcon
              />
            </Card>
          )}

          {/* OBSERVACIONES */}
          {examen.observaciones && (
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  Observaciones
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Paragraph>{examen.observaciones}</Paragraph>
            </Card>
          )}
        </Col>

        {/* COLUMNA DERECHA */}
        <Col xs={24} lg={8}>
          {/* INFORMACIÓN ADICIONAL */}
          <Card
            title={
              <Space>
                <InfoCircleOutlined />
                Información Adicional
              </Space>
            }
          >
            <Descriptions column={1} bordered size="small">
              {examen.dias_desde_solicitud !== undefined && (
                <Descriptions.Item label="Días desde solicitud">
                  <Badge count={examen.dias_desde_solicitud} showZero color={examen.dias_desde_solicitud > 3 ? 'red' : 'blue'} />
                </Descriptions.Item>
              )}
              {examen.esta_vencido !== undefined && (
                <Descriptions.Item label="Estado de tiempo">
                  {examen.esta_vencido ? (
                    <Tag color="red">Vencido</Tag>
                  ) : (
                    <Tag color="green">A tiempo</Tag>
                  )}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Fecha de Registro">
                {examen.fecha_creacion
                  ? dayjs(examen.fecha_creacion).format('DD/MM/YYYY HH:mm')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Última Modificación">
                {examen.fecha_actualizacion
                  ? dayjs(examen.fecha_actualizacion).format('DD/MM/YYYY HH:mm')
                  : '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DetalleLaboratorio;
