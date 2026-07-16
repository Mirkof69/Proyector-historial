import React, { useState, useCallback } from 'react';
import {
  Modal,
  Form,
  Row,
  Col,
  Divider,
  Space,
  Card,
  Button
} from 'antd';
import {
  UserOutlined,
  PhoneOutlined,
  MedicineBoxOutlined,
  CheckCircleOutlined,
  SaveOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAntdApp } from '../../../hooks/useMessage';
import { API_URL } from '../../../services/api';
import { RegistroPacienteCompleto } from './registroPacienteTypes';
import PasoDatosPersonalesReg from './components/PasoDatosPersonalesReg';
import PasoContactoReg from './components/PasoContactoReg';
import PasoDatosClinicosReg from './components/PasoDatosClinicosReg';

export type { RegistroPacienteCompleto };

export const ModalRegistroPacienteCompleto: React.FC<{
  open: boolean;
  onClose: () => void;
  onSuccess?: (paciente: RegistroPacienteCompleto) => void;
  pacienteEditar?: Partial<RegistroPacienteCompleto>;
}> = ({ open, onClose, onSuccess, pacienteEditar }) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<Partial<RegistroPacienteCompleto>>({});

  React.useEffect(() => {
    if (!open) return;
    if (pacienteEditar) {
      form.setFieldsValue(pacienteEditar);
      setFormData(pacienteEditar);
    } else {
      form.resetFields();
      setFormData({});
      setCurrentStep(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const handleSubmit = useCallback(async (values: any) => {
    setLoading(true);
    try {
      const datosCompletos: Partial<RegistroPacienteCompleto> = {
        ...formData,
        ...values,
        fecha_registro: new Date().toISOString(),
        activo: true
      };

      // Calcular edad si tiene fecha de nacimiento
      if (datosCompletos.fecha_nacimiento) {
        const nacimiento = new Date(datosCompletos.fecha_nacimiento);
        const hoy = new Date();
        let edad = hoy.getFullYear() - nacimiento.getFullYear();
        const mes = hoy.getMonth() - nacimiento.getMonth();
        if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
          edad--;
        }
        datosCompletos.edad = edad;
      }

      const endpoint = pacienteEditar?.id_clinico
        ? `${API_URL}/pacientes/${pacienteEditar.id_clinico}/`
        : `${API_URL}/pacientes/`;

      const method = pacienteEditar?.id_clinico ? 'PUT' : 'POST';

      // Auth por cookie httpOnly + CSRF (defaults globales de axios:
      // withCredentials y X-CSRFToken configurados en services/api.ts)
      const response = await axios({
        method,
        url: endpoint,
        data: datosCompletos,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      message.success(pacienteEditar ? 'Paciente actualizado exitosamente' : 'Paciente registrado exitosamente');

      if (onSuccess) {
        onSuccess(response.data);
      }

      form.resetFields();
      setFormData({});
      setCurrentStep(0);
      onClose();
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al guardar el paciente');
    } finally {
      setLoading(false);
    }
  }, [formData, pacienteEditar, form, message, onSuccess, onClose]);

  const nextStep = useCallback(async () => {
    try {
      const values = await form.validateFields();
      setFormData(prev => ({ ...prev, ...values }));
      setCurrentStep(prev => prev + 1);
    } catch (error) {
    }
  }, [form]);

  const prevStep = useCallback(() => {
    setCurrentStep(prev => prev - 1);
  }, []);

  const steps = [
    {
      title: 'Datos Personales',
      icon: <UserOutlined />,
      content: <PasoDatosPersonalesReg />
    },
    {
      title: 'Contacto',
      icon: <PhoneOutlined />,
      content: <PasoContactoReg />
    },
    {
      title: 'Datos Clínicos',
      icon: <MedicineBoxOutlined />,
      content: <PasoDatosClinicosReg />
    }
  ];

  return (
    <Modal
      title={
        <Space>
          <UserOutlined style={{ fontSize: 20, color: '#1890ff' }} />
          <span style={{ fontSize: 18, fontWeight: 600 }}>
            {pacienteEditar ? 'Editar Paciente' : 'Registro Completo de Paciente'}
          </span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      width={1000}
      footer={null}
      destroyOnHidden
      style={{ top: 20 }}
    >
      <Divider style={{ marginTop: 0 }} />

      {/* Progress Steps */}
      <div style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          {steps.map((step, index) => (
            <Col span={8} key={step.title}>
              <Card
                size="small"
                style={{
                  backgroundColor: currentStep === index ? '#e6f7ff' : currentStep > index ? '#f6ffed' : '#fafafa',
                  borderColor: currentStep === index ? '#1890ff' : currentStep > index ? '#52c41a' : '#d9d9d9',
                  cursor: 'pointer'
                }}
                onClick={() => setCurrentStep(index)}
              >
                <Space>
                  {currentStep > index ? (
                    <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                  ) : (
                    <span style={{
                      fontSize: 20,
                      color: currentStep === index ? '#1890ff' : '#8c8c8c'
                    }}>
                      {step.icon}
                    </span>
                  )}
                  <span style={{ fontWeight: currentStep === index ? 600 : 400 }}>
                    {step.title}
                  </span>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={currentStep === steps.length - 1 ? handleSubmit : nextStep}
        initialValues={formData}
      >
        <div style={{ minHeight: 400 }}>
          {steps[currentStep].content}
        </div>

        <Divider />

        <Row justify="space-between">
          <Col>
            {currentStep > 0 && (
              <Button onClick={prevStep}>
                Anterior
              </Button>
            )}
          </Col>
          <Col>
            <Space>
              <Button onClick={onClose}>
                Cancelar
              </Button>
              {currentStep < steps.length - 1 ? (
                <Button type="primary" htmlType="submit">
                  Siguiente
                </Button>
              ) : (
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<SaveOutlined />}
                >
                  {pacienteEditar ? 'Actualizar Paciente' : 'Registrar Paciente'}
                </Button>
              )}
            </Space>
          </Col>
        </Row>
      </Form>
    </Modal>
  );
};

export const BotonRegistroPacienteRapido: React.FC<{
  style?: React.CSSProperties;
  onSuccess?: (paciente: RegistroPacienteCompleto) => void;
}> = ({ style, onSuccess }) => {
  const [modalVisible, setModalVisible] = useState(false);

  return (
    <>
      <Button
        type="primary"
        size="large"
        icon={<UserOutlined />}
        onClick={() => setModalVisible(true)}
        style={{
          ...style,
          height: 48,
          fontSize: 16,
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)'
        }}
      >
        Registrar Nuevo Paciente
      </Button>

      <ModalRegistroPacienteCompleto
        open={modalVisible}
        onClose={() => setModalVisible(false)}
        onSuccess={(paciente) => {
          setModalVisible(false);
          if (onSuccess) onSuccess(paciente);
        }}
      />
    </>
  );
};
