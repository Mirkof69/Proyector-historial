/**
 * =============================================================================
 * DETALLE DE PARTO - VISTA COMPLETA
 * =============================================================================
 * Muestra información completa de un parto específico
 * - Datos del parto y trabajo de parto
 * - Información del recién nacido
 * - Apgar scores y estado neonatal
 * - Complicaciones maternas y neonatales
 * - Procedimientos realizados
 * - Conexión: GET /partos/{id}/
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
  Timeline,
  message,
  Spin,
  Typography,
  Badge,
  Modal,
  Statistic,
  Collapse,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  DeleteOutlined,
  MedicineBoxOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  UserOutlined,
  HeartOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  SmileOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import { partosService, Parto } from '../../services/partosService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './DetalleParto.css';

dayjs.extend(duration);

const { Title, Text, Paragraph } = Typography;

const ARROW_LEFT_ICON_3 = <ArrowLeftOutlined />;
const PRINTER_ICON_2 = <PrinterOutlined />;
const EDIT_ICON_3 = <EditOutlined />;
const DELETE_ICON_4 = <DeleteOutlined />;

const DetalleParto: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [parto, setParto] = useState<Parto | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const embarazoRef = useRef<Embarazo | null>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // ✅ DETECTAR SI ES ABORTO O PARTO SEGÚN LOS CAMPOS REGISTRADOS
  const esAborto = () => {
    // Si tiene tipo_aborto registrado, ES UN ABORTO
    if ((parto as any)?.tipo_aborto) {
      return true;
    }
    // Si tiene tipo_parto registrado, ES UN PARTO
    if (parto?.tipo_parto) {
      return false;
    }
    // Solo si no tiene ninguno, usar edad gestacional para determinar
    if (!parto?.edad_gestacional_parto) return false;
    try {
      const semanas = parseInt(parto.edad_gestacional_parto.split('+')[0]);
      return semanas < 20;
    } catch {
      return false;
    }
  };

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    setLoading(true);
    try {
      // Cargar parto
      const partoData = await partosService.getById(Number(id));
      setParto(partoData);

      // Si el parto ya incluye paciente_info (serializer expandido), usarlo directamente
      if (partoData.paciente_info) {
        // Crear objeto Paciente completo desde paciente_info
        const pacienteCompleto: Paciente = {
          id: partoData.paciente_info.id || partoData.paciente || 0,
          id_clinico: partoData.paciente_info.id_clinico || '',
          nombre: partoData.paciente_info.nombre || '',
          apellido_paterno: partoData.paciente_info.apellido_paterno || '',
          apellido_materno: partoData.paciente_info.apellido_materno || '',
          fecha_nacimiento: '', // No siempre viene en info parcial
          genero: 'femenino',
          ci: partoData.paciente_info.cedula_identidad || '',
        };
        setPaciente(pacienteCompleto);
      }

      // Cargar embarazo relacionado si existe
      if (partoData.embarazo) {
        try {
          const embarazoData = await embarazosService.getById(partoData.embarazo);
          embarazoRef.current = embarazoData;

          // Solo cargar paciente si no fue cargado desde paciente_info
          if (!partoData.paciente_info && embarazoData.paciente) {
            const pacienteId = typeof embarazoData.paciente === 'number'
              ? embarazoData.paciente
              : (embarazoData.paciente as any).id;

            const pacienteData = await pacientesService.getById(pacienteId);
            setPaciente(pacienteData);
          }
        } catch (embarazoError) {
          // Continuar aunque falle la carga del embarazo
        }
      }

      if (isMounted.current) {
        message.success('Datos cargados correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al cargar los datos del parto');
      }
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, [id]);

  const loadedIdRef = useRef<number | null>(null);
  if (id && loadedIdRef.current !== Number(id)) {
    loadedIdRef.current = Number(id);
    cargarDatos();
  }



  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    Modal.confirm({
      title: '¿Eliminar este registro de parto?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await partosService.delete(Number(id));
          message.success('Parto eliminado correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS);
        } catch (error) {
          message.error('Error al eliminar el parto');
        }
      },
    });
  };

  const handleImprimir = () => {
    window.print();
  };

  // ==========================================================================
  // FUNCIONES AUXILIARES
  // ==========================================================================
  const getViaPartoColor = (via: string) => {
    const colores: Record<string, string> = {
      vaginal_espontaneo: 'green',
      vaginal_instrumentado: 'blue',
      cesarea_electiva: 'orange',
      cesarea_urgencia: 'red',
      cesarea_emergencia: 'volcano',
    };
    return colores[via] || 'default';
  };

  const getApgarInterpretacion = (apgar: number) => {
    if (apgar >= 7) {
      return { text: 'Normal', color: 'success', icon: <CheckCircleOutlined /> };
    } else if (apgar >= 4) {
      return { text: 'Depresión moderada', color: 'warning', icon: <ExclamationCircleOutlined /> };
    } else {
      return { text: 'Depresión severa', color: 'error', icon: <WarningOutlined /> };
    }
  };

  const calcularDuracionTrabajoParto = () => {
    if (!parto?.fecha_inicio_trabajo_parto || !parto?.fecha_parto) return null;

    const inicio = dayjs(parto.fecha_inicio_trabajo_parto);
    const fin = dayjs(parto.fecha_parto);
    const duracion = dayjs.duration(fin.diff(inicio));

    const horas = Math.floor(duracion.asHours());
    const minutos = duracion.minutes();

    return `${horas}h ${minutos}min`;
  };

  const getClasificacionPeso = (peso: number) => {
    if (peso < 2500) {
      return { text: 'Bajo peso', color: 'orange' };
    } else if (peso >= 2500 && peso <= 4000) {
      return { text: 'Peso adecuado', color: 'green' };
    } else {
      return { text: 'Macrosomía', color: 'red' };
    }
  };

  const getEdadGestacionalCategoria = () => {
    if (!parto?.edad_gestacional_parto) return null;

    // Parse "39+2"
    const parts = parto.edad_gestacional_parto.split('+');
    const semanas = parseInt(parts[0]);

    if (semanas < 37) {
      return { text: 'Pretérmino', color: 'orange' };
    } else if (semanas >= 37 && semanas <= 42) {
      return { text: 'A término', color: 'green' };
    } else {
      return { text: 'Postérmino', color: 'red' };
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, fontSize: 16 }}>Cargando datos del parto…</div>
      </div>
    );
  }

  if (!parto) {
    return (
      <Card>
        <Alert
          message="Parto no encontrado"
          description="No se encontró el registro de parto solicitado."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver al listado
        </Button>
      </Card>
    );
  }

  const rn = parto.recien_nacidos && parto.recien_nacidos.length > 0 ? parto.recien_nacidos[0] : null;
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const apgar1Interpretacion = getApgarInterpretacion(rn?.apgar_1_minuto || parto.apgar_1min || 0);
  const apgar5Interpretacion = getApgarInterpretacion(rn?.apgar_5_minutos || parto.apgar_5min || 0);
  const duracionTP = calcularDuracionTrabajoParto();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const clasificacionPeso = rn?.peso_nacimiento ? getClasificacionPeso(rn.peso_nacimiento) : (parto.peso_bebe ? getClasificacionPeso(parto.peso_bebe) : null);
  const categoriaEG = getEdadGestacionalCategoria();

  return (
    <div className="detalle-parto-container">
      {/* HEADER */}
      <Card className="header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button icon={ARROW_LEFT_ICON_3} onClick={handleVolver}>
                Volver
              </Button>
              <Divider type="vertical" />
              {esAborto() ? (
                <WarningOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
              ) : (
                <MedicineBoxOutlined style={{ fontSize: 24, color: '#722ed1' }} />
              )}
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  {esAborto() ? 'Registro de Aborto' : 'Registro de Parto'} {paciente && `- ${paciente.nombre} ${paciente.apellido_paterno} ${paciente.apellido_materno || ''}`}
                </Title>
                <Space>
                  <Text type="secondary">
                    {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
                  </Text>
                  {paciente?.id_clinico && (
                    <>
                      <Divider type="vertical" />
                      <Tag color="blue">ID: {paciente.id_clinico}</Tag>
                    </>
                  )}
                </Space>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={PRINTER_ICON_2} onClick={handleImprimir}>
                Imprimir
              </Button>
              <Button type="primary" icon={EDIT_ICON_3} onClick={handleEditar}>
                Editar
              </Button>
              <Button danger icon={DELETE_ICON_4} onClick={handleEliminar}>
                Eliminar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* ALERTAS DE COMPLICACIONES */}
      {(parto.complicaciones_maternas || (rn?.complicaciones_neonatales)) && (
        <Alert
          message="⚠️ Atención: Complicaciones Registradas"
          description={
            <Space direction="vertical">
              {parto.complicaciones_maternas && (
                <Text>• Complicaciones maternas presentes</Text>
              )}
              {rn?.complicaciones_neonatales && (
                <Text>• Complicaciones neonatales presentes</Text>
              )}
            </Space>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {/* ✅ VISTA DE ABORTO - Solo si < 20 semanas */}
      {/* ═════════════════════════════════════════════════════════════════════════ */}
      {esAborto() ? (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={24}>
            {/* INFORMACIÓN DEL PACIENTE */}
            {paciente && (
              <Card
                title={
                  <Space>
                    <UserOutlined />
                    Información de la Paciente
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                  <Descriptions.Item label="Nombre Completo">
                    <Text strong>
                      {paciente.nombre} {paciente.apellido_paterno}{' '}
                      {paciente.apellido_materno}
                    </Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="ID Clínico">
                    <Tag color="blue">{paciente.id_clinico}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
                </Descriptions>
              </Card>
            )}

            {/* DATOS DEL ABORTO */}
            <Card
              title={
                <Space>
                  <WarningOutlined style={{ color: '#ff4d4f' }} />
                  Datos del Aborto
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                <Descriptions.Item label="Fecha del Evento">
                  <Space>
                    <CalendarOutlined />
                    {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Edad Gestacional">
                  <Tag color="orange">{parto.edad_gestacional_parto} semanas</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Tipo de Aborto">
                  <Tag color="red">
                    {parto.tipo_aborto?.replace('_', ' ').toUpperCase() || 'No especificado'}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Método de Evacuación">
                  {parto.metodo_evacuacion?.replace('_', ' ').toUpperCase() || 'No especificado'}
                </Descriptions.Item>
                <Descriptions.Item label="Apoyo Psicológico">
                  {parto.apoyo_psicologico_realizado ? (
                    <Tag color="green"><CheckCircleOutlined /> Sí proporcionado</Tag>
                  ) : (
                    <Tag color="orange">No proporcionado</Tag>
                  )}
                </Descriptions.Item>
                <Descriptions.Item label="Protocolo de Duelo">
                  {parto.protocolo_duelo_aplicado ? (
                    <Tag color="green"><CheckCircleOutlined /> Sí aplicado</Tag>
                  ) : (
                    <Tag color="orange">No aplicado</Tag>
                  )}
                </Descriptions.Item>
                {parto.perdida_sanguinea_estimada && (
                  <Descriptions.Item label="Pérdida Sanguínea Estimada">
                    {parto.perdida_sanguinea_estimada} mL
                  </Descriptions.Item>
                )}
                {parto.hemorragia_postparto && (
                  <Descriptions.Item label="Hemorragia Post-Evacuación" span={2}>
                    <Tag color="red"><WarningOutlined /> Sí presente</Tag>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            {/* COMPLICACIONES MATERNAS */}
            {parto.complicaciones_maternas && (
              <Card
                title={
                  <Space>
                    <WarningOutlined style={{ color: '#ff4d4f' }} />
                    Complicaciones
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Alert
                  message="Complicaciones Maternas"
                  description={<Paragraph>{parto.complicaciones_maternas}</Paragraph>}
                  type="error"
                  showIcon
                />
              </Card>
            )}

            {/* OBSERVACIONES DEL ABORTO */}
            {parto.observaciones_aborto && (
              <Card
                title={
                  <Space>
                    <FileTextOutlined />
                    Observaciones del Aborto
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Paragraph>{parto.observaciones_aborto}</Paragraph>
              </Card>
            )}

            {/* ✅ ALERTAS MÉDICAS */}
            {parto.alertas_parto && parto.alertas_parto.length > 0 && (
              <Card
                title={
                  <Space>
                    <WarningOutlined />
                    Alertas Médicas
                    {parto.tiene_alertas_criticas && (
                      <Badge count="CRÍTICO" style={{ backgroundColor: '#f5222d' }} />
                    )}
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {parto.alertas_parto.map((alerta: any) => (
                    <Alert
                      key={alerta.tipo + alerta.mensaje}
                      message={alerta.mensaje}
                      description={
                        <div>
                          <strong>Recomendación:</strong> {alerta.recomendacion}
                        </div>
                      }
                      type={alerta.nivel === 'error' ? 'error' : 'warning'}
                      showIcon
                      icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />}
                    />
                  ))}
                </Space>
              </Card>
            )}

            {/* ✅ RECOMENDACIONES MÉDICAS */}
            {parto.recomendaciones_por_edad && parto.recomendaciones_por_edad.length > 0 && (
              <Card
                title={
                  <Space>
                    <InfoCircleOutlined />
                    Recomendaciones Médicas
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Alert
                  message="Recomendaciones generales"
                  description="Estas son recomendaciones generales basadas en la situación. Siempre consulte con el médico tratante."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Collapse accordion defaultActiveKey={['0']}
                  items={parto.recomendaciones_por_edad.map((rec: any) => {
                    const getAlertType = () => {
                      switch (rec.tipo) {
                        case 'urgente':
                          return 'error';
                        case 'atencion':
                          return 'warning';
                        case 'importante':
                          return 'warning';
                        default:
                          return 'info';
                      }
                    };

                    const getIcon = () => {
                      switch (rec.tipo) {
                        case 'urgente':
                        case 'atencion':
                          return <WarningOutlined />;
                        default:
                          return <InfoCircleOutlined />;
                      }
                    };

                    return {
                      key: rec.id || rec.periodo,
                      label: (
                        <Space>
                          {getIcon()}
                          <strong>{rec.periodo}:</strong> {rec.titulo}
                        </Space>
                      ),
                      children: (
                        <Alert
                          type={getAlertType()}
                          message={rec.titulo}
                          description={
                            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                              {rec.recomendaciones.map((r: string) => (
                                <li key={`rec-${rec.id || rec.periodo}-${r}`}>{r}</li>
                              ))}
                            </ul>
                          }
                          showIcon
                        />
                      )
                    };
                  })}
                />
              </Card>
            )}
          </Col>
        </Row>
        ) : (
        /* ═════════════════════════════════════════════════════════════════════════ */
        /* ✅ VISTA DE PARTO COMPLETA - Para >= 20 semanas */
        /* ═════════════════════════════════════════════════════════════════════════ */
        <Row gutter={[16, 16]}>
          {/* COLUMNA IZQUIERDA */}
          <Col xs={24} lg={16}>
            {/* ESTADÍSTICAS PRINCIPALES */}
            <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Tipo de Parto"
                    value={parto.tipo_parto?.replace('_', ' ').toUpperCase()}
                    valueStyle={{ fontSize: 16 }}
                    prefix={
                      <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
                        {parto.tipo_parto?.split('_')[0].toUpperCase()}
                      </Tag>
                    }
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Presentación"
                    value={parto.presentacion_fetal?.toUpperCase()}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Duración Trabajo de Parto"
                    value={duracionTP || 'No registrado'}
                    valueStyle={{ fontSize: 18, color: '#1890ff' }}
                    prefix={<ClockCircleOutlined />}
                  />
                </Card>
              </Col>
            </Row>

            {/* INFORMACIÓN DEL PACIENTE */}
            {paciente && (
              <Card
                title={
                  <Space>
                    <UserOutlined />
                    Información de la Paciente
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                  <Descriptions.Item label="Nombre Completo">
                    <Text strong>
                      {paciente.nombre} {paciente.apellido_paterno}{' '}
                      {paciente.apellido_materno}
                    </Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="ID Clínico">
                    <Tag color="blue">{paciente.id_clinico}</Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="CI">{paciente.ci}</Descriptions.Item>
                </Descriptions>
              </Card>
            )}

            {/* DATOS DEL PARTO */}
            <Card
              title={
                <Space>
                  <MedicineBoxOutlined />
                  Datos del Parto
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                <Descriptions.Item label="Fecha y Hora">
                  <Space>
                    <CalendarOutlined />
                    {dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Edad Gestacional">
                  <Space>
                    <span>
                      {parto.edad_gestacional_parto}
                    </span>
                    {categoriaEG && <Tag color={categoriaEG.color}>{categoriaEG.text}</Tag>}
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label="Tipo de Parto">
                  <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
                    {parto.tipo_parto?.replace('_', ' ').toUpperCase()}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Presentación">
                  {parto.presentacion_fetal?.toUpperCase()}
                </Descriptions.Item>
                {parto.fecha_inicio_trabajo_parto && (
                  <Descriptions.Item label="Inicio Trabajo de Parto">
                    {dayjs(parto.fecha_inicio_trabajo_parto).format('DD/MM/YYYY HH:mm')}
                  </Descriptions.Item>
                )}
                {duracionTP && (
                  <Descriptions.Item label="Duración Trabajo de Parto">
                    <Text strong>{duracionTP}</Text>
                  </Descriptions.Item>
                )}
                {parto.estado_membranas && (
                  <Descriptions.Item label="Estado Membranas">
                    {parto.estado_membranas.replace('_', ' ').toUpperCase()}
                  </Descriptions.Item>
                )}
                {parto.caracteristicas_liquido && (
                  <Descriptions.Item label="Líquido Amniótico">
                    {parto.caracteristicas_liquido}
                  </Descriptions.Item>
                )}
                {parto.tipo_alumbramiento && (
                  <Descriptions.Item label="Alumbramiento" span={2}>
                    {parto.tipo_alumbramiento.toUpperCase()}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            {/* ✅ ALERTAS MÉDICAS */}
            {parto.alertas_parto && parto.alertas_parto.length > 0 && (
              <Card
                title={
                  <Space>
                    <WarningOutlined />
                    Alertas Médicas
                    {parto.tiene_alertas_criticas && (
                      <Badge count="CRÍTICO" style={{ backgroundColor: '#f5222d' }} />
                    )}
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  {parto.alertas_parto.map((alerta: any) => (
                    <Alert
                      key={alerta.tipo + alerta.mensaje}
                      message={alerta.mensaje}
                      description={
                        <div>
                          <strong>Recomendación:</strong> {alerta.recomendacion}
                        </div>
                      }
                      type={alerta.nivel === 'error' ? 'error' : 'warning'}
                      showIcon
                      icon={alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> : <WarningOutlined />}
                    />
                  ))}
                </Space>

                {parto.tipo_parto_segun_edad && (
                  <Alert
                    message={parto.tipo_parto_segun_edad.descripcion}
                    type="info"
                    showIcon
                    style={{ marginTop: 16 }}
                  />
                )}
              </Card>
            )}

            {/* ✅ RECOMENDACIONES MÉDICAS */}
            {parto.recomendaciones_por_edad && parto.recomendaciones_por_edad.length > 0 && (
              <Card
                title={
                  <Space>
                    <InfoCircleOutlined />
                    Recomendaciones Médicas por Edad Gestacional
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Alert
                  message="Recomendaciones generales"
                  description="Estas son recomendaciones generales basadas en la edad gestacional. Siempre consulte con el médico tratante."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Collapse accordion defaultActiveKey={['0']}
                  items={parto.recomendaciones_por_edad.map((rec: any) => {
                    const getAlertType = () => {
                      switch (rec.tipo) {
                        case 'urgente':
                          return 'error';
                        case 'atencion':
                          return 'warning';
                        case 'importante':
                          return 'warning';
                        default:
                          return 'info';
                      }
                    };

                    const getIcon = () => {
                      switch (rec.tipo) {
                        case 'urgente':
                        case 'atencion':
                          return <WarningOutlined />;
                        default:
                          return <InfoCircleOutlined />;
                      }
                    };

                    return {
                      key: rec.id || rec.periodo,
                      label: (
                        <Space>
                          {getIcon()}
                          <strong>{rec.periodo}:</strong> {rec.titulo}
                        </Space>
                      ),
                      children: (
                        <Alert
                          type={getAlertType()}
                          message={rec.titulo}
                          description={
                            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                              {rec.recomendaciones.map((r: string) => (
                                <li key={`rec-${rec.id || rec.periodo}-${r}`}>{r}</li>
                              ))}
                            </ul>
                          }
                          showIcon
                        />
                      )
                    };
                  })}
                />
              </Card>
            )}

            {/* SCORE DE APGAR */}
            <Card
              title={
                <Space>
                  <HeartOutlined />
                  Score de Apgar
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              {(() => {
                const apgar1 = rn?.apgar_1_minuto || parto.apgar_1min || 0;
                const apgar5 = rn?.apgar_5_minutos || parto.apgar_5min || 0;
                const apgar1Interpretacion = getApgarInterpretacion(apgar1);
                const apgar5Interpretacion = getApgarInterpretacion(apgar5);

                return (
                  <Row gutter={[24, 24]}>
                    <Col span={24} md={12}>
                      <Card type="inner" title="Apgar al 1 minuto">
                        <div style={{ textAlign: 'center' }}>
                          <Title level={1} style={{ margin: 0, color: apgar1Interpretacion.color === 'error' ? '#ff4d4f' : (apgar1Interpretacion.color === 'warning' ? '#faad14' : '#52c41a') }}>
                            {apgar1}
                          </Title>
                          <Divider style={{ margin: '12px 0' }} />
                          <Alert
                            message={apgar1Interpretacion.text}
                            type={apgar1Interpretacion.color as any}
                            showIcon
                            icon={apgar1Interpretacion.icon}
                          />
                        </div>
                      </Card>
                    </Col>
                    <Col span={24} md={12}>
                      <Card type="inner" title="Apgar a los 5 minutos">
                        <div style={{ textAlign: 'center' }}>
                          <Title level={1} style={{ margin: 0, color: apgar5Interpretacion.color === 'error' ? '#ff4d4f' : (apgar5Interpretacion.color === 'warning' ? '#faad14' : '#52c41a') }}>
                            {apgar5}
                          </Title>
                          <Divider style={{ margin: '12px 0' }} />
                          <Alert
                            message={apgar5Interpretacion.text}
                            type={apgar5Interpretacion.color as any}
                            showIcon
                            icon={apgar5Interpretacion.icon}
                          />
                        </div>
                      </Card>
                    </Col>
                  </Row>
                );
              })()}
            </Card>

            {/* COMPLICACIONES */}
            {(parto.complicaciones_maternas || (rn?.complicaciones_neonatales)) && (
              <Card
                title={
                  <Space>
                    <WarningOutlined style={{ color: '#ff4d4f' }} />
                    Complicaciones
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                {parto.complicaciones_maternas && (
                  <>
                    <Title level={5}>Complicaciones Maternas</Title>
                    <Alert
                      message="Complicaciones en la Madre"
                      description={<Paragraph>{parto.complicaciones_maternas}</Paragraph>}
                      type="error"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />
                  </>
                )}
                {rn?.complicaciones_neonatales && (
                  <>
                    <Title level={5}>Complicaciones Neonatales</Title>
                    <Alert
                      message="Complicaciones en el Recién Nacido"
                      description={<Paragraph>{rn.complicaciones_neonatales}</Paragraph>}
                      type="warning"
                      showIcon
                    />
                  </>
                )}
              </Card>
            )}

            {/* OBSERVACIONES */}
            {parto.observaciones_parto && (
              <Card
                title={
                  <Space>
                    <FileTextOutlined />
                    Observaciones
                  </Space>
                }
                style={{ marginBottom: 16 }}
              >
                <Paragraph>{parto.observaciones_parto}</Paragraph>
              </Card>
            )}
          </Col>

          {/* COLUMNA DERECHA */}
          <Col xs={24} lg={8}>
            {/* RESUMEN RÁPIDO */}
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  Resumen Rápido
                </Space>
              }
              style={{ marginBottom: 16 }}
            >
              <Timeline
                items={[
                  {
                    color: 'blue',
                    dot: <CalendarOutlined />,
                    children: (
                      <>
                        <Text strong>Fecha del Parto</Text>
                        <br />
                        <Text>{dayjs(parto.fecha_parto).format('DD/MM/YYYY HH:mm')}</Text>
                      </>
                    ),
                  },
                  {
                    color: 'green',
                    dot: <CheckCircleOutlined />,
                    children: (
                      <>
                        <Text strong>Tipo de Parto</Text>
                        <br />
                        <Tag color={getViaPartoColor(parto.tipo_parto || '')}>
                          {parto.tipo_parto?.replace('_', ' ').toUpperCase()}
                        </Tag>
                      </>
                    ),
                  },
                  {
                    color: 'purple',
                    dot: <SmileOutlined />,
                    children: (
                      <>
                        <Text strong>Recién Nacido</Text>
                        <br />
                        {rn ? (
                          <Text>
                            {rn.sexo === 'masculino' ? 'Masculino' : 'Femenino'} -{' '}
                            {rn.peso_nacimiento}g
                          </Text>
                        ) : <Text>Sin datos</Text>}
                      </>
                    ),
                  },
                  {
                    color: apgar5Interpretacion.color === 'success'
                      ? 'green'
                      : apgar5Interpretacion.color === 'warning'
                        ? 'orange'
                        : 'red',
                    dot: <HeartOutlined />,
                    children: (
                      <>
                        <Text strong>Apgar 5 min</Text>
                        <br />
                        <Text>{rn?.apgar_5_minutos || parto.apgar_5min} - {apgar5Interpretacion.text}</Text>
                      </>
                    ),
                  },
                ]}
              />
            </Card>

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
                {parto.medico_responsable && (
                  <Descriptions.Item label="Médico Responsable">
                    ID: {parto.medico_responsable}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          </Col>
        </Row>
      )}
      {/* ═════════════════════════════════════════════════════════════════════════ */}
    </div>
  );
};

export default DetalleParto;
