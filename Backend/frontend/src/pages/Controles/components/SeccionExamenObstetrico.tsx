import React from 'react';
import { Form, InputNumber, Row, Col, Select, Divider, Space } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';

const { Option } = Select;

interface SeccionExamenObstetricoProps {
  semanasGestacion: number;
}

const SeccionExamenObstetrico: React.FC<SeccionExamenObstetricoProps> = ({ semanasGestacion }) => (
  <>
    {/* ========== EXAMEN OBSTÉTRICO ========== */}
    <Divider orientation="left">
      <Space>
        <MedicineBoxOutlined />
        Examen Obstétrico
      </Space>
    </Divider>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="altura_uterina"
          label="Altura Uterina (cm)"
          tooltip="Medida desde la sínfisis púbica al fondo uterino. Medible desde ~12 semanas, aunque más útil desde las 20 semanas."
          rules={[
            {
              required: semanasGestacion >= 12,
              message: 'Requerido (a partir de 12 semanas)',
            },
            {
              type: 'number',
              min: 10,
              max: 50,
              message: 'Rango válido: 10-50 cm',
            },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={10}
            max={50}
            step={0.1}
            placeholder="Ej: 13.0"
            size="large"
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          name="frecuencia_cardiaca_fetal"
          label="FCF (lpm)"
          tooltip="Frecuencia Cardíaca Fetal. Detectable desde 10-12 semanas con Doppler, audible desde 18-20 semanas."
          rules={[
            {
              required: semanasGestacion >= 20,
              message: 'Requerido (a partir de 20 semanas)',
            },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={90}
            max={180}
            placeholder="120-160"
            size="large"
          />
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          name="presentacion_fetal"
          label="Presentación"
          rules={[
            {
              required: semanasGestacion >= 20,
              message: 'Requerido (a partir de 20 semanas)',
            },
          ]}
        >
          <Select placeholder="Seleccionar" size="large">
            <Option value="cefalica">Cefálica</Option>
            <Option value="podalica">Podálica</Option>
            <Option value="transversa">Transversa</Option>
            <Option value="oblicua">Oblicua</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>

    <Row gutter={16}>
      <Col span={8}>
        <Form.Item
          name="movimientos_fetales"
          label="Movimientos Fetales"
          tooltip="Documentar desde ~18-20 semanas cuando la madre comienza a percibir movimientos. Antes de esta edad, dejar en 'Presentes' por defecto."
          rules={[
            {
              required: semanasGestacion >= 20,
              message: 'Requerido (a partir de 20 semanas)',
            },
          ]}
        >
          <Select size="large" placeholder="Seleccionar">
            <Option value="presentes">Presentes</Option>
            <Option value="ausentes">Ausentes</Option>
            <Option value="disminuidos">Disminuidos</Option>
            <Option value="aumentados">Aumentados</Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          name="edema"
          label="Edema"
          rules={[
            {
              required: semanasGestacion >= 20,
              message: 'Requerido (a partir de 20 semanas)',
            },
          ]}
        >
          <Select size="large">
            <Option value="no">No</Option>
            <Option value="leve">Leve (+)</Option>
            <Option value="moderado">Moderado (++)</Option>
            <Option value="severo">Severo (+++)</Option>
            <Option value="generalizado">Generalizado</Option>
          </Select>
        </Form.Item>
      </Col>
      <Col span={8}>
        <Form.Item
          name="proteinuria"
          label="Proteinuria"
          rules={[
            {
              required: semanasGestacion >= 20,
              message: 'Requerido (a partir de 20 semanas)',
            },
          ]}
        >
          <Select size="large">
            <Option value="negativa">Negativa</Option>
            <Option value="trazas">Trazas</Option>
            <Option value="positiva_1">+ (30 mg/dL)</Option>
            <Option value="positiva_2">++ (100 mg/dL)</Option>
            <Option value="positiva_3">+++ (300 mg/dL)</Option>
            <Option value="positiva_4">++++ (1000 mg/dL)</Option>
          </Select>
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionExamenObstetrico;
