import React from 'react';
import { Card, List, Badge, Tag, Button, Space, Avatar, Tooltip, Empty, Spin } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

interface AlertaMedica {
  id: number;
  titulo: string;
  descripcion: string;
  tipo: string;
  prioridad: number;
  paciente_nombre?: string;
  estado: string;
  fecha_creacion: string;
  categoria: string;
  asignado_a?: string;
}

interface AlertListProps {
  alertas: AlertaMedica[];
  loading: boolean;
  vistaActiva: string;
  onTabChange: (key: string) => void;
  onViewDetail: (alerta: AlertaMedica) => void;
  getTipoConfig: (tipo: string) => { icon: React.ReactElement; color: string; text: string };
  getEstadoConfig: (estado: string) => { icon: React.ReactElement; color: string; text: string };
}

const AlertList: React.FC<AlertListProps> = ({
  alertas, loading, vistaActiva, onTabChange, onViewDetail, getTipoConfig, getEstadoConfig,
}) => (
  <Card
    title={
      <Space>
        <BellOutlined />
        <span>Alertas Médicas</span>
        <Badge count={alertas.length} showZero />
      </Space>
    }
  >
    <Spin spinning={loading}>
      {alertas.length === 0 ? (
        <Empty description="No hay alertas que mostrar" />
      ) : (
        <List
          itemLayout="vertical"
          dataSource={alertas}
          pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total ${total} alertas` }}
          renderItem={(alerta) => {
            const tipoConfig = getTipoConfig(alerta.tipo);
            const estadoConfig = getEstadoConfig(alerta.estado);
            return (
              <List.Item
                key={alerta.id}
                extra={
                  <Space direction="vertical" align="end">
                    <Tag icon={tipoConfig.icon} style={{ backgroundColor: tipoConfig.color, color: 'white', border: 'none' }}>
                      {tipoConfig.text}
                    </Tag>
                    <Tag color={estadoConfig.color} icon={estadoConfig.icon}>{estadoConfig.text}</Tag>
                    <Tooltip title="Ver detalle completo de la alerta">
                      <Button type="primary" size="small" onClick={() => onViewDetail(alerta)}>Ver Detalle</Button>
                    </Tooltip>
                  </Space>
                }
              >
                <List.Item.Meta
                  avatar={<Avatar style={{ backgroundColor: tipoConfig.color }} icon={tipoConfig.icon} />}
                  title={<Space><strong>{alerta.titulo}</strong><Tag>{alerta.categoria}</Tag></Space>}
                  description={
                    <Space direction="vertical" size="small">
                      <div>{alerta.descripcion}</div>
                      {alerta.paciente_nombre && <div><BellOutlined /> Paciente: {alerta.paciente_nombre}</div>}
                      {alerta.asignado_a && <div><BellOutlined /> Asignado a: {alerta.asignado_a}</div>}
                      <div><BellOutlined /> {dayjs(alerta.fecha_creacion).fromNow()}</div>
                    </Space>
                  }
                />
              </List.Item>
            );
          }}
        />
      )}
    </Spin>
  </Card>
);

export default AlertList;
