import React from 'react';
import { Button, Space, Tag, Avatar, Typography, Tooltip, Popconfirm } from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Notificacion } from '../../../services/notificacionesService';
import { getTypeIcon, getTypeLabel } from '../notificacionesUtils';

const { Text } = Typography;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;

interface BuildColumnsArgs {
  handleViewDetails: (notificacion: Notificacion) => void;
  handleMarkAsRead: (id: number) => void;
  handleDelete: (id: number) => void;
}

export const buildColumnsNotificaciones = ({ handleViewDetails, handleMarkAsRead, handleDelete }: BuildColumnsArgs) => [
  {
    title: 'Tipo',
    dataIndex: 'tipo',
    key: 'tipo',
    width: 150,
    render: (tipo: string) => (
      <Space>
        <Avatar
          icon={getTypeIcon(tipo)}
          style={{
            backgroundColor:
              tipo === 'error' || tipo === 'warning' ? '#ff4d4f' :
              tipo === 'success' ? '#52c41a' :
              tipo === 'cita' ? '#1890ff' :
              tipo === 'examen' ? '#faad14' : '#13c2c2'
          }}
        />
        <Tag color={
          tipo === 'error' || tipo === 'warning' ? 'red' :
          tipo === 'success' ? 'green' :
          tipo === 'cita' ? 'blue' :
          tipo === 'examen' ? 'orange' : 'cyan'
        }>
          {getTypeLabel(tipo)}
        </Tag>
      </Space>
    ),
  },
  {
    title: 'Contenido',
    key: 'contenido',
    render: (_: any, record: Notificacion) => (
      <button
        type="button"
        onClick={() => handleViewDetails(record)}
        style={{ cursor: 'pointer', background: 'none', border: 'none', padding: 0, textAlign: 'left', width: '100%' }}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleViewDetails(record); } }}
      >
        <Text strong={!record.leida} style={{ display: 'block', marginBottom: 4 }}>
          {record.titulo}
        </Text>
        <Text type="secondary" style={{ fontSize: 13 }}>
          {record.mensaje}
        </Text>
      </button>
    ),
  },
  {
    title: 'Fecha',
    dataIndex: 'fecha_creacion',
    key: 'fecha',
    width: 150,
    render: (date: string) => (
      <Tooltip title={dayjs(date).format('DD/MM/YYYY HH:mm:ss')}>
        <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>
          <ClockCircleOutlined style={{ marginRight: 6 }} />
          {dayjs(date).fromNow()}
        </span>
      </Tooltip>
    ),
    sorter: (a: Notificacion, b: Notificacion) =>
      new Date(a.fecha_creacion).getTime() - new Date(b.fecha_creacion).getTime(),
  },
  {
    title: 'Acciones',
    key: 'acciones',
    width: 100,
    render: (_: any, record: Notificacion) => (
      <Space>
        {!record.leida && (
          <Tooltip title="Marcar como leída">
            <Button
              type="text"
              className="action-btn read"
              icon={CHECK_ICON_2}
              onClick={() => handleMarkAsRead(record.id)}
            />
          </Tooltip>
        )}
        <Popconfirm
          title="¿Eliminar notificación?"
          onConfirm={() => handleDelete(record.id)}
          okText="Sí"
          cancelText="No"
        >
          <Tooltip title="Eliminar">
            <Button
              type="text"
              className="action-btn delete"
              icon={DELETE_ICON_6}
            />
          </Tooltip>
        </Popconfirm>
      </Space>
    ),
  },
];
