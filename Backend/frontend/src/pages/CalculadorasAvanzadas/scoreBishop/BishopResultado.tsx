import React, { lazy, Suspense } from 'react';
import { Card, Row, Col, Space, Statistic, Divider, Alert, Descriptions, Spin } from 'antd';
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { TENDENCIA_DOMAIN, ResultadoBishop } from './scoreBishopUtils';

const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })) as any);
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })) as any);
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })) as any);

const renderPieLabel = ({ name, value }: { name: string; value: number }) => `${name}: ${value}`;

interface BishopResultadoProps {
  resultado: ResultadoBishop | null;
  distribucionPie: Array<{ name: string; value: number; color: string }>;
  histograma: Array<{ rango: string; cantidad: number; color: string }>;
  tendencia: any[];
}

const BishopResultado: React.FC<BishopResultadoProps> = ({ resultado, distribucionPie, histograma, tendencia }) => {
  if (!resultado) {
    return (
      <Card>
        <Alert
          message="Instrucciones"
          description={
            <div>
              <p><strong>Score de Bishop: Evaluación Cervical para Inducción</strong></p>
              <ul>
                <li><strong>Favorable (≥8):</strong> Alta probabilidad parto vaginal (&gt;90%)</li>
                <li><strong>Intermedio (6-7):</strong> Requiere maduración cervical</li>
                <li><strong>Desfavorable (≤5):</strong> Alto riesgo cesárea (&gt;40%)</li>
              </ul>
              <p>Complete los 5 parámetros cervicales y calcule el puntaje.</p>
            </div>
          }
          type="info"
          showIcon
        />
      </Card>
    );
  }

  const color =
    resultado.clasificacion === 'FAVORABLE' ? '#52c41a'
      : resultado.clasificacion === 'INTERMEDIO' ? '#faad14'
        : '#f5222d';

  return (
    <>
      <Card
        title={
          <Space>
            {resultado.clasificacion === 'FAVORABLE' ? (
              <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 24 }} />
            ) : resultado.clasificacion === 'INTERMEDIO' ? (
              <WarningOutlined style={{ color: '#faad14', fontSize: 24 }} />
            ) : (
              <CloseCircleOutlined style={{ color: '#f5222d', fontSize: 24 }} />
            )}
            <span>Resultado del Score de Bishop</span>
          </Space>
        }
        variant="borderless"
      >
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Statistic
              title="Puntaje Total"
              value={resultado.puntaje}
              suffix="/ 13"
              valueStyle={{ fontSize: 48, color }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="Probabilidad de Éxito"
              value={resultado.probabilidadExito}
              suffix="%"
              valueStyle={{ fontSize: 36 }}
            />
          </Col>
        </Row>

        <Divider />

        <Alert
          message={`CÉRVIX ${resultado.clasificacion}`}
          description={resultado.interpretacion}
          type={resultado.color as any}
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Descriptions title="Recomendación Clínica" bordered column={1}>
          <Descriptions.Item label="Conducta Obstétrica">
            {resultado.recomendacion}
          </Descriptions.Item>
          <Descriptions.Item label="Monitoreo">
            Vigilancia materno-fetal continua durante inducción. NST basal + monitoreo continuo FCF y DU.
          </Descriptions.Item>
          <Descriptions.Item label="Criterios de Falla">
            No progreso de dilatación tras 12-18h de oxitocina adecuada o aparición de SFA.
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Divider />

      {/* Gráficas Estadísticas */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="Distribución Poblacional (n=5)" variant="borderless">
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={distribucionPie}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderPieLabel}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {distribucionPie.map((entry) => (
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
          <Card title="Histograma de Puntajes" variant="borderless">
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={histograma}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="rango" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="cantidad" fill="#1890ff">
                    {histograma.map((entry) => (
                      <Cell key={`cell-${entry.rango}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Suspense>
          </Card>
        </Col>

        <Col span={24}>
          <Card title="Tendencia de Evaluaciones" variant="borderless">
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={tendencia}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis domain={TENDENCIA_DOMAIN} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="puntaje" stroke="#1890ff" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Suspense>
          </Card>
        </Col>
      </Row>
    </>
  );
};

export default BishopResultado;
