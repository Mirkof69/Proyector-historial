// Página Principal de Pacientes
import React from 'react';
import { Card } from 'antd';
import PacientesList from './PacientesList';

const PacientesPage: React.FC = () => {
  return (
    <div style={{ padding: 24 }}>
      <Card title="Gestión de Pacientes">
        <PacientesList />
      </Card>
    </div>
  );
};

export default PacientesPage;
