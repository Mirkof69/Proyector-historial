import React from 'react';
import { Tag, Badge, Button, Space } from 'antd';
import { BellOutlined, FileTextOutlined, CheckOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica } from '../../services/reportesService';
import { AlertasState, getSeveridadColor } from './alertasMedicasUtils';

interface BuildColumnsArgs {
  setState: React.Dispatch<React.SetStateAction<AlertasState>>;
  marcarResuelta: (id: number) => void;
}

export const buildColumnsAlertasMedicas = ({ setState, marcarResuelta }: BuildColumnsArgs) => [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: 70,
    sorter: (a: AlertaMedica, b: AlertaMedica) => a.id - b.id
  },
  {
    title: 'Paciente',
    dataIndex: 'paciente_nombre',
    key: 'paciente',
    render: (nombre: string | null) => nombre || '—'
  },
  {
    title: 'Título / Tipo',
    dataIndex: 'titulo',
    key: 'titulo',
    render: (titulo: string, record: AlertaMedica) => (
      <div>
        <div style={{ fontWeight: 500 }}>{titulo}</div>
        <Tag icon={<BellOutlined />}>{record.tipo_display || record.tipo}</Tag>
      </div>
    )
  },
  {
    title: 'Prioridad',
    dataIndex: 'prioridad',
    key: 'prioridad',
    render: (prioridad: string, record: AlertaMedica) => (
      <Badge
        count={record.prioridad_display || prioridad.toUpperCase()}
        style={{
          backgroundColor: getSeveridadColor(prioridad),
          fontWeight: 'bold'
        }}
      />
    ),
    sorter: (a: AlertaMedica, b: AlertaMedica) => {
      const orden: Record<string, number> = { baja: 1, media: 2, alta: 3, critica: 4, emergencia: 5 };
      return (orden[a.prioridad] || 0) - (orden[b.prioridad] || 0);
    }
  },
  {
    title: 'Descripción',
    dataIndex: 'descripcion',
    key: 'descripcion',
    ellipsis: true
  },
  {
    title: 'Módulo Origen',
    dataIndex: 'modulo_origen_display',
    key: 'modulo',
    render: (modulo: string, record: AlertaMedica) => (
      <Tag color="cyan">{modulo || record.modulo_origen}</Tag>
    )
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    render: (estado: string, record: AlertaMedica) => {
      const status = estado === 'resuelta' ? 'success' : estado === 'descartada' ? 'default' : 'error';
      return <Badge status={status as any} text={record.estado_display || estado} />;
    },
    filters: [
      { text: 'Activa', value: 'activa' },
      { text: 'Revisada', value: 'revisada' },
      { text: 'Resuelta', value: 'resuelta' },
      { text: 'Descartada', value: 'descartada' },
      { text: 'Escalada', value: 'escalada' }
    ],
    onFilter: (value: any, record: AlertaMedica) => record.estado === value
  },
  {
    title: 'Fecha',
    dataIndex: 'fecha_creacion',
    key: 'fecha',
    render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm'),
    sorter: (a: AlertaMedica, b: AlertaMedica) =>
      dayjs(a.fecha_creacion).unix() - dayjs(b.fecha_creacion).unix()
  },
  {
    title: 'Acciones',
    key: 'acciones',
    render: (_: any, record: AlertaMedica) => (
      <Space>
        <Button
          type="link"
          icon={<FileTextOutlined />}
          onClick={() => {
            setState(prev => ({ ...prev, selectedAlerta: record, drawerVisible: true }));
          }}
        >
          Detalle
        </Button>
        {record.estado !== 'resuelta' && record.estado !== 'descartada' && (
          <Button
            type="link"
            icon={<CheckOutlined />}
            onClick={() => marcarResuelta(record.id)}
          >
            Resolver
          </Button>
        )}
      </Space>
    )
  }
];
