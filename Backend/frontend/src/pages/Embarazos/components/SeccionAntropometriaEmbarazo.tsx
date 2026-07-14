import React from 'react';
import { Divider, Row, Col, Form, InputNumber, Alert, Input } from 'antd';

const { TextArea } = Input;

interface SeccionAntropometriaEmbarazoProps {
  imcCalculado: string;
  onCalcularIMC: () => void;
}

const SeccionAntropometriaEmbarazo: React.FC<SeccionAntropometriaEmbarazoProps> = ({ imcCalculado, onCalcularIMC }) => (
  <>
    <Divider orientation="left">Datos Antropométricos Maternos</Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="peso_pregestacional"
          label="Peso Pregestacional (kg)"
          rules={[{ type: 'number', min: 30, max: 200, message: 'El peso debe estar entre 30 y 200 kg' }]}
          tooltip="Peso de la madre antes del embarazo"
        >
          <InputNumber style={{ width: '100%' }} min={30} max={200} step={0.1} placeholder="Ej: 65.5" onChange={onCalcularIMC} />
        </Form.Item>
      </Col>

      <Col span={8}>
        <Form.Item
          name="talla_materna"
          label="Talla Materna (cm)"
          rules={[{ type: 'number', min: 100, max: 230, message: 'La talla debe estar entre 100 y 230 cm' }]}
          tooltip="Estatura de la madre en centímetros"
        >
          <InputNumber style={{ width: '100%' }} min={100} max={230} step={0.1} placeholder="Ej: 165" onChange={onCalcularIMC} />
        </Form.Item>
      </Col>

      <Col span={8}>
        {imcCalculado && (
          <Alert message={imcCalculado} type="info" showIcon style={{ marginTop: 30 }} />
        )}
      </Col>
    </Row>

    <Divider orientation="left">Notas Medicas</Divider>

    <Form.Item name="notas" label="Notas y Observaciones">
      <TextArea rows={4} placeholder="Ingrese cualquier informacion adicional relevante" maxLength={1000} showCount />
    </Form.Item>
  </>
);

export default SeccionAntropometriaEmbarazo;
