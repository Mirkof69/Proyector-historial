/**
 * =============================================================================
 * 15 CALCULADORAS FMF - FETAL MEDICINE FOUNDATION
 * =============================================================================
 */

import React, { useState } from 'react';
import {
  Card, Tabs, Form, Input, InputNumber, Button, Select, Space, message,
  Row, Col, Typography, Alert, Divider, Descriptions, Tag,
} from 'antd';
import {
  CalculatorOutlined, HeartOutlined, ExperimentOutlined,
  WarningOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import { calculadorasService } from '../services/calculadorasService';

const { TabPane } = Tabs;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const CalculadorasNew: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<any>(null);
  const [form] = Form.useForm();

  const handleCalcular = async (calculadora: string, values: any) => {
    setLoading(true);
    setResultado(null);
    try {
      let res;
      switch (calculadora) {
        case 'preeclampsia':
          res = await calculadorasService.preeclampsia(values);
          break;
        case 'trisomias':
          res = await calculadorasService.trisomias(values);
          break;
        case 'sga':
          res = await calculadorasService.sga(values);
          break;
        case 'diabetes':
          res = await calculadorasService.diabetesGestacional(values);
          break;
        case 'parto_pretermino':
          res = await calculadorasService.partoPretermino(values);
          break;
        case 'peso_fetal':
          res = await calculadorasService.pesoFetal(values);
          break;
        case 'translucencia':
          res = await calculadorasService.translucenciaNucal(values);
          break;
        case 'doppler':
          res = await calculadorasService.dopplerFetal(values);
          break;
        case 'pam':
          res = await calculadorasService.presionArterialMedia(values);
          break;
        case 'biomarcadores':
          res = await calculadorasService.biomarcadores(values);
          break;
        case 'indice_shock':
          res = await calculadorasService.indiceShock(values);
          break;
        case 'nst':
          res = await calculadorasService.testNoEstresante(values);
          break;
        default:
          throw new Error('Calculadora no encontrada');
      }
      setResultado(res);
      message.success('Cálculo realizado correctamente');
    } catch (error: any) {
      message.error(error.message || 'Error al realizar el cálculo');
    } finally {
      setLoading(false);
    }
  };

  const renderResultado = () => {
    if (!resultado) return null;

    return (
      <Card
        title={
          <Space>
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
            <Text strong>Resultado del Cálculo</Text>
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Descriptions column={1} bordered>
          {Object.entries(resultado).map(([key, value]: [string, any]) => (
            <Descriptions.Item label={key.replace(/_/g, ' ').toUpperCase()} key={key}>
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>
    );
  };

  return (
    <div>
      <Card
        title={
          <Space>
            <CalculatorOutlined style={{ fontSize: 24 }} />
            <Title level={3} style={{ margin: 0 }}>
              Calculadoras FMF - Fetal Medicine Foundation
            </Title>
          </Space>
        }
      >
        <Paragraph>
          Herramientas clínicas validadas por la Fetal Medicine Foundation para evaluación de riesgos
          durante el embarazo.
        </Paragraph>

        <Tabs defaultActiveKey="1" type="card">
          {/* 1. PREECLAMPSIA */}
          <TabPane tab="Preeclampsia" key="1">
            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => handleCalcular('preeclampsia', values)}
            >
              <Alert
                message="Predicción de Preeclampsia - Primer Trimestre"
                description="Algoritmo FMF para calcular el riesgo de preeclampsia basado en características maternas y biomarcadores."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="edad_materna"
                    label="Edad Materna (años)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={15} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="peso" label="Peso (kg)" rules={[{ required: true }]}>
                    <InputNumber min={30} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="talla" label="Talla (cm)" rules={[{ required: true }]}>
                    <InputNumber min={120} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="pam" label="PAM (mmHg)" rules={[{ required: true }]}>
                    <InputNumber min={60} max={150} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="ip_uterinas_promedio"
                    label="IP Uterinas (promedio)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={5} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="eg_semanas" label="EG (semanas)" rules={[{ required: true }]}>
                    <InputNumber min={11} max={14} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="plgf" label="PlGF (pg/ml)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Calcular Riesgo de Preeclampsia
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 2. TRISOMÍAS */}
          <TabPane tab="Trisomías 21/18/13" key="2">
            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => handleCalcular('trisomias', values)}
            >
              <Alert
                message="Screening de Trisomías - Primer Trimestre"
                description="Cálculo de riesgo para trisomías 21, 18 y 13 basado en marcadores bioquímicos y ecográficos."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="edad_materna" label="Edad Materna" rules={[{ required: true }]}>
                    <InputNumber min={15} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="eg_semanas" label="EG (semanas)" rules={[{ required: true }]}>
                    <InputNumber min={11} max={14} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="nt_mm"
                    label="Translucencia Nucal (mm)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0.5} max={10} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="papp_a_mom"
                    label="PAPP-A (MoM)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0.01} max={10} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="beta_hcg_mom"
                    label="β-hCG (MoM)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0.01} max={20} step={0.01} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="hueso_nasal_presente"
                    label="Hueso Nasal"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={true}>Presente</Option>
                      <Option value={false}>Ausente</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Calcular Riesgo de Trisomías
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 3. PARTO PRETÉRMINO */}
          <TabPane tab="Parto Pretérmino" key="3">
            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => handleCalcular('parto_pretermino', values)}
            >
              <Alert
                message="Predicción de Parto Pretérmino"
                description="Evaluación del riesgo basada en longitud cervical y antecedentes."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="edad_materna" label="Edad Materna" rules={[{ required: true }]}>
                    <InputNumber min={15} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="paridad" label="Paridad" rules={[{ required: true }]}>
                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="parto_pretermino_previo"
                    label="¿Parto Pretérmino Previo?"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={true}>Sí</Option>
                      <Option value={false}>No</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="eg_parto_previo" label="EG del Parto Previo">
                    <InputNumber min={20} max={37} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="embarazo_multiple"
                    label="¿Embarazo Múltiple?"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value={true}>Sí</Option>
                      <Option value={false}>No</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="longitud_cervical"
                    label="Longitud Cervical (mm)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={70} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="eg_medicion" label="EG Medición" rules={[{ required: true }]}>
                <InputNumber min={16} max={24} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Calcular Riesgo de Parto Pretérmino
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 4. PESO FETAL */}
          <TabPane tab="Peso Fetal" key="4">
            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => handleCalcular('peso_fetal', values)}
            >
              <Alert
                message="Estimación de Peso Fetal"
                description="Cálculo mediante fórmula de Hadlock basada en biometrías fetales."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="dbp"
                    label="Diámetro Biparietal (mm)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={10} max={120} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="ca"
                    label="Circunferencia Abdominal (mm)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={50} max={500} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="fl" label="Longitud Femoral (mm)" rules={[{ required: true }]}>
                    <InputNumber min={10} max={90} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="hc" label="Circunferencia Cefálica (mm)">
                    <InputNumber min={50} max={400} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item name="eg_semanas" label="EG (semanas)" rules={[{ required: true }]}>
                <InputNumber min={12} max={42} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Calcular Peso Fetal Estimado
                </Button>
              </Form.Item>
            </Form>
          </TabPane>

          {/* 5. TEST NO ESTRESANTE (NST) */}
          <TabPane tab="Test No Estresante" key="5">
            <Form
              form={form}
              layout="vertical"
              onFinish={(values) => handleCalcular('nst', values)}
            >
              <Alert
                message="Test No Estresante (NST)"
                description="Evaluación del bienestar fetal mediante análisis de la frecuencia cardíaca fetal."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="fcf_basal" label="FCF Basal (lpm)" rules={[{ required: true }]}>
                    <InputNumber min={90} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="aceleraciones"
                    label="N° de Aceleraciones"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={20} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="variabilidad"
                    label="Variabilidad (lpm)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={0} max={50} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="desaceleraciones"
                    label="Tipo de Desaceleraciones"
                    rules={[{ required: true }]}
                  >
                    <Select>
                      <Option value="ninguna">Ninguna</Option>
                      <Option value="variables">Variables</Option>
                      <Option value="tardias">Tardías</Option>
                      <Option value="prolongadas">Prolongadas</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="duracion_minutos"
                    label="Duración (min)"
                    rules={[{ required: true }]}
                  >
                    <InputNumber min={10} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="eg_semanas" label="EG (semanas)" rules={[{ required: true }]}>
                    <InputNumber min={26} max={42} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  Evaluar Test No Estresante
                </Button>
              </Form.Item>
            </Form>
          </TabPane>
        </Tabs>

        {renderResultado()}
      </Card>
    </div>
  );
};

export default CalculadorasNew;
