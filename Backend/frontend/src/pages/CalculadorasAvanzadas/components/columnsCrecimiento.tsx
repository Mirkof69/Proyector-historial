import React from 'react';
import { Tag } from 'antd';

export const columnsCrecimiento = [
  { title: 'Fecha', dataIndex: 'fecha', key: 'fecha' },
  { title: 'Semanas', dataIndex: 'semanas', key: 'semanas', render: (val: number) => `${val.toFixed(1)} sem` },
  { title: 'EFW (g)', dataIndex: 'efw', key: 'efw', render: (val: number) => val.toFixed(0) },
  {
    title: 'Percentil',
    dataIndex: 'percentil',
    key: 'percentil',
    render: (val: number) => {
      let color = 'green';
      if (val < 3) color = 'red';
      else if (val < 10) color = 'orange';
      else if (val > 97) color = 'red';
      else if (val > 90) color = 'gold';
      return <Tag color={color}>p{val.toFixed(1)}</Tag>;
    }
  },
  { title: 'Clasificación', dataIndex: 'clasificacion', key: 'clasificacion' },
  { title: 'BPD (mm)', dataIndex: 'bpd', key: 'bpd', render: (val: number) => val.toFixed(1) },
  { title: 'HC (mm)', dataIndex: 'hc', key: 'hc', render: (val: number) => val.toFixed(1) },
  { title: 'AC (mm)', dataIndex: 'ac', key: 'ac', render: (val: number) => val.toFixed(1) },
  { title: 'FL (mm)', dataIndex: 'fl', key: 'fl', render: (val: number) => val.toFixed(1) }
];
