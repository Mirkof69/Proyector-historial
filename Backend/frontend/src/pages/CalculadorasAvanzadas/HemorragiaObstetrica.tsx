import React, { useState } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Button,
  Row,
  Col,
  Statistic,
  Alert,
  Table,
  Tag,
  Select,
  Divider,
  Checkbox,
  Space
} from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ComposedChart, Area
} from 'recharts';
import {
  HeartOutlined,
  WarningOutlined,
  ThunderboltOutlined,
  MedicineBoxOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import './HemorragiaObstetrica.css';

const { Option } = Select;

// ============================================
// INTERFACES Y TIPOS
// ============================================

interface DatosHemorragia {
  // Signos vitales
  frecuencia_cardiaca: number;
  presion_sistolica: number;
  presion_diastolica: number;
  frecuencia_respiratoria: number;
  temperatura: number;
  saturacion_o2: number;

  // Pérdida sanguínea
  perdida_estimada_ml: number;
  tiempo_minutos: number;

  // Causa (4 T's)
  causa_principal: 'tono' | 'trauma' | 'tejido' | 'trombina';

  // Evaluación obstétrica
  tono_uterino: 'firme' | 'blando' | 'muy_blando';
  placenta_completa: boolean;
  laceraciones: boolean;
  coagulopatia: boolean;

  // Laboratorio
  hemoglobina_inicial: number;
  hemoglobina_actual: number;
  plaquetas: number;
  fibrinogeno: number;
}

interface ResultadoHemorragia {
  shock_index: number;
  clasificacion_shock: string;
  color_shock: string;
  gravedad: string;
  color_gravedad: string;
  porcentaje_perdida: number;
  volumen_compensar: number;

  // Estados clínicos
  estado_hemodinamico: string;
  riesgo_shock: string;
  requiere_ptm: boolean;

  // Recomendaciones
  medidas_inmediatas: string[];
  protocolo_ptm: {
    globulos_rojos: number;
    plasma: number;
    plaquetas: number;
    crioprecipitado: number;
  };
  intervenciones_sugeridas: string[];

  interpretacion: string;
}

interface RegistroHemorragia {
  fecha: string;
  shock_index: number;
  perdida_ml: number;
  gravedad: string;
  causa: string;
}

// ============================================
// FUNCIONES DE CÁLCULO
// ============================================

const calcularShockIndex = (fc: number, pas: number): number => {
  if (pas === 0) return 0;
  return fc / pas;
};

const clasificarShock = (si: number): { clase: string; color: string } => {
  if (si < 0.7) {
    return { clase: '✅ Normal', color: '#52c41a' };
  } else if (si < 0.9) {
    return { clase: '⚠️ Vigilancia', color: '#faad14' };
  } else if (si < 1.2) {
    return { clase: '🟠 Compensado', color: '#fa8c16' };
  } else if (si < 1.5) {
    return { clase: '🔴 Descompensado', color: '#ff4d4f' };
  } else {
    return { clase: '🚨 CRÍTICO', color: '#a8071a' };
  }
};

const clasificarGravedad = (perdida_ml: number): { gravedad: string; color: string } => {
  if (perdida_ml < 500) {
    return { gravedad: 'Leve', color: '#52c41a' };
  } else if (perdida_ml < 1000) {
    return { gravedad: 'Moderada', color: '#faad14' };
  } else if (perdida_ml < 1500) {
    return { gravedad: 'Severa', color: '#ff4d4f' };
  } else {
    return { gravedad: 'Masiva', color: '#a8071a' };
  }
};

const calcularHemorragia = (valores: DatosHemorragia): ResultadoHemorragia => {
  // Calcular Shock Index
  const shock_index = calcularShockIndex(valores.frecuencia_cardiaca, valores.presion_sistolica);
  const { clase: clasificacion_shock, color: color_shock } = clasificarShock(shock_index);

  // Clasificar gravedad por volumen
  const { gravedad, color: color_gravedad } = clasificarGravedad(valores.perdida_estimada_ml);

  // Estimar volemia total (aproximadamente 70 ml/kg en mujeres, asumiendo 60 kg promedio)
  const volemia_total = 4200; // ml
  const porcentaje_perdida = (valores.perdida_estimada_ml / volemia_total) * 100;

  // Volumen a compensar (1.5-3x la pérdida dependiendo severidad)
  let factor_reemplazo = 1.5;
  if (valores.perdida_estimada_ml > 1500) factor_reemplazo = 3.0;
  else if (valores.perdida_estimada_ml > 1000) factor_reemplazo = 2.5;
  else if (valores.perdida_estimada_ml > 500) factor_reemplazo = 2.0;

  const volumen_compensar = valores.perdida_estimada_ml * factor_reemplazo;

  // Evaluar estado hemodinámico
  let estado_hemodinamico = 'Estable';
  if (shock_index > 1.2 || valores.presion_sistolica < 90) {
    estado_hemodinamico = 'Inestable - CRÍTICO';
  } else if (shock_index > 0.9 || valores.presion_sistolica < 100) {
    estado_hemodinamico = 'Compensado';
  }

  // Evaluar riesgo de shock
  let riesgo_shock = 'Bajo';
  if (shock_index > 1.5 || porcentaje_perdida > 40) {
    riesgo_shock = 'Shock Hemorrágico ESTABLECIDO';
  } else if (shock_index > 1.2 || porcentaje_perdida > 30) {
    riesgo_shock = 'Alto - Inminente';
  } else if (shock_index > 0.9 || porcentaje_perdida > 20) {
    riesgo_shock = 'Moderado';
  }

  // Determinar si requiere Protocolo de Transfusión Masiva (PTM)
  const requiere_ptm = valores.perdida_estimada_ml > 1500 ||
                       shock_index > 1.5 ||
                       porcentaje_perdida > 30 ||
                       (valores.coagulopatia && valores.perdida_estimada_ml > 1000);

  // Protocolo PTM - Ratio 1:1:1 (GR:PFC:Plaq)
  let protocolo_ptm = {
    globulos_rojos: 0,
    plasma: 0,
    plaquetas: 0,
    crioprecipitado: 0
  };

  if (requiere_ptm) {
    // Unidades estimadas basadas en pérdida
    const unidades_base = Math.ceil(valores.perdida_estimada_ml / 500);
    protocolo_ptm = {
      globulos_rojos: unidades_base * 2, // Concentrados eritrocitarios
      plasma: unidades_base * 2, // Plasma fresco congelado
      plaquetas: unidades_base, // Unidades de plaquetas
      crioprecipitado: valores.fibrinogeno < 150 ? 10 : 0 // Si fibrinógeno bajo
    };
  }

  // Medidas inmediatas según 4 T's
  const medidas_inmediatas: string[] = [];

  // Medidas generales
  medidas_inmediatas.push('🔴 ACTIVAR CÓDIGO ROJO - Equipo multidisciplinario');
  medidas_inmediatas.push('💉 Dos accesos IV calibre 14-16G');
  medidas_inmediatas.push('📊 Laboratorios STAT: BHC, TP/TPT, Fibrinógeno, Gasometría');

  // Específicas por causa (4 T's)
  switch (valores.causa_principal) {
    case 'tono':
      medidas_inmediatas.push('🤲 TONO: Masaje uterino bimanual vigoroso');
      medidas_inmediatas.push('💊 Oxitocina 20-40 UI en 1000ml SSN a goteo rápido');
      if (valores.tono_uterino === 'muy_blando') {
        medidas_inmediatas.push('💉 Metilergonovina 0.2mg IM (si no HTA)');
        medidas_inmediatas.push('🧪 Misoprostol 800-1000 mcg rectal');
        medidas_inmediatas.push('⚠️ Considerar: Carboprost 250mcg IM c/15min (máx 8 dosis)');
      }
      break;

    case 'trauma':
      medidas_inmediatas.push('🔍 TRAUMA: Inspección cervical/vaginal/perineal minuciosa');
      medidas_inmediatas.push('🪡 Sutura inmediata de laceraciones identificadas');
      if (valores.laceraciones) {
        medidas_inmediatas.push('⚠️ Evaluar lesiones de tracto genital alto');
        medidas_inmediatas.push('🏥 Considerar revisión quirúrgica si sangrado persiste');
      }
      break;

    case 'tejido':
      medidas_inmediatas.push('🧪 TEJIDO: Revisión de cavidad uterina');
      if (!valores.placenta_completa) {
        medidas_inmediatas.push('🤚 Extracción manual de restos placentarios');
        medidas_inmediatas.push('💊 Antibióticos profilácticos');
        medidas_inmediatas.push('📋 Enviar placenta a patología si anormal');
      }
      medidas_inmediatas.push('🔍 Descartar acretismo placentario');
      break;

    case 'trombina':
      medidas_inmediatas.push('🩸 TROMBINA: Manejo de coagulopatía');
      if (valores.coagulopatia) {
        medidas_inmediatas.push('💉 Ácido tranexámico 1g IV en 10 min, luego 1g en 8h');
        medidas_inmediatas.push('🧊 Crioprecipitado 10 U si fibrinógeno <150 mg/dL');
        medidas_inmediatas.push('🩸 PFC 4 unidades si TP/TPT >1.5x normal');
      }
      medidas_inmediatas.push('🔬 Laboratorios cada 30-60 min');
      break;
  }

  // Medidas según gravedad
  if (valores.perdida_estimada_ml > 1000) {
    medidas_inmediatas.push('🩸 Transfusión: Iniciar GR O negativo si no tipificada');
  }

  if (requiere_ptm) {
    medidas_inmediatas.push('🚨 ACTIVAR PROTOCOLO DE TRANSFUSIÓN MASIVA');
    medidas_inmediatas.push('🏥 Avisar a Banco de Sangre - Transfusión continua');
  }

  // Intervenciones sugeridas (escalonadas)
  const intervenciones_sugeridas: string[] = [];

  if (valores.perdida_estimada_ml < 1000) {
    intervenciones_sugeridas.push('1️⃣ Medidas médicas (uterotónicos, ácido tranexámico)');
    intervenciones_sugeridas.push('2️⃣ Reposición con cristaloides');
  } else if (valores.perdida_estimada_ml < 1500) {
    intervenciones_sugeridas.push('1️⃣ Uterotónicos en dosis máximas');
    intervenciones_sugeridas.push('2️⃣ Taponamiento con balón intrauterino (Bakri)');
    intervenciones_sugeridas.push('3️⃣ Considerar suturas hemostáticas (B-Lynch, Cho)');
    intervenciones_sugeridas.push('4️⃣ Transfusión según protocolo');
  } else {
    intervenciones_sugeridas.push('1️⃣ MÁXIMAS medidas médicas');
    intervenciones_sugeridas.push('2️⃣ Taponamiento Bakri + Suturas compresivas');
    intervenciones_sugeridas.push('3️⃣ Embolización arterial selectiva si disponible');
    intervenciones_sugeridas.push('4️⃣ Ligadura arterias uterinas/hipogástricas');
    intervenciones_sugeridas.push('5️⃣ Histerectomía obstétrica si falla lo anterior');
    intervenciones_sugeridas.push('⚠️ LLAMAR A CIRUGÍA GENERAL Y RADIOLOGÍA INTERVENCIONISTA');
  }

  // Interpretación
  let interpretacion = `Hemorragia obstétrica ${gravedad.toUpperCase()} con pérdida estimada de ${valores.perdida_estimada_ml} ml `;
  interpretacion += `(${porcentaje_perdida.toFixed(1)}% de volemia). `;
  interpretacion += `Shock Index: ${shock_index.toFixed(2)} (${clasificacion_shock}). `;
  interpretacion += `Estado hemodinámico: ${estado_hemodinamico}. `;

  if (requiere_ptm) {
    interpretacion += `\n\n🚨 CUMPLE CRITERIOS PARA PROTOCOLO DE TRANSFUSIÓN MASIVA. `;
    interpretacion += `Se requiere transfusión agresiva con ratio 1:1:1 y manejo multidisciplinario urgente.`;
  }

  interpretacion += `\n\nCausa principal identificada: ${getCausaTexto(valores.causa_principal)}. `;
  interpretacion += `Se recomienda manejo escalonado según respuesta clínica.`;

  if (shock_index > 1.5) {
    interpretacion += `\n\n⚠️ PACIENTE EN ESTADO CRÍTICO - Shock hemorrágico establecido. Requiere reanimación agresiva inmediata.`;
  }

  return {
    shock_index,
    clasificacion_shock,
    color_shock,
    gravedad,
    color_gravedad,
    porcentaje_perdida,
    volumen_compensar,
    estado_hemodinamico,
    riesgo_shock,
    requiere_ptm,
    medidas_inmediatas,
    protocolo_ptm,
    intervenciones_sugeridas,
    interpretacion
  };
};

const getCausaTexto = (causa: string): string => {
  const causas: { [key: string]: string } = {
    'tono': 'TONO - Atonía uterina (70% de HPP)',
    'trauma': 'TRAUMA - Laceraciones/Desgarros',
    'tejido': 'TEJIDO - Retención placentaria',
    'trombina': 'TROMBINA - Coagulopatía'
  };
  return causas[causa] || causa;
};

// ============================================
// COMPONENTE PRINCIPAL
// ============================================

const renderVolemiaLabel = (props: any) => {
  const { name, value } = props;
  return `${name}: ${value.toFixed(1)}%`;
};
const HISTORIAL_TICK = { fontSize: 12 };
const SHOCK_INDEX_LABEL = { value: 'Shock Index', angle: -90, position: 'insideLeft' };
const PERDIDA_LABEL = { value: 'Pérdida (ml)', angle: 90, position: 'insideRight' };

const getDataCausas4T = () => [
  { causa: 'TONO\nAtonía', porcentaje: 70, color: '#ff4d4f' },
  { causa: 'TRAUMA\nLaceraciones', porcentaje: 20, color: '#fa8c16' },
  { causa: 'TEJIDO\nRetención', porcentaje: 8, color: '#faad14' },
  { causa: 'TROMBINA\nCoagulopatía', porcentaje: 2, color: '#722ed1' },
];

const HemorragiaObstetrica: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoHemorragia | null>(null);
  const [historial, setHistorial] = useState<RegistroHemorragia[]>([]);
  const [loading, setLoading] = useState(false);

  const onFinish = (valores: any) => {
    setLoading(true);

    const datos: DatosHemorragia = {
      frecuencia_cardiaca: valores.frecuencia_cardiaca,
      presion_sistolica: valores.presion_sistolica,
      presion_diastolica: valores.presion_diastolica,
      frecuencia_respiratoria: valores.frecuencia_respiratoria,
      temperatura: valores.temperatura,
      saturacion_o2: valores.saturacion_o2,
      perdida_estimada_ml: valores.perdida_estimada_ml,
      tiempo_minutos: valores.tiempo_minutos,
      causa_principal: valores.causa_principal,
      tono_uterino: valores.tono_uterino,
      placenta_completa: valores.placenta_completa ?? false,
      laceraciones: valores.laceraciones ?? false,
      coagulopatia: valores.coagulopatia ?? false,
      hemoglobina_inicial: valores.hemoglobina_inicial,
      hemoglobina_actual: valores.hemoglobina_actual,
      plaquetas: valores.plaquetas,
      fibrinogeno: valores.fibrinogeno
    };

    const res = calcularHemorragia(datos);
    setResultado(res);

    // Agregar al historial
    const nuevoRegistro: RegistroHemorragia = {
      fecha: new Date().toLocaleString('es-ES'),
      shock_index: res.shock_index,
      perdida_ml: valores.perdida_estimada_ml,
      gravedad: res.gravedad,
      causa: getCausaTexto(valores.causa_principal)
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);

    setLoading(false);
  };

  // ============================================
  // DATOS PARA GRÁFICAS
  // ============================================


  const getDataDistribucion = () => {
    if (!resultado) return [];

    return [
      { name: 'Pérdida Actual', value: resultado.porcentaje_perdida, color: resultado.color_gravedad },
      { name: 'Volemia Restante', value: 100 - resultado.porcentaje_perdida, color: '#95de64' }
    ];
  };

  const getDataSignosVitales = () => {
    const valores = form.getFieldsValue();
    return [
      {
        parametro: 'FC',
        valor: valores.frecuencia_cardiaca || 0,
        normal_min: 60,
        normal_max: 100,
        referencia: 80
      },
      {
        parametro: 'PAS',
        valor: valores.presion_sistolica || 0,
        normal_min: 90,
        normal_max: 140,
        referencia: 120
      },
      {
        parametro: 'PAD',
        valor: valores.presion_diastolica || 0,
        normal_min: 60,
        normal_max: 90,
        referencia: 80
      },
      {
        parametro: 'FR',
        valor: valores.frecuencia_respiratoria || 0,
        normal_min: 12,
        normal_max: 20,
        referencia: 16
      }
    ];
  };

  const getDataPTM = () => {
    if (!resultado || !resultado.requiere_ptm) return [];

    return [
      { componente: 'GR', unidades: resultado.protocolo_ptm.globulos_rojos, color: '#ff4d4f' },
      { componente: 'PFC', unidades: resultado.protocolo_ptm.plasma, color: '#faad14' },
      { componente: 'Plaq', unidades: resultado.protocolo_ptm.plaquetas, color: '#1890ff' },
      { componente: 'Crio', unidades: resultado.protocolo_ptm.crioprecipitado, color: '#722ed1' }
    ];
  };

  const columnasHistorial = [
    {
      title: 'Fecha/Hora',
      dataIndex: 'fecha',
      key: 'fecha'
    },
    {
      title: 'Shock Index',
      dataIndex: 'shock_index',
      key: 'shock_index',
      render: (si: number) => si.toFixed(2)
    },
    {
      title: 'Pérdida (ml)',
      dataIndex: 'perdida_ml',
      key: 'perdida_ml'
    },
    {
      title: 'Gravedad',
      dataIndex: 'gravedad',
      key: 'gravedad',
      render: (gravedad: string) => {
        let color = 'green';
        if (gravedad === 'Severa') color = 'red';
        else if (gravedad === 'Masiva') color = 'volcano';
        else if (gravedad === 'Moderada') color = 'orange';
        return <Tag color={color}>{gravedad}</Tag>;
      }
    },
    {
      title: 'Causa',
      dataIndex: 'causa',
      key: 'causa'
    }
  ];



  return (
    <div className="hemorragia-obstetrica-page">
      <Card
        title={
          <span>
            <HeartOutlined style={{ marginRight: 8, color: '#ff4d4f' }} />
            Evaluación de Hemorragia Obstétrica
          </span>
        }
      >
        <Alert
          message="Protocolo 4 T's para Hemorragia Postparto"
          description="Evaluación sistemática: TONO (atonía), TRAUMA (laceraciones), TEJIDO (retención), TROMBINA (coagulopatía). Incluye Shock Index y Protocolo de Transfusión Masiva."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            frecuencia_cardiaca: 80,
            presion_sistolica: 120,
            presion_diastolica: 80,
            frecuencia_respiratoria: 16,
            temperatura: 36.5,
            saturacion_o2: 98,
            perdida_estimada_ml: 500,
            tiempo_minutos: 30,
            causa_principal: 'tono',
            tono_uterino: 'firme',
            placenta_completa: true,
            laceraciones: false,
            coagulopatia: false,
            hemoglobina_inicial: 12,
            hemoglobina_actual: 11,
            plaquetas: 200000,
            fibrinogeno: 350
          }}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Divider orientation="left">Signos Vitales</Divider>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Frecuencia Cardíaca (lpm)"
                name="frecuencia_cardiaca"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={40} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Presión Sistólica (mmHg)"
                name="presion_sistolica"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={50} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Presión Diastólica (mmHg)"
                name="presion_diastolica"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={30} max={120} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Frecuencia Respiratoria (rpm)"
                name="frecuencia_respiratoria"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={8} max={40} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Temperatura (°C)"
                name="temperatura"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={34} max={42} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={8}>
              <Form.Item
                label="Saturación O₂ (%)"
                name="saturacion_o2"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={70} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Divider orientation="left">Pérdida Sanguínea</Divider>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item
                label="Pérdida Estimada (ml)"
                name="perdida_estimada_ml"
                rules={[{ required: true, message: 'Requerido' }]}
                tooltip="Volumen total estimado de sangre perdida"
              >
                <InputNumber min={0} max={5000} step={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item
                label="Tiempo desde inicio (minutos)"
                name="tiempo_minutos"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={0} max={360} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Divider orientation="left">Evaluación Obstétrica (4 T's)</Divider>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item
                label="Causa Principal Sospechada"
                name="causa_principal"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Select>
                  <Option value="tono">🔴 TONO - Atonía Uterina (70%)</Option>
                  <Option value="trauma">🟠 TRAUMA - Laceraciones/Desgarros (20%)</Option>
                  <Option value="tejido">🟡 TEJIDO - Retención Placentaria (8%)</Option>
                  <Option value="trombina">🟣 TROMBINA - Coagulopatía (2%)</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={12}>
              <Form.Item
                label="Tono Uterino"
                name="tono_uterino"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Select>
                  <Option value="firme">✅ Firme (bien contraído)</Option>
                  <Option value="blando">⚠️ Blando</Option>
                  <Option value="muy_blando">🔴 Muy Blando (atónico)</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col xs={24} sm={8}>
              <Form.Item name="placenta_completa" valuePropName="checked">
                <Checkbox>Placenta Completa</Checkbox>
              </Form.Item>
            </Col>

            <Col xs={24} sm={8}>
              <Form.Item name="laceraciones" valuePropName="checked">
                <Checkbox>Laceraciones Identificadas</Checkbox>
              </Form.Item>
            </Col>

            <Col xs={24} sm={8}>
              <Form.Item name="coagulopatia" valuePropName="checked">
                <Checkbox>Coagulopatía Presente</Checkbox>
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Divider orientation="left">Laboratorios</Divider>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label="Hb Inicial (g/dL)"
                name="hemoglobina_inicial"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={5} max={18} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label="Hb Actual (g/dL)"
                name="hemoglobina_actual"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={3} max={18} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label="Plaquetas (/μL)"
                name="plaquetas"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={10000} max={500000} step={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Form.Item
                label="Fibrinógeno (mg/dL)"
                name="fibrinogeno"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={50} max={600} style={{ width: '100%' }} />
              </Form.Item>
            </Col>

            <Col xs={24}>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block size="large">
                  <ThunderboltOutlined /> Evaluar Hemorragia
                </Button>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {resultado && (
        <>
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Shock Index"
                  value={resultado.shock_index.toFixed(2)}
                  valueStyle={{ color: resultado.color_shock }}
                  prefix={<HeartOutlined />}
                  suffix={resultado.clasificacion_shock}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Gravedad"
                  value={resultado.gravedad}
                  valueStyle={{ color: resultado.color_gravedad }}
                  prefix={<WarningOutlined />}
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Pérdida de Volemia"
                  value={resultado.porcentaje_perdida.toFixed(1)}
                  valueStyle={{ color: resultado.porcentaje_perdida > 30 ? '#ff4d4f' : '#faad14' }}
                  suffix="%"
                />
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="Volumen a Reponer"
                  value={resultado.volumen_compensar.toFixed(0)}
                  valueStyle={{ color: '#1890ff' }}
                  suffix="ml"
                  prefix={<MedicineBoxOutlined />}
                />
              </Card>
            </Col>
          </Row>

          <Card title="Interpretación Clínica" style={{ marginTop: 16 }}>
            <Alert
              message={`Estado: ${resultado.estado_hemodinamico} | Riesgo de Shock: ${resultado.riesgo_shock}`}
              description={resultado.interpretacion}
              type={resultado.shock_index > 1.2 ? 'error' : resultado.shock_index > 0.9 ? 'warning' : 'success'}
              showIcon
            />
          </Card>

          {resultado.requiere_ptm && (
            <Card
              title={
                <span style={{ color: '#ff4d4f' }}>
                  🚨 PROTOCOLO DE TRANSFUSIÓN MASIVA (PTM) ACTIVADO
                </span>
              }
              style={{ marginTop: 16 }}
            >
              <Alert
                message="CRITERIOS CUMPLIDOS PARA PTM"
                description="Transfusión agresiva necesaria. Ratio 1:1:1 (GR:PFC:Plaq). Contactar Banco de Sangre INMEDIATAMENTE."
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Glóbulos Rojos"
                    value={resultado.protocolo_ptm.globulos_rojos}
                    suffix="unidades"
                    valueStyle={{ color: '#ff4d4f' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Plasma Fresco"
                    value={resultado.protocolo_ptm.plasma}
                    suffix="unidades"
                    valueStyle={{ color: '#faad14' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Plaquetas"
                    value={resultado.protocolo_ptm.plaquetas}
                    suffix="unidades"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Statistic
                    title="Crioprecipitado"
                    value={resultado.protocolo_ptm.crioprecipitado}
                    suffix="unidades"
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          <Card title="🚨 Medidas Inmediatas" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {resultado.medidas_inmediatas.map((medida) => (
                <Alert
                  key={`medida-${medida}`}
                  message={medida}
                  type={medida.includes('🚨') || medida.includes('🔴') ? 'error' : 'warning'}
                  showIcon
                />
              ))}
            </Space>
          </Card>

          <Card title="📋 Intervenciones Escalonadas" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {resultado.intervenciones_sugeridas.map((intervencion) => (
                <Alert
                  key={`interv-${intervencion}`}
                  message={intervencion}
                  type="info"
                  showIcon
                />
              ))}
            </Space>
          </Card>

          <Divider>
            <LineChartOutlined /> Análisis Gráfico
          </Divider>
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Distribución de Causas HPP (4 T's)">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={getDataCausas4T()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="causa" />
                    <YAxis label={{ value: 'Frecuencia (%)', angle: -90, position: 'insideLeft' }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="porcentaje" name="Frecuencia (%)">
                      {getDataCausas4T().map((entry: any) => (
                        <Cell key={`cell-${entry.causa}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Pérdida de Volemia">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={getDataDistribucion()}
                      label={renderVolemiaLabel}
                      outerRadius={100}
                      dataKey="value"
                    >
                      {getDataDistribucion().map((entry: any) => (
                        <Cell key={`cell-${entry.name}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            <Col xs={24} lg={12}>
              <Card title="Signos Vitales vs Valores Normales">
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={getDataSignosVitales()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="parametro" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="valor" fill="#ff4d4f" name="Valor Actual" />
                    <Line type="monotone" dataKey="referencia" stroke="#52c41a" name="Referencia" strokeWidth={2} />
                    <Area type="monotone" dataKey="normal_max" fill="#95de64" stroke="#95de64" fillOpacity={0.3} name="Rango Normal" />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            {resultado && resultado.requiere_ptm && (
              <Col xs={24} lg={12}>
                <Card title="Protocolo PTM - Componentes">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={getDataPTM()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="componente" />
                      <YAxis label={{ value: 'Unidades', angle: -90, position: 'insideLeft' }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="unidades" name="Unidades">
                        {getDataPTM().map((entry: any) => (
                          <Cell key={`cell-${entry.componente}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            )}
          </Row>

          {historial.length > 0 && (
            <Card title="Historial de Evaluaciones" style={{ marginTop: 16 }}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={[...historial].reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" tick={HISTORIAL_TICK} />
                  <YAxis yAxisId="left" label={SHOCK_INDEX_LABEL} />
                  <YAxis yAxisId="right" orientation="right" label={PERDIDA_LABEL} />
                  <Tooltip />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="shock_index" stroke="#ff4d4f" name="Shock Index" strokeWidth={2} />
                  <Line yAxisId="right" type="monotone" dataKey="perdida_ml" stroke="#1890ff" name="Pérdida (ml)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>

              <Table
                columns={columnasHistorial}
                dataSource={historial}
                rowKey={(record) => record.fecha}
                pagination={{ pageSize: 5 }}
                size="small"
                style={{ marginTop: 16 }}
              />
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default HemorragiaObstetrica;
