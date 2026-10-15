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

    <Row gutter={[16, 16]} className="calc-fila-stats">
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Total Mediciones"
            value={historial.length}
            prefix={<LineChartOutlined />}
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Ganancia Promedio"
            value={promedioGanancia}
            suffix="kg"
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="% Ganancia Adecuada"
            value={tasaAdecuada}
            suffix="%"
          />
        </Card>
      </Col>
      <Col xs={12} sm={6}>
        <Card className="calc-stat-card">
          <Statistic
            title="Último Registro"
            value={historial[0]?.semanas || 0}
            suffix="sem"
          />
        </Card>
      </Col>
    </Row>

    <Card title="Historial de Mediciones">
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
