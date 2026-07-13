import React, { useReducer, lazy, Suspense } from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Divider, Table, Tag, Select, Typography, Spin } from 'antd';
import { ExperimentOutlined, LineChartOutlined, BarChartOutlined, AlertOutlined, SafetyOutlined } from '@ant-design/icons';
import './CrecimientoFetal.css';

const BarChart = lazy(() => import('recharts').then(m => ({ default: m.BarChart })) as any);
const Bar = lazy(() => import('recharts').then(m => ({ default: m.Bar })) as any);
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const PieChart = lazy(() => import('recharts').then(m => ({ default: m.PieChart })) as any);
const Pie = lazy(() => import('recharts').then(m => ({ default: m.Pie })) as any);
const Cell = lazy(() => import('recharts').then(m => ({ default: m.Cell })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const ComposedChart = lazy(() => import('recharts').then(m => ({ default: m.ComposedChart })) as any);
const Area = lazy(() => import('recharts').then(m => ({ default: m.Area })) as any);
const ReferenceLine = lazy(() => import('recharts').then(m => ({ default: m.ReferenceLine })) as any);

const { Title, Text } = Typography;
const { Option } = Select;

// ==========================================================================
// REDUCER FOR GROWTH STATE (replaces cascading setState)
// ==========================================================================
interface GrowthState {
  resultado: ResultadoCrecimiento | null;
  historial: RegistroCrecimiento[];
  datosBiometria: DatosBiometria | null;
  usandoDatosEjemplo: boolean;
}

type GrowthAction =
  | { type: 'CALCULATE'; payload: { datos: DatosBiometria; resultado: ResultadoCrecimiento; registro: RegistroCrecimiento } }
  | { type: 'RESET' };

function growthReducer(state: GrowthState, action: GrowthAction): GrowthState {
  switch (action.type) {
    case 'CALCULATE':
      return {
        resultado: action.payload.resultado,
        historial: [action.payload.registro, ...state.historial],
        datosBiometria: action.payload.datos,
        usandoDatosEjemplo: false,
      };
    case 'RESET':
      return {
        resultado: null,
        historial: [],
        datosBiometria: null,
        usandoDatosEjemplo: false,
      };
    default:
      return state;
  }
}

const initialGrowthState: GrowthState = {
  resultado: null,
  historial: [],
  datosBiometria: null,
  usandoDatosEjemplo: false,
};

interface DatosBiometria {
  semanas: number;
  bpd: number;
  hc: number;
  ac: number;
  fl: number;
  formula: 'hadlock1' | 'hadlock2' | 'hadlock3' | 'hadlock4';
}

interface ResultadoCrecimiento {
  efw: number;
  percentil: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  zscore: number;
  desviacion_estandar: number;
  bpd_percentil: number;
  hc_percentil: number;
  ac_percentil: number;
  fl_percentil: number;
  categoria: 'RCIU' | 'PEG' | 'NORMAL' | 'GEG' | 'MACROSOMIA';
}

interface RegistroCrecimiento extends ResultadoCrecimiento {
  fecha: string;
  semanas: number;
  bpd: number;
  hc: number;
  ac: number;
  fl: number;
}

const PROPORCIONES_DOMAIN = [0, 1.5];
const formatPesoTooltip = (value: any) => value ? `${Number(value).toFixed(0)}g` : '';
const formatRatioTooltip = (value: any) => value ? Number(value).toFixed(3) : '';
const renderPercentilLabel = ({ name, value }: { name: string; value: number }) => `${name}: p${(value || 0).toFixed(0)}`;
const formatPercentilTooltip = (value: any) => value ? `p${Number(value).toFixed(1)}` : '';

// Fórmulas de Hadlock para EFW
const calcularEFW = (valores: DatosBiometria): number => {
  const { bpd, hc, ac, fl, formula } = valores;
  let efw = 0;

  switch (formula) {
    case 'hadlock1':
      const log_efw1 = 1.3596 + 0.0064 * hc + 0.0424 * ac + 0.174 * fl + 0.00061 * bpd * ac - 0.00386 * ac * fl;
      efw = Math.pow(10, log_efw1);
      break;
    case 'hadlock2':
      const log_efw2 = 1.304 + 0.05281 * ac + 0.1938 * fl - 0.004 * ac * fl;
      efw = Math.pow(10, log_efw2);
      break;
    case 'hadlock3':
      const log_efw3 = 1.335 - 0.0034 * ac * fl + 0.0316 * bpd + 0.0457 * ac + 0.1623 * fl;
      efw = Math.pow(10, log_efw3);
      break;
    case 'hadlock4':
      const log_efw4 = 1.326 - 0.00326 * ac * fl + 0.0107 * hc + 0.0438 * ac + 0.158 * fl;
      efw = Math.pow(10, log_efw4);
      break;
    default:
      efw = 0;
  }

  return efw;
};

// Percentiles de EFW según edad gestacional (basado en curvas Intergrowth-21st)
const getMedianaEFW = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    20: 300, 21: 360, 22: 430, 23: 501, 24: 600, 25: 660, 26: 760,
    27: 875, 28: 1005, 29: 1153, 30: 1319, 31: 1502, 32: 1702,
    33: 1918, 34: 2146, 35: 2383, 36: 2622, 37: 2859, 38: 3083,
    39: 3288, 40: 3462, 41: 3597, 42: 3685
  };
  const semana_int = Math.round(semanas);
  return medianas[semana_int] || 2500;
};

