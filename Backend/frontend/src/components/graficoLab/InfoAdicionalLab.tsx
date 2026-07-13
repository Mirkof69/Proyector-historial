import React, { lazy, Suspense, useCallback } from 'react';
import { Space, Typography, Tag, Spin } from 'antd';
import { PuntoGrafico } from './graficoLabUtils';

const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);

const { Text } = Typography;

interface InfoAdicionalLabProps {
  data: PuntoGrafico[];
  unidad: string;
  valorMinimo?: number;
  valorMaximo?: number;
}

const InfoAdicionalLab: React.FC<InfoAdicionalLabProps> = ({ data, unidad, valorMinimo, valorMaximo }) => {
  const formatTooltipValue = useCallback((value: any) => {
    const num = Number(value);
    return [`${!isNaN(num) ? num.toFixed(2) : '-'} ${unidad}`, 'Valor'];
  }, [unidad]);

  return (
    <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#fafafa', borderRadius: '4px' }}>
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <Text strong>Interpretación:</Text>
        <Text style={{ fontSize: 13 }}>
          • Total de mediciones: <strong>{data.length}</strong>
        </Text>
        <Text style={{ fontSize: 13 }}>
          • Rango de valores: <strong>
            {Math.min(...data.map(d => d.valor || 0)).toFixed(2)} -
            {Math.max(...data.map(d => d.valor || 0)).toFixed(2)} {unidad}
          </strong>
        </Text>
        {valorMinimo && valorMaximo && (
          <Text style={{ fontSize: 13 }}>
            • Valores dentro del rango normal:{' '}
            <strong>
              {data.filter(d => {
                const v = d.valor || 0;
                return v >= valorMinimo && v <= valorMaximo;
              }).length}{' '}
              de {data.length}
            </strong>
            {' '}
            <Tag color="green">
              {((data.filter(d => {
                const v = d.valor || 0;
                return v >= valorMinimo && v <= valorMaximo;
              }).length / data.length) * 100).toFixed(0)}%
            </Tag>
          </Text>
        )}

        {/* MINI GRÁFICO DE TENDENCIA SIMPLIFICADO */}
        <div style={{ marginTop: 12 }}>
          <Text strong style={{ fontSize: 12 }}>Vista Simplificada:</Text>
          <Suspense fallback={<Spin size="small" />}>
            <ResponsiveContainer width="100%" height={80}>
              <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                <Line
                  type="monotone"
                  dataKey="valor"
                  stroke="#1890ff"
                  strokeWidth={2}
                  dot={false}
                  name="Tendencia"
                />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  formatter={formatTooltipValue}
                />
              </LineChart>
            </ResponsiveContainer>
          </Suspense>
        </div>
      </Space>
    </div>
  );
};

export default InfoAdicionalLab;
