import React from 'react';
import { Col, Card, Space, Badge, List, Avatar, Tag, Button, Typography, Empty } from 'antd';
import { WarningOutlined, ExclamationCircleOutlined, ThunderboltOutlined, InfoCircleOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';

const { Text } = Typography;

interface AlertaMedica {
  id: number;
  titulo: string;
  mensaje: string;
  tipo: 'critica' | 'urgente' | 'moderada' | 'info';
  paciente_nombre?: string;
  paciente_id?: number;
  fecha_creacion: string;
  requiere_accion_inmediata?: boolean;
  _uniqueKey?: string;
}

interface DashboardAlertasProps {
  alertasMedicas: AlertaMedica[];
}

const DashboardAlertasMedicas: React.FC<DashboardAlertasProps> = ({ alertasMedicas }) => {
  const navigate = useNavigate();

  return (
    <Col xs={24} lg={12}>
      <Card
        title={<Space><WarningOutlined className="dashboard-alertas__icono-titulo" /><span>Alertas Médicas Activas</span></Space>}
        className="shadow-card"
        extra={<Badge count={alertasMedicas.length} showZero className="dashboard-alertas__contador" />}
      >
        {alertasMedicas.length === 0 ? (
          <Empty
            description="No hay alertas médicas activas"
            className="dashboard-alertas__vacio"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={alertasMedicas}
            rowKey={(alerta) => alerta._uniqueKey || `alerta-fallback-${alerta.id}`}
            renderItem={(alerta: AlertaMedica) => (
              <List.Item>
                <List.Item.Meta
                  avatar={
                    <Avatar
                      className={`dashboard-alerta__avatar dashboard-alerta__avatar--${alerta.tipo}`}
                      icon={
                        alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> :
                        alerta.tipo === 'urgente' ? <WarningOutlined /> :
                        alerta.tipo === 'moderada' ? <ThunderboltOutlined /> : <InfoCircleOutlined />
                      }
                    />
                  }
                  title={
                    <div className="dashboard-alerta__cabecera">
                      <Text strong className="dashboard-alerta__titulo">{alerta.titulo}</Text>
                      <Tag
                        color={
                          alerta.tipo === 'critica' ? 'error' :
                          alerta.tipo === 'urgente' || alerta.tipo === 'moderada' ? 'warning' : 'processing'
                        }
                      >
                        {(alerta.tipo || 'info').toUpperCase()}
                      </Tag>
                    </div>
                  }
                  description={
                    <div>
                      <Text type="secondary" className="dashboard-alerta__mensaje">
                        {(alerta.mensaje || '').length > 80 ? `${alerta.mensaje.substring(0, 80)}...` : alerta.mensaje}
                      </Text>
                      <Space size={4}>
                        {alerta.paciente_nombre && (
                          <Text type="secondary" className="dashboard-alerta__meta"><UserOutlined /> {alerta.paciente_nombre}</Text>
                        )}
                        <Text type="secondary" className="dashboard-alerta__meta">• {dayjs(alerta.fecha_creacion).fromNow()}</Text>
                      </Space>
                    </div>
                  }
                />
                {alerta.requiere_accion_inmediata && (
                  <Button
                    type="primary"
                    danger
                    size="small"
                    onClick={() => {
                      if (alerta.paciente_id) {
                        navigate(`/dashboard/pacientes/${alerta.paciente_id}/historia`);
                      }
                    }}
                  >
                    Ver
                  </Button>
                )}
              </List.Item>
            )}
          />
        )}
        {alertasMedicas.length > 0 && (
          <div className="dashboard-alertas__pie">
            <Button type="link" onClick={() => navigate('/dashboard/pacientes?filter=alert')}>
              Ver todas las alertas →
            </Button>
          </div>
        )}
      </Card>
    </Col>
  );
};

export default DashboardAlertasMedicas;
