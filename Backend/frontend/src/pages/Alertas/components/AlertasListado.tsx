import React from 'react';
import { Card, Badge, List, Tag, Button, Space, Empty, Spin, Tabs, Avatar, Tooltip } from 'antd';
import {
  BellOutlined, WarningOutlined, ClockCircleOutlined, ExclamationCircleOutlined,
  MedicineBoxOutlined, UserOutlined, FireOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica, AlertAction, getTipoConfig, getEstadoConfig } from '../sistemaAlertasUtils';

interface AlertasListadoProps {
  alertas: AlertaMedica[];
  alertasFiltradas: AlertaMedica[];
  vistaActiva: string;
  loading: boolean;
  dispatch: React.Dispatch<AlertAction>;
  handleVerDetalle: (alerta: AlertaMedica) => void;
}

const AlertasListado: React.FC<AlertasListadoProps> = ({
  alertas, alertasFiltradas, vistaActiva, loading, dispatch, handleVerDetalle,
}) => (
  <Card
    title={
      <Space>
        <BellOutlined />
        <span>Alertas Médicas</span>
        <Badge count={alertasFiltradas.length} showZero />
      </Space>
    }
  >
    <Tabs
      activeKey={vistaActiva}
      onChange={(key) => dispatch({ type: 'SET_VISTA_ACTIVA', payload: key })}
      items={[
        {
          key: 'todas',
          label: (
            <Tooltip title="Ver todas las alertas">
              <span>
                <BellOutlined /> Todas ({alertas.length})
              </span>
            </Tooltip>
          ),
          children: null,
        },
        {
          key: 'criticas',
          label: (
            <Tooltip title="Alertas que requieren atención inmediata">
              <span>
                <FireOutlined /> Críticas ({alertas.filter(a => a.tipo === 'critica').length})
              </span>
            </Tooltip>
          ),
          children: null,
        },
        {
          key: 'altas',
          label: (
            <Tooltip title="Alertas de alta prioridad">
              <span>
                <WarningOutlined /> Altas ({alertas.filter(a => a.tipo === 'alta').length})
              </span>
            </Tooltip>
          ),
          children: null,
        },
        {
          key: 'medias',
          label: (
            <Tooltip title="Alertas de prioridad media">
              <span>
                <ExclamationCircleOutlined /> Medias ({alertas.filter(a => a.tipo === 'media').length})
              </span>
            </Tooltip>
          ),
          children: null,
        },
        {
          key: 'bajas',
          label: (
            <Tooltip title="Alertas de baja prioridad e informativas">
              <span>
                <InfoCircleOutlined /> Bajas/Info ({alertas.filter(a => a.tipo === 'baja' || a.tipo === 'info').length})
              </span>
            </Tooltip>
          ),
          children: null,
        },
      ]}
    />

    <Spin spinning={loading}>
      {alertasFiltradas.length === 0 ? (
        <Empty description="No hay alertas que mostrar" />
      ) : (
        <List
          itemLayout="vertical"
          dataSource={alertasFiltradas}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} alertas`,
          }}
          renderItem={alerta => {
            const tipoConfig = getTipoConfig(alerta.tipo);
            const estadoConfig = getEstadoConfig(alerta.estado);

            return (
              <List.Item
                key={alerta.id}
                extra={
                  <Space direction="vertical" align="end">
                    <Tag
                      icon={tipoConfig.icon}
                      style={{
                        backgroundColor: tipoConfig.color,
                        color: 'white',
                        border: 'none',
                      }}
                    >
                      {tipoConfig.text}
                    </Tag>
                    <Tag color={estadoConfig.color} icon={estadoConfig.icon}>
                      {estadoConfig.text}
                    </Tag>
                    <Tooltip title="Ver detalle completo de la alerta">
                      <Button
                        type="primary"
                        size="small"
                        onClick={() => handleVerDetalle(alerta)}
                      >
                        Ver Detalle
                      </Button>
                    </Tooltip>
                  </Space>
                }
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      style={{
                        backgroundColor: tipoConfig.color,
                      }}
                      icon={tipoConfig.icon}
                    />
                  }
                  title={
                    <Space>
                      <strong>{alerta.titulo}</strong>
                      <Tag>{alerta.categoria}</Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <div>{alerta.descripcion}</div>
                      {alerta.paciente_nombre && (
                        <div>
                          <UserOutlined /> Paciente: {alerta.paciente_nombre}
                        </div>
                      )}
                      {alerta.asignado_a && (
                        <div>
                          <MedicineBoxOutlined /> Asignado a: {alerta.asignado_a}
                        </div>
                      )}
                      <div>
                        <ClockCircleOutlined /> {dayjs(alerta.fecha_creacion).fromNow()}
                      </div>
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

export default AlertasListado;
