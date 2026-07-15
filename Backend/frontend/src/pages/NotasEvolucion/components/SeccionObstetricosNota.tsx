import React from 'react';
import { Form, Input, InputNumber, Select, Row, Col, Divider, Tooltip } from 'antd';

const { Option } = Select;

interface SeccionObstetricosNotaProps {
  edadGestacional: string;
}

const SeccionObstetricosNota: React.FC<SeccionObstetricosNotaProps> = ({ edadGestacional }) => (
  <>
    <Divider orientation="left">Datos Obstétricos (si aplica)</Divider>

    <Row gutter={16}>
      <Col xs={24} sm={6}>
        <Form.Item
          label="Edad Gestacional (semanas)"
          name="edad_gestacional_semanas"
          rules={[{ type: 'number', min: 0, max: 42, message: '0-42 semanas' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            max={42}
            placeholder="Ej: 28"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="Días adicionales"
          name="edad_gestacional_dias"
          rules={[{ type: 'number', min: 0, max: 6, message: '0-6 días' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            max={6}
            placeholder="Ej: 4"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="Altura Uterina (cm)"
          name="altura_uterina"
          rules={[{ type: 'number', min: 0, max: 50, message: '0-50 cm' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            max={50}
            step={0.1}
            precision={1}
            placeholder="Ej: 28.5"
          />
        </Form.Item>
      </Col>

      <Col xs={24} sm={6}>
        <Form.Item
          label="FCF (lpm)"
          name="frecuencia_cardiaca_fetal"
          rules={[{ type: 'number', min: 100, max: 180, message: '100-180 lpm' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={100}
            max={180}
            placeholder="Ej: 140"
          />
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col xs={24} sm={8}>
        <Form.Item label="Presentación Fetal" name="presentacion_fetal">
          <Select placeholder="Seleccionar presentación">
            <Option value="cefalica">Cefálica</Option>
            <Option value="podalica">Podálica</Option>
            <Option value="transversa">Transversa</Option>
            <Option value="oblicua">Oblicua</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col xs={24} sm={8}>
        <Form.Item label="Movimientos Fetales" name="movimientos_fetales">
          <Select placeholder="Seleccionar estado">
            <Option value="presentes">Presentes</Option>
            <Option value="ausentes">Ausentes</Option>
            <Option value="disminuidos">Disminuidos</Option>
            <Option value="aumentados">Aumentados</Option>
          </Select>
        </Form.Item>
      </Col>

      <Col xs={24} sm={8}>
        <Tooltip title="Edad gestacional calculada automáticamente">
          <Form.Item label="EG (semanas)">
            <Input value={edadGestacional} disabled placeholder="28s 4d" />
          </Form.Item>
        </Tooltip>
      </Col>
    </Row>
  </>
);

export default SeccionObstetricosNota;
