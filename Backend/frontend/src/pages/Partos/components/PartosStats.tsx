import React from 'react';
import { Row, Col, Card, Statistic } from 'antd';
import { MedicineBoxOutlined, WarningOutlined, WomanOutlined } from '@ant-design/icons';

interface PartosStatsProps {
  total: number;
  cesareas: number;
  vaginales: number;
}

const PartosStats: React.FC<PartosStatsProps> = ({ total, cesareas, vaginales }) => (
  <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
    <Col xs={24} sm={8}>
      <Card>
        <Statistic
          title="Total Partos Registrados"
          value={total}
          prefix={<MedicineBoxOutlined />}
          valueStyle={{ color: '#722ed1' }}
        />
      </Card>
    </Col>
    <Col xs={24} sm={8}>
      <Card>
        <Statistic
          title="Cesáreas"
          value={cesareas}
          suffix={`/ ${total}`}
          valueStyle={{ color: '#cf1322' }}
          prefix={<WarningOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={8}>
      <Card>
        <Statistic
          title="Partos Vaginales"
          value={vaginales}
          suffix={`/ ${total}`}
          valueStyle={{ color: '#389e0d' }}
          prefix={<WomanOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default PartosStats;
