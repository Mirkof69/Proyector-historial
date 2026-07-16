import React from 'react';
import {
  FileImageOutlined, FundProjectionScreenOutlined, CheckCircleOutlined,
  WarningOutlined, DashboardOutlined,
} from '@ant-design/icons';
import { EstadisticasIA } from '../../../services/iaMedicaService';

interface IaMedicaStatsProps {
  estadisticas: EstadisticasIA;
}

const IaMedicaStats: React.FC<IaMedicaStatsProps> = ({ estadisticas }) => (
  <div className="stats-grid">
    <div className="stat-card">
      <div className="stat-icon primary"><FileImageOutlined /></div>
      <div className="stat-content">
        <h3>Total Imágenes</h3>
        <p>{estadisticas.total_imagenes}</p>
      </div>
    </div>
    <div className="stat-card">
      <div className="stat-icon primary"><FundProjectionScreenOutlined /></div>
      <div className="stat-content">
        <h3>Análisis CNN Realizados</h3>
        <p>{estadisticas.total_analisis}</p>
      </div>
    </div>
    <div className="stat-card">
      <div className="stat-icon success"><CheckCircleOutlined /></div>
      <div className="stat-content">
        <h3>Casos Normales</h3>
        <p>{estadisticas.analisis_normales}</p>
      </div>
    </div>
    <div className="stat-card">
      <div className="stat-icon warning"><WarningOutlined /></div>
      <div className="stat-content">
        <h3>Anomalías Detectadas</h3>
        <p>{estadisticas.analisis_anomalias}</p>
      </div>
    </div>
    <div className="stat-card">
      <div className="stat-icon primary"><DashboardOutlined /></div>
      <div className="stat-content">
        <h3>Confianza Promedio</h3>
        <p>{estadisticas.confianza_promedio}%</p>
      </div>
    </div>
  </div>
);

export default IaMedicaStats;
