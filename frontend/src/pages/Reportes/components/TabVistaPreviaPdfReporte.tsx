import React from 'react';
import { Reporte } from '../reporteTypes';

interface TabVistaPreviaPdfReporteProps {
  reporte: Reporte;
  apiUrl: string;
}

const TabVistaPreviaPdfReporte: React.FC<TabVistaPreviaPdfReporteProps> = ({ reporte, apiUrl }) => (
  <div className="reportes-visor-pdf">
    <iframe
      src={reporte.archivo_url!.startsWith('http') ? reporte.archivo_url! : `${apiUrl.replace('/api', '')}${reporte.archivo_url}`}
      width="100%"
      height="100%"
      title="Vista Previa PDF"
      sandbox="allow-scripts"
    />
  </div>
);

export default TabVistaPreviaPdfReporte;
