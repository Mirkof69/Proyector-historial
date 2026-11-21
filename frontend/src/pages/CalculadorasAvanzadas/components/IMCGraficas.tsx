import React from 'react';
import { Card, Row, Col, Divider, Typography } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import {
  DatosPaciente, ResultadoIMC, RegistroIMC,
  renderIMCLabel, formatPesoTooltip,
  getCurvasGanancia, getComponentesPeso, getComparacionTrimestre, getEvolucionIMC,
} from '../imcGananciaUtils';

const { Text } = Typography;

interface IMCGraficasProps {
  values: DatosPaciente;
  resultado: ResultadoIMC;
  historial: RegistroIMC[];
}

const IMCGraficas: React.FC<IMCGraficasProps> = ({ values, resultado, historial }) => (
  <>
    <Divider>Análisis Gráfico</Divider>
    <Row gutter={[16, 16]}>
      {/* Curvas de ganancia ponderal */}
      <Col xs={24} lg={12}>
        <Card title="Curvas de Ganancia Ponderal (Percentiles)">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getCurvasGanancia(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Ganancia de Peso (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="P10" stroke="var(--color-aviso)" strokeWidth={2} strokeDasharray="5 5" name="Percentil 10" />
              <Line type="monotone" dataKey="P50" stroke="var(--grafico-2)" strokeWidth={3} name="Percentil 50 (Ideal)" />
              <Line type="monotone" dataKey="P90" stroke="var(--color-peligro)" strokeWidth={2} strokeDasharray="5 5" name="Percentil 90" />
              <Line type="monotone" dataKey="Actual" stroke="var(--grafico-1)" strokeWidth={4} name="Ganancia Actual" dot={{ r: 6, fill: 'var(--grafico-1)' }} />
            </LineChart>
          </ResponsiveContainer>
          <Text type="secondary" className="calc-pie-grafica">
            Basado en curvas de Atalah y recomendaciones IOM
          </Text>
        </Card>
      </Col>

      {/* Comparación por trimestre */}
      <Col xs={24} lg={12}>
        <Card title="Ganancia por Trimestre vs Recomendado">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getComparacionTrimestre(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="trimestre" />
              <YAxis label={{ value: 'Ganancia (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Actual" fill="var(--grafico-1)" name="Ganancia Actual" />
              <Bar dataKey="Recomendada" fill="var(--grafico-2)" name="Recomendada" />
              <Bar dataKey="Min" fill="var(--color-aviso)" fillOpacity={0.35} name="Mínimo" />
              <Bar dataKey="Max" fill="var(--color-peligro)" fillOpacity={0.35} name="Máximo" />
            </BarChart>
          </ResponsiveContainer>
          <Text type="secondary" className="calc-pie-grafica">
            Distribución de ganancia ponderal por etapa gestacional
          </Text>
        </Card>
      </Col>

      {/* Distribución de componentes del peso */}
      <Col xs={24} lg={12}>
        <Card title="Componentes de la Ganancia de Peso">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getComponentesPeso(resultado)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderIMCLabel}
                outerRadius={80}
                dataKey="value"
              >
                {getComponentesPeso(resultado).map((entry, index) => (
                  <Cell key={`cell-${entry.name || index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={formatPesoTooltip} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <Text type="secondary" className="calc-pie-grafica">
            Distribución fisiológica promedio de la ganancia ponderal
          </Text>
        </Card>
      </Col>

      {/* Evolución temporal del IMC */}
      <Col xs={24} lg={12}>
        <Card title="Evolución del Peso Gestacional">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getEvolucionIMC(historial)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fecha" />
              <YAxis yAxisId="left" label={{ value: 'Peso (kg)', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'IMC', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="peso" stroke="var(--grafico-1)" strokeWidth={3} name="Peso (kg)" />
              <Line yAxisId="right" type="monotone" dataKey="imc" stroke="var(--grafico-2)" strokeWidth={2} strokeDasharray="5 5" name="IMC" />
            </LineChart>
          </ResponsiveContainer>
          <Text type="secondary" className="calc-pie-grafica">
            Seguimiento longitudinal del peso y IMC
          </Text>
        </Card>
      </Col>

      {/* Tendencia acumulada de ganancia (AreaChart) */}
      <Col xs={24}>
        <Card title={
          <>
            Tendencia Acumulada de Ganancia Ponderal
          </>
        }>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={getCurvasGanancia(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Ganancia Acumulada (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="P90" stroke="var(--color-peligro)" fill="var(--color-peligro)" fillOpacity={0.2} name="Zona Alta (>P90)" />
              <Area type="monotone" dataKey="P50" stroke="var(--color-exito)" fill="var(--color-exito)" fillOpacity={0.2} name="Zona Ideal (P50)" />
              <Area type="monotone" dataKey="P10" stroke="var(--color-aviso)" fill="var(--color-aviso)" fillOpacity={0.2} name="Zona Baja (<P10)" />
            </AreaChart>
          </ResponsiveContainer>
          <Text type="secondary" className="calc-pie-grafica">
            Visualización de zonas de ganancia ponderal según percentiles
          </Text>
        </Card>
      </Col>
    </Row>
  </>
);

export default IMCGraficas;
