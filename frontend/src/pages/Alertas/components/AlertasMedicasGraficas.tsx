import React, { Suspense } from 'react';
import { Card, Spin } from 'antd';
import { AlertaMedica } from '../../../services/reportesService';
import {
  renderPieLabel, getSeveridadData, getModuloData, getTiempoResolucionData,
} from '../alertasMedicasUtils';
// Recharts se importa directo: envuelto en lazy() pieza por pieza, el gráfico no
// reconocía a sus hijos (Pie, Bar, Line…) y se dibujaba vacío.
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line } from 'recharts';

export interface ResumenAlertas {
  total_alertas: number;
  alertas_activas: number;
  alertas_criticas_activas: number;
  pendientes: number;
  hoy: number;
  por_prioridad: { prioridad: string; count: number }[];
  por_modulo: { modulo: string; cantidad: number }[];
}

interface AlertasMedicasGraficasProps {
  alertas: AlertaMedica[];
  resumen?: ResumenAlertas | null;
}

const COLOR_PRIORIDAD: Record<string, [string, string]> = {
  baja: ['Baja', 'var(--color-info)'], media: ['Media', 'var(--color-aviso)'], alta: ['Alta', 'var(--grafico-5)'],
  critica: ['Crítica', 'var(--color-peligro)'],
};

/** Severidad de todas las alertas (resumen del servidor) o, sin él, de las cargadas. */
const severidad = (alertas: AlertaMedica[], resumen?: ResumenAlertas | null) => {
  if (!resumen) return getSeveridadData(alertas);
  const cuenta: Record<string, number> = { baja: 0, media: 0, alta: 0, critica: 0 };
  resumen.por_prioridad.forEach(({ prioridad, count }) => {
    const clave = prioridad === 'emergencia' ? 'critica' : prioridad;
    cuenta[clave] = (cuenta[clave] || 0) + count;
  });
  return Object.entries(COLOR_PRIORIDAD).map(([k, [name, color]]) => ({ name, value: cuenta[k] || 0, color }));
};

const AlertasMedicasGraficas: React.FC<AlertasMedicasGraficasProps> = ({ alertas, resumen }) => (
  <>
    <div className="alertas-page__graficas">
        <Card title="Alertas por Severidad">
          <Suspense fallback={<div className="alertas-page__cargando"><Spin /></div>}>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severidad(alertas, resumen)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPieLabel}
                outerRadius={80}
                dataKey="value"
              >
                {severidad(alertas, resumen).map((entry) => (
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
            <BarChart data={resumen?.por_modulo ?? getModuloData(alertas)}>
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
