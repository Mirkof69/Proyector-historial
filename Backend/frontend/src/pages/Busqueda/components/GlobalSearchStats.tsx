import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import {
  SearchOutlined, UserOutlined, HeartOutlined, CalendarOutlined,
  FileImageOutlined, ExperimentOutlined, FileTextOutlined, HomeOutlined, AlertOutlined,
} from '@ant-design/icons';

interface GlobalSearchStatsProps {
  totalResults: number;
  urgentResultsCount: number;
  pacientesResults: any[];
  embarazosResults: any[];
  citasResults: any[];
  ecografiasResults: any[];
  laboratorioResults: any[];
  evolucionesResults: any[];
  consultoriosResults: any[];
}

const GlobalSearchStats: React.FC<GlobalSearchStatsProps> = ({
  totalResults, urgentResultsCount, pacientesResults, embarazosResults, citasResults,
  ecografiasResults, laboratorioResults, evolucionesResults, consultoriosResults,
}) => (
  <Row gutter={16} style={{ marginTop: 16, marginBottom: 16 }}>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Total"
          value={totalResults}
          prefix={<SearchOutlined />}
          valueStyle={{ color: '#1890ff', fontSize: 20 }}
        />
      </Card>
    </Col>
    {urgentResultsCount > 0 && (
      <Col xs={24} sm={12} md={6} lg={3}>
        <Card size="small">
          <Statistic
            title="Urgentes"
            value={urgentResultsCount}
            prefix={<AlertOutlined />}
            valueStyle={{ color: '#ff4d4f', fontSize: 20 }}
          />
        </Card>
      </Col>
    )}
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Pacientes"
          value={pacientesResults.length}
          prefix={<UserOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Embarazos"
          value={embarazosResults.length}
          prefix={<HeartOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Citas"
          value={citasResults.length}
          prefix={<CalendarOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Ecografías"
          value={ecografiasResults.length}
          prefix={<FileImageOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Laboratorio"
          value={laboratorioResults.length}
          prefix={<ExperimentOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Evoluciones"
          value={evolucionesResults.length}
          prefix={<FileTextOutlined />}
        />
      </Card>
    </Col>
    <Col xs={24} sm={12} md={6} lg={3}>
      <Card size="small">
        <Statistic
          title="Consultorios"
          value={consultoriosResults.length}
          prefix={<HomeOutlined />}
        />
      </Card>
    </Col>
  </Row>
);

export default GlobalSearchStats;
