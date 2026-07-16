import React from 'react';
import { Modal, Form, Input, DatePicker, Select, Row, Col, Divider, Button, Steps } from 'antd';
import {
  UserOutlined, HomeOutlined, MedicineBoxOutlined, IdcardOutlined,
  PhoneOutlined, MailOutlined, GlobalOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import type { FormInstance } from 'antd';
import dayjs from 'dayjs';
import locale from 'antd/es/date-picker/locale/es_ES';
import { Paciente } from '../pacientesTypes';

const { Option } = Select;
const { Step } = Steps;

const USER_ICON = <UserOutlined />;
const HOME_ICON_2 = <HomeOutlined />;
const MEDICINE_BOX_ICON_4 = <MedicineBoxOutlined />;
const CHECK_CIRCLE_ICON_5 = <CheckCircleOutlined />;

interface PacienteWizardModalProps {
  modalVisible: boolean;
  editingPaciente: Paciente | null;
  currentStep: number;
  setCurrentStep: React.Dispatch<React.SetStateAction<number>>;
  form: FormInstance;
  formLoading: boolean;
  handleSubmit: () => void;
  onCancel: () => void;
}

const PacienteWizardModal: React.FC<PacienteWizardModalProps> = ({
  modalVisible, editingPaciente, currentStep, setCurrentStep, form, formLoading,
  handleSubmit, onCancel,
}) => (
  <Modal
    title={editingPaciente ? `Editar: ${editingPaciente.nombre_completo}` : 'Registro de Nuevo Paciente'}
    open={modalVisible}
    onCancel={onCancel}
    footer={null}
    width={800}
    maskClosable={false}
  >
    <Steps current={currentStep} style={{ marginBottom: 24 }} size="small">
      <Step title="Datos Personales" icon={USER_ICON} />
      <Step title="Contacto" icon={HOME_ICON_2} />
      <Step title="Información Médica" icon={MEDICINE_BOX_ICON_4} />
    </Steps>

    <Form
      form={form}
      layout="vertical"
      initialValues={{ pais: 'Bolivia', activo: true }}
    >
      {/* PASO 1: DATOS PERSONALES */}
      <div style={{ display: currentStep === 0 ? 'block' : 'none' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="nombre" label="Nombres" rules={[{ required: true, message: 'Requerido' }]}>
              <Input prefix={<UserOutlined />} placeholder="Ej: Ana María" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="apellido_paterno" label="Apellido Paterno" rules={[{ required: true, message: 'Requerido' }]}>
              <Input placeholder="Ej: Flores" />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="apellido_materno" label="Apellido Materno">
              <Input placeholder="Ej: Quispe" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="ci" label="Cédula de Identidad" rules={[{ required: true, message: 'Requerido' }, { pattern: /^[0-9]{5,10}$/, message: '5-10 dígitos' }]}>
              <Input prefix={<IdcardOutlined />} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="fecha_nacimiento" label="Fecha de Nacimiento" rules={[{ required: true, message: 'Seleccione fecha' }]}>
              <DatePicker
                style={{ width: '100%' }}
                format="DD/MM/YYYY"
                locale={locale}
                disabledDate={(d) => d && d > dayjs()}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="genero" label="Género" rules={[{ required: true }]}>
              <Select>
                <Option value="femenino">Femenino</Option>
                <Option value="masculino">Masculino</Option>
                <Option value="otro">Otro</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </div>

      {/* PASO 2: CONTACTO */}
      <div style={{ display: currentStep === 1 ? 'block' : 'none' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="telefono" label="Teléfono / Celular" rules={[{ pattern: /^[0-9]{7,8}$/, message: 'Número inválido (7-8 dígitos)' }]}>
              <Input prefix={<PhoneOutlined />} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="email" label="Correo Electrónico" rules={[{ type: 'email' }]}>
              <Input prefix={<MailOutlined />} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="direccion" label="Dirección Domiciliaria">
          <Input prefix={<HomeOutlined />} />
        </Form.Item>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="ciudad" label="Ciudad">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="pais" label="País">
              <Input prefix={<GlobalOutlined />} />
            </Form.Item>
          </Col>
        </Row>
      </div>

      {/* PASO 3: EXTRA */}
      <div style={{ display: currentStep === 2 ? 'block' : 'none' }}>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="grupo_sanguineo" label="Grupo Sanguíneo">
              <Select placeholder="Seleccione...">
                <Option value="O+">O+</Option>
                <Option value="O-">O-</Option>
                <Option value="A+">A+</Option>
                <Option value="A-">A-</Option>
                <Option value="B+">B+</Option>
                <Option value="B-">B-</Option>
                <Option value="AB+">AB+</Option>
                <Option value="AB-">AB-</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="estado_civil" label="Estado Civil">
              <Select>
                <Option value="soltero">Soltero/a</Option>
                <Option value="casado">Casado/a</Option>
                <Option value="union_libre">Unión Libre</Option>
                <Option value="divorciado">Divorciado/a</Option>
                <Option value="viudo">Viudo/a</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="peso_kg"
              label="Peso (kg)"
              rules={[
                {
                  pattern: /^\d+(\.\d{1,2})?$/,
                  message: 'Ingrese un peso válido'
                }
              ]}
            >
              <Input
                type="number"
                placeholder="Ej: 65.5"
                suffix="kg"
                step="0.1"
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="altura_cm"
              label="Altura (cm)"
              rules={[
                {
                  pattern: /^\d+(\.\d{1,2})?$/,
                  message: 'Ingrese una altura válida'
                }
              ]}
            >
              <Input
                type="number"
                placeholder="Ej: 165"
                suffix="cm"
                step="0.1"
              />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="ocupacion" label="Ocupación">
          <Input />
        </Form.Item>
        <Form.Item name="observaciones" label="Observaciones / Antecedentes Breves">
          <Input.TextArea rows={3} />
        </Form.Item>
      </div>
    </Form>

    <Divider />

    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
      <Button disabled={currentStep === 0} onClick={() => setCurrentStep(prev => prev - 1)}>
        Atrás
      </Button>
      {currentStep < 2 && (
        <Button type="primary" onClick={() => setCurrentStep(prev => prev + 1)}>
          Siguiente
        </Button>
      )}
      {currentStep === 2 && (
        <Button type="primary" icon={CHECK_CIRCLE_ICON_5} onClick={handleSubmit} loading={formLoading}>
          {editingPaciente ? 'Guardar Cambios' : 'Registrar Paciente'}
        </Button>
      )}
    </div>
  </Modal>
);

export default PacienteWizardModal;
