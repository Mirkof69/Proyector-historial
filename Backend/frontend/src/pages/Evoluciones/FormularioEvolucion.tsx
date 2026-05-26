import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Form,
  Button,
  Input,
  Select,
  DatePicker,
  TimePicker,
  Card,
  Row,
  Col,
  Steps,
  Alert,
  Divider,
  Space,
  Checkbox,
  InputNumber,
  Typography,
  Skeleton
} from 'antd';
import {
  SaveOutlined,
  ArrowLeftOutlined,
  UserOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  RiseOutlined,
  CheckCircleOutlined,
  CloseOutlined,
  EditOutlined,
  ExperimentOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import { evolucionesService } from '../../services/evolucionesService';
import { pacientesService } from '../../services/pacientesService';
import { useAntdApp } from '../../hooks/useMessage';
import './Evoluciones.css';

const { TextArea } = Input;
const { Title, Text } = Typography;
const { Step } = Steps;

const FormularioEvolucion: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [form] = Form.useForm();
  const { message } = useAntdApp();

  // Estados
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  const loadPacientes = useCallback(async () => {
    try {
      const data = await pacientesService.listar();
      setPacientes(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('No se pudo cargar el listado de pacientes');
    }
  }, [message]);

  const loadEvolucion = useCallback(async (evolucionId: number) => {
    setLoading(true);
    try {
      const data = await evolucionesService.obtener(evolucionId);
      form.setFieldsValue({
        ...data,
        fecha: data.fecha ? dayjs(data.fecha) : dayjs(),
        hora_atencion: data.fecha ? dayjs(data.fecha) : dayjs(),
      });
    } catch (error) {
      message.error('Error al cargar la nota de evolución');
    } finally {
      setLoading(false);
    }
  }, [form, message]);

  useEffect(() => {
    loadPacientes();
    if (id) {
      loadEvolucion(Number(id));
    }
  }, [id, loadPacientes, loadEvolucion]);

  const onFinish = useCallback(async (values: any) => {
    setSubmitting(true);
    try {
      const payload = {
        ...values,
        fecha: values.fecha.format('YYYY-MM-DDTHH:mm:ss'),
      };

      if (id) {
        await evolucionesService.actualizar(Number(id), payload);
        message.success('Nota de evolución actualizada');
      } else {
        await evolucionesService.crear(payload);
        message.success('Nueva nota de evolución registrada');
      }
      navigate('/dashboard/evoluciones');
    } catch (error) {
      message.error('Error al procesar la solicitud');
    } finally {
      setSubmitting(false);
    }
  }, [id, navigate, message]);

  const steps = useMemo(() => [
    {
      title: 'Identificación',
      icon: <UserOutlined />,
      content: (
        <Space direction="vertical" size="middle" style={{ width: '100%', padding: '16px' }}>
          <Alert
            message="Selección del Paciente"
            description="Vincule esta nota de evolución a un paciente registrado en el sistema."
            type="info"
            showIcon
            style={{ borderRadius: '8px' }}
          />
          <Form.Item label="Paciente" name="paciente" rules={[{ required: true, message: 'Debe seleccionar un paciente' }]}>
            <Select
              placeholder="Escriba nombre o cédula para buscar..."
              showSearch
              size="large"
              style={{ width: '100%' }}
              filterOption={(input, option) =>
                (option?.label as string).toLowerCase().includes(input.toLowerCase())
              }
              options={pacientes.map(p => ({
                label: `${p.nombre} ${p.apellido_paterno || p.apellido} - ${p.ci || p.id_clinico}`,
                value: p.id,
              }))}
            />
          </Form.Item>
        </Space>
      ),
    },
    {
      title: 'Contexto Clínico',
      icon: <CalendarOutlined />,
      content: (
        <div style={{ padding: '16px' }}>
          <Row gutter={24}>
            <Col xs={24} md={8}>
              <Form.Item label="Fecha de Atención" name="fecha" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} size="large" format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Hora de Inicio" name="hora_atencion">
                <TimePicker style={{ width: '100%' }} size="large" format="HH:mm" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Duración (minutos)" name="duracion_consulta">
                <InputNumber style={{ width: '100%' }} size="large" min={1} max={300} placeholder="30" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Clasificación Médica</Divider>

          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item label="Tipo de Evento" name="tipo" rules={[{ required: true }]}>
                <Select
                  size="large"
                  options={[
                    { label: 'Consulta General', value: 'consulta' },
                    { label: 'Control Prenatal', value: 'control' },
                    { label: 'Urgencia Obstétrica', value: 'urgencia' },
                    { label: 'Seguimiento Telefónico', value: 'seguimiento' },
                  ]}
                />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="Estado de la Nota" name="estado">
                <Select
                  size="large"
                  options={[
                    { label: 'En Proceso / Borrador', value: 'pendiente' },
                    { label: 'Completada / Cerrada', value: 'completado' },
                  ]}
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Personal Responsable</Divider>

          <Row gutter={24}>
            <Col xs={24} md={12}>
              <Form.Item label="Médico Tratante" name="medico" rules={[{ required: true }]}>
                <Input prefix={<MedicineBoxOutlined />} placeholder="Nombre y especialidad" size="large" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12} style={{ paddingTop: '32px' }}>
              <Space size="large">
                <Form.Item name="requiere_seguimiento" valuePropName="checked" noStyle>
                  <Checkbox><Text strong>Requiere Seguimiento</Text></Checkbox>
                </Form.Item>
                <Form.Item name="es_urgente" valuePropName="checked" noStyle>
                  <Checkbox><Text strong style={{ color: '#ff4d4f' }}>Marcar como Urgente</Text></Checkbox>
                </Form.Item>
              </Space>
            </Col>
          </Row>
        </div>
      ),
    },
    {
      title: 'Hallazgos y Diagnóstico',
      icon: <RiseOutlined />,
      content: (
        <div style={{ padding: '16px' }}>
          <Form.Item
            label={<Text strong>Resumen Clínico / Evolución S.O.A.P.</Text>}
            name="resumen"
            extra="Subjetivo, Objetivo, Análisis, Plan"
          >
            <TextArea rows={6} placeholder="Describa la evolución del paciente desde la última visita..." />
          </Form.Item>

          <Divider />

          <Form.Item
            label={<Text strong>Diagnóstico Clínico (CIE-10)</Text>}
            name="diagnostico"
            rules={[{ required: true, message: 'El diagnóstico es obligatorio', min: 10 }]}
          >
            <TextArea rows={3} placeholder="Ingrese el diagnóstico principal y diagnósticos asociados..." />
          </Form.Item>
        </div>
      ),
    },
    {
      title: 'Prescripción y Plan',
      icon: <ExperimentOutlined />,
      content: (
        <div style={{ padding: '16px' }}>
          <Form.Item label={<Text strong>Tratamiento / Prescripción Médica</Text>} name="tratamiento">
            <TextArea rows={5} placeholder="Medicamentos, dosis, frecuencia y vía de administración..." />
          </Form.Item>

          <Divider />

          <Form.Item label={<Text strong>Plan de Seguimiento / Próximos Pasos</Text>} name="plan">
            <TextArea rows={5} placeholder="Exámenes solicitados, interconsultas, fecha de próximo control..." />
          </Form.Item>
        </div>
      ),
    },
  ], [pacientes]);

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        {/* HEADER */}
        <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space align="center" size="large">
                <Button
                  icon={<ArrowLeftOutlined />}
                  onClick={() => navigate('/dashboard/evoluciones')}
                  className="back-button-white"
                />
                <div className="header-icon-container">
                  <EditOutlined style={{ fontSize: '32px', color: '#fff' }} />
                </div>
                <div>
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>
                    {id ? 'Actualizar Evolución' : 'Registro de Evolución'}
                  </Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Documentación clínica del paciente conforme a estándares internacionales</Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  size="large"
                  icon={<CloseOutlined />}
                  onClick={() => navigate('/dashboard/evoluciones')}
                >
                  Cancelar
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<SaveOutlined />}
                  onClick={() => form.submit()}
                  loading={submitting}
                  className="btn-success-gradient"
                >
                  {id ? 'Guardar Cambios' : 'Finalizar Registro'}
                </Button>
              </Space>
            </Col>
          </Row>
        </div>

        {loading ? (
          <Skeleton active paragraph={{ rows: 12 }} style={{ padding: '48px' }} />
        ) : (
          <div style={{ padding: '24px 48px' }}>
            <Steps
              current={currentStep}
              onChange={setCurrentStep}
              className="premium-steps"
              style={{ marginBottom: '40px' }}
            >
              {steps.map(step => (
                <Step key={step.title} title={step.title} icon={step.icon} />
              ))}
            </Steps>

            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              className="premium-form"
              initialValues={{
                fecha: dayjs(),
                estado: 'completado',
                tipo: 'consulta',
                duracion_consulta: 30
              }}
            >
              <div className="form-step-content" style={{ minHeight: '400px', background: '#fcfcfc', borderRadius: '12px', border: '1px solid #f0f0f0' }}>
                {steps[currentStep].content}
              </div>

              <Row justify="space-between" align="middle" style={{ marginTop: '32px' }}>
                <Col>
                  <Button
                    size="large"
                    onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                    disabled={currentStep === 0}
                    icon={<ArrowLeftOutlined />}
                  >
                    Regresar al paso anterior
                  </Button>
                </Col>
                <Col>
                  <Space size="middle">
                    {currentStep < steps.length - 1 ? (
                      <Button
                        type="primary"
                        size="large"
                        onClick={() => setCurrentStep(prev => prev + 1)}
                        icon={<ArrowRightOutlined />}
                      >
                        Continuar al siguiente paso
                      </Button>
                    ) : (
                      <Button
                        type="primary"
                        size="large"
                        htmlType="submit"
                        icon={<CheckCircleOutlined />}
                        loading={submitting}
                        className="btn-success-gradient"
                      >
                        {id ? 'Finalizar Edición' : 'Confirmar y Guardar Evolución'}
                      </Button>
                    )}
                  </Space>
                </Col>
              </Row>
            </Form>
          </div>
        )}
      </Card>
    </div>
  );
};

export default FormularioEvolucion;
