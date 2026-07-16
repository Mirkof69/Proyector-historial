import React from 'react';
import { Card, Row, Col, Statistic, Table, Divider } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { RegistroIMC } from '../imcGananciaUtils';
import { columnsIMC } from './columnsIMC';

interface IMCHistorialProps {
  historial: RegistroIMC[];
  promedioGanancia: string;
  tasaAdecuada: string;
}

const IMCHistorial: React.FC<IMCHistorialProps> = ({ historial, promedioGanancia, tasaAdecuada }) => (
  <>
    <Divider>Estadísticas del Historial</Divider>

    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={12} sm={6}>
        <Card bordered={false}>
          <Statistic
            title="Total Mediciones"
            value={historial.length}
            prefix={<LineChartOutlined />}
            valueStyle={{ color: '#1890ff' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card bordered={false}>
          <Statistic
            title="Ganancia Promedio"
            value={promedioGanancia}
            suffix="kg"
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card bordered={false}>
          <Statistic
            title="% Ganancia Adecuada"
            value={tasaAdecuada}
            suffix="%"
            valueStyle={{ color: '#722ed1' }}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card bordered={false}>
          <Statistic
            title="Último Registro"
            value={historial[0]?.semanas || 0}
            suffix="sem"
            valueStyle={{ color: '#fa8c16' }}
          />
        </Card>
      </Col>
    </Row>

    <Card title="Historial de Mediciones" bordered={false}>
      <Table
        columns={columnsIMC}
        dataSource={historial}
        rowKey="id"
        pagination={{ pageSize: 10 }}
        scroll={{ x: 800 }}
      />
    </Card>
  </>
);

export default IMCHistorial;
