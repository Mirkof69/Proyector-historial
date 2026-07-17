import React from 'react';
import { Card, Row, Col, Button, Space, Divider, Tag, Typography } from 'antd';
import {
  ExpandOutlined, InfoCircleOutlined, SettingOutlined, DownloadOutlined,
  FullscreenOutlined, FullscreenExitOutlined, FileImageOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ViewerAction } from '../visorDicomReducer';

const { Text } = Typography;

interface VisorTopBarProps {
  ecografia: any;
  fullscreen: boolean;
  dispatch: React.Dispatch<ViewerAction>;
  toggleFullscreen: () => void;
  onVolver: () => void;
}

const VisorTopBar: React.FC<VisorTopBarProps> = ({
  ecografia, fullscreen, dispatch, toggleFullscreen, onVolver,
}) => (
  <Card
    size="small"
    style={{ borderRadius: 0, background: '#141414' }}
    styles={{ body: { padding: '8px 16px' } }}
  >
    <Row justify="space-between" align="middle">
      <Col>
        <Space>
          <Button
            size="small"
            icon={<ExpandOutlined />}
            onClick={onVolver}
          >
            Volver
          </Button>
          <Divider type="vertical" style={{ background: '#434343' }} />
          <Text style={{ color: '#fff' }}>
            <FileImageOutlined /> {ecografia.tipo_ecografia || 'Ecografía'}
          </Text>
          <Tag color="blue">{ecografia.paciente_nombre}</Tag>
          <Tag color="green">{dayjs(ecografia.fecha).format('DD/MM/YYYY')}</Tag>
        </Space>
      </Col>
      <Col>
        <Space>
          <Button
            size="small"
            icon={<InfoCircleOutlined />}
            onClick={() => dispatch({ type: 'TOGGLE_METADATA' })}
          >
            Metadata
          </Button>
          <Button
            size="small"
            icon={<SettingOutlined />}
            onClick={() => dispatch({ type: 'SET_SETTINGS_VISIBLE', payload: true })}
          >
            Configuración
          </Button>
          <Button
            size="small"
            icon={<DownloadOutlined />}
            onClick={() => dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: true })}
          >
            Exportar

          </Button>
          <Button
            size="small"
            icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={toggleFullscreen}
          >
            {fullscreen ? 'Salir' : 'Pantalla Completa'}
          </Button>
        </Space>
      </Col>
    </Row>
  </Card>
);

export default VisorTopBar;
