import React from 'react';
import { Card, Form, Input, Button, Select, Switch, Typography, Space } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { logger } from '../../utils/logger';

const { Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const handleFinish = (values: any) => {
  logger.log('Guardar antecedente patológico:', values);
};

const FormularioAntecedentePatologico: React.FC = () => {
  const [form] = Form.useForm();

  return (
    <Card title={<span style={{ fontSize: 18, fontWeight: 600 }}>Formulario de Antecedente Patológico</span>}>
      <Form form={form} layout="vertical" onFinish={handleFinish} style={{ maxWidth: 800 }}>
        <Title level={5}>Información General</Title>
        <Form.Item name="paciente" label="Paciente" rules={[{ required: true }]}>
          <Select placeholder="Seleccione un paciente" showSearch>
            <Option value={1}>Paciente 1</Option>
            <Option value={2}>Paciente 2</Option>
          </Select>
        </Form.Item>
        <Form.Item name="tipo" label="Tipo" rules={[{ required: true }]}>
          <Select placeholder="Seleccione tipo">
            <Option value="personal">Personales</Option>
            <Option value="heredofamiliar">Heredofamiliares</Option>
          </Select>
        </Form.Item>

        <Title level={5}>Alergias</Title>
        <Form.Item name="tiene_alergias" label="Tiene Alergias" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item name="alergias_medicamentos" label="Alergias a Medicamentos">
          <Input placeholder="Ej: Penicilina, sulfa" />
        </Form.Item>
        <Form.Item name="alergias_alimentos" label="Alergias a Alimentos">
          <Input placeholder="Ej: Mariscos, maní" />
        </Form.Item>

        <Title level={5}>Enfermedades Crónicas</Title>
        <Form.Item name="diabetes" label="Diabetes" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item name="hipertension" label="Hipertensión" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item name="asma" label="Asma" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item name="cardiopatias" label="Cardiopatías" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Title level={5}>Antecedentes Obstétricos Específicos</Title>
        <Form.Item name="preeclampsia_previa" label="Preeclampsia Previa" valuePropName="checked">
          <Switch />
        </Form.Item>
        <Form.Item name="diabetes_gestacional_previa" label="Diabetes Gestacional Previa" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item name="otras_enfermedades" label="Otras Enfermedades">
          <TextArea rows={3} placeholder="Describa otras enfermedades o condiciones relevantes" />
        </Form.Item>
        <Form.Item name="cirugias_anteriores" label="Cirugías Anteriores">
          <TextArea rows={3} placeholder="Describa cirugías previas" />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>Guardar</Button>
            <Button icon={<CloseOutlined />}>Cancelar</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default FormularioAntecedentePatologico;
