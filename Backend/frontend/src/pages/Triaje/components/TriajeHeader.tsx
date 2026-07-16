import React from 'react';
import { Row, Col, Space, Button, Typography } from 'antd';
import { ArrowLeftOutlined, PrinterOutlined, EditOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { TriajeEnfermeria } from '../../../services/triajeService';

const { Title, Text } = Typography;

interface TriajeHeaderProps {
  triaje: TriajeEnfermeria;
  onVolver: () => void;
  onEditar: () => void;
}

const TriajeHeader: React.FC<TriajeHeaderProps> = ({ triaje, onVolver, onEditar }) => (
  <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '24px' }}>
    <Row justify="space-between" align="middle">
      <Col>
        <Space size="large">
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={onVolver}
            ghost
          />
          <div>
            <Title level={2} style={{ color: '#fff', margin: 0 }}>
              Detalle de Evaluación de Triaje
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>
              ID Registro: #{triaje.id} | Fecha: {dayjs(triaje.fecha_registro).format('DD/MM/YYYY HH:mm')}
            </Text>
          </div>
        </Space>
      </Col>
      <Col>
        <Space>
          <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
            Imprimir Informe
          </Button>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={onEditar}
          >
            Editar Registro
          </Button>
        </Space>
      </Col>
    </Row>
  </div>
);

export default TriajeHeader;
