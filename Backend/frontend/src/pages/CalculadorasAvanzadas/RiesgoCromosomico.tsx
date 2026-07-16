import React, { useReducer } from 'react';
import { Row, Col, Typography, Form } from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import './RiesgoCromosomico.css';
import {
  DatosScreening, RegistroScreening,
  screeningReducer, initialScreeningState, calcularRiesgo,
} from './riesgoCromosomicoUtils';
import RiesgoCromosomicoForm from './components/RiesgoCromosomicoForm';
import RiesgoCromosomicoResultado from './components/RiesgoCromosomicoResultado';
import RiesgoCromosomicoGraficas from './components/RiesgoCromosomicoGraficas';

const { Title, Text } = Typography;

const RiesgoCromosomico: React.FC = () => {
  const [form] = Form.useForm();
  const [state, dispatch] = useReducer(screeningReducer, initialScreeningState);
  const { resultado, historial, usandoDatosEjemplo } = state;

  const onFinish = (values: DatosScreening) => {
    const res = calcularRiesgo(values);

    const nuevoRegistro: RegistroScreening = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      edad: values.edad,
      semanas: values.semanas
    };

    dispatch({
      type: 'CALCULATE',
      payload: { resultado: res, registro: nuevoRegistro }
    });
  };

  return (
    <div className="riesgo-cromosomico-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ExperimentOutlined style={{ marginRight: 8, color: '#722ed1' }} />
          Screening de Aneuploidías - Primer Trimestre (FMF)
        </Title>
        <Text type="secondary">
          Cálculo de riesgo combinado para T21 (Down), T18 (Edwards) y T13 (Patau) con NT, PAPP-A y βhCG libre
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <RiesgoCromosomicoForm form={form} onFinish={onFinish} usandoDatosEjemplo={usandoDatosEjemplo} />
        </Col>

        <Col xs={24} lg={12}>
          {resultado && <RiesgoCromosomicoResultado resultado={resultado} />}
        </Col>
      </Row>

      {resultado && <RiesgoCromosomicoGraficas resultado={resultado} historial={historial} />}
    </div>
  );
};

export default RiesgoCromosomico;
