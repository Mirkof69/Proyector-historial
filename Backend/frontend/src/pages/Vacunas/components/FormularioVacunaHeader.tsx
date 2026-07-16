import React from 'react';
import { Row, Col, Space, Button, Typography } from 'antd';
import { ArrowLeftOutlined, SafetyOutlined, CloseOutlined, SaveOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface FormularioVacunaHeaderProps {
  esEdicion: boolean;
  submitting: boolean;
  onCancelar: () => void;
  onGuardar: () => void;
}

const FormularioVacunaHeader: React.FC<FormularioVacunaHeaderProps> = ({ esEdicion, submitting, onCancelar, onGuardar }) => (
  <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
    <Row justify="space-between" align="middle">
      <Col>
        <Space align="center" size="large">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={onCancelar}
            className="back-button-white"
          />
          <div className="header-icon-container">
            <SafetyOutlined style={{ fontSize: '32px', color: '#fff' }} />
          </div>
          <div>
            <Title level={2} style={{ color: '#fff', margin: 0 }}>
              {esEdicion ? 'Editar Registro' : 'Nueva Inmunización'}
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Registro oficial de aplicación de vacunas y biológicos</Text>
          </div>
        </Space>
      </Col>
      <Col>
        <Space>
          <Button
            size="large"
            icon={<CloseOutlined />}
            onClick={onCancelar}
          >
            Cancelar
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<SaveOutlined />}
            onClick={onGuardar}
            loading={submitting}
            className="btn-success-gradient"
          >
            {esEdicion ? 'Actualizar Registro' : 'Guardar Inmunización'}
          </Button>
        </Space>
      </Col>
    </Row>
  </div>
);

export default FormularioVacunaHeader;
