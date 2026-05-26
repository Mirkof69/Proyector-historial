import React from 'react';
import { Row, Col, Card } from 'antd';
import dayjs from 'dayjs';
import { MedicalAreaChart } from '../../../../components/Charts';

interface DashboardTendenciasProps {
  chartData: any[];
}

const DashboardTendencias: React.FC<DashboardTendenciasProps> = ({ chartData }) => (
  <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
    <Col span={24}>
      <Card className="shadow-card">
        <MedicalAreaChart
          type="area"
          data={chartData}
          series={[
            { dataKey: 'pacientes', name: 'Nuevos Pacientes', color: '#722ed1' },
            { dataKey: 'citas', name: 'Citas Atendidas', color: '#f5222d' }
          ]}
          xAxisKey="name"
          height={300}
          title="Estadísticas y Alertas en Tiempo Real"
          subtitle={`Tendencias diarias de ${dayjs().format('MMMM YYYY')}`}
          colors={['#722ed1', '#f5222d']}
          key="chart-tendencias-full"
        />
      </Card>
    </Col>
  </Row>
);

export default DashboardTendencias;
