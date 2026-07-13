import React, { useState, useCallback } from 'react';
import {
  Modal,
  Form,
  Row,
  Col,
  Input,
  DatePicker,
  Select,
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
import dayjs from 'dayjs';
import { useAntdApp } from '../../../hooks/useMessage';
import { useAuth } from '../../../hooks/useAuth';
import { API_URL } from '../../../services/api';
import { ESTADO_CIVIL_OPTS } from '../utils';

export interface RegistroPacienteCompleto {
  // Datos demográficos
  id_clinico: string;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  cedula_identidad: string;
  fecha_nacimiento: string;
  edad: number;
  sexo: 'F' | 'M';

  // Contacto
  telefono: string;
  celular?: string;
  email?: string;
  direccion: string;
  ciudad: string;
  provincia: string;
  codigo_postal?: string;

  // Datos obstétricos
  grupo_sanguineo?: string;
  factor_rh?: string;
  gestas_previas?: number;
  partos_previos?: number;
  cesareas_previas?: number;
  abortos_previos?: number;
  hijos_vivos?: number;

  // Antecedentes médicos
  antecedentes_personales: string[];
  antecedentes_familiares: string[];
  alergias: string[];
  medicamentos_actuales: string[];
  cirugias_previas: string[];

  // Datos sociales
  estado_civil?: string;
  ocupacion?: string;
  nivel_educativo?: string;
  seguro_medico?: string;
  numero_seguro?: string;

  // Contacto de emergencia
  emergencia_nombre?: string;
  emergencia_telefono?: string;
  emergencia_relacion?: string;

  // Auditoría
  fecha_registro: string;
  activo: boolean;
}

export const ModalRegistroPacienteCompleto: React.FC<{
  open: boolean;
  onClose: () => void;
  onSuccess?: (paciente: RegistroPacienteCompleto) => void;
  pacienteEditar?: Partial<RegistroPacienteCompleto>;
}> = ({ open, onClose, onSuccess, pacienteEditar }) => {
  const { message } = useAntdApp();
  const [form] = Form.useForm();
  const { getToken } = useAuth();
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

      const response = await axios({
        method,
        url: endpoint,
        data: datosCompletos,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
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
  }, [formData, pacienteEditar, form, message, onSuccess, onClose, getToken]);

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
      content: (
        <>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Nombre"
                name="nombre"
                rules={[{ required: true, message: 'Nombre requerido' }]}
              >
                <Input placeholder="Nombre(s)" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Apellido Paterno"
                name="apellido_paterno"
                rules={[{ required: true, message: 'Apellido requerido' }]}
              >
                <Input placeholder="Apellido Paterno" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Apellido Materno"
                name="apellido_materno"
              >
                <Input placeholder="Apellido Materno" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Cédula de Identidad"
                name="cedula_identidad"
                rules={[
                  { required: true, message: 'CI requerida' },
                  { pattern: /^[0-9]{6,10}$/, message: 'CI inválida' }
                ]}
              >
                <Input placeholder="12345678" maxLength={10} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Fecha de Nacimiento"
                name="fecha_nacimiento"
                rules={[{ required: true, message: 'Fecha requerida' }]}
              >
                <DatePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  placeholder="Seleccione fecha"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Sexo"
                name="sexo"
                rules={[{ required: true, message: 'Sexo requerido' }]}
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="F">Femenino</Select.Option>
                  <Select.Option value="M">Masculino</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Estado Civil"
                name="estado_civil"
              >
                <Select placeholder="Seleccione">
                  {ESTADO_CIVIL_OPTS.map((estado) => (
                    <Select.Option key={estado} value={estado.toLowerCase().replace(/ /g, '_')}>
                      {estado}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Ocupación"
                name="ocupacion"
              >
                <Input placeholder="Profesión u ocupación" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Nivel Educativo"
                name="nivel_educativo"
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="primaria">Primaria</Select.Option>
                  <Select.Option value="secundaria">Secundaria</Select.Option>
                  <Select.Option value="tecnico">Técnico</Select.Option>
                  <Select.Option value="universitario">Universitario</Select.Option>
                  <Select.Option value="postgrado">Postgrado</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </>
      )
    },
    {
      title: 'Contacto',
      icon: <PhoneOutlined />,
      content: (
        <>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Teléfono"
                name="telefono"
                rules={[
                  { required: true, message: 'Teléfono requerido' },
                  { pattern: /^[0-9]{7,10}$/, message: 'Teléfono inválido' }
                ]}
              >
                <Input placeholder="12345678" maxLength={10} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Celular"
                name="celular"
                rules={[
                  { pattern: /^[0-9]{8,10}$/, message: 'Celular inválido' }
                ]}
              >
                <Input placeholder="70123456" maxLength={10} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Email"
                name="email"
                rules={[
                  { type: 'email', message: 'Email inválido' }
                ]}
              >
                <Input placeholder="email@ejemplo.com" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                label="Dirección"
                name="direccion"
                rules={[{ required: true, message: 'Dirección requerida' }]}
              >
                <Input.TextArea
                  rows={2}
                  placeholder="Dirección completa (Calle, Número, Zona, Referencia)"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Ciudad"
                name="ciudad"
                rules={[{ required: true, message: 'Ciudad requerida' }]}
              >
                <Input placeholder="Ciudad" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Provincia/Departamento"
                name="provincia"
                rules={[{ required: true, message: 'Provincia requerida' }]}
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="La Paz">La Paz</Select.Option>
                  <Select.Option value="Santa Cruz">Santa Cruz</Select.Option>
                  <Select.Option value="Cochabamba">Cochabamba</Select.Option>
                  <Select.Option value="Oruro">Oruro</Select.Option>
                  <Select.Option value="Potosí">Potosí</Select.Option>
                  <Select.Option value="Chuquisaca">Chuquisaca</Select.Option>
                  <Select.Option value="Tarija">Tarija</Select.Option>
                  <Select.Option value="Beni">Beni</Select.Option>
                  <Select.Option value="Pando">Pando</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Código Postal"
                name="codigo_postal"
              >
                <Input placeholder="0000" maxLength={4} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Contacto de Emergencia</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Nombre Completo"
                name="emergencia_nombre"
                rules={[{ required: true, message: 'Nombre requerido' }]}
              >
                <Input placeholder="Nombre del contacto" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Teléfono"
                name="emergencia_telefono"
                rules={[
                  { required: true, message: 'Teléfono requerido' },
                  { pattern: /^[0-9]{7,10}$/, message: 'Teléfono inválido' }
                ]}
              >
                <Input placeholder="12345678" maxLength={10} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Relación"
                name="emergencia_relacion"
                rules={[{ required: true, message: 'Relación requerida' }]}
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="Esposo/a">Esposo/a</Select.Option>
                  <Select.Option value="Padre/Madre">Padre/Madre</Select.Option>
                  <Select.Option value="Hermano/a">Hermano/a</Select.Option>
                  <Select.Option value="Hijo/a">Hijo/a</Select.Option>
                  <Select.Option value="Otro familiar">Otro familiar</Select.Option>
                  <Select.Option value="Amigo/a">Amigo/a</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </>
      )
    },
    {
      title: 'Datos Clínicos',
      icon: <MedicineBoxOutlined />,
      content: (
        <>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Grupo Sanguíneo"
                name="grupo_sanguineo"
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="A">A</Select.Option>
                  <Select.Option value="B">B</Select.Option>
                  <Select.Option value="AB">AB</Select.Option>
                  <Select.Option value="O">O</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Factor RH"
                name="factor_rh"
              >
                <Select placeholder="Seleccione">
                  <Select.Option value="Positivo">Positivo (+)</Select.Option>
                  <Select.Option value="Negativo">Negativo (-)</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Seguro Médico"
                name="seguro_medico"
              >
                <Input placeholder="Nombre del seguro" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Antecedentes Obstétricos</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Gestas Previas"
                name="gestas_previas"
              >
                <Input type="number" min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Partos Previos"
                name="partos_previos"
              >
                <Input type="number" min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Cesáreas Previas"
                name="cesareas_previas"
              >
                <Input type="number" min={0} placeholder="0" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                label="Abortos Previos"
                name="abortos_previos"
              >
                <Input type="number" min={0} placeholder="0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Hijos Vivos"
                name="hijos_vivos"
              >
                <Input type="number" min={0} placeholder="0" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Antecedentes Médicos</Divider>

          <Form.Item
            label="Antecedentes Personales"
            name="antecedentes_personales"
            tooltip="Enfermedades crónicas, cirugías previas, etc."
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Agregue antecedentes personales"
              tokenSeparators={[',']}
            >
              <Select.Option value="Diabetes">Diabetes</Select.Option>
              <Select.Option value="Hipertensión">Hipertensión</Select.Option>
              <Select.Option value="Asma">Asma</Select.Option>
              <Select.Option value="Epilepsia">Epilepsia</Select.Option>
              <Select.Option value="Cardiopatía">Cardiopatía</Select.Option>
              <Select.Option value="Nefropatía">Nefropatía</Select.Option>
              <Select.Option value="Hipotiroidismo">Hipotiroidismo</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Antecedentes Familiares"
            name="antecedentes_familiares"
            tooltip="Enfermedades hereditarias en la familia"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Agregue antecedentes familiares"
              tokenSeparators={[',']}
            >
              <Select.Option value="Diabetes">Diabetes</Select.Option>
              <Select.Option value="Hipertensión">Hipertensión</Select.Option>
              <Select.Option value="Cáncer">Cáncer</Select.Option>
              <Select.Option value="Cardiopatías">Cardiopatías</Select.Option>
              <Select.Option value="Malformaciones congénitas">Malformaciones congénitas</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Alergias"
            name="alergias"
            tooltip="Alergias a medicamentos, alimentos, etc."
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Agregue alergias conocidas"
              tokenSeparators={[',']}
            >
              <Select.Option value="Penicilina">Penicilina</Select.Option>
              <Select.Option value="Sulfas">Sulfas</Select.Option>
              <Select.Option value="AINEs">AINEs</Select.Option>
              <Select.Option value="Yodo">Yodo</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Medicamentos Actuales"
            name="medicamentos_actuales"
            tooltip="Medicamentos que toma regularmente"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Agregue medicamentos actuales"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            label="Cirugías Previas"
            name="cirugias_previas"
          >
            <Select
              mode="tags"
              style={{ width: '100%' }}
              placeholder="Agregue cirugías previas"
              tokenSeparators={[',']}
            >
              <Select.Option value="Cesárea">Cesárea</Select.Option>
              <Select.Option value="Apendicectomía">Apendicectomía</Select.Option>
              <Select.Option value="Colecistectomía">Colecistectomía</Select.Option>
              <Select.Option value="Histerectomía">Histerectomía</Select.Option>
            </Select>
          </Form.Item>
        </>
      )
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
