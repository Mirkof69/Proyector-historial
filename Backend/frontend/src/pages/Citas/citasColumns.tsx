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
    // Orden en el SERVIDOR (`?ordering=fecha_cita`, que desempata por hora):
    // antes ordenaba en el navegador solo lo descargado.
    dataIndex: 'fecha_cita',
    key: 'fecha_cita',
    width: 180,
    sorter: true,
    defaultSortOrder: 'descend',
    render: (_, record: Cita) => {
      const atrasada = esAtrasada(record.fecha_cita, record.estado);
      const hoy = esHoy(record.fecha_cita);
      return (
        <Space direction="vertical" size="small">
          <Space>
            <span className={`citas-page__fecha${atrasada ? ' citas-page__fecha--atrasada' : hoy ? ' citas-page__fecha--hoy' : ''}`}>
              <CalendarOutlined />
              {dayjs(record.fecha_cita).format('DD/MM/YYYY')}
            </span>
          </Space>
          <Space>
            <span className={`citas-page__fecha${atrasada ? ' citas-page__fecha--atrasada' : ''}`}>
              <ClockCircleOutlined />
              {record.hora_cita.substring(0, 5)}
            </span>
          </Space>
          {atrasada && (
            <Tag icon={<WarningOutlined />} color="error" className="citas-sin-margen">
              Atrasada
            </Tag>
          )}
          {hoy && !atrasada && (
            <Tag icon={<CalendarOutlined />} color="processing" className="citas-sin-margen">
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
          <small className="citas-page__secundario texto-mono">ID: {record.paciente_info?.id_clinico}</small>
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
        <Button
          type="link"
          icon={<EyeOutlined />}
          aria-label="Ver detalle de la cita"
          title="Ver detalle"
          onClick={() => handleVerVistaRapida(record)}
        />
        {canChange('cita') && (
          <Button
            type="link"
            icon={<EditOutlined />}
            aria-label="Editar cita"
            title="Editar"
            onClick={() => handleEditar(record.id!)}
            disabled={['completada', 'cancelada', 'no_asistio'].includes(record.estado)}
          />
        )}
        <Dropdown menu={getMenuAcciones(record)} trigger={['click']}>
          <Button type="link" icon={<MoreOutlined />} aria-label="Más acciones de la cita" title="Más acciones" />
        </Dropdown>
        {canDelete('cita') && (
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            aria-label="Eliminar cita"
            title="Eliminar"
            onClick={() => handleEliminar(record)}
          />
        )}
      </Space>
    ),
  },
];
