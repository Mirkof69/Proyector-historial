import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Card,
  Button,
  Descriptions,
  Divider,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  Alert,
  Typography,
  Skeleton,
  Badge,
  Result,
  Avatar
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  ArrowLeftOutlined,
  PrinterOutlined,
  FileTextOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  CalendarOutlined,
  RiseOutlined,
  ExperimentOutlined,
  HomeOutlined,
  InfoCircleOutlined,
  WarningOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';
import { evolucionesService } from '../../services/evolucionesService';
import { useAntdApp } from '../../hooks/useMessage';
import './Evoluciones.css';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Title, Text, Paragraph } = Typography;

const handlePrint = () => {
  window.print();
};

const DetalleEvolucion: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { message, modal } = useAntdApp();

  const [evolucion, setEvolucion] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const loadEvolucion = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await evolucionesService.obtener(Number(id));
      setEvolucion(data);
    } catch (error) {
      message.error('No se pudo recuperar la información de la evolución');
      navigate('/dashboard/evoluciones');
    } finally {
      setLoading(false);
    }
  }, [id, message, navigate]);

  useEffect(() => {
    loadEvolucion();
  }, [loadEvolucion]);

  const handleDelete = useCallback(() => {
    modal.confirm({
      title: '¿Eliminar esta evolución?',
      content: 'Esta acción es permanente y eliminará el registro clínico del historial.',
      okText: 'Sí, eliminar',
      cancelText: 'Cancelar',
      okType: 'danger',
      onOk: async () => {
        try {
          await evolucionesService.eliminar(Number(id));
          message.success('Evolución eliminada satisfactoriamente');
          navigate('/dashboard/evoluciones');
        } catch (error) {
          message.error('Error al intentar eliminar el registro');
        }
      },
    });
  }, [id, modal, message, navigate]);

  const colorTipo = useMemo(() => {
    if (!evolucion) return 'blue';
    const tipo = (evolucion.tipo || evolucion.tipo_evento || '').toLowerCase();
    if (tipo === 'urgencia') return 'red';
    if (tipo === 'control') return 'green';
    return 'blue';
  }, [evolucion]);

  if (loading) {
    return (
      <div style={{ padding: '24px' }}>
        <Skeleton active avatar paragraph={{ rows: 15 }} />
      </div>
    );
  }

  if (!evolucion) return <Result status="404" title="Evolución no encontrada" />;

  return (
    <div className="animate-fade-in print-container" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        {/* HEADER SECTION */}
        <div className="blue-gradient-header no-print" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space align="center" size="large">
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate('/dashboard/evoluciones')}
                  className="back-button-white"
                />
                <div className="header-icon-container">
                  <FileTextOutlined style={{ fontSize: '32px', color: '#fff' }} />
                </div>
                <div>
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>Resumen de Evolución Clínica</Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)' }}>
                    {evolucion.paciente_nombre} • ID: {evolucion.id} • {dayjs(evolucion.fecha).format('DD MMM, YYYY')}
                  </Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  size="large"
                  icon={<PrinterOutlined />}
                  onClick={handlePrint}
                >
                  Imprimir Reporte
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<EditOutlined />}
                  onClick={() => navigate(`/dashboard/evoluciones/${id}/editar`)}
                  className="btn-success-gradient"
                >
                  Editar Registro
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {/* PRINT ONLY HEADER */}
        <div className="print-only" style={{ textAlign: 'center', marginBottom: 30 }}>
          <Title level={2}>REPORTE DE EVOLUCIÓN CLÍNICA - FETAL MEDICAL</Title>
          <Divider />
        </div>

        <Row gutter={[24, 24]}>
          <Col xs={24} lg={16}>
            {/* ALERTAS Y ESTADO */}
            {evolucion.es_urgente && (
              <Alert
                message="ATENCIÓN: Evolución de Carácter Urgente"
                description="Este registro ha sido marcado como prioritario debido a hallazgos clínicos de importancia."
                type="error"
                showIcon
                icon={<WarningOutlined className="status-pulse" />}
                style={{ marginBottom: 24, borderRadius: '12px' }}
              />
            )}

            <Card className="detail-section-card" title={<Space><UserOutlined /> Identificación del Paciente</Space>}>
              <Descriptions column={{ xs: 1, sm: 2 }} bordered>
                <Descriptions.Item label="Nombre Completo" span={2}>
                  <Text strong style={{ fontSize: '1.2em' }}>{evolucion.paciente_nombre}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="ID de Referencia">#{evolucion.paciente}</Descriptions.Item>
                <Descriptions.Item label="Fecha de Registro">{dayjs(evolucion.fecha).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
              </Descriptions>
            </Card>

            <Card className="detail-section-card" style={{ marginTop: 24 }} title={<Space><RiseOutlined /> Evaluación Clínica (Hallazgos)</Space>}>
              <div style={{ background: '#f8fafc', padding: '24px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <Title level={4}>Subjetivo / Objetivo / Análisis</Title>
                <Paragraph style={{ fontSize: '1.1em', lineHeight: '1.8', whiteSpace: 'pre-wrap' }}>
                  {evolucion.resumen || 'No se registraron detalles del resumen clínico.'}
                </Paragraph>
              </div>

              <Divider />

              <div style={{ marginTop: 20 }}>
                <Text strong style={{ color: '#ff4d4f', fontSize: '1.1em' }}><RiseOutlined /> Juicio Clínico / Diagnóstico:</Text>
                <Alert
                  message={<Text strong style={{ fontSize: '1.1em' }}>{evolucion.diagnostico || 'Sin diagnóstico definido'}</Text>}
                  type="info"
                  style={{ marginTop: 12, boxShadow: 'inset 3px 0 0 #91caff' }}
                />
              </div>
            </Card>

            <Card className="detail-section-card" style={{ marginTop: 24 }} title={<Space><ExperimentOutlined /> Terapéutica y Seguimiento</Space>}>
              <Row gutter={24}>
                <Col span={24}>
                  <Title level={5}>Tratamiento Prescrito</Title>
                  <div style={{ background: '#f0fdf4', padding: '16px', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{evolucion.tratamiento || 'Sin tratamiento farmacológico indicado.'}</Text>
                  </div>
                </Col>
                <Col span={24} style={{ marginTop: 24 }}>
                  <Title level={5}>Plan de Trabajo</Title>
                  <Paragraph style={{ whiteSpace: 'pre-wrap' }}>{evolucion.plan || 'No se detalló un plan de seguimiento.'}</Paragraph>
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={8}>
            <Card className="sidebar-card" title={<Space><CalendarOutlined /> Resumen Técnico</Space>}>
              <div style={{ textAlign: 'center', marginBottom: 24 }}>
                <Statistic
                  title="Días transcurridos"
                  value={dayjs().diff(dayjs(evolucion.fecha), 'day')}
                  suffix="DÍAS"
                  valueStyle={{ color: '#1890ff', fontWeight: 'bold' }}
                />
                <Tag color={colorTipo} style={{ marginTop: 12, fontSize: '1em', padding: '4px 12px' }}>
                  {(evolucion.tipo || 'CONSULTA').toUpperCase()}
                </Tag>
              </div>

              <Divider />

              <Descriptions column={1} size="small">
                <Descriptions.Item label="Estado">
                  <Badge status={evolucion.estado === 'completado' ? 'success' : 'processing'} text={evolucion.estado?.toUpperCase() || 'PENDIENTE'} />
                </Descriptions.Item>
                <Descriptions.Item label="Duración">
                  {evolucion.duracion_consulta ? `${evolucion.duracion_consulta} min` : 'N/A'}
                </Descriptions.Item>
              </Descriptions>

              <Divider />

              <div style={{ background: '#fff9db', padding: '16px', borderRadius: '8px', border: '1px solid #fab005' }}>
                <Space align="start">
                  <InfoCircleOutlined style={{ color: '#f08c00', marginTop: 4 }} />
                  <div>
                    <Text strong>Seguimiento:</Text>
                    <br />
                    <Text>{evolucion.requiere_seguimiento ? 'Paciente requiere contacto posterior' : 'No se requiere seguimiento activo'}</Text>
                  </div>
                </Space>
              </div>
            </Card>

            <Card className="sidebar-card" style={{ marginTop: 24 }} title={<Space><MedicineBoxOutlined /> Profesional a Cargo</Space>}>
              <div style={{ textAlign: 'center', paddingBottom: 20 }}>
                <Avatar size={64} icon={<UserOutlined />} style={{ backgroundColor: '#1890ff', marginBottom: 16 }} />
                <Title level={4} style={{ margin: 0 }}>Dr(a). {evolucion.medico || 'No Especificado'}</Title>
                <Text type="secondary">Especialista en Ginecología y Obstetricia</Text>
              </div>
              <Divider style={{ margin: '12px 0' }} />
              <div style={{ textAlign: 'center' }}>
                <div className="signature-placeholder" style={{ height: 60, width: '100%', marginBottom: 10 }}></div>
                <Text type="secondary" style={{ fontSize: '0.8em' }}>Sello y Firma Médica</Text>
              </div>
            </Card>

            <div className="no-print" style={{ marginTop: 24 }}>
              <Button
                danger
                block
                size="large"
                icon={<DeleteOutlined />}
                onClick={handleDelete}
                className="btn-danger-soft"
              >
                Eliminar Registro Permanente
              </Button>
            </div>
          </Col>
        </Row>

        {/* FOOTER ACTIONS */}
        <div className="no-print" style={{ marginTop: 32, padding: '20px', background: '#f8fafc', borderRadius: '12px', textAlign: 'right' }}>
          <Space>
            <Button icon={<HomeOutlined />} onClick={() => navigate('/dashboard')}>Inicio</Button>
            <Button icon={<FileTextOutlined />} onClick={() => navigate('/dashboard/evoluciones')}>Listado Evoluciones</Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default DetalleEvolucion;
