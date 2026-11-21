import React, { Suspense } from 'react';
import { Card, Form, Select, Space, Button, Spin } from 'antd';
import type { FormInstance } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import { BISHOP_DOMAIN, BishopScore, ResultadoBishop } from './scoreBishopUtils';
// Recharts se importa directo: envuelto en lazy() pieza por pieza, el gráfico no
// reconocía a sus hijos (Pie, Bar, Line…) y se dibujaba vacío.
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

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
    <Card title="Evaluación de Parámetros Cervicales">
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
      <Card title="Distribución de Parámetros" className="calc-bloque-arriba">
        <Suspense fallback={<div className="calc-cargando"><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={radarData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="parametro" />
              <YAxis domain={BISHOP_DOMAIN} />
              <Tooltip />
              <Legend />
              <Bar name="Valor Actual" dataKey="valor" fill="var(--grafico-1)" />
              <Bar name="Máximo" dataKey="maxValor" fill="var(--color-borde-fuerte)" />
            </BarChart>
          </ResponsiveContainer>
        </Suspense>
      </Card>
    )}
  </>
);

export default BishopForm;
