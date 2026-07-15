import React from 'react';
import { Button, Space, Tag, Tooltip, Dropdown, MenuProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  EyeOutlined, EditOutlined, DeleteOutlined, CalendarOutlined,
  ClockCircleOutlined, UserOutlined, MedicineBoxOutlined, WarningOutlined,
  MoreOutlined, PhoneOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Cita, EstadoCita, TipoCita } from '../../services/citasService';
import { getEstadoTag, getTipoColor, getTipoTexto, esAtrasada, esHoy } from './citasUtils';

interface BuildColumnsArgs {
  canChange: (perm: string) => boolean;
  canDelete: (perm: string) => boolean;
  handleVerVistaRapida: (cita: Cita) => void;
  handleEditar: (id: number) => void;
  handleEliminar: (cita: any) => void;
  getMenuAcciones: (record: Cita) => MenuProps;
}

export const buildCitasColumns = ({
  canChange, canDelete, handleVerVistaRapida, handleEditar, handleEliminar, getMenuAcciones,
}: BuildColumnsArgs): ColumnsType<Cita> => [
  {
    title: 'Fecha y Hora',
    key: 'fecha_hora',
    width: 180,
    sorter: (a, b) => dayjs(`${a.fecha_cita} ${a.hora_cita}`).unix() - dayjs(`${b.fecha_cita} ${b.hora_cita}`).unix(),
    defaultSortOrder: 'ascend',
    render: (_, record: Cita) => {
      const atrasada = esAtrasada(record.fecha_cita, record.estado);
      const hoy = esHoy(record.fecha_cita);
      return (
        <Space direction="vertical" size="small">
          <Space>
            <CalendarOutlined style={{ color: atrasada ? '#ff4d4f' : hoy ? '#1890ff' : '#52c41a' }} />
            <span style={{ color: atrasada ? '#ff4d4f' : 'inherit', fontWeight: hoy ? 600 : 500 }}>
              {dayjs(record.fecha_cita).format('DD/MM/YYYY')}
            </span>
          </Space>
          <Space>
            <ClockCircleOutlined style={{ color: atrasada ? '#ff4d4f' : '#52c41a' }} />
            <span style={{ color: atrasada ? '#ff4d4f' : 'inherit' }}>
              {record.hora_cita.substring(0, 5)}
            </span>
          </Space>
          {atrasada && (
            <Tag icon={<WarningOutlined />} color="error" style={{ margin: 0 }}>
              Atrasada
            </Tag>
          )}
          {hoy && !atrasada && (
            <Tag icon={<CalendarOutlined />} color="processing" style={{ margin: 0 }}>
              Hoy
            </Tag>
          )}
        </Space>
      );
    },
  },
  {
    title: 'Paciente',
    key: 'paciente',
    width: 220,
    render: (_, record: Cita) => (
      <Space direction="vertical" size="small">
        <Space>
          <UserOutlined />
          <strong>{record.paciente_info?.nombre_completo || 'No especificado'}</strong>
        </Space>
        {record.paciente_info?.id_clinico && (
          <small style={{ color: '#8c8c8c' }}>ID: {record.paciente_info?.id_clinico}</small>
        )}
        {record.paciente_info?.telefono && (
          <Space size="small">
            <PhoneOutlined />
            <small>{record.paciente_info?.telefono}</small>
          </Space>
        )}
      </Space>
    ),
  },
  {
    title: 'Médico',
    dataIndex: ['medico_info', 'nombre'],
    key: 'medico',
    width: 180,
    render: (nombre: string) => (
      <Space>
        <MedicineBoxOutlined />
        {nombre || 'No asignado'}
      </Space>
    ),
  },
  {
    title: 'Tipo',
    dataIndex: 'tipo_cita',
    key: 'tipo_cita',
    width: 120,
    render: (tipo: TipoCita) => (
      <Tag color={getTipoColor(tipo)}>{getTipoTexto(tipo)}</Tag>
    ),
  },
  {
    title: 'Motivo',
    dataIndex: 'motivo',
    key: 'motivo',
    width: 200,
    ellipsis: true,
    render: (motivo: string) => (
      <Tooltip title={motivo}>
        <span>{motivo || '-'}</span>
      </Tooltip>
    ),
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    width: 140,
    render: (estado: EstadoCita) => getEstadoTag(estado),
  },
  {
    title: 'Acciones',
    key: 'acciones',
    fixed: 'right',
    width: 180,
    render: (_, record: Cita) => (
      <Space size="small">
        <Tooltip title="Ver detalle">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleVerVistaRapida(record)}
          />
        </Tooltip>
        {canChange('cita') && (
          <Tooltip title="Editar">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEditar(record.id!)}
              disabled={['completada', 'cancelada', 'no_asistio'].includes(record.estado)}
            />
          </Tooltip>
        )}
        <Dropdown menu={getMenuAcciones(record)} trigger={['click']}>
          <Button type="link" icon={<MoreOutlined />} />
        </Dropdown>
        {canDelete('cita') && (
          <Tooltip title="Eliminar">
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleEliminar(record)}
            />
          </Tooltip>
        )}
      </Space>
    ),
  },
];
