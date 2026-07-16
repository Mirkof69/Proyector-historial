/**
 * =============================================================================
 * CALCULADORAS AVANZADAS - HERRAMIENTAS CLÍNICAS
 * =============================================================================
 * Conjunto completo de calculadoras médicas para gineco-obstetricia
 * - Edad gestacional y FPP
 * - Score de Bishop
 * - IMC y ganancia de peso
 * - Riesgo de preeclampsia
 * - Tamizaje de diabetes gestacional
 * - Índice de líquido amniótico
 * - Estimación de peso fetal
 * - Score de Apgar
 * - Conexión: GET /calculadoras-avanzadas/
 * =============================================================================
 */

import React, { useState } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { Card, Tabs, Form, Space, Alert } from "antd";
import { CalculatorOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import './CalculadorasAvanzadas.css';
import { ResultadoCalculo, guardarResultado } from './calcAvanzadasHelpers';
import { buildCalcAvanzadasTabs } from './calcAvanzadasTabs';

const CalculadorasAvanzadas: React.FC = () => {
  const [formEdadGestacional] = Form.useForm();
  const { message } = useAntdApp();
  const [formBishop] = Form.useForm();
  const [formIMC] = Form.useForm();
  const [formPreeclampsia] = Form.useForm();
  const [formDiabetes] = Form.useForm();
  const [formILA] = Form.useForm();
  const [formPesoFetal] = Form.useForm();
  const [formApgar] = Form.useForm();

  const [resultados, setResultados] = useState({
    edadGestacional: null as ResultadoCalculo | null,
    bishop: null as ResultadoCalculo | null,
    imc: null as ResultadoCalculo | null,
    preeclampsia: null as ResultadoCalculo | null,
    diabetes: null as ResultadoCalculo | null,
    ila: null as ResultadoCalculo | null,
    pesoFetal: null as ResultadoCalculo | null,
    apgar: null as ResultadoCalculo | null,
  });

  const resultadoEdadGestacional = resultados.edadGestacional;
  const setResultadoEdadGestacional = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, edadGestacional: val }));

  const resultadoBishop = resultados.bishop;
  const setResultadoBishop = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, bishop: val }));

  const resultadoIMC = resultados.imc;
  const setResultadoIMC = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, imc: val }));

  const resultadoPreeclampsia = resultados.preeclampsia;
  const setResultadoPreeclampsia = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, preeclampsia: val }));

  const resultadoDiabetes = resultados.diabetes;
  const setResultadoDiabetes = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, diabetes: val }));

  const resultadoILA = resultados.ila;
  const setResultadoILA = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, ila: val }));

  const resultadoPesoFetal = resultados.pesoFetal;
  const setResultadoPesoFetal = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, pesoFetal: val }));

  const resultadoApgar = resultados.apgar;
  const setResultadoApgar = (val: ResultadoCalculo | null) =>
    setResultados((prev) => ({ ...prev, apgar: val }));

  // Persistencia en backend: esta pantalla nunca guardaba nada, ni siquiera
  // en localStorage — el resultado se perdía al cambiar de pestaña.
  // ==========================================================================
  // CALCULADORA 1: EDAD GESTACIONAL Y FPP
  // ==========================================================================
  const calcularEdadGestacional = (values: any) => {
    try {
      const fum = dayjs(values.fum);
      const fechaActual = values.fecha_actual ? dayjs(values.fecha_actual) : dayjs();

      const diasDiferencia = fechaActual.diff(fum, 'day');
      const semanas = Math.floor(diasDiferencia / 7);
      const dias = diasDiferencia % 7;

      // Calcular FPP (280 días desde FUM)
      const fpp = fum.add(280, 'day');

      // Determinar trimestre
      let trimestre = '';
      let categoria = '';
      let color = '';

      if (semanas <= 13) {
        trimestre = 'Primer Trimestre';
        categoria = 'primer_trimestre';
        color = 'cyan';
      } else if (semanas <= 27) {
        trimestre = 'Segundo Trimestre';
        categoria = 'segundo_trimestre';
        color = 'blue';
      } else {
        trimestre = 'Tercer Trimestre';
        categoria = 'tercer_trimestre';
        color = 'purple';
      }

      const diasRestantes = 280 - diasDiferencia;
      const semanasRestantes = Math.floor(diasRestantes / 7);

      const resultado: ResultadoCalculo = {
        valor: `${semanas} semanas + ${dias} días`,
        interpretacion: `${trimestre}. Faltan ${semanasRestantes} semanas aproximadamente para la fecha probable de parto.`,
        categoria,
        color,
        recomendaciones: [
          `Fecha Probable de Parto: ${fpp.format('DD/MM/YYYY')}`,
          `Días de gestación: ${diasDiferencia}`,
          `Días restantes: ${diasRestantes}`,
        ],
      };

      setResultadoEdadGestacional(resultado);
      guardarResultado('edad_gestacional', values, resultado);
      message.success('Edad gestacional calculada correctamente');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 2: SCORE DE BISHOP
  // ==========================================================================
  const calcularBishop = (values: any) => {
    try {
      const score =
        (values.dilatacion || 0) +
        (values.borramiento || 0) +
        (values.posicion || 0) +
        (values.consistencia || 0) +
        (values.altura_presentacion || 0);

      let interpretacion = '';
      let categoria = '';
      let color = '';
      let recomendaciones: string[] = [];

      if (score <= 5) {
        interpretacion = 'Cérvix desfavorable';
        categoria = 'desfavorable';
        color = 'red';
        recomendaciones = [
          'La inducción del parto puede ser difícil',
          'Considerar maduración cervical previa',
          'Puede requerir cesárea si la inducción falla',
        ];
      } else if (score <= 8) {
        interpretacion = 'Cérvix intermedio';
        categoria = 'intermedio';
        color = 'orange';
        recomendaciones = [
          'Inducción con probabilidad moderada de éxito',
          'Considerar maduración cervical',
          'Monitoreo cercano durante la inducción',
        ];
      } else {
        interpretacion = 'Cérvix favorable';
        categoria = 'favorable';
        color = 'green';
        recomendaciones = [
          'Alta probabilidad de éxito en la inducción',
          'El trabajo de parto puede iniciarse espontáneamente pronto',
          'Buenas condiciones para parto vaginal',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: score,
        interpretacion,
        categoria,
        color,
        recomendaciones,
      };

      setResultadoBishop(resultado);
      guardarResultado('bishop', values, resultado);
      message.success('Score de Bishop calculado correctamente');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 3: IMC Y GANANCIA DE PESO
  // ==========================================================================
  const calcularIMC = (values: any) => {
    try {
      const peso = values.peso;
      const altura = values.altura / 100; // Convertir cm a metros
      const imc = peso / (altura * altura);

      let categoria = '';
      let color = '';
      let interpretacion = '';
      let gananciaRecomendada = '';
      let recomendaciones: string[] = [];

      if (imc < 18.5) {
        categoria = 'Bajo peso';
        color = 'orange';
        interpretacion = 'IMC por debajo del rango normal';
        gananciaRecomendada = '12.5 - 18 kg';
        recomendaciones = [
          'Ganancia de peso recomendada durante el embarazo: 12.5-18 kg',
          'Consultar con nutricionista',
          'Aumentar ingesta calórica controlada',
        ];
      } else if (imc < 25) {
        categoria = 'Peso normal';
        color = 'green';
        interpretacion = 'IMC dentro del rango saludable';
        gananciaRecomendada = '11.5 - 16 kg';
        recomendaciones = [
          'Ganancia de peso recomendada durante el embarazo: 11.5-16 kg',
          'Mantener dieta balanceada',
          'Ejercicio moderado regular',
        ];
      } else if (imc < 30) {
        categoria = 'Sobrepeso';
        color = 'orange';
        interpretacion = 'IMC por encima del rango normal';
        gananciaRecomendada = '7 - 11.5 kg';
        recomendaciones = [
          'Ganancia de peso recomendada durante el embarazo: 7-11.5 kg',
          'Control nutricional estricto',
          'Mayor riesgo de diabetes gestacional y preeclampsia',
        ];
      } else {
        categoria = 'Obesidad';
        color = 'red';
        interpretacion = 'IMC en rango de obesidad';
        gananciaRecomendada = '5 - 9 kg';
        recomendaciones = [
          'Ganancia de peso recomendada durante el embarazo: 5-9 kg',
          'Seguimiento nutricional especializado',
          'Alto riesgo de complicaciones obstétricas',
          'Vigilancia estrecha de diabetes gestacional',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: imc.toFixed(2),
        interpretacion: `${categoria} - ${interpretacion}`,
        categoria,
        color,
        recomendaciones: [
          `Ganancia de peso recomendada: ${gananciaRecomendada}`,
          ...recomendaciones,
        ],
      };

      setResultadoIMC(resultado);
      guardarResultado('imc', values, resultado);
      message.success('IMC calculado correctamente');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 4: RIESGO DE PREECLAMPSIA
  // ==========================================================================
  const calcularRiesgoPreeclampsia = (values: any) => {
    try {
      let puntos = 0;
      const factores: string[] = [];

      // Factores de riesgo alto (2 puntos cada uno)
      if (values.preeclampsia_previa) {
        puntos += 2;
        factores.push('Preeclampsia previa');
      }
      if (values.hipertension_cronica) {
        puntos += 2;
        factores.push('Hipertensión crónica');
      }
      if (values.diabetes_pregestacional) {
        puntos += 2;
        factores.push('Diabetes pregestacional');
      }
      if (values.enfermedad_renal) {
        puntos += 2;
        factores.push('Enfermedad renal');
      }

      // Factores de riesgo moderado (1 punto cada uno)
      if (values.edad >= 40) {
        puntos += 1;
        factores.push('Edad ≥40 años');
      }
      if (values.primiparidad) {
        puntos += 1;
        factores.push('Primiparidad');
      }
      if (values.obesidad) {
        puntos += 1;
        factores.push('Obesidad (IMC ≥30)');
      }
      if (values.embarazo_multiple) {
        puntos += 1;
        factores.push('Embarazo múltiple');
      }
      if (values.intervalo_largo) {
        puntos += 1;
        factores.push('Intervalo >10 años entre embarazos');
      }

      let categoria = '';
      let color = '';
      let interpretacion = '';
      let recomendaciones: string[] = [];

      if (puntos === 0) {
        categoria = 'Riesgo Bajo';
        color = 'green';
        interpretacion = 'Sin factores de riesgo significativos';
        recomendaciones = [
          'Control prenatal rutinario',
          'Vigilancia estándar de presión arterial',
          'Dieta saludable y ejercicio',
        ];
      } else if (puntos <= 2) {
        categoria = 'Riesgo Moderado';
        color = 'orange';
        interpretacion = 'Presencia de factores de riesgo moderados';
        recomendaciones = [
          'Considerar aspirina 100-150mg diaria desde las 12 semanas',
          'Control prenatal cada 3-4 semanas',
          'Monitoreo de presión arterial en casa',
          'Vigilancia de síntomas de alarma',
        ];
      } else {
        categoria = 'Riesgo Alto';
        color = 'red';
        interpretacion = 'Múltiples factores de riesgo presentes';
        recomendaciones = [
          'Aspirina 100-150mg diaria desde las 12 semanas (OBLIGATORIO)',
          'Control prenatal cada 2-3 semanas',
          'Monitoreo estricto de presión arterial',
          'Proteinuria en cada visita',
          'Ecografía Doppler de arterias uterinas',
          'Vigilancia de restricción de crecimiento fetal',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: `${puntos} puntos`,
        interpretacion,
        categoria,
        color,
        recomendaciones: [
          `Factores de riesgo identificados: ${factores.length > 0 ? factores.join(', ') : 'Ninguno'}`,
          ...recomendaciones,
        ],
      };

      setResultadoPreeclampsia(resultado);
      guardarResultado('riesgo_preeclampsia', values, resultado);
      message.success('Riesgo de preeclampsia calculado correctamente');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 5: TAMIZAJE DIABETES GESTACIONAL
  // ==========================================================================
  const calcularDiabetesGestacional = (values: any) => {
    try {
      const ayunas = values.glucosa_ayunas;
      const hora1 = values.glucosa_1h;
      const hora2 = values.glucosa_2h;

      let diagnostico = '';
      let categoria = '';
      let color = '';
      let interpretacion = '';
      let alertas: string[] = [];
      let recomendaciones: string[] = [];

      // Criterios de Carpenter-Coustan (CTOG 100g)
      const ayunasAlto = ayunas >= 95;
      const hora1Alto = hora1 >= 180;
      const hora2Alto = hora2 >= 155;

      const valoresAlterados = [ayunasAlto, hora1Alto, hora2Alto].filter(Boolean).length;

      if (valoresAlterados === 0) {
        diagnostico = 'Normal';
        categoria = 'normal';
        color = 'green';
        interpretacion = 'Tolerancia a la glucosa normal';
        recomendaciones = [
          'Continuar dieta saludable',
          'Ejercicio regular',
          'Repetir tamizaje si hay factores de riesgo',
        ];
      } else if (valoresAlterados === 1) {
        diagnostico = 'Intolerancia a la glucosa';
        categoria = 'intolerancia';
        color = 'orange';
        interpretacion = 'Un valor alterado - No cumple criterios de diabetes gestacional';
        alertas.push('Requiere seguimiento cercano');
        recomendaciones = [
          'Dieta controlada en carbohidratos',
          'Monitoreo de glucosa en casa',
          'Repetir CTOG en 4 semanas',
          'Consulta con nutricionista',
        ];
      } else {
        diagnostico = 'Diabetes Gestacional';
        categoria = 'diabetes';
        color = 'red';
        interpretacion = `Dos o más valores alterados - Diagnóstico de Diabetes Gestacional`;
        alertas.push('DIAGNÓSTICO CONFIRMADO - Requiere manejo inmediato');
        recomendaciones = [
          'Inicio de dieta para diabetes gestacional',
          'Monitoreo de glucosa 4 veces al día (ayunas y 2h post-prandial)',
          'Referencia a endocrinología',
          'Considerar insulina si no hay control con dieta',
          'Ecografías seriadas para vigilar crecimiento fetal',
          'Vigilancia de líquido amniótico',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: diagnostico,
        interpretacion,
        categoria,
        color,
        recomendaciones,
        alertas,
      };

      setResultadoDiabetes(resultado);
      guardarResultado('diabetes_gestacional', values, resultado);
      message.success('Tamizaje de diabetes gestacional calculado');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 6: ÍNDICE DE LÍQUIDO AMNIÓTICO (ILA)
  // ==========================================================================
  const calcularILA = (values: any) => {
    try {
      const ila =
        (values.cuadrante1 || 0) +
        (values.cuadrante2 || 0) +
        (values.cuadrante3 || 0) +
        (values.cuadrante4 || 0);

      let categoria = '';
      let color = '';
      let interpretacion = '';
      let recomendaciones: string[] = [];
      let alertas: string[] = [];

      if (ila < 5) {
        categoria = 'Oligohidramnios';
        color = 'red';
        interpretacion = 'Líquido amniótico disminuido';
        alertas.push('ALERTA: Oligohidramnios severo');
        recomendaciones = [
          'Evaluación inmediata del bienestar fetal',
          'Doppler de arteria umbilical',
          'Descartar rotura prematura de membranas',
          'Evaluar función renal fetal',
          'Considerar finalización del embarazo si >34 semanas',
          'Hidratación materna',
        ];
      } else if (ila < 8) {
        categoria = 'Oligohidramnios leve';
        color = 'orange';
        interpretacion = 'Líquido amniótico en límite inferior';
        alertas.push('Vigilancia estrecha requerida');
        recomendaciones = [
          'Repetir ILA en 1 semana',
          'Perfil biofísico',
          'Aumentar hidratación materna',
          'Vigilancia de movimientos fetales',
        ];
      } else if (ila <= 24) {
        categoria = 'Normal';
        color = 'green';
        interpretacion = 'Líquido amniótico adecuado';
        recomendaciones = [
          'Continuar controles prenatales rutinarios',
          'ILA normal para la edad gestacional',
        ];
      } else if (ila <= 30) {
        categoria = 'Polihidramnios leve';
        color = 'orange';
        interpretacion = 'Líquido amniótico aumentado';
        alertas.push('Investigar causa de polihidramnios');
        recomendaciones = [
          'Descartar diabetes gestacional',
          'Ecografía anatómica detallada',
          'Evaluar malformaciones fetales',
          'Repetir ILA en 2 semanas',
        ];
      } else {
        categoria = 'Polihidramnios moderado-severo';
        color = 'red';
        interpretacion = 'Líquido amniótico muy aumentado';
        alertas.push('ALERTA: Polihidramnios severo');
        recomendaciones = [
          'Investigación exhaustiva de causa',
          'Descartar diabetes gestacional',
          'Descartar malformaciones fetales (atresia esofágica, anencefalia)',
          'Considerar amniocentesis terapéutica si sintomática',
          'Vigilancia de trabajo de parto prematuro',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: `${ila.toFixed(1)} cm`,
        interpretacion,
        categoria,
        color,
        recomendaciones,
        alertas,
      };

      setResultadoILA(resultado);
      guardarResultado('ila', values, resultado);
      message.success('Índice de líquido amniótico calculado');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 7: PESO FETAL ESTIMADO
  // ==========================================================================
  const calcularPesoFetal = (values: any) => {
    try {
      const dbp = values.dbp;
      const ca = values.ca;
      const lf = values.lf;

      // Fórmula de Hadlock
      const logPeso =
        1.3596 +
        0.0064 * ca +
        0.0424 * dbp +
        0.174 * lf +
        0.00061 * dbp * ca -
        0.00386 * ca * lf;

      const pesoGramos = Math.round(Math.pow(10, logPeso));
      const semanas = values.edad_gestacional_semanas;

      // Percentiles aproximados por semana gestacional
      const percentilesAproximados: Record<number, { p10: number; p50: number; p90: number }> = {
        20: { p10: 270, p50: 320, p90: 370 },
        24: { p10: 550, p50: 650, p90: 750 },
        28: { p10: 950, p50: 1100, p90: 1250 },
        32: { p10: 1500, p50: 1800, p90: 2100 },
        36: { p10: 2300, p50: 2700, p90: 3100 },
        40: { p10: 2900, p50: 3400, p90: 3900 },
      };

      const percentilesRef = percentilesAproximados[semanas] || { p10: 0, p50: 0, p90: 0 };

      let categoria = '';
      let color = '';
      let interpretacion = '';
      let recomendaciones: string[] = [];
      let alertas: string[] = [];

      if (pesoGramos < percentilesRef.p10) {
        categoria = 'Peso bajo para edad gestacional';
        color = 'red';
        interpretacion = `Peso estimado por debajo del percentil 10 para ${semanas} semanas`;
        alertas.push('Posible restricción de crecimiento intrauterino');
        recomendaciones = [
          'Doppler de arteria umbilical y cerebral media',
          'Perfil biofísico',
          'Ecografías seriadas cada 2 semanas',
          'Evaluar causas de RCIU',
          'Considerar finalización si hay deterioro del bienestar fetal',
        ];
      } else if (pesoGramos <= percentilesRef.p90) {
        categoria = 'Peso adecuado para edad gestacional';
        color = 'green';
        interpretacion = `Peso estimado entre percentiles 10-90 para ${semanas} semanas`;
        recomendaciones = [
          'Crecimiento fetal adecuado',
          'Continuar controles prenatales rutinarios',
        ];
      } else {
        categoria = 'Peso alto para edad gestacional';
        color = 'orange';
        interpretacion = `Peso estimado por encima del percentil 90 para ${semanas} semanas`;
        alertas.push('Posible macrosomía fetal');
        recomendaciones = [
          'Descartar diabetes gestacional',
          'Evaluar vía de parto (riesgo de distocia de hombros)',
          'Considerar finalización a las 39 semanas',
          'Informar riesgos de parto vaginal vs cesárea',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: `${pesoGramos}g`,
        interpretacion,
        categoria,
        color,
        recomendaciones: [
          `Percentil 10: ${percentilesRef.p10}g`,
          `Percentil 50: ${percentilesRef.p50}g`,
          `Percentil 90: ${percentilesRef.p90}g`,
          ...recomendaciones,
        ],
        alertas,
      };

      setResultadoPesoFetal(resultado);
      guardarResultado('peso_fetal', values, resultado);
      message.success('Peso fetal estimado calculado');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // CALCULADORA 8: SCORE DE APGAR
  // ==========================================================================
  const calcularApgar = (values: any) => {
    try {
      const score =
        (values.frecuencia_cardiaca || 0) +
        (values.esfuerzo_respiratorio || 0) +
        (values.tono_muscular || 0) +
        (values.reflejos || 0) +
        (values.color || 0);

      let categoria = '';
      let color = '';
      let interpretacion = '';
      let recomendaciones: string[] = [];
      let alertas: string[] = [];

      if (score <= 3) {
        categoria = 'Depresión severa';
        color = 'red';
        interpretacion = 'Recién nacido en estado crítico';
        alertas.push('EMERGENCIA: Reanimación neonatal inmediata');
        recomendaciones = [
          'Reanimación neonatal avanzada',
          'Intubación endotraqueal',
          'Compresiones torácicas si FC <60 lpm',
          'Adrenalina según protocolo',
          'UCIN inmediatamente',
        ];
      } else if (score <= 6) {
        categoria = 'Depresión moderada';
        color = 'orange';
        interpretacion = 'Recién nacido con dificultad moderada';
        alertas.push('Requiere reanimación');
        recomendaciones = [
          'Estimulación táctil',
          'Aspiración de secreciones',
          'Oxígeno suplementario',
          'Ventilación con presión positiva',
          'Reevaluar Apgar al minuto',
        ];
      } else if (score <= 7) {
        categoria = 'Buena condición';
        color = 'blue';
        interpretacion = 'Recién nacido con adaptación adecuada';
        recomendaciones = [
          'Vigilancia cercana',
          'Estimulación suave',
          'Contacto piel a piel',
          'Reevaluar a los 5 minutos',
        ];
      } else {
        categoria = 'Excelente condición';
        color = 'green';
        interpretacion = 'Recién nacido vigoroso y con buena adaptación';
        recomendaciones = [
          'Pinzamiento tardío del cordón (1-3 min)',
          'Contacto piel a piel inmediato',
          'Inicio de lactancia materna en primera hora',
          'Cuidados rutinarios del recién nacido',
        ];
      }

      const resultado: ResultadoCalculo = {
        valor: score,
        interpretacion,
        categoria,
        color,
        recomendaciones,
        alertas,
      };

      setResultadoApgar(resultado);
      guardarResultado('apgar', values, resultado);
      message.success('Score de Apgar calculado');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // RENDER PRINCIPAL
  // ==========================================================================
  const tabsItems = buildCalcAvanzadasTabs({
    formEdadGestacional, formBishop, formIMC, formPreeclampsia, formDiabetes,
    formILA, formPesoFetal, formApgar,
    resultadoEdadGestacional, resultadoBishop, resultadoIMC, resultadoPreeclampsia,
    resultadoDiabetes, resultadoILA, resultadoPesoFetal, resultadoApgar,
    calcularEdadGestacional, calcularBishop, calcularIMC, calcularRiesgoPreeclampsia,
    calcularDiabetesGestacional, calcularILA, calcularPesoFetal, calcularApgar,
  });

  return (
    <div className="calculadoras-avanzadas-container">
      <Card
        title={
          <Space>
            <CalculatorOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>
              Calculadoras Clínicas Avanzadas
            </span>
          </Space>
        }
      >
        <Alert
          message="Herramientas de Cálculo Médico"
          description="Conjunto completo de calculadoras obstétricas validadas para apoyo en la toma de decisiones clínicas."
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        <Tabs defaultActiveKey="1" type="card" items={tabsItems} />
      </Card>
    </div>
  );
};

export default CalculadorasAvanzadas;
