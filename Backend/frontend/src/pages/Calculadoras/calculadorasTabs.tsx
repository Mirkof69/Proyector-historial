import React from 'react';
import {
  Card, Row, Col, Button, Space, Form, DatePicker, Select, InputNumber, Divider,
  Statistic, Typography, Alert, Tag, Progress, Tooltip, Badge, Input, Spin, Radio, Result,
} from 'antd';
import {
  CalculatorOutlined, CalendarOutlined, LineChartOutlined, HeartOutlined,
  CheckCircleOutlined, WarningOutlined, BarChartOutlined, PercentageOutlined,
  TeamOutlined, FileOutlined, SaveOutlined,
} from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { ResultadosAction } from './calculadorasReducer';

const { Title, Text, Paragraph } = Typography;

export interface CalculadorasTabsDeps {
  formEG: FormInstance;
  formIMC: FormInstance;
  formBishop: FormInstance;
  formPreeclampsia: FormInstance;
  formILA: FormInstance;
  formPesoFetal: FormInstance;
  formApgar: FormInstance;
  loading: boolean;
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
  calcularEdadGestacional: (values: any) => void;
  calcularIMC: (values: any) => void;
  calcularBishop: (values: any) => void;
  calcularRiesgoPreeclampsia: (values: any) => void;
  calcularILA: (values: any) => void;
  calcularPesoFetal: (values: any) => void;
  calcularApgar: (values: any) => void;
  calcularCapurro: (textura: number, oreja: number, mama: number, pezon: number, planta: number) => void;
  calcularICC: (ac: number, cerebelo: number) => void;
  calcularPA: (sistolica: number, diastolica: number) => void;
  calcularFCMax: (edad: number) => void;
  dispatchResultado: React.Dispatch<ResultadosAction>;
  message: { success: (m: string) => void };
}

export const buildCalculadorasTabs = (deps: CalculadorasTabsDeps) => {
  const {
    formEG, formIMC, formBishop, formPreeclampsia, formILA, formPesoFetal, formApgar,
    loading, resultadoEG, resultadoIMC, resultadoBishop, resultadoPreeclampsia,
    resultadoILA, resultadoPesoFetal, resultadoApgar, resultadoCapurro,
    resultadoSilverman, resultadoBallard, resultadoICC, resultadoPA, resultadoFCMax,
    calcularEdadGestacional, calcularIMC, calcularBishop, calcularRiesgoPreeclampsia,
    calcularILA, calcularPesoFetal, calcularApgar, calcularCapurro, calcularICC,
    calcularPA, calcularFCMax, dispatchResultado, message,
  } = deps;

  return [
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
            const total = Object.values(values).reduce((acc: number, val) => acc + (val as number || 0), 0) as number;
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
            const total = Object.values(values).reduce((acc: number, val) => acc + (val as number || 0), 0) as number;
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
};
