import React from 'react';
import { Alert, Descriptions, Divider, Table, Tag, Typography } from 'antd';
import { InfoCircleOutlined } from '@ant-design/icons';
import { Reporte } from '../reporteTypes';

const { Text } = Typography;

interface TabFiltrosReporteProps {
  reporte: Reporte;
}

const TabFiltrosReporte: React.FC<TabFiltrosReporteProps> = ({ reporte }) => (
  <div style={{ background: '#f5f5f5', padding: 20, borderRadius: 8 }}>
    <Alert
      message="Auditoría de Filtros"
      description="Estos son los parámetros exactos que se utilizaron para generar este documento."
      type="info"
      showIcon
      icon={<InfoCircleOutlined />}
      style={{ marginBottom: 15 }}
    />

    <Descriptions title="Parámetros" bordered size="small" column={1}>
      {Object.entries(reporte.parametros_busqueda).map(([key, value]) => (
        <Descriptions.Item label={key.replace(/_/g, ' ').toUpperCase()} key={key}>
          {typeof value === 'boolean'
            ? (value ? 'SÍ' : 'NO')
            : Array.isArray(value)
              ? value.join(', ')
              : String(value || 'N/A')}
        </Descriptions.Item>
      ))}
    </Descriptions>

    <Divider>Tabla de Parámetros</Divider>

    <Table
      dataSource={Object.entries(reporte.parametros_busqueda).map(([key, value], index) => ({
        key: index,
        parametro: key.replace(/_/g, ' ').toUpperCase(),
        valor: typeof value === 'boolean'
          ? (value ? 'SÍ' : 'NO')
          : Array.isArray(value)
            ? value.join(', ')
            : String(value || 'N/A'),
        tipo: Array.isArray(value) ? 'Array' : typeof value
      }))}
      columns={[
        {
          title: 'Parámetro',
          dataIndex: 'parametro',
          key: 'parametro',
          render: (text) => <Text strong>{text}</Text>
        },
        {
          title: 'Valor',
          dataIndex: 'valor',
          key: 'valor',
        },
        {
          title: 'Tipo',
          dataIndex: 'tipo',
          key: 'tipo',
          render: (tipo) => <Tag color="blue">{tipo}</Tag>
        }
      ]}
      pagination={false}
      size="small"
    />
  </div>
);

export default TabFiltrosReporte;
