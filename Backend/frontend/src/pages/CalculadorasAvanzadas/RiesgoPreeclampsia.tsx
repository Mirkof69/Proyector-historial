import React, { useState } from 'react';
import { Form, Row, Col, Typography } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import './RiesgoPreeclampsia.css';
import { DatosRiesgo, ResultadoRiesgo, RegistroRiesgo, calcularRiesgo } from './riesgoPreeclampsiaUtils';
import RiesgoPEForm from './components/RiesgoPEForm';
import RiesgoPEResultado from './components/RiesgoPEResultado';
import RiesgoPEGraficas from './components/RiesgoPEGraficas';

const { Title, Text } = Typography;

const RiesgoPreeclampsia: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoRiesgo | null>(null);
  const [historial, setHistorial] = useState<RegistroRiesgo[]>([]);

  const onFinish = (values: DatosRiesgo) => {
    const res = calcularRiesgo(values);
    setResultado(res);

    const nuevoRegistro: RegistroRiesgo = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      semanas: values.semanas
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  return (
    <div className="riesgo-preeclampsia-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ExperimentOutlined style={{ marginRight: 8, color: '#667eea' }} />
          Calculadora de Riesgo de Preeclampsia (FMF)
        </Title>
        <Text type="secondary">
          Modelo Bayesiano de la Fetal Medicine Foundation con biomarcadores séricos, ecográficos y factores maternos
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <RiesgoPEForm form={form} onFinish={onFinish} />
        </Col>

        <Col xs={24} lg={12}>
          {resultado && <RiesgoPEResultado resultado={resultado} />}
        </Col>
      </Row>

      {resultado && <RiesgoPEGraficas resultado={resultado} historial={historial} />}
    </div>
  );
};

export default RiesgoPreeclampsia;
