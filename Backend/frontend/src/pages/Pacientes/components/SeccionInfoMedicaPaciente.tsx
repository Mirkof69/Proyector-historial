import React from 'react';
import { Form, Input, InputNumber, Row, Col, Select, Divider, Alert } from 'antd';
import { RiseOutlined } from '@ant-design/icons';

const { Option } = Select;

interface SeccionInfoMedicaPacienteProps {
  calcularIMC: () => void;
  imcCalculado: string;
}

const SeccionInfoMedicaPaciente: React.FC<SeccionInfoMedicaPacienteProps> = ({ calcularIMC, imcCalculado }) => (
  <>
    <Divider orientation="left">Informacion Medica</Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="tipo_sangre"
          label="Tipo de Sangre"
        >
          <Select placeholder="Seleccione tipo de sangre">
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

      <Col span={8}>
        <Form.Item
          name="factor_rh"
          label="Factor RH"
        >
          <Select placeholder="Seleccione factor RH">
            <Option value="positivo">Positivo</Option>
            <Option value="negativo">Negativo</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="numero_seguro_social"
          label="Numero de Seguro Social"
          rules={[
            {
              pattern: /^[0-9-]*$/,
              message: 'Solo numeros y guiones',
            },
          ]}
          tooltip="Numero del seguro o afiliacion medica"
        >
          <Input placeholder="Ej: 123456789-0" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="peso_kg"
          label="Peso (kg)"
          rules={[
            {
              type: 'number',
              min: 20,
              max: 200,
              message: 'El peso debe estar entre 20 y 200 kg',
            },
          ]}
          tooltip="Peso actual del paciente en kilogramos"
        >
          <InputNumber
            style={{ width: '100%' }}
            min={20}
            max={200}
            step={0.1}
            placeholder="Ej: 65.5"
            prefix={<RiseOutlined />}
            onChange={calcularIMC}
          />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="altura_cm"
          label="Altura (cm)"
          rules={[
            {
              type: 'number',
              min: 100,
              max: 220,
              message: 'La altura debe estar entre 100 y 220 cm',
            },
          ]}
          tooltip="Altura del paciente en centimetros"
        >
          <InputNumber
            style={{ width: '100%' }}
            min={100}
            max={220}
            step={0.1}
            placeholder="Ej: 165"
            prefix={<RiseOutlined />}
            onChange={calcularIMC}
          />
        </Form.Item>
      </Col>

      <Col span={8}>
        {imcCalculado && (
          <Alert
            message={imcCalculado}
            type="info"
            showIcon
            style={{ marginTop: 30 }}
          />
        )}
      </Col>
    </Row>
  </>
);

export default SeccionInfoMedicaPaciente;
