import React, { useState } from 'react';
import { Card, Row, Col, Form, Input, DatePicker, Button, InputNumber, Alert, Select, Tabs, Tooltip } from 'antd';
import { CalculatorOutlined, ReloadOutlined, InfoCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { TabPane } = Tabs;
const { Option } = Select;

const Calculadoras: React.FC = () => {
  const [fppForm] = Form.useForm();
  const [imcForm] = Form.useForm();
  const [bishopForm] = Form.useForm();
  const [apgarForm] = Form.useForm();
  const [preeclampsiaForm] = Form.useForm();

  const [fppResultado, setFppResultado] = useState<string>('');
  const [edadGestacional, setEdadGestacional] = useState<string>('');
  const [imcResultado, setImcResultado] = useState<any>(null);
  const [bishopResultado, setBishopResultado] = useState<any>(null);
  const [preeclampsiaResultado, setPreeclampsiaResultado] = useState<any>(null);
  const [apgarResultado, setApgarResultado] = useState<any>(null);

  // Reiniciar FPP
  const reiniciarFPP = () => {
    fppForm.resetFields();
    setFppResultado('');
    setEdadGestacional('');
  };

  // Reiniciar IMC
  const reiniciarIMC = () => {
    imcForm.resetFields();
    setImcResultado(null);
  };

  // Reiniciar Bishop
  const reiniciarBishop = () => {
    bishopForm.resetFields();
    setBishopResultado(null);
  };

  // Reiniciar Apgar
  const reiniciarApgar = () => {
    apgarForm.resetFields();
    setApgarResultado(null);
  };

  // Reiniciar Preeclampsia
  const reiniciarPreeclampsia = () => {
    preeclampsiaForm.resetFields();
    setPreeclampsiaResultado(null);
  };

  // Calculadora FPP
  const calcularFPP = (fum: any) => {
    if (fum) {
      const fpp = dayjs(fum).add(280, 'day');
      setFppResultado(fpp.format('DD/MM/YYYY'));
      
      const hoy = dayjs();
      const diasDiferencia = hoy.diff(dayjs(fum), 'day');
      const semanas = Math.floor(diasDiferencia / 7);
      const dias = diasDiferencia % 7;
      setEdadGestacional(`${semanas} semanas + ${dias} días`);
    }
  };

  // Calculadora IMC
  const calcularIMC = (values: any) => {
    const { peso, altura } = values;
    if (peso && altura) {
      const alturaM = altura / 100;
      const imc = peso / (alturaM * alturaM);
      
      let clasificacion = '';
      let color = '';
      if (imc < 18.5) {
        clasificacion = 'Bajo peso';
        color = 'warning';
      } else if (imc < 25) {
        clasificacion = 'Normal';
        color = 'success';
      } else if (imc < 30) {
        clasificacion = 'Sobrepeso';
        color = 'warning';
      } else {
        clasificacion = 'Obesidad';
        color = 'error';
      }
      
      setImcResultado({ imc: imc.toFixed(2), clasificacion, color });
    }
  };

  // Calculadora Bishop
  const calcularBishop = (values: any) => {
    const { dilatacion, borramiento, consistencia, posicion, estacion } = values;
    
    let puntos = 0;
    
    if (dilatacion >= 6) puntos += 3;
    else if (dilatacion >= 4) puntos += 2;
    else if (dilatacion >= 2) puntos += 1;
    
    if (borramiento >= 80) puntos += 3;
    else if (borramiento >= 60) puntos += 2;
    else if (borramiento >= 40) puntos += 1;
    
    if (consistencia === 'blando') puntos += 2;
    else if (consistencia === 'medio') puntos += 1;
    
    if (posicion === 'anterior') puntos += 2;
    else if (posicion === 'media') puntos += 1;
    
    if (estacion >= 2) puntos += 3;
    else if (estacion >= 0) puntos += 2;
    else if (estacion >= -2) puntos += 1;
    
    let interpretacion = '';
    let color = '';
    if (puntos >= 8) {
      interpretacion = 'Favorable para inducción';
      color = 'success';
    } else if (puntos >= 5) {
      interpretacion = 'Moderadamente favorable';
      color = 'warning';
    } else {
      interpretacion = 'Desfavorable - considerar maduración cervical';
      color = 'error';
    }
    
    setBishopResultado({ puntos, interpretacion, color });
  };

  // Calculadora Riesgo Preeclampsia
  const calcularRiesgoPreeclampsia = (values: any) => {
    const { sistolica, diastolica, edad, primiparidad, antecedentes } = values;
    
    let riesgo = 0;
    
    if (sistolica >= 140 || diastolica >= 90) riesgo += 3;
    else if (sistolica >= 130 || diastolica >= 85) riesgo += 2;
    
    if (edad >= 40 || edad < 20) riesgo += 2;
    else if (edad >= 35) riesgo += 1;
    
    if (primiparidad) riesgo += 1;
    if (antecedentes) riesgo += 3;
    
    let nivel = '';
    let color = '';
    let recomendacion = '';
    
    if (riesgo >= 6) {
      nivel = 'ALTO';
      color = 'error';
      recomendacion = 'Requiere monitoreo estrecho, considerar aspirina profiláctica';
    } else if (riesgo >= 3) {
      nivel = 'MODERADO';
      color = 'warning';
      recomendacion = 'Vigilancia prenatal reforzada, control de PA frecuente';
    } else {
      nivel = 'BAJO';
      color = 'success';
      recomendacion = 'Control prenatal rutinario';
    }
    
    setPreeclampsiaResultado({ riesgo, nivel, color, recomendacion });
  };

  // Calculadora Apgar
  const calcularApgar = (values: any) => {
    const { apgar1, apgar5 } = values;
    
    const evaluarApgar = (puntos: number) => {
      if (puntos >= 7) return { estado: 'Normal', color: 'success' };
      if (puntos >= 4) return { estado: 'Depresión moderada - requiere atención', color: 'warning' };
      return { estado: 'Depresión severa - requiere reanimación', color: 'error' };
    };
    
    const eval1 = evaluarApgar(apgar1);
    const eval5 = evaluarApgar(apgar5);
    
    setApgarResultado({ apgar1, apgar5, eval1, eval5 });
  };

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>
        <CalculatorOutlined /> Calculadoras Clínicas Obstétricas
      </h1>

      <Tabs defaultActiveKey="1">
        <TabPane tab="Básicas" key="1">
          <Row gutter={[16, 16]}>
            {/* FPP y Edad Gestacional */}
            <Col span={12}>
              <Card 
                title="Fecha Probable de Parto (FPP) y Edad Gestacional"
                extra={
                  <Tooltip title="Calcula la fecha probable de parto sumando 280 días (40 semanas) a la FUM">
                    <InfoCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                  </Tooltip>
                }
              >
                <Alert
                  message="¿Qué calcula?"
                  description="Determina la fecha probable de parto (FPP) usando la Regla de Naegele y calcula las semanas de gestación actuales."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form form={fppForm} layout="vertical">
                  <Form.Item 
                    label={
                      <span>
                        Fecha Última Menstruación (FUM) 
                        <Tooltip title="Primer día del último período menstrual">
                          <InfoCircleOutlined style={{ marginLeft: 4, color: '#1890ff' }} />
                        </Tooltip>
                      </span>
                    }
                  >
                    <DatePicker 
                      style={{ width: '100%' }} 
                      format="DD/MM/YYYY"
                      onChange={calcularFPP}
                    />
                  </Form.Item>
                  
                  <Button icon={<ReloadOutlined />} onClick={reiniciarFPP}>
                    Reiniciar
                  </Button>
                  
                  {fppResultado && (
                    <Alert
                      message="Resultados"
                      description={
                        <div>
                          <p><strong>FPP:</strong> {fppResultado}</p>
                          <p><strong>Edad Gestacional:</strong> {edadGestacional}</p>
                        </div>
                      }
                      type="success"
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Form>
              </Card>
            </Col>

            {/* IMC */}
            <Col span={12}>
              <Card 
                title="Índice de Masa Corporal (IMC)"
                extra={
                  <Tooltip title="Relación entre peso y altura al cuadrado">
                    <InfoCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                  </Tooltip>
                }
              >
                <Alert
                  message="¿Qué calcula?"
                  description="Evalúa si el peso es adecuado para la altura. IMC = Peso(kg) / Altura(m)²"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form form={imcForm} layout="vertical" onFinish={calcularIMC}>
                  <Form.Item name="peso" label="Peso (kg)" rules={[{ required: true }]}>
                    <InputNumber style={{ width: '100%' }} min={0} step={0.1} placeholder="Ej: 65.5" />
                  </Form.Item>
                  
                  <Form.Item name="altura" label="Altura (cm)" rules={[{ required: true }]}>
                    <InputNumber style={{ width: '100%' }} min={0} placeholder="Ej: 165" />
                  </Form.Item>
                  
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular IMC
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={reiniciarIMC} style={{ marginLeft: 8 }}>
                    Reiniciar
                  </Button>
                  
                  {imcResultado && (
                    <Alert
                      message="Resultado"
                      description={
                        <div>
                          <p><strong>IMC:</strong> {imcResultado.imc}</p>
                          <p><strong>Clasificación:</strong> {imcResultado.clasificacion}</p>
                          <p style={{ fontSize: 12, marginTop: 8 }}>
                            <strong>Rangos:</strong> Bajo peso (&lt;18.5) | Normal (18.5-24.9) | Sobrepeso (25-29.9) | Obesidad (≥30)
                          </p>
                        </div>
                      }
                      type={imcResultado.color}
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Evaluación Clínica" key="2">
          <Row gutter={[16, 16]}>
            {/* Puntaje de Bishop */}
            <Col span={12}>
              <Card 
                title="Puntaje de Bishop (Inducción del Parto)"
                extra={
                  <Tooltip title="Evalúa maduración cervical para decidir inducción">
                    <InfoCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                  </Tooltip>
                }
              >
                <Alert
                  message="¿Qué evalúa?"
                  description="Puntaje de 0-13 que mide la maduración del cuello uterino. ≥8: Favorable | 5-7: Moderado | <5: Desfavorable"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form form={bishopForm} layout="vertical" onFinish={calcularBishop}>
                  <Form.Item 
                    name="dilatacion" 
                    label={
                      <span>
                        Dilatación (cm) 
                        <Tooltip title="Apertura del cuello uterino (0-10 cm)">
                          <InfoCircleOutlined style={{ marginLeft: 4 }} />
                        </Tooltip>
                      </span>
                    }
                    rules={[{ required: true }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={0} max={10} />
                  </Form.Item>
                  
                  <Form.Item 
                    name="borramiento" 
                    label={
                      <span>
                        Borramiento (%) 
                        <Tooltip title="Adelgazamiento del cuello uterino (0-100%)">
                          <InfoCircleOutlined style={{ marginLeft: 4 }} />
                        </Tooltip>
                      </span>
                    }
                    rules={[{ required: true }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={0} max={100} />
                  </Form.Item>
                  
                  <Form.Item name="consistencia" label="Consistencia del cuello" rules={[{ required: true }]}>
                    <Select>
                      <Option value="firme">Firme (duro)</Option>
                      <Option value="medio">Medio</Option>
                      <Option value="blando">Blando (suave)</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item name="posicion" label="Posición del cuello" rules={[{ required: true }]}>
                    <Select>
                      <Option value="posterior">Posterior (atrás)</Option>
                      <Option value="media">Media</Option>
                      <Option value="anterior">Anterior (adelante)</Option>
                    </Select>
                  </Form.Item>
                  
                  <Form.Item 
                    name="estacion" 
                    label={
                      <span>
                        Estación 
                        <Tooltip title="Altura de la cabeza fetal (-3 a +3)">
                          <InfoCircleOutlined style={{ marginLeft: 4 }} />
                        </Tooltip>
                      </span>
                    }
                    rules={[{ required: true }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={-3} max={3} />
                  </Form.Item>
                  
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Calcular Bishop
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={reiniciarBishop} style={{ marginLeft: 8 }}>
                    Reiniciar
                  </Button>
                  
                  {bishopResultado && (
                    <Alert
                      message="Resultado"
                      description={
                        <div>
                          <p><strong>Puntaje:</strong> {bishopResultado.puntos}/13</p>
                          <p><strong>Interpretación:</strong> {bishopResultado.interpretacion}</p>
                        </div>
                      }
                      type={bishopResultado.color}
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Form>
              </Card>
            </Col>

            {/* Apgar */}
            <Col span={12}>
              <Card 
                title="Puntaje de Apgar"
                extra={
                  <Tooltip title="Evalúa vitalidad del recién nacido">
                    <InfoCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                  </Tooltip>
                }
              >
                <Alert
                  message="¿Qué evalúa?"
                  description="Puntaje de 0-10 que mide la vitalidad del bebé al nacer. ≥7: Normal | 4-6: Depresión moderada | <4: Depresión severa"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form form={apgarForm} layout="vertical" onFinish={calcularApgar}>
                  <Form.Item 
                    name="apgar1" 
                    label={
                      <span>
                        Apgar 1 minuto 
                        <Tooltip title="Evaluación al primer minuto de vida">
                          <InfoCircleOutlined style={{ marginLeft: 4 }} />
                        </Tooltip>
                      </span>
                    }
                    rules={[{ required: true }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={0} max={10} />
                  </Form.Item>
                  
                  <Form.Item 
                    name="apgar5" 
                    label={
                      <span>
                        Apgar 5 minutos 
                        <Tooltip title="Evaluación a los 5 minutos de vida">
                          <InfoCircleOutlined style={{ marginLeft: 4 }} />
                        </Tooltip>
                      </span>
                    }
                    rules={[{ required: true }]}
                  >
                    <InputNumber style={{ width: '100%' }} min={0} max={10} />
                  </Form.Item>
                  
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Evaluar Apgar
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={reiniciarApgar} style={{ marginLeft: 8 }}>
                    Reiniciar
                  </Button>
                  
                  {apgarResultado && (
                    <div style={{ marginTop: 16 }}>
                      <Alert
                        message="Apgar 1 minuto"
                        description={`${apgarResultado.apgar1}/10 - ${apgarResultado.eval1.estado}`}
                        type={apgarResultado.eval1.color}
                        showIcon
                        style={{ marginBottom: 8 }}
                      />
                      <Alert
                        message="Apgar 5 minutos"
                        description={`${apgarResultado.apgar5}/10 - ${apgarResultado.eval5.estado}`}
                        type={apgarResultado.eval5.color}
                        showIcon
                      />
                    </div>
                  )}
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Riesgo Obstétrico" key="3">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card 
                title="Evaluación de Riesgo de Preeclampsia"
                extra={
                  <Tooltip title="Identifica riesgo de hipertensión gestacional">
                    <InfoCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
                  </Tooltip>
                }
              >
                <Alert
                  message="¿Qué evalúa?"
                  description="Calcula el riesgo de desarrollar preeclampsia (hipertensión del embarazo) basado en factores de riesgo clínicos."
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                <Form form={preeclampsiaForm} layout="vertical" onFinish={calcularRiesgoPreeclampsia}>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Form.Item 
                        name="sistolica" 
                        label={
                          <span>
                            PA Sistólica (mmHg) 
                            <Tooltip title="Presión arterial sistólica (número superior). mmHg = milímetros de mercurio">
                              <InfoCircleOutlined style={{ marginLeft: 4 }} />
                            </Tooltip>
                          </span>
                        }
                        rules={[{ required: true }]}
                      >
                        <InputNumber style={{ width: '100%' }} min={0} placeholder="Ej: 120" />
                      </Form.Item>
                    </Col>
                    
                    <Col span={6}>
                      <Form.Item 
                        name="diastolica" 
                        label={
                          <span>
                            PA Diastólica (mmHg) 
                            <Tooltip title="Presión arterial diastólica (número inferior)">
                              <InfoCircleOutlined style={{ marginLeft: 4 }} />
                            </Tooltip>
                          </span>
                        }
                        rules={[{ required: true }]}
                      >
                        <InputNumber style={{ width: '100%' }} min={0} placeholder="Ej: 80" />
                      </Form.Item>
                    </Col>
                    
                    <Col span={6}>
                      <Form.Item name="edad" label="Edad (años)" rules={[{ required: true }]}>
                        <InputNumber style={{ width: '100%' }} min={0} placeholder="Ej: 30" />
                      </Form.Item>
                    </Col>
                    
                    <Col span={6}>
                      <Form.Item 
                        name="primiparidad" 
                        label={
                          <span>
                            Primiparidad 
                            <Tooltip title="Primer embarazo">
                              <InfoCircleOutlined style={{ marginLeft: 4 }} />
                            </Tooltip>
                          </span>
                        }
                        initialValue={false}
                      >
                        <Select>
                          <Option value={true}>Sí (primer embarazo)</Option>
                          <Option value={false}>No</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                  
                  <Form.Item 
                    name="antecedentes" 
                    label="Antecedentes de Preeclampsia" 
                    initialValue={false}
                  >
                    <Select>
                      <Option value={true}>Sí (en embarazo anterior)</Option>
                      <Option value={false}>No</Option>
                    </Select>
                  </Form.Item>
                  
                  <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />}>
                    Evaluar Riesgo
                  </Button>
                  <Button icon={<ReloadOutlined />} onClick={reiniciarPreeclampsia} style={{ marginLeft: 8 }}>
                    Reiniciar
                  </Button>
                  
                  {preeclampsiaResultado && (
                    <Alert
                      message={`Riesgo ${preeclampsiaResultado.nivel} de Preeclampsia`}
                      description={
                        <div>
                          <p><strong>Puntuación:</strong> {preeclampsiaResultado.riesgo}/9</p>
                          <p><strong>Recomendación:</strong> {preeclampsiaResultado.recomendacion}</p>
                          <p style={{ fontSize: 12, marginTop: 8 }}>
                            <strong>Factores evaluados:</strong> Presión arterial, edad materna, primiparidad, antecedentes
                          </p>
                        </div>
                      }
                      type={preeclampsiaResultado.color}
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                  )}
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Calculadoras;