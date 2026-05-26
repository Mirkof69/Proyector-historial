import React, { useState } from 'react';
import {
  Card, Row, Col, Form, Select, Button, Statistic, Alert, Table,
  Descriptions, Space, Tag, message, Divider
} from 'antd';
import {
  CalculatorOutlined, CheckCircleOutlined, WarningOutlined,
  CloseCircleOutlined, TrophyOutlined, HistoryOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import './ScoreBishop.css';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell
} from 'recharts';

interface BishopScore {
  dilatacion: number;
  borramiento: number;
  estacion: number;
  consistencia: number;
  posicion: number;
}

interface ResultadoBishop {
  puntaje: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  probabilidadExito: number;
}

interface HistorialBishop {
  id: number;
  fecha: string;
  paciente: string;
  edadGestacional: number;
  puntaje: number;
  resultado: string;
}

const CALCULATOR_ICON_2 = <CalculatorOutlined />;

const BISHOP_DOMAIN = [0, 3];
const TENDENCIA_DOMAIN = [0, 13];
const renderPieLabel = ({ name, value }: { name: string; value: number }) => `${name}: ${value}`;

const ScoreBishop: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoBishop | null>(null);
  const [historial, setHistorial] = useState<HistorialBishop[]>([
    {
      id: 1,
      fecha: '2024-12-18 10:30',
      paciente: 'María García',
      edadGestacional: 40,
      puntaje: 9,
      resultado: 'Favorable'
    },
    {
      id: 2,
      fecha: '2024-12-18 09:15',
      paciente: 'Carmen López',
      edadGestacional: 39,
      puntaje: 4,
      resultado: 'Desfavorable'
    },
    {
      id: 3,
      fecha: '2024-12-17 16:20',
      paciente: 'Ana Martínez',
      edadGestacional: 41,
      puntaje: 7,
      resultado: 'Intermedio'
    },
    {
      id: 4,
      fecha: '2024-12-17 14:10',
      paciente: 'Laura Fernández',
      edadGestacional: 40,
      puntaje: 10,
      resultado: 'Favorable'
    },
    {
      id: 5,
      fecha: '2024-12-16 11:45',
      paciente: 'Rosa Sánchez',
      edadGestacional: 38,
      puntaje: 3,
      resultado: 'Desfavorable'
    }
  ]);
  const [loading, setLoading] = useState(false);

  const calcularBishop = (values: BishopScore): ResultadoBishop => {
    const puntaje =
      values.dilatacion +
      values.borramiento +
      values.estacion +
      values.consistencia +
      values.posicion;

    let clasificacion = '';
    let color = '';
    let interpretacion = '';
    let recomendacion = '';
    let probabilidadExito = 0;

    if (puntaje >= 8) {
      clasificacion = 'FAVORABLE';
      color = 'success';
      interpretacion =
        'Cérvix favorable para inducción. Alta probabilidad de parto vaginal exitoso (>90%).';
      recomendacion =
        'Proceder con inducción según indicación clínica. Oxitocina IV o amniotomía. Monitoreo materno-fetal continuo.';
      probabilidadExito = 90 + puntaje;
    } else if (puntaje >= 6) {
      clasificacion = 'INTERMEDIO';
      color = 'warning';
      interpretacion =
        'Cérvix moderadamente favorable. Probabilidad intermedia de éxito (70-85%).';
      recomendacion =
        'Considerar maduración cervical con prostaglandinas (misoprostol 25 µg vaginal cada 3-6h o dinoprostona gel). Reevaluar Bishop en 12-24h antes de proceder con oxitocina.';
      probabilidadExito = 65 + puntaje * 2;
    } else {
      clasificacion = 'DESFAVORABLE';
      color = 'error';
      interpretacion =
        'Cérvix desfavorable. Alta probabilidad de falla de inducción y necesidad de cesárea (>40%).';
      recomendacion =
        'Maduración cervical obligatoria: prostaglandinas vaginales (misoprostol, dinoprostona) o sonda Foley. NO iniciar oxitocina. Reevaluar Bishop cada 24h. Considerar cesárea electiva según indicación.';
      probabilidadExito = 30 + puntaje * 5;
    }

    return {
      puntaje,
      clasificacion,
      color,
      interpretacion,
      recomendacion,
      probabilidadExito: Math.min(probabilidadExito, 99)
    };
  };

  const onFinish = (values: BishopScore) => {
    setLoading(true);
    setTimeout(() => {
      const res = calcularBishop(values);
      setResultado(res);
      message.success(`Score Bishop: ${res.puntaje} - ${res.clasificacion}`);
      setLoading(false);
    }, 500);
  };

  const resetear = () => {
    form.resetFields();
    setResultado(null);
  };

  // Datos para gráficas
  const getRadarData = () => {
    if (!resultado) return [];
    const values = form.getFieldsValue();
    return [
      { parametro: 'Dilatación', valor: values.dilatacion || 0, maxValor: 3 },
      { parametro: 'Borramiento', valor: values.borramiento || 0, maxValor: 3 },
      { parametro: 'Estación', valor: values.estacion || 0, maxValor: 3 },
      { parametro: 'Consistencia', valor: values.consistencia || 0, maxValor: 2 },
      { parametro: 'Posición', valor: values.posicion || 0, maxValor: 2 }
    ];
  };

  const getHistogramaData = () => {
    const distribucion = [
      { rango: '0-2', cantidad: historial.filter(h => h.puntaje <= 2).length, color: '#f5222d' },
      { rango: '3-5', cantidad: historial.filter(h => h.puntaje >= 3 && h.puntaje <= 5).length, color: '#fa8c16' },
      { rango: '6-7', cantidad: historial.filter(h => h.puntaje >= 6 && h.puntaje <= 7).length, color: '#faad14' },
      { rango: '8-10', cantidad: historial.filter(h => h.puntaje >= 8 && h.puntaje <= 10).length, color: '#52c41a' },
      { rango: '11-13', cantidad: historial.filter(h => h.puntaje >= 11).length, color: '#1890ff' }
    ];
    return distribucion;
  };

  const getDistribucionPie = () => {
    const favorable = historial.filter(h => h.puntaje >= 8).length;
    const intermedio = historial.filter(h => h.puntaje >= 6 && h.puntaje < 8).length;
    const desfavorable = historial.filter(h => h.puntaje < 6).length;

    return [
      { name: 'Favorable', value: favorable, color: '#52c41a' },
      { name: 'Intermedio', value: intermedio, color: '#faad14' },
      { name: 'Desfavorable', value: desfavorable, color: '#f5222d' }
    ];
  };

  const getTendenciaData = () => {
    return historial.slice(0, 10).reverse().map((item, index) => ({
      fecha: dayjs(item.fecha).format('DD/MM HH:mm'),
      puntaje: item.puntaje,
      egSemanas: item.edadGestacional
    }));
  };

  // Estadísticas globales
  const promedioScore = historial.length > 0
    ? (historial.reduce((sum, h) => sum + h.puntaje, 0) / historial.length).toFixed(1)
    : 0;
  const tasaFavorable = historial.length > 0
    ? ((historial.filter(h => h.puntaje >= 8).length / historial.length) * 100).toFixed(0)
    : 0;

  const columnsHistorial = [
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm')
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente',
      key: 'paciente'
    },
    {
      title: 'EG (semanas)',
      dataIndex: 'edadGestacional',
      key: 'eg'
    },
    {
      title: 'Score',
      dataIndex: 'puntaje',
      key: 'puntaje',
      render: (puntaje: number) => (
        <Tag color={puntaje >= 8 ? 'green' : puntaje >= 6 ? 'orange' : 'red'}>
          <strong>{puntaje}</strong>
        </Tag>
      )
    },
    {
      title: 'Resultado',
      dataIndex: 'resultado',
      key: 'resultado',
      render: (resultado: string) => (
        <Tag color={resultado === 'Favorable' ? 'success' : resultado === 'Intermedio' ? 'warning' : 'error'}>
          {resultado}
        </Tag>
      )
    }
  ];

  return (
    <div className="score-bishop-page" style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1><CalculatorOutlined /> Score de Bishop - Maduración Cervical</h1>
        <p style={{ color: '#666' }}>
          Evaluación cuantitativa de favorabilidad del cérvix para inducción del parto (0-13 puntos)
        </p>
      </div>

      {/* Estadísticas globales */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Evaluaciones"
              value={historial.length}
              prefix={<HistoryOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Promedio Score"
              value={promedioScore}
              suffix="/ 13"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Tasa Favorable"
              value={tasaFavorable}
              suffix="%"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Último Score"
              value={historial[0]?.puntaje || 0}
              suffix="puntos"
              valueStyle={{
                color: (historial[0]?.puntaje || 0) >= 8 ? '#52c41a' : '#fa8c16'
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Formulario */}
        <Col xs={24} lg={10}>
          <Card title="Evaluación de Parámetros Cervicales" bordered={false}>
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                dilatacion: 0,
                borramiento: 0,
                estacion: 0,
                consistencia: 0,
                posicion: 0
              }}
            >
              <Form.Item
                label="Dilatación Cervical"
                name="dilatacion"
                rules={[{ required: true, message: 'Seleccione dilatación' }]}
              >
                <Select size="large">
                  <Select.Option value={0}>Cerrado (0 puntos)</Select.Option>
                  <Select.Option value={1}>1-2 cm (1 punto)</Select.Option>
                  <Select.Option value={2}>3-4 cm (2 puntos)</Select.Option>
                  <Select.Option value={3}>≥5 cm (3 puntos)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Borramiento Cervical"
                name="borramiento"
                rules={[{ required: true, message: 'Seleccione borramiento' }]}
              >
                <Select size="large">
                  <Select.Option value={0}>0-30% (0 puntos)</Select.Option>
                  <Select.Option value={1}>40-50% (1 punto)</Select.Option>
                  <Select.Option value={2}>60-70% (2 puntos)</Select.Option>
                  <Select.Option value={3}>≥80% (3 puntos)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Estación de Presentación"
                name="estacion"
                rules={[{ required: true, message: 'Seleccione estación' }]}
              >
                <Select size="large">
                  <Select.Option value={0}>-3 (0 puntos)</Select.Option>
                  <Select.Option value={1}>-2 (1 punto)</Select.Option>
                  <Select.Option value={2}>-1 / 0 (2 puntos)</Select.Option>
                  <Select.Option value={3}>+1 / +2 (3 puntos)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Consistencia Cervical"
                name="consistencia"
                rules={[{ required: true, message: 'Seleccione consistencia' }]}
              >
                <Select size="large">
                  <Select.Option value={0}>Firme (0 puntos)</Select.Option>
                  <Select.Option value={1}>Media (1 punto)</Select.Option>
                  <Select.Option value={2}>Blanda (2 puntos)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="Posición Cervical"
                name="posicion"
                rules={[{ required: true, message: 'Seleccione posición' }]}
              >
                <Select size="large">
                  <Select.Option value={0}>Posterior (0 puntos)</Select.Option>
                  <Select.Option value={1}>Media (1 punto)</Select.Option>
                  <Select.Option value={2}>Anterior (2 puntos)</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={CALCULATOR_ICON_2}
                    size="large"
                    loading={loading}
                  >
                    Calcular Score
                  </Button>
                  <Button onClick={resetear} size="large">
                    Limpiar
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>

          {/* Gráfica de Parámetros */}
          {resultado && (
            <Card title="Distribución de Parámetros" style={{ marginTop: 16 }}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getRadarData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="parametro" />
                  <YAxis domain={BISHOP_DOMAIN} />
                  <Tooltip />
                  <Legend />
                  <Bar name="Valor Actual" dataKey="valor" fill="#1890ff" />
                  <Bar name="Máximo" dataKey="maxValor" fill="#52c41a" opacity={0.3} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </Col>

        {/* Resultado */}
        <Col xs={24} lg={14}>
          {resultado ? (
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
                bordered={false}
              >
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Statistic
                      title="Puntaje Total"
                      value={resultado.puntaje}
                      suffix="/ 13"
                      valueStyle={{
                        fontSize: 48,
                        color:
                          resultado.clasificacion === 'FAVORABLE'
                            ? '#52c41a'
                            : resultado.clasificacion === 'INTERMEDIO'
                            ? '#faad14'
                            : '#f5222d'
                      }}
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
                  <Card title="Distribución Poblacional (n=5)" bordered={false}>
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={getDistribucionPie()}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={renderPieLabel}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {getDistribucionPie().map((entry) => (
                            <Cell key={`cell-${entry.name}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col xs={24} md={12}>
                  <Card title="Histograma de Puntajes" bordered={false}>
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={getHistogramaData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="rango" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="cantidad" fill="#1890ff">
                          {getHistogramaData().map((entry) => (
                            <Cell key={`cell-${entry.rango}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>

                <Col span={24}>
                  <Card title="Tendencia de Evaluaciones" bordered={false}>
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={getTendenciaData()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="fecha" />
                        <YAxis domain={TENDENCIA_DOMAIN} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="puntaje" stroke="#1890ff" strokeWidth={2} />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                </Col>
              </Row>
            </>
          ) : (
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
          )}
        </Col>
      </Row>

      {/* Historial */}
      <Card title="Historial de Evaluaciones" style={{ marginTop: 24 }}>
        <Table
          columns={columnsHistorial}
          dataSource={historial}
          rowKey="id"
          pagination={{ pageSize: 5 }}
        />
      </Card>
    </div>
  );
};

export default ScoreBishop;
