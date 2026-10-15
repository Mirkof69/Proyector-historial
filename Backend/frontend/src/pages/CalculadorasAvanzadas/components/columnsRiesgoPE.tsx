import React from 'react';
import { Tag } from 'antd';

export const columnsRiesgoPE = [
  { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
  { title: 'Semanas', dataIndex: 'semanas', key: 'semanas' },
  {
    title: 'Riesgo PE Precoz',
    dataIndex: 'riesgo_pe_precoz',
    key: 'riesgo_pe_precoz',
    render: (val: number) => <Tag color={val >= 10 ? 'error' : val >= 5 ? 'warning' : 'success'}>{val.toFixed(2)}%</Tag>
  },
  {
    title: 'Riesgo PE Tardía',
    dataIndex: 'riesgo_pe_tardia',
    key: 'riesgo_pe_tardia',
    render: (val: number) => <Tag color={val >= 15 ? 'error' : val >= 5 ? 'warning' : 'success'}>{val.toFixed(2)}%</Tag>
  },
  {
    title: 'PlGF MoM',
    dataIndex: 'plgf_mom',
    key: 'plgf_mom',
    render: (val: number) => <span className="calc-valor-estado" style={{ color: val < 0.7 ? 'var(--color-peligro)' : 'var(--color-exito)' }}>{val.toFixed(2)}</span>
  },
  {
    title: 'Ratio sFlt/PlGF',
    dataIndex: 'ratio_sflt_plgf',
    key: 'ratio_sflt_plgf',
    render: (val: number) => <span className="calc-valor-estado" style={{ color: val > 85 ? 'var(--color-peligro)' : val > 38 ? 'var(--color-aviso)' : 'var(--color-exito)' }}>{val.toFixed(1)}</span>
  },
  { title: 'Clasificación', dataIndex: 'clasificacion', key: 'clasificacion' }
];
