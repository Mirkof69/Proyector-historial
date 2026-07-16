import React from 'react';
import { Card, Form, InputNumber, Button } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { DatosPaciente } from '../imcGananciaUtils';

interface IMCFormProps {
  form: FormInstance;
  onFinish: (formValues: DatosPaciente) => void;
}

const IMCForm: React.FC<IMCFormProps> = ({ form, onFinish }) => (
  <Card title="Datos de la Paciente" bordered={false}>
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Form.Item
        label="Peso Pregestacional (kg)"
        name="peso_pregestacional"
        rules={[{ required: true, message: 'Ingrese el peso pregestacional' }]}
      >
        <InputNumber
          min={30}
          max={200}
          step={0.1}
          style={{ width: '100%' }}
          placeholder="Ej: 65.5"
        />
      </Form.Item>

      <Form.Item
        label="Talla (cm)"
        name="talla"
        rules={[{ required: true, message: 'Ingrese la talla' }]}
      >
        <InputNumber
          min={130}
          max={200}
          step={0.1}
          style={{ width: '100%' }}
          placeholder="Ej: 165"
        />
      </Form.Item>

      <Form.Item
        label="Peso Actual (kg)"
        name="peso_actual"
        rules={[{ required: true, message: 'Ingrese el peso actual' }]}
      >
        <InputNumber
          min={30}
          max={200}
          step={0.1}
          style={{ width: '100%' }}
          placeholder="Ej: 72.3"
        />
      </Form.Item>

      <Form.Item
        label="Semanas de Gestación"
        name="semanas_gestacion"
        rules={[{ required: true, message: 'Ingrese las semanas de gestación' }]}
      >
        <InputNumber
          min={1}
          max={42}
          step={1}
          style={{ width: '100%' }}
          placeholder="Ej: 24"
        />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} block size="large">
          Calcular IMC y Ganancia
        </Button>
      </Form.Item>
    </Form>
  </Card>
);

export default IMCForm;
