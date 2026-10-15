import React from 'react';
import { Form, InputNumber, Card, Row, Col, Divider, Space, Typography } from 'antd';
import { HeartOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface SeccionSignosVitalesProps {
  gananciaCalculada: string;
  imcCalculado: string;
  pamCalculada: string;
  modal: { warning: (config: any) => void };
}

const SeccionSignosVitales: React.FC<SeccionSignosVitalesProps> = ({
  gananciaCalculada, imcCalculado, pamCalculada, modal,
}) => (
  <>
    {/* ========== SIGNOS VITALES MATERNOS ========== */}
    <Divider orientation="left">
      <Space>
        <HeartOutlined />
        Signos Vitales Maternos
      </Space>
    </Divider>

    <Card size="small" className="u-mb-4 controles-signos">
      <Row gutter={16}>
        <Col xs={12} md={6}>
          <Form.Item
            name="peso_actual"
            label="Peso Actual (kg)"
            rules={[{ required: true, message: 'Requerido' }]}
          >
            <InputNumber
              className="u-ancho"
              min={30}
              max={200}
              step={0.1}
              placeholder="65.5"
              size="large"
            />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item name="peso_pregestacional" label="Peso Pregestacional (kg)">
            <InputNumber
              className="u-ancho"
              min={30}
              max={200}
              step={0.1}
              placeholder="60.0"
              size="large"
            />
          </Form.Item>
          {gananciaCalculada && (
            <Text type="success" className="u-t-xs">
              ✓ Ganancia: {gananciaCalculada}
            </Text>
          )}
        </Col>
        <Col xs={12} md={6}>
          <Form.Item
            name="talla"
            label="Talla (cm)"
            tooltip="Talla materna. Se auto-completa del registro del embarazo si está disponible."
          >
            <InputNumber
              className="u-ancho"
              min={130}
              max={200}
              placeholder="160"
              size="large"
              onChange={(value) => {
                if (value && (value < 100 || value > 220)) {
                  modal.warning({
                    title: '⚠️ Advertencia: Talla Fuera de Rango',
                    content: 'La talla debe estar entre 120 y 220 cm.',
                  });
                }
              }}
            />
          </Form.Item>
          {imcCalculado && (
            <Text type="secondary" className="u-t-xs">
              IMC: {imcCalculado}
            </Text>
          )}
        </Col>
        <Col xs={12} md={6}>
          <Form.Item name="temperatura" label="Temperatura (°C)">
            <InputNumber
              className="u-ancho"
              min={35}
              max={42}
              step={0.1}
              placeholder="36.5"
              size="large"
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={12} md={6}>
          <Form.Item
            name="presion_arterial_sistolica"
            label="PA Sistólica (mmHg)"
            rules={[
              { required: true, message: 'Requerido' },
              {
                type: 'number',
                min: 70,
                max: 200,
                message: 'Rango válido: 70-200 mmHg',
              },
            ]}
          >
            <InputNumber
              className="u-ancho"
              min={70}
              max={220}
              placeholder="120"
              size="large"
            />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item
            name="presion_arterial_diastolica"
            label="PA Diastólica (mmHg)"
            rules={[
              { required: true, message: 'Requerido' },
              {
                type: 'number',
                min: 40,
                max: 140,
                message: 'Rango válido: 40-140 mmHg',
              },
            ]}
          >
            <InputNumber
              className="u-ancho"
              min={40}
              max={140}
              placeholder="80"
              size="large"
            />
          </Form.Item>
          {pamCalculada && (
            <Text type="secondary" className="u-t-xs">
              {pamCalculada}
            </Text>
          )}
        </Col>
        <Col xs={12} md={6}>
          <Form.Item name="frecuencia_cardiaca" label="Frecuencia Cardíaca (lpm)">
            <InputNumber
              className="u-ancho"
              min={40}
              max={200}
              placeholder="80"
              size="large"
            />
          </Form.Item>
        </Col>
      </Row>
    </Card>
  </>
);

export default SeccionSignosVitales;
