import React from 'react';
import { Space, Button, Typography } from 'antd';
import { ArrowLeftOutlined, CloseOutlined, SaveOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface FormularioVacunaHeaderProps {
  esEdicion: boolean;
  submitting: boolean;
  onCancelar: () => void;
  onGuardar: () => void;
}

const FormularioVacunaHeader: React.FC<FormularioVacunaHeaderProps> = ({ esEdicion, submitting, onCancelar, onGuardar }) => (
  <header className="vacunas-page__cabecera">
    <div>
      <Title level={2}>
        {esEdicion ? 'Editar Registro' : 'Nueva Inmunización'}
      </Title>
      <Text type="secondary">Registro oficial de aplicación de vacunas y biológicos</Text>
    </div>
    <Space wrap>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={onCancelar}
        aria-label="Volver"
      />
      <Button
        icon={<CloseOutlined />}
        onClick={onCancelar}
      >
        Cancelar
      </Button>
      <Button
        type="primary"
        icon={<SaveOutlined />}
        onClick={onGuardar}
        loading={submitting}
      >
        {esEdicion ? 'Actualizar Registro' : 'Guardar Inmunización'}
      </Button>
    </Space>
  </header>
);

export default FormularioVacunaHeader;
