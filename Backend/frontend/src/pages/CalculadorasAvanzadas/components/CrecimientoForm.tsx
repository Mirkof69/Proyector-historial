import React from 'react';
import { Card, Form, InputNumber, Button, Divider, Select, Tag } from 'antd';
import { ExperimentOutlined, BarChartOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { DatosBiometria } from '../crecimientoFetalUtils';

const { Option } = Select;

interface CrecimientoFormProps {
  form: FormInstance;
  onFinish: (values: DatosBiometria) => void;
  usandoDatosEjemplo: boolean;
}

const CrecimientoForm: React.FC<CrecimientoFormProps> = ({ form, onFinish, usandoDatosEjemplo }) => (
  <Card title={
    <>
      <BarChartOutlined /> Datos de Biometría Fetal
      {usandoDatosEjemplo && <Tag color="blue" style={{ marginLeft: 8 }}>Datos de Ejemplo</Tag>}
    </>
  }>
    <Form form={form} layout="vertical" onFinish={onFinish}>
      <Form.Item label="Edad Gestacional (semanas)" name="semanas" rules={[{ required: true }]} initialValue={28}>
        <InputNumber min={20} max={42} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Divider>Parámetros Biométricos</Divider>

      <Form.Item
        label="BPD - Diámetro Biparietal (mm)"
        name="bpd"
        rules={[{ required: true }]}
        initialValue={73}
        tooltip="Diámetro mayor de la cabeza fetal, medido de hueso externo a hueso interno"
      >
        <InputNumber min={20} max={120} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="HC - Circunferencia Cefálica (mm)"
        name="hc"
        rules={[{ required: true }]}
        initialValue={269}
        tooltip="Perímetro de la cabeza fetal a nivel de tálamos y cavum septum pellucidum"
      >
        <InputNumber min={100} max={450} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="AC - Circunferencia Abdominal (mm)"
        name="ac"
        rules={[{ required: true }]}
        initialValue={253}
        tooltip="Perímetro del abdomen a nivel de vena umbilical y estómago"
      >
        <InputNumber min={100} max={500} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="FL - Longitud del Fémur (mm)"
        name="fl"
        rules={[{ required: true }]}
        initialValue={56}
        tooltip="Longitud del fémur de metáfisis a metáfisis, excluyendo epífisis"
      >
        <InputNumber min={10} max={100} step={0.1} style={{ width: '100%' }} />
      </Form.Item>

      <Form.Item
        label="Fórmula de Hadlock"
        name="formula"
        rules={[{ required: true }]}
        initialValue="hadlock4"
        tooltip="Hadlock 4 (HC, AC, FL) es la más precisa y usada"
      >
        <Select>
          <Option value="hadlock1">Hadlock 1 (BPD, HC, AC, FL) - Más completa</Option>
          <Option value="hadlock2">Hadlock 2 (AC, FL) - Más simple</Option>
          <Option value="hadlock3">Hadlock 3 (BPD, AC, FL)</Option>
          <Option value="hadlock4">Hadlock 4 (HC, AC, FL) - Recomendada</Option>
        </Select>
      </Form.Item>

      <Form.Item style={{ marginTop: 24 }}>
        <Button type="primary" htmlType="submit" block size="large" icon={<ExperimentOutlined />}>
          Calcular EFW y Percentiles
        </Button>
      </Form.Item>
    </Form>
  </Card>
);

export default CrecimientoForm;
