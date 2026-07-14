import React, { useState } from 'react';
import { Form, Row, Col, Typography } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import './IMCGananciaPonderal.css';
import { DatosPaciente, ResultadoIMC, RegistroIMC, calcularIMC } from './imcGananciaUtils';
import IMCForm from './components/IMCForm';
import IMCResultado from './components/IMCResultado';
import IMCGraficas from './components/IMCGraficas';
import IMCHistorial from './components/IMCHistorial';

const { Title, Text } = Typography;

  const IMCGananciaPonderal: React.FC = () => {
    const [form] = Form.useForm();
    const [values, setValues] = useState<DatosPaciente>({
      peso_pregestacional: 60,
      talla: 165,
      peso_actual: 68,
      semanas_gestacion: 24
    });
    const [resultado, setResultado] = useState<ResultadoIMC | null>(null);
    const [historial, setHistorial] = useState<RegistroIMC[]>([]);

  const onFinish = (formValues: DatosPaciente) => {
    setValues(formValues);
    const result = calcularIMC(formValues);
    setResultado(result);

    // Agregar al historial
    const nuevoRegistro: RegistroIMC = {
      id: historial.length + 1,
      fecha: new Date().toISOString().slice(0, 10),
      semanas: formValues.semanas_gestacion,
      peso: formValues.peso_actual,
      ganancia: result.ganancia_actual,
      imc: result.imc_pregestacional,
      estado: result.estado_nutricional
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  // Estadísticas en tiempo real
  const promedioGanancia = historial.length > 0
    ? (historial.reduce((sum, h) => sum + h.ganancia, 0) / historial.length).toFixed(1)
    : '0.0';

  const tasaAdecuada = historial.length > 0
    ? ((historial.filter(h => h.estado.includes('ADECUADA')).length / historial.length) * 100).toFixed(0)
    : '0';

  return (
    <div className="imc-ganancia-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <CalculatorOutlined style={{ marginRight: 8, color: '#1890ff' }} />
          IMC y Ganancia Ponderal Gestacional
        </Title>
        <Text type="secondary">
          Calculadora de Índice de Masa Corporal pregestacional y monitoreo de ganancia de peso según guías IOM (Institute of Medicine)
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* Formulario de entrada */}
        <Col xs={24} lg={8}>
          <IMCForm form={form} onFinish={onFinish} />
        </Col>

        {/* Resultados */}
        <Col xs={24} lg={16}>
          {resultado && <IMCResultado resultado={resultado} values={values} />}
        </Col>
      </Row>

      {/* Gráficas */}
      {resultado && <IMCGraficas values={values} resultado={resultado} historial={historial} />}

      {/* Historial y estadísticas */}
      {historial.length > 0 && (
        <IMCHistorial historial={historial} promedioGanancia={promedioGanancia} tasaAdecuada={tasaAdecuada} />
      )}
    </div>
  );
};

export default IMCGananciaPonderal;
