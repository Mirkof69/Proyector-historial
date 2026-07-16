import React from 'react';
import { Card, Space, Row, Col, Statistic, Divider, Progress } from 'antd';
import {
  ExperimentOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';

interface ResumenResultadosLabProps {
  resumen: any;
}

const ResumenResultadosLab: React.FC<ResumenResultadosLabProps> = ({ resumen }) => (
  <Card
    title={
      <Space>
        <InfoCircleOutlined />
        Resumen de Resultados
      </Space>
    }
    style={{ marginBottom: 16 }}
  >
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Total Parámetros"
            value={resumen.total_parametros}
            prefix={<ExperimentOutlined />}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Normales"
            value={resumen.normales}
            valueStyle={{ color: '#52c41a' }}
            prefix={<CheckCircleOutlined />}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Anormales"
            value={resumen.anormales}
            valueStyle={{ color: '#faad14' }}
            prefix={<ExclamationCircleOutlined />}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic
            title="Críticos"
            value={resumen.criticos}
            valueStyle={{ color: '#ff4d4f' }}
            prefix={<WarningOutlined />}
          />
        </Card>
      </Col>
    </Row>
    <Divider />
    <Progress
      percent={resumen.porcentaje_normalidad}
      status={resumen.porcentaje_normalidad >= 80 ? 'success' : resumen.porcentaje_normalidad >= 50 ? 'normal' : 'exception'}
      format={(percent) => `${percent}% de normalidad`}
    />
  </Card>
);

export default ResumenResultadosLab;
