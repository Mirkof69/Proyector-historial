import React from 'react';
import { Card, Form, Select, InputNumber, Row, Col, Divider, Typography, Checkbox, Radio } from 'antd';

const { Option } = Select;
const { Title } = Typography;

const TabAnexosEco: React.FC = () => (
  <Card className="shadow-sm">
    <Row gutter={24}>
      <Col xs={24} md={12}>
        <Title level={5}>Placenta</Title>
        <Form.Item name={['anexos', 'placenta_localizacion']} label="Localización"><Select><Option value="anterior">Anterior</Option><Option value="posterior">Posterior</Option><Option value="fundica">Fúndica</Option><Option value="lateral_derecha">Lateral Derecha</Option><Option value="lateral_izquierda">Lateral Izquierda</Option><Option value="previa_marginal">Previa Marginal</Option><Option value="previa_oclusiva">Previa Oclusiva Total</Option></Select></Form.Item>
        <Form.Item name={['anexos', 'grado_madurez_placenta']} label="Grado de Madurez (Grannum)"><Select><Option value={0}>Grado 0</Option><Option value={1}>Grado I</Option><Option value={2}>Grado II</Option><Option value={3}>Grado III</Option></Select></Form.Item>
        <Form.Item name={['anexos', 'placenta_previa']} valuePropName="checked"><Checkbox>Placenta Previa</Checkbox></Form.Item>
      </Col>
      <Col xs={24} md={12}>
        <Title level={5}>Líquido Amniótico y Cordón</Title>
        <Form.Item name={['anexos', 'liquido_amniotico_normal']} valuePropName="checked"><Checkbox>Líquido Amniótico Normal</Checkbox></Form.Item>
        <Row gutter={16}><Col span={12}><Form.Item name="indice_liquido_amniotico" label="ILA (cm)"><InputNumber step={0.1} style={{ width: '100%' }} /></Form.Item></Col><Col span={12}><Form.Item name="bolsillo_maximo" label="Bolsillo Máx (cm)"><InputNumber step={0.1} style={{ width: '100%' }} /></Form.Item></Col></Row>
        <Form.Item name={['anexos', 'numero_vasos_cordon']} label="Vasos del Cordón"><Radio.Group><Radio value={3}>3 Vasos</Radio><Radio value={2}>2 Vasos (AUU)</Radio></Radio.Group></Form.Item>
        <Form.Item name={['anexos', 'circular_cordon']} valuePropName="checked"><Checkbox>Circular de Cordón</Checkbox></Form.Item>
      </Col>
    </Row>
    <Divider />
    <Row gutter={24}><Col xs={24} md={12}><Form.Item name={['anexos', 'longitud_cervical']} label="Longitud Cervical (mm)"><InputNumber style={{ width: '100%' }} /></Form.Item></Col></Row>
  </Card>
);

export default TabAnexosEco;
