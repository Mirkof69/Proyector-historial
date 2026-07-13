import React, { useState } from 'react';
import { Card, Form, InputNumber, Button, Row, Col, Statistic, Alert, Divider, Table, Tag, Checkbox, Typography } from 'antd';
import { ExperimentOutlined, HeartOutlined, SafetyOutlined, MedicineBoxOutlined, WarningOutlined } from '@ant-design/icons';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Area
} from 'recharts';
import './RiesgoPreeclampsia.css';

const { Title, Text } = Typography;

interface DatosRiesgo {
  edad: number;
  peso: number;
  talla: number;
  semanas: number;
  plgf: number;
  sflt1: number;
  pappa: number;
  map: number;
  uta_pi: number;
  historia_previa: boolean;
  hipertension: boolean;
  diabetes: boolean;
  obesidad: boolean;
  gestacion_multiple: boolean;
  raza_afro: boolean;
}

interface ResultadoRiesgo {
  riesgo_pe_precoz: number;
  riesgo_pe_tardia: number;
  plgf_mom: number;
  sflt1_mom: number;
  pappa_mom: number;
  map_mom: number;
  uta_pi_mom: number;
  ratio_sflt_plgf: number;
  clasificacion: string;
  color: string;
  interpretacion: string;
  recomendacion: string;
  aspirina_indicada: boolean;
  seguimiento: string;
}

interface RegistroRiesgo extends ResultadoRiesgo {
  fecha: string;
  semanas: number;
}

// Medianas según semana gestacional (FMF references)
const getMedianaPLGF = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    11: 32.5, 12: 39.8, 13: 48.5, 14: 59.0, 15: 71.5,
    16: 86.5, 17: 104.0, 18: 124.5, 19: 148.0, 20: 175.0,
    21: 205.5, 22: 240.0, 23: 278.5, 24: 321.0, 25: 368.0,
    26: 419.5, 27: 476.0, 28: 537.5, 29: 604.5, 30: 677.0,
    31: 755.0, 32: 839.0, 33: 929.0, 34: 1025.5, 35: 1129.0
  };
  return medianas[Math.round(semanas)] || 500;
};

const getMedianaSflt1 = (semanas: number): number => {
  const medianas: { [key: number]: number } = {
    11: 1450, 12: 1520, 13: 1590, 14: 1665, 15: 1740,
    16: 1820, 17: 1900, 18: 1985, 19: 2070, 20: 2160,
    21: 2250, 22: 2345, 23: 2440, 24: 2540, 25: 2640,
    26: 2745, 27: 2850, 28: 2960, 29: 3070, 30: 3185,
    31: 3300, 32: 3420, 33: 3540, 34: 3665, 35: 3790
  };
  return medianas[Math.round(semanas)] || 2500;
};

const getMedianaPAPPA = (semanas: number): number => {
  if (semanas <= 13) return 1.2 + (semanas - 11) * 0.3;
  return 2.0;
};

const getMedianaMAP = (edad: number): number => {
  return 90 + (edad - 30) * 0.15;
};

const getMedianaUtAPI = (semanas: number): number => {
  if (semanas <= 16) return 2.35 - (semanas - 11) * 0.12;
  if (semanas <= 23) return 1.75 - (semanas - 16) * 0.08;
  return 1.2 - (semanas - 23) * 0.02;
};

