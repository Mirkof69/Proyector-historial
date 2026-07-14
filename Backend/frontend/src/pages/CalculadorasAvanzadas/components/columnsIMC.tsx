import React from 'react';
import { Tag } from 'antd';

export const columnsIMC = [
  {
    title: 'Fecha',
    dataIndex: 'fecha',
    key: 'fecha',
    width: 120
  },
  {
    title: 'Semanas',
    dataIndex: 'semanas',
    key: 'semanas',
    width: 100,
    render: (semanas: number) => `${semanas} sem`
  },
  {
    title: 'Peso (kg)',
    dataIndex: 'peso',
    key: 'peso',
    width: 100,
    render: (peso: number) => peso.toFixed(1)
  },
  {
    title: 'Ganancia (kg)',
    dataIndex: 'ganancia',
    key: 'ganancia',
    width: 120,
    render: (ganancia: number) => (
      <span style={{ color: ganancia >= 0 ? '#52c41a' : '#f5222d', fontWeight: 'bold' }}>
        {ganancia >= 0 ? '+' : ''}{ganancia.toFixed(1)}
      </span>
    )
  },
  {
    title: 'IMC',
    dataIndex: 'imc',
    key: 'imc',
    width: 100,
    render: (imc: number) => imc.toFixed(1)
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    render: (estado: string) => {
      let color = 'default';
      if (estado.includes('ADECUADA')) color = 'success';
      if (estado.includes('INSUFICIENTE') || estado.includes('EXCESIVA')) color = 'warning';
      return <Tag color={color}>{estado}</Tag>;
    }
  }
];
