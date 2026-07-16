import React from 'react';
import {
  Card, Form, Row, Col, DatePicker, Button, Select, InputNumber, Alert, Typography,
  Switch, Divider,
} from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import {
  ResultadoCalculo, ResultadoCard,
  tabEdadGestacional, tabBishop, tabIMC, tabPreeclampsia,
  tabDiabetesGestacional, tabILA, tabPesoFetal, tabApgar,
} from './calcAvanzadasHelpers';

const { Title } = Typography;
const { Option } = Select;

export interface CalcAvanzadasTabsDeps {
  formEdadGestacional: FormInstance;
  formBishop: FormInstance;
  formIMC: FormInstance;
  formPreeclampsia: FormInstance;
  formDiabetes: FormInstance;
  formILA: FormInstance;
  formPesoFetal: FormInstance;
  formApgar: FormInstance;
  resultadoEdadGestacional: ResultadoCalculo | null;
  resultadoBishop: ResultadoCalculo | null;
  resultadoIMC: ResultadoCalculo | null;
  resultadoPreeclampsia: ResultadoCalculo | null;
  resultadoDiabetes: ResultadoCalculo | null;
  resultadoILA: ResultadoCalculo | null;
  resultadoPesoFetal: ResultadoCalculo | null;
  resultadoApgar: ResultadoCalculo | null;
  calcularEdadGestacional: (values: any) => void;
  calcularBishop: (values: any) => void;
  calcularIMC: (values: any) => void;
  calcularRiesgoPreeclampsia: (values: any) => void;
  calcularDiabetesGestacional: (values: any) => void;
  calcularILA: (values: any) => void;
  calcularPesoFetal: (values: any) => void;
  calcularApgar: (values: any) => void;
}

export const buildCalcAvanzadasTabs = (deps: CalcAvanzadasTabsDeps) => {
  const {
    formEdadGestacional, formBishop, formIMC, formPreeclampsia, formDiabetes,
    formILA, formPesoFetal, formApgar,
    resultadoEdadGestacional, resultadoBishop, resultadoIMC, resultadoPreeclampsia,
    resultadoDiabetes, resultadoILA, resultadoPesoFetal, resultadoApgar,
    calcularEdadGestacional, calcularBishop, calcularIMC, calcularRiesgoPreeclampsia,
    calcularDiabetesGestacional, calcularILA, calcularPesoFetal, calcularApgar,
  } = deps;

  return [
    {
      key: "1",
      label: tabEdadGestacional,
      children: (
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
      )
    },

    {
      key: "2",
      label: tabBishop,
      children: (
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
      )
    },

    {
      key: "3",
      label: tabIMC,
      children: (
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
      )
    },

    {
      key: "4",
      label: tabPreeclampsia,
      children: (
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
      )
    },

    {
      key: "5",
      label: tabDiabetesGestacional,
      children: (
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
      )
    },

    {
      key: "6",
      label: tabILA,
      children: (
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
      )
    },

    {
      key: "7",
      label: tabPesoFetal,
      children: (
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
      )
    },

    {
      key: "8",
      label: tabApgar,
      children: (
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
      )
    },
  ];
};
