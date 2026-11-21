import React from 'react';
import {
  FileImageOutlined, FundProjectionScreenOutlined, CheckCircleOutlined,
  WarningOutlined, DashboardOutlined,
} from '@ant-design/icons';
import { EstadisticasIA } from '../../../services/iaMedicaService';
import { useCountUp } from '../../../hooks/useCountUp';

/** Número con conteo animado para las tarjetas de cifras del módulo IA. */
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
  <div className="ia-cifras">
    <div className="ia-cifra">
      <div className="ia-cifra-icono"><FileImageOutlined /></div>
      <div className="ia-cifra-texto">
        <h3>Imágenes guardadas</h3>
        <p><AnimatedNumber value={estadisticas.total_imagenes} /></p>
      </div>
    </div>
    <div className="ia-cifra">
      <div className="ia-cifra-icono"><FundProjectionScreenOutlined /></div>
      <div className="ia-cifra-texto">
        <h3>Análisis realizados</h3>
        <p><AnimatedNumber value={estadisticas.total_analisis} /></p>
      </div>
    </div>
    <div className="ia-cifra">
      <div className="ia-cifra-icono exito"><CheckCircleOutlined /></div>
      <div className="ia-cifra-texto">
        <h3>Sin hallazgos</h3>
        <p><AnimatedNumber value={estadisticas.analisis_normales} /></p>
      </div>
    </div>
    <div className="ia-cifra">
      <div className="ia-cifra-icono aviso"><WarningOutlined /></div>
      <div className="ia-cifra-texto">
        <h3>Con hallazgos o revisión</h3>
        <p><AnimatedNumber value={estadisticas.analisis_anomalias} /></p>
      </div>
    </div>
    <div className="ia-cifra">
      <div className="ia-cifra-icono"><DashboardOutlined /></div>
      <div className="ia-cifra-texto">
        <h3>Confianza media de las redes</h3>
        <p><AnimatedNumber value={estadisticas.confianza_promedio} decimals={1} suffix="%" /></p>
      </div>
    </div>
  </div>
);

export default IaMedicaStats;
