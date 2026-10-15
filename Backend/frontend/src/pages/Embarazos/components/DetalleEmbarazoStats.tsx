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
  <Row gutter={[16, 16]} className="pc-cifras">
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Edad Gestacional"
          value={eg.semanas}
          suffix={`semanas + ${eg.dias}d`}
          prefix={<CalendarOutlined />}
        />
        <Tag color={trimestre.color} className="u-mt-2">
          {trimestre.texto}
        </Tag>
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Días hasta FPP"
          value={diasRestantes}
          suffix="días"
          prefix={<ClockCircleOutlined />}
          valueStyle={{ color: diasRestantes < 30 ? 'var(--color-peligro)' : 'var(--color-exito)' }}
        />
        <Text type="secondary" className="u-t-xs">
          {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
        </Text>
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Progreso Gestacional"
          value={progreso}
          suffix="%"
          prefix={<LineChartOutlined />}
        />
        <Progress
          percent={progreso}
          showInfo={false}
          strokeColor="var(--color-primario)"
          className="u-mt-2"
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Controles Realizados"
          value={controles.length}
          prefix={<MedicineBoxOutlined />}
          valueStyle={{ color: controles.length >= trimestre.numero * 3 ? 'var(--color-exito)' : 'var(--color-aviso)' }}
        />
        {controlesConAlertas > 0 && (
          <Badge count={controlesConAlertas} className="u-mt-2">
            <Tag color="error">Con alertas</Tag>
          </Badge>
        )}
      </Card>
    </Col>
  </Row>
);

export default DetalleEmbarazoStats;
