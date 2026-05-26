import React from 'react';
import { Form, Row, Col, Select, InputNumber, Divider } from 'antd';

const { Option } = Select;

interface SeccionRecienNacidoProps {
  tipoEvento: 'aborto' | 'parto' | null;
}

export const SeccionRecienNacido: React.FC<SeccionRecienNacidoProps> = ({ tipoEvento }) => {
  if (tipoEvento !== 'parto') return null;

  return (
    <>
      <Divider orientation="left">Datos del Recién Nacido</Divider>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item
            name="sexo_bebe"
            label="Sexo"
            rules={[{ required: true, message: 'Seleccione sexo' }]}
          >
            <Select placeholder="Seleccione sexo">
              <Option value="masculino">Masculino</Option>
              <Option value="femenino">Femenino</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            name="peso_bebe"
            label="Peso (g)"
            rules={[{ required: true, message: 'Ingrese peso' }]}
          >
            <InputNumber min={300} max={6000} style={{ width: '100%' }} placeholder="3200" />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item
            name="talla_bebe"
            label="Talla (cm)"
            rules={[{ required: true, message: 'Ingrese talla' }]}
          >
            <InputNumber min={20} max={60} step={0.1} style={{ width: '100%' }} placeholder="50.0" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="apgar_1min"
            label="Apgar 1 min"
            rules={[{ required: true, message: 'Ingrese Apgar 1 min' }]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="apgar_5min"
            label="Apgar 5 min"
            rules={[{ required: true, message: 'Ingrese Apgar 5 min' }]}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>
    </>
  );
};
