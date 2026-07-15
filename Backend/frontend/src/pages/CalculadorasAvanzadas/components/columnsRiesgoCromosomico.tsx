import React from 'react';
import { Tag } from 'antd';
import { formatRiesgo } from '../riesgoCromosomicoUtils';

export const columnsRiesgoCromosomico = [
  { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
  { title: 'Edad', dataIndex: 'edad', key: 'edad', render: (val: number) => `${val} años` },
  { title: 'Semanas', dataIndex: 'semanas', key: 'semanas', render: (val: number) => `${val.toFixed(1)} sem` },
  {
    title: 'Riesgo T21',
    dataIndex: 'riesgo_t21',
    key: 'riesgo_t21',
    render: (val: number) => {
      const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
      return <Tag color={color}>{formatRiesgo(val)}</Tag>;
    }
  },
  {
    title: 'Riesgo T18',
    dataIndex: 'riesgo_t18',
    key: 'riesgo_t18',
    render: (val: number) => {
      const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
      return <Tag color={color}>{formatRiesgo(val)}</Tag>;
    }
  },
  {
    title: 'Riesgo T13',
    dataIndex: 'riesgo_t13',
    key: 'riesgo_t13',
    render: (val: number) => {
      const color = val >= 1 / 250 ? 'red' : val >= 1 / 1000 ? 'orange' : 'green';
      return <Tag color={color}>{formatRiesgo(val)}</Tag>;
    }
  },
  { title: 'NT MoM', dataIndex: 'nt_mom', key: 'nt_mom', render: (val: number) => val.toFixed(2) },
  { title: 'Clasificación', dataIndex: 'clasificacion_t21', key: 'clasificacion_t21' }
];
