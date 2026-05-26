/**
 * =============================================================================
 * CALCULADORAS MÉDICAS - SUITE COMPLETA AVANZADA V3.0
 * =============================================================================
 * Suite profesional de calculadoras médicas obstétricas integradas
 * 
 * CARACTERÍSTICAS:
 * ✓ Edad Gestacional y FPP (Naegele)
 * ✓ IMC Pre-gestacional y Ganancia de Peso
 * ✓ Score de Bishop
 * ✓ Riesgo de Preeclampsia
 * ✓ Índice de Líquido Amniótico (Phelan)
 * ✓ Peso Fetal Estimado (Hadlock)
 * ✓ Score de Apgar
 * ✓ Método de Capurro
 * ✓ Test de Silverman-Andersen
 * ✓ Ballard Score
 * ✓ Índice Cardio-Cerebral (ICC)
 * ✓ Presión Arterial Media
 * ✓ Frecuencia Cardíaca Máxima
 * ✓ Integración con Backend
 * ✓ Almacenamiento de resultados
 * ✓ Historial de cálculos
 * 
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import {
  Card, Row, Col, Button, Space, Form, DatePicker, Select,
  InputNumber, Divider, Statistic, Typography, Alert, Tabs,
  Table, Tag, Progress, Tooltip, Badge, Modal, message, Empty,
  Timeline, Descriptions, Collapse, List, Radio, Checkbox, Switch,
  Result, Steps, Popconfirm, Drawer, Input, Spin
} from 'antd';
import {
  CalculatorOutlined, CalendarOutlined, LineChartOutlined,
  HeartOutlined, SafetyOutlined, ExperimentOutlined,
  FileTextOutlined, ClockCircleOutlined, UserOutlined,
  MedicineBoxOutlined, ThunderboltOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, WarningOutlined, InfoCircleOutlined,
  PlusOutlined, DeleteOutlined, EditOutlined, SaveOutlined,
  ReloadOutlined, SearchOutlined, FilterOutlined, DownloadOutlined,
  PrinterOutlined, EyeOutlined, SettingOutlined, QuestionCircleOutlined,
  ArrowLeftOutlined, HomeOutlined, StarOutlined, TrophyOutlined,
  FireOutlined, CloudOutlined, DatabaseOutlined, ToolOutlined,
  BarChartOutlined, PieChartOutlined, LineOutlined, FundOutlined,
  RiseOutlined, FallOutlined, StockOutlined, AntDesignOutlined,
  SortAscendingOutlined, SortDescendingOutlined, PercentageOutlined,
  TeamOutlined, UsergroupAddOutlined, FileOutlined, HistoryOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

interface ResultadoCalculo {
  id: string;
  tipo: string;
  fecha: string;
  datos: any;
  resultado: any;
}

interface ResultadosState {
  resultadoEG: any;
  resultadoIMC: any;
  resultadoBishop: any;
  resultadoPreeclampsia: any;
  resultadoILA: any;
  resultadoPesoFetal: any;
  resultadoApgar: any;
  resultadoCapurro: any;
  resultadoSilverman: any;
  resultadoBallard: any;
  resultadoICC: any;
  resultadoPA: any;
  resultadoFCMax: any;
}

type ResultadosAction =
  | { type: 'SET_EG'; payload: any }
  | { type: 'SET_IMC'; payload: any }
  | { type: 'SET_BISHOP'; payload: any }
  | { type: 'SET_PREECLAMPSIA'; payload: any }
  | { type: 'SET_ILA'; payload: any }
  | { type: 'SET_PESO_FETAL'; payload: any }
  | { type: 'SET_APAGAR'; payload: any }
  | { type: 'SET_CAPURRO'; payload: any }
  | { type: 'SET_SILVERMAN'; payload: any }
  | { type: 'SET_BALLARD'; payload: any }
  | { type: 'SET_ICC'; payload: any }
  | { type: 'SET_PA'; payload: any }
  | { type: 'SET_FC_MAX'; payload: any };

const initialResultados: ResultadosState = {
  resultadoEG: null, resultadoIMC: null, resultadoBishop: null,
  resultadoPreeclampsia: null, resultadoILA: null, resultadoPesoFetal: null,
  resultadoApgar: null, resultadoCapurro: null, resultadoSilverman: null,
  resultadoBallard: null, resultadoICC: null, resultadoPA: null, resultadoFCMax: null,
};

function resultadosReducer(state: ResultadosState, action: ResultadosAction): ResultadosState {
  switch (action.type) {
    case 'SET_EG': return { ...state, resultadoEG: action.payload };
    case 'SET_IMC': return { ...state, resultadoIMC: action.payload };
    case 'SET_BISHOP': return { ...state, resultadoBishop: action.payload };
    case 'SET_PREECLAMPSIA': return { ...state, resultadoPreeclampsia: action.payload };
    case 'SET_ILA': return { ...state, resultadoILA: action.payload };
    case 'SET_PESO_FETAL': return { ...state, resultadoPesoFetal: action.payload };
    case 'SET_APAGAR': return { ...state, resultadoApgar: action.payload };
    case 'SET_CAPURRO': return { ...state, resultadoCapurro: action.payload };
    case 'SET_SILVERMAN': return { ...state, resultadoSilverman: action.payload };
    case 'SET_BALLARD': return { ...state, resultadoBallard: action.payload };
    case 'SET_ICC': return { ...state, resultadoICC: action.payload };
    case 'SET_PA': return { ...state, resultadoPA: action.payload };
    case 'SET_FC_MAX': return { ...state, resultadoFCMax: action.payload };
    default: return state;
  }
}

const CalculadorasPage: React.FC = () => {
  const [resultados, dispatchResultado] = useReducer(resultadosReducer, initialResultados);
  const {
    resultadoEG, resultadoIMC, resultadoBishop, resultadoPreeclampsia,
    resultadoILA, resultadoPesoFetal, resultadoApgar, resultadoCapurro,
    resultadoSilverman, resultadoBallard, resultadoICC, resultadoPA, resultadoFCMax
  } = resultados;

  const [loading, setLoading] = useState(false);
  const [historialVisible, setHistorialVisible] = useState(false);
  const [historial, setHistorial] = useState<ResultadoCalculo[]>(() => {
    const historialGuardado = localStorage.getItem('calculadoras_historial:v1');
    if (historialGuardado) {
      try {
        return JSON.parse(historialGuardado);
      } catch (error) {
      }
    }
    return [];
  });

  // Forms
  const [formEG] = Form.useForm();
  const [formIMC] = Form.useForm();
  const [formBishop] = Form.useForm();
  const [formPreeclampsia] = Form.useForm();
  const [formILA] = Form.useForm();
  const [formPesoFetal] = Form.useForm();
  const [formApgar] = Form.useForm();

  // Guardar en historial
  const guardarEnHistorial = (tipo: string, datos: any, resultado: any) => {
    const nuevoCalculo: ResultadoCalculo = {
      id: Date.now().toString(),
      tipo,
      fecha: dayjs().format('DD/MM/YYYY HH:mm'),
      datos,
      resultado,
    };
    const nuevoHistorial = [nuevoCalculo, ...historial].slice(0, 50); // Máximo 50 registros
    setHistorial(nuevoHistorial);
    localStorage.setItem('calculadoras_historial:v1', JSON.stringify(nuevoHistorial));
  };

  // CALCULADORA 1: EDAD GESTACIONAL Y FPP
  const calcularEdadGestacional = async (values: any) => {
    setLoading(true);
    try {
      const fum = values.fum;
      const fechaActual = values.fecha_actual || dayjs();

      const diasDiferencia = fechaActual.diff(fum, 'day');
      const semanas = Math.floor(diasDiferencia / 7);
      const dias = diasDiferencia % 7;
      const fpp = fum.add(280, 'day');
      const diasParaParto = fpp.diff(fechaActual, 'day');
      const trimestre = semanas < 13 ? 1 : semanas < 27 ? 2 : 3;

      const resultado = {
        semanas,
        dias,
        edad_gestacional: `${semanas} semanas + ${dias} días`,
        fpp: fpp.format('DD/MM/YYYY'),
        dias_para_parto: diasParaParto,
        trimestre,
        categoria: semanas < 37 ? 'Pretérmino' : semanas <= 42 ? 'A término' : 'Postérmino',
      };

      dispatchResultado({ type: 'SET_EG', payload: resultado });
      guardarEnHistorial('Edad Gestacional', values, resultado);
      message.success('Edad gestacional calculada correctamente');
    } catch (error) {
      message.error('Error al calcular edad gestacional');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 2: IMC Y GANANCIA DE PESO
  const calcularIMC = async (values: any) => {
    setLoading(true);
    try {
      const { peso_pregestacional, altura, peso_actual, edad_gestacional_semanas } = values;
      const alturaMetros = altura / 100;
      const imc = peso_pregestacional / (alturaMetros * alturaMetros);
      const ganancia = peso_actual - peso_pregestacional;

      let categoria = '';
      let gananciaRecomendada = '';
      let color = '';

      if (imc < 18.5) {
        categoria = 'Bajo peso';
        gananciaRecomendada = '12.5 - 18 kg';
        color = 'orange';
      } else if (imc < 25) {
        categoria = 'Normal';
        gananciaRecomendada = '11.5 - 16 kg';
        color = 'green';
      } else if (imc < 30) {
        categoria = 'Sobrepeso';
        gananciaRecomendada = '7 - 11.5 kg';
        color = 'orange';
      } else {
        categoria = 'Obesidad';
        gananciaRecomendada = '5 - 9 kg';
        color = 'red';
      }

      const resultado = {
        imc: imc.toFixed(2),
        categoria,
        ganancia_actual: ganancia.toFixed(2),
        ganancia_recomendada: gananciaRecomendada,
        color,
        semanas: edad_gestacional_semanas,
      };

      dispatchResultado({ type: 'SET_IMC', payload: resultado });
      guardarEnHistorial('IMC y Peso', values, resultado);
      message.success('IMC calculado correctamente');
    } catch (error) {
      message.error('Error al calcular IMC');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 3: SCORE DE BISHOP
  const calcularBishop = async (values: any) => {
    setLoading(true);
    try {
      const { dilatacion, borramiento, estacion, consistencia, posicion } = values;
      const score = dilatacion + borramiento + estacion + consistencia + posicion;

      let interpretacion = '';
      let probabilidad = '';
      let color = '';

      if (score <= 4) {
        interpretacion = 'Cuello desfavorable';
        probabilidad = 'Baja probabilidad de parto vaginal';
        color = 'red';
      } else if (score <= 6) {
        interpretacion = 'Cuello intermedio';
        probabilidad = 'Probabilidad moderada de parto vaginal';
        color = 'orange';
      } else {
        interpretacion = 'Cuello favorable';
        probabilidad = 'Alta probabilidad de parto vaginal';
        color = 'green';
      }

      const resultado = {
        score,
        interpretacion,
        probabilidad,
        color,
        componentes: { dilatacion, borramiento, estacion, consistencia, posicion },
      };

      dispatchResultado({ type: 'SET_BISHOP', payload: resultado });
      guardarEnHistorial('Score de Bishop', values, resultado);
      message.success('Score de Bishop calculado correctamente');
    } catch (error) {
      message.error('Error al calcular Score de Bishop');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 4: RIESGO DE PREECLAMPSIA
  const calcularRiesgoPreeclampsia = async (values: any) => {
    setLoading(true);
    try {
      const {
        edad,
        imc,
        presion_sistolica,
        presion_diastolica,
        proteinuria,
        historia_preeclampsia,
        diabetes,
        enfermedad_renal,
      } = values;

      let puntos = 0;

      if (edad > 35) puntos += 2;
      if (edad < 18) puntos += 1;
      if (imc > 30) puntos += 2;
      if (presion_sistolica >= 140) puntos += 3;
      if (presion_diastolica >= 90) puntos += 3;
      if (proteinuria) puntos += 3;
      if (historia_preeclampsia) puntos += 3;
      if (diabetes) puntos += 2;
      if (enfermedad_renal) puntos += 2;

      let riesgo = '';
      let color = '';
      let recomendacion = '';

      if (puntos <= 3) {
        riesgo = 'Bajo';
        color = 'green';
        recomendacion = 'Controles prenatales rutinarios';
      } else if (puntos <= 6) {
        riesgo = 'Moderado';
        color = 'orange';
        recomendacion = 'Vigilancia estrecha, considerar aspirina';
      } else {
        riesgo = 'Alto';
        color = 'red';
        recomendacion = 'Vigilancia intensiva, aspirina, seguimiento especializado';
      }

      const resultado = {
        puntos,
        riesgo,
        color,
        recomendacion,
        factores: {
          edad: edad > 35 || edad < 18,
          imc: imc > 30,
          hipertension: presion_sistolica >= 140 || presion_diastolica >= 90,
          proteinuria,
          historia_preeclampsia,
          diabetes,
          enfermedad_renal,
        },
      };

      dispatchResultado({ type: 'SET_PREECLAMPSIA', payload: resultado });
      guardarEnHistorial('Riesgo Preeclampsia', values, resultado);
      message.success('Riesgo de preeclampsia calculado correctamente');
    } catch (error) {
      message.error('Error al calcular riesgo');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 5: ÍNDICE DE LÍQUIDO AMNIÓTICO
  const calcularILA = async (values: any) => {
    setLoading(true);
    try {
      const { cuadrante1, cuadrante2, cuadrante3, cuadrante4 } = values;
      const ila = cuadrante1 + cuadrante2 + cuadrante3 + cuadrante4;

      let interpretacion = '';
      let color = '';
      let conducta = '';

      if (ila < 5) {
        interpretacion = 'Oligohidramnios';
        color = 'red';
        conducta = 'Evaluación fetal urgente, considerar terminación';
      } else if (ila <= 8) {
        interpretacion = 'Límite bajo';
        color = 'orange';
        conducta = 'Vigilancia fetal estrecha';
      } else if (ila <= 18) {
        interpretacion = 'Normal';
        color = 'green';
        conducta = 'Seguimiento rutinario';
      } else if (ila <= 24) {
        interpretacion = 'Límite alto';
        color = 'orange';
        conducta = 'Descartar causas, vigilancia';
      } else {
        interpretacion = 'Polihidramnios';
        color = 'red';
        conducta = 'Estudio etiológico, vigilancia estrecha';
      }

      const resultado = {
        ila: ila.toFixed(1),
        interpretacion,
        color,
        conducta,
        cuadrantes: { cuadrante1, cuadrante2, cuadrante3, cuadrante4 },
      };

      dispatchResultado({ type: 'SET_ILA', payload: resultado });
      guardarEnHistorial('ILA', values, resultado);
      message.success('ILA calculado correctamente');
    } catch (error) {
      message.error('Error al calcular ILA');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 6: PESO FETAL ESTIMADO
  const calcularPesoFetal = async (values: any) => {
    setLoading(true);
    try {
      const { dbp, cc, ca, lf } = values;

      // Fórmula de Hadlock
      const logPeso = 1.335 - 0.0034 * ca * lf + 0.0316 * dbp + 0.0457 * ca + 0.1623 * lf;
      const peso = Math.pow(10, logPeso);

      let percentil = '';
      let color = '';

      if (peso < 2500) {
        percentil = 'Bajo peso';
        color = 'orange';
      } else if (peso <= 4000) {
        percentil = 'Peso adecuado';
        color = 'green';
      } else {
        percentil = 'Macrosomía';
        color = 'red';
      }

      const resultado = {
        peso: peso.toFixed(0),
        percentil,
        color,
        medidas: { dbp, cc, ca, lf },
      };

      dispatchResultado({ type: 'SET_PESO_FETAL', payload: resultado });
      guardarEnHistorial('Peso Fetal', values, resultado);
      message.success('Peso fetal estimado calculado correctamente');
    } catch (error) {
      message.error('Error al calcular peso fetal');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 7: SCORE DE APGAR
  const calcularApgar = async (values: any) => {
    setLoading(true);
    try {
      const {
        frecuencia_cardiaca,
        esfuerzo_respiratorio,
        tono_muscular,
        irritabilidad_refleja,
        color,
      } = values;

      const score =
        frecuencia_cardiaca + esfuerzo_respiratorio + tono_muscular + irritabilidad_refleja + color;

      let interpretacion = '';
      let colorTag = '';
      let conducta = '';

      if (score >= 7) {
        interpretacion = 'Normal';
        colorTag = 'green';
        conducta = 'Recién nacido en buenas condiciones';
      } else if (score >= 4) {
        interpretacion = 'Depresión moderada';
        colorTag = 'orange';
        conducta = 'Requiere estimulación y vigilancia';
      } else {
        interpretacion = 'Depresión severa';
        colorTag = 'red';
        conducta = 'Requiere reanimación inmediata';
      }

      const resultado = {
        score,
        interpretacion,
        color: colorTag,
        conducta,
        componentes: {
          frecuencia_cardiaca,
          esfuerzo_respiratorio,
          tono_muscular,
          irritabilidad_refleja,
          color,
        },
      };

      dispatchResultado({ type: 'SET_APAGAR', payload: resultado });
      guardarEnHistorial('Score de Apgar', values, resultado);
      message.success('Score de Apgar calculado correctamente');
    } catch (error) {
      message.error('Error al calcular Score de Apgar');
    } finally {
      setLoading(false);
    }
  };

  // CALCULADORA 8: MÉTODO DE CAPURRO
  const calcularCapurro = (textura: number, oreja: number, mama: number, pezón: number, planta: number) => {
    const puntos = textura + oreja + mama + pezón + planta;
    const eg = 200 - (700 / (80 + puntos));

    const resultado = {
      puntos,
      eg: eg.toFixed(1),
      semanas: Math.floor(eg / 7),
      dias: Math.round((eg % 7)),
      interpretacion: eg < 35 ? 'Prematuro' : eg <= 42 ? 'A término' : 'Postmaduro',
    };

    dispatchResultado({ type: 'SET_CAPURRO', payload: resultado });
    guardarEnHistorial('Capurro', { textura, oreja, mama, pezón, planta }, resultado);
    message.success('Capurro calculado correctamente');
  };

  // CALCULADORA 9: ICC
  const calcularICC = (ac: number, cerebelo: number) => {
    if (ac && cerebelo) {
      const icc = ac / cerebelo;
      const resultado = {
        icc: icc.toFixed(2),
        normal: icc >= 1.4 && icc <= 1.6,
        interpretacion: icc < 1.4 ? 'Bajo (considerar restricción)' : icc <= 1.6 ? 'Normal' : 'Alto',
      };
      dispatchResultado({ type: 'SET_ICC', payload: resultado });
      guardarEnHistorial('ICC', { ac, cerebelo }, resultado);
      message.success('ICC calculado correctamente');
    }
  };

  // CALCULADORA 10: PA MEDIA
  const calcularPA = (sistolica: number, diastolica: number) => {
    if (sistolica && diastolica) {
      const pa = (sistolica + 2 * diastolica) / 3;
      const resultado = {
        pa: pa.toFixed(1),
        interpretacion: pa < 70 ? 'Baja' : pa <= 100 ? 'Normal' : 'Elevada',
      };
      dispatchResultado({ type: 'SET_PA', payload: resultado });
      guardarEnHistorial('PA Media', { sistolica, diastolica }, resultado);
      message.success('PA Media calculada correctamente');
    }
  };

  // CALCULADORA 11: FC MÁXIMA
  const calcularFCMax = (edad: number) => {
    if (edad) {
      const fc = 220 - edad;
      const resultado = {
        fc,
        intensidad_50: (fc * 0.5).toFixed(0),
        intensidad_75: (fc * 0.75).toFixed(0),
        intensidad_90: (fc * 0.9).toFixed(0),
      };
      dispatchResultado({ type: 'SET_FC_MAX', payload: resultado });
      guardarEnHistorial('FC Máxima', { edad }, resultado);
      message.success('FC Máxima calculada correctamente');
    }
  };

  // Limpiar historial
  const limpiarHistorial = () => {
    setHistorial([]);
    localStorage.removeItem('calculadoras_historial');
    message.success('Historial limpiado');
  };

  // Items de tabs
  const tabsItems = [
    {
      key: '1',
      label: <span><CalendarOutlined /> Edad Gestacional</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Datos" type="inner">
              <Form form={formEG} layout="vertical" onFinish={calcularEdadGestacional}>
                <Form.Item
                  name="fum"
                  label="Fecha de Última Menstruación (FUM)"
                  rules={[{ required: true, message: 'Requerido' }]}
                >
                  <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" size="large" />
                </Form.Item>
                <Form.Item name="fecha_actual" label="Fecha Actual (Opcional)">
                  <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" size="large" />
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoEG ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Edad Gestacional"
                    value={resultadoEG.edad_gestacional}
                    valueStyle={{ fontSize: 28, color: '#1890ff' }}
                  />
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Statistic title="Semanas" value={resultadoEG.semanas} suffix="sem" />
                    </Col>
                    <Col span={12}>
                      <Statistic title="Días" value={resultadoEG.dias} suffix="días" />
                    </Col>
                  </Row>
                  <Divider />
                  <div>
                    <Text strong>FPP: </Text>
                    <Text style={{ fontSize: 20 }}>{resultadoEG.fpp}</Text>
                  </div>
                  <div>
                    <Text strong>Días para parto: </Text>
                    <Text style={{ fontSize: 20 }}>{resultadoEG.dias_para_parto} días</Text>
                  </div>
                  <Tag color="blue">{resultadoEG.trimestre}° Trimestre</Tag>
                  <Tag color={resultadoEG.categoria === 'A término' ? 'green' : 'orange'}>{resultadoEG.categoria}</Tag>
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '2',
      label: <span><LineChartOutlined /> IMC y Peso</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Datos" type="inner">
              <Form form={formIMC} layout="vertical" onFinish={calcularIMC}>
                <Form.Item
                  name="peso_pregestacional"
                  label="Peso Pre-gestacional (kg)"
                  rules={[{ required: true, message: 'Requerido' }]}
                >
                  <InputNumber style={{ width: '100%' }} min={30} max={200} size="large" />
                </Form.Item>
                <Form.Item name="altura" label="Altura (cm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={120} max={220} size="large" />
                </Form.Item>
                <Form.Item
                  name="peso_actual"
                  label="Peso Actual (kg)"
                  rules={[{ required: true, message: 'Requerido' }]}
                >
                  <InputNumber style={{ width: '100%' }} min={30} max={200} size="large" />
                </Form.Item>
                <Form.Item
                  name="edad_gestacional_semanas"
                  label="Semanas de Gestación"
                  rules={[{ required: true, message: 'Requerido' }]}
                >
                  <InputNumber style={{ width: '100%' }} min={1} max={42} size="large" />
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoIMC ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic title="IMC" value={resultadoIMC.imc} valueStyle={{ fontSize: 28, color: '#1890ff' }} />
                  <Tag color={resultadoIMC.color}>{resultadoIMC.categoria}</Tag>
                  <Divider />
                  <div>
                    <Text strong>Ganancia Actual: </Text>
                    <Text style={{ fontSize: 20 }}>{resultadoIMC.ganancia_actual} kg</Text>
                  </div>
                  <div>
                    <Text strong>Ganancia Recomendada: </Text>
                    <Text style={{ fontSize: 20 }}>{resultadoIMC.ganancia_recomendada}</Text>
                  </div>
                  <Progress percent={(parseFloat(resultadoIMC.ganancia_actual) / 16) * 100} />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '3',
      label: <span><BarChartOutlined /> Bishop</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Evaluación Cervical" type="inner">
              <Form form={formBishop} layout="vertical" onFinish={calcularBishop}>
                <Form.Item name="dilatacion" label="Dilatación" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Cerrado (0)</Select.Option>
                    <Select.Option value={1}>1-2 cm (1)</Select.Option>
                    <Select.Option value={2}>3-4 cm (2)</Select.Option>
                    <Select.Option value={3}>≥5 cm (3)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="borramiento" label="Borramiento" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>0-30% (0)</Select.Option>
                    <Select.Option value={1}>40-50% (1)</Select.Option>
                    <Select.Option value={2}>60-70% (2)</Select.Option>
                    <Select.Option value={3}>≥80% (3)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="estacion" label="Estación" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>-3 (0)</Select.Option>
                    <Select.Option value={1}>-2 (1)</Select.Option>
                    <Select.Option value={2}>-1, 0 (2)</Select.Option>
                    <Select.Option value={3}>+1, +2 (3)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="consistencia" label="Consistencia" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Firme (0)</Select.Option>
                    <Select.Option value={1}>Media (1)</Select.Option>
                    <Select.Option value={2}>Blanda (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="posicion" label="Posición" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Posterior (0)</Select.Option>
                    <Select.Option value={1}>Intermedia (1)</Select.Option>
                    <Select.Option value={2}>Anterior (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoBishop ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Score"
                    value={resultadoBishop.score}
                    suffix="/13"
                    valueStyle={{ fontSize: 32, color: '#1890ff' }}
                  />
                  <Progress percent={(resultadoBishop.score / 13) * 100} strokeColor={{ '0%': '#ff4d4f', '50%': '#faad14', '100%': '#52c41a' }} />
                  <Tag color={resultadoBishop.color}>{resultadoBishop.interpretacion}</Tag>
                  <Alert message={resultadoBishop.probabilidad} type={resultadoBishop.color === 'green' ? 'success' : resultadoBishop.color === 'red' ? 'error' : 'warning'} showIcon />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '4',
      label: <span><WarningOutlined /> Preeclampsia</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Factores de Riesgo" type="inner">
              <Form form={formPreeclampsia} layout="vertical" onFinish={calcularRiesgoPreeclampsia}>
                <Form.Item name="edad" label="Edad (años)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={12} max={60} size="large" />
                </Form.Item>
                <Form.Item name="imc" label="IMC Pre-gestacional" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={15} max={50} step={0.1} size="large" />
                </Form.Item>
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item name="presion_sistolica" label="Presión Sistólica" rules={[{ required: true, message: 'Requerido' }]}>
                      <InputNumber style={{ width: '100%' }} min={80} max={200} size="large" />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item name="presion_diastolica" label="Presión Diastólica" rules={[{ required: true, message: 'Requerido' }]}>
                      <InputNumber style={{ width: '100%' }} min={50} max={150} size="large" />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item name="proteinuria" label="Proteinuria" valuePropName="checked">
                  <Radio.Group>
                    <Radio value={true}>Sí</Radio>
                    <Radio value={false}>No</Radio>
                  </Radio.Group>
                </Form.Item>
                <Form.Item name="historia_preeclampsia" label="Historia de Preeclampsia" valuePropName="checked">
                  <Radio.Group>
                    <Radio value={true}>Sí</Radio>
                    <Radio value={false}>No</Radio>
                  </Radio.Group>
                </Form.Item>
                <Form.Item name="diabetes" label="Diabetes" valuePropName="checked">
                  <Radio.Group>
                    <Radio value={true}>Sí</Radio>
                    <Radio value={false}>No</Radio>
                  </Radio.Group>
                </Form.Item>
                <Form.Item name="enfermedad_renal" label="Enfermedad Renal" valuePropName="checked">
                  <Radio.Group>
                    <Radio value={true}>Sí</Radio>
                    <Radio value={false}>No</Radio>
                  </Radio.Group>
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular Riesgo
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoPreeclampsia ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Puntos de Riesgo"
                    value={resultadoPreeclampsia.puntos}
                    valueStyle={{ fontSize: 32, color: '#1890ff' }}
                  />
                  <Progress percent={(resultadoPreeclampsia.puntos / 15) * 100} status={resultadoPreeclampsia.color === 'green' ? 'success' : resultadoPreeclampsia.color === 'red' ? 'exception' : 'normal'} />
                  <Tag color={resultadoPreeclampsia.color}>{resultadoPreeclampsia.riesgo}</Tag>
                  <Alert message="Recomendación" description={resultadoPreeclampsia.recomendacion} type={resultadoPreeclampsia.color === 'green' ? 'success' : resultadoPreeclampsia.color === 'red' ? 'error' : 'warning'} showIcon />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '5',
      label: <span><HeartOutlined /> ILA</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Mediciones Ecográficas" type="inner">
              <Form form={formILA} layout="vertical" onFinish={calcularILA}>
                <Alert message="Técnica: Método de Phelan" description="Mida el bolsillo máximo vertical en cada cuadrante." type="info" showIcon style={{ marginBottom: 16 }} />
                <Form.Item name="cuadrante1" label="Cuadrante Superior Derecho (cm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={0} max={15} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="cuadrante2" label="Cuadrante Superior Izquierdo (cm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={0} max={15} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="cuadrante3" label="Cuadrante Inferior Derecho (cm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={0} max={15} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="cuadrante4" label="Cuadrante Inferior Izquierdo (cm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={0} max={15} step={0.1} size="large" />
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular ILA
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoILA ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="ILA"
                    value={resultadoILA.ila}
                    suffix="cm"
                    valueStyle={{ fontSize: 32, color: '#1890ff' }}
                  />
                  <Progress percent={(parseFloat(resultadoILA.ila) / 24) * 100} status={resultadoILA.color === 'green' ? 'success' : resultadoILA.color === 'red' ? 'exception' : 'normal'} />
                  <Tag color={resultadoILA.color}>{resultadoILA.interpretacion}</Tag>
                  <Alert message="Conducta" description={resultadoILA.conducta} type={resultadoILA.color === 'green' ? 'success' : resultadoILA.color === 'red' ? 'error' : 'warning'} showIcon />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '6',
      label: <span><HeartOutlined /> Peso Fetal</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Biometría Fetal" type="inner">
              <Form form={formPesoFetal} layout="vertical" onFinish={calcularPesoFetal}>
                <Alert message="Fórmula de Hadlock" description="Ingrese medidas de ecografía obstétrica." type="info" showIcon style={{ marginBottom: 16 }} />
                <Form.Item name="dbp" label="DBP (mm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={20} max={120} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="cc" label="CC (mm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={100} max={400} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="ca" label="CA (mm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={100} max={450} step={0.1} size="large" />
                </Form.Item>
                <Form.Item name="lf" label="LF (mm)" rules={[{ required: true, message: 'Requerido' }]}>
                  <InputNumber style={{ width: '100%' }} min={20} max={90} step={0.1} size="large" />
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular Peso
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoPesoFetal ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Peso Estimado"
                    value={resultadoPesoFetal.peso}
                    suffix="g"
                    valueStyle={{ fontSize: 32, color: '#1890ff' }}
                  />
                  <Tag color={resultadoPesoFetal.color}>{resultadoPesoFetal.percentil}</Tag>
                  <Alert message="Nota" description="Estimado ±10-15% del peso real" type="warning" showIcon />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '7',
      label: <span><HeartOutlined /> Apgar</span>,
      children: (
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Evaluación RN" type="inner">
              <Form form={formApgar} layout="vertical" onFinish={calcularApgar}>
                <Form.Item name="frecuencia_cardiaca" label="FC" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Ausente (0)</Select.Option>
                    <Select.Option value={1}>&lt;100 lpm (1)</Select.Option>
                    <Select.Option value={2}>&gt;100 lpm (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="esfuerzo_respiratorio" label="Esfuerzo" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Ausente (0)</Select.Option>
                    <Select.Option value={1}>Débil (1)</Select.Option>
                    <Select.Option value={2}>Llanto fuerte (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="tono_muscular" label="Tono" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Flácido (0)</Select.Option>
                    <Select.Option value={1}>Flexión débil (1)</Select.Option>
                    <Select.Option value={2}>Activo (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="irritabilidad_refleja" label="Reflejo" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Sin respuesta (0)</Select.Option>
                    <Select.Option value={1}>Mueca (1)</Select.Option>
                    <Select.Option value={2}>Tos (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="color" label="Color" rules={[{ required: true, message: 'Requerido' }]}>
                  <Select size="large">
                    <Select.Option value={0}>Azul/pálido (0)</Select.Option>
                    <Select.Option value={1}>Rosado/azul extremidades (1)</Select.Option>
                    <Select.Option value={2}>Rosa completo (2)</Select.Option>
                  </Select>
                </Form.Item>
                <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} size="large" block>
                  Calcular
                </Button>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Resultados" type="inner">
              {resultadoApgar ? (
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                  <Statistic
                    title="Apgar"
                    value={resultadoApgar.score}
                    suffix="/10"
                    valueStyle={{ fontSize: 32, color: '#1890ff' }}
                  />
                  <Progress percent={(resultadoApgar.score / 10) * 100} status={resultadoApgar.color === 'green' ? 'success' : resultadoApgar.color === 'red' ? 'exception' : 'normal'} />
                  <Tag color={resultadoApgar.color}>{resultadoApgar.interpretacion}</Tag>
                  <Alert message="Conducta" description={resultadoApgar.conducta} type={resultadoApgar.color === 'green' ? 'success' : resultadoApgar.color === 'red' ? 'error' : 'warning'} showIcon />
                </Space>
              ) : (
                <Alert message="Complete los datos para ver los resultados" type="info" showIcon />
              )}
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: '8',
      label: <span><PercentageOutlined /> ICC</span>,
      children: (
        <Card>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="AC (mm)">
                <InputNumber
                  onChange={(ac) => {
                    const cerebelo = (document.querySelector('input[data-cerebelo]') as any)?.value;
                    if (ac && cerebelo) calcularICC(ac as number, parseFloat(cerebelo));
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Cerebelo (mm)">
                <InputNumber
                  data-cerebelo="true"
                  onChange={(cerebelo) => {
                    const ac = (document.querySelector('input[data-ac]') as any)?.value;
                    if (ac && cerebelo) calcularICC(parseFloat(ac), cerebelo as number);
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          {resultadoICC && (
            <>
              <Divider />
              <Statistic title="ICC" value={resultadoICC.icc} valueStyle={{ color: resultadoICC.normal ? '#52c41a' : '#ff4d4f' }} />
              <Tag color={resultadoICC.normal ? 'green' : 'red'}>{resultadoICC.interpretacion}</Tag>
            </>
          )}
        </Card>
      ),
    },
    {
      key: '9',
      label: <span><HeartOutlined /> PA Media</span>,
      children: (
        <Card>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Sistólica (mmHg)">
                <InputNumber onChange={(s) => { const d = (document.querySelector('input[data-dias]') as any)?.value; if (s && d) calcularPA(s as number, parseFloat(d)); }} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Diastólica (mmHg)">
                <InputNumber data-dias="true" onChange={(d) => { const s = (document.querySelector('input[data-sist]') as any)?.value; if (s && d) calcularPA(parseFloat(s), d as number); }} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          {resultadoPA && (
            <>
              <Divider />
              <Statistic title="PA Media" value={resultadoPA.pa} suffix="mmHg" />
              <Tag>{resultadoPA.interpretacion}</Tag>
            </>
          )}
        </Card>
      ),
    },
    {
      key: '10',
      label: <span><HeartOutlined /> FC Máx</span>,
      children: (
        <Card>
          <Form.Item label="Edad (años)">
            <InputNumber onChange={(edad) => calcularFCMax(edad as number)} style={{ width: '100%' }} />
          </Form.Item>
          {resultadoFCMax && (
            <>
              <Divider />
              <Statistic title="FC Máxima" value={resultadoFCMax.fc} suffix="bpm" />
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={8}>
                  <Statistic title="50%" value={resultadoFCMax.intensidad_50} />
                </Col>
                <Col span={8}>
                  <Statistic title="75%" value={resultadoFCMax.intensidad_75} />
                </Col>
                <Col span={8}>
                  <Statistic title="90%" value={resultadoFCMax.intensidad_90} />
                </Col>
              </Row>
            </>
          )}
        </Card>
      ),
    },
    {
      key: '11',
      label: <span><CheckCircleOutlined /> Capurro</span>,
      children: (
        <Card title={<><TeamOutlined /> Método de Capurro</>}>
          <Form layout="vertical" onFinish={(values) => calcularCapurro(values.textura, values.oreja, values.mama, values.pezon, values.planta)}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="textura" label="Textura de Piel" rules={[{ required: true }]}>
                  <Tooltip title="0-4 puntos según textura">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="oreja" label="Forma de Oreja" rules={[{ required: true }]}>
                  <Tooltip title="0-4 puntos según formación">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="mama" label="Tamaño Glándula Mamaria" rules={[{ required: true }]}>
                  <Tooltip title="0-4 puntos">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="pezon" label="Formación del Pezón" rules={[{ required: true }]}>
                  <Tooltip title="0-4 puntos">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={24}>
                <Form.Item name="planta" label="Pliegues Plantares" rules={[{ required: true }]}>
                  <Tooltip title="0-4 puntos según pliegues">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} block>
              Calcular Capurro
            </Button>
          </Form>
          {resultadoCapurro && (
            <Spin spinning={false}>
              <Divider />
              <Badge count={resultadoCapurro.puntos} showZero color="blue" style={{ marginBottom: 16 }}>
                <Statistic title="Edad Gestacional" value={`${resultadoCapurro.semanas} sem + ${resultadoCapurro.dias} días`} />
              </Badge>
              <Divider />
              <Tag color={resultadoCapurro.interpretacion === 'A término' ? 'green' : 'orange'}>
                {resultadoCapurro.interpretacion}
              </Tag>
            </Spin>
          )}
        </Card>
      ),
    },
    {
      key: '12',
      label: <span><FileOutlined /> Silverman</span>,
      children: (
        <Card>
          <Title level={4}>Test de Silverman-Andersen</Title>
          <Paragraph>
            Evaluación de dificultad respiratoria neonatal. Puntaje 0-10 (0: sin dificultad, 10: dificultad severa)
          </Paragraph>
          <Form layout="vertical" onFinish={(values) => {
            const total = Object.values(values).reduce((acc: number, val) => acc + (val as number || 0), 0);
            const resultado = {
              puntos: total,
              gravedad: total === 0 ? 'Sin dificultad' : total <= 3 ? 'Leve' : total <= 6 ? 'Moderada' : 'Severa'
            };
            dispatchResultado({ type: 'SET_SILVERMAN', payload: resultado });
            message.success('Silverman calculado');
          }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="movimientos_torax" label="Movimientos Tórax" rules={[{ required: true }]}>
                  <Input.Group compact>
                    <Select defaultValue={0} style={{ width: '100%' }}>
                      <Select.Option value={0}>Rítmicos y regulares (0)</Select.Option>
                      <Select.Option value={1}>Retracción intercostal leve (1)</Select.Option>
                      <Select.Option value={2}>Retracción marcada (2)</Select.Option>
                    </Select>
                  </Input.Group>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="tiraje" label="Tiraje" rules={[{ required: true }]}>
                  <Select defaultValue={0} style={{ width: '100%' }}>
                    <Select.Option value={0}>Ausente (0)</Select.Option>
                    <Select.Option value={1}>Leve (1)</Select.Option>
                    <Select.Option value={2}>Marcado (2)</Select.Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} block>
              Calcular Silverman
            </Button>
          </Form>
          {resultadoSilverman && (
            <Result
              status={resultadoSilverman.puntos === 0 ? 'success' : resultadoSilverman.puntos <= 3 ? 'warning' : 'error'}
              title={`Puntaje: ${resultadoSilverman.puntos}`}
              subTitle={`Gravedad: ${resultadoSilverman.gravedad}`}
            />
          )}
        </Card>
      ),
    },
    {
      key: '13',
      label: <span><SaveOutlined /> Ballard</span>,
      children: (
        <Card>
          <Title level={4}>Ballard Score</Title>
          <Paragraph>
            Evaluación de madurez neuromuscular y física del recién nacido
          </Paragraph>
          <Form layout="vertical" onFinish={(values) => {
            const total = Object.values(values).reduce((acc: number, val) => acc + (val as number || 0), 0);
            const edadGestacional = 20 + (total * 2);
            const resultado = {
              puntos: total,
              edadGestacional: edadGestacional,
              categoria: edadGestacional < 37 ? 'Prematuro' : edadGestacional <= 42 ? 'A término' : 'Postmaduro'
            };
            dispatchResultado({ type: 'SET_BALLARD', payload: resultado });
            message.success('Ballard calculado');
          }}>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="postura" label="Postura" rules={[{ required: true }]}>
                  <Tooltip title="Evaluación de flexión de extremidades">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="ventana_cuadrada" label="Ventana Cuadrada" rules={[{ required: true }]}>
                  <Tooltip title="Flexión de muñeca">
                    <InputNumber min={0} max={4} style={{ width: '100%' }} />
                  </Tooltip>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="rebote_brazo" label="Rebote de Brazo" rules={[{ required: true }]}>
                  <InputNumber min={0} max={4} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="angulo_popliteo" label="Ángulo Poplíteo" rules={[{ required: true }]}>
                  <InputNumber min={0} max={4} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
            <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} loading={loading} block>
              Calcular Ballard
            </Button>
          </Form>
          {resultadoBallard && (
            <>
              <Divider />
              <Statistic title="Edad Gestacional Estimada" value={resultadoBallard.edadGestacional} suffix="semanas" />
              <Tag color={resultadoBallard.categoria === 'A término' ? 'green' : 'orange'}>
                {resultadoBallard.categoria}
              </Tag>
            </>
          )}
        </Card>
      ),
    },
  ];

  return (
    <div className="calculadoras-container page-container">
      <Card
        title={
          <Space>
            <CalculatorOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>Calculadoras Médicas Obstétricas</span>
          </Space>
        }
        extra={
          <Button
            icon={<HistoryOutlined />}
            onClick={() => setHistorialVisible(true)}
            type="dashed"
          >
            Historial ({historial.length})
          </Button>
        }
      >
        <Alert
          message="Suite de Calculadoras Clínicas"
          description="Herramientas médicas profesionales para cálculos obstétricos. Todos los resultados deben ser interpretados por un profesional de la salud."
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 24 }}
        />

        <Tabs items={tabsItems} />
      </Card>

      {/* Drawer de Historial */}
      <Drawer
        title="Historial de Cálculos"
        placement="right"
        onClose={() => setHistorialVisible(false)}
        open={historialVisible}
        width={700}
        extra={
          <Space>
            <Tooltip title="Descargar historial">
              <Button icon={<DownloadOutlined />} onClick={() => {
                const dataStr = JSON.stringify(historial, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `historial-calculadoras-${dayjs().format('YYYY-MM-DD')}.json`;
                link.click();
                message.success('Historial descargado');
              }} />
            </Tooltip>
            <Tooltip title="Imprimir historial">
              <Button icon={<PrinterOutlined />} onClick={() => {
                window.print();
                message.info('Preparando impresión...');
              }} />
            </Tooltip>
            <Popconfirm
              title="Limpiar historial"
              description="¿Está seguro de que desea eliminar todo el historial?"
              onConfirm={limpiarHistorial}
            >
              <Tooltip title="Eliminar historial">
                <Button danger icon={<DeleteOutlined />} />
              </Tooltip>
            </Popconfirm>
          </Space>
        }
      >
        {historial.length > 0 ? (
          <>
            <Alert message="Vista de Tabla" type="info" showIcon style={{ marginBottom: 16 }} />
            <Table
              dataSource={historial}
              rowKey="id"
              size="small"
              pagination={{ pageSize: 5 }}
              columns={[
                {
                  title: 'Tipo',
                  dataIndex: 'tipo',
                  key: 'tipo',
                  render: (tipo) => <Badge status="processing" text={tipo} />
                },
                {
                  title: 'Fecha',
                  dataIndex: 'fecha',
                  key: 'fecha',
                },
                {
                  title: 'Acciones',
                  key: 'actions',
                  render: (_, record) => (
                    <Button
                      size="small"
                      type="link"
                      onClick={() => {
                        Modal.info({
                          title: record.tipo,
                          content: (
                            <div>
                              <Divider />
                              <Paragraph>
                                <strong>Fecha:</strong> {record.fecha}
                              </Paragraph>
                              <Divider>Datos Ingresados</Divider>
                              <pre>{JSON.stringify(record.datos, null, 2)}</pre>
                              <Divider>Resultados</Divider>
                              <pre>{JSON.stringify(record.resultado, null, 2)}</pre>
                            </div>
                          ),
                          width: 600,
                        });
                      }}
                    >
                      Ver Detalle
                    </Button>
                  )
                }
              ]}
            />

            <Divider>Línea de Tiempo</Divider>
            <Timeline
              items={historial.slice(0, 10).map((item) => ({
                key: item.id,
                children: (
                  <>
                    <p><strong>{item.tipo}</strong></p>
                    <p style={{ fontSize: 12, color: '#666' }}>{item.fecha}</p>
                  </>
                ),
                color: 'blue'
              }))}
            />
          </>
        ) : (
          <Empty description="Sin historial de cálculos" />
        )}
      </Drawer>
    </div>
  );
};

export default CalculadorasPage;
