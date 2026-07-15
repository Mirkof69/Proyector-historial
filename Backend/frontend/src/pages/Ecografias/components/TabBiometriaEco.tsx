import React from 'react';
import { Card, Form, InputNumber, Row, Col, Divider, Alert } from 'antd';

const TabBiometriaEco: React.FC = () => (
  <Card className="shadow-sm">
    <Alert message="Mediciones Biométricas" description="Ingrese las medidas en milímetros (mm). El peso fetal se calculará automáticamente si no se especifica." type="info" showIcon style={{ marginBottom: 24 }} />
    <Row gutter={24}>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'diametro_biparietal']} label="DBP (mm)"><InputNumber style={{ width: '100%' }} placeholder="Diámetro Biparietal" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'circunferencia_cefalica']} label="CC (mm)"><InputNumber style={{ width: '100%' }} placeholder="Circunferencia Cefálica" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'circunferencia_abdominal']} label="CA (mm)"><InputNumber style={{ width: '100%' }} placeholder="Circunferencia Abdominal" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'longitud_femur']} label="LF (mm)"><InputNumber style={{ width: '100%' }} placeholder="Longitud Fémur" /></Form.Item></Col>
    </Row>
    <Row gutter={24}>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'diametro_occipito_frontal']} label="DOF (mm)"><InputNumber style={{ width: '100%' }} placeholder="Diámetro Occípito-Frontal" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'longitud_humero']} label="LH (mm)"><InputNumber style={{ width: '100%' }} placeholder="Longitud Húmero" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'diametro_transverso_cerebelo']} label="DTC (mm)"><InputNumber style={{ width: '100%' }} placeholder="Diámetro Cerebelo" /></Form.Item></Col>
      <Col xs={24} md={6}><Form.Item name={['biometria', 'cisterna_magna']} label="Cisterna Magna (mm)"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
    </Row>
    <Divider />
    <Row gutter={24}>
      <Col xs={24} md={8}><Form.Item name={['biometria', 'peso_fetal_estimado']} label="Peso Fetal Estimado (g)"><InputNumber style={{ width: '100%' }} suffix="g" /></Form.Item></Col>
      <Col xs={24} md={8}><Form.Item name={['biometria', 'percentil_peso']} label="Percentil de Peso"><InputNumber min={1} max={100} style={{ width: '100%' }} /></Form.Item></Col>
    </Row>
  </Card>
);

export default TabBiometriaEco;
