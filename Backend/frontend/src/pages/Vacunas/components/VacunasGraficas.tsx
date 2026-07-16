import React from 'react';
import { Card, Row, Col, Space } from 'antd';
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
  <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
    <Col xs={24} lg={14}>
      <Card title={<Space><BarChartOutlined /> Histórico de Aplicaciones</Space>} size="small" className="chart-card">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={graficoPorMes}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
            <XAxis dataKey="mes" axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
            <YAxis axisLine={false} tickLine={false} tick={AXIS_TICK_STYLE} />
            <RechartsTooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
            <Bar dataKey="cantidad" fill="#3b82f6" radius={BAR_RADIUS} barSize={40} />
          </BarChart>
        </ResponsiveContainer>
      </Card>
    </Col>
    <Col xs={24} lg={10}>
      <Card title={<Space><SafetyOutlined /> Distribución por Inmunógeno</Space>} size="small" className="chart-card">
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie
              data={graficoPorTipo}
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
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
    </Col>
  </Row>
);

export default VacunasGraficas;
