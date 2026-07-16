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
  estadistico: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
  paciente: <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
  institucional: <FileTextOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
  regulatorio: <FileTextOutlined style={{ fontSize: 48, color: '#fa8c16' }} />,
  clinico: <FileTextOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />,
  financiero: <BarChartOutlined style={{ fontSize: 48, color: '#13c2c2' }} />,
};
