import React, { useReducer, useCallback } from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Divider, Table, Tag, Checkbox, Typography } from 'antd';
import { ExperimentOutlined, WarningOutlined, SafetyOutlined, LineChartOutlined } from '@ant-design/icons';
import './RiesgoCromosomico.css';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Area
} from 'recharts';

const { Title, Text } = Typography;

// ==========================================================================
// REDUCER FOR SCREENING STATE (replaces cascading setState)
// ==========================================================================
interface ScreeningState {
  resultado: ResultadoRiesgo | null;
  historial: RegistroScreening[];
  usandoDatosEjemplo: boolean;
}

type ScreeningAction =
  | { type: 'INIT_WITH_EXAMPLE'; payload: { resultado: ResultadoRiesgo; historial: RegistroScreening[] } }
  | { type: 'CALCULATE'; payload: { resultado: ResultadoRiesgo; registro: RegistroScreening } };

function screeningReducer(state: ScreeningState, action: ScreeningAction): ScreeningState {
  switch (action.type) {
    case 'INIT_WITH_EXAMPLE':
      return {
        resultado: action.payload.resultado,
        historial: action.payload.historial,
        usandoDatosEjemplo: true,
      };
    case 'CALCULATE':
      return {
        resultado: action.payload.resultado,
        historial: [action.payload.registro, ...state.historial],
        usandoDatosEjemplo: false,
      };
    default:
      return state;
  }
}

const initialScreeningState: ScreeningState = {
  resultado: null,
  historial: [],
  usandoDatosEjemplo: true,
};

interface DatosScreening {
  edad: number;
  semanas: number;
  nt: number;
  pappa: number;
  bhcg_libre: number;
  historia_t21: boolean;
  hallazgos_eco: boolean;
}

interface ResultadoRiesgo {
  riesgo_t21: number;
  riesgo_t18: number;
  riesgo_t13: number;
  nt_mom: number;
  pappa_mom: number;
  bhcg_mom: number;
  riesgo_edad_t21: number;
  lr_t21: number;
  lr_t18: number;
  lr_t13: number;
  clasificacion_t21: string;
  clasificacion_t18: string;
  clasificacion_t13: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  screening_positivo: boolean;
}

interface RegistroScreening extends ResultadoRiesgo {
  fecha: string;
  edad: number;
  semanas: number;
}

const formatMoMTooltip = (value: any) => value ? Number(value).toFixed(2) : '0';
const renderRiesgoLabel = (props: any) => {
  const { name, riesgoStr } = props;
  return riesgoStr ? `${name}: ${riesgoStr}` : name;
};
const formatRiesgoTooltip = (value: any) => value ? `${Number(value).toFixed(4)}%` : '0%';
const formatLRTooltip = (value: any) => value ? `LR: ${Number(value).toFixed(2)}` : '';

