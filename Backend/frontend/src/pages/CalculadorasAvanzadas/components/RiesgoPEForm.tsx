import React from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Divider, Checkbox } from 'antd';
import { HeartOutlined, ExperimentOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { DatosRiesgo } from '../riesgoPreeclampsiaUtils';

const EXPERIMENT_ICON_2 = <ExperimentOutlined />;

interface RiesgoPEFormProps {
  form: FormInstance;
  onFinish: (values: DatosRiesgo) => void;
}

const RiesgoPEForm: React.FC<RiesgoPEFormProps> = ({ form, onFinish }) => (
  <Card title={
    <>
      <HeartOutlined /> Datos Maternos y Biomarcadores
    </>
  } className="form-card">
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item label="Edad (años)" name="edad" rules={[{ required: true }]} initialValue={28}>
            <InputNumber min={15} max={55} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Peso (kg)" name="peso" rules={[{ required: true }]} initialValue={65}>
            <InputNumber min={40} max={150} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Talla (cm)" name="talla" rules={[{ required: true }]} initialValue={160}>
            <InputNumber min={140} max={200} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Semanas Gestación" name="semanas" rules={[{ required: true }]} initialValue={12}>
            <InputNumber min={11} max={35} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider>Biomarcadores Séricos</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item label="PlGF (pg/mL)" name="plgf" rules={[{ required: true }]} initialValue={45.5}>
            <InputNumber min={1} max={3000} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="sFlt-1 (pg/mL)" name="sflt1" rules={[{ required: true }]} initialValue={1680}>
            <InputNumber min={100} max={15000} step={1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={24}>
          <Form.Item label="PAPP-A (mUI/mL)" name="pappa" rules={[{ required: true }]} initialValue={1.5}>
            <InputNumber min={0.1} max={10} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider>Biomarcadores Ecográficos</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item label="MAP (mmHg)" name="map" rules={[{ required: true }]} initialValue={88}>
            <InputNumber min={60} max={140} step={1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="UtA-PI" name="uta_pi" rules={[{ required: true }]} initialValue={1.8}>
            <InputNumber min={0.5} max={4.0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider>Factores de Riesgo Maternos</Divider>

      <Row gutter={[8, 8]}>
        <Col span={12}>
          <Form.Item name="historia_previa" valuePropName="checked" initialValue={false}>
            <Checkbox>Preeclampsia previa</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="hipertension" valuePropName="checked" initialValue={false}>
            <Checkbox>Hipertensión crónica</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="diabetes" valuePropName="checked" initialValue={false}>
            <Checkbox>Diabetes</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="obesidad" valuePropName="checked" initialValue={false}>
            <Checkbox>Obesidad (IMC ≥30)</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="gestacion_multiple" valuePropName="checked" initialValue={false}>
            <Checkbox>Gestación múltiple</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="raza_afro" valuePropName="checked" initialValue={false}>
            <Checkbox>Raza afrocaribeña</Checkbox>
          </Form.Item>
        </Col>
      </Row>

      <Form.Item style={{ marginTop: 24 }}>
        <Button type="primary" htmlType="submit" block size="large" icon={EXPERIMENT_ICON_2}>
          Calcular Riesgo FMF
        </Button>
      </Form.Item>
    </Form>
  </Card>
);

export default RiesgoPEForm;
