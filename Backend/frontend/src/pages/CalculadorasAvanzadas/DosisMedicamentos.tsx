import React, { useState, useCallback } from 'react';
import { Form, Row, Col, Typography } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';
import {
  calcularDosis, DatosPaciente, ResultadoDosis, RegistroDosis,
} from './dosisMedicamentos/dosisMedicamentosUtils';
import FormDosis from './dosisMedicamentos/FormDosis';
import ResultadoDosisPanel from './dosisMedicamentos/ResultadoDosisPanel';
import AnalisisDosis from './dosisMedicamentos/AnalisisDosis';
import './DosisMedicamentos.css';

const { Title, Text } = Typography;

const DosisMedicamentos: React.FC = () => {
  const [form] = Form.useForm();
  const [resultado, setResultado] = useState<ResultadoDosis | null>(null);
  const [historial, setHistorial] = useState<RegistroDosis[]>([]);

  const tooltipFormatter = useCallback((value: any) => value ? `${value} ${resultado?.unidad ?? ''}` : '', [resultado?.unidad]);

  const onFinish = (valores: DatosPaciente) => {
    const res = calcularDosis(valores);
    setResultado(res);

    const nuevoRegistro: RegistroDosis = {
      ...res,
      fecha: new Date().toLocaleString('es-ES'),
      peso: valores.peso
    };
    setHistorial(prev => [nuevoRegistro, ...prev]);
  };

  return (
    <div className="dosis-medicamentos-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <MedicineBoxOutlined style={{ marginRight: 8, color: '#13c2c2' }} />
          Calculadora de Dosis Obstétricas
        </Title>
        <Text type="secondary">
          Cálculo de dosis de 16 medicamentos obstétricos con ajuste por peso, función renal y alertas de seguridad
        </Text>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <FormDosis form={form} onFinish={onFinish} />
        </Col>

        <Col xs={24} lg={14}>
          {resultado && <ResultadoDosisPanel resultado={resultado} />}
        </Col>
      </Row>

      {resultado && (
        <AnalisisDosis
          resultado={resultado}
          historial={historial}
          tooltipFormatter={tooltipFormatter}
        />
      )}
    </div>
  );
};

export default DosisMedicamentos;
