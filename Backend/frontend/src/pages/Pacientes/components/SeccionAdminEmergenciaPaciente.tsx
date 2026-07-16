import React from 'react';
import { Form, Input, DatePicker, Row, Col, Select, Divider } from 'antd';
import { UserOutlined, PhoneOutlined } from '@ant-design/icons';

const { Option } = Select;

const SeccionAdminEmergenciaPaciente: React.FC = () => (
  <>
    <Divider orientation="left">Estado Administrativo</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="estado_paciente"
          label="Estado"
        >
          <Select placeholder="Seleccione estado">
            <Option value="activo">Activo</Option>
            <Option value="inactivo">Inactivo</Option>
            <Option value="trasladado">Trasladado</Option>
            <Option value="fallecido">Fallecido</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="fecha_baja"
          label="Fecha de Baja (si aplica)"
          tooltip="Solo si el paciente esta inactivo"
        >
          <DatePicker
            style={{ width: '100%' }}
            format="DD/MM/YYYY"
            placeholder="Seleccione fecha"
          />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Contacto de Emergencia</Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="contacto_emergencia_nombre"
          label="Nombre"
          rules={[
            {
              pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/,
              message: 'Solo letras y espacios',
            },
          ]}
        >
          <Input prefix={<UserOutlined />} placeholder="Nombre del contacto" />
        </Form.Item>
      </Col>

      <Col span={12}>
        <Form.Item
          name="contacto_emergencia_telefono"
          label="Telefono"
          rules={[
            {
              pattern: /^[0-9+\-\s()]*$/,
              message: 'Solo numeros y simbolos telefonicos',
            },
            {
              validator: (_, value) => {
                if (!value) return Promise.resolve();
                const clean = value.replace(/[\s\-()]/g, '');
                if (clean.length >= 7 && clean.length <= 8) return Promise.resolve();
                return Promise.reject(new Error('Telefono debe tener 7-8 digitos'));
              },
            },
          ]}
        >
          <Input prefix={<PhoneOutlined />} placeholder="Ej: 70123456" />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          name="contacto_emergencia_relacion"
          label="Relacion con el Paciente"
          rules={[
            {
              pattern: /^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$/,
              message: 'Solo letras y espacios',
            },
          ]}
        >
          <Input placeholder="Ej: Madre, Esposo, Hermano, etc." />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionAdminEmergenciaPaciente;
