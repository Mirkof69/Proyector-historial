import React from 'react';
import { Form, InputNumber, Row, Col, Divider, Space } from 'antd';
import { CalendarOutlined } from '@ant-design/icons';

const SeccionEdadGestacional: React.FC = () => (
  <>
    {/* ========== EDAD GESTACIONAL ========== */}
    <Divider orientation="left">
      <Space>
        <CalendarOutlined />
        Edad Gestacional
      </Space>
    </Divider>

    <Row gutter={16}>
      <Col span={12}>
        <Form.Item
          name="edad_gestacional_semanas"
          label="Semanas de Gestación"
          rules={[{ required: true, message: 'Requerido' }]}
        >
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            max={42}
            suffix="semanas"
            size="large"
          />
        </Form.Item>
      </Col>
      <Col span={12}>
        <Form.Item name="edad_gestacional_dias" label="Días adicionales">
          <InputNumber
            style={{ width: '100%' }}
            min={0}
            max={6}
            suffix="días"
            size="large"
          />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionEdadGestacional;
