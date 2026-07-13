/**
 * =============================================================================
 * MÓDULO: EMBARAZOS - DETALLE COMPLETO
 * =============================================================================
 * Muestra todos los detalles de un embarazo individual
 * Incluye progreso gestacional, controles y análisis médico
 * Con cálculos automáticos y visualizaciones mejoradas
 * =============================================================================
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Spin,
  Tag,
  Space,
  Row,
  Col,
  Typography,
  Alert,
  Progress,
  Timeline,
  Tabs,
  Statistic,
  Empty,
  Tooltip,
  Badge,
  List,
  Modal,
  Divider,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  HeartOutlined,
  CalendarOutlined,
  WarningOutlined,
  PlusOutlined,
  MedicineBoxOutlined,
  SoundOutlined,
  ExperimentOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  LineChartOutlined,
  SafetyOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { controlesService, ControlPrenatal } from '../../services/controlesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAntdApp } from '../../hooks/useMessage';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

const tabEcografias = <span><SoundOutlined /> Ecografías</span>;
const tabLaboratorio = <span><ExperimentOutlined /> Laboratorio</span>;

const arrowLeftIcon = <ArrowLeftOutlined />;
const arrowLeftIcon2 = <ArrowLeftOutlined />;
const editIcon2 = <EditOutlined />;
const plusIcon2 = <PlusOutlined />;
const safetyIcon2 = <SafetyOutlined />;
const historyIcon2 = <HistoryOutlined />;
const warningIcon = <WarningOutlined />;
const warningIcon2 = <WarningOutlined />;
const calendarIcon3 = <CalendarOutlined />;
const clockCircleIcon3 = <ClockCircleOutlined />;
const lineChartIcon = <LineChartOutlined />;
const medicineBoxIcon = <MedicineBoxOutlined />;
const userIcon = <UserOutlined />;
const infoCircleIcon = <InfoCircleOutlined />;
const infoCircleIcon2 = <InfoCircleOutlined />;
const checkCircleIcon3 = <CheckCircleOutlined />;
const soundIcon = <SoundOutlined />;
const experimentIcon2 = <ExperimentOutlined />;

// ── Cálculos obstétricos y config (puros, nivel de módulo) ───────────────────
const calcularSemanasGestacion = (fum: string) => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasDiferencia = hoy.diff(fechaFum, 'day');
  const semanas = Math.floor(diasDiferencia / 7);
  const dias = diasDiferencia % 7;
  return { semanas, dias, texto: `${semanas} semanas + ${dias} días` };
};

const calcularDiasRestantes = (fpp: string) => {
  const hoy = dayjs();
  const fechaFpp = dayjs(fpp);
  const diasRestantes = fechaFpp.diff(hoy, 'day');
  return diasRestantes > 0 ? diasRestantes : 0;
};

const calcularProgreso = (fum: string) => {
  const hoy = dayjs();
  const fechaFum = dayjs(fum);
  const diasTranscurridos = hoy.diff(fechaFum, 'day');
  const progreso = Math.min((diasTranscurridos / 280) * 100, 100);
  return Math.round(progreso);
};

const getTrimestre = (semanas: number) => {
  if (semanas < 13) return { numero: 1, texto: 'Primer Trimestre', color: 'cyan' };
  if (semanas < 28) return { numero: 2, texto: 'Segundo Trimestre', color: 'blue' };
  return { numero: 3, texto: 'Tercer Trimestre', color: 'purple' };
};

const calcularIMCClasificacion = (imc: number) => {
  if (imc < 18.5) return { texto: 'Bajo peso', color: 'orange' };
  if (imc < 25) return { texto: 'Normal', color: 'green' };
  if (imc < 30) return { texto: 'Sobrepeso', color: 'orange' };
  return { texto: 'Obesidad', color: 'red' };
};

const getEstadoConfig = (estado: string) => {
  const configs = {
    activo: { color: 'success', icon: checkCircleIcon3, texto: 'ACTIVO' },
    finalizado: { color: 'default', icon: infoCircleIcon, texto: 'FINALIZADO' },
    perdida: { color: 'error', icon: warningIcon, texto: 'PÉRDIDA' },
  };
  return configs[estado as keyof typeof configs] || configs.activo;
};

const getRiesgoConfig = (riesgo: string) => {
  const configs = {
    bajo: { color: 'success', texto: 'BAJO RIESGO' },
    medio: { color: 'warning', texto: 'RIESGO MEDIO' },
    alto: { color: 'error', texto: 'ALTO RIESGO' },
  };
  return configs[riesgo as keyof typeof configs] || configs.bajo;
};

const DetalleEmbarazo: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const antdApp = useAntdApp();

  const [embarazo, setEmbarazo] = useState<Embarazo | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [controles, setControles] = useState<ControlPrenatal[]>([]);

  const loadingRef = useRef(true);
  const [loadingControles, setLoadingControles] = useState(false);
  const [modalRiesgoVisible, setModalRiesgoVisible] = useState(false);
  const [loadingRiesgo, setLoadingRiesgo] = useState(false);
  const [riesgoDetallado, setRiesgoDetallado] = useState<any>(null);
  const [modalTimelineVisible, setModalTimelineVisible] = useState(false);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [timelineData, setTimelineData] = useState<any>(null);

  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const fetchEmbarazo = async (embarazoId: number) => {
    loadingRef.current = true;
    try {
      const data = await embarazosService.getById(embarazoId);
      if (!isMounted.current) return;
      setEmbarazo(data);

      // Cargar datos de la paciente
      if (data.paciente) {
        // Extraer ID del paciente (puede ser número u objeto)
        const pacienteId = typeof data.paciente === 'number'
          ? data.paciente
          : data.paciente.id;

        const pacienteData = await pacientesService.getById(pacienteId);
        if (isMounted.current) setPaciente(pacienteData);
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al cargar datos del embarazo');
      }
    } finally {
      if (isMounted.current) loadingRef.current = false;
    }
  };

  useEffect(() => {
    if (id) fetchEmbarazo(parseInt(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const fetchControles = async (embarazoId: number) => {
    setLoadingControles(true);
    try {
      const controlesData = await controlesService.getByEmbarazo(embarazoId);
      if (isMounted.current) {
        setControles(Array.isArray(controlesData) ? controlesData : []);
      }
    } catch (error: any) {
      if (isMounted.current) {
        setControles([]);
      }
    } finally {
      if (isMounted.current) {
        setLoadingControles(false);
      }
    }
  };

  // âœ¨ NUEVA FUNCIÓN - Calcular riesgo detallado
  const handleCalcularRiesgo = async () => {
    if (!embarazo?.id) return;
    setModalRiesgoVisible(true);
    setLoadingRiesgo(true);
    try {
      const data = await embarazosService.calcularRiesgoDetallado(embarazo.id);
      if (isMounted.current) {
        setRiesgoDetallado(data);
        antdApp.message.success('Análisis de riesgo completado');
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al calcular el riesgo detallado');
        setRiesgoDetallado(null);
      }
    } finally {
      if (isMounted.current) {
        setLoadingRiesgo(false);
      }
    }
  };

  // âœ¨ NUEVA FUNCIÓN - Ver timeline completo
  const handleVerTimeline = async () => {
    if (!embarazo?.id) return;
    setModalTimelineVisible(true);
    setLoadingTimeline(true);
    try {
      const data = await embarazosService.getTimelineCompleto(embarazo.id, {
        incluir_controles: true,
        incluir_ecografias: true,
        incluir_laboratorio: true,
        incluir_riesgos: true,
        incluir_complicaciones: true,
      });
      if (isMounted.current) {
        setTimelineData(data);
        antdApp.message.success('Timeline cargado correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        antdApp.message.error('Error al cargar el timeline completo');
        setTimelineData(null);
      }
    } finally {
      if (isMounted.current) {
        setLoadingTimeline(false);
      }
    }
  };

  // ========== HANDLERS ==========
  const handleBack = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS);
  };

  const handleEdit = () => {
    if (embarazo && embarazo.id) {
      navigate(FRONTEND_ROUTES.DASHBOARD.EMBARAZOS_EDITAR(embarazo.id));
    }
  };

  const handleNuevoControl = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_NUEVO);
  };

  const handleVerControl = (controlId: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.CONTROLES_DETALLE(controlId));
  };

  if (loadingRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" tip="Cargando información del embarazo…"><div /></Spin>
      </div>
    );
  }

  if (!embarazo) {
    return (
      <div>
        <Button
          icon={arrowLeftIcon2}
          onClick={handleBack}
          style={{ marginBottom: 16 }}
        >
          Volver a la lista
        </Button>
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                No se encontró el embarazo solicitado
                <br />
                <Text type="secondary">El embarazo no existe o ha sido eliminado</Text>
              </span>
            }
          >
            <Button type="primary" onClick={handleBack}>
              Volver a la lista
            </Button>
          </Empty>
        </Card>
      </div>
    );
  }

  // ========== CÁLCULOS ==========
  const eg = calcularSemanasGestacion(embarazo.fecha_ultima_menstruacion);
  const diasRestantes = calcularDiasRestantes(embarazo.fecha_probable_parto || new Date().toISOString());
  const progreso = calcularProgreso(embarazo.fecha_ultima_menstruacion);
  const trimestre = getTrimestre(eg.semanas);
  const estadoConfig = getEstadoConfig(embarazo.estado || 'activo');
  const riesgoConfig = getRiesgoConfig(embarazo.riesgo_embarazo || 'bajo');

  const nombrePaciente = paciente
    ? `${paciente.nombre} ${paciente.apellido_paterno} ${paciente.apellido_materno || ''}`.trim()
    : 'Cargando…';

  const formulaObstetrica = `G${embarazo.numero_gesta}P${embarazo.partos_previos || 0}C${embarazo.cesareas_previas || 0
    }A${embarazo.abortos_previos || 0}`;

  const imcClasificacion = embarazo.imc_pregestacional
    ? calcularIMCClasificacion(embarazo.imc_pregestacional)
    : null;

  // @ts-ignore
  const controlesConAlertas = controles.filter((c) => c.tiene_alertas).length;
  const ultimoControl = controles.length > 0 ? controles[controles.length - 1] : null;

  return (
    <div>
      {/* ========== HEADER CON ACCIONES ========== */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Button icon={arrowLeftIcon} onClick={handleBack}>
          Volver a la lista
        </Button>
        <Button type="primary" icon={editIcon2} onClick={handleEdit}>
          Editar Embarazo
        </Button>
        <Button type="default" icon={plusIcon2} onClick={handleNuevoControl}>
          Nuevo Control Prenatal
        </Button>
        <Button
          icon={safetyIcon2}
          onClick={handleCalcularRiesgo}
          style={{ borderColor: '#ff4d4f', color: '#ff4d4f' }}
        >
          Análisis de Riesgo Detallado
        </Button>
        <Button
          icon={historyIcon2}
          onClick={handleVerTimeline}
          style={{ borderColor: '#722ed1', color: '#722ed1' }}
        >
          Ver Timeline Completo
        </Button>
      </Space>

      {/* ========== ALERTAS DE RIESGO ========== */}
      {embarazo.riesgo_embarazo === 'alto' && embarazo.estado === 'activo' && (
        <Alert
          message="Embarazo de Alto Riesgo"
          description="Este embarazo requiere seguimiento médico especializado y controles más frecuentes."
          type="error"
          showIcon
          icon={warningIcon2}
          style={{ marginBottom: 16 }}
        />
      )}

      {controlesConAlertas > 0 && (
        <Alert
          message={`Controles con Alertas: ${controlesConAlertas}`}
          description="Se han detectado alertas médicas en los controles prenatales. Revise el historial de controles."
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          closable
        />
      )}

      {/* ========== ESTADÍSTICAS RÁPIDAS ========== */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Edad Gestacional"
              value={eg.semanas}
              suffix={`semanas + ${eg.dias}d`}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <Tag color={trimestre.color} style={{ marginTop: 8 }}>
              {trimestre.texto}
            </Tag>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Días hasta FPP"
              value={diasRestantes}
              suffix="días"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: diasRestantes < 30 ? '#ff4d4f' : '#52c41a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Progreso Gestacional"
              value={progreso}
              suffix="%"
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <Progress
              percent={progreso}
              showInfo={false}
              strokeColor={{
                '0%': '#87d068',
                '50%': '#1890ff',
                '100%': '#722ed1',
              }}
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Controles Realizados"
              value={controles.length}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: controles.length >= trimestre.numero * 3 ? '#52c41a' : '#faad14' }}
            />
            {controlesConAlertas > 0 && (
              <Badge count={controlesConAlertas} style={{ marginTop: 8 }}>
                <Tag color="error">Con alertas</Tag>
              </Badge>
            )}
          </Card>
        </Col>
      </Row>

      {/* ========== INFORMACIÓN PRINCIPAL ========== */}
      <Card
        title={
          <Space>
            <HeartOutlined style={{ fontSize: 20, color: '#ff4d4f' }} />
            <Title level={4} style={{ margin: 0 }}>
              Embarazo #{embarazo.id}
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Tag color={estadoConfig.color} icon={estadoConfig.icon}>
              {estadoConfig.texto}
            </Tag>
            <Tag color={riesgoConfig.color} icon={embarazo.riesgo_embarazo === 'alto' ? <WarningOutlined /> : undefined}>
              {riesgoConfig.texto}
            </Tag>
          </Space>
        }
      >
        <Descriptions bordered column={2} size="middle">
          {/* INFORMACIÓN DE LA PACIENTE */}
          <Descriptions.Item label={<><UserOutlined /> Paciente</>} span={2}>
            <Space>
              <Text strong style={{ fontSize: 16 }}>
                {nombrePaciente}
              </Text>
              {paciente && <Tag color="blue">{paciente.id_clinico}</Tag>}
            </Space>
          </Descriptions.Item>

          {/* DATOS OBSTÉTRICOS */}
          <Descriptions.Item label="Número de Gesta">
            <Tag color="geekblue" style={{ fontSize: 14 }}>
              G{embarazo.numero_gesta}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="Fórmula Obstétrica">
            <Tooltip title="Gesta-Partos-Cesáreas-Abortos">
              <Tag color="purple" style={{ fontSize: 14 }}>
                {formulaObstetrica}
              </Tag>
            </Tooltip>
          </Descriptions.Item>

          <Descriptions.Item label="Tipo de Embarazo">
            <Tag color={embarazo.tipo_embarazo === 'multiple' || embarazo.tipo_embarazo === 'gemelar' ? 'orange' : 'default'}>
              {embarazo.tipo_embarazo ? (embarazo.tipo_embarazo.charAt(0).toUpperCase() +
                embarazo.tipo_embarazo.slice(1)) : 'Simple'}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="Hijos Vivos">
            <Badge count={embarazo.hijos_vivos || 0} showZero style={{ backgroundColor: '#52c41a' }} />
          </Descriptions.Item>

          {/* FECHAS IMPORTANTES */}
          <Descriptions.Item label={<><CalendarOutlined /> Fecha Última Menstruación (FUM)</>}>
            <Text strong>{dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}</Text>
          </Descriptions.Item>

          <Descriptions.Item label={<><CalendarOutlined /> Fecha Probable de Parto (FPP)</>}>
            <Space>
              <Text strong>{dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}</Text>
              <Tag color={diasRestantes < 30 ? 'error' : 'success'}>
                {diasRestantes} días
              </Tag>
            </Space>
          </Descriptions.Item>

          {/* EDAD GESTACIONAL */}
          <Descriptions.Item label="Edad Gestacional Actual" span={2}>
            <Space size="large">
              <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
                {eg.texto}
              </Text>
              <Tag color={trimestre.color} style={{ fontSize: 14 }}>
                {trimestre.texto}
              </Tag>
            </Space>
          </Descriptions.Item>

          {/* PROGRESO */}
          <Descriptions.Item label="Progreso del Embarazo" span={2}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Progress
                percent={progreso}
                status="active"
                strokeColor={{
                  '0%': '#87d068',
                  '50%': '#1890ff',
                  '100%': '#722ed1',
                }}
              />
              <Space>
                <Text>
                  <strong>{diasRestantes} días restantes</strong> hasta la FPP
                </Text>
                {diasRestantes < 30 && (
                  <Tag color="orange" icon={infoCircleIcon2}>
                    Término cercano
                  </Tag>
                )}
              </Space>
            </Space>
          </Descriptions.Item>

          {/* DATOS ANTROPOMÉTRICOS */}
          {embarazo.peso_pregestacional && (
            <Descriptions.Item label="Peso Pregestacional">
              {embarazo.peso_pregestacional} kg
            </Descriptions.Item>
          )}

          {embarazo.talla_materna && (
            <Descriptions.Item label="Talla Materna">
              {embarazo.talla_materna} cm
            </Descriptions.Item>
          )}

          {embarazo.imc_pregestacional && imcClasificacion && (
            <Descriptions.Item label="IMC Pregestacional" span={2}>
              <Space>
                <Text strong>{embarazo.imc_pregestacional.toFixed(2)}</Text>
                <Tag color={imcClasificacion.color}>{imcClasificacion.texto}</Tag>
              </Space>
            </Descriptions.Item>
          )}

          {/* OTROS DATOS */}
          {embarazo.grupo_sanguineo_pareja && (
            <Descriptions.Item label="Grupo Sanguíneo Pareja" span={2}>
              <Tag color="red">{embarazo.grupo_sanguineo_pareja}</Tag>
            </Descriptions.Item>
          )}

          {embarazo.medico_responsable && (
            <Descriptions.Item label="Médico Responsable" span={2}>
              <Text>{embarazo.medico_responsable}</Text>
            </Descriptions.Item>
          )}

          {embarazo.notas && (
            <Descriptions.Item label="Observaciones Clínicas" span={2}>
              <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>
                {embarazo.notas}
              </Paragraph>
            </Descriptions.Item>
          )}

          {/* METADATOS */}
          <Descriptions.Item label="Fecha de Registro" span={2}>
            <Space>
              <CalendarOutlined />
              {embarazo.fecha_registro
                ? dayjs(embarazo.fecha_registro).format('DD/MM/YYYY HH:mm')
                : 'No disponible'}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* ========== TABS CON INFORMACIÓN ADICIONAL ========== */}
      <Card style={{ marginTop: 16 }} title={<><MedicineBoxOutlined /> Seguimiento del Embarazo</>}>
        <Tabs defaultActiveKey="controles" items={[
          {
            key: 'controles',
            label: (
              <Badge count={controles.length} offset={[10, 0]}>
                <span>
                  <MedicineBoxOutlined /> Controles Prenatales
                </span>
              </Badge>
            ),
            children: loadingControles ? (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <Spin tip="Cargando controles…"><div /></Spin>
              </div>
            ) : controles.length > 0 ? (
              <>
                <Alert
                  message={`${controles.length} control(es) prenatal(es) registrado(s)`}
                  description={ultimoControl && `Último control: ${dayjs(ultimoControl.fecha_control).format('DD/MM/YYYY')}`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <List
                  itemLayout="horizontal"
                  dataSource={controles}
                  renderItem={(control, idx) => (
                    <List.Item
                      key={control.id}
                      actions={[
                        <Button
                          key="ver_detalle"
                          type="link"
                          onClick={() => handleVerControl(control.id!)}
                        >
                          Ver Detalle
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        avatar={
                          // @ts-ignore
                          control.tiene_alertas ? (
                            <Badge dot>
                              <MedicineBoxOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
                            </Badge>
                          ) : (
                            <MedicineBoxOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                          )
                        }
                        title={
                          <Space>
                            <Text strong>Control #{control.numero_control}</Text>
                            <Tag color="blue">
                              {control.edad_gestacional_semanas}s + {control.edad_gestacional_dias || 0}d
                            </Tag>
                            {/* @ts-ignore */}
                            {control.tiene_alertas && (
                              <Tag color="error" icon={warningIcon}>
                                Con alertas
                              </Tag>
                            )}
                          </Space>
                        }
                        description={
                          <Space direction="vertical" size={0}>
                            <Text type="secondary">
                              Fecha: {dayjs(control.fecha_control).format('DD/MM/YYYY')}
                            </Text>
                            {control.presion_arterial_sistolica && control.presion_arterial_diastolica && (
                              <Text type="secondary">
                                PA: {control.presion_arterial_sistolica}/{control.presion_arterial_diastolica} mmHg
                              </Text>
                            )}
                            {control.frecuencia_cardiaca_fetal && (
                              <Text type="secondary">
                                FCF: {control.frecuencia_cardiaca_fetal} lpm
                              </Text>
                            )}
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </>
            ) : (
              <Empty
                description="No hay controles prenatales registrados"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" icon={plusIcon2} onClick={handleNuevoControl}>
                  Crear Primer Control
                </Button>
              </Empty>
            ),
          },
          {
            key: 'ecografias',
            label: tabEcografias,
            children: (
              <>
                <Alert
                  message="Módulo en Desarrollo"
                  description="El registro y visualización de ecografías estará disponible próximamente."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Empty description="No hay ecografías registradas" />
              </>
            ),
          },
          {
            key: 'laboratorio',
            label: tabLaboratorio,
            children: (
              <>
                <Alert
                  message="Módulo en Desarrollo"
                  description="Los resultados de laboratorio se mostrarán aquí próximamente."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Empty description="No hay estudios de laboratorio" />
              </>
            ),
          },
        ]} />
      </Card>

      {/* ========== LÍNEA DE TIEMPO ========== */}
      <Card title={<><CalendarOutlined /> Línea de Tiempo del Embarazo</>} style={{ marginTop: 16 }}>
        <Timeline
          mode="left"
          items={[
            {
              color: 'green',
              label: embarazo.fecha_registro ? dayjs(embarazo.fecha_registro).format('DD/MM/YYYY HH:mm') : 'Fecha desconocida',
              children: (
                <>
                  <strong>Embarazo Registrado</strong>
                  <br />
                  <Text type="secondary">Inicio del seguimiento en el sistema</Text>
                </>
              )
            },
            {
              color: 'blue',
              label: dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY'),
              children: (
                <>
                  <strong>Fecha Última Menstruación (FUM)</strong>
                  <br />
                  <Text type="secondary">Inicio del embarazo</Text>
                </>
              )
            },
            {
              color: trimestre.color,
              label: dayjs().format('DD/MM/YYYY'),
              dot: <ClockCircleOutlined style={{ fontSize: 16 }} />,
              children: (
                <>
                  <strong>Edad Gestacional Actual</strong>
                  <br />
                  <Tag color={trimestre.color}>{eg.texto}</Tag>
                  <Tag color={trimestre.color}>{trimestre.texto}</Tag>
                </>
              )
            },
            ...(controles.length > 0 ? [
              {
                color: 'cyan',
                label: dayjs(ultimoControl!.fecha_control).format('DD/MM/YYYY'),
                children: (
                  <>
                    <strong>Último Control Prenatal</strong>
                    <br />
                    <Text type="secondary">Control #{ultimoControl!.numero_control}</Text>
                  </>
                )
              }
            ] : []),
            {
              color: 'purple',
              label: dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY'),
              children: (
                <>
                  <strong>Fecha Probable de Parto (FPP)</strong>
                  <br />
                  <Text type="secondary">{diasRestantes} días restantes</Text>
                </>
              )
            }
          ]}
        />
      </Card>

      {/* NUEVO MODAL - Análisis de Riesgo Detallado */}
      <Modal
        title={
          <Space>
            <SafetyOutlined style={{ color: '#ff4d4f' }} />
            <span>Análisis de Riesgo Obstétrico Detallado</span>
          </Space>
        }
        open={modalRiesgoVisible}
        onCancel={() => {
          setModalRiesgoVisible(false);
          setRiesgoDetallado(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setModalRiesgoVisible(false);
              setRiesgoDetallado(null);
            }}
          >
            Cerrar
          </Button>,
        ]}
        width={900}
      >
        <Spin spinning={loadingRiesgo}>
          {riesgoDetallado ? (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message={`Nivel de Riesgo: ${riesgoDetallado.nivel_riesgo?.toUpperCase()}`}
                description={`Puntaje total: ${riesgoDetallado.puntaje_total || 0} puntos`}
                type={
                  riesgoDetallado.nivel_riesgo === 'alto'
                    ? 'error'
                    : riesgoDetallado.nivel_riesgo === 'medio'
                      ? 'warning'
                      : 'success'
                }
                showIcon
              />

              <Divider orientation="left">Factores de Riesgo Identificados</Divider>
              {riesgoDetallado.factores_riesgo && riesgoDetallado.factores_riesgo.length > 0 ? (
                <List
                  dataSource={riesgoDetallado.factores_riesgo}
                  renderItem={(factor: any) => (
                    <List.Item key={`factor-${factor.nombre || factor.descripcion}`}>
                      <List.Item.Meta
                        avatar={<WarningOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />}
                        title={<Text strong>{factor.nombre || factor.descripcion}</Text>}
                        description={
                          <Space direction="vertical" size={0}>
                            <Text type="secondary">{factor.detalle || factor.observaciones}</Text>
                            {factor.puntaje && (
                              <Tag color="red">Puntaje: {factor.puntaje} puntos</Tag>
                            )}
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Alert
                  message="Sin factores de riesgo"
                  description="No se identificaron factores de riesgo significativos."
                  type="success"
                  showIcon
                />
              )}

              <Divider orientation="left">Recomendaciones Médicas</Divider>
              {riesgoDetallado.recomendaciones && riesgoDetallado.recomendaciones.length > 0 ? (
                <List
                  dataSource={riesgoDetallado.recomendaciones}
                   renderItem={(recomendacion: string, index: number) => (
                     <List.Item key={`rec-${recomendacion.substring(0, 30)}`}>
                      <List.Item.Meta
                        avatar={<CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />}
                        title={`Recomendación ${index + 1}`}
                        description={recomendacion}
                      />
                    </List.Item>
                  )}
                />
              ) : (
                <Alert
                  message="Continuar con controles regulares"
                  description="Mantener el seguimiento prenatal según calendario establecido."
                  type="info"
                  showIcon
                />
              )}
            </Space>
          ) : (
            !loadingRiesgo && (
              <Empty description="No hay datos de riesgo disponibles" />
            )
          )}
        </Spin>
      </Modal>

      {/* NUEVO MODAL - Timeline Completo */}
      <Modal
        title={
          <Space>
            <HistoryOutlined style={{ color: '#722ed1' }} />
            <span>Timeline Completo del Embarazo</span>
          </Space>
        }
        open={modalTimelineVisible}
        onCancel={() => {
          setModalTimelineVisible(false);
          setTimelineData(null);
        }}
        footer={[
          <Button
            key="close"
            onClick={() => {
              setModalTimelineVisible(false);
              setTimelineData(null);
            }}
          >
            Cerrar
          </Button>,
        ]}
        width={1000}
      >
        <Spin spinning={loadingTimeline}>
          {timelineData ? (
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Alert
                message="Historial Completo"
                description="Todos los eventos registrados del embarazo en orden cronológico."
                type="info"
                showIcon
                icon={historyIcon2}
              />

              <Timeline
                mode="left"
                items={timelineData.eventos && timelineData.eventos.length > 0 ? (
                  timelineData.eventos.map((evento: any, index: number) => {
                    const iconMap: Record<string, any> = {
                      control: <MedicineBoxOutlined />,
                      ecografia: <SoundOutlined />,
                      laboratorio: <ExperimentOutlined />,
                      riesgo: <WarningOutlined />,
                      complicacion: <WarningOutlined />,
                      registro: <CheckCircleOutlined />,
                    };

                    const colorMap: Record<string, string> = {
                      control: 'blue',
                      ecografia: 'cyan',
                      laboratorio: 'purple',
                      riesgo: 'orange',
                      complicacion: 'red',
                      registro: 'green',
                    };

                    return {
                      key: evento.id || `evt-${evento.tipo}-${evento.fecha}`,
                      color: colorMap[evento.tipo] || 'gray',
                      dot: iconMap[evento.tipo],
                      label: evento.fecha
                        ? dayjs(evento.fecha).format('DD/MM/YYYY HH:mm')
                        : 'Fecha desconocida',
                      children: (
                        <Card size="small" style={{ marginBottom: 8 }}>
                          <Space direction="vertical" size={4} style={{ width: '100%' }}>
                            <Text strong style={{ fontSize: 14 }}>
                              {evento.titulo || evento.descripcion}
                            </Text>
                            {evento.tipo && (
                              <Tag color={colorMap[evento.tipo]}>
                                {evento.tipo.toUpperCase()}
                              </Tag>
                            )}
                            {evento.detalle && (
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {evento.detalle}
                              </Text>
                            )}
                            {evento.observaciones && (
                              <Paragraph
                                type="secondary"
                                style={{ fontSize: 12, marginBottom: 0 }}
                                ellipsis={{ rows: 2, expandable: true }}
                              >
                                {evento.observaciones}
                              </Paragraph>
                            )}
                          </Space>
                        </Card>
                      )
                    };
                  })
                ) : [
                  {
                    color: 'gray',
                    children: <Empty description="No hay eventos registrados" />
                  }
                ]}
              />

              {timelineData.estadisticas && (
                <>
                  <Divider orientation="left">Estadísticas del Embarazo</Divider>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Statistic
                        title="Total Controles"
                        value={timelineData.estadisticas.total_controles || 0}
                        prefix={<MedicineBoxOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="Ecografías"
                        value={timelineData.estadisticas.total_ecografias || 0}
                        prefix={<SoundOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="Laboratorios"
                        value={timelineData.estadisticas.total_laboratorios || 0}
                        prefix={<ExperimentOutlined />}
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="Eventos Totales"
                        value={timelineData.eventos?.length || 0}
                        prefix={<InfoCircleOutlined />}
                      />
                    </Col>
                  </Row>
                </>
              )}
            </Space>
          ) : (
            !loadingTimeline && (
              <Empty description="No hay datos de timeline disponibles" />
            )
          )}
        </Spin>
      </Modal>
    </div>
  );
};

export default DetalleEmbarazo;

