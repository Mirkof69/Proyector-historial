import React from 'react';
import { Space, Alert, Form, Select } from 'antd';

interface PasoIdentificacionProps {
  pacientes: any[];
}

const PasoIdentificacion: React.FC<PasoIdentificacionProps> = ({ pacientes }) => (
  <Space direction="vertical" size="middle" style={{ width: '100%', padding: '16px' }}>
    <Alert
      message="Selección del Paciente"
      description="Vincule esta nota de evolución a un paciente registrado en el sistema."
      type="info"
      showIcon
      style={{ borderRadius: '8px' }}
    />
    <Form.Item label="Paciente" name="paciente" rules={[{ required: true, message: 'Debe seleccionar un paciente' }]}>
      <Select
        placeholder="Escriba nombre o cédula para buscar..."
        showSearch
        size="large"
        style={{ width: '100%' }}
        filterOption={(input, option) =>
          (option?.label as string).toLowerCase().includes(input.toLowerCase())
        }
        options={pacientes.map(p => ({
          label: `${p.nombre} ${p.apellido_paterno || p.apellido} - ${p.ci || p.id_clinico}`,
          value: p.id,
        }))}
      />
    </Form.Item>
  </Space>
);

export default PasoIdentificacion;
