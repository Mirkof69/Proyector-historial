/* eslint-disable react-doctor/prefer-dynamic-import */
import React from 'react';
import { Card, Row, Col, Divider, Space, Typography, Empty } from 'antd';
import {
  BarChartOutlined, LineChartOutlined, DashboardOutlined, ScanOutlined,
} from '@ant-design/icons';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend,
  ResponsiveContainer, AreaChart, Area, ComposedChart
} from 'recharts';
import {
  COLORS, renderVacunaLabel,
  getTriajesTimeline, getEstadisticasVacunas, getNotasPorTipo,
} from '../detallePacienteUtils';

const { Text } = Typography;

interface DetallePacienteGraficasProps {
  triajes: any[];
  vacunas: any[];
  notasEvolucion: any[];
}

const DetallePacienteGraficas: React.FC<DetallePacienteGraficasProps> = ({ triajes, vacunas, notasEvolucion }) => (
  <>
    {/* Separador de Sección */}
    <Divider orientation="left">
      <Space>
        <ScanOutlined />
        <Text strong>Análisis Gráfico del Expediente</Text>
      </Space>
    </Divider>

    {/* Gráficas de Análisis */}
    <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
      <Col xs={24} lg={12}>
        <Card title={<span><LineChartOutlined /> Evolución de Signos Vitales (Últimos Triajes)</span>} variant="borderless">
          {triajes.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={getTriajesTimeline(triajes)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" fontSize={12} />
                <YAxis fontSize={12} />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" name="PA Sistólica" strokeWidth={2} />
                <Line type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" name="PA Diastólica" strokeWidth={2} />
                <Line type="monotone" dataKey="FC" stroke="#52c41a" name="Frecuencia Cardíaca" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Sin triajes registrados" />
          )}
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title={<span><BarChartOutlined /> Distribución de Vacunas</span>} variant="borderless">
          {vacunas.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getEstadisticasVacunas(vacunas)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderVacunaLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getEstadisticasVacunas(vacunas).map((entry, index) => (
                    <Cell key={`cell-${entry.name}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Sin vacunas registradas" />
          )}
        </Card>
      </Col>
    </Row>

    {/* Nuevas Gráficas Avanzadas */}
    <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
      <Col xs={24} lg={12}>
        <Card title={<span><BarChartOutlined /> Distribución de Notas por Tipo</span>} variant="borderless">
          {notasEvolucion.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getNotasPorTipo(notasEvolucion, 'tipo')}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tipo" fontSize={12} />
                <YAxis fontSize={12} />
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="cantidad" fill="#8884d8" name="Cantidad de Notas" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Sin notas de evolución registradas" />
          )}
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title={<span><DashboardOutlined /> Tendencia de Signos Vitales (Área)</span>} variant="borderless">
          {triajes.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={getTriajesTimeline(triajes)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" fontSize={12} />
                <YAxis fontSize={12} />
                <RechartsTooltip />
                <Legend />
                <Area type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" fill="#ff4d4f" fillOpacity={0.3} name="PA Sistólica" />
                <Area type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" fill="#1890ff" fillOpacity={0.3} name="PA Diastólica" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Sin triajes registrados" />
          )}
        </Card>
      </Col>
    </Row>

    {/* Gráfico Compuesto */}
    <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
      <Col span={24}>
        <Card title={<span><LineChartOutlined /> Análisis Combinado de Signos Vitales y Tendencias</span>} variant="borderless">
          {triajes.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={getTriajesTimeline(triajes)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" fontSize={12} />
                <YAxis fontSize={12} />
                <RechartsTooltip />
                <Legend />
                <Area type="monotone" dataKey="Temperatura" fill="#faad14" stroke="#faad14" fillOpacity={0.2} name="Temperatura (°C)" />
                <Bar dataKey="FC" fill="#52c41a" name="Frecuencia Cardíaca" />
                <Line type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" strokeWidth={2} name="PA Sistólica" />
                <Line type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" strokeWidth={2} name="PA Diastólica" />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Sin datos para análisis combinado" />
          )}
        </Card>
      </Col>
    </Row>
  </>
);

export default DetallePacienteGraficas;
