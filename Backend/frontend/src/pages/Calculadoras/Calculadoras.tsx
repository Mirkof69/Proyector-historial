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

import React, { useState, useReducer } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Card, Button, Space, Form, Alert, Tabs } from "antd";
import {
  CalculatorOutlined, InfoCircleOutlined, HistoryOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import calculoHistorialService from '../../services/calculoHistorialService';
import {
  ResultadoCalculo, initialResultados, resultadosReducer, TIPO_CALCULADORA_SLUG,
} from './calculadorasReducer';
import { buildCalculadorasTabs } from './calculadorasTabs';
import HistorialDrawer from './components/HistorialDrawer';

const CalculadorasPage: React.FC = () => {
  const [resultados, dispatchResultado] = useReducer(resultadosReducer, initialResultados);
  const { message, modal } = useAntdApp();
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

  // Guardar en historial: localStorage como cache instantáneo/offline, y
  // backend como fuente de verdad (antes solo se guardaba en localStorage y
  // se perdía al cerrar sesión o cambiar de dispositivo).
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

    const tipoCalculadora = TIPO_CALCULADORA_SLUG[tipo];
    if (tipoCalculadora) {
      calculoHistorialService.crear({
        tipo_calculadora: tipoCalculadora,
        inputs_json: datos,
        resultado_json: resultado,
        resultado_resumen: typeof resultado === 'string' ? resultado : JSON.stringify(resultado).slice(0, 250),
      });
    }
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
  const tabsItems = buildCalculadorasTabs({
    formEG, formIMC, formBishop, formPreeclampsia, formILA, formPesoFetal, formApgar,
    loading, resultadoEG, resultadoIMC, resultadoBishop, resultadoPreeclampsia,
    resultadoILA, resultadoPesoFetal, resultadoApgar, resultadoCapurro,
    resultadoSilverman, resultadoBallard, resultadoICC, resultadoPA, resultadoFCMax,
    calcularEdadGestacional, calcularIMC, calcularBishop, calcularRiesgoPreeclampsia,
    calcularILA, calcularPesoFetal, calcularApgar, calcularCapurro, calcularICC,
    calcularPA, calcularFCMax, dispatchResultado, message,
  });

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
      <HistorialDrawer
        historialVisible={historialVisible}
        onClose={() => setHistorialVisible(false)}
        historial={historial}
        limpiarHistorial={limpiarHistorial}
        message={message}
        modal={modal}
      />
    </div>
  );
};

export default CalculadorasPage;
