import React, { useState } from 'react';
import { Alert, Button, Card, Col, Form, InputNumber, Row, Space, Tag, Typography } from 'antd';
import { CalculatorOutlined } from '@ant-design/icons';
import { evaluarDiabetesGestacional, ResultadoDG, UMBRALES_IADPSG } from '../../../utils/diabetesGestacional';

const { Text } = Typography;

const COLOR: Record<ResultadoDG['diagnostico'], 'success' | 'warning' | 'error'> = {
  normal: 'success',
  diabetes_gestacional: 'warning',
  diabetes_manifiesta: 'error',
};

interface Props {
  onGuardar: (tipo: string, datos: any, resultado: any) => void;
}

/** PTOG de 75 g con criterios IADPSG/OMS (ver utils/diabetesGestacional). */
const DiabetesGestacionalTab: React.FC<Props> = ({ onGuardar }) => {
  const [resultado, setResultado] = useState<ResultadoDG | null>(null);

  const calcular = (v: { ayunas: number; h1?: number; h2?: number }) => {
    const r = evaluarDiabetesGestacional(v.ayunas, v.h1, v.h2);
    setResultado(r);
    onGuardar('Diabetes Gestacional', v, r);
  };

  return (
    <Row gutter={[24, 24]}>
      <Col xs={24} lg={12}>
        <Card title="Prueba de tolerancia oral a la glucosa (75 g)" type="inner">
          <Form layout="vertical" onFinish={calcular}>
            <Form.Item name="ayunas" label={`Glucemia en ayunas (mg/dL) · corte ${UMBRALES_IADPSG.ayunas}`}
              rules={[{ required: true, message: 'Requerido' }]}>
              <InputNumber min={30} max={600} size="large" />
            </Form.Item>
            <Form.Item name="h1" label={`A la hora (mg/dL) · corte ${UMBRALES_IADPSG.h1}`}>
              <InputNumber min={30} max={600} size="large" />
            </Form.Item>
            <Form.Item name="h2" label={`A las 2 horas (mg/dL) · corte ${UMBRALES_IADPSG.h2}`}>
              <InputNumber min={30} max={600} size="large" />
            </Form.Item>
            <Button type="primary" htmlType="submit" icon={<CalculatorOutlined />} size="large" block>
              Evaluar
            </Button>
          </Form>
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card title="Resultado" type="inner">
          {resultado ? (
            <Space direction="vertical" className="calculadoras-pila">
              <Alert type={COLOR[resultado.diagnostico]} showIcon message={resultado.titulo}
                description={resultado.alterados.length
                  ? <Space wrap>{resultado.alterados.map((a) => <Tag key={a} color="error">{a}</Tag>)}</Space>
                  : 'Ningún valor alcanza los cortes.'} />
              <ul className="calculadoras-lista">
                {resultado.recomendaciones.map((r) => <li key={r}>{r}</li>)}
              </ul>
              <Text type="secondary" className="calculadoras-nota">
                Criterios IADPSG / OMS 2013: basta un valor igual o mayor al corte. Apoyo a la decisión, no reemplaza el criterio médico.
              </Text>
            </Space>
          ) : (
            <Alert message="Ingrese al menos la glucemia en ayunas" type="info" showIcon />
          )}
        </Card>
      </Col>
    </Row>
  );
};

export default DiabetesGestacionalTab;
