import React, { lazy, Suspense } from 'react';
import { Card, Spin } from 'antd';
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
    <div className="alertas-page__graficas">
        <Card title="Alertas por Severidad">
          <Suspense fallback={<div className="alertas-page__cargando"><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getSeveridadData(alertas)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPieLabel}
                outerRadius={80}
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
        <Card title="Alertas por Módulo">
          <Suspense fallback={<div className="alertas-page__cargando"><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getModuloData(alertas)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="modulo" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="cantidad" fill="var(--grafico-1)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          </Suspense>
        </Card>
    </div>

    {getTiempoResolucionData(alertas).length > 0 && (
      <div className="alertas-page__graficas alertas-page__graficas--ancha">
          <Card title="Tiempo de Resolución (horas)">
            <Suspense fallback={<div className="alertas-page__cargando"><Spin /></div>}>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={getTiempoResolucionData(alertas)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tipo" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="horas" stroke="var(--grafico-1)" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          </Suspense>
          </Card>
      </div>
    )}
  </>
);

export default AlertasMedicasGraficas;
