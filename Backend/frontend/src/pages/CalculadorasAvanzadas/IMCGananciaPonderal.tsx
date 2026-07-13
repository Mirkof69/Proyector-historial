import React, { useState } from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Table, Divider, Typography, Space, Tag } from 'antd';
import { CalculatorOutlined, HeartOutlined, LineChartOutlined, RiseOutlined } from '@ant-design/icons';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area
} from 'recharts';
import './IMCGananciaPonderal.css';

const { Title, Text } = Typography;

interface DatosPaciente {
  peso_pregestacional: number;
  talla: number;
  peso_actual: number;
  semanas_gestacion: number;
}

interface ResultadoIMC {
  imc_pregestacional: number;
  clasificacion_imc: string;
  color_imc: string;
  ganancia_actual: number;
  ganancia_recomendada_min: number;
  ganancia_recomendada_max: number;
  ganancia_ideal_semana: number;
  ganancia_total_esperada: number;
  percentil_ganancia: number;
  estado_nutricional: string;
  recomendaciones: string[];
  alertas: string[];
}

interface RegistroIMC {
  id: number;
  fecha: string;
  semanas: number;
  peso: number;
  ganancia: number;
  imc: number;
  estado: string;
}

const renderIMCLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`;
const formatPesoTooltip = (value: any) => value ? `${Number(value).toFixed(2)} kg` : '0 kg';



// Función para clasificar IMC según OMS
const clasificarIMC = (imc: number): { clasificacion: string; color: string } => {
  if (imc < 18.5) return { clasificacion: 'BAJO PESO', color: '#faad14' };
  if (imc < 25) return { clasificacion: 'NORMAL', color: '#52c41a' };
  if (imc < 30) return { clasificacion: 'SOBREPESO', color: '#fa8c16' };
  if (imc < 35) return { clasificacion: 'OBESIDAD I', color: '#f5222d' };
  if (imc < 40) return { clasificacion: 'OBESIDAD II', color: '#cf1322' };
  return { clasificacion: 'OBESIDAD III', color: '#a8071a' };
};

// Función para obtener ganancia recomendada según IOM (Institute of Medicine)
const getGananciaRecomendada = (imc: number): { min: number; max: number; semanal: number } => {
  if (imc < 18.5) return { min: 12.5, max: 18, semanal: 0.5 };
  if (imc < 25) return { min: 11.5, max: 16, semanal: 0.4 };
  if (imc < 30) return { min: 7, max: 11.5, semanal: 0.3 };
  return { min: 5, max: 9, semanal: 0.2 };
};

// Función para calcular percentil de ganancia
const calcularPercentil = (imc: number, semanas: number, ganancia: number): number => {
  const gananciaRecomendada = getGananciaRecomendada(imc);
  const gananciaEsperada = gananciaRecomendada.semanal * semanas;
  const desviacion = (ganancia - gananciaEsperada) / gananciaEsperada;
  if (desviacion < -0.3) return 10;
  if (desviacion < -0.1) return 25;
  if (desviacion < 0.1) return 50;
  if (desviacion < 0.3) return 75;
  return 90;
};

const calcularIMC = (values: DatosPaciente): ResultadoIMC => {
  const imc_pregestacional = values.peso_pregestacional / Math.pow(values.talla / 100, 2);
  const { clasificacion, color } = clasificarIMC(imc_pregestacional);
  const gananciaRecomendada = getGananciaRecomendada(imc_pregestacional);
  const ganancia_actual = values.peso_actual - values.peso_pregestacional;
  const ganancia_esperada_semana = gananciaRecomendada.semanal * values.semanas_gestacion;
  const percentil = calcularPercentil(imc_pregestacional, values.semanas_gestacion, ganancia_actual);

  let estado_nutricional = '';
  let alertas: string[] = [];
  let recomendaciones: string[] = [];

  if (ganancia_actual < gananciaRecomendada.min) {
    estado_nutricional = '⚠️ GANANCIA INSUFICIENTE';
    alertas.push('Ganancia de peso por debajo del rango recomendado');
    recomendaciones.push('Aumentar ingesta calórica en 300-500 kcal/día');
    recomendaciones.push('Consulta nutricional especializada');
    recomendaciones.push('Monitoreo de crecimiento fetal con ecografía');
  } else if (ganancia_actual > gananciaRecomendada.max) {
    estado_nutricional = '⚠️ GANANCIA EXCESIVA';
    alertas.push('Ganancia de peso por encima del rango recomendado');
    recomendaciones.push('Control dietético y actividad física moderada');
      recomendaciones.push('Evaluar retención de líquidos y descartar preeclampsia');
      recomendaciones.push('Screening de diabetes gestacional');
    } else {
      estado_nutricional = '✅ GANANCIA ADECUADA';
      recomendaciones.push('Mantener alimentación balanceada actual');
      recomendaciones.push('Continuar con actividad física regular');
      recomendaciones.push('Controles prenatales según protocolo');
    }

    if (imc_pregestacional < 18.5) {
      recomendaciones.push('🔹 Bajo peso: Dieta hipercalórica (2200-2400 kcal/día)');
      recomendaciones.push('Suplementación con ácidos grasos omega-3');
    } else if (imc_pregestacional >= 30) {
      recomendaciones.push('🔹 Obesidad: Control estricto de ganancia ponderal');
      recomendaciones.push('Evaluación para riesgo de diabetes gestacional y preeclampsia');
      recomendaciones.push('Dieta balanceada normocalórica (1800-2000 kcal/día)');
    }

    return {
      imc_pregestacional,
      clasificacion_imc: clasificacion,
      color_imc: color,
      ganancia_actual,
      ganancia_recomendada_min: gananciaRecomendada.min,
      ganancia_recomendada_max: gananciaRecomendada.max,
      ganancia_ideal_semana: gananciaRecomendada.semanal,
      ganancia_total_esperada: ganancia_esperada_semana,
      percentil_ganancia: percentil,
      estado_nutricional,
      recomendaciones,
      alertas
    };
  };

  const IMCGananciaPonderal: React.FC = () => {
    const [form] = Form.useForm();
    const [values, setValues] = useState<DatosPaciente>({
      peso_pregestacional: 60,
      talla: 165,
      peso_actual: 68,
      semanas_gestacion: 24
    });
    const [resultado, setResultado] = useState<ResultadoIMC | null>(null);
    const [historial, setHistorial] = useState<RegistroIMC[]>([]);

  const onFinish = (formValues: DatosPaciente) => {
    setValues(formValues);
    const result = calcularIMC(formValues);
    setResultado(result);

    // Agregar al historial
    const nuevoRegistro: RegistroIMC = {
      id: historial.length + 1,
      fecha: new Date().toISOString().slice(0, 10),
      semanas: formValues.semanas_gestacion,
      peso: formValues.peso_actual,
      ganancia: result.ganancia_actual,
      imc: result.imc_pregestacional,
      estado: result.estado_nutricional
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  // Datos para gráfica de curvas de ganancia ponderal (P10, P50, P90)
  const getCurvasGanancia = () => {
    const semanas = Array.from({ length: 40 }, (_, i) => i + 1);
    const gananciaRecomendada = getGananciaRecomendada(values.peso_pregestacional / Math.pow(values.talla / 100, 2));

    return semanas.map(semana => {
      const gananciaP50 = gananciaRecomendada.semanal * semana;
      const gananciaP10 = gananciaP50 * 0.6;
      const gananciaP90 = gananciaP50 * 1.4;
      const gananciaActual = semana === values.semanas_gestacion ? resultado?.ganancia_actual : null;

      return {
        semana,
        P10: gananciaP10,
        P50: gananciaP50,
        P90: gananciaP90,
        Actual: gananciaActual
      };
    });
  };

  // Datos para gráfica de distribución de componentes del peso
  const getComponentesPeso = () => {
    const gananciaTotal = resultado?.ganancia_actual || 0;

    return [
      { name: 'Feto', value: gananciaTotal * 0.25, porcentaje: 25, color: '#1890ff' },
      { name: 'Placenta', value: gananciaTotal * 0.05, porcentaje: 5, color: '#13c2c2' },
      { name: 'Líquido Amniótico', value: gananciaTotal * 0.06, porcentaje: 6, color: '#52c41a' },
      { name: 'Útero + Mamas', value: gananciaTotal * 0.10, porcentaje: 10, color: '#722ed1' },
      { name: 'Sangre', value: gananciaTotal * 0.12, porcentaje: 12, color: '#eb2f96' },
      { name: 'Líquidos Extracelulares', value: gananciaTotal * 0.17, porcentaje: 17, color: '#fa8c16' },
      { name: 'Reservas Grasas', value: gananciaTotal * 0.25, porcentaje: 25, color: '#faad14' }
    ];
  };

  // Datos para gráfica de comparación por trimestre
  const getComparacionTrimestre = () => {
    const imc = values.peso_pregestacional / Math.pow(values.talla / 100, 2);
    const gananciaRecomendada = getGananciaRecomendada(imc);

    return [
      {
        trimestre: '1er Trimestre',
        Actual: values.semanas_gestacion >= 13 ? gananciaRecomendada.semanal * 13 * 0.3 : resultado?.ganancia_actual || 0,
        Recomendada: gananciaRecomendada.semanal * 13 * 0.3,
        Min: gananciaRecomendada.min * 0.1,
        Max: gananciaRecomendada.max * 0.1
      },
      {
        trimestre: '2do Trimestre',
        Actual: values.semanas_gestacion >= 27 ? gananciaRecomendada.semanal * 14 * 1.2 : (values.semanas_gestacion > 13 ? resultado?.ganancia_actual || 0 : 0),
        Recomendada: gananciaRecomendada.semanal * 14 * 1.2,
        Min: gananciaRecomendada.min * 0.35,
        Max: gananciaRecomendada.max * 0.35
      },
      {
        trimestre: '3er Trimestre',
        Actual: values.semanas_gestacion > 27 ? resultado?.ganancia_actual || 0 : 0,
        Recomendada: gananciaRecomendada.semanal * 13 * 1.5,
        Min: gananciaRecomendada.min * 0.55,
        Max: gananciaRecomendada.max * 0.55
      }
    ];
  };

  // Datos para evolución temporal del IMC
  const getEvolucionIMC = () => {
    return historial.slice().reverse().map(registro => ({
      fecha: registro.fecha,
      semanas: registro.semanas,
      imc: registro.imc.toFixed(1),
      peso: registro.peso
    }));
  };

  // Columnas de la tabla de historial
  const columns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      width: 120
    },
    {
      title: 'Semanas',
      dataIndex: 'semanas',
      key: 'semanas',
      width: 100,
      render: (semanas: number) => `${semanas} sem`
    },
    {
      title: 'Peso (kg)',
      dataIndex: 'peso',
      key: 'peso',
      width: 100,
      render: (peso: number) => peso.toFixed(1)
    },
    {
      title: 'Ganancia (kg)',
      dataIndex: 'ganancia',
      key: 'ganancia',
      width: 120,
      render: (ganancia: number) => (
        <span style={{ color: ganancia >= 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }}>
          {ganancia >= 0 ? '+' : ''}{ganancia.toFixed(1)}
        </span>
      )
    },
    {
      title: 'IMC',
      dataIndex: 'imc',
      key: 'imc',
      width: 100,
      render: (imc: number) => imc.toFixed(1)
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        let color = 'default';
        if (estado.includes('ADECUADA')) color = 'success';
        if (estado.includes('INSUFICIENTE') || estado.includes('EXCESIVA')) color = 'warning';
        return <Tag color={color}>{estado}</Tag>;
      }
    }
  ];

  // Estadísticas en tiempo real
  const promedioGanancia = historial.length > 0
    ? (historial.reduce((sum, h) => sum + h.ganancia, 0) / historial.length).toFixed(1)
    : '0.0';

  const tasaAdecuada = historial.length > 0
    ? ((historial.filter(h => h.estado.includes('ADECUADA')).length / historial.length) * 100).toFixed(0)
    : '0';

  return (
    <div className="imc-ganancia-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <CalculatorOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          IMC y Ganancia Ponderal Gestacional
        </Title>
        <Text type="secondary">
          Calculadora de Índice de Masa Corporal pregestacional y monitoreo de ganancia de peso según guías IOM (Institute of Medicine)
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* Formulario de entrada */}
        <Col xs={24} lg={8}>
          <Card title="Datos de la Paciente" bordered={false}>
            <Form form={form} layout="vertical" onFinish={onFinish}>
              <Form.Item
                label="Peso Pregestacional (kg)"
                name="peso_pregestacional"
                rules={[{ required: true, message: 'Ingrese el peso pregestacional' }]}
              >
                <InputNumber
                  min={30}
                  max={200}
                  step={0.1}
                  style={{ width: '100%' }}
                  placeholder="Ej: 65.5"
                />
              </Form.Item>

              <Form.Item
                label="Talla (cm)"
                name="talla"
                rules={[{ required: true, message: 'Ingrese la talla' }]}
              >
                <InputNumber
                  min={130}
                  max={200}
                  step={0.1}
                  style={{ width: '100%' }}
                  placeholder="Ej: 165"
                />
              </Form.Item>

              <Form.Item
                label="Peso Actual (kg)"
                name="peso_actual"
                rules={[{ required: true, message: 'Ingrese el peso actual' }]}
              >
                <InputNumber
                  min={30}
                  max={200}
                  step={0.1}
                  style={{ width: '100%' }}
                  placeholder="Ej: 72.3"
                />
              </Form.Item>

              <Form.Item
                label="Semanas de Gestación"
                name="semanas_gestacion"
                rules={[{ required: true, message: 'Ingrese las semanas de gestación' }]}
              >
                <InputNumber
                  min={1}
                  max={42}
                  step={1}
                  style={{ width: '100%' }}
                  placeholder="Ej: 24"
                />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} block size="large">
                  Calcular IMC y Ganancia
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Resultados */}
        <Col xs={24} lg={16}>
          {resultado && (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* Estadísticas principales */}
              <Row gutter={16}>
                <Col xs={12} sm={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="IMC Pregestacional"
                      value={resultado.imc_pregestacional.toFixed(1)}
                      suffix="kg/m²"
                      valueStyle={{ color: resultado.color_imc }}
                    />
                    <Tag color={resultado.color_imc} style={{ marginTop: 8 }}>
                      {resultado.clasificacion_imc}
                    </Tag>
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="Ganancia Actual"
                      value={resultado.ganancia_actual.toFixed(1)}
                      suffix="kg"
                      prefix={resultado.ganancia_actual >= 0 ? <RiseOutlined /> : ''}
                      valueStyle={{ color: resultado.ganancia_actual >= 0 ? '#52c41a' : '#f5222d' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {values.semanas_gestacion} semanas
                    </Text>
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="Rango Recomendado"
                      value={`${resultado.ganancia_recomendada_min}-${resultado.ganancia_recomendada_max}`}
                      suffix="kg"
                      valueStyle={{ color: '#1890ff' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Total embarazo
                    </Text>
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card bordered={false}>
                    <Statistic
                      title="Percentil Ganancia"
                      value={`P${resultado.percentil_ganancia}`}
                      prefix={<LineChartOutlined />}
                      valueStyle={{ color: '#722ed1' }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Curva Atalah
                    </Text>
                  </Card>
                </Col>
              </Row>

              {/* Estado nutricional */}
              <Card>
                <Alert
                  message={resultado.estado_nutricional}
                  description={
                    <div>
                      <Text strong>Ganancia ideal semanal: </Text>
                      <Text>{resultado.ganancia_ideal_semana.toFixed(2)} kg/semana</Text>
                      <br />
                      <Text strong>Ganancia esperada a {values.semanas_gestacion} semanas: </Text>
                      <Text>{resultado.ganancia_total_esperada.toFixed(1)} kg</Text>
                    </div>
                  }
                  type={resultado.alertas.length > 0 ? 'warning' : 'success'}
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {resultado.alertas.length > 0 && (
                  <Alert
                    message="Alertas Clínicas"
                    description={
                      <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                        {resultado.alertas.map((alerta) => (
                          <li key={`alerta-${alerta}`}>{alerta}</li>
                        ))}
                      </ul>
                    }
                    type="error"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )}

                <div>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>
                    <HeartOutlined style={{ marginRight: 8, color: '#eb2f96' }} />
                    Recomendaciones Clínicas:
                  </Text>
                  <ul style={{ marginBottom: 0 }}>
                    {resultado.recomendaciones.map((rec) => (
                      <li key={`rec-${rec}`} style={{ marginBottom: 4 }}>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </Card>
            </Space>
          )}
        </Col>
      </Row>

      {/* Gráficas */}
      {resultado && (
        <>
          <Divider>Análisis Gráfico</Divider>
          <Row gutter={[16, 16]}>
            {/* Curvas de ganancia ponderal */}
            <Col xs={24} lg={12}>
              <Card title="Curvas de Ganancia Ponderal (Percentiles)" bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getCurvasGanancia()}>
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
              <Card title="Ganancia por Trimestre vs Recomendado" bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getComparacionTrimestre()}>
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
              <Card title="Componentes de la Ganancia de Peso" bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getComponentesPeso()}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderIMCLabel}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {getComponentesPeso().map((entry, index) => (
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
              <Card title="Evolución del Peso Gestacional" bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={getEvolucionIMC()}>
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
              } bordered={false}>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={getCurvasGanancia()}>
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
      )}

      {/* Historial y estadísticas */}
      {historial.length > 0 && (
        <>
          <Divider>Estadísticas del Historial</Divider>

          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={6}>
              <Card bordered={false}>
                <Statistic
                  title="Total Mediciones"
                  value={historial.length}
                  prefix={<LineChartOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card bordered={false}>
                <Statistic
                  title="Ganancia Promedio"
                  value={promedioGanancia}
                  suffix="kg"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card bordered={false}>
                <Statistic
                  title="% Ganancia Adecuada"
                  value={tasaAdecuada}
                  suffix="%"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card bordered={false}>
                <Statistic
                  title="Último Registro"
                  value={historial[0]?.semanas || 0}
                  suffix="sem"
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
          </Row>

          <Card title="Historial de Mediciones" bordered={false}>
            <Table
              columns={columns}
              dataSource={historial}
              rowKey="id"
              pagination={{ pageSize: 10 }}
              scroll={{ x: 800 }}
            />
          </Card>
        </>
      )}
    </div>
  );
};

export default IMCGananciaPonderal;
