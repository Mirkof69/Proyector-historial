import React, { lazy, Suspense } from 'react';
import { Card, Form, Select, Space, Button, Spin } from 'antd';
import type { FormInstance } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import { BISHOP_DOMAIN, BishopScore, ResultadoBishop } from './scoreBishopUtils';

const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);

interface BishopFormProps {
  form: FormInstance;
  loading: boolean;
  resultado: ResultadoBishop | null;
  radarData: any[];
  onFinish: (values: BishopScore) => void;
  onReset: () => void;
}

const BishopForm: React.FC<BishopFormProps> = ({ form, loading, resultado, radarData, onFinish, onReset }) => (
  <>
    <Card title="Evaluación de Parámetros Cervicales" bordered={false}>
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{ dilatacion: 0, borramiento: 0, estacion: 0, consistencia: 0, posicion: 0 }}
      >
        <Form.Item label="Dilatación Cervical" name="dilatacion" rules={[{ required: true, message: 'Seleccione dilatación' }]}>
          <Select size="large">
            <Select.Option value={0}>Cerrado (0 puntos)</Select.Option>
            <Select.Option value={1}>1-2 cm (1 punto)</Select.Option>
            <Select.Option value={2}>3-4 cm (2 puntos)</Select.Option>
            <Select.Option value={3}>≥5 cm (3 puntos)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Borramiento Cervical" name="borramiento" rules={[{ required: true, message: 'Seleccione borramiento' }]}>
          <Select size="large">
            <Select.Option value={0}>0-30% (0 puntos)</Select.Option>
            <Select.Option value={1}>40-50% (1 punto)</Select.Option>
            <Select.Option value={2}>60-70% (2 puntos)</Select.Option>
            <Select.Option value={3}>≥80% (3 puntos)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Estación de Presentación" name="estacion" rules={[{ required: true, message: 'Seleccione estación' }]}>
          <Select size="large">
            <Select.Option value={0}>-3 (0 puntos)</Select.Option>
            <Select.Option value={1}>-2 (1 punto)</Select.Option>
            <Select.Option value={2}>-1 / 0 (2 puntos)</Select.Option>
            <Select.Option value={3}>+1 / +2 (3 puntos)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Consistencia Cervical" name="consistencia" rules={[{ required: true, message: 'Seleccione consistencia' }]}>
          <Select size="large">
            <Select.Option value={0}>Firme (0 puntos)</Select.Option>
            <Select.Option value={1}>Media (1 punto)</Select.Option>
            <Select.Option value={2}>Blanda (2 puntos)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="Posición Cervical" name="posicion" rules={[{ required: true, message: 'Seleccione posición' }]}>
          <Select size="large">
            <Select.Option value={0}>Posterior (0 puntos)</Select.Option>
            <Select.Option value={1}>Media (1 punto)</Select.Option>
            <Select.Option value={2}>Anterior (2 puntos)</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} size="large" loading={loading}>
              Calcular Score
            </Button>
            <Button onClick={onReset} size="large">
              Limpiar
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>

    {resultado && (
      <Card title="Distribución de Parámetros" style={{ marginTop: 16 }}>
        <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={radarData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="parametro" />
              <YAxis domain={BISHOP_DOMAIN} />
              <Tooltip />
              <Legend />
              <Bar name="Valor Actual" dataKey="valor" fill="#1890ff" />
              <Bar name="Máximo" dataKey="maxValor" fill="#52c41a" opacity={0.3} />
            </BarChart>
          </ResponsiveContainer>
        </Suspense>
      </Card>
    )}
  </>
);

export default BishopForm;
