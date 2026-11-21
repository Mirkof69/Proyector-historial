import React from 'react';
import { Space, Typography, Tag, Tooltip, Badge, Button } from 'antd';
import {
  UserOutlined, CalendarOutlined, WarningOutlined,
  EyeOutlined, EditOutlined, DeleteOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ExamenLaboratorio } from '../../../services/laboratorioService';

const { Text } = Typography;

export const buildLaboratorioColumns = (
  canChange: (perm: string) => boolean,
  canDelete: (perm: string) => boolean,
  onVer: (id: number) => void,
  onEditar: (id: number) => void,
  onEliminar: (examen: any) => void,
) => [
  {
    title: 'Paciente',
    key: 'paciente',
    width: 200,
    render: (_: any, record: ExamenLaboratorio) => (
      <Space direction="vertical" size={0}>
        <Space>
          <span className="laboratorio-page__paciente">
            <UserOutlined />
            {record.paciente_nombre || 'No especificado'}
          </span>
        </Space>
      </Space>
    ),
  },
  {
    title: 'Tipo de Examen',
    dataIndex: 'tipo_examen_nombre',
    key: 'tipo_examen',
    width: 220,
    render: (text: string, record: ExamenLaboratorio) => (
      <Space direction="vertical" size={0}>
        <Text>{text || '-'}</Text>
        {record.categoria && (
          <Tag>
            {record.categoria}
          </Tag>
        )}
      </Space>
    ),
  },
  {
    title: 'Fecha Solicitud',
    dataIndex: 'fecha_solicitud',
    key: 'fecha_solicitud',
    width: 140,
    sorter: (a: ExamenLaboratorio, b: ExamenLaboratorio) =>
      dayjs(a.fecha_solicitud).unix() - dayjs(b.fecha_solicitud).unix(),
    render: (fecha: string) => (
      <Space>
        <CalendarOutlined />
        {dayjs(fecha).format('DD/MM/YYYY')}
      </Space>
    ),
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    width: 120,
    render: (estado: string) => {
      const colors = {
        solicitado: 'warning',
        en_proceso: 'processing',
        completado: 'success',
        cancelado: 'default',
      };
      const nombres: Record<string, string> = {
        solicitado: 'Solicitado', en_proceso: 'En proceso', completado: 'Completado', cancelado: 'Cancelado',
      };
      return <Tag color={colors[estado as keyof typeof colors] || 'default'}>{nombres[estado] ?? estado}</Tag>;
    },
  },
  {
    title: 'Prioridad',
    dataIndex: 'prioridad',
    key: 'prioridad',
    width: 100,
    render: (prioridad: string) => {
      const colors = {
        normal: 'default',
        urgente: 'warning',
        stat: 'error',
      };
      const nombres: Record<string, string> = { normal: 'Normal', urgente: 'Urgente', stat: 'Inmediata' };
      return <Tag color={colors[prioridad as keyof typeof colors] || 'default'}>{nombres[prioridad] ?? prioridad}</Tag>;
    },
  },
  {
    title: 'Resultados',
    key: 'resultados',
    width: 145,
    render: (_: any, record: ExamenLaboratorio) => {
      if (record.resumen) {
        const { criticos, anormales } = record.resumen;
        if (criticos > 0) {
          return (
            <Tooltip title={`${criticos} crítico(s)`}>
              <Badge count={criticos} showZero>
                <Tag color="error" icon={<WarningOutlined />}>
                  CRÍTICOS
                </Tag>
              </Badge>
            </Tooltip>
          );
        }
        if (anormales > 0) {
          return (
            <Tooltip title={`${anormales} anormal(es)`}>
              <Badge count={anormales}>
                <Tag color="warning">ANORMALES</Tag>
              </Badge>
            </Tooltip>
          );
        }
        return <Tag color="success">NORMALES</Tag>;
      }
      return <Text type="secondary">Sin resultados</Text>;
    },
  },
  {
    title: 'Acciones',
    key: 'acciones',
    fixed: 'right' as const,
    width: 150,
    render: (_: any, record: ExamenLaboratorio) => (
      <Space size="small">
        <Tooltip title="Ver detalle">
          <Button type="link" icon={<EyeOutlined />} onClick={() => onVer(record.id!)} />
        </Tooltip>
        {canChange('examenlaboratorio') && (
          <Tooltip title="Editar">
            <Button type="link" icon={<EditOutlined />} onClick={() => onEditar(record.id!)} />
          </Tooltip>
        )}
        {canDelete('examenlaboratorio') && (
          <Tooltip title="Eliminar">
            <Button type="link" danger icon={<DeleteOutlined />} onClick={() => onEliminar(record)} />
          </Tooltip>
        )}
      </Space>
    ),
  },
];
