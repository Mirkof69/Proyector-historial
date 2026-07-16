import React from 'react';
import { Form, Input, Divider, Typography } from 'antd';

const { TextArea } = Input;
const { Text } = Typography;

const PasoHallazgos: React.FC = () => (
  <div style={{ padding: '16px' }}>
    <Form.Item
      label={<Text strong>Resumen Clínico / Evolución S.O.A.P.</Text>}
      name="resumen"
      extra="Subjetivo, Objetivo, Análisis, Plan"
    >
      <TextArea rows={6} placeholder="Describa la evolución del paciente desde la última visita..." />
    </Form.Item>

    <Divider />

    <Form.Item
      label={<Text strong>Diagnóstico Clínico (CIE-10)</Text>}
      name="diagnostico"
      rules={[{ required: true, message: 'El diagnóstico es obligatorio', min: 10 }]}
    >
      <TextArea rows={3} placeholder="Ingrese el diagnóstico principal y diagnósticos asociados..." />
    </Form.Item>
  </div>
);

export default PasoHallazgos;