const getSDEFW = (semanas: number): number => {
  return getMedianaEFW(semanas) * 0.15;
};

const zscoreToPercentile = (zscore: number): number => {
  const t = 1 / (1 + 0.2316419 * Math.abs(zscore));
  const d = 0.3989423 * Math.exp(-zscore * zscore / 2);
  const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));

  if (zscore > 0) {
    return (1 - p) * 100;
  } else {
    return p * 100;
  }
};

const calcularPercentil = (efw: number, semanas: number): number => {
  const mediana = getMedianaEFW(semanas);
  const sd = getSDEFW(semanas);
  const zscore = (efw - mediana) / sd;
  return zscoreToPercentile(zscore);
};

// Percentiles de biometría individual (BPD, HC, AC, FL)
const calcularPercentilBiometria = (valor: number, tipo: 'bpd' | 'hc' | 'ac' | 'fl', semanas: number): number => {
  const medianas: { [key: string]: { [key: number]: number } } = {
    bpd: { 20: 47, 22: 54, 24: 61, 26: 67, 28: 73, 30: 78, 32: 83, 34: 87, 36: 90, 38: 93, 40: 95 },
    hc: { 20: 175, 22: 200, 24: 224, 26: 247, 28: 269, 30: 289, 32: 307, 34: 323, 36: 336, 38: 347, 40: 355 },
    ac: { 20: 150, 22: 175, 24: 201, 26: 227, 28: 253, 30: 279, 32: 304, 34: 327, 36: 348, 38: 366, 40: 381 },
    fl: { 20: 33, 22: 39, 24: 45, 26: 51, 28: 56, 30: 61, 32: 65, 34: 69, 36: 72, 38: 75, 40: 77 }
  };

  const semana_int = Math.round(semanas);
  const mediana = medianas[tipo][semana_int] || medianas[tipo][Math.min(...Object.keys(medianas[tipo]).reduce<number[]>((acc, k) => { const n = Number(k); if (n <= semana_int) acc.push(n); return acc; }, []))];
  const sd = mediana * 0.1;
  const zscore = (valor - mediana) / sd;

  return zscoreToPercentile(zscore);
};

