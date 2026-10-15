import React from 'react';
import { Tag } from 'antd';

export const columnasHistorialHemorragia = [
  {
    title: 'Fecha/Hora',
    dataIndex: 'fecha',
    key: 'fecha'
  },
  {
    title: 'Shock Index',
    dataIndex: 'shock_index',
    key: 'shock_index',
    render: (si: number) => si.toFixed(2)
  },
  {
    title: 'Pérdida (ml)',
    dataIndex: 'perdida_ml',
    key: 'perdida_ml'
  },
  {
    title: 'Gravedad',
    dataIndex: 'gravedad',
    key: 'gravedad',
    render: (gravedad: string) => {
      let color = 'success';
      if (gravedad === 'Severa') color = 'error';
      else if (gravedad === 'Masiva') color = 'error';
      else if (gravedad === 'Moderada') color = 'warning';
      return <Tag color={color}>{gravedad}</Tag>;
    }
  },
  {
    title: 'Causa',
    dataIndex: 'causa',
    key: 'causa'
  }
];
