import React from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Divider, Checkbox, Tag } from 'antd';
import { ExperimentOutlined, LineChartOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { DatosScreening } from '../riesgoCromosomicoUtils';

interface RiesgoCromosomicoFormProps {
  form: FormInstance;
  onFinish: (values: DatosScreening) => void;
  usandoDatosEjemplo: boolean;
}

const RiesgoCromosomicoForm: React.FC<RiesgoCromosomicoFormProps> = ({ form, onFinish, usandoDatosEjemplo }) => (
  <Card title={
    <>
      <LineChartOutlined /> Datos Maternos y Biomarcadores
      {usandoDatosEjemplo && <Tag color="blue" style={{ marginLeft: 8 }}>Datos de Ejemplo</Tag>}
    </>
  }>
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item label="Edad Materna (años)" name="edad" rules={[{ required: true }]} initialValue={32}>
            <InputNumber min={15} max={50} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item label="Semanas Gestación" name="semanas" rules={[{ required: true }]} initialValue={12.5} tooltip="11+0 a 13+6 semanas">
            <InputNumber min={11} max={14} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider>Biomarcadores Ecográficos</Divider>

      <Form.Item
        label="NT - Translucencia Nucal (mm)"
        name="nt"
        rules={[{ required: true }]}
        initialValue={2.2}
        tooltip="Medida del espacio translúcido en región nucal fetal, 11-13+6 semanas"
      >
        <InputNumber min={0.5} max={8.0} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Divider>Biomarcadores Séricos</Divider>

      <Form.Item
        label="PAPP-A (mUI/mL)"
        name="pappa"
        rules={[{ required: true }]}
        initialValue={1.2}
        tooltip="Proteína plasmática A asociada al embarazo"
      >
        <InputNumber min={0.1} max={10} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="βhCG libre (ng/mL)"
        name="bhcg_libre"
        rules={[{ required: true }]}
        initialValue={42}
        tooltip="Subunidad beta libre de gonadotropina coriónica humana"
      >
        <InputNumber min={1} max={200} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Divider>Factores de Riesgo Adicionales</Divider>

      <Row gutter={[8, 8]}>
        <Col span={12}>
          <Form.Item name="historia_t21" valuePropName="checked" initialValue={false}>
            <Checkbox>Historia previa de T21</Checkbox>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="hallazgos_eco" valuePropName="checked" initialValue={false}>
            <Checkbox>Hallazgos ecográficos sospechosos</Checkbox>
          </Form.Item>
        </Col>
      </Row>

      <Form.Item style={{ marginTop: 24 }}>
        <Button type="primary" htmlType="submit" block size="large" icon={<ExperimentOutlined />}>
          Calcular Riesgo Combinado
        </Button>
      </Form.Item>
    </Form>
  </Card>
);

export default RiesgoCromosomicoForm;
