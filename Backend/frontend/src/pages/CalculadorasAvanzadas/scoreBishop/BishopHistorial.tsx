import React from 'react';
import { Card, Table, Tag } from 'antd';
import dayjs from 'dayjs';
import { HistorialBishop } from './scoreBishopUtils';

const columnsHistorial = [
  {
    title: 'Fecha',
    dataIndex: 'fecha',
    key: 'fecha',
    render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm'),
  },
  { title: 'Paciente', dataIndex: 'paciente', key: 'paciente' },
  { title: 'EG (semanas)', dataIndex: 'edadGestacional', key: 'eg' },
  {
    title: 'Score',
    dataIndex: 'puntaje',
    key: 'puntaje',
    render: (puntaje: number) => (
      <Tag color={puntaje >= 8 ? 'green' : puntaje >= 6 ? 'orange' : 'red'}>
        <strong>{puntaje}</strong>
      </Tag>
    ),
  },
  {
    title: 'Resultado',
    dataIndex: 'resultado',
    key: 'resultado',
    render: (resultado: string) => (
      <Tag color={resultado === 'Favorable' ? 'success' : resultado === 'Intermedio' ? 'warning' : 'error'}>
        {resultado}
      </Tag>
    ),
  },
];

const BishopHistorial: React.FC<{ historial: HistorialBishop[] }> = ({ historial }) => (
  <Card title="Historial de Evaluaciones" style={{ marginTop: 24 }}>
    <Table
      columns={columnsHistorial}
      dataSource={historial}
      rowKey="id"
      pagination={{ pageSize: 5 }}
    />
  </Card>
);

export default BishopHistorial;
