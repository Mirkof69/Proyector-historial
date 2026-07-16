import React from 'react';
import { Row, Col, Statistic, Progress } from 'antd';
import { LineChartOutlined, WarningOutlined, BulbOutlined } from '@ant-design/icons';

interface IAStatsPanelProps {
  estadisticasIA: {
    analisisRealizados: number;
    alertasGeneradas: number;
    recomendacionesDadas: number;
    precision: number;
  };
}

const IAStatsPanel: React.FC<IAStatsPanelProps> = ({ estadisticasIA }) => (
  <>
    <Row gutter={8} style={{ marginBottom: 16 }}>
      <Col span={8}>
        <Statistic
          title="Análisis"
          value={estadisticasIA.analisisRealizados}
          prefix={<LineChartOutlined />}
          valueStyle={{ fontSize: 16 }}
        />
      </Col>
      <Col span={8}>
        <Statistic
          title="Alertas"
          value={estadisticasIA.alertasGeneradas}
          prefix={<WarningOutlined />}
          valueStyle={{ fontSize: 16, color: '#ff4d4f' }}
        />
      </Col>
      <Col span={8}>
        <Statistic
          title="Recomendaciones"
          value={estadisticasIA.recomendacionesDadas}
          prefix={<BulbOutlined />}
          valueStyle={{ fontSize: 16, color: '#52c41a' }}
        />
      </Col>
    </Row>

    <Progress
      percent={estadisticasIA.precision}
      strokeColor={{ from: '#108ee9', to: '#87d068' }}
      status="active"
      format={percent => `Precisión: ${percent}%`}
    />
  </>
);

export default IAStatsPanel;
