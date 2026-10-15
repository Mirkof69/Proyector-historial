import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import { FileImageOutlined } from '@ant-design/icons';

interface EcografiasStatsProps {
  estadisticas: {
    total: number;
    primerTrimestre: number;
    segundoTrimestre: number;
    tercerTrimestre: number;
  };
}

const EcografiasStats: React.FC<EcografiasStatsProps> = ({ estadisticas }) => (
  <Row gutter={[16, 16]} className="pc-cifras">
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Total Ecografías"
          value={estadisticas.total}
          prefix={<FileImageOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Primer Trimestre"
          value={estadisticas.primerTrimestre}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Segundo Trimestre"
          value={estadisticas.segundoTrimestre}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6}>
      <Card className="pc-cifra">
        <Statistic
          title="Tercer Trimestre"
          value={estadisticas.tercerTrimestre}
        />
      </Card>
    </Col>
  </Row>
);

export default EcografiasStats;
