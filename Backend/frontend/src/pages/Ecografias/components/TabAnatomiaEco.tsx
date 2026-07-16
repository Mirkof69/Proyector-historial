import React from 'react';
import { Card, Form, InputNumber, Row, Col, Divider, Typography, Checkbox, Radio, Input } from 'antd';

const { Title } = Typography;
const { TextArea } = Input;

const TabAnatomiaEco: React.FC = () => (
  <Card className="shadow-sm">
    <Row gutter={24}>
      <Col xs={24} md={8}>
        <Title level={5}>Cabeza y Cuello</Title>
        <Form.Item name={['anatomia', 'craneo_normal']} valuePropName="checked"><Checkbox>Cráneo Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'cerebro_normal']} valuePropName="checked"><Checkbox>Cerebro Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'cerebelo_normal']} valuePropName="checked"><Checkbox>Cerebelo Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'perfil_facial_normal']} valuePropName="checked"><Checkbox>Perfil Facial Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'labios_normales']} valuePropName="checked"><Checkbox>Labios Normales</Checkbox></Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Title level={5}>Tórax y Abdomen</Title>
        <Form.Item name={['anatomia', 'corazon_normal']} valuePropName="checked"><Checkbox>Corazón Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'pulmones_normales']} valuePropName="checked"><Checkbox>Pulmones Normales</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'estomago_normal']} valuePropName="checked"><Checkbox>Estómago Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'rinones_normales']} valuePropName="checked"><Checkbox>Riñones Normales</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'vejiga_normal']} valuePropName="checked"><Checkbox>Vejiga Normal</Checkbox></Form.Item>
      </Col>
      <Col xs={24} md={8}>
        <Title level={5}>Esqueleto y Otros</Title>
        <Form.Item name={['anatomia', 'columna_normal']} valuePropName="checked"><Checkbox>Columna Vertebral Normal</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'extremidades_superiores_normales']} valuePropName="checked"><Checkbox>Extremidades Superiores</Checkbox></Form.Item>
        <Form.Item name={['anatomia', 'extremidades_inferiores_normales']} valuePropName="checked"><Checkbox>Extremidades Inferiores</Checkbox></Form.Item>
        <Divider />
        <Form.Item name={['anatomia', 'sexo_fetal']} label="Sexo Fetal"><Radio.Group><Radio value="masculino">Masculino</Radio><Radio value="femenino">Femenino</Radio><Radio value="indeterminado">Indeterminado</Radio></Radio.Group></Form.Item>
      </Col>
    </Row>
    <Divider />
    <Row gutter={24}>
      <Col xs={24} md={12}><Form.Item name={['anatomia', 'translucencia_nucal']} label="Translucencia Nucal (mm)"><InputNumber step={0.1} style={{ width: '100%' }} /></Form.Item></Col>
      <Col xs={24} md={12}><Form.Item name={['anatomia', 'hueso_nasal_presente']} valuePropName="checked"><Checkbox>Hueso Nasal Presente</Checkbox></Form.Item></Col>
    </Row>
    <Form.Item name={['anatomia', 'hallazgos_anormales']} label="Hallazgos Anormales / Observaciones Anatómicas"><TextArea rows={3} /></Form.Item>
  </Card>
);

export default TabAnatomiaEco;
