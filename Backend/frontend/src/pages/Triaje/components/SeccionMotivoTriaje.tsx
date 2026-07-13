import React from 'react';
import { Divider, Row, Col, Form, Input } from 'antd';
import { MedicineBoxOutlined } from '@ant-design/icons';

const { TextArea } = Input;

const SeccionMotivoTriaje: React.FC = () => (
  <>
    <Divider orientation="left"><MedicineBoxOutlined /> Motivo de Consulta y Observaciones</Divider>

    <Row gutter={16}>
      <Col span={24}>
        <Form.Item
          label="Motivo de la Visita"
          name="motivo_visita"
          rules={[{ required: true, message: 'Debe ingresar el motivo de consulta' }]}
        >
          <TextArea
            rows={4}
            placeholder="Describa el motivo principal de la visita y síntomas actuales..."
            className="custom-textarea"
            maxLength={1000}
            showCount
          />
        </Form.Item>
      </Col>
      <Col span={24}>
        <Form.Item label="Observaciones de Enfermería" name="observaciones">
          <TextArea rows={2} placeholder="Observaciones adicionales, hallazgos físicos notables, etc." />
        </Form.Item>
      </Col>
    </Row>
  </>
);

export default SeccionMotivoTriaje;
