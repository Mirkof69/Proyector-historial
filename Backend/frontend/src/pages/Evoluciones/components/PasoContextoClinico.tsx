import React from 'react';
import { Row, Col, Form, DatePicker, TimePicker, InputNumber, Select, Divider, Input, Space, Checkbox, Typography } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';

const { Text } = Typography;

const PasoContextoClinico: React.FC = () => (
  <div style={{ padding: '16px' }}>
    <Row gutter={24}>
      <Col xs={24} md={8}>
        <Form.Item label="Fecha de Atención" name="fecha" rules={[{ required: true }]}>
          <DatePicker style={{ width: '100%' }} size="large" format="DD/MM/YYYY" />
        </Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Form.Item label="Hora de Inicio" name="hora_atencion">
          <TimePicker style={{ width: '100%' }} size="large" format="HH:mm" />
        </Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Form.Item label="Duración (minutos)" name="duracion_consulta">
          <InputNumber style={{ width: '100%' }} size="large" min={1} max={300} placeholder="30" />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Clasificación Médica</Divider>

    <Row gutter={24}>
      <Col xs={24} md={12}>
        <Form.Item label="Tipo de Evento" name="tipo" rules={[{ required: true }]}>
          <Select
            size="large"
            options={[
              { label: 'Consulta General', value: 'consulta' },
              { label: 'Control Prenatal', value: 'control' },
              { label: 'Urgencia Obstétrica', value: 'urgencia' },
              { label: 'Seguimiento Telefónico', value: 'seguimiento' },
            ]}
          />
        </Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Form.Item label="Estado de la Nota" name="estado">
          <Select
            size="large"
            options={[
              { label: 'En Proceso / Borrador', value: 'pendiente' },
              { label: 'Completada / Cerrada', value: 'completado' },
            ]}
          />
        </Form.Item>
      </Col>
    </Row>

    <Divider orientation="left">Personal Responsable</Divider>

    <Row gutter={24}>
      <Col xs={24} md={12}>
        <Form.Item label="Médico Tratante" name="medico" rules={[{ required: true }]}>
          <Input prefix={<MedicineBoxOutlined />} placeholder="Nombre y especialidad" size="large" />
        </Form.Item>
      </Col>
      <Col xs={24} md={12} style={{ paddingTop: '32px' }}>
        <Space size="large">
          <Form.Item name="requiere_seguimiento" valuePropName="checked" noStyle>
            <Checkbox><Text strong>Requiere Seguimiento</Text></Checkbox>
          </Form.Item>
          <Form.Item name="es_urgente" valuePropName="checked" noStyle>
            <Checkbox><Text strong style={{ color: '#ff4d4f' }}>Marcar como Urgente</Text></Checkbox>
          </Form.Item>
        </Space>
      </Col>
    </Row>
  </div>
);

export default PasoContextoClinico;
