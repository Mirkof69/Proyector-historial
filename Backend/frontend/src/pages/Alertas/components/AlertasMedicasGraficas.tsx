import React, { lazy, Suspense } from 'react';
import { Card, Row, Col, Spin } from 'antd';
import { AlertaMedica } from '../../../services/reportesService';
import {
  renderPieLabel, getSeveridadData, getModuloData, getTiempoResolucionData,
} from '../alertasMedicasUtils';

const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })) as any);
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })) as any);
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);

interface AlertasMedicasGraficasProps {
  alertas: AlertaMedica[];
}

const AlertasMedicasGraficas: React.FC<AlertasMedicasGraficasProps> = ({ alertas }) => (
  <>
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} md={12}>
        <Card title="Alertas por Severidad" variant="borderless">
          <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getSeveridadData(alertas)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPieLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {getSeveridadData(alertas).map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          </Suspense>
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card title="Alertas por Módulo" variant="borderless">
          <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getModuloData(alertas)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="modulo" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="cantidad" fill="#1890ff" />
            </BarChart>
          </ResponsiveContainer>
          </Suspense>
        </Card>
      </Col>
    </Row>

    {getTiempoResolucionData(alertas).length > 0 && (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Tiempo de Resolución (horas)" variant="borderless">
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={getTiempoResolucionData(alertas)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tipo" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="horas" stroke="#52c41a" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          </Suspense>
          </Card>
        </Col>
      </Row>
    )}
  </>
);

export default AlertasMedicasGraficas;
