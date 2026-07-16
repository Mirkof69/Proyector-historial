import React from 'react';
import { Card, Table, Tag, Typography } from 'antd';
import { SmileOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

interface RecienNacido {
  id: number;
  nombre?: string;
  sexo?: string;
  peso_nacimiento?: number;
  talla_nacimiento?: number;
  apgar_1_minuto?: number;
  apgar_5_minutos?: number;
  fecha_nacimiento?: string;
  observaciones?: string;
}

const mockData: RecienNacido[] = [
  { id: 1, nombre: 'Recién Nacido 1', sexo: 'femenino', peso_nacimiento: 3200, talla_nacimiento: 50, apgar_1_minuto: 8, apgar_5_minutos: 9, fecha_nacimiento: '2024-12-01T10:30:00' },
  { id: 2, nombre: 'Recién Nacido 2', sexo: 'masculino', peso_nacimiento: 2800, talla_nacimiento: 48, apgar_1_minuto: 7, apgar_5_minutos: 8, fecha_nacimiento: '2024-12-01T10:35:00' },
];

const RecienNacidos: React.FC = () => {
  const columns = [
    { title: 'Nombre', dataIndex: 'nombre', key: 'nombre' },
    {
      title: 'Sexo', dataIndex: 'sexo', key: 'sexo',
      render: (s: string) => <Tag color={s === 'masculino' ? 'blue' : 'magenta'}>{s === 'masculino' ? 'Masculino' : 'Femenino'}</Tag>,
    },
    { title: 'Peso (g)', dataIndex: 'peso_nacimiento', key: 'peso', render: (v: number) => v ? <Tag color={v < 2500 ? 'orange' : 'green'}>{v}g</Tag> : '-' },
    { title: 'Talla (cm)', dataIndex: 'talla_nacimiento', key: 'talla', render: (v: number) => v ? `${v} cm` : '-' },
    {
      title: 'Apgar 1\'', dataIndex: 'apgar_1_minuto', key: 'apgar1',
      render: (v: number) => v != null ? <Tag color={v >= 7 ? 'success' : v >= 4 ? 'warning' : 'error'}>{v}</Tag> : '-',
    },
    {
      title: 'Apgar 5\'', dataIndex: 'apgar_5_minutos', key: 'apgar5',
      render: (v: number) => v != null ? <Tag color={v >= 7 ? 'success' : v >= 4 ? 'warning' : 'error'}>{v}</Tag> : '-',
    },
    { title: 'Fecha Nac.', dataIndex: 'fecha_nacimiento', key: 'fecha', render: (f: string) => f ? dayjs(f).format('DD/MM/YYYY') : '-' },
    { title: 'Observaciones', dataIndex: 'observaciones', key: 'obs', ellipsis: true },
  ];

  return (
    <Card title={<span><SmileOutlined style={{ color: '#52c41a', marginRight: 8 }} />Recién Nacidos</span>}>
      <Table columns={columns} dataSource={mockData} rowKey="id" pagination={false} bordered />
    </Card>
  );
};

export default RecienNacidos;
