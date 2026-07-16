import React from 'react';
import { Form, Input, Divider, Typography } from 'antd';

const { TextArea } = Input;
const { Text } = Typography;

const PasoPrescripcion: React.FC = () => (
  <div style={{ padding: '16px' }}>
    <Form.Item label={<Text strong>Tratamiento / Prescripción Médica</Text>} name="tratamiento">
      <TextArea rows={5} placeholder="Medicamentos, dosis, frecuencia y vía de administración..." />
    </Form.Item>

    <Divider />

    <Form.Item label={<Text strong>Plan de Seguimiento / Próximos Pasos</Text>} name="plan">
      <TextArea rows={5} placeholder="Exámenes solicitados, interconsultas, fecha de próximo control..." />
    </Form.Item>
  </div>
);

export default PasoPrescripcion;
