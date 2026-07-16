import React from 'react';
import { Form, Row, Col, Input, DatePicker, Select, Divider } from 'antd';
import { ESTADO_CIVIL_OPTS } from '../../utils';

const PasoDatosPersonalesReg: React.FC = () => (
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
);

export default PasoDatosPersonalesReg;
