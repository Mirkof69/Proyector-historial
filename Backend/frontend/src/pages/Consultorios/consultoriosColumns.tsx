import React from 'react';
import { Button, Space, Tag, Tooltip, Popconfirm } from 'antd';
import {
  EditOutlined, DeleteOutlined, EyeOutlined, HomeOutlined, ToolOutlined,
  CheckCircleOutlined, CloseCircleOutlined, CalendarOutlined, BarChartOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { Consultorio, TipoConsultorio, EstadoConsultorio } from '../../services/consultoriosService';

const checkCircleIcon = <CheckCircleOutlined />;
const homeIcon = <HomeOutlined />;
const closeCircleIcon = <CloseCircleOutlined />;
const eyeIcon = <EyeOutlined />;
const editIcon = <EditOutlined />;
const calendarIcon = <CalendarOutlined />;
const toolIcon = <ToolOutlined />;
const barChartIcon = <BarChartOutlined />;
const clockCircleIcon = <ClockCircleOutlined />;
const deleteIcon = <DeleteOutlined />;

export interface ConsultoriosColumnsDeps {
  navigate: (path: string) => void;
  handleAbrirModalEditar: (consultorio: Consultorio) => void;
  handleAbrirReservas: (consultorio: Consultorio) => void;
  handleAbrirMantenimiento: (consultorio: Consultorio) => void;
  handleAbrirEstadisticas: (consultorio: Consultorio) => void;
  handleAbrirDisponibilidad: (consultorio: Consultorio) => void;
  handleEliminar: (id: number) => void;
}

export const buildConsultoriosColumns = (deps: ConsultoriosColumnsDeps) => {
  const {
    navigate, handleAbrirModalEditar, handleAbrirReservas, handleAbrirMantenimiento,
    handleAbrirEstadisticas, handleAbrirDisponibilidad, handleEliminar,
  } = deps;

  return [
    {
      title: 'Código',
      dataIndex: 'codigo',
      key: 'codigo',
      width: 120,
      sorter: (a: Consultorio, b: Consultorio) => (a.codigo || '').localeCompare(b.codigo || ''),
    },
    {
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
      sorter: (a: Consultorio, b: Consultorio) => (a.nombre || '').localeCompare(b.nombre || ''),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 150,
      render: (tipo: TipoConsultorio) => {
        const colors: Record<string, string> = {
          'general': 'blue',
          'especializado': 'purple',
          'procedimientos': 'orange',
          'consulta_rapida': 'cyan',
          'emergencias': 'red',
        };
        return <Tag color={colors[tipo] || 'default'}>{tipo}</Tag>;
      },
    },
    {
      title: 'Ubicación',
      key: 'ubicacion',
      render: (_: any, record: Consultorio) => (
        <span>
          {record.area && `${record.area}`}
          {record.piso && ` - Piso ${record.piso}`}
        </span>
      ),
    },
    {
      title: 'Capacidad',
      dataIndex: 'capacidad_personas',
      key: 'capacidad_personas',
      width: 100,
      align: 'center' as const,
    },
    {
      title: 'Equipamiento',
      key: 'equipamiento',
      render: (_: any, record: Consultorio) => (
        <Space size="small">
          {record.tiene_camilla && <Tooltip title="Camilla"><Tag color="green">C</Tag></Tooltip>}
          {record.tiene_escritorio && <Tooltip title="Escritorio"><Tag color="blue">E</Tag></Tooltip>}
          {record.tiene_computadora && <Tooltip title="Computadora"><Tag color="purple">PC</Tag></Tooltip>}
        </Space>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 130,
      render: (estado: EstadoConsultorio) => {
        const configs: Record<string, { color: string; icon: React.ReactElement; text: string }> = {
          'disponible': { color: 'success', icon: checkCircleIcon, text: 'Disponible' },
          'ocupado': { color: 'processing', icon: homeIcon, text: 'Ocupado' },
          'mantenimiento': { color: 'warning', icon: toolIcon, text: 'Mantenimiento' },
          'reservado': { color: 'default', icon: homeIcon, text: 'Reservado' },
          'inactivo': { color: 'error', icon: closeCircleIcon, text: 'Inactivo' },
        };
        const config = configs[estado] || configs['inactivo'];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 280,
      fixed: 'right' as const,
      render: (_: any, record: Consultorio) => (
        <Space size="small" wrap>
          <Tooltip title="Ver detalle">
            <Button
              type="text"
              size="small"
              icon={eyeIcon}
              onClick={() => navigate(`/consultorios/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Editar en modal">
            <Button
              type="text"
              size="small"
              icon={editIcon}
              onClick={() => handleAbrirModalEditar(record)}
            />
          </Tooltip>
          <Tooltip title="Reservas">
            <Button
              type="text"
              size="small"
              icon={calendarIcon}
              onClick={() => handleAbrirReservas(record)}
            />
          </Tooltip>
          <Tooltip title="Mantenimiento">
            <Button
              type="text"
              size="small"
              icon={toolIcon}
              onClick={() => handleAbrirMantenimiento(record)}
            />
          </Tooltip>
          <Tooltip title="Estadísticas">
            <Button
              type="text"
              size="small"
              icon={barChartIcon}
              onClick={() => handleAbrirEstadisticas(record)}
            />
          </Tooltip>
          <Tooltip title="Verificar disponibilidad">
            <Button
              type="text"
              size="small"
              icon={clockCircleIcon}
              onClick={() => handleAbrirDisponibilidad(record)}
            />
          </Tooltip>
          <Tooltip title="Eliminar">
            <Popconfirm
              title="¿Está seguro de eliminar este consultorio?"
              onConfirm={() => handleEliminar(record.id!)}
              okText="Sí"
              cancelText="No"
            >
              <Button
                type="text"
                size="small"
                danger
                icon={deleteIcon}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];
};
