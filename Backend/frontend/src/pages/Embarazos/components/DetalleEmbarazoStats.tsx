import React from 'react';
import { Card, Tag, Row, Col, Typography, Progress, Statistic, Badge } from 'antd';
import {
  CalendarOutlined, ClockCircleOutlined, LineChartOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Embarazo } from '../../../services/embarazosService';
import { ControlPrenatal } from '../../../services/controlesService';

const { Text } = Typography;

interface DetalleEmbarazoStatsProps {
  eg: { semanas: number; dias: number; texto: string };
  diasRestantes: number;
  progreso: number;
  trimestre: { numero: number; texto: string; color: string };
  embarazo: Embarazo;
  controles: ControlPrenatal[];
  controlesConAlertas: number;
}

const DetalleEmbarazoStats: React.FC<DetalleEmbarazoStatsProps> = ({
  eg, diasRestantes, progreso, trimestre, embarazo, controles, controlesConAlertas,
}) => (
  <Row gutter={16} style={{ marginBottom: 16 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Edad Gestacional"
          value={eg.semanas}
          suffix={`semanas + ${eg.dias}d`}
          prefix={<CalendarOutlined />}
          valueStyle={{ color: '#1890ff' }}
        />
        <Tag color={trimestre.color} style={{ marginTop: 8 }}>
          {trimestre.texto}
        </Tag>
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Días hasta FPP"
          value={diasRestantes}
          suffix="días"
          prefix={<ClockCircleOutlined />}
          valueStyle={{ color: diasRestantes < 30 ? '#ff4d4f' : '#52c41a' }}
        />
        <Text type="secondary" style={{ fontSize: 12 }}>
          {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
        </Text>
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Progreso Gestacional"
          value={progreso}
          suffix="%"
          prefix={<LineChartOutlined />}
          valueStyle={{ color: '#3f8600' }}
        />
        <Progress
          percent={progreso}
          showInfo={false}
          strokeColor={{
            '0%': '#87d068',
            '50%': '#1890ff',
            '100%': '#722ed1',
          }}
          style={{ marginTop: 8 }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Controles Realizados"
          value={controles.length}
          prefix={<MedicineBoxOutlined />}
          valueStyle={{ color: controles.length >= trimestre.numero * 3 ? '#52c41a' : '#faad14' }}
        />
        {controlesConAlertas > 0 && (
          <Badge count={controlesConAlertas} style={{ marginTop: 8 }}>
            <Tag color="error">Con alertas</Tag>
          </Badge>
        )}
      </Card>
    </Col>
  </Row>
);

export default DetalleEmbarazoStats;
