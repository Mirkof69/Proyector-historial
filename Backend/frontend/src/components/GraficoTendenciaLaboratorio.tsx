/**
 * =============================================================================
 * GRÁFICO DE TENDENCIA DE LABORATORIO
 * =============================================================================
 * Componente para visualizar evolución temporal de parámetros de laboratorio
 * - Gráfico de línea con valores históricos
 * - Líneas de referencia para rangos normales
 * - Área sombreada para rango de normalidad
 * - Estadísticas: promedio, tendencia, variación
 * =============================================================================
 */

import React, { lazy, Suspense } from 'react';
import { Card, Space, Typography, Alert, Spin } from 'antd';
import { TrophyOutlined } from '@ant-design/icons';
import {
  HistoricoData,
  transformarHistorico,
  calcularPromedio,
  calcularTendencia,
  calcularUltimaVariacion,
  getEstadoActual,
} from './graficoLab/graficoLabUtils';
import CustomTooltipLab from './graficoLab/CustomTooltipLab';
import EstadisticasLab from './graficoLab/EstadisticasLab';
import InfoAdicionalLab from './graficoLab/InfoAdicionalLab';

const ComposedChart = lazy(() => import('recharts').then(m => ({ default: m.ComposedChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ReferenceLine = lazy(() => import('recharts').then(m => ({ default: m.ReferenceLine })) as any);
const Area = lazy(() => import('recharts').then(m => ({ default: m.Area })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const ReferenceArea = lazy(() => import('recharts').then(m => ({ default: m.ReferenceArea })) as any);

const { Title } = Typography;

interface Props {
  parametro: string;
  historico: HistoricoData[];
  valorMinimo?: number;
  valorMaximo?: number;
  criticoBajo?: number;
  criticoAlto?: number;
  unidad?: string;
}

const GraficoTendenciaLaboratorio: React.FC<Props> = ({
  parametro,
  historico,
  valorMinimo,
  valorMaximo,
  criticoBajo,
  criticoAlto,
  unidad = '',
}) => {
  const data = transformarHistorico(historico, valorMinimo, valorMaximo);
  const promedio = calcularPromedio(data);
  const tendencia = calcularTendencia(data);
  const ultimaVariacion = calcularUltimaVariacion(data);
  const estadoActual = getEstadoActual(data, { valorMinimo, valorMaximo, criticoBajo, criticoAlto });

  if (data.length === 0) {
    return (
      <Card>
        <Alert
          message="Sin Datos Históricos"
          description={`No hay datos históricos suficientes para mostrar la evolución de ${parametro}.`}
          type="info"
          showIcon
        />
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <TrophyOutlined />
          <Title level={4} style={{ margin: 0 }}>Evolución de {parametro}</Title>
        </Space>
      }
    >
      {/* ESTADO ACTUAL */}
      {estadoActual !== 'normal' && estadoActual !== 'sin-datos' && (
        <Alert
          message={
            estadoActual.includes('critico')
              ? 'Valor actual en rango crítico'
              : 'Valor Actual Fuera del Rango Normal'
          }
          description={
            estadoActual === 'critico-bajo'
              ? `El último valor está por debajo del límite crítico (< ${criticoBajo} ${unidad})`
              : estadoActual === 'critico-alto'
                ? `El último valor está por encima del límite crítico (> ${criticoAlto} ${unidad})`
                : estadoActual === 'bajo'
                  ? `El último valor está por debajo del mínimo normal (< ${valorMinimo} ${unidad})`
                  : `El último valor está por encima del máximo normal (> ${valorMaximo} ${unidad})`
          }
          type={estadoActual.includes('critico') ? 'error' : 'warning'}
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* GRÁFICO */}
      <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="fecha"
              style={{ fontSize: 12 }}
            />
            <YAxis
              style={{ fontSize: 12 }}
              label={{ value: unidad, angle: -90, position: 'insideLeft' }}
            />
            <Tooltip content={<CustomTooltipLab unidad={unidad} valorMinimo={valorMinimo} valorMaximo={valorMaximo} />} />
            <Legend />

            {valorMinimo !== undefined && valorMaximo !== undefined && (
              <ReferenceArea
                y1={valorMinimo}
                y2={valorMaximo}
                fill="var(--color-exito)"
                fillOpacity={0.1}
                label={{ value: 'Rango Normal', position: 'insideTopRight', fontSize: 12 }}
              />
            )}

            {valorMinimo !== undefined && (
              <ReferenceLine
                y={valorMinimo}
                stroke="var(--color-exito)"
                strokeDasharray="5 5"
                label={{
                  value: `Mín: ${valorMinimo}`,
                  position: 'right',
                  fontSize: 12,
                  fill: 'var(--color-exito)'
                }}
              />
            )}

            {valorMaximo !== undefined && (
              <ReferenceLine
                y={valorMaximo}
                stroke="var(--color-exito)"
                strokeDasharray="5 5"
                label={{
                  value: `Máx: ${valorMaximo}`,
                  position: 'right',
                  fontSize: 12,
                  fill: 'var(--color-exito)'
                }}
              />
            )}

            {criticoBajo !== undefined && (
              <ReferenceLine
                y={criticoBajo}
                stroke="var(--color-peligro)"
                strokeDasharray="3 3"
                label={{
                  value: `Crítico Bajo: ${criticoBajo}`,
                  position: 'right',
                  fontSize: 12,
                  fill: 'var(--color-peligro)'
                }}
              />
            )}

            {criticoAlto !== undefined && (
              <ReferenceLine
                y={criticoAlto}
                stroke="var(--color-peligro)"
                strokeDasharray="3 3"
                label={{
                  value: `Crítico Alto: ${criticoAlto}`,
                  position: 'right',
                  fontSize: 12,
                  fill: 'var(--color-peligro)'
                }}
              />
            )}

            <ReferenceLine
              y={promedio}
              stroke="var(--color-primario)"
              strokeDasharray="10 5"
              label={{
                value: `Promedio: ${promedio.toFixed(2)}`,
                position: 'left',
                fontSize: 12,
                fill: 'var(--color-primario)'
              }}
            />

            <Area
              type="monotone"
              dataKey="valor"
              fill="var(--grafico-2)"
              fillOpacity={0.2}
              stroke="none"
              name={`Área de ${parametro}`}
            />

            <Line
              type="monotone"
              dataKey="valor"
              stroke="var(--grafico-2)"
              strokeWidth={3}
              dot={{ r: 6, fill: 'var(--grafico-2)' }}
              activeDot={{ r: 8 }}
              name={`${parametro} (${unidad})`}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </Suspense>

      {/* ESTADÍSTICAS */}
      <EstadisticasLab
        promedio={promedio}
        tendencia={tendencia}
        ultimaVariacion={ultimaVariacion}
        unidad={unidad}
      />

      {/* INFORMACIÓN ADICIONAL */}
      <InfoAdicionalLab
        data={data}
        unidad={unidad}
        valorMinimo={valorMinimo}
        valorMaximo={valorMaximo}
      />
    </Card>
  );
};

export default GraficoTendenciaLaboratorio;
