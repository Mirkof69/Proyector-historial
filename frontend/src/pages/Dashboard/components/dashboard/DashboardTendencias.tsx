import React from 'react';
import { Row, Col, Card } from 'antd';
import { MedicalAreaChart } from '../../../../components/Charts';

interface DashboardTendenciasProps {
  chartData: any[];
}

const DashboardTendencias: React.FC<DashboardTendenciasProps> = ({ chartData }) => (
  <Row gutter={[16, 16]}>
    <Col span={24}>
      <Card
        className="shadow-card"
        title="Actividad de los últimos 30 días"
        extra={<span className="texto-secundario">Por día, de todo el establecimiento</span>}
      >
        <MedicalAreaChart
          type="area"
          data={chartData}
          series={[
            { dataKey: 'controles', name: 'Controles prenatales', color: 'var(--grafico-1)' },
            { dataKey: 'citas', name: 'Citas atendidas', color: 'var(--grafico-2)' },
            { dataKey: 'examenes', name: 'Exámenes pedidos', color: 'var(--grafico-3)' },
            { dataKey: 'pacientes', name: 'Pacientes nuevas', color: 'var(--grafico-4)' },
          ]}
          xAxisKey="name"
          height={300}
          title="Actividad de los últimos 30 días"
          subtitle="Por día, de todo el establecimiento"
          colors={['var(--grafico-1)', 'var(--grafico-2)', 'var(--grafico-3)', 'var(--grafico-4)']}
          key="chart-tendencias-full"
        />
      </Card>
    </Col>
  </Row>
);

export default DashboardTendencias;
