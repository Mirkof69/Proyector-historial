import React from 'react';
import { Space, Tag, Progress, Typography } from 'antd';
import {
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { interpretarResultado, calcularPorcentajeEnRango } from '../detalleLaboratorioUtils';

const { Text } = Typography;

export const buildColumnsResultados = () => [
  {
    title: 'Parámetro',
    dataIndex: 'parametro_nombre',
    key: 'parametro',
    width: 180,
  },
  {
    title: 'Valor Obtenido',
    key: 'valor',
    width: 150,
    render: (record: any) => (
      <Space direction="vertical" size={0}>
        <Text strong style={{ fontSize: 16 }}>
          {record.valor_numerico || record.valor_texto}{' '}
          {record.unidad && record.unidad !== 'cualitativo' && `${record.unidad}`}
        </Text>
      </Space>
    ),
  },
  {
    title: 'Rango de Referencia',
    key: 'rango',
    width: 200,
    render: (record: any) => (
      <Space direction="vertical" size={4} style={{ width: '100%' }}>
        <Text type="secondary">{record.rango_referencia || 'N/A'}</Text>
        {record.valor_numerico && record.rango_referencia && (
          <Progress
            percent={calcularPorcentajeEnRango(record)}
            size="small"
            status={record.es_normal ? 'success' : record.es_critico ? 'exception' : 'normal'}
            showInfo={false}
          />
        )}
      </Space>
    ),
  },
  {
    title: 'Interpretación',
    key: 'interpretacion',
    width: 250,
    render: (record: any) => (
      <Space direction="vertical" size={0}>
        {record.es_critico && (
          <>
            <Tag color="red" icon={<WarningOutlined />}>CRÍTICO</Tag>
            <Text type="danger" style={{ fontSize: 12 }}>
              Requiere atención inmediata
            </Text>
          </>
        )}
        {!record.es_critico && !record.es_normal && (
          <>
            <Tag color="orange" icon={<ExclamationCircleOutlined />}>ANORMAL</Tag>
            <Text type="warning" style={{ fontSize: 12 }}>
              {interpretarResultado(record)}
            </Text>
          </>
        )}
        {record.es_normal && (
          <>
            <Tag color="green" icon={<CheckCircleOutlined />}>NORMAL</Tag>
            <Text style={{ fontSize: 12, color: '#52c41a' }}>
              Dentro del rango esperado
            </Text>
          </>
        )}
      </Space>
    ),
  },
  {
    title: 'Observaciones',
    dataIndex: 'observaciones',
    key: 'observaciones',
    render: (text: string) => text || '-',
  },
];
