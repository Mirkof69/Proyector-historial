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
        <Card title="Curvas de Ganancia Ponderal (Percentiles)" variant="borderless">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getCurvasGanancia(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Ganancia de Peso (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="P10" stroke="#faad14" strokeWidth={2} strokeDasharray="5 5" name="Percentil 10" />
              <Line type="monotone" dataKey="P50" stroke="#1890ff" strokeWidth={3} name="Percentil 50 (Ideal)" />
              <Line type="monotone" dataKey="P90" stroke="#f5222d" strokeWidth={2} strokeDasharray="5 5" name="Percentil 90" />
              <Line type="monotone" dataKey="Actual" stroke="#52c41a" strokeWidth={4} name="Ganancia Actual" dot={{ r: 6, fill: '#52c41a' }} />
            </LineChart>
          </ResponsiveContainer>
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
            Basado en curvas de Atalah y recomendaciones IOM
          </Text>
        </Card>
      </Col>

      {/* Comparación por trimestre */}
      <Col xs={24} lg={12}>
        <Card title="Ganancia por Trimestre vs Recomendado" variant="borderless">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={getComparacionTrimestre(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="trimestre" />
              <YAxis label={{ value: 'Ganancia (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="Actual" fill="#52c41a" name="Ganancia Actual" />
              <Bar dataKey="Recomendada" fill="#1890ff" name="Recomendada" />
              <Bar dataKey="Min" fill="#faad14" opacity={0.3} name="Mínimo" />
              <Bar dataKey="Max" fill="#f5222d" opacity={0.3} name="Máximo" />
            </BarChart>
          </ResponsiveContainer>
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
            Distribución de ganancia ponderal por etapa gestacional
          </Text>
        </Card>
      </Col>

      {/* Distribución de componentes del peso */}
      <Col xs={24} lg={12}>
        <Card title="Componentes de la Ganancia de Peso" variant="borderless">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={getComponentesPeso(resultado)}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderIMCLabel}
                outerRadius={80}
                fill="#8884d8"
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
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
            Distribución fisiológica promedio de la ganancia ponderal
          </Text>
        </Card>
      </Col>

      {/* Evolución temporal del IMC */}
      <Col xs={24} lg={12}>
        <Card title="Evolución del Peso Gestacional" variant="borderless">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={getEvolucionIMC(historial)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="fecha" />
              <YAxis yAxisId="left" label={{ value: 'Peso (kg)', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'IMC', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="peso" stroke="#1890ff" strokeWidth={3} name="Peso (kg)" />
              <Line yAxisId="right" type="monotone" dataKey="imc" stroke="#722ed1" strokeWidth={2} strokeDasharray="5 5" name="IMC" />
            </LineChart>
          </ResponsiveContainer>
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
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
        } variant="borderless">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={getCurvasGanancia(values, resultado)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
              <YAxis label={{ value: 'Ganancia Acumulada (kg)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="P90" stroke="#f5222d" fill="#f5222d" fillOpacity={0.2} name="Zona Alta (>P90)" />
              <Area type="monotone" dataKey="P50" stroke="#1890ff" fill="#1890ff" fillOpacity={0.3} name="Zona Ideal (P50)" />
              <Area type="monotone" dataKey="P10" stroke="#faad14" fill="#faad14" fillOpacity={0.2} name="Zona Baja (<P10)" />
            </AreaChart>
          </ResponsiveContainer>
          <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginTop: 8 }}>
            Visualización de zonas de ganancia ponderal según percentiles
          </Text>
        </Card>
      </Col>
    </Row>
  </>
);

export default IMCGraficas;
