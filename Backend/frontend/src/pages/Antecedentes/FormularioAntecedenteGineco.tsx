import React from 'react';
import { Card, Form, Input, Button, Select, InputNumber, Typography, Space } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import { logger } from '../../utils/logger';

const { Title } = Typography;
const { Option } = Select;

const handleFinish = (values: any) => {
  logger.log('Guardar antecedente gineco:', values);
};

const FormularioAntecedenteGineco: React.FC = () => {
  const [form] = Form.useForm();

  return (
    <Card title={<span style={{ fontSize: 18, fontWeight: 600 }}>Formulario de Antecedente Gineco-Obstétrico</span>}>
      <Form form={form} layout="vertical" onFinish={handleFinish} style={{ maxWidth: 800 }}>
        <Title level={5}>Datos de Menstruación</Title>
        <Form.Item name="menarquia_edad" label="Edad de Menarquia">
          <InputNumber min={8} max={20} style={{ width: '100%' }} placeholder="Ej: 12" />
        </Form.Item>
        <Form.Item name="ciclos_menstruales" label="Tipo de Ciclo">
          <Select placeholder="Seleccione tipo">
            <Option value="regular">Regular</Option>
            <Option value="irregular">Irregular</Option>
            <Option value="amenorrea">Amenorrea</Option>
          </Select>
        </Form.Item>
        <Form.Item name="duracion_ciclo_dias" label="Duración del Ciclo (días)">
          <InputNumber min={20} max={45} style={{ width: '100%' }} placeholder="Ej: 28" />
        </Form.Item>
        <Form.Item name="duracion_menstruacion_dias" label="Duración de Menstruación (días)">
          <InputNumber min={2} max={10} style={{ width: '100%' }} placeholder="Ej: 5" />
        </Form.Item>

        <Title level={5}>Fórmula Obstétrica (GPAC)</Title>
        <Form.Item name="gestas" label="Gestas (G)" rules={[{ required: true }]}>
          <InputNumber min={0} style={{ width: '100%' }} placeholder="Número total de embarazos" />
        </Form.Item>
        <Form.Item name="partos" label="Partos (P)">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="Número de partos" />
        </Form.Item>
        <Form.Item name="abortos" label="Abortos (A)">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="Número de abortos" />
        </Form.Item>
        <Form.Item name="cesareas" label="Cesáreas (C)">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="Número de cesáreas" />
        </Form.Item>
        <Form.Item name="hijos_vivos" label="Hijos Vivos">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="Número de hijos vivos" />
        </Form.Item>

        <Title level={5}>Vida Sexual y Anticoncepción</Title>
        <Form.Item name="inicio_vida_sexual_edad" label="Inicio de Vida Sexual (edad)">
          <InputNumber min={10} max={60} style={{ width: '100%' }} placeholder="Ej: 18" />
        </Form.Item>
        <Form.Item name="numero_parejas_sexuales" label="Número de Parejas Sexuales">
          <InputNumber min={1} style={{ width: '100%' }} placeholder="Ej: 1" />
        </Form.Item>
        <Form.Item name="metodo_anticonceptivo_actual" label="Método Anticonceptivo Actual">
          <Select placeholder="Seleccione método" allowClear>
            <Option value="ninguno">Ninguno</Option>
            <Option value="aoc">Anticonceptivos Orales</Option>
            <Option value="condon">Condón</Option>
            <Option value="diu">DIU</Option>
            <Option value="implante">Implante Subdérmico</Option>
            <Option value="ligadura">Ligadura de Trompas</Option>
            <Option value="vasectomia">Vasectomía</Option>
          </Select>
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

export default FormularioAntecedenteGineco;
