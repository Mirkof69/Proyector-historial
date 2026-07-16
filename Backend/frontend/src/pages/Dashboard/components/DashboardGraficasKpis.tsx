import React from 'react';
import { Card, Row, Col, Statistic, Typography, Tag, Badge } from 'antd';
import {
  HeartOutlined, WarningOutlined, CalendarOutlined,
  RiseOutlined, SmileOutlined, MedicineBoxOutlined,
  CheckCircleOutlined, ExperimentOutlined, FileImageOutlined, TeamOutlined,
} from '@ant-design/icons';
import { COLORS, DashboardKpis } from '../dashboardGraficasUtils';
import { useCountUp } from '../../../hooks/useCountUp';

const { Text } = Typography;

/** Statistic con conteo animado (premium) — respeta prefers-reduced-motion. */
const AnimatedStatistic: React.FC<React.ComponentProps<typeof Statistic> & { value: number }> = ({
  value,
  ...rest
}) => {
  const animated = useCountUp(value);
  return <Statistic {...rest} value={animated} />;
};

interface DashboardGraficasKpisProps {
  kpis: DashboardKpis;
}

const DashboardGraficasKpis: React.FC<DashboardGraficasKpisProps> = ({ kpis }) => (
  <>
    {/* KPIs Principales */}
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Badge count={kpis.pacientes.nuevosMes} offset={[-10, 10]} showZero>
          <Card className="stats-card">
            <AnimatedStatistic
              title="Pacientes Activos"
              value={kpis.pacientes.total}
              prefix={<TeamOutlined />}
              valueStyle={{ color: COLORS.primary }}
              suffix={
                <Tag color="green" icon={<RiseOutlined />}>
                  +{kpis.pacientes.nuevosMes} mes
                </Tag>
              }
            />
          </Card>
        </Badge>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Badge count={kpis.embarazos.altoRiesgo} offset={[-10, 10]}>
          <Card className="stats-card">
            <AnimatedStatistic
              title="Embarazos Activos"
              value={kpis.embarazos.activos}
              prefix={<HeartOutlined />}
              valueStyle={{ color: COLORS.success }}
              suffix={
                kpis.embarazos.altoRiesgo > 0 && (
                  <Tag color="red" icon={<WarningOutlined />}>
                    {kpis.embarazos.altoRiesgo} alto riesgo
                  </Tag>
                )
              }
            />
          </Card>
        </Badge>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Badge count={kpis.citas.pendientes} offset={[-10, 10]}>
          <Card className="stats-card">
            <AnimatedStatistic
              title="Citas Hoy"
              value={kpis.citas.hoy}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: COLORS.warning }}
              suffix={
                <Tag color="blue">
                  {kpis.citas.pendientes} pendientes
                </Tag>
              }
            />
          </Card>
        </Badge>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card className="stats-card">
          <AnimatedStatistic
            title="Partos este Mes"
            value={kpis.partos.mes}
            prefix={<SmileOutlined />}
            valueStyle={{ color: COLORS.purple }}
            suffix={
              <Tag color="orange">
                {kpis.partos.tasaCesarea}% cesáreas
              </Tag>
            }
          />
        </Card>
      </Col>
    </Row>

    {/* Estadísticas Adicionales con Iconos Restaurados */}
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} md={6}>
        <Card className="stats-card">
          <AnimatedStatistic
            title="Ecografías Realizadas"
            value={kpis.ecografias.mes}
            prefix={<FileImageOutlined />}
            valueStyle={{ color: COLORS.cyan }}
            suffix={<Text type="secondary">este mes</Text>}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card className="stats-card">
          <AnimatedStatistic
            title="Exámenes de Laboratorio"
            value={kpis.laboratorio.total}
            prefix={<ExperimentOutlined />}
            valueStyle={{ color: COLORS.orange }}
            suffix={
              <Badge count={kpis.laboratorio.pendientes} offset={[10, 0]}>
                <Tag color="orange">{kpis.laboratorio.pendientes} pendientes</Tag>
              </Badge>
            }
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card className="stats-card">
          <AnimatedStatistic
            title="Consultas Médicas"
            value={kpis.citas.semana}
            prefix={<MedicineBoxOutlined />}
            valueStyle={{ color: COLORS.green }}
            suffix={<Text type="secondary">esta semana</Text>}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card className="stats-card">
          <AnimatedStatistic
            title="Partos Exitosos"
            value={kpis.partos.total}
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: COLORS.success }}
            suffix={
              <Tag color="green" icon={<CheckCircleOutlined />}>
                Completados
              </Tag>
            }
          />
        </Card>
      </Col>
    </Row>
  </>
);

export default DashboardGraficasKpis;
