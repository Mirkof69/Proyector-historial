import React from 'react';
import { Card, Row, Col, Statistic, Alert, Space, Divider, Table, Tag } from 'antd';
import {
  SafetyOutlined,
  LineChartOutlined,
  WarningOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import { lazy } from 'react';

const BarChart = lazy(() => import('recharts').then(mod => ({ default: mod.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(mod => ({ default: mod.Bar })) as any);
const PieChart = lazy(() => import('recharts').then(mod => ({ default: mod.PieChart })) as any);
const Pie = lazy(() => import('recharts').then(mod => ({ default: mod.Pie })) as any);
const Cell = lazy(() => import('recharts').then(mod => ({ default: mod.Cell })) as any);
const XAxis = lazy(() => import('recharts').then(mod => ({ default: mod.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(mod => ({ default: mod.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(mod => ({ default: mod.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(mod => ({ default: mod.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(mod => ({ default: mod.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(mod => ({ default: mod.ResponsiveContainer })) as any);
const LineChart = lazy(() => import('recharts').then(mod => ({ default: mod.LineChart })) as any);
const Line = lazy(() => import('recharts').then(mod => ({ default: mod.Line })) as any);

interface ResultadoSufrimiento {
  bpp_score: number;
  bpp_color: string;
  bpp_componentes: { nst: number; respiracion: number; movimientos: number; tono: number; liquido: number };
  ctg_categoria: string;
  ctg_color: string;
  ctg_interpretacion: string;
  relacion_cp: number;
  nivel_riesgo: string;
  color_riesgo: string;
  accion_inmediata: string;
  interpretacion: string;
  recomendaciones: string[];
  doppler_anormal: boolean;
}

interface RegistroSufrimiento {
  fecha: string;
  bpp_score: number;
  ctg_categoria: string;
  nivel_riesgo: string;
}

interface ResultadosBienestarFetalProps {
  resultado: ResultadoSufrimiento;
  historial: RegistroSufrimiento[];
  form: any;
}

const BPP_TICKS = [0, 1, 2];
const BPP_SCORE_DOMAIN = [0, 2];
const BPP_DOMAIN = [0, 100];
const HISTORIAL_DOMAIN = [0, 10];
const HISTORIAL_TICK = { fontSize: 12 };
const SCORE_LABEL = { value: 'Score (%)', angle: -90, position: 'insideLeft' };
const BPP_LABEL = { value: 'BPP Score', angle: -90, position: 'insideLeft' };

const renderCTGLabel = (props: any) => {
  const { categoria, frecuencia } = props;
  return `${categoria}: ${frecuencia}%`;
};

export const ResultadosBienestarFetal: React.FC<ResultadosBienestarFetalProps> = ({ resultado, historial, form }) => {
  const getDataBPP = () => [
    { componente: 'NST', puntos: resultado.bpp_componentes.nst, maximo: 2 },
    { componente: 'Respiración', puntos: resultado.bpp_componentes.respiracion, maximo: 2 },
    { componente: 'Movimientos', puntos: resultado.bpp_componentes.movimientos, maximo: 2 },
    { componente: 'Tono', puntos: resultado.bpp_componentes.tono, maximo: 2 },
    { componente: 'Líquido', puntos: resultado.bpp_componentes.liquido, maximo: 2 },
  ];

  const getDataCTG = () => [
    { categoria: 'Cat I\nNormal', frecuencia: 60, color: '#52c41a' },
    { categoria: 'Cat II\nIndeterminado', frecuencia: 30, color: '#faad14' },
    { categoria: 'Cat III\nAnormal', frecuencia: 10, color: '#ff4d4f' },
  ];

  const getDataDoppler = () => {
    const valores = form.getFieldsValue();
    return [
      { parametro: 'AU PI', valor: valores.arteria_umbilical_pi || 0, normal: 1.0, limite: 1.4 },
      { parametro: 'AU RI', valor: valores.arteria_umbilical_ri || 0, normal: 0.55, limite: 0.7 },
      { parametro: 'ACM PI', valor: valores.arteria_cerebral_media_pi || 0, normal: 1.8, limite: 1.0 },
      { parametro: 'CPR', valor: resultado?.relacion_cp || 0, normal: 1.5, limite: 1.0 },
    ];
  };

  const getDataRadar = () => [
    { categoria: 'BPP', puntaje: (resultado.bpp_score / 10) * 100, fullMark: 100 },
    { categoria: 'CTG', puntaje: resultado.ctg_categoria.includes('I') ? 100 : resultado.ctg_categoria.includes('II') ? 50 : 0, fullMark: 100 },
    { categoria: 'Doppler', puntaje: resultado.doppler_anormal ? 30 : 100, fullMark: 100 },
    { categoria: 'LA', puntaje: form.getFieldValue('volumen_liquido') >= 5 ? 100 : (form.getFieldValue('volumen_liquido') / 5) * 100, fullMark: 100 },
    { categoria: 'Crecimiento', puntaje: form.getFieldValue('peso_estimado_percentil'), fullMark: 100 },
  ];

  const columnasHistorial = [
    { title: 'Fecha/Hora', dataIndex: 'fecha', key: 'fecha' },
    {
      title: 'BPP Score', dataIndex: 'bpp_score', key: 'bpp_score',
      render: (score: number) => {
        let color = 'green';
        if (score <= 2) color = 'red';
        else if (score <= 4) color = 'orange';
        else if (score === 6) color = 'gold';
        return <Tag color={color}>{score}/10</Tag>;
      },
    },
    {
      title: 'CTG', dataIndex: 'ctg_categoria', key: 'ctg_categoria',
      render: (cat: string) => {
        let color = 'green';
        if (cat.includes('III')) color = 'red';
        else if (cat.includes('II')) color = 'orange';
        return <Tag color={color}>{cat}</Tag>;
      },
    },
    {
      title: 'Nivel de Riesgo', dataIndex: 'nivel_riesgo', key: 'nivel_riesgo',
      render: (riesgo: string) => {
        let color = 'green';
        if (riesgo.includes('CRÍTICO')) color = 'red';
        else if (riesgo === 'ALTO') color = 'orange';
        else if (riesgo === 'MODERADO') color = 'gold';
        return <Tag color={color}>{riesgo}</Tag>;
      },
    },
  ];

  return (
    <>
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="BPP Score" value={`${resultado.bpp_score}/10`} valueStyle={{ color: resultado.bpp_color }} prefix={<SafetyOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="CTG" value={resultado.ctg_categoria} valueStyle={{ color: resultado.ctg_color, fontSize: 16 }} prefix={<LineChartOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="Relación C/P" value={resultado.relacion_cp.toFixed(2)} valueStyle={{ color: resultado.relacion_cp >= 1.0 ? '#52c41a' : '#ff4d4f' }} suffix={resultado.relacion_cp >= 1.0 ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : <WarningOutlined style={{ color: '#ff4d4f' }} />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic title="Nivel de Riesgo" value={resultado.nivel_riesgo} valueStyle={{ color: resultado.color_riesgo, fontSize: 14 }} prefix={<WarningOutlined />} />
          </Card>
        </Col>
      </Row>

      <Card title="Interpretación Clínica" style={{ marginTop: 16 }}>
        <Alert message={resultado.accion_inmediata} description={resultado.interpretacion} type={resultado.nivel_riesgo.includes('CRÍTICO') ? 'error' : resultado.nivel_riesgo === 'ALTO' ? 'warning' : 'success'} showIcon />
      </Card>

      <Card title="Recomendaciones de Manejo" style={{ marginTop: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          {resultado.recomendaciones.map((rec) => (
            <Alert key={`rec-${rec}`} message={rec} type={resultado.nivel_riesgo.includes('CRÍTICO') ? 'error' : resultado.nivel_riesgo === 'ALTO' ? 'warning' : 'info'} showIcon />
          ))}
        </Space>
      </Card>

      <Divider><LineChartOutlined /> Análisis Gráfico</Divider>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Perfil Biofísico - Componentes">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataBPP()}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="componente" /><YAxis domain={BPP_SCORE_DOMAIN} ticks={BPP_TICKS} /><Tooltip /><Legend />
                <Bar dataKey="puntos" fill="#eb2f96" name="Puntos Obtenidos" /><Bar dataKey="maximo" fill="#d9d9d9" name="Máximo" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Distribución CTG (ACOG)">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={getDataCTG()} label={renderCTGLabel} outerRadius={100} dataKey="frecuencia">
                  {getDataCTG().map((entry) => (<Cell key={`cell-${entry.categoria}`} fill={entry.color} />))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Índices Doppler">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataDoppler()}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="parametro" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="valor" fill="#722ed1" name="Valor Actual" /><Bar dataKey="normal" fill="#52c41a" name="Normal" /><Bar dataKey="limite" fill="#ff4d4f" name="Límite" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Evaluación Multidimensional - Scores">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataRadar()}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="categoria" /><YAxis domain={BPP_DOMAIN} label={SCORE_LABEL} /><Tooltip /><Legend />
                <Bar dataKey="puntaje" fill="#eb2f96" name="Puntaje" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {historial.length > 0 && (
        <Card title="Historial de Evaluaciones" style={{ marginTop: 16 }}>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={[...historial].reverse()}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="fecha" tick={HISTORIAL_TICK} /><YAxis domain={HISTORIAL_DOMAIN} label={BPP_LABEL} /><Tooltip /><Legend />
              <Line type="monotone" dataKey="bpp_score" stroke="#eb2f96" name="BPP Score" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <Table columns={columnasHistorial} dataSource={historial} rowKey={(record) => record.fecha} pagination={{ pageSize: 5 }} size="small" style={{ marginTop: 16 }} />
        </Card>
      )}
    </>
  );
};
