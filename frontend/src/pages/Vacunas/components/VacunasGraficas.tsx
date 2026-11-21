import React from 'react';
import { Card, Space } from 'antd';
import { BarChartOutlined, SafetyOutlined } from '@ant-design/icons';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  ResponsiveContainer, PieChart, Pie, Cell,
  Tooltip as RechartsTooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { COLORS, AXIS_TICK_STYLE, BAR_RADIUS } from '../vacunasUtils';

interface VacunasGraficasProps {
  graficoPorMes: { mes: string; cantidad: number }[];
  graficoPorTipo: { name: string; value: number }[];
}

const VacunasGraficas: React.FC<VacunasGraficasProps> = ({ graficoPorMes, graficoPorTipo }) => (
  <div className="vacunas-page__graficas">
      <Card title={<Space><BarChartOutlined /> Histórico de Aplicaciones</Space>} size="small">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={graficoPorMes}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="mes" axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
            <YAxis axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
            <RechartsTooltip cursor={{ fill: 'var(--color-hover)' }} />
            <Bar dataKey="cantidad" fill="var(--grafico-1)" radius={BAR_RADIUS} barSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
      <Card title={<Space><SafetyOutlined /> Distribución por Inmunógeno</Space>} size="small">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={graficoPorTipo}
              innerRadius={60}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {graficoPorTipo.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={COLORS[graficoPorTipo.indexOf(entry) % COLORS.length]} />
              ))}
            </Pie>
            <RechartsTooltip />
            <Legend verticalAlign="bottom" height={36} />
          </PieChart>
        </ResponsiveContainer>
      </Card>
  </div>
);

export default VacunasGraficas;
