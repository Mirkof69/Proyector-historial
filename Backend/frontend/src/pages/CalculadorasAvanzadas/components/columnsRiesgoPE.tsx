import React from 'react';
import { Tag } from 'antd';

export const columnsRiesgoPE = [
  { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
  { title: 'Semanas', dataIndex: 'semanas', key: 'semanas' },
  {
    title: 'Riesgo PE Precoz',
    dataIndex: 'riesgo_pe_precoz',
    key: 'riesgo_pe_precoz',
    render: (val: number) => <Tag color={val >= 10 ? 'red' : val >= 5 ? 'orange' : 'green'}>{val.toFixed(2)}%</Tag>
  },
  {
    title: 'Riesgo PE Tardía',
    dataIndex: 'riesgo_pe_tardia',
    key: 'riesgo_pe_tardia',
    render: (val: number) => <Tag color={val >= 15 ? 'red' : val >= 5 ? 'orange' : 'green'}>{val.toFixed(2)}%</Tag>
  },
  {
    title: 'PlGF MoM',
    dataIndex: 'plgf_mom',
    key: 'plgf_mom',
    render: (val: number) => <span style={{ color: val < 0.7 ? '#f5222d' : '#52c41a', fontWeight: 'bold' }}>{val.toFixed(2)}</span>
  },
  {
    title: 'Ratio sFlt/PlGF',
    dataIndex: 'ratio_sflt_plgf',
    key: 'ratio_sflt_plgf',
    render: (val: number) => <span style={{ color: val > 85 ? '#f5222d' : val > 38 ? '#fa8c16' : '#52c41a', fontWeight: 'bold' }}>{val.toFixed(1)}</span>
  },
  { title: 'Clasificación', dataIndex: 'clasificacion', key: 'clasificacion' }
];
