/* eslint-disable react-doctor/prefer-dynamic-import */
import React from 'react';
import { Card, Row, Col, Progress, Space, Typography, Divider, Tag, Alert, Statistic } from 'antd';
import {
  RiseOutlined, UserOutlined, FallOutlined, MinusOutlined,
} from '@ant-design/icons';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, LabelList,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  COLORS, PIE_COLORS, renderPieLabel, renderPartosLabel, RADAR_DOMAIN, DashboardKpis,
} from '../dashboardGraficasUtils';

const { Text } = Typography;

interface DashboardGraficasChartsProps {
  kpis: DashboardKpis;
  pacientesPorMes: any[];
  embarazosPorTrimestre: any[];
  distribucionRiesgos: any[];
  citasPorEstado: any[];
  partosPorTipo: any[];
  ecografiasPorTipo: any[];
  evolucionesPorSemana: any[];
  laboratorioPorEstado: any[];
  radarData: any[];
  pacientesPorEdad: any[];
}

const DashboardGraficasCharts: React.FC<DashboardGraficasChartsProps> = ({
  kpis, pacientesPorMes, embarazosPorTrimestre, distribucionRiesgos, citasPorEstado,
  partosPorTipo, ecografiasPorTipo, evolucionesPorSemana, laboratorioPorEstado, radarData, pacientesPorEdad,
}) => (
  <>
    {/* Fila 1: Pacientes y Embarazos */}
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} lg={12}>
        <Card title="📈 Pacientes Nuevos por Mes (Últimos 6 meses)">
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={pacientesPorMes}>
              <defs>
                <linearGradient id="colorPacientes" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
                  <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="pacientes"
                stroke={COLORS.primary}
                fillOpacity={1}
                fill="url(#colorPacientes)"
                name="Pacientes"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="🤰 Embarazos por Trimestre">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={embarazosPorTrimestre}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="trimestre" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="embarazos" fill={COLORS.success} name="Embarazos">
                <LabelList dataKey="embarazos" position="top" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>

    {/* Fila 2: Riesgos y Citas */}
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} lg={8}>
        <Card title="⚠️ Distribución de Riesgos">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={distribucionRiesgos}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPieLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {distribucionRiesgos.map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card title="📅 Citas por Estado">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={citasPorEstado} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="estado" type="category" width={100} />
              <Tooltip />
              <Bar dataKey="cantidad" fill={COLORS.cyan} name="Cantidad">
                <LabelList dataKey="cantidad" position="right" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={8}>
        <Card title="👶 Partos por Tipo">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={partosPorTipo}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPartosLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="cantidad"
              >
                {partosPorTipo.map((entry) => (
                  <Cell key={`cell-${entry.tipo}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>

    {/* Fila 3: Ecografías y Evoluciones */}
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      <Col xs={24} lg={12}>
        <Card title="🔬 Ecografías por Tipo (Últimos 3 meses)">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={ecografiasPorTipo}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tipo" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="cantidad" fill={COLORS.purple} name="Cantidad">
                <LabelList dataKey="cantidad" position="top" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card title="📝 Evoluciones por Semana (Últimas 8 semanas)">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={evolucionesPorSemana}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semana" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="evoluciones"
                stroke={COLORS.green}
                strokeWidth={3}
                dot={{ r: 5 }}
                name="Evoluciones"
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>

    {/* Fila 4: Laboratorio e Indicadores */}
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={8}>
        <Card title="🧪 Laboratorio por Estado">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={laboratorioPorEstado}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderPieLabel}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {laboratorioPorEstado.map((entry) => (
                  <Cell key={`cell-${entry.name}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>

      <Col xs={24} lg={16}>
        <Card title="📊 Indicadores de Calidad">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <div style={{ marginBottom: 24 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Tasa de Cesáreas: {kpis.partos.tasaCesarea}%</Text>
                  <Progress
                    percent={kpis.partos.tasaCesarea}
                    status={kpis.partos.tasaCesarea > 30 ? 'exception' : 'success'}
                    strokeColor={kpis.partos.tasaCesarea > 30 ? COLORS.danger : COLORS.success}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Meta OMS: {'<'}30%. Total de partos: {kpis.partos.total}
                  </Text>
                </Space>
              </div>
            </Col>
            <Col span={24}>
              <div style={{ marginBottom: 24 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Tasa de Alto Riesgo: {kpis.embarazos.tasaRiesgo}%</Text>
                  <Progress
                    percent={kpis.embarazos.tasaRiesgo}
                    status="exception"
                    strokeColor={kpis.embarazos.tasaRiesgo > 20 ? COLORS.danger : COLORS.warning}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    {kpis.embarazos.altoRiesgo} de {kpis.embarazos.activos} embarazos activos
                  </Text>
                </Space>
              </div>
            </Col>
            <Col span={24}>
              <div>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Text strong>Crecimiento de Pacientes: {kpis.pacientes.crecimiento}%</Text>
                  <Progress
                    percent={Math.min(kpis.pacientes.crecimiento, 100)}
                    strokeColor={COLORS.primary}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    +{kpis.pacientes.nuevosMes} pacientes nuevos este mes
                  </Text>
                </Space>
              </div>
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>

    {/* Fila Nueva: Distribución de Pacientes por Edad - USANDO PIE_COLORS y UserOutlined */}
    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
      <Col xs={24} lg={12}>
        <Card
          title={
            <Space>
              <UserOutlined style={{ fontSize: 20, color: COLORS.primary }} />
              <span>Distribución de Pacientes por Edad</span>
            </Space>
          }
        >
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={pacientesPorEdad}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={renderPieLabel}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {pacientesPorEdad.map((entry, index) => (
                  <Cell key={`cell-${entry.name}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <Divider />
          <Alert
            message="Análisis Demográfico"
            description={`Total de ${kpis.pacientes.total} pacientes registrados. La mayoría se encuentran en el rango de edad reproductiva óptima (20-35 años).`}
            type="info"
            showIcon
            icon={<UserOutlined />}
          />
        </Card>
      </Col>

      <Col xs={24} lg={12}>
        <Card
          title={
            <Space>
              <UserOutlined style={{ fontSize: 20, color: COLORS.success }} />
              <span>Estadísticas de Pacientes</span>
            </Space>
          }
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Statistic
                title="Pacientes Activos"
                value={kpis.pacientes.total}
                prefix={<UserOutlined />}
                valueStyle={{ color: COLORS.primary }}
              />
            </Col>
            <Col span={12}>
              <Statistic
                title="Nuevos Este Mes"
                value={kpis.pacientes.nuevosMes}
                prefix={<UserOutlined />}
                valueStyle={{ color: COLORS.success }}
                suffix={
                  <Tag color="green" icon={<RiseOutlined />}>
                    +{kpis.pacientes.crecimiento}%
                  </Tag>
                }
              />
            </Col>
            <Col span={24}>
              <Divider style={{ margin: '12px 0' }} />
            </Col>
            <Col span={24}>
              <div>
                <Text strong>Crecimiento Mensual</Text>
                <Progress
                  percent={Math.min(kpis.pacientes.crecimiento, 100)}
                  strokeColor={{
                    from: COLORS.primary,
                    to: COLORS.success,
                  }}
                  status="active"
                />
              </div>
            </Col>
            <Col span={24}>
              <div>
                <Text strong>Tasa de Retención de Pacientes</Text>
                <Progress
                  percent={92}
                  strokeColor={COLORS.cyan}
                  status="success"
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  92% de los pacientes continúan su tratamiento
                </Text>
              </div>
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>

    {/* Fila 5: Radar Chart - Rendimiento General */}
    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
      <Col xs={24}>
        <Card title="🎯 Radar de Rendimiento del Sistema">
          <ResponsiveContainer width="100%" height={400}>
            {/* @ts-ignore */}
            <RadarChart data={radarData}>
              {/* @ts-ignore */}
              <PolarGrid />
              {/* @ts-ignore */}
              <PolarAngleAxis dataKey="indicator" />
              {/* @ts-ignore */}
              <PolarRadiusAxis angle={90} domain={RADAR_DOMAIN} />
              {/* @ts-ignore */}
              <Radar
                name="Rendimiento Actual"
                dataKey="value"
                stroke={COLORS.primary}
                fill={COLORS.primary}
                fillOpacity={0.6}
              />
              <Tooltip />
              <Legend />
            </RadarChart>
          </ResponsiveContainer>
          <div style={{ marginTop: 16, textAlign: 'center' }}>
            <Space>
              <Tag color="blue" icon={<RiseOutlined />}>
                Indicadores de actividad del sistema
              </Tag>
              <Tag color="orange" icon={<FallOutlined />}>
                Áreas de mejora identificadas
              </Tag>
              <Tag color="default" icon={<MinusOutlined />}>
                Estabilidad operativa
              </Tag>
            </Space>
          </div>
        </Card>
      </Col>
    </Row>
  </>
);

export default DashboardGraficasCharts;
