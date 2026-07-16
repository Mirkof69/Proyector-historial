import React from 'react';
import { Row, Col, Space, Button, Typography } from 'antd';
import { ArrowLeftOutlined, EditOutlined, CloseOutlined, SaveOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

interface FormularioEvolucionHeaderProps {
  esEdicion: boolean;
  submitting: boolean;
  onCancelar: () => void;
  onGuardar: () => void;
}

const FormularioEvolucionHeader: React.FC<FormularioEvolucionHeaderProps> = ({
  esEdicion,
  submitting,
  onCancelar,
  onGuardar,
}) => (
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
            <EditOutlined style={{ fontSize: '32px', color: '#fff' }} />
          </div>
          <div>
            <Title level={2} style={{ color: '#fff', margin: 0 }}>
              {esEdicion ? 'Actualizar Evolución' : 'Registro de Evolución'}
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Documentación clínica del paciente conforme a estándares internacionales</Text>
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
            {esEdicion ? 'Guardar Cambios' : 'Finalizar Registro'}
          </Button>
        </Space>
      </Col>
    </Row>
  </div>
);

export default FormularioEvolucionHeader;
