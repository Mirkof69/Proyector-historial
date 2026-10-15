import React from 'react';
import { FileTextOutlined, BarChartOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

export interface FormValues {
  tipo_reporte: number;
  nombre: string;
  descripcion?: string;
  formato: string;
  rango_fechas?: [dayjs.Dayjs, dayjs.Dayjs];
  incluir_graficos?: boolean;
  incluir_estadisticas?: boolean;
  agrupar_por?: string;
  filtros_adicionales?: string[];
}

export const iconoPorCategoria: Record<string, React.ReactElement> = {
  estadistico: <BarChartOutlined className="reportes-icono-tipo" />,
  paciente: <FileTextOutlined className="reportes-icono-tipo" />,
  institucional: <FileTextOutlined className="reportes-icono-tipo" />,
  regulatorio: <FileTextOutlined className="reportes-icono-tipo" />,
  clinico: <FileTextOutlined className="reportes-icono-tipo" />,
  financiero: <BarChartOutlined className="reportes-icono-tipo" />,
};
