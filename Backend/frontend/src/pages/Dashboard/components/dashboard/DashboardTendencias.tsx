import React from 'react';
import { Row, Col, Card } from 'antd';
import dayjs from 'dayjs';
import { MedicalAreaChart } from '../../../../components/Charts';

interface DashboardTendenciasProps {
  chartData: any[];
}

const DashboardTendencias: React.FC<DashboardTendenciasProps> = ({ chartData }) => (
  <Row gutter={[16, 16]}>
    <Col span={24}>
      <Card
        className="shadow-card"
        title="Estadísticas y Alertas en Tiempo Real"
        extra={<span className="texto-secundario">{`Tendencias diarias de ${dayjs().format('MMMM YYYY')}`}</span>}
      >
        <MedicalAreaChart
          type="area"
          data={chartData}
          series={[
            { dataKey: 'pacientes', name: 'Nuevos Pacientes', color: 'var(--grafico-1)' },
            { dataKey: 'citas', name: 'Citas Atendidas', color: 'var(--grafico-2)' }
          ]}
          xAxisKey="name"
          height={300}
          title="Estadísticas y Alertas en Tiempo Real"
          subtitle={`Tendencias diarias de ${dayjs().format('MMMM YYYY')}`}
          colors={['var(--grafico-1)', 'var(--grafico-2)']}
          key="chart-tendencias-full"
        />
      </Card>
    </Col>
  </Row>
);

export default DashboardTendencias;
