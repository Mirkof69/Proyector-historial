import React from 'react';
import { Card, Statistic } from 'antd';
import { ExperimentOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';

interface LaboratorioStatsProps {
  total: number;
  solicitados: number;
  en_proceso: number;
  completados: number;
  con_anormales: number;
  con_criticos: number;
}

const LaboratorioStats: React.FC<LaboratorioStatsProps> = ({
  total, solicitados, en_proceso, completados, con_anormales, con_criticos,
}) => (
  <div className="laboratorio-page__cifras">
    <Card size="small">
      <Statistic title={<><ExperimentOutlined />Total Exámenes</>} value={total} />
    </Card>
    <Card size="small">
      <Statistic title="Solicitados" value={solicitados} />
    </Card>
    <Card size="small">
      <Statistic title="En Proceso" value={en_proceso} />
    </Card>
    <Card size="small">
      <Statistic title="Completados" value={completados} />
    </Card>
    <Card size="small" className={con_anormales > 0 ? 'laboratorio-page__cifra--aviso' : undefined}>
      <Statistic title={<><ExclamationCircleOutlined />Con Anormales</>} value={con_anormales} />
    </Card>
    <Card size="small" className={con_criticos > 0 ? 'laboratorio-page__cifra--peligro' : undefined}>
      <Statistic title={<><WarningOutlined />Con Críticos</>} value={con_criticos} />
    </Card>
  </div>
);

export default LaboratorioStats;
