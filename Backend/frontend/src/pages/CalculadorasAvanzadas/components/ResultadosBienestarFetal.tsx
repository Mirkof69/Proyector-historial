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

const getDataBPP = (resultado: ResultadoSufrimiento) => [
  { componente: 'NST', puntos: resultado.bpp_componentes.nst, maximo: 2 },
  { componente: 'Respiración', puntos: resultado.bpp_componentes.respiracion, maximo: 2 },
  { componente: 'Movimientos', puntos: resultado.bpp_componentes.movimientos, maximo: 2 },
  { componente: 'Tono', puntos: resultado.bpp_componentes.tono, maximo: 2 },
  { componente: 'Líquido', puntos: resultado.bpp_componentes.liquido, maximo: 2 },
];

const getDataCTG = () => [
  { categoria: 'Cat I\nNormal', frecuencia: 60, color: 'var(--color-exito)' },
  { categoria: 'Cat II\nIndeterminado', frecuencia: 30, color: 'var(--color-aviso)' },
  { categoria: 'Cat III\nAnormal', frecuencia: 10, color: 'var(--color-peligro)' },
];

const getDataDoppler = (form: any, resultado: ResultadoSufrimiento) => {
  const valores = form.getFieldsValue();
  return [
    { parametro: 'AU PI', valor: valores.arteria_umbilical_pi || 0, normal: 1.0, limite: 1.4 },
    { parametro: 'AU RI', valor: valores.arteria_umbilical_ri || 0, normal: 0.55, limite: 0.7 },
    { parametro: 'ACM PI', valor: valores.arteria_cerebral_media_pi || 0, normal: 1.8, limite: 1.0 },
    { parametro: 'CPR', valor: resultado?.relacion_cp || 0, normal: 1.5, limite: 1.0 },
  ];
};

const getDataRadar = (resultado: ResultadoSufrimiento, form: any) => [
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
      let color = 'success';
      if (score <= 2) color = 'error';
      else if (score <= 4) color = 'warning';
      else if (score === 6) color = 'warning';
      return <Tag color={color}>{score}/10</Tag>;
    },
  },
  {
    title: 'CTG', dataIndex: 'ctg_categoria', key: 'ctg_categoria',
    render: (cat: string) => {
      let color = 'success';
      if (cat.includes('III')) color = 'error';
      else if (cat.includes('II')) color = 'warning';
      return <Tag color={color}>{cat}</Tag>;
    },
  },
  {
    title: 'Nivel de Riesgo', dataIndex: 'nivel_riesgo', key: 'nivel_riesgo',
    render: (riesgo: string) => {
      let color = 'success';
      if (riesgo.includes('CRÍTICO')) color = 'error';
      else if (riesgo === 'ALTO') color = 'warning';
      else if (riesgo === 'MODERADO') color = 'warning';
      return <Tag color={color}>{riesgo}</Tag>;
    },
  },
];

export const ResultadosBienestarFetal: React.FC<ResultadosBienestarFetalProps> = ({ resultado, historial, form }) => {
  return (
    <>
      <Row gutter={[16, 16]} className="calc-bloque-arriba">
        <Col xs={24} sm={12} md={6}>
          <Card className="calc-stat-card">
            <Statistic title="BPP Score" value={`${resultado.bpp_score}/10`} valueStyle={{ color: resultado.bpp_color }} prefix={<SafetyOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="calc-stat-card">
            <Statistic title="CTG" value={resultado.ctg_categoria} className="calc-cifra-pequena" valueStyle={{ color: resultado.ctg_color }} prefix={<LineChartOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="calc-stat-card">
            <Statistic title="Relación C/P" value={resultado.relacion_cp.toFixed(2)} valueStyle={{ color: resultado.relacion_cp >= 1.0 ? 'var(--color-exito)' : 'var(--color-peligro)' }} suffix={resultado.relacion_cp >= 1.0 ? <CheckCircleOutlined /> : <WarningOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="calc-stat-card">
            <Statistic title="Nivel de Riesgo" value={resultado.nivel_riesgo} className="calc-cifra-pequena" valueStyle={{ color: resultado.color_riesgo }} prefix={<WarningOutlined />} />
          </Card>
        </Col>
      </Row>

      <Card title="Interpretación Clínica" className="calc-bloque-arriba">
        <Alert message={resultado.accion_inmediata} description={resultado.interpretacion} type={resultado.nivel_riesgo.includes('CRÍTICO') ? 'error' : resultado.nivel_riesgo === 'ALTO' ? 'warning' : 'success'} showIcon />
      </Card>

      <Card title="Recomendaciones de Manejo" className="calc-bloque-arriba">
        <Space direction="vertical" className="calc-pila">
          {(() => {
            // Tipo constante por render: se calcula una vez fuera del map.
            const tipoRec = resultado.nivel_riesgo.includes('CRÍTICO') ? 'error' : resultado.nivel_riesgo === 'ALTO' ? 'warning' : 'info';
            return resultado.recomendaciones.map((rec) => (
              <Alert key={`rec-${rec}`} message={rec} type={tipoRec} showIcon />
            ));
          })()}
        </Space>
      </Card>

      <Divider><span className="calc-titulo-seccion"><LineChartOutlined /> Análisis Gráfico</span></Divider>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Perfil Biofísico - Componentes">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataBPP(resultado)}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="componente" /><YAxis domain={BPP_SCORE_DOMAIN} ticks={BPP_TICKS} /><Tooltip /><Legend />
                <Bar dataKey="puntos" fill="var(--grafico-1)" name="Puntos Obtenidos" /><Bar dataKey="maximo" fill="var(--color-borde-fuerte)" name="Máximo" />
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
              <BarChart data={getDataDoppler(form, resultado)}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="parametro" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="valor" fill="var(--grafico-1)" name="Valor Actual" /><Bar dataKey="normal" fill="var(--color-exito)" name="Normal" /><Bar dataKey="limite" fill="var(--color-peligro)" name="Límite" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Evaluación Multidimensional - Scores">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getDataRadar(resultado, form)}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="categoria" /><YAxis domain={BPP_DOMAIN} label={SCORE_LABEL} /><Tooltip /><Legend />
                <Bar dataKey="puntaje" fill="var(--grafico-1)" name="Puntaje" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {historial.length > 0 && (
        <Card title="Historial de Evaluaciones" className="calc-bloque-arriba">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={[...historial].reverse()}>
              <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="fecha" tick={HISTORIAL_TICK} /><YAxis domain={HISTORIAL_DOMAIN} label={BPP_LABEL} /><Tooltip /><Legend />
              <Line type="monotone" dataKey="bpp_score" stroke="var(--grafico-1)" name="BPP Score" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <Table columns={columnasHistorial} dataSource={historial} rowKey={(record) => record.fecha} pagination={{ pageSize: 5 }} size="small" className="calc-bloque-arriba" />
        </Card>
      )}
    </>
  );
};
