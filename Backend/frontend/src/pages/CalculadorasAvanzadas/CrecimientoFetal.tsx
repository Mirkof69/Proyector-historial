import React, { useReducer } from 'react';
import { Form, Row, Col, Typography } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import './CrecimientoFetal.css';
import {
  DatosBiometria, RegistroCrecimiento,
  growthReducer, initialGrowthState, calcularCrecimiento,
} from './crecimientoFetalUtils';
import CrecimientoForm from './components/CrecimientoForm';
import CrecimientoResultado from './components/CrecimientoResultado';
import CrecimientoGraficas from './components/CrecimientoGraficas';

const { Title, Text } = Typography;

const CrecimientoFetal: React.FC = () => {
  const [form] = Form.useForm();
  const [state, dispatch] = useReducer(growthReducer, initialGrowthState);
  const { resultado, historial, datosBiometria, usandoDatosEjemplo } = state;

  const onFinish = (values: DatosBiometria) => {
    const res = calcularCrecimiento(values);

    const nuevoRegistro: RegistroCrecimiento = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      semanas: values.semanas,
      bpd: values.bpd,
      hc: values.hc,
      ac: values.ac,
      fl: values.fl
    };

    dispatch({
      type: 'CALCULATE',
      payload: { datos: values, resultado: res, registro: nuevoRegistro }
    });
  };

  return (
    <div className="crecimiento-fetal-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <LineChartOutlined style={{ marginRight: 8, color: '#00bcd4' }} />
          Calculadora de Crecimiento Fetal y Biometría
        </Title>
        <Text type="secondary">
          Estimación del peso fetal (EFW) con fórmulas de Hadlock y análisis de percentiles según Intergrowth-21st
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <CrecimientoForm form={form} onFinish={onFinish} usandoDatosEjemplo={usandoDatosEjemplo} />
        </Col>

        <Col xs={24} lg={14}>
          {resultado && <CrecimientoResultado resultado={resultado} />}
        </Col>
      </Row>

      {resultado && datosBiometria && (
        <CrecimientoGraficas resultado={resultado} datosBiometria={datosBiometria} historial={historial} />
      )}
    </div>
  );
};

export default CrecimientoFetal;
