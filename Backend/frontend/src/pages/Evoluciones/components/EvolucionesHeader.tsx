import React from 'react';
import { Button, Row, Col, Space, Typography } from 'antd';
import { PlusOutlined, ReloadOutlined, FileTextOutlined, ExportOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

interface EvolucionesHeaderProps {
  loading: boolean;
  onReload: () => void;
  onExport: () => void;
}

const EvolucionesHeader: React.FC<EvolucionesHeaderProps> = ({ loading, onReload, onExport }) => {
  const navigate = useNavigate();

  return (
    <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
      <Row justify="space-between" align="middle">
        <Col>
          <Space align="center" size="large">
            <div className="header-icon-container">
              <FileTextOutlined style={{ fontSize: '32px', color: '#fff' }} />
            </div>
            <div>
              <Title level={2} style={{ color: '#fff', margin: 0 }}>Evolución Clínica del Embarazo</Title>
              <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Historial consolidado de seguimientos, diagnósticos y eventos clínicos</Text>
            </div>
          </Space>
        </Col>
        <Col>
          <Space>
            <Button
              type="primary"
              size="large"
              icon={<PlusOutlined />}
              onClick={() => navigate('/dashboard/evoluciones/nuevo')}
              className="btn-success-gradient"
            >
              Nueva Evolución
            </Button>
            <Button
              size="large"
              icon={<ExportOutlined />}
              onClick={onExport}
            >
              Exportar
            </Button>
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={onReload}
              loading={loading}
            />
          </Space>
        </Col>
      </Row>
    </div>
  );
};

export default EvolucionesHeader;
