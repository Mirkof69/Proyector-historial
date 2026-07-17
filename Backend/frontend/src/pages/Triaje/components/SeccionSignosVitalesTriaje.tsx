import React from 'react';
import { Divider, Row, Col, Card, Form, InputNumber, Typography, Tag } from 'antd';
import { HeartOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const getClasificacionIMC = (imcValue: number): string => {
  if (imcValue < 18.5) return 'Bajo peso';
  if (imcValue < 25) return 'Normal';
  if (imcValue < 30) return 'Sobrepeso';
  if (imcValue < 35) return 'Obesidad I';
  if (imcValue < 40) return 'Obesidad II';
  return 'Obesidad III';
};

interface SeccionSignosVitalesTriajeProps {
  imc: number | null;
}

const SeccionSignosVitalesTriaje: React.FC<SeccionSignosVitalesTriajeProps> = ({ imc }) => (
  <>
    <Divider orientation="left"><HeartOutlined /> Signos Vitales y Antropometría</Divider>

    <Row gutter={[24, 0]}>
      <Col xs={24} lg={16}>
        <Card type="inner" className="mb-4">
          <Row gutter={16}>
            <Col xs={12} sm={6}>
              <Form.Item label="P. Sistólica" name="presion_sistolica" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="mmHg" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="P. Diastólica" name="presion_diastolica" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="mmHg" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="Temperatura" name="temperatura" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="°C" step={0.1} />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="F. Cardíaca" name="frecuencia_cardiaca" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="bpm" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="F. Resp." name="frecuencia_respiratoria" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="rpm" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="Saturación" name="saturacion_oxigeno">
                <InputNumber className="w-full" size="large" suffix="%" />
              </Form.Item>
            </Col>
            <Col xs={12} sm={6}>
              <Form.Item label="Dolor (0-10)" name="dolor_escala">
                <InputNumber className="w-full" size="large" min={0} max={10} />
              </Form.Item>
            </Col>
          </Row>
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card type="inner" className="mb-4">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Peso" name="peso_kg" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="kg" step={0.1} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Talla" name="talla_cm" rules={[{ required: true }]}>
                <InputNumber className="w-full" size="large" suffix="cm" />
              </Form.Item>
            </Col>
            <Col span={24}>
              {imc !== null && (
                <div className="imc-display" style={{
                  padding: '12px',
                  borderRadius: '8px',
                  backgroundColor: '#f0f5ff',
                  border: '1px solid #adc6ff',
                  textAlign: 'center'
                }}>
                  <Text type="secondary">IMC Calculado:</Text>
                  <Title level={4} style={{ margin: 0 }}>{imc}</Title>
                  <Tag color="processing">{getClasificacionIMC(imc)}</Tag>
                </div>
              )}
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  </>
);

export default SeccionSignosVitalesTriaje;
