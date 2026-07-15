import React from 'react';
import { Tag, Space, Typography } from 'antd';
import { WarningOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { ComparacionControl } from './detalleControlUtils';

const { Text } = Typography;

export const columnasComparacion = [
  {
    title: 'Parámetro',
    dataIndex: 'campo',
    key: 'campo',
    render: (text: string, record: ComparacionControl) => (
      <Space>
        {record.importante && <WarningOutlined style={{ color: '#ff4d4f' }} />}
        <Text strong={record.importante}>{text}</Text>
      </Space>
    ),
  },
  {
    title: 'Control Anterior',
    dataIndex: 'valorAnterior',
    key: 'valorAnterior',
    render: (text: string) => <Text type="secondary">{text}</Text>,
  },
  {
    title: 'Control Actual',
    dataIndex: 'valorActual',
    key: 'valorActual',
    render: (text: string) => <Text strong>{text}</Text>,
  },
  {
    title: 'Cambio',
    dataIndex: 'cambio',
    key: 'cambio',
    align: 'center' as const,
    render: (cambio: 'mejora' | 'empeora' | 'igual') => {
      const config = {
        mejora: { color: 'success', text: 'Mejoró', icon: <CheckCircleOutlined /> },
        empeora: { color: 'error', text: 'Empeoró', icon: <WarningOutlined /> },
        igual: { color: 'default', text: 'Sin cambio', icon: <InfoCircleOutlined /> },
      };
      return (
        <Tag color={config[cambio].color} icon={config[cambio].icon}>
          {config[cambio].text}
        </Tag>
      );
    },
  },
];
