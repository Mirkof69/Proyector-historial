import React from 'react';
import { Button, Space, Tag, Badge, Tooltip, Typography } from 'antd';
import {
  EyeOutlined, EditOutlined, DeleteOutlined, UserOutlined, FilePdfOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { RegistroVacunaExtended, getEstadoDosis } from './vacunasUtils';

const { Text } = Typography;

interface BuildColumnsArgs {
  handleVerCarnet: (vacuna: RegistroVacunaExtended) => void;
  handleVerDetalle: (id: number) => void;
  handleEditar: (id: number) => void;
  handleEliminar: (vacuna: RegistroVacunaExtended) => void;
}

export const buildColumnsVacunas = ({ handleVerCarnet, handleVerDetalle, handleEditar, handleEliminar }: BuildColumnsArgs): ColumnsType<RegistroVacunaExtended> => [
  {
    title: 'Paciente',
    key: 'paciente',
    fixed: 'left',
    width: 250,
    render: (_, record) => (
      <Space size="middle">
        <Badge dot status={getEstadoDosis(record).color as any} offset={[-5, 30]}>
          <div className="avatar-placeholder" style={{ backgroundColor: '#f0f5ff', padding: '8px', borderRadius: '8px' }}>
            <UserOutlined style={{ color: '#1890ff', fontSize: '1.2em' }} />
          </div>
        </Badge>
        <div>
          <Text strong className="block">{record.paciente_info?.nombre_completo || record.paciente_nombre}</Text>
          <Text type="secondary" style={{ fontSize: '0.85em' }}>ID: {record.paciente_info?.id_clinico || '-'}</Text>
        </div>
      </Space>
    )
  },
  {
    title: 'Vacuna / Dosis',
    key: 'vacuna',
    width: 200,
    render: (_, record) => (
      <Space direction="vertical" size={0}>
        <Text strong>{record.tipo_vacuna_info?.nombre || record.tipo_vacuna_nombre}</Text>
        <Space>
          <Tag color="cyan">Dosis {record.numero_dosis}</Tag>
          {record.tipo_vacuna_info?.dosis_requeridas && (
            <small style={{ color: '#999' }}>de {record.tipo_vacuna_info?.dosis_requeridas}</small>
          )}
        </Space>
      </Space>
    )
  },
  {
    title: 'Aplicación',
    dataIndex: 'fecha_aplicacion',
    key: 'fecha_aplicacion',
    width: 150,
    render: (fecha) => (
      <Space direction="vertical" size={0}>
        <Text>{dayjs(fecha).format('DD/MM/YYYY')}</Text>
        <Text type="secondary" style={{ fontSize: '0.8em' }}>{dayjs(fecha).fromNow()}</Text>
      </Space>
    )
  },
  {
    title: 'Programación',
    key: 'proxima',
    width: 180,
    render: (_, record) => {
      const estado = getEstadoDosis(record);
      return (
        <Space direction="vertical" size={2}>
          <Tag color={estado.color} style={{ borderRadius: '12px' }}>
            {estado.texto.toUpperCase()}
          </Tag>
          {record.proxima_dosis_fecha && (
            <Text strong style={{ fontSize: '0.9em' }}>
              {dayjs(record.proxima_dosis_fecha).format('DD/MM/YYYY')}
            </Text>
          )}
        </Space>
      );
    }
  },
  {
    title: 'Lote / Lab',
    key: 'logistica',
    width: 180,
    render: (_, record) => (
      <div>
        <div><Text type="secondary">L:</Text> {record.lote || '-'}</div>
        <div><Text type="secondary">Lab:</Text> {record.laboratorio || '-'}</div>
      </div>
    )
  },
  {
    title: 'Acciones',
    key: 'acciones',
    fixed: 'right',
    width: 180,
    align: 'center',
    render: (_, record) => (
      <Space>
        <Tooltip title="Certificado">
          <Button
            type="text"
            icon={<FilePdfOutlined />}
            onClick={() => handleVerCarnet(record)}
            className="action-btn-pdf"
          />
        </Tooltip>
        <Tooltip title="Detalles">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleVerDetalle(record.id)}
            className="action-btn-view"
          />
        </Tooltip>
        <Tooltip title="Editar">
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditar(record.id)}
            className="action-btn-edit"
          />
        </Tooltip>
        <Tooltip title="Eliminar">
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleEliminar(record)}
            className="action-btn-delete"
          />
        </Tooltip>
      </Space>
    )
  }
];
