import React from 'react';
import {
  FileImageOutlined, FundProjectionScreenOutlined, CheckCircleOutlined,
  WarningOutlined, DashboardOutlined,
} from '@ant-design/icons';
import { EstadisticasIA } from '../../../services/iaMedicaService';
import { useCountUp } from '../../../hooks/useCountUp';

/** Número con conteo animado para las stat-cards custom del módulo IA. */
const AnimatedNumber: React.FC<{ value: number; decimals?: number; suffix?: string }> = ({
  value, decimals = 0, suffix = '',
}) => {
  const animated = useCountUp(Number(value) || 0, 900, decimals);
  return <>{animated}{suffix}</>;
};

interface IaMedicaStatsProps {
  estadisticas: EstadisticasIA;
}

const IaMedicaStats: React.FC<IaMedicaStatsProps> = ({ estadisticas }) => (
  <div className="stats-grid">
    <div className="stat-card stats-card">
      <div className="stat-icon primary"><FileImageOutlined /></div>
      <div className="stat-content">
        <h3>Total Imágenes</h3>
        <p><AnimatedNumber value={estadisticas.total_imagenes} /></p>
      </div>
    </div>
    <div className="stat-card stats-card">
      <div className="stat-icon primary"><FundProjectionScreenOutlined /></div>
      <div className="stat-content">
        <h3>Análisis CNN Realizados</h3>
        <p><AnimatedNumber value={estadisticas.total_analisis} /></p>
      </div>
    </div>
    <div className="stat-card stats-card">
      <div className="stat-icon success"><CheckCircleOutlined /></div>
      <div className="stat-content">
        <h3>Casos Normales</h3>
        <p><AnimatedNumber value={estadisticas.analisis_normales} /></p>
      </div>
    </div>
    <div className="stat-card stats-card">
      <div className="stat-icon warning"><WarningOutlined /></div>
      <div className="stat-content">
        <h3>Anomalías Detectadas</h3>
        <p><AnimatedNumber value={estadisticas.analisis_anomalias} /></p>
      </div>
    </div>
    <div className="stat-card stats-card">
      <div className="stat-icon primary"><DashboardOutlined /></div>
      <div className="stat-content">
        <h3>Confianza Promedio</h3>
        <p><AnimatedNumber value={estadisticas.confianza_promedio} decimals={1} suffix="%" /></p>
      </div>
    </div>
  </div>
);

export default IaMedicaStats;