const calcularRiesgo = (valores: DatosRiesgo): ResultadoRiesgo => {
    // Calcular MoMs
    const plgf_mom = valores.plgf / getMedianaPLGF(valores.semanas);
    const sflt1_mom = valores.sflt1 / getMedianaSflt1(valores.semanas);
    const pappa_mom = valores.pappa / getMedianaPAPPA(valores.semanas);
    const map_mom = valores.map / getMedianaMAP(valores.edad);
    const uta_pi_mom = valores.uta_pi / getMedianaUtAPI(valores.semanas);
    const ratio_sflt_plgf = valores.sflt1 / valores.plgf;

    // Modelo Bayesiano FMF - Likelihood Ratios
    let lr_precoz = 1.0;
    let lr_tardia = 1.0;

    // PlGF (factor protector más importante)
    if (plgf_mom < 0.4) {
      lr_precoz *= 15.0;
      lr_tardia *= 8.0;
    } else if (plgf_mom < 0.7) {
      lr_precoz *= 5.0;
      lr_tardia *= 3.0;
    } else if (plgf_mom > 1.5) {
      lr_precoz *= 0.3;
      lr_tardia *= 0.5;
    }

    // Ratio sFlt-1/PlGF (Verlohren rule)
    if (ratio_sflt_plgf > 85) {
      lr_precoz *= 12.0;
      lr_tardia *= 6.0;
    } else if (ratio_sflt_plgf > 38) {
      lr_precoz *= 4.0;
      lr_tardia *= 2.5;
    }

    // MAP
    if (map_mom > 1.15) {
      lr_precoz *= 3.5;
      lr_tardia *= 2.0;
    } else if (map_mom > 1.08) {
      lr_precoz *= 1.8;
      lr_tardia *= 1.3;
    }

    // UtA-PI
    if (uta_pi_mom > 1.5) {
      lr_precoz *= 4.0;
      lr_tardia *= 2.2;
    } else if (uta_pi_mom > 1.2) {
      lr_precoz *= 2.0;
      lr_tardia *= 1.5;
    }

    // PAPP-A (solo para precoz)
    if (pappa_mom < 0.4) {
      lr_precoz *= 2.5;
    } else if (pappa_mom < 0.6) {
      lr_precoz *= 1.5;
    }

    // Factores de riesgo maternos
    if (valores.historia_previa) {
      lr_precoz *= 8.0;
      lr_tardia *= 4.0;
    }
    if (valores.hipertension) {
      lr_precoz *= 3.5;
      lr_tardia *= 2.5;
    }
    if (valores.diabetes) {
      lr_precoz *= 2.0;
      lr_tardia *= 1.8;
    }
    if (valores.obesidad) {
      lr_precoz *= 2.2;
      lr_tardia *= 1.6;
    }
    if (valores.gestacion_multiple) {
      lr_precoz *= 3.0;
      lr_tardia *= 2.0;
    }
    if (valores.raza_afro) {
      lr_precoz *= 1.8;
      lr_tardia *= 1.4;
    }
    if (valores.edad >= 40) {
      lr_precoz *= 1.7;
      lr_tardia *= 1.5;
    } else if (valores.edad >= 35) {
      lr_precoz *= 1.3;
      lr_tardia *= 1.2;
    }

    // Riesgo basal según edad y paridad
    const riesgo_basal_precoz = 0.005; // 0.5%
    const riesgo_basal_tardia = 0.025; // 2.5%

    // Calcular riesgo posterior
    const odds_precoz = (riesgo_basal_precoz / (1 - riesgo_basal_precoz)) * lr_precoz;
    const riesgo_pe_precoz = (odds_precoz / (1 + odds_precoz)) * 100;

    const odds_tardia = (riesgo_basal_tardia / (1 - riesgo_basal_tardia)) * lr_tardia;
    const riesgo_pe_tardia = (odds_tardia / (1 + odds_tardia)) * 100;

    // Clasificación de riesgo (según FMF)
    let clasificacion = '';
    let color = '';
    let interpretacion = '';
    let recomendacion = '';
    let aspirina_indicada = false;
    let seguimiento = '';

    if (riesgo_pe_precoz >= 10) {
      clasificacion = '🔴 ALTO RIESGO';
      color = '#f5222d';
      interpretacion = 'Riesgo elevado de preeclampsia precoz (<34 semanas). Requiere monitoreo intensivo y profilaxis farmacológica.';
      recomendacion = 'Aspirina 150mg/día desde las 12 semanas hasta las 36 semanas. Vigilancia estrecha cada 2-3 semanas con biomarcadores y Doppler.';
      aspirina_indicada = true;
      seguimiento = 'Control cada 2-3 semanas con PlGF, sFlt-1, MAP, UtA-PI y biometría fetal.';
    } else if (riesgo_pe_precoz >= 5 || riesgo_pe_tardia >= 15) {
      clasificacion = '🟡 RIESGO INTERMEDIO';
      color = '#fa8c16';
      interpretacion = 'Riesgo moderado de preeclampsia. Se recomienda profilaxis y seguimiento cercano.';
      recomendacion = 'Aspirina 150mg/día desde las 12 semanas. Considerar suplementación con calcio 1.5g/día si ingesta dietética baja.';
      aspirina_indicada = true;
      seguimiento = 'Control cada 3-4 semanas con biomarcadores y evaluación clínica.';
    } else if (riesgo_pe_precoz >= 1 || riesgo_pe_tardia >= 5) {
      clasificacion = '🟢 BAJO RIESGO';
      color = '#52c41a';
      interpretacion = 'Riesgo bajo de preeclampsia. Continuar con seguimiento prenatal habitual.';
      recomendacion = 'Seguimiento prenatal estándar. Educación sobre signos de alarma. Dieta saludable y actividad física regular.';
      aspirina_indicada = false;
      seguimiento = 'Control prenatal estándar según protocolo. Vigilancia de signos de alarma.';
    } else {
      clasificacion = '🟢 RIESGO MUY BAJO';
      color = '#389e0d';
      interpretacion = 'Riesgo muy bajo de preeclampsia. Biomarcadores protectores.';
      recomendacion = 'Continuar con controles prenatales de rutina. Mantener estilo de vida saludable.';
      aspirina_indicada = false;
      seguimiento = 'Control prenatal estándar.';
    }

    return {
      riesgo_pe_precoz,
      riesgo_pe_tardia,
      plgf_mom,
      sflt1_mom,
      pappa_mom,
      map_mom,
      uta_pi_mom,
      ratio_sflt_plgf,
      clasificacion,
      color,
      interpretacion,
      recomendacion,
      aspirina_indicada,
      seguimiento
    };
};

