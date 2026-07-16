import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { FileImageOutlined } from '@ant-design/icons';

interface EcografiasStatsProps {
  estadisticas: {
    total: number;
    primerTrimestre: number;
    segundoTrimestre: number;
    tercerTrimestre: number;
    conAlertas: number;
  };
}

const EcografiasStats: React.FC<EcografiasStatsProps> = ({ estadisticas }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Total Ecografías"
          value={estadisticas.total}
          prefix={<FileImageOutlined />}
          valueStyle={{ color: '#722ed1' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Primer Trimestre"
          value={estadisticas.primerTrimestre}
          valueStyle={{ color: '#13c2c2' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Segundo Trimestre"
          value={estadisticas.segundoTrimestre}
          valueStyle={{ color: '#1890ff' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card>
        <Statistic
          title="Tercer Trimestre"
          value={estadisticas.tercerTrimestre}
          valueStyle={{ color: '#722ed1' }}
        />
      </Card>
    </Col>
  </Row>
);

export default EcografiasStats;
