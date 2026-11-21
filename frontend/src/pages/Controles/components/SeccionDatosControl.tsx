import React from 'react';
import { Form, InputNumber, DatePicker, Row, Col, Divider, Space } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';
import { Embarazo } from '../../../services/embarazosService';
import { EmbarazoSelect } from '../../../components/clinico/SelectoresClinicos';

interface SeccionDatosControlProps {
  isEditing: boolean;
  calcularSemanasGestacion: (embarazoId: number, embarazo?: Embarazo) => void;
}

const SeccionDatosControl: React.FC<SeccionDatosControlProps> = ({
  isEditing, calcularSemanasGestacion,
}) => (
  <>
    {/* ========== DATOS DEL CONTROL ========== */}
    <Divider orientation="left">
      <Space>
        <MedicineBoxOutlined />
        Datos del Control
      </Space>
    </Divider>

    <Row gutter={16}>
      <Col xs={24} md={12}>
        <Form.Item
          name="embarazo"
          label="Embarazo"
          rules={[{ required: true, message: 'Seleccione un embarazo' }]}
        >
          <EmbarazoSelect
            disabled={isEditing}
            onChange={(id, embarazo) => { if (id) calcularSemanasGestacion(id, embarazo as Embarazo | undefined); }}
          />
        </Form.Item>
      </Col>
      <Col xs={12} md={6}>
        <Form.Item
          name="numero_control"
          label="N° Control"
          rules={[{ required: true, message: 'Requerido' }]}
        >
          <InputNumber className="u-ancho" min={1} max={20} size="large" />
        </Form.Item>
      </Col>
      <Col xs={12} md={6}>
        <Form.Item
          name="fecha_control"
          label="Fecha del Control"
          rules={[{ required: true, message: 'Requerido' }]}
        >
          <DatePicker className="u-ancho" format={{ format: 'DD/MM/YYYY', type: 'mask' }} size="large" />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionDatosControl;
