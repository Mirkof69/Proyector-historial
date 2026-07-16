import React from 'react';
import { Space, Typography, Tag, Tooltip, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  EditOutlined, DeleteOutlined, EyeOutlined, CheckCircleOutlined,
  CloseCircleOutlined, ClockCircleOutlined, AlertOutlined, WarningOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import type { NavigateFunction } from 'react-router-dom';
import { TriajeEnfermeria } from '../../../services/triajeService';

const { Text } = Typography;

export const buildTriajeColumns = (
  navigate: NavigateFunction,
  onComplete: (id: number) => void,
  onDelete: (id: number) => void,
): ColumnsType<TriajeEnfermeria> => [
  {
    title: 'Paciente',
    key: 'paciente',
    render: (_: any, record: TriajeEnfermeria) => (
      <Space direction="vertical" size={0}>
        <Text strong>{record.paciente_info?.nombre_completo || record.paciente_nombre || 'Sin nombre'}</Text>
        <Text type="secondary" style={{ fontSize: '12px' }}>{(record.paciente_info as any)?.id_clinico || '-'}</Text>
      </Space>
    ),
  },
  {
    title: 'Fecha/Hora',
    key: 'fecha_hora',
    width: 150,
    render: (_: any, record: TriajeEnfermeria) => (
      <Space direction="vertical" size={0}>
        <Text>{dayjs(record.fecha_hora || record.fecha_registro).format('DD/MM/YYYY')}</Text>
        <Text type="secondary">{dayjs(record.fecha_hora || record.fecha_registro).format('HH:mm')}</Text>
      </Space>
    ),
    sorter: (a: TriajeEnfermeria, b: TriajeEnfermeria) =>
      new Date(a.fecha_hora || a.fecha_registro || 0).getTime() -
      new Date(b.fecha_hora || b.fecha_registro || 0).getTime(),
  },
  {
    title: 'Prioridad',
    dataIndex: 'prioridad',
    key: 'prioridad',
    width: 120,
    render: (prioridad: string) => {
      if (!prioridad) return <Tag>Sin prioridad</Tag>;
      const config: { [key: string]: { color: string; icon: React.ReactNode } } = {
        urgente: { color: 'red', icon: <AlertOutlined /> },
        alto: { color: 'orange', icon: <WarningOutlined /> },
        normal: { color: 'blue', icon: <ClockCircleOutlined /> },
        bajo: { color: 'green', icon: <CheckCircleOutlined /> },
      };
      const { color, icon } = config[prioridad] || { color: 'default', icon: null };
      return <Tag color={color} icon={icon}>{prioridad.toUpperCase()}</Tag>;
    },
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    width: 130,
    render: (estado: string) => {
      const config: { [key: string]: { color: string; icon: React.ReactNode } } = {
        pendiente: { color: 'warning', icon: <ClockCircleOutlined /> },
        completado: { color: 'success', icon: <CheckCircleOutlined /> },
        cancelado: { color: 'error', icon: <CloseCircleOutlined /> },
      };
      const { color, icon } = config[estado] || { color: 'default', icon: null };
      return <Tag color={color} icon={icon}>{estado?.toUpperCase() || 'PENDIENTE'}</Tag>;
    },
  },
  {
    title: 'Motivo',
    key: 'motivo',
    ellipsis: true,
    render: (_: any, record: TriajeEnfermeria) => (
      <Tooltip title={record.motivo_consulta || record.motivo_visita}>
        <Text ellipsis style={{ maxWidth: 200 }}>{record.motivo_consulta || record.motivo_visita}</Text>
      </Tooltip>
    ),
  },
  {
    title: 'Acciones',
    key: 'acciones',
    fixed: 'right' as const,
    width: 150,
    render: (_: any, record: TriajeEnfermeria) => (
      <Space>
        <Tooltip title="Ver detalles">
          <Button
            type="primary"
            ghost
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/dashboard/triaje/${record.id}`)}
          />
        </Tooltip>
        <Tooltip title="Editar">
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => navigate(`/dashboard/triaje/${record.id}/editar`)}
          />
        </Tooltip>
        {record.estado === 'pendiente' && (
          <Tooltip title="Completar">
            <Button
              size="small"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => onComplete(record.id!)}
            />
          </Tooltip>
        )}
        <Tooltip title="Eliminar">
          <Button
            danger
            ghost
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => onDelete(record.id!)}
          />
        </Tooltip>
      </Space>
    ),
  },
];
