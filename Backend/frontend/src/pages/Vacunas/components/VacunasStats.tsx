import React from 'react';
import { Row, Col, Alert, Typography } from 'antd';
import {
  MedicineBoxOutlined, CalendarOutlined, ClockCircleOutlined,
  WarningOutlined, BarChartOutlined, SafetyOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface VacunasStatsProps {
  stats: {
    total: number;
    conProximaDosis: number;
    conReacciones: number;
    esteMes: number;
    vencidas: number;
    proximaSemana: number;
  };
}

const VacunasStats: React.FC<VacunasStatsProps> = ({ stats }) => (
  <>
    {/* ALERTS SECTION */}
    {(stats.vencidas > 0 || stats.proximaSemana > 0) && (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        {stats.vencidas > 0 && (
          <Col span={stats.proximaSemana > 0 ? 12 : 24}>
            <Alert
              message={<Text strong>Dosis Retrasadas detectadas</Text>}
              description={`${stats.vencidas} pacientes requieren atención inmediata por esquemas vencidos.`}
              type="error"
              showIcon
              icon={<WarningOutlined className="status-pulse" />}
              style={{ borderRadius: '8px' }}
            />
          </Col>
        )}
        {stats.proximaSemana > 0 && (
          <Col span={stats.vencidas > 0 ? 12 : 24}>
            <Alert
              message={<Text strong>Próximas Dosis (7 días)</Text>}
              description={`${stats.proximaSemana} dosis programadas para la siguiente semana.`}
              type="warning"
              showIcon
              style={{ borderRadius: '8px' }}
            />
          </Col>
        )}
      </Row>
    )}

    {/* STATISTICS CARDS */}
    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium blue">
          <div className="stat-icon"><MedicineBoxOutlined /></div>
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Aplicadas</div>
        </div>
      </Col>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium green">
          <div className="stat-icon"><CalendarOutlined /></div>
          <div className="stat-value">{stats.esteMes}</div>
          <div className="stat-label">Este Mes</div>
        </div>
      </Col>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium orange">
          <div className="stat-icon"><ClockCircleOutlined /></div>
          <div className="stat-value">{stats.conProximaDosis}</div>
          <div className="stat-label">Seguimientos</div>
        </div>
      </Col>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium red">
          <div className="stat-icon"><WarningOutlined /></div>
          <div className="stat-value">{stats.vencidas}</div>
          <div className="stat-label">Vencidas</div>
        </div>
      </Col>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium purple">
          <div className="stat-icon"><SafetyOutlined /></div>
          <div className="stat-value">{stats.conReacciones}</div>
          <div className="stat-label">Reacciones</div>
        </div>
      </Col>
      <Col xs={12} md={6} lg={4}>
        <div className="stat-card-premium cyan">
          <div className="stat-icon"><BarChartOutlined /></div>
          <div className="stat-value">{((stats.total / (stats.total + stats.vencidas || 1)) * 100).toFixed(0)}%</div>
          <div className="stat-label">Cobertura</div>
        </div>
      </Col>
    </Row>
  </>
);

export default VacunasStats;
