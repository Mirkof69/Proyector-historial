import React from 'react';
import { Form, Row, Col, Input, Select, Divider } from 'antd';

const PasoContactoReg: React.FC = () => (
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
);

export default PasoContactoReg;
