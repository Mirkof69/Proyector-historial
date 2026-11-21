import React from 'react';
import { Tag, Space, Button, Badge, Tooltip, Typography } from 'antd';
import { EyeOutlined, AlertOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { SearchResult } from './globalSearchUtils';

const { Text } = Typography;

const EYE_ICON_2 = <EyeOutlined />;

// Columnas para tablas de resultados
export const getSearchColumns = (handleViewDetail: (result: SearchResult) => void) => [
  {
    title: 'Título',
    dataIndex: 'titulo',
    key: 'titulo',
    render: (text: string, record: SearchResult) => (
      <Space direction="vertical" size={0}>
        <Text strong>{text}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>{record.subtitulo}</Text>
      </Space>
    ),
  },
  {
    title: 'Descripción',
    dataIndex: 'descripcion',
    key: 'descripcion',
    ellipsis: true,
  },
  {
    title: 'Fecha',
    dataIndex: 'fecha',
    key: 'fecha',
    width: 150,
    render: (fecha: string) => fecha ? dayjs(fecha).format('DD/MM/YYYY HH:mm') : '-',
  },
  {
    title: 'Estado',
    dataIndex: 'estado',
    key: 'estado',
    width: 120,
    render: (estado: string, record: SearchResult) => {
      const colors: Record<string, string> = {
        'activo': 'success',
        'Embarazo Activo': 'success',
        'disponible': 'success',
        'confirmada': 'success',
        'completada': 'processing',
        'pendiente': 'warning',
        'cancelada': 'error',
        'ocupado': 'error',
      };

      // Mostrar icono de alerta para resultados urgentes
      const isUrgent = (record.tipo === 'embarazo' && (record.data?.riesgo === 'alto' || record.data?.alto_riesgo)) ||
                      (record.tipo === 'cita' && estado === 'pendiente' && dayjs(record.fecha).isBefore(dayjs().add(1, 'day')));

      return (
        <Space>
          {isUrgent && <AlertOutlined className="busqueda-urgente" />}
          <Tag color={colors[estado] || 'default'}>{estado || 'N/A'}</Tag>
        </Space>
      );
    },
  },
  {
    title: 'Relevancia',
    dataIndex: 'relevancia',
    key: 'relevancia',
    width: 100,
    sorter: (a: SearchResult, b: SearchResult) => b.relevancia - a.relevancia,
    render: (score: number) => (
      <Badge
        count={score}
        style={{ backgroundColor: score > 50 ? 'var(--color-exito)' : score > 25 ? 'var(--color-aviso)' : 'var(--color-texto-3)', color: 'var(--color-sobre-primario)' }}
      />
    ),
  },
  {
    title: 'Acciones',
    key: 'acciones',
    width: 100,
    fixed: 'right' as const,
    render: (_: any, record: SearchResult) => (
      <Tooltip title="Ver detalle">
        <Button
          size="small"
          icon={EYE_ICON_2}
          onClick={() => handleViewDetail(record)}
        />
      </Tooltip>
    ),
  },
];
