import React from 'react';
import { Row, Col, Card, Button, List, Avatar, Space, Tag, Typography } from 'antd';
import { ClockCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import WidgetPacientesAltoRiesgo from '../../../../components/Widgets/WidgetPacientesAltoRiesgo';

const { Text } = Typography;

interface CitaHoy {
  id: number;
  paciente_nombre: string;
  hora: string;
  motivo: string;
  estado: string;
  _uniqueKey?: string;
}

interface DashboardAgendaProps {
  citasHoy: CitaHoy[];
}

const DashboardAgenda: React.FC<DashboardAgendaProps> = ({ citasHoy }) => {
  const navigate = useNavigate();

  return (
    <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
      <Col xs={24} lg={16}>
        <Card title="Agenda del Día" extra={<Button type="link" onClick={() => navigate('/dashboard/citas')} style={{ padding: 0 }}>Ver todo</Button>} className="shadow-card">
          <List
            itemLayout="horizontal"
            dataSource={citasHoy}
            rowKey={(item) => item._uniqueKey || `cita-fallback-${item.id}`}
            renderItem={(item: CitaHoy) => (
              <List.Item>
                <List.Item.Meta
                  avatar={<Avatar icon={<ClockCircleOutlined />} style={{ backgroundColor: '#1890ff' }} />}
                  title={<span><strong>{item.hora}</strong> - {item.paciente_nombre}</span>}
                  description={
                    <Space>
                      <Tag color={item.estado === 'CONFIRMADA' ? 'green' : 'orange'}>{item.estado}</Tag>
                      <Text type="secondary">{item.motivo}</Text>
                    </Space>
                  }
                />
              </List.Item>
            )}
            locale={{ emptyText: 'No hay citas programadas para hoy' }}
          />
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <WidgetPacientesAltoRiesgo />
      </Col>
    </Row>
  );
};

export default DashboardAgenda;