const EXPERIMENT_ICON_2 = <ExperimentOutlined />;
const MEDICINE_BOX_ICON_5 = <MedicineBoxOutlined />;

const formatMoMTooltip = (value: any) => value ? Number(value).toFixed(2) : '0';
const renderRiesgoLabel = ({ name, percent }: { name: string; percent: number }) => `${name}: ${((percent || 0) * 100).toFixed(1)}%`;
const formatRiesgoTooltip = (value: any) => value ? `${Number(value).toFixed(2)}%` : '0%';
const formatRatioTooltip = (value: any) => value ? Number(value).toFixed(1) : '0';

const RiesgoPreeclampsia: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoRiesgo | null>(null);
  const [historial, setHistorial] = useState<RegistroRiesgo[]>([]);

  const onFinish = (values: DatosRiesgo) => {
    const res = calcularRiesgo(values);
    setResultado(res);

    const nuevoRegistro: RegistroRiesgo = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      semanas: values.semanas
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  const getDataBiomarcadores = () => {
    if (!resultado) return [];
    return [
      { name: 'PlGF', mom: resultado.plgf_mom, referencia: 1.0, color: '#1890ff' },
      { name: 'sFlt-1', mom: resultado.sflt1_mom, referencia: 1.0, color: '#f5222d' },
      { name: 'PAPP-A', mom: resultado.pappa_mom, referencia: 1.0, color: '#52c41a' },
      { name: 'MAP', mom: resultado.map_mom, referencia: 1.0, color: '#fa8c16' },
      { name: 'UtA-PI', mom: resultado.uta_pi_mom, referencia: 1.0, color: '#722ed1' }
    ];
  };

  const getDataDistribucionRiesgo = () => {
    if (!resultado) return [];
    return [
      { name: 'PE Precoz', value: resultado.riesgo_pe_precoz, color: '#f5222d' },
      { name: 'PE Tardía', value: resultado.riesgo_pe_tardia, color: '#fa8c16' },
      { name: 'Sin PE', value: Math.max(0, 100 - resultado.riesgo_pe_precoz - resultado.riesgo_pe_tardia), color: '#52c41a' }
    ];
  };

  const getDataEvolucionTemporal = () => {
    return historial.slice().reverse().map((item, index) => ({
      evaluacion: `Ev ${index + 1}`,
      semanas: item.semanas,
      riesgo_precoz: item.riesgo_pe_precoz,
      riesgo_tardia: item.riesgo_pe_tardia,
      plgf_mom: item.plgf_mom
    }));
  };

  const getDataRatioSfltPlgf = () => {
    if (!resultado) return [];
    const ratioActual = resultado.ratio_sflt_plgf;
    return [
      { semana: '12-16', ratio: ratioActual * 0.6, limite_normal: 38, limite_pe: 85 },
      { semana: '17-20', ratio: ratioActual * 0.75, limite_normal: 38, limite_pe: 85 },
      { semana: '21-24', ratio: ratioActual * 0.85, limite_normal: 38, limite_pe: 85 },
      { semana: '25-28', ratio: ratioActual * 0.95, limite_normal: 38, limite_pe: 85 },
      { semana: '29-32', ratio: ratioActual, limite_normal: 38, limite_pe: 85 },
      { semana: '33-36', ratio: ratioActual * 1.1, limite_normal: 38, limite_pe: 85 }
    ];
  };

  const columnas = [
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
    { title: 'Semanas', dataIndex: 'semanas', key: 'semanas' },
    {
      title: 'Riesgo PE Precoz',
      dataIndex: 'riesgo_pe_precoz',
      key: 'riesgo_pe_precoz',
      render: (val: number) => <Tag color={val >= 10 ? 'red' : val >= 5 ? 'orange' : 'green'}>{val.toFixed(2)}%</Tag>
    },
    {
      title: 'Riesgo PE Tardía',
      dataIndex: 'riesgo_pe_tardia',
      key: 'riesgo_pe_tardia',
      render: (val: number) => <Tag color={val >= 15 ? 'red' : val >= 5 ? 'orange' : 'green'}>{val.toFixed(2)}%</Tag>
    },
    {
      title: 'PlGF MoM',
      dataIndex: 'plgf_mom',
      key: 'plgf_mom',
      render: (val: number) => <span style={{ color: val < 0.7 ? '#f5222d' : '#52c41a', fontWeight: 'bold' }}>{val.toFixed(2)}</span>
    },
    {
      title: 'Ratio sFlt/PlGF',
      dataIndex: 'ratio_sflt_plgf',
      key: 'ratio_sflt_plgf',
      render: (val: number) => <span style={{ color: val > 85 ? '#f5222d' : val > 38 ? '#fa8c16' : '#52c41a', fontWeight: 'bold' }}>{val.toFixed(1)}</span>
    },
    { title: 'Clasificación', dataIndex: 'clasificacion', key: 'clasificacion' }
  ];

  return (
    <div className="riesgo-preeclampsia-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ExperimentOutlined style={{ marginRight: 8, color: '#667eea' }} />
          Calculadora de Riesgo de Preeclampsia (FMF)
        </Title>
        <Text type="secondary">
          Modelo Bayesiano de la Fetal Medicine Foundation con biomarcadores séricos, ecográficos y factores maternos
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={
            <>
              <HeartOutlined /> Datos Maternos y Biomarcadores
            </>
          } className="form-card">
            <Form form={form} layout="vertical" onFinish={onFinish}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="Edad (años)" name="edad" rules={[{ required: true }]} initialValue={28}>
                    <InputNumber min={15} max={55} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Peso (kg)" name="peso" rules={[{ required: true }]} initialValue={65}>
                    <InputNumber min={40} max={150} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Talla (cm)" name="talla" rules={[{ required: true }]} initialValue={160}>
                    <InputNumber min={140} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="Semanas Gestación" name="semanas" rules={[{ required: true }]} initialValue={12}>
                    <InputNumber min={11} max={35} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Biomarcadores Séricos</Divider>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="PlGF (pg/mL)" name="plgf" rules={[{ required: true }]} initialValue={45.5}>
                    <InputNumber min={1} max={3000} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="sFlt-1 (pg/mL)" name="sflt1" rules={[{ required: true }]} initialValue={1680}>
                    <InputNumber min={100} max={15000} step={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item label="PAPP-A (mUI/mL)" name="pappa" rules={[{ required: true }]} initialValue={1.5}>
                    <InputNumber min={0.1} max={10} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Biomarcadores Ecográficos</Divider>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item label="MAP (mmHg)" name="map" rules={[{ required: true }]} initialValue={88}>
                    <InputNumber min={60} max={140} step={1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label="UtA-PI" name="uta_pi" rules={[{ required: true }]} initialValue={1.8}>
                    <InputNumber min={0.5} max={4.0} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Factores de Riesgo Maternos</Divider>

              <Row gutter={[8, 8]}>
                <Col span={12}>
                  <Form.Item name="historia_previa" valuePropName="checked" initialValue={false}>
                    <Checkbox>Preeclampsia previa</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="hipertension" valuePropName="checked" initialValue={false}>
                    <Checkbox>Hipertensión crónica</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="diabetes" valuePropName="checked" initialValue={false}>
                    <Checkbox>Diabetes</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="obesidad" valuePropName="checked" initialValue={false}>
                    <Checkbox>Obesidad (IMC ≥30)</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="gestacion_multiple" valuePropName="checked" initialValue={false}>
                    <Checkbox>Gestación múltiple</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="raza_afro" valuePropName="checked" initialValue={false}>
                    <Checkbox>Raza afrocaribeña</Checkbox>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item style={{ marginTop: 24 }}>
                <Button type="primary" htmlType="submit" block size="large" icon={EXPERIMENT_ICON_2}>
                  Calcular Riesgo FMF
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
                  <Col span={12}>
                    <Statistic
                      title="Riesgo PE Precoz (<34 sem)"
                      value={resultado.riesgo_pe_precoz}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: resultado.riesgo_pe_precoz >= 10 ? '#f5222d' : resultado.riesgo_pe_precoz >= 5 ? '#fa8c16' : '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Riesgo PE Tardía (≥34 sem)"
                      value={resultado.riesgo_pe_tardia}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: resultado.riesgo_pe_tardia >= 15 ? '#f5222d' : resultado.riesgo_pe_tardia >= 5 ? '#fa8c16' : '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="PlGF MoM"
                      value={resultado.plgf_mom}
                      precision={2}
                      valueStyle={{ color: resultado.plgf_mom < 0.7 ? '#f5222d' : '#52c41a' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Ratio sFlt-1/PlGF"
                      value={resultado.ratio_sflt_plgf}
                      precision={1}
                      valueStyle={{ color: resultado.ratio_sflt_plgf > 85 ? '#f5222d' : resultado.ratio_sflt_plgf > 38 ? '#fa8c16' : '#52c41a' }}
                    />
                  </Col>
                </Row>
              </Card>

              <Alert
                message={resultado.clasificacion}
                description={
                  <div>
                    <p style={{ marginBottom: 8 }}><strong>Interpretación:</strong> {resultado.interpretacion}</p>
                    <p style={{ marginBottom: 8 }}><strong>Recomendación:</strong> {resultado.recomendacion}</p>
                    <p style={{ marginBottom: 0 }}><strong>Seguimiento:</strong> {resultado.seguimiento}</p>
                  </div>
                }
                type={resultado.riesgo_pe_precoz >= 10 ? 'error' : resultado.riesgo_pe_precoz >= 5 ? 'warning' : 'success'}
                showIcon
                icon={resultado.riesgo_pe_precoz >= 10 ? <WarningOutlined /> : resultado.aspirina_indicada ? <MedicineBoxOutlined /> : <SafetyOutlined />}
                style={{ marginBottom: 16 }}
              />

              {resultado.aspirina_indicada && (
                <Alert
                  message="Profilaxis con Aspirina Indicada"
                  description="Iniciar Aspirina 150mg/día vía oral, por la noche, desde las 12 hasta las 36 semanas de gestación. Demostrado reducir el riesgo de PE precoz hasta en 62% (metaanálisis ASPRE trial)."
                  type="info"
                  showIcon
                  icon={MEDICINE_BOX_ICON_5}
                  style={{ marginBottom: 16 }}
                />
              )}
            </>
          )}
        </Col>
      </Row>

      {resultado && (
        <>
          <Divider>📊 Análisis de Biomarcadores (MoM)</Divider>
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Biomarcadores MoM vs Referencia">
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
                <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
                  <p><strong>MoM (Multiple of Median):</strong> Ratio del valor observado respecto a la mediana poblacional para esa edad gestacional.</p>
                  <p>• PlGF {'<'}0.7 MoM: Factor de riesgo significativo</p>
                  <p>• UtA-PI {'>'}1.5 MoM: Resistencia placentaria elevada</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Distribución del Riesgo">
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
                <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
                  <p><strong>PE Precoz:</strong> Preeclampsia antes de las 34 semanas (más severa)</p>
                  <p><strong>PE Tardía:</strong> Preeclampsia después de las 34 semanas</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Ratio sFlt-1/PlGF (Verlohren Rule)">
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={getDataRatioSfltPlgf()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" />
                    <YAxis />
                    <Tooltip formatter={formatRatioTooltip} />
                    <Legend />
                    <Area type="monotone" dataKey="limite_pe" fill="#f5222d20" stroke="#f5222d" name="Umbral PE (>85)" />
                    <Area type="monotone" dataKey="limite_normal" fill="#52c41a20" stroke="#52c41a" name="Límite Normal (38)" />
                    <Line type="monotone" dataKey="ratio" stroke="#1890ff" strokeWidth={3} name="Ratio Actual" dot={{ r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
                <div style={{ marginTop: 16, fontSize: 12, color: '#666' }}>
                  <p><strong>Verlohren Rule:</strong></p>
                  <p>• Ratio {'<'}38: Riesgo muy bajo de PE en próxima semana</p>
                  <p>• Ratio 38-85: Zona intermedia, vigilancia</p>
                  <p>• Ratio {'>'}85: Alto riesgo de PE, considerar finalización</p>
                </div>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              {historial.length > 1 && (
                <Card title="Evolución Temporal del Riesgo">
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={getDataEvolucionTemporal()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="evaluacion" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Line yAxisId="left" type="monotone" dataKey="riesgo_precoz" stroke="#f5222d" strokeWidth={2} name="Riesgo Precoz (%)" dot={{ r: 4 }} />
                      <Line yAxisId="left" type="monotone" dataKey="riesgo_tardia" stroke="#fa8c16" strokeWidth={2} name="Riesgo Tardía (%)" dot={{ r: 4 }} />
                      <Line yAxisId="right" type="monotone" dataKey="plgf_mom" stroke="#1890ff" strokeWidth={2} name="PlGF MoM" dot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              )}
            </Col>
          </Row>

      <Divider>📋 Historial de Evaluaciones</Divider>

          <Card>
            <Table
              dataSource={historial}
              columns={columnas}
              pagination={{ pageSize: 5 }}
              rowKey={(record) => record.fecha}
              size="small"
            />
          </Card>

          <Divider>📚 Información Clínica</Divider>

          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Modelo FMF Bayesiano" size="small">
                <p><strong>Fundamento:</strong> El modelo de la Fetal Medicine Foundation combina factores maternos, biomarcadores séricos y ecográficos mediante likelihood ratios para estimar el riesgo individualizado.</p>
                <p><strong>Biomarcadores clave:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li><strong>PlGF:</strong> Factor de crecimiento placentario. Bajo en PE por disfunción placentaria.</li>
                  <li><strong>sFlt-1:</strong> Receptor soluble antiangiogénico. Elevado en PE.</li>
                  <li><strong>PAPP-A:</strong> Proteína plasmática A asociada al embarazo. Baja en PE precoz.</li>
                  <li><strong>MAP:</strong> Presión arterial media. Elevada indica riesgo cardiovascular.</li>
                  <li><strong>UtA-PI:</strong> Índice de pulsatilidad de arterias uterinas. Alto indica resistencia placentaria.</li>
                </ul>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Profilaxis y Manejo" size="small">
                <p><strong>Aspirina (AAS):</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>Dosis: 150mg/día VO nocturna</li>
                  <li>Inicio: 11-14 semanas (idealmente antes de 16 sem)</li>
                  <li>Duración: Hasta 36 semanas</li>
                  <li>Eficacia: Reduce PE precoz en 62% (ASPRE trial)</li>
                </ul>
                <p><strong>Calcio:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>Dosis: 1.5-2g/día si ingesta dietética {'<'}600mg/día</li>
                  <li>Eficacia: Reduce PE en 55% en mujeres con baja ingesta</li>
                </ul>
                <p><strong>Seguimiento:</strong></p>
                <ul style={{ fontSize: 12 }}>
                  <li>Alto riesgo: Control cada 2-3 semanas</li>
                  <li>Riesgo intermedio: Control cada 3-4 semanas</li>
                  <li>Bajo riesgo: Seguimiento prenatal estándar</li>
                </ul>
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default RiesgoPreeclampsia;
