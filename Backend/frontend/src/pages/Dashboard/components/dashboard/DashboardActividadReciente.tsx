import React from 'react';
import { Row, Col, Card, Timeline, Space, Typography } from 'antd';
import { BellOutlined, WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

interface ActividadReciente {
  id: number;
  usuario: string;
  accion: string;
  fecha: string;
  tipo: 'info' | 'warning' | 'success' | 'danger';
  _uniqueKey?: string;
}

interface DashboardActividadProps {
  actividades: ActividadReciente[];
}

const DashboardActividadReciente: React.FC<DashboardActividadProps> = ({ actividades }) => (
  <Col xs={24} lg={12}>
    <Card
      title={<Space><BellOutlined /><span>Actividad Reciente</span></Space>}
      className="shadow-card"
    >
      <Timeline
        items={actividades.map((act) => ({
          key: act._uniqueKey || `act-${act.id}`,
          dot: act.tipo === 'warning' ? <WarningOutlined style={{ color: 'orange' }} /> :
            act.tipo === 'success' ? <CheckCircleOutlined style={{ color: 'green' }} /> : undefined,
          children: (
            <div>
              <Text strong>{act.usuario}</Text>
              <br />
              <Text type="secondary">{act.accion}</Text>
              <br />
              <Text type="secondary" style={{ fontSize: 12 }}>{dayjs(act.fecha).fromNow()}</Text>
            </div>
          )
        }))}
      />
    </Card>
  </Col>
);

export default DashboardActividadReciente;