const RiesgoCromosomico: React.FC = () => {
  const [form] = Form.useForm();
  const [state, dispatch] = useReducer(screeningReducer, initialScreeningState);
  const { resultado, historial, usandoDatosEjemplo } = state;

  const initExampleData = useCallback(() => {
    const datosEjemplo: DatosScreening = {
      edad: 32,
      semanas: 12.5,
      nt: 1.8,
      pappa: 1.5,
      bhcg_libre: 40,
      historia_t21: false,
      hallazgos_eco: false
    };

    const resultadoEjemplo = calcularRiesgo(datosEjemplo);

    const historialEjemplo: RegistroScreening[] = [
      {
        ...resultadoEjemplo,
        fecha: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toLocaleString('es-ES'),
        edad: 32,
        semanas: 12.5
      },
      {
        riesgo_t21: 0.0012,
        riesgo_t18: 0.00015,
        riesgo_t13: 0.00008,
        nt_mom: 0.95,
        pappa_mom: 1.45,
        bhcg_mom: 1.02,
        riesgo_edad_t21: 1 / 720,
        lr_t21: 0.85,
        lr_t18: 0.6,
        lr_t13: 0.4,
        clasificacion_t21: '🟢 BAJO RIESGO',
        clasificacion_t18: '🟢 BAJO RIESGO',
        clasificacion_t13: '🟢 BAJO RIESGO',
        color: '#52c41a',
        interpretacion: 'Screening NEGATIVO. Riesgo bajo de aneuploidías.',
        recomendacion: 'Continuar con seguimiento prenatal habitual.',
        screening_positivo: false,
        fecha: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toLocaleString('es-ES'),
        edad: 32,
        semanas: 12
      }
    ];

    dispatch({
      type: 'INIT_WITH_EXAMPLE',
      payload: { resultado: resultadoEjemplo, historial: historialEjemplo }
    });
  }, []);

  React.useEffect(() => {
    initExampleData();
  }, [initExampleData]);

  // Riesgo basal por edad materna (T21)
  const getRiesgoEdad = (edad: number): number => {
    const riesgos: { [key: number]: number } = {
      20: 1 / 1500, 21: 1 / 1450, 22: 1 / 1400, 23: 1 / 1350, 24: 1 / 1300,
      25: 1 / 1250, 26: 1 / 1200, 27: 1 / 1150, 28: 1 / 1100, 29: 1 / 1050,
      30: 1 / 900, 31: 1 / 800, 32: 1 / 720, 33: 1 / 600, 34: 1 / 450,
      35: 1 / 350, 36: 1 / 280, 37: 1 / 210, 38: 1 / 170, 39: 1 / 130,
      40: 1 / 100, 41: 1 / 80, 42: 1 / 60, 43: 1 / 50, 44: 1 / 40, 45: 1 / 30
    };
    return riesgos[Math.round(edad)] || (edad < 25 ? 1 / 1500 : 1 / 30);
  };

  // Medianas de NT según semanas (FMF)
  const getMedianaNT = (semanas: number): number => {
    const medianas: { [key: number]: number } = {
      11.0: 1.6, 11.5: 1.7, 12.0: 1.8, 12.5: 1.9,
      13.0: 2.0, 13.5: 2.1, 14.0: 2.2
    };
    const sem = Math.round(semanas * 2) / 2; // Redondear a 0.5
    return medianas[sem] || 1.8;
  };

  // Medianas de PAPP-A según semanas
  const getMedianaPAPPA = (semanas: number): number => {
    if (semanas <= 10) return 0.8;
    if (semanas <= 11) return 1.0;
    if (semanas <= 12) return 1.3;
    if (semanas <= 13) return 1.7;
    return 2.0;
  };

  // Medianas de βhCG libre según semanas
  const getMedianaBHCG = (semanas: number): number => {
    if (semanas <= 10) return 50;
    if (semanas <= 11) return 45;
    if (semanas <= 12) return 40;
    if (semanas <= 13) return 35;
    return 30;
  };

  const calcularMoM = (valor: number, mediana: number): number => {
    return valor / mediana;
  };

  const calcularRiesgo = (valores: DatosScreening): ResultadoRiesgo => {
    // Calcular MoMs
    const nt_mom = calcularMoM(valores.nt, getMedianaNT(valores.semanas));
    const pappa_mom = calcularMoM(valores.pappa, getMedianaPAPPA(valores.semanas));
    const bhcg_mom = calcularMoM(valores.bhcg_libre, getMedianaBHCG(valores.semanas));

    // Riesgo basal por edad
    const riesgo_edad_t21 = getRiesgoEdad(valores.edad);

    // Likelihood Ratios (LR) basados en FMF para T21
    let lr_t21 = 1.0;

    // NT (factor más importante)
    if (nt_mom > 2.5) {
      lr_t21 *= 25.0;
    } else if (nt_mom > 2.0) {
      lr_t21 *= 10.0;
    } else if (nt_mom > 1.5) {
      lr_t21 *= 3.5;
    } else if (nt_mom > 1.2) {
      lr_t21 *= 1.5;
    } else if (nt_mom < 0.8) {
      lr_t21 *= 0.3;
    }

    // PAPP-A (bajo es factor de riesgo)
    if (pappa_mom < 0.25) {
      lr_t21 *= 5.0;
    } else if (pappa_mom < 0.5) {
      lr_t21 *= 2.5;
    } else if (pappa_mom < 0.75) {
      lr_t21 *= 1.5;
    } else if (pappa_mom > 1.5) {
      lr_t21 *= 0.6;
    }

    // βhCG libre (alto es factor de riesgo)
    if (bhcg_mom > 2.5) {
      lr_t21 *= 3.5;
    } else if (bhcg_mom > 2.0) {
      lr_t21 *= 2.0;
    } else if (bhcg_mom < 0.5) {
      lr_t21 *= 0.7;
    }

    // Historia previa de T21
    if (valores.historia_t21) {
      lr_t21 *= 3.0;
    }

    // Hallazgos ecográficos adicionales
    if (valores.hallazgos_eco) {
      lr_t21 *= 5.0;
    }

    // Calcular riesgo posterior para T21
    const odds_t21 = riesgo_edad_t21 / (1 - riesgo_edad_t21) * lr_t21;
    const riesgo_t21 = odds_t21 / (1 + odds_t21);

    // Likelihood Ratios para T18
    let lr_t18 = 1.0;

    if (nt_mom > 2.0) lr_t18 *= 15.0;
    else if (nt_mom > 1.5) lr_t18 *= 5.0;

    // En T18: PAPP-A y βhCG AMBOS bajos
    if (pappa_mom < 0.5 && bhcg_mom < 0.5) {
      lr_t18 *= 10.0;
    } else if (pappa_mom < 0.5) {
      lr_t18 *= 3.0;
    }
    if (bhcg_mom < 0.25) {
      lr_t18 *= 2.0;
    }

    if (valores.hallazgos_eco) lr_t18 *= 8.0;

    const riesgo_basal_t18 = 1 / 6000;
    const odds_t18 = riesgo_basal_t18 / (1 - riesgo_basal_t18) * lr_t18;
    const riesgo_t18 = odds_t18 / (1 + odds_t18);

    // Likelihood Ratios para T13
    let lr_t13 = 1.0;

    if (nt_mom > 2.0) lr_t13 *= 12.0;
    else if (nt_mom > 1.5) lr_t13 *= 4.0;

    if (pappa_mom < 0.5) lr_t13 *= 2.5;
    if (valores.hallazgos_eco) lr_t13 *= 10.0;

    const riesgo_basal_t13 = 1 / 10000;
    const odds_t13 = riesgo_basal_t13 / (1 - riesgo_basal_t13) * lr_t13;
    const riesgo_t13 = odds_t13 / (1 + odds_t13);

    // Clasificación de riesgo (punto de corte 1:250)
    const punto_corte = 1 / 250;

    let clasificacion_t21 = '';
    let clasificacion_t18 = '';
    let clasificacion_t13 = '';
    let color = '';
    let interpretacion = '';
    let recomendacion = '';
    let screening_positivo = false;

    // Clasificar T21
    if (riesgo_t21 >= punto_corte) {
      clasificacion_t21 = '🔴 ALTO RIESGO';
      color = '#f5222d';
      screening_positivo = true;
    } else if (riesgo_t21 >= 1 / 1000) {
      clasificacion_t21 = '🟡 RIESGO INTERMEDIO';
      color = '#fa8c16';
    } else {
      clasificacion_t21 = '🟢 BAJO RIESGO';
      color = '#52c41a';
    }

    // Clasificar T18
    if (riesgo_t18 >= 1 / 250) {
      clasificacion_t18 = '🔴 ALTO RIESGO';
      screening_positivo = true;
    } else if (riesgo_t18 >= 1 / 1000) {
      clasificacion_t18 = '🟡 RIESGO INTERMEDIO';
    } else {
      clasificacion_t18 = '🟢 BAJO RIESGO';
    }

    // Clasificar T13
    if (riesgo_t13 >= 1 / 250) {
      clasificacion_t13 = '🔴 ALTO RIESGO';
      screening_positivo = true;
    } else if (riesgo_t13 >= 1 / 1000) {
      clasificacion_t13 = '🟡 RIESGO INTERMEDIO';
    } else {
      clasificacion_t13 = '🟢 BAJO RIESGO';
    }

    // Interpretación global
    if (screening_positivo) {
      interpretacion = `Screening POSITIVO (riesgo ≥1:250). Riesgo elevado de aneuploidía. Se requiere consejo genético y oferta de prueba diagnóstica invasiva.`;
      recomendacion = 'Oferta de estudio genético invasivo (amniocentesis o biopsia corial). Consejo genético especializado. Alternativa: NIPT (Test Prenatal No Invasivo) como segundo screening. Evaluación ecográfica detallada del segundo trimestre.';
    } else if (riesgo_t21 >= 1 / 1000 || riesgo_t18 >= 1 / 1000 || riesgo_t13 >= 1 / 1000) {
      interpretacion = `Screening NEGATIVO pero con riesgo intermedio (1:250-1:1000). Considerar pruebas adicionales.`;
      recomendacion = 'Considerar NIPT (Test Prenatal No Invasivo) como seguimiento. Ecografía detallada a las 18-22 semanas. Seguimiento estrecho. Consejo genético si persisten dudas.';
    } else {
      interpretacion = `Screening NEGATIVO (riesgo <1:1000). Riesgo bajo de aneuploidías con el screening actual.`;
      recomendacion = 'Continuar con seguimiento prenatal habitual. Ecografía morfológica a las 18-22 semanas. Recordar que ningún screening es 100% sensible.';
    }

    return {
      riesgo_t21,
      riesgo_t18,
      riesgo_t13,
      nt_mom,
      pappa_mom,
      bhcg_mom,
      riesgo_edad_t21,
      lr_t21,
      lr_t18,
      lr_t13,
      clasificacion_t21,
      clasificacion_t18,
      clasificacion_t13,
      color,
      interpretacion,
      recomendacion,
      screening_positivo
    };
  };

  const onFinish = (values: DatosScreening) => {
    const res = calcularRiesgo(values);

    const nuevoRegistro: RegistroScreening = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      edad: values.edad,
      semanas: values.semanas
    };

    dispatch({
      type: 'CALCULATE',
      payload: { resultado: res, registro: nuevoRegistro }
    });
  };

  const formatRiesgo = (riesgo: number): string => {
    if (riesgo === 0) return '1:>100,000';
    const denominador = Math.round(1 / riesgo);
    return `1:${denominador.toLocaleString()}`;
  };

  const getDataBiomarcadores = () => {
    if (!resultado) return [];
    return [
      { name: 'NT', mom: resultado.nt_mom, referencia: 1.0, color: '#1890ff' },
      { name: 'PAPP-A', mom: resultado.pappa_mom, referencia: 1.0, color: '#52c41a' },
      { name: 'βhCG libre', mom: resultado.bhcg_mom, referencia: 1.0, color: '#fa8c16' }
    ];
  };

  const getDataDistribucionRiesgo = () => {
    if (!resultado) return [];
    return [
      { name: 'T21 (Down)', value: resultado.riesgo_t21 * 100, color: '#f5222d', riesgoStr: formatRiesgo(resultado.riesgo_t21) },
      { name: 'T18 (Edwards)', value: resultado.riesgo_t18 * 100, color: '#fa8c16', riesgoStr: formatRiesgo(resultado.riesgo_t18) },
      { name: 'T13 (Patau)', value: resultado.riesgo_t13 * 100, color: '#722ed1', riesgoStr: formatRiesgo(resultado.riesgo_t13) },
      { name: 'Normal', value: Math.max(0, 100 - (resultado.riesgo_t21 + resultado.riesgo_t18 + resultado.riesgo_t13) * 100), color: '#52c41a', riesgoStr: '' }
    ];
  };

  const getDataLikelihoodRatios = () => {
    if (!resultado) return [];
    return [
      { aneuplodia: 'T21', lr: resultado.lr_t21, color: '#1890ff' },
      { aneuplodia: 'T18', lr: resultado.lr_t18, color: '#fa8c16' },
      { aneuplodia: 'T13', lr: resultado.lr_t13, color: '#722ed1' }
    ];
  };

  const getDataEdadVsRiesgo = () => {
    const curva = [];
    for (let edad = 20; edad <= 45; edad += 1) {
      const riesgo = getRiesgoEdad(edad);
      curva.push({
        edad,
        riesgo_basal: riesgo * 100,
        punto_corte: (1 / 250) * 100
      });
    }
    return curva;
  };

  const getDataEvolucion = () => {
    return historial.slice().reverse().map((item, index) => ({
      evaluacion: `${item.edad}a-${item.semanas.toFixed(1)}s`,
      riesgo_t21_pct: item.riesgo_t21 * 100,
      riesgo_t18_pct: item.riesgo_t18 * 100,
      riesgo_t13_pct: item.riesgo_t13 * 100
    }));
  };

  const columnas = [
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
    { title: 'Edad', dataIndex: 'edad', key: 'edad', render: (val: number) => `${val} años` },
    { title: 'Semanas', dataIndex: 'semanas', key: 'semanas', render: (val: number) => `${val.toFixed(1)} sem` },
    {
      title: 'Riesgo T21',
      dataIndex: 'riesgo_t21',
      key: 'riesgo_t21',
      render: (val: number) => {
        const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
        return <Tag color={color}>{formatRiesgo(val)}</Tag>;
      }
    },
    {
      title: 'Riesgo T18',
      dataIndex: 'riesgo_t18',
      key: 'riesgo_t18',
      render: (val: number) => {
        const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
        return <Tag color={color}>{formatRiesgo(val)}</Tag>;
      }
    },
    {
      title: 'Riesgo T13',
      dataIndex: 'riesgo_t13',
      key: 'riesgo_t13',
      render: (val: number) => {
        const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
        return <Tag color={color}>{formatRiesgo(val)}</Tag>;
      }
    },
    { title: 'NT MoM', dataIndex: 'nt_mom', key: 'nt_mom', render: (val: number) => val.toFixed(2) },
    { title: 'Clasificación', dataIndex: 'clasificacion_t21', key: 'clasificacion_t21' }
  ];

  return (
    <div className="riesgo-cromosomico-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ExperimentOutlined style={{ marginRight: 8, color: '#722ed1' }} />
          Screening de Aneuploidías - Primer Trimestre (FMF)
        </Title>
        <Text type="secondary">
          Cálculo de riesgo combinado para T21 (Down), T18 (Edwards) y T13 (Patau) con NT, PAPP-A y βhCG libre
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={
            <>
              <LineChartOutlined /> Datos Maternos y Biomarcadores
              {usandoDatosEjemplo && <Tag color="blue" style={{ marginLeft: 8 }}>Datos de Ejemplo</Tag>}
            </>
          }>
            <Form form={form} layout="vertical" onFinish={onFinish}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Edad Materna (años)" name="edad" rules={[{ required: true }]} initialValue={32}>
                    <InputNumber min={15} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Semanas Gestación" name="semanas" rules={[{ required: true }]} initialValue={12.5} tooltip="11+0 a 13+6 semanas">
                    <InputNumber min={11} max={14} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Biomarcadores Ecográficos</Divider>

              <Form.Item
                label="NT - Translucencia Nucal (mm)"
                name="nt"
                rules={[{ required: true }]}
                initialValue={2.2}
                tooltip="Medida del espacio translúcido en región nucal fetal, 11-13+6 semanas"
              >
                <InputNumber min={0.5} max={8.0} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Divider>Biomarcadores Séricos</Divider>

              <Form.Item
                label="PAPP-A (mUI/mL)"
                name="pappa"
                rules={[{ required: true }]}
                initialValue={1.2}
                tooltip="Proteína plasmática A asociada al embarazo"
              >
                <InputNumber min={0.1} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="βhCG libre (ng/mL)"
                name="bhcg_libre"
                rules={[{ required: true }]}
                initialValue={42}
                tooltip="Subunidad beta libre de gonadotropina coriónica humana"
              >
                <InputNumber min={1} max={200} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Divider>Factores de Riesgo Adicionales</Divider>

              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <Form.Item name="historia_t21" valuePropName="checked" initialValue={false}>
                    <Checkbox>Historia previa de T21</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="hallazgos_eco" valuePropName="checked" initialValue={false}>
                    <Checkbox>Hallazgos ecográficos sospechosos</Checkbox>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item style={{ marginTop: 24 }}>
                <Button type="primary" htmlType="submit" block size="large" icon={<ExperimentOutlined />}>
                  Calcular Riesgo Combinado
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          {resultado && (
            <>
              <Card title={<><SafetyOutlined /> Estadísticas del Riesgo</>} style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="Riesgo T21 (Down)"
                      value={formatRiesgo(resultado.riesgo_t21)}
                      valueStyle={{ color: resultado.riesgo_t21 >= 1 / 250 ? '#f5222d' : resultado.riesgo_t21 >= 1 / 1000 ? '#fa8c16' : '#52c41a', fontSize: 18, fontWeight: 'bold' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Riesgo T18 (Edwards)"
                      value={formatRiesgo(resultado.riesgo_t18)}
                      valueStyle={{ color: resultado.riesgo_t18 >= 1 / 250 ? '#f5222d' : resultado.riesgo_t18 >= 1 / 1000 ? '#fa8c16' : '#52c41a', fontSize: 18, fontWeight: 'bold' }}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="Riesgo T13 (Patau)"
                      value={formatRiesgo(resultado.riesgo_t13)}
                      valueStyle={{ color: resultado.riesgo_t13 >= 1 / 250 ? '#f5222d' : resultado.riesgo_t13 >= 1 / 1000 ? '#fa8c16' : '#52c41a', fontSize: 18, fontWeight: 'bold' }}
                    />
                  </Col>
                </Row>
                <Divider style={{ margin: '12px 0' }} />
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic title="NT MoM" value={resultado.nt_mom} precision={2} valueStyle={{ fontSize: 16 }} />
                  </Col>
                  <Col span={8}>
                    <Statistic title="PAPP-A MoM" value={resultado.pappa_mom} precision={2} valueStyle={{ fontSize: 16 }} />
                  </Col>
                  <Col span={8}>
                    <Statistic title="βhCG MoM" value={resultado.bhcg_mom} precision={2} valueStyle={{ fontSize: 16 }} />
                  </Col>
                </Row>
              </Card>

              <Alert
                message={resultado.screening_positivo ? 'SCREENING POSITIVO' : 'SCREENING NEGATIVO'}
                description={
                  <div>
                    <p style={{ marginBottom: 8 }}><strong>T21:</strong> {resultado.clasificacion_t21}</p>
                    <p style={{ marginBottom: 8 }}><strong>T18:</strong> {resultado.clasificacion_t18}</p>
                    <p style={{ marginBottom: 8 }}><strong>T13:</strong> {resultado.clasificacion_t13}</p>
                    <p style={{ marginBottom: 8 }}><strong>Interpretación:</strong> {resultado.interpretacion}</p>
                    <p style={{ marginBottom: 0 }}><strong>Recomendación:</strong> {resultado.recomendacion}</p>
                  </div>
                }
                type={resultado.screening_positivo ? 'error' : 'success'}
                showIcon
                icon={resultado.screening_positivo ? <WarningOutlined /> : <SafetyOutlined />}
                style={{ marginBottom: 16 }}
              />
            </>
          )}
        </Col>
      </Row>

      {resultado && (
        <>
          <Divider>📊 Análisis de Biomarcadores y Riesgo</Divider>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Biomarcadores MoM (Múltiplos de la Mediana)">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getDataBiomarcadores()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip formatter={formatMoMTooltip} />
                    <Legend />
                    <Bar dataKey="referencia" fill="#8884d8" name="Referencia (MoM=1.0)" />
                    <Bar dataKey="mom" fill="#82ca9d" name="MoM Actual">
                      {getDataBiomarcadores().map((entry) => (
                        <Cell key={`cell-${entry.name}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p><strong>NT elevado (MoM {'>'}2.0):</strong> Aumenta riesgo de aneuploidías</p>
                  <p><strong>PAPP-A bajo (MoM {'<'}0.5):</strong> Marcador de riesgo para T21</p>
                  <p><strong>βhCG alto (MoM {'>'}2.0):</strong> Asociado a T21</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Distribución del Riesgo de Aneuploidías">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getDataDistribucionRiesgo()}
                      label={renderRiesgoLabel}
                      outerRadius={100}
                      dataKey="value"
                    >
                      {getDataDistribucionRiesgo().map((entry) => (
                        <Cell key={`cell-${entry.name}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={formatRiesgoTooltip} />
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p><strong>Punto de corte screening:</strong> 1:250 (0.4%)</p>
                  <p><strong>Riesgo intermedio:</strong> 1:250 - 1:1000</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Likelihood Ratios (LR) por Aneuploidía">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getDataLikelihoodRatios()} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="aneuplodia" type="category" />
                    <Tooltip formatter={formatLRTooltip} />
                    <Legend />
                    <Bar dataKey="lr" name="Likelihood Ratio">
                      {getDataLikelihoodRatios().map((entry) => (
                        <Cell key={`cell-${entry.aneuplodia}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p><strong>LR {'>'} 10:</strong> Fuerte incremento del riesgo</p>
                  <p><strong>LR 1-10:</strong> Incremento moderado</p>
                  <p><strong>LR {'<'} 1:</strong> Disminución del riesgo</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Riesgo Basal por Edad Materna (T21)">
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={getDataEdadVsRiesgo()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="edad" label={{ value: 'Edad Materna (años)', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'Riesgo (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip formatter={formatRiesgoTooltip} />
                    <Legend />
                    <Area type="monotone" dataKey="riesgo_basal" fill="#1890ff20" stroke="#1890ff" strokeWidth={3} name="Riesgo Edad" />
                    <Line type="monotone" dataKey="punto_corte" stroke="#f5222d" strokeWidth={2} strokeDasharray="5 5" name="Punto Corte (1:250)" dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 12, fontSize: 12, color: '#666' }}>
                  <p>El riesgo aumenta exponencialmente con la edad, especialmente después de los 35 años.</p>
                </div>
              </Card>
            </Col>

            {historial.length > 1 && (
              <Col xs={24}>
                <Card title="Evolución del Riesgo en Evaluaciones Sucesivas">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={getDataEvolucion()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="evaluacion" />
                      <YAxis label={{ value: 'Riesgo (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip formatter={formatRiesgoTooltip} />
                      <Legend />
                      <Line type="monotone" dataKey="riesgo_t21_pct" stroke="#f5222d" strokeWidth={2} name="T21" dot={{ r: 5 }} />
                      <Line type="monotone" dataKey="riesgo_t18_pct" stroke="#fa8c16" strokeWidth={2} name="T18" dot={{ r: 5 }} />
                      <Line type="monotone" dataKey="riesgo_t13_pct" stroke="#722ed1" strokeWidth={2} name="T13" dot={{ r: 5 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            )}
          </Row>

          <Divider>📋 Historial de Screenings</Divider>

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
              <Card title="Screening Combinado Primer Trimestre" size="small">
                <p><strong>Fundamento:</strong> Combina edad materna, NT ecográfico y biomarcadores séricos (PAPP-A y βhCG libre) mediante modelo Bayesiano (Fetal Medicine Foundation).</p>
                <p style={{ fontSize: 12, marginTop: 8 }}><strong>Ventana temporal:</strong> 11+0 a 13+6 semanas de gestación</p>
                <p style={{ fontSize: 12 }}><strong>Sensibilidad:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>T21: 90-95% (tasa de falsos positivos 5%)</li>
                  <li>T18/T13: 85-90%</li>
                </ul>
                <p style={{ fontSize: 12 }}><strong>Punto de corte:</strong> 1:250 al término (screening positivo)</p>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Aneuploidías Principales" size="small">
                <p><strong>Trisomía 21 (Síndrome de Down):</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>NT elevado, PAPP-A bajo, βhCG alto</li>
                  <li>Incidencia: 1:700 nacimientos (varía con edad materna)</li>
                  <li>Compatible con vida, discapacidad intelectual variable</li>
                </ul>
                <p style={{ fontSize: 12, marginTop: 8 }}><strong>Trisomía 18 (Síndrome de Edwards):</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>NT elevado, PAPP-A bajo, βhCG bajo</li>
                  <li>Incidencia: 1:6000</li>
                  <li>Pronóstico grave, alta mortalidad perinatal</li>
                </ul>
                <p style={{ fontSize: 12, marginTop: 8 }}><strong>Trisomía 13 (Síndrome de Patau):</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>NT elevado, biomarcadores variables</li>
                  <li>Incidencia: 1:10000</li>
                  <li>Pronóstico grave, alta mortalidad perinatal</li>
                </ul>
              </Card>
            </Col>

            <Col xs={24}>
              <Card title="Manejo según Resultado" size="small">
                <Row gutter={16}>
                  <Col span={8}>
                    <p><strong>Screening POSITIVO (≥1:250):</strong></p>
                    <ul style={{ fontSize: 12 }}>
                      <li>Consejo genético</li>
                      <li>Oferta de estudio invasivo (amniocentesis/biopsia corial)</li>
                      <li>Alternativa: NIPT como segunda línea</li>
                      <li>Ecografía detallada 18-22 semanas</li>
                    </ul>
                  </Col>
                  <Col span={8}>
                    <p><strong>Riesgo INTERMEDIO (1:250-1:1000):</strong></p>
                    <ul style={{ fontSize: 12 }}>
                      <li>Considerar NIPT</li>
                      <li>Ecografía detallada</li>
                      <li>Consejo genético optativo</li>
                      <li>Seguimiento estrecho</li>
                    </ul>
                  </Col>
                  <Col span={8}>
                    <p><strong>Screening NEGATIVO ({'<'}1:1000):</strong></p>
                    <ul style={{ fontSize: 12 }}>
                      <li>Seguimiento habitual</li>
                      <li>Ecografía morfológica 18-22 semanas</li>
                      <li>Recordar: No excluye 100% aneuploidía</li>
                    </ul>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default RiesgoCromosomico;
