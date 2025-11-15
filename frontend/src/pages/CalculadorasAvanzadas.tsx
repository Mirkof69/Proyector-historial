/**
 * =============================================================================
 * PÁGINA DE CALCULADORAS AVANZADAS
 * =============================================================================
 * Calculadoras médicas especializadas para obstetricia
 * =============================================================================
 */

import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  InputNumber,
  Button,
  Select,
  Checkbox,
  Divider,
  Alert,
  Descriptions,
  Space,
  message,
  Tabs,
  DatePicker,
  Statistic,
  Tag,
} from 'antd';
import {
  CalculatorOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  LineChartOutlined,
  FundOutlined,
} from '@ant-design/icons';
import calculadorasAvanzadasService from '../services/calculadorasAvanzadasService';

const { Option } = Select;
const { TabPane } = Tabs;

const CalculadorasAvanzadas: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [resultado, setResultado] = useState<any>(null);
  const [activeCalculator, setActiveCalculator] = useState<string>('cardiovascular');

  const [formCardiovascular] = Form.useForm();
  const [formTromboembolia] = Form.useForm();
  const [formDosisMedicamento] = Form.useForm();
  const [formRiesgoPrematuro] = Form.useForm();
  const [formCrecimientoFetal] = Form.useForm();
  const [formIndiceResistencia] = Form.useForm();
  const [formEdadGestacional] = Form.useForm();
  const [formPercentiles] = Form.useForm();
  const [formPerfilBiofisico] = Form.useForm();
  const [formIMCAjustado] = Form.useForm();
  const [formGananciaPeso] = Form.useForm();

  const handleCalcularCardiovascular = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularRiesgoCardiovascular(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular riesgo cardiovascular');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularTromboembolia = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularRiesgoTromboembolia(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular riesgo de tromboembolia');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularDosisMedicamento = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularDosisMedicamento(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular dosis de medicamento');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularRiesgoPrematuro = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularRiesgoPrematuro(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular riesgo de parto prematuro');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluarCrecimientoFetal = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.evaluarCrecimientoFetal(values);
      setResultado(result);
      message.success('Evaluación completada');
    } catch (error) {
      message.error('Error al evaluar crecimiento fetal');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularIndiceResistencia = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularIndiceResistencia(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular índice de resistencia');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularEdadGestacional = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularEdadGestacionalAvanzada(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular edad gestacional');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularPercentiles = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularPercentiles(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular percentiles');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluarPerfilBiofisico = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.evaluarPerfilBiofisico(values);
      setResultado(result);
      message.success('Evaluación completada');
    } catch (error) {
      message.error('Error al evaluar perfil biofísico');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularIMCAjustado = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularIMCAjustado(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular IMC ajustado');
    } finally {
      setLoading(false);
    }
  };

  const handleCalcularGananciaPeso = async (values: any) => {
    setLoading(true);
    try {
      const result = await calculadorasAvanzadasService.calcularGananciaPeso(values);
      setResultado(result);
      message.success('Cálculo completado');
    } catch (error) {
      message.error('Error al calcular ganancia de peso');
    } finally {
      setLoading(false);
    }
  };

  const renderResultado = () => {
    if (!resultado) return null;

    return (
      <Card title="Resultado del Cálculo" style={{ marginTop: '24px' }}>
        <Descriptions bordered column={1}>
          {Object.entries(resultado).map(([key, value]: [string, any]) => (
            <Descriptions.Item key={key} label={key.replace(/_/g, ' ').toUpperCase()}>
              {typeof value === 'boolean' ? (
                <Tag color={value ? 'green' : 'red'}>{value ? 'Sí' : 'No'}</Tag>
              ) : typeof value === 'number' ? (
                value.toFixed(2)
              ) : (
                String(value)
              )}
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>
    );
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1>Calculadoras Médicas Avanzadas</h1>
      <p>Herramientas especializadas para evaluación y cálculo en obstetricia</p>

      <Tabs
        activeKey={activeCalculator}
        onChange={(key) => {
          setActiveCalculator(key);
          setResultado(null);
        }}
      >
        {/* Riesgo Cardiovascular */}
        <TabPane
          tab={
            <span>
              <HeartOutlined />
              Riesgo Cardiovascular
            </span>
          }
          key="cardiovascular"
        >
          <Card>
            <Form form={formCardiovascular} layout="vertical" onFinish={handleCalcularCardiovascular}>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="edad"
                    label="Edad (años)"
                    rules={[{ required: true, message: 'Ingrese la edad' }]}
                  >
                    <InputNumber min={15} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="presion_sistolica"
                    label="Presión Sistólica (mmHg)"
                    rules={[{ required: true, message: 'Ingrese presión sistólica' }]}
                  >
                    <InputNumber min={80} max={200} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="presion_diastolica"
                    label="Presión Diastólica (mmHg)"
                    rules={[{ required: true, message: 'Ingrese presión diastólica' }]}
                  >
                    <InputNumber min={50} max={130} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="colesterol_total" label="Colesterol Total (mg/dL)">
                    <InputNumber min={100} max={400} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="colesterol_hdl" label="Colesterol HDL (mg/dL)">
                    <InputNumber min={20} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="imc" label="IMC">
                    <InputNumber min={15} max={50} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="diabetes" valuePropName="checked">
                    <Checkbox>Diabetes</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="fumadora" valuePropName="checked">
                    <Checkbox>Fumadora</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Calcular Riesgo Cardiovascular
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Riesgo de Tromboembolia */}
        <TabPane
          tab={
            <span>
              <MedicineBoxOutlined />
              Riesgo Tromboembolia
            </span>
          }
          key="tromboembolia"
        >
          <Card>
            <Form form={formTromboembolia} layout="vertical" onFinish={handleCalcularTromboembolia}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="edad"
                    label="Edad (años)"
                    rules={[{ required: true, message: 'Ingrese la edad' }]}
                  >
                    <InputNumber min={15} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="imc"
                    label="IMC"
                    rules={[{ required: true, message: 'Ingrese IMC' }]}
                  >
                    <InputNumber min={15} max={50} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="embarazo_multiple" valuePropName="checked">
                    <Checkbox>Embarazo Múltiple</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="reposo_prolongado" valuePropName="checked">
                    <Checkbox>Reposo Prolongado</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="historia_trombosis" valuePropName="checked">
                    <Checkbox>Historia de Trombosis</Checkbox>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="trombofilias" valuePropName="checked">
                    <Checkbox>Trombofilias</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="cesarea_programada" valuePropName="checked">
                    <Checkbox>Cesárea Programada</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Calcular Riesgo de Tromboembolia
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Dosis de Medicamento */}
        <TabPane
          tab={
            <span>
              <ExperimentOutlined />
              Dosis Medicamento
            </span>
          }
          key="dosis"
        >
          <Card>
            <Form form={formDosisMedicamento} layout="vertical" onFinish={handleCalcularDosisMedicamento}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="medicamento"
                    label="Medicamento"
                    rules={[{ required: true, message: 'Seleccione medicamento' }]}
                  >
                    <Select placeholder="Seleccione medicamento">
                      <Option value="acido_folico">Ácido Fólico</Option>
                      <Option value="sulfato_ferroso">Sulfato Ferroso</Option>
                      <Option value="metildopa">Metildopa</Option>
                      <Option value="nifedipino">Nifedipino</Option>
                      <Option value="insulina">Insulina</Option>
                      <Option value="heparina">Heparina</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="peso_kg"
                    label="Peso (kg)"
                    rules={[{ required: true, message: 'Ingrese peso' }]}
                  >
                    <InputNumber min={40} max={150} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="edad_gestacional_semanas"
                    label="Edad Gestacional (semanas)"
                    rules={[{ required: true, message: 'Ingrese edad gestacional' }]}
                  >
                    <InputNumber min={4} max={42} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="funcion_renal" label="Función Renal">
                    <Select placeholder="Seleccione función renal">
                      <Option value="normal">Normal</Option>
                      <Option value="leve">Insuficiencia Leve</Option>
                      <Option value="moderada">Insuficiencia Moderada</Option>
                      <Option value="severa">Insuficiencia Severa</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="funcion_hepatica" label="Función Hepática">
                    <Select placeholder="Seleccione función hepática">
                      <Option value="normal">Normal</Option>
                      <Option value="leve">Insuficiencia Leve</Option>
                      <Option value="moderada">Insuficiencia Moderada</Option>
                      <Option value="severa">Insuficiencia Severa</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Calcular Dosis
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Riesgo de Parto Prematuro */}
        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              Riesgo Prematuro
            </span>
          }
          key="prematuro"
        >
          <Card>
            <Form form={formRiesgoPrematuro} layout="vertical" onFinish={handleCalcularRiesgoPrematuro}>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="edad_materna"
                    label="Edad Materna (años)"
                    rules={[{ required: true, message: 'Ingrese edad' }]}
                  >
                    <InputNumber min={15} max={60} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="gestas_previas"
                    label="Gestas Previas"
                    rules={[{ required: true, message: 'Ingrese gestas previas' }]}
                  >
                    <InputNumber min={0} max={20} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="partos_prematuros_previos"
                    label="Partos Prematuros Previos"
                    rules={[{ required: true, message: 'Ingrese partos prematuros' }]}
                  >
                    <InputNumber min={0} max={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="longitud_cervical_mm"
                    label="Longitud Cervical (mm)"
                    rules={[{ required: true, message: 'Ingrese longitud cervical' }]}
                  >
                    <InputNumber min={10} max={60} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="edad_gestacional_semanas"
                    label="Edad Gestacional (semanas)"
                    rules={[{ required: true, message: 'Ingrese edad gestacional' }]}
                  >
                    <InputNumber min={20} max={36} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="embarazo_multiple" valuePropName="checked">
                    <Checkbox>Embarazo Múltiple</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="infeccion_urinaria" valuePropName="checked">
                    <Checkbox>Infección Urinaria</Checkbox>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Calcular Riesgo de Parto Prematuro
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Crecimiento Fetal */}
        <TabPane
          tab={
            <span>
              <FundOutlined />
              Crecimiento Fetal
            </span>
          }
          key="crecimiento"
        >
          <Card>
            <Form form={formCrecimientoFetal} layout="vertical" onFinish={handleEvaluarCrecimientoFetal}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="edad_gestacional_semanas"
                    label="Edad Gestacional (semanas)"
                    rules={[{ required: true, message: 'Ingrese edad gestacional' }]}
                  >
                    <InputNumber min={12} max={42} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="edad_gestacional_dias"
                    label="Días Adicionales"
                    rules={[{ required: true, message: 'Ingrese días' }]}
                  >
                    <InputNumber min={0} max={6} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="peso_estimado_gramos"
                    label="Peso Estimado (g)"
                    rules={[{ required: true, message: 'Ingrese peso estimado' }]}
                  >
                    <InputNumber min={200} max={6000} step={10} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="circunferencia_abdominal_mm"
                    label="Circunferencia Abdominal (mm)"
                    rules={[{ required: true, message: 'Ingrese CA' }]}
                  >
                    <InputNumber min={50} max={400} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="diametro_biparietal_mm"
                    label="Diámetro Biparietal (mm)"
                    rules={[{ required: true, message: 'Ingrese DBP' }]}
                  >
                    <InputNumber min={20} max={120} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="longitud_femur_mm"
                    label="Longitud Fémur (mm)"
                    rules={[{ required: true, message: 'Ingrese LF' }]}
                  >
                    <InputNumber min={10} max={90} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Evaluar Crecimiento Fetal
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Índice de Resistencia Doppler */}
        <TabPane
          tab={
            <span>
              <LineChartOutlined />
              Índice Resistencia
            </span>
          }
          key="doppler"
        >
          <Card>
            <Form form={formIndiceResistencia} layout="vertical" onFinish={handleCalcularIndiceResistencia}>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="velocidad_sistolica"
                    label="Velocidad Sistólica (cm/s)"
                    rules={[{ required: true, message: 'Ingrese velocidad sistólica' }]}
                  >
                    <InputNumber min={0} max={200} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="velocidad_diastolica"
                    label="Velocidad Diastólica (cm/s)"
                    rules={[{ required: true, message: 'Ingrese velocidad diastólica' }]}
                  >
                    <InputNumber min={0} max={100} step={0.1} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    name="arteria"
                    label="Arteria"
                    rules={[{ required: true, message: 'Seleccione arteria' }]}
                  >
                    <Select placeholder="Seleccione arteria">
                      <Option value="umbilical">Umbilical</Option>
                      <Option value="cerebral_media">Cerebral Media</Option>
                      <Option value="uterina">Uterina</Option>
                      <Option value="ductus">Ductus Venoso</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} icon={<CalculatorOutlined />}>
                  Calcular Índice de Resistencia
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>

      {renderResultado()}
    </div>
  );
};

export default CalculadorasAvanzadas;