const CrecimientoFetal: React.FC = () => {
  const [form] = Form.useForm();
  const [state, dispatch] = useReducer(growthReducer, initialGrowthState);
  const { resultado, historial, datosBiometria, usandoDatosEjemplo } = state;

  const calcularCrecimiento = React.useCallback((valores: DatosBiometria): ResultadoCrecimiento => {
    const efw = calcularEFW(valores);
    const percentil = calcularPercentil(efw, valores.semanas);
    const mediana = getMedianaEFW(valores.semanas);
    const sd = getSDEFW(valores.semanas);
    const zscore = (efw - mediana) / sd;

    const bpd_percentil = calcularPercentilBiometria(valores.bpd, 'bpd', valores.semanas);
    const hc_percentil = calcularPercentilBiometria(valores.hc, 'hc', valores.semanas);
    const ac_percentil = calcularPercentilBiometria(valores.ac, 'ac', valores.semanas);
    const fl_percentil = calcularPercentilBiometria(valores.fl, 'fl', valores.semanas);

    let clasificacion = '';
    let color = '';
    let interpretacion = '';
    let recomendacion = '';
    let categoria: 'RCIU' | 'PEG' | 'NORMAL' | 'GEG' | 'MACROSOMIA' = 'NORMAL';

    if (percentil < 3) {
      clasificacion = '🔴 RCIU (Restricción del Crecimiento Intrauterino)';
      color = '#f5222d';
      categoria = 'RCIU';
      interpretacion = `Peso fetal estimado <p3 (${percentil.toFixed(1)}). Restricción severa del crecimiento intrauterino. Requiere evaluación urgente.`;
      recomendacion = 'Doppler de arterias umbilical, cerebral media y ductus venoso. Evaluación del líquido amniótico. Considerar monitoreo fetal intensivo y posible interrupción según edad gestacional y hallazgos Doppler.';
    } else if (percentil < 10) {
      clasificacion = '🟠 PEG (Pequeño para Edad Gestacional)';
      color = '#fa8c16';
      categoria = 'PEG';
      interpretacion = `Peso fetal estimado entre p3-p10 (${percentil.toFixed(1)}). Pequeño para edad gestacional. Riesgo intermedio.`;
      recomendacion = 'Doppler umbilical y seguimiento semanal. Evaluar diferencial entre constitucional y patológico mediante Doppler y líquido amniótico. Controles cada 7-14 días.';
    } else if (percentil >= 10 && percentil <= 90) {
      clasificacion = '🟢 NORMAL';
      color = '#52c41a';
      categoria = 'NORMAL';
      interpretacion = `Peso fetal estimado dentro de rango normal (p${percentil.toFixed(1)}). Crecimiento adecuado para edad gestacional.`;
      recomendacion = 'Continuar con seguimiento prenatal habitual. Próxima ecografía según protocolo estándar.';
    } else if (percentil > 90 && percentil < 97) {
      clasificacion = '🟡 GEG (Grande para Edad Gestacional)';
      color = '#faad14';
      categoria = 'GEG';
      interpretacion = `Peso fetal estimado entre p90-p97 (${percentil.toFixed(1)}). Grande para edad gestacional.`;
      recomendacion = 'Descartar diabetes gestacional (curva de glucosa si no se ha realizado). Seguimiento ecográfico cada 3-4 semanas. Evaluar vía de parto según evolución y estimación de peso al término.';
    } else {
      clasificacion = '🔴 MACROSOMÍA';
      color = '#f5222d';
      categoria = 'MACROSOMIA';
      interpretacion = `Peso fetal estimado >p97 (${percentil.toFixed(1)}). Macrosomía fetal. Riesgo de complicaciones al parto.`;
      recomendacion = 'Optimizar control glucémico si diabetes gestacional. Seguimiento ecográfico cada 2-3 semanas. Discutir vía de parto (cesárea electiva si EFW >4500g o >4000g con diabetes). Prevenir distocia de hombros.';
    }

    return {
      efw,
      percentil,
      clasificacion,
      color,
      interpretacion,
      recomendacion,
      zscore,
      desviacion_estandar: sd,
      bpd_percentil,
      hc_percentil,
      ac_percentil,
      fl_percentil,
      categoria
    };
  }, []);

  const onFinish = (values: DatosBiometria) => {
    const res = calcularCrecimiento(values);

    const nuevoRegistro: RegistroCrecimiento = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      semanas: values.semanas,
      bpd: values.bpd,
      hc: values.hc,
      ac: values.ac,
      fl: values.fl
    };

    dispatch({
      type: 'CALCULATE',
      payload: { datos: values, resultado: res, registro: nuevoRegistro }
    });
  };

  const getDataBiometria = () => {
    if (!datosBiometria) return [];
    return [
      { parametro: 'BPD', valor: datosBiometria.bpd, unidad: 'mm', percentil: resultado?.bpd_percentil || 0 },
      { parametro: 'HC', valor: datosBiometria.hc, unidad: 'mm', percentil: resultado?.hc_percentil || 0 },
      { parametro: 'AC', valor: datosBiometria.ac, unidad: 'mm', percentil: resultado?.ac_percentil || 0 },
      { parametro: 'FL', valor: datosBiometria.fl, unidad: 'mm', percentil: resultado?.fl_percentil || 0 }
    ];
  };

  const getDataCurvasCrecimiento = () => {
    if (!datosBiometria) return [];
    const semanaInicio = Math.max(20, datosBiometria.semanas - 5);
    const semanaFin = Math.min(42, datosBiometria.semanas + 5);
    const curva = [];

    for (let s = semanaInicio; s <= semanaFin; s += 1) {
      const mediana = getMedianaEFW(s);
      const sd = getSDEFW(s);

      curva.push({
        semana: s,
        p3: mediana - 1.88 * sd,
        p10: mediana - 1.28 * sd,
        p50: mediana,
        p90: mediana + 1.28 * sd,
        p97: mediana + 1.88 * sd,
        actual: s === Math.round(datosBiometria.semanas) ? resultado?.efw : null
      });
    }

    return curva;
  };

  const getDataDistribucionPercentiles = () => {
    if (!resultado) return [];

    const percentiles = [
      { name: 'BPD', value: resultado.bpd_percentil },
      { name: 'HC', value: resultado.hc_percentil },
      { name: 'AC', value: resultado.ac_percentil },
      { name: 'FL', value: resultado.fl_percentil }
    ];

    return percentiles;
  };

  const getDataProporcionesFetales = () => {
    if (!datosBiometria) return [];

    // Ratios útiles clínicamente
    const hc_ac = datosBiometria.hc / datosBiometria.ac;
    const fl_ac = datosBiometria.fl / datosBiometria.ac;
    const fl_hc = datosBiometria.fl / datosBiometria.hc;

    return [
      { ratio: 'HC/AC', valor: hc_ac, normal_min: 0.95, normal_max: 1.15, color: hc_ac >= 0.95 && hc_ac <= 1.15 ? '#52c41a' : '#faad14' },
      { ratio: 'FL/AC', valor: fl_ac, normal_min: 0.20, normal_max: 0.24, color: fl_ac >= 0.20 && fl_ac <= 0.24 ? '#52c41a' : '#faad14' },
      { ratio: 'FL/HC', valor: fl_hc, normal_min: 0.18, normal_max: 0.22, color: fl_hc >= 0.18 && fl_hc <= 0.22 ? '#52c41a' : '#faad14' }
    ];
  };

  const getDataEvolucion = () => {
    return historial.slice().reverse().map((item, index) => ({
      evaluacion: `${item.semanas.toFixed(1)}s`,
      efw: item.efw,
      percentil: item.percentil,
      p50: getMedianaEFW(item.semanas)
    }));
  };

  const columnas = [
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
    { title: 'Semanas', dataIndex: 'semanas', key: 'semanas', render: (val: number) => `${val.toFixed(1)} sem` },
    { title: 'EFW (g)', dataIndex: 'efw', key: 'efw', render: (val: number) => val.toFixed(0) },
    {
      title: 'Percentil',
      dataIndex: 'percentil',
      key: 'percentil',
      render: (val: number) => {
        let color = 'green';
        if (val < 3) color = 'red';
        else if (val < 10) color = 'orange';
        else if (val > 97) color = 'red';
        else if (val > 90) color = 'gold';
        return <Tag color={color}>p{val.toFixed(1)}</Tag>;
      }
    },
    { title: 'Clasificación', dataIndex: 'clasificacion', key: 'clasificacion' },
    { title: 'BPD (mm)', dataIndex: 'bpd', key: 'bpd', render: (val: number) => val.toFixed(1) },
    { title: 'HC (mm)', dataIndex: 'hc', key: 'hc', render: (val: number) => val.toFixed(1) },
    { title: 'AC (mm)', dataIndex: 'ac', key: 'ac', render: (val: number) => val.toFixed(1) },
    { title: 'FL (mm)', dataIndex: 'fl', key: 'fl', render: (val: number) => val.toFixed(1) }
  ];

  return (
    <div className="crecimiento-fetal-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <LineChartOutlined style={{ marginRight: 8, color: '#00bcd4' }} />
          Calculadora de Crecimiento Fetal y Biometría
        </Title>
        <Text type="secondary">
          Estimación del peso fetal (EFW) con fórmulas de Hadlock y análisis de percentiles según Intergrowth-21st
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title={
            <>
              <BarChartOutlined /> Datos de Biometría Fetal
              {usandoDatosEjemplo && <Tag color="blue" style={{ marginLeft: 8 }}>Datos de Ejemplo</Tag>}
            </>
          }>
            <Form form={form} layout="vertical" onFinish={onFinish}>
              <Form.Item label="Edad Gestacional (semanas)" name="semanas" rules={[{ required: true }]} initialValue={28}>
                <InputNumber min={20} max={42} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Divider>Parámetros Biométricos</Divider>

              <Form.Item
                label="BPD - Diámetro Biparietal (mm)"
                name="bpd"
                rules={[{ required: true }]}
                initialValue={73}
                tooltip="Diámetro mayor de la cabeza fetal, medido de hueso externo a hueso interno"
              >
                <InputNumber min={20} max={120} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="HC - Circunferencia Cefálica (mm)"
                name="hc"
                rules={[{ required: true }]}
                initialValue={269}
                tooltip="Perímetro de la cabeza fetal a nivel de tálamos y cavum septum pellucidum"
              >
                <InputNumber min={100} max={450} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="AC - Circunferencia Abdominal (mm)"
                name="ac"
                rules={[{ required: true }]}
                initialValue={253}
                tooltip="Perímetro del abdomen a nivel de vena umbilical y estómago"
              >
                <InputNumber min={100} max={500} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="FL - Longitud del Fémur (mm)"
                name="fl"
                rules={[{ required: true }]}
                initialValue={56}
                tooltip="Longitud del fémur de metáfisis a metáfisis, excluyendo epífisis"
              >
                <InputNumber min={10} max={100} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="Fórmula de Hadlock"
                name="formula"
                rules={[{ required: true }]}
                initialValue="hadlock4"
                tooltip="Hadlock 4 (HC, AC, FL) es la más precisa y usada"
              >
                <Select>
                  <Option value="hadlock1">Hadlock 1 (BPD, HC, AC, FL) - Más completa</Option>
                  <Option value="hadlock2">Hadlock 2 (AC, FL) - Más simple</Option>
                  <Option value="hadlock3">Hadlock 3 (BPD, AC, FL)</Option>
                  <Option value="hadlock4">Hadlock 4 (HC, AC, FL) - Recomendada</Option>
                </Select>
              </Form.Item>

              <Form.Item style={{ marginTop: 24 }}>
                <Button type="primary" htmlType="submit" block size="large" icon={<ExperimentOutlined />}>
                  Calcular EFW y Percentiles
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          {resultado && (
            <>
              <Card title={<><SafetyOutlined /> Estadísticas del Crecimiento</>} style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="Peso Fetal Estimado"
                      value={resultado.efw}
                      precision={0}
                      suffix="g"
                      valueStyle={{ color: resultado.color, fontWeight: 'bold' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Percentil"
                      value={resultado.percentil}
                      precision={1}
                      prefix="p"
                      valueStyle={{ color: resultado.color, fontWeight: 'bold' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Z-Score"
                      value={resultado.zscore}
                      precision={2}
                      valueStyle={{ color: Math.abs(resultado.zscore) > 2 ? '#f5222d' : '#52c41a' }}
                    />
                  </Col>
                </Row>
              </Card>

              <Alert
                message={resultado.clasificacion}
                description={
                  <div>
                    <p style={{ marginBottom: 8 }}><strong>Interpretación:</strong> {resultado.interpretacion}</p>
                    <p style={{ marginBottom: 0 }}><strong>Recomendación:</strong> {resultado.recomendacion}</p>
                  </div>
                }
                type={resultado.categoria === 'NORMAL' ? 'success' : resultado.categoria === 'PEG' || resultado.categoria === 'GEG' ? 'warning' : 'error'}
                showIcon
                icon={resultado.categoria === 'NORMAL' ? <SafetyOutlined /> : <AlertOutlined />}
                style={{ marginBottom: 16 }}
              />

              <Card title="Percentiles de Parámetros Biométricos" size="small">
                <Row gutter={8}>
                  <Col span={6}>
                    <Statistic title="BPD" value={resultado.bpd_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="HC" value={resultado.hc_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="AC" value={resultado.ac_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
                  </Col>
                  <Col span={6}>
                    <Statistic title="FL" value={resultado.fl_percentil} precision={1} prefix="p" valueStyle={{ fontSize: 16 }} />
                  </Col>
                </Row>
              </Card>
            </>
          )}
        </Col>
      </Row>

      {resultado && datosBiometria && (
        <>
          <Divider>📊 Curvas de Crecimiento Fetal</Divider>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={16}>
              <Card title="Curva de Peso Fetal Estimado (EFW) - Percentiles Intergrowth-21st">
                <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
                  <ResponsiveContainer width="100%" height={350}>
                    <ComposedChart data={getDataCurvasCrecimiento()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
                      <YAxis label={{ value: 'Peso (g)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={formatPesoTooltip} />
                      <Legend />
                      <Area type="monotone" dataKey="p3" fill="#f5222d15" stroke="#f5222d" strokeWidth={1} name="p3" />
                      <Area type="monotone" dataKey="p10" fill="#fa8c1615" stroke="#fa8c16" strokeWidth={1} name="p10" />
                      <Line type="monotone" dataKey="p50" stroke="#1890ff" strokeWidth={3} name="p50 (Mediana)" dot={false} />
                      <Line type="monotone" dataKey="p90" stroke="#fa8c16" strokeWidth={1} name="p90" dot={false} />
                      <Line type="monotone" dataKey="p97" stroke="#f5222d" strokeWidth={1} name="p97" dot={false} />
                      <Line type="monotone" dataKey="actual" stroke="#52c41a" strokeWidth={4} name="EFW Actual" dot={{ r: 8, fill: '#52c41a' }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </Suspense>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p><strong>Interpretación de percentiles:</strong></p>
                  <p>• {'<'}p3: RCIU severo | p3-p10: PEG | p10-p90: Normal | p90-p97: GEG | {'>'}p97: Macrosomía</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={8}>
              <Card title="Valores Biométricos vs Percentiles">
                <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={getDataBiometria()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="parametro" />
                      <YAxis yAxisId="left" orientation="left" label={{ value: 'Valor (mm)', angle: -90, position: 'insideLeft' }} />
                      <YAxis yAxisId="right" orientation="right" label={{ value: 'Percentil', angle: 90, position: 'insideRight' }} />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="left" dataKey="valor" fill="#1890ff" name="Valor Medido (mm)" />
                      <Bar yAxisId="right" dataKey="percentil" fill="#52c41a" name="Percentil" />
                      <ReferenceLine yAxisId="right" y={50} stroke="red" strokeDasharray="3 3" label="p50" />
                    </BarChart>
                  </ResponsiveContainer>
                </Suspense>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Ratios de Proporciones Fetales">
                <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={getDataProporcionesFetales()} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={PROPORCIONES_DOMAIN} />
                      <YAxis dataKey="ratio" type="category" />
                      <Tooltip formatter={formatRatioTooltip} />
                      <Legend />
                      <Bar dataKey="valor" name="Valor Calculado">
                        {getDataProporcionesFetales().map((entry) => (
                          <Cell key={`cell-${entry.ratio}`} fill={entry.color} />
                        ))}
                      </Bar>
                      <ReferenceLine x={1.0} stroke="#666" strokeDasharray="3 3" />
                    </BarChart>
                  </ResponsiveContainer>
                </Suspense>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p><strong>HC/AC:</strong> {'>'} 1 sugiere asimetría cefálica (RCIU tipo II)</p>
                  <p><strong>FL/AC:</strong> Útil para detectar anomalías esqueléticas</p>
                  <p><strong>FL/HC:</strong> Alterado en displasias y cromosomopatías</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Distribución de Percentiles Biométricos">
                <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={getDataDistribucionPercentiles()}
                        label={renderPercentilLabel}
                        outerRadius={100}
                        dataKey="value"
                        nameKey="name"
                      >
                        {getDataDistribucionPercentiles().map((entry, index) => {
                          const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1'];
                          return <Cell key={`cell-${entry.name}`} fill={colors[index % colors.length]} />;
                        })}
                      </Pie>
                      <Tooltip formatter={formatPercentilTooltip} />
                    </PieChart>
                  </ResponsiveContainer>
                </Suspense>
              </Card>
            </Col>

            {historial.length > 1 && (
              <Col xs={24}>
                <Card title="Evolución del Crecimiento Fetal">
                  <Suspense fallback={<div style={{ textAlign: 'center', padding: 20 }}><Spin /></div>}>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={getDataEvolucion()}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="evaluacion" />
                        <YAxis yAxisId="left" label={{ value: 'EFW (g)', angle: -90, position: 'insideLeft' }} />
                        <YAxis yAxisId="right" orientation="right" label={{ value: 'Percentil', angle: 90, position: 'insideRight' }} />
                        <Tooltip />
                        <Legend />
                        <Line yAxisId="left" type="monotone" dataKey="efw" stroke="#1890ff" strokeWidth={3} name="EFW (g)" dot={{ r: 5 }} />
                        <Line yAxisId="left" type="monotone" dataKey="p50" stroke="#52c41a" strokeWidth={2} strokeDasharray="5 5" name="p50 Esperado" dot={{ r: 4 }} />
                        <Line yAxisId="right" type="monotone" dataKey="percentil" stroke="#fa8c16" strokeWidth={2} name="Percentil Actual" dot={{ r: 5 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </Suspense>
                </Card>
              </Col>
            )}
          </Row>

          <Divider>📋 Historial de Mediciones</Divider>

          <Card>
            <Table
              dataSource={historial}
              columns={columnas}
              pagination={{ pageSize: 5 }}
              rowKey={(record) => record.fecha}
              size="small"
              scroll={{ x: true }}
            />
          </Card>

          <Divider>📚 Información Clínica</Divider>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Fórmulas de Hadlock" size="small">
                <p><strong>Fórmulas de Estimación de Peso Fetal:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li><strong>Hadlock 1:</strong> Utiliza BPD, HC, AC, FL (4 parámetros) - Más completa pero requiere todas las mediciones</li>
                  <li><strong>Hadlock 2:</strong> Utiliza AC, FL (2 parámetros) - Más simple, útil cuando faltan medidas cefálicas</li>
                  <li><strong>Hadlock 3:</strong> Utiliza BPD, AC, FL (3 parámetros)</li>
                  <li><strong>Hadlock 4:</strong> Utiliza HC, AC, FL (3 parámetros) - Recomendada por ISUOG, mejor precisión</li>
                </ul>
                <p style={{ fontSize: 12, marginTop: 12 }}><strong>Precisión:</strong> ±15% del peso real en el 95% de los casos. Tiende a sobreestimar en fetos pequeños y subestimar en macrosómicos.</p>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Clasificaciones Clínicas" size="small">
                <p><strong>Categorías según Percentil:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li><strong>RCIU ({'<'}p3):</strong> Restricción del crecimiento intrauterino. Requiere Doppler y evaluación urgente.</li>
                  <li><strong>PEG (p3-p10):</strong> Pequeño para edad gestacional. Puede ser constitucional o patológico.</li>
                  <li><strong>NORMAL (p10-p90):</strong> Rango adecuado para edad gestacional.</li>
                  <li><strong>GEG (p90-p97):</strong> Grande para edad gestacional. Descartar diabetes gestacional.</li>
                  <li><strong>MACROSOMÍA ({'>'}p97):</strong> Riesgo aumentado de distocia de hombros y trauma obstétrico.</li>
                </ul>
                <p style={{ fontSize: 12, marginTop: 12 }}><strong>RCIU Tipo I:</strong> Simétrico (proporcionado) - afectación temprana</p>
                <p style={{ fontSize: 12 }}><strong>RCIU Tipo II:</strong> Asimétrico (desproporcionado) - afectación tardía, HC/AC {'>'}1</p>
              </Card>
            </Col>

            <Col xs={24}>
              <Card title="Estándares Intergrowth-21st" size="small">
                <p><strong>Proyecto Intergrowth-21st:</strong> Estudio multicéntrico de la OMS que generó estándares internacionales de crecimiento fetal basados en poblaciones sanas de 8 países.</p>
                <p style={{ fontSize: 12, marginTop: 8 }}><strong>Ventajas:</strong> Aplicables universalmente, metodología rigurosa, incluyen múltiples parámetros biométricos y peso estimado.</p>
                <p style={{ fontSize: 12 }}><strong>Uso clínico:</strong> Identificación temprana de RCIU y macrosomía, seguimiento de embarazos de alto riesgo, toma de decisiones sobre momento y vía de parto.</p>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default CrecimientoFetal;
