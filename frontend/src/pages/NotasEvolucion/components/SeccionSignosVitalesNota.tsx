import React from 'react';
import { Form, Input, InputNumber, Row, Col, Divider, Tooltip } from 'antd';

interface SeccionSignosVitalesNotaProps {
  presionArterial: string;
}

const SeccionSignosVitalesNota: React.FC<SeccionSignosVitalesNotaProps> = ({ presionArterial }) => (
  <>
    <Divider orientation="left">Signos Vitales</Divider>

    <Row gutter={16}>
      <Col xs={24} sm={6}>
        <Form.Item
          label="Presión Sistólica (mmHg)"
          name="presion_arterial_sistolica"
          rules={[
            { required: true, message: 'Requerido' },
            { type: 'number', min: 50, max: 250, message: '50-250 mmHg' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={50}
            max={250}
            placeholder="Ej: 120"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="Presión Diastólica (mmHg)"
          name="presion_arterial_diastolica"
          rules={[
            { required: true, message: 'Requerido' },
            { type: 'number', min: 30, max: 150, message: '30-150 mmHg' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={30}
            max={150}
            placeholder="Ej: 80"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="Frecuencia Cardíaca (lpm)"
          name="frecuencia_cardiaca"
          rules={[
            { required: true, message: 'Requerido' },
            { type: 'number', min: 40, max: 200, message: '40-200 lpm' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={40}
            max={200}
            placeholder="Ej: 75"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="Temperatura (°C)"
          name="temperatura"
          rules={[
            { required: true, message: 'Requerido' },
            { type: 'number', min: 34, max: 42, message: '34-42°C' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={34}
            max={42}
            step={0.1}
            precision={1}
            placeholder="Ej: 36.5"
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24} sm={8}>
        <Form.Item
          label="Frecuencia Respiratoria (rpm)"
          name="frecuencia_respiratoria"
          rules={[{ type: 'number', min: 8, max: 40, message: '8-40 rpm' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={8}
            max={40}
            placeholder="Ej: 18"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={8}>
        <Form.Item
          label="Saturación de O₂ (%)"
          name="saturacion_oxigeno"
          rules={[{ type: 'number', min: 70, max: 100, message: '70-100%' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={70}
            max={100}
            placeholder="Ej: 98"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={8}>
        <Tooltip title="Presión arterial calculada automáticamente">
          <Form.Item label="PA (mmHg)">
            <Input value={presionArterial} disabled placeholder="120/80" />
          </Form.Item>
        </Tooltip>
      </Col>
    </Row>
  </>
);

export default SeccionSignosVitalesNota;
