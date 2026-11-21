import React from 'react';
import { Alert, Card, Statistic, Typography } from 'antd';
import {
  MedicineBoxOutlined, CalendarOutlined, ClockCircleOutlined,
  WarningOutlined, BarChartOutlined, SafetyOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

interface VacunasStatsProps {
  stats: {
    total: number;
    conProximaDosis: number;
    conReacciones: number;
    esteMes: number;
    vencidas: number;
    proximaSemana: number;
  };
}

const VacunasStats: React.FC<VacunasStatsProps> = ({ stats }) => (
  <>
    {/* ALERTS SECTION */}
    {(stats.vencidas > 0 || stats.proximaSemana > 0) && (
      <div className="vacunas-page__avisos">
        {stats.vencidas > 0 && (
            <Alert
              message={<Text strong>Dosis Retrasadas detectadas</Text>}
              description={`${stats.vencidas} pacientes requieren atención inmediata por esquemas vencidos.`}
              type="error"
              showIcon
              icon={<WarningOutlined />}
            />
        )}
        {stats.proximaSemana > 0 && (
            <Alert
              message={<Text strong>Próximas Dosis (7 días)</Text>}
              description={`${stats.proximaSemana} dosis programadas para la siguiente semana.`}
              type="warning"
              showIcon
            />
        )}
      </div>
    )}

    {/* STATISTICS CARDS */}
    <div className="vacunas-page__cifras">
      <Card size="small">
        <Statistic title={<><MedicineBoxOutlined />Total Aplicadas</>} value={stats.total} />
      </Card>
      <Card size="small">
        <Statistic title={<><CalendarOutlined />Este Mes</>} value={stats.esteMes} />
      </Card>
      <Card size="small">
        <Statistic title={<><ClockCircleOutlined />Seguimientos</>} value={stats.conProximaDosis} />
      </Card>
      <Card size="small" className={stats.vencidas > 0 ? 'vacunas-page__cifra--peligro' : undefined}>
        <Statistic title={<><WarningOutlined />Vencidas</>} value={stats.vencidas} />
      </Card>
      <Card size="small" className={stats.conReacciones > 0 ? 'vacunas-page__cifra--aviso' : undefined}>
        <Statistic title={<><SafetyOutlined />Reacciones</>} value={stats.conReacciones} />
      </Card>
      <Card size="small">
        <Statistic title={<><BarChartOutlined />Cobertura</>} value={((stats.total / (stats.total + stats.vencidas || 1)) * 100).toFixed(0)} suffix="%" />
      </Card>
    </div>
  </>
);

export default VacunasStats;
