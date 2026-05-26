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
import {
  Card,
  Tabs,
  Form,
  Input,
  InputNumber,
  DatePicker,
  Button,
  Space,
  Row,
  Col,
  Divider,
  message,
  Alert,
  Statistic,
  Typography,
  Select,
  Radio,
  Badge,
  Timeline,
  Table,
  Tooltip,
  Switch,
} from 'antd';
import {
  CalculatorOutlined,
  CalendarOutlined,
  HeartOutlined,
  UserOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  LineChartOutlined,
  BulbOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import './CalculadorasAvanzadas.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

// Hoisted tab labels (static JSX - avoids recreation on every render)
const tabEdadGestacional = (
  <Space>
    <CalendarOutlined />
    Edad Gestacional
  </Space>
);
const tabBishop = (
  <Space>
    <MedicineBoxOutlined />
    Score de Bishop
  </Space>
);
const tabIMC = (
  <Space>
    <UserOutlined />
    IMC
  </Space>
);
const tabPreeclampsia = (
  <Space>
    <WarningOutlined />
    Riesgo Preeclampsia
  </Space>
);
const tabDiabetesGestacional = (
  <Space>
    <LineChartOutlined />
    Diabetes Gestacional
  </Space>
);
const tabILA = (
  <Space>
    <ExperimentOutlined />
    Índice Líquido Amniótico
  </Space>
);
const tabPesoFetal = (
  <Space>
    <HeartOutlined />
    Peso Fetal
  </Space>
);
const tabApgar = (
  <Space>
    <HeartOutlined />
    Score de Apgar
  </Space>
);

interface ResultadoCalculo {
  valor: number | string;
  interpretacion: string;
  categoria: string;
  color: string;
  recomendaciones?: string[];
  alertas?: string[];
}

// ==========================================================================
// RESULTADO CARD COMPONENT (extracted from render-in-render)
// ==========================================================================
interface ResultadoCardProps {
  resultado: ResultadoCalculo;
}

const ResultadoCard: React.FC<ResultadoCardProps> = ({ resultado }) => (
  <Card
    style={{
      marginTop: 24,
      borderColor: resultado.color,
      borderWidth: 2,
    }}
  >
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Statistic
        title="Resultado"
        value={resultado.valor}
        valueStyle={{ color: resultado.color, fontSize: 36 }}
        prefix={<CalculatorOutlined />}
      />

      <Alert
        message={resultado.categoria}
        description={resultado.interpretacion}
        type={
          resultado.color === 'green'
            ? 'success'
            : resultado.color === 'red'
              ? 'error'
              : 'warning'
        }
        showIcon
      />

      {resultado.alertas && resultado.alertas.length > 0 && (
        <Alert
          message="⚠️ ALERTAS IMPORTANTES"
          description={
            <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
              {resultado.alertas.map((alerta) => (
                <li key={`alerta-${alerta}`}>
                  <strong>{alerta}</strong>
                </li>
              ))}
            </ul>
          }
          type="error"
          showIcon
          icon={<WarningOutlined />}
        />
      )}

      {resultado.recomendaciones && resultado.recomendaciones.length > 0 && (
        <Card
          type="inner"
          title={
            <Space>
              <BulbOutlined style={{ color: '#faad14' }} />
              Recomendaciones
              <Badge count={resultado.recomendaciones.length} showZero style={{ backgroundColor: '#52c41a' }} />
            </Space>
          }
        >
          <Timeline
            items={resultado.recomendaciones.map((rec) => ({
              key: `rec-${rec}`,
              color: resultado.color,
              dot: <CheckCircleOutlined />,
              children: (
                <Tooltip title="Recomendación basada en guías clínicas">
                  <Text>{rec}</Text>
                </Tooltip>
              )
            }))}
          />
        </Card>
      )}

      <Card type="inner">
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <InfoCircleOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            <Text strong>Notas del Cálculo</Text>
          </div>
          <Paragraph type="secondary">
            Este resultado ha sido calculado usando fórmulas médicas estándar.
            Siempre consulte con un profesional de salud para interpretación clínica.
          </Paragraph>

          <Divider>Guardar Preferencias</Divider>
          <Radio.Group defaultValue="metric">
            <Radio value="metric">Sistema Métrico</Radio>
            <Radio value="imperial">Sistema Imperial</Radio>
          </Radio.Group>

          <Divider>Agregar Notas</Divider>
          <Input.TextArea
            rows={2}
            placeholder="Notas adicionales sobre este cálculo..."
          />
        </Space>
      </Card>

      <Card type="inner" title="Historial Reciente">
        <Table
          size="small"
          dataSource={[
            { key: '1', fecha: dayjs().format('DD/MM/YYYY HH:mm'), valor: resultado.valor, categoria: resultado.categoria },
          ]}
          columns={[
            { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
            { title: 'Valor', dataIndex: 'valor', key: 'valor' },
            {
              title: 'Categoría',
              dataIndex: 'categoria',
              key: 'categoria',
              render: (cat: string) => <Badge status="processing" text={cat} />
            },
          ]}
          pagination={false}
        />
      </Card>
    </Space>
  </Card>
);

const CalculadorasAvanzadas: React.FC = () => {
  const [formEdadGestacional] = Form.useForm();
  const [formBishop] = Form.useForm();
  const [formIMC] = Form.useForm();
  const [formPreeclampsia] = Form.useForm();
  const [formDiabetes] = Form.useForm();
  const [formILA] = Form.useForm();
  const [formPesoFetal] = Form.useForm();
  const [formApgar] = Form.useForm();

  const [resultadoEdadGestacional, setResultadoEdadGestacional] =
    useState<ResultadoCalculo | null>(null);
  const [resultadoBishop, setResultadoBishop] = useState<ResultadoCalculo | null>(null);
  const [resultadoIMC, setResultadoIMC] = useState<ResultadoCalculo | null>(null);
  const [resultadoPreeclampsia, setResultadoPreeclampsia] =
    useState<ResultadoCalculo | null>(null);
  const [resultadoDiabetes, setResultadoDiabetes] = useState<ResultadoCalculo | null>(
    null
  );
  const [resultadoILA, setResultadoILA] = useState<ResultadoCalculo | null>(null);
  const [resultadoPesoFetal, setResultadoPesoFetal] = useState<ResultadoCalculo | null>(
    null
  );
  const [resultadoApgar, setResultadoApgar] = useState<ResultadoCalculo | null>(null);

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
      message.success('Score de Apgar calculado');
    } catch (error) {
      message.error('Error en el cálculo');
    }
  };

  // ==========================================================================
  // RENDER PRINCIPAL
  // ==========================================================================
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

        <Tabs defaultActiveKey="1" type="card">
          {/* TAB 1: EDAD GESTACIONAL */}
          <TabPane
            tab={tabEdadGestacional}
            key="1"
          >
            <Card type="inner" title="Calcular Edad Gestacional y FPP">
              <Form
                form={formEdadGestacional}
                layout="vertical"
                onFinish={calcularEdadGestacional}
              >
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="fum"
                      label="Fecha de Última Menstruación (FUM)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <DatePicker
                        style={{ width: '100%' }}
                        format="DD/MM/YYYY"
                        placeholder="Seleccione FUM"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="fecha_actual"
                      label="Fecha Actual (Opcional)"
                      tooltip="Si no se especifica, se usa la fecha de hoy"
                    >
                      <DatePicker
                        style={{ width: '100%' }}
                        format="DD/MM/YYYY"
                        placeholder="Fecha de cálculo"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular
                  </Button>
                </Form.Item>
              </Form>
              {resultadoEdadGestacional && <ResultadoCard resultado={resultadoEdadGestacional} />}
            </Card>
          </TabPane>

          {/* TAB 2: BISHOP */}
          <TabPane
            tab={tabBishop}
            key="2"
          >
            <Card type="inner" title="Evaluar Maduración Cervical">
              <Form form={formBishop} layout="vertical" onFinish={calcularBishop}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="dilatacion"
                      label="Dilatación Cervical"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Cerrado (0 puntos)</Option>
                        <Option value={1}>1-2 cm (1 punto)</Option>
                        <Option value={2}>3-4 cm (2 puntos)</Option>
                        <Option value={3}>≥5 cm (3 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="borramiento"
                      label="Borramiento Cervical"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>0-30% (0 puntos)</Option>
                        <Option value={1}>40-50% (1 punto)</Option>
                        <Option value={2}>60-70% (2 puntos)</Option>
                        <Option value={3}>≥80% (3 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="consistencia"
                      label="Consistencia Cervical"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Firme (0 puntos)</Option>
                        <Option value={1}>Media (1 punto)</Option>
                        <Option value={2}>Blanda (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="posicion"
                      label="Posición del Cérvix"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Posterior (0 puntos)</Option>
                        <Option value={1}>Media (1 punto)</Option>
                        <Option value={2}>Anterior (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="altura_presentacion"
                      label="Altura de la Presentación"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>-3 (0 puntos)</Option>
                        <Option value={1}>-2 (1 punto)</Option>
                        <Option value={2}>-1, 0 (2 puntos)</Option>
                        <Option value={3}>+1, +2 (3 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular Score
                  </Button>
                </Form.Item>
              </Form>
              {resultadoBishop && <ResultadoCard resultado={resultadoBishop} />}
            </Card>
          </TabPane>

          {/* TAB 3: IMC */}
          <TabPane
            tab={tabIMC}
            key="3"
          >
            <Card type="inner" title="Calcular Índice de Masa Corporal">
              <Form form={formIMC} layout="vertical" onFinish={calcularIMC}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="peso"
                      label="Peso (kg)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={30}
                        max={200}
                        placeholder="Ej: 65"
                        suffix="kg"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="altura"
                      label="Altura (cm)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={120}
                        max={220}
                        placeholder="Ej: 165"
                        suffix="cm"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular IMC
                  </Button>
                </Form.Item>
              </Form>
              {resultadoIMC && <ResultadoCard resultado={resultadoIMC} />}
            </Card>
          </TabPane>

          {/* TAB 4: PREECLAMPSIA */}
          <TabPane
            tab={tabPreeclampsia}
            key="4"
          >
            <Card type="inner" title="Evaluar Riesgo de Preeclampsia">
              <Form
                form={formPreeclampsia}
                layout="vertical"
                onFinish={calcularRiesgoPreeclampsia}
              >
                <Title level={5}>Factores de Alto Riesgo (2 puntos cada uno)</Title>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="preeclampsia_previa"
                      label="Preeclampsia en embarazo previo"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="hipertension_cronica"
                      label="Hipertensión crónica"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="diabetes_pregestacional"
                      label="Diabetes tipo 1 o 2"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="enfermedad_renal"
                      label="Enfermedad renal crónica"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />
                <Title level={5}>Factores de Riesgo Moderado (1 punto cada uno)</Title>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item name="edad" label="Edad de la paciente">
                      <InputNumber
                        style={{ width: '100%' }}
                        min={15}
                        max={60}
                        placeholder="Ej: 35"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="primiparidad"
                      label="Primiparidad (primer embarazo)"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="obesidad"
                      label="Obesidad (IMC ≥30)"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="embarazo_multiple"
                      label="Embarazo múltiple"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="intervalo_largo"
                      label="Intervalo >10 años entre embarazos"
                      valuePropName="checked"
                    >
                      <Switch />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Evaluar Riesgo
                  </Button>
                </Form.Item>
              </Form>
              {resultadoPreeclampsia && <ResultadoCard resultado={resultadoPreeclampsia} />}
            </Card>
          </TabPane>

          {/* TAB 5: DIABETES GESTACIONAL */}
          <TabPane
            tab={tabDiabetesGestacional}
            key="5"
          >
            <Card type="inner" title="Tamizaje de Diabetes Gestacional (CTOG 100g)">
              <Alert
                message="Curva de Tolerancia a la Glucosa Oral - 100g"
                description="Criterios de Carpenter-Coustan: Ayunas ≥95, 1h ≥180, 2h ≥155, 3h ≥140 mg/dL. Dos o más valores alterados confirman diagnóstico."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form
                form={formDiabetes}
                layout="vertical"
                onFinish={calcularDiabetesGestacional}
              >
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="glucosa_ayunas"
                      label="Glucosa en Ayunas (mg/dL)"
                      rules={[{ required: true, message: 'Requerido' }]}
                      tooltip="Valor normal: <95 mg/dL"
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={40}
                        max={400}
                        placeholder="Ej: 90"
                        suffix="mg/dL"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="glucosa_1h"
                      label="Glucosa a 1 hora (mg/dL)"
                      rules={[{ required: true, message: 'Requerido' }]}
                      tooltip="Valor normal: <180 mg/dL"
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={40}
                        max={400}
                        placeholder="Ej: 170"
                        suffix="mg/dL"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="glucosa_2h"
                      label="Glucosa a 2 horas (mg/dL)"
                      rules={[{ required: true, message: 'Requerido' }]}
                      tooltip="Valor normal: <155 mg/dL"
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={40}
                        max={400}
                        placeholder="Ej: 150"
                        suffix="mg/dL"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Evaluar Resultado
                  </Button>
                </Form.Item>
              </Form>
              {resultadoDiabetes && <ResultadoCard resultado={resultadoDiabetes} />}
            </Card>
          </TabPane>

          {/* TAB 6: ILA */}
          <TabPane
            tab={tabILA}
            key="6"
          >
            <Card type="inner" title="Calcular Índice de Líquido Amniótico (ILA)">
              <Alert
                message="Técnica de 4 Cuadrantes"
                description="Sume la medida del bolsillo vertical máximo de líquido amniótico en cada uno de los 4 cuadrantes uterinos."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form form={formILA} layout="vertical" onFinish={calcularILA}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="cuadrante1"
                      label="Cuadrante 1 (Sup. Derecho) cm"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        max={15}
                        step={0.1}
                        placeholder="Ej: 4.5"
                        suffix="cm"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="cuadrante2"
                      label="Cuadrante 2 (Sup. Izquierdo) cm"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        max={15}
                        step={0.1}
                        placeholder="Ej: 5.0"
                        suffix="cm"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="cuadrante3"
                      label="Cuadrante 3 (Inf. Derecho) cm"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        max={15}
                        step={0.1}
                        placeholder="Ej: 4.8"
                        suffix="cm"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="cuadrante4"
                      label="Cuadrante 4 (Inf. Izquierdo) cm"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={0}
                        max={15}
                        step={0.1}
                        placeholder="Ej: 4.2"
                        suffix="cm"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular ILA
                  </Button>
                </Form.Item>
              </Form>
              {resultadoILA && <ResultadoCard resultado={resultadoILA} />}
            </Card>
          </TabPane>

          {/* TAB 7: PESO FETAL */}
          <TabPane
            tab={tabPesoFetal}
            key="7"
          >
            <Card type="inner" title="Estimación de Peso Fetal (Fórmula de Hadlock)">
              <Alert
                message="Biometría Fetal Requerida"
                description="Se requieren las medidas de DBP (Diámetro Biparietal), CA (Circunferencia Abdominal) y LF (Longitud del Fémur) obtenidas por ecografía."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form form={formPesoFetal} layout="vertical" onFinish={calcularPesoFetal}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="edad_gestacional_semanas"
                      label="Semanas de Gestación"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={20}>20 semanas</Option>
                        <Option value={24}>24 semanas</Option>
                        <Option value={28}>28 semanas</Option>
                        <Option value={32}>32 semanas</Option>
                        <Option value={36}>36 semanas</Option>
                        <Option value={40}>40 semanas</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="dbp"
                      label="Diámetro Biparietal (mm)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={20}
                        max={120}
                        placeholder="Ej: 85"
                        suffix="mm"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="ca"
                      label="Circunferencia Abdominal (mm)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={50}
                        max={450}
                        placeholder="Ej: 280"
                        suffix="mm"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="lf"
                      label="Longitud del Fémur (mm)"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <InputNumber
                        style={{ width: '100%' }}
                        min={10}
                        max={90}
                        placeholder="Ej: 65"
                        suffix="mm"
                      />
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular Peso
                  </Button>
                </Form.Item>
              </Form>
              {resultadoPesoFetal && <ResultadoCard resultado={resultadoPesoFetal} />}
            </Card>
          </TabPane>

          {/* TAB 8: APGAR */}
          <TabPane
            tab={tabApgar}
            key="8"
          >
            <Card type="inner" title="Evaluar Score de Apgar del Recién Nacido">
              <Alert
                message="Evaluación Neonatal"
                description="El score de Apgar se evalúa al minuto y a los 5 minutos de vida. Evalúa 5 parámetros: FC, esfuerzo respiratorio, tono muscular, reflejos y color."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form form={formApgar} layout="vertical" onFinish={calcularApgar}>
                <Row gutter={16}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="frecuencia_cardiaca"
                      label="Frecuencia Cardíaca"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Ausente (0 puntos)</Option>
                        <Option value={1}>&lt;100 lpm (1 punto)</Option>
                        <Option value={2}>&gt;100 lpm (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="esfuerzo_respiratorio"
                      label="Esfuerzo Respiratorio"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Ausente (0 puntos)</Option>
                        <Option value={1}>Débil, irregular (1 punto)</Option>
                        <Option value={2}>Llanto fuerte (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="tono_muscular"
                      label="Tono Muscular"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Flácido (0 puntos)</Option>
                        <Option value={1}>Flexión de extremidades (1 punto)</Option>
                        <Option value={2}>Movimiento activo (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="reflejos"
                      label="Irritabilidad Refleja"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Sin respuesta (0 puntos)</Option>
                        <Option value={1}>Mueca (1 punto)</Option>
                        <Option value={2}>Llanto vigoroso (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="color"
                      label="Color de la Piel"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select placeholder="Seleccione">
                        <Option value={0}>Azul/pálido (0 puntos)</Option>
                        <Option value={1}>Cuerpo rosado, extremidades azules (1 punto)</Option>
                        <Option value={2}>Completamente rosado (2 puntos)</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
                <Form.Item>
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular Apgar
                  </Button>
                </Form.Item>
              </Form>
              {resultadoApgar && <ResultadoCard resultado={resultadoApgar} />}
            </Card>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default CalculadorasAvanzadas;
