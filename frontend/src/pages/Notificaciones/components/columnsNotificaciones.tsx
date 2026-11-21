import React from 'react';
import { Button, Space, Tag, Avatar, Typography, Tooltip, Popconfirm } from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Notificacion } from '../../../services/notificacionesService';
import { getTypeIcon, getTypeLabel, getTypeTagColor, getTypeAvatarClass } from '../notificacionesUtils';

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
    // tipo_display trae el nombre legible («Examen crítico»); el código crudo se veía en pantalla.
    render: (tipo: string, registro: Notificacion & { tipo_display?: string }) => (
      <Space>
        <Avatar icon={getTypeIcon(tipo)} className={getTypeAvatarClass(tipo)} />
        <Tag color={getTypeTagColor(tipo)}>
          {registro.tipo_display || getTypeLabel(tipo)}
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
        className="notifications-page__contenido"
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleViewDetails(record); } }}
      >
        <Text strong={!record.leida}>
          {record.titulo}
        </Text>
        <Text type="secondary" className="notifications-page__mensaje">
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
        <span className="notifications-page__fecha">
          <ClockCircleOutlined />
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
              className="notifications-page__accion--leida"
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
              danger
              icon={DELETE_ICON_6}
            />
          </Tooltip>
        </Popconfirm>
      </Space>
    ),
  },
];
