import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Form, Button, Card, Row, Col, Steps, Space, Skeleton } from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  CalendarOutlined,
  RiseOutlined,
  CheckCircleOutlined,
  ExperimentOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import { evolucionesService } from '../../services/evolucionesService';
import { pacientesService } from '../../services/pacientesService';
import { useAntdApp } from '../../hooks/useMessage';
import FormularioEvolucionHeader from './components/FormularioEvolucionHeader';
import PasoIdentificacion from './components/PasoIdentificacion';
import PasoContextoClinico from './components/PasoContextoClinico';
import PasoHallazgos from './components/PasoHallazgos';
import PasoPrescripcion from './components/PasoPrescripcion';
import './Evoluciones.css';

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
    { title: 'Identificación', icon: <UserOutlined />, content: <PasoIdentificacion pacientes={pacientes} /> },
    { title: 'Contexto Clínico', icon: <CalendarOutlined />, content: <PasoContextoClinico /> },
    { title: 'Hallazgos y Diagnóstico', icon: <RiseOutlined />, content: <PasoHallazgos /> },
    { title: 'Prescripción y Plan', icon: <ExperimentOutlined />, content: <PasoPrescripcion /> },
  ], [pacientes]);

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        <FormularioEvolucionHeader
          esEdicion={!!id}
          submitting={submitting}
          onCancelar={() => navigate('/dashboard/evoluciones')}
          onGuardar={() => form.submit()}
        />

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
