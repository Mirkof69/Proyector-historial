import React from 'react';
import { Col, Card, Space, Badge, List, Avatar, Tag, Button, Typography, Empty } from 'antd';
import { WarningOutlined, ExclamationCircleOutlined, ThunderboltOutlined, InfoCircleOutlined } from '@ant-design/icons';
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
        title={<Space><WarningOutlined style={{ color: '#fa8c16' }} /><span>Alertas Médicas Activas</span></Space>}
        className="shadow-card"
        extra={<Badge count={alertasMedicas.length} showZero style={{ backgroundColor: '#fa8c16' }} />}
      >
        {alertasMedicas.length === 0 ? (
          <Empty
            description="No hay alertas médicas activas"
            style={{ padding: '20px 0' }}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        ) : (
          <List
            dataSource={alertasMedicas}
            rowKey={(alerta) => alerta._uniqueKey || `alerta-fallback-${alerta.id}`}
            renderItem={(alerta: AlertaMedica) => (
              <List.Item style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
                <List.Item.Meta
                  avatar={
                    <Avatar
                      style={{
                        backgroundColor:
                          alerta.tipo === 'critica' ? '#ff4d4f' :
                          alerta.tipo === 'urgente' ? '#fa8c16' :
                          alerta.tipo === 'moderada' ? '#faad14' : '#52c41a'
                      }}
                      icon={
                        alerta.tipo === 'critica' ? <ExclamationCircleOutlined /> :
                        alerta.tipo === 'urgente' ? <WarningOutlined /> :
                        alerta.tipo === 'moderada' ? <ThunderboltOutlined /> : <InfoCircleOutlined />
                      }
                    />
                  }
                  title={
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Text strong style={{ fontSize: 13 }}>{alerta.titulo}</Text>
                      <Tag
                        color={
                          alerta.tipo === 'critica' ? 'red' :
                          alerta.tipo === 'urgente' ? 'orange' :
                          alerta.tipo === 'moderada' ? 'gold' : 'blue'
                        }
                        style={{ fontSize: 12 }}
                      >
                        {alerta.tipo.toUpperCase()}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                        {alerta.mensaje.length > 80 ? `${alerta.mensaje.substring(0, 80)}...` : alerta.mensaje}
                      </Text>
                      <Space size={4}>
                        {alerta.paciente_nombre && (
                          <Text type="secondary" style={{ fontSize: 12 }}>👤 {alerta.paciente_nombre}</Text>
                        )}
                        <Text type="secondary" style={{ fontSize: 12 }}>• {dayjs(alerta.fecha_creacion).fromNow()}</Text>
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
          <div style={{ marginTop: 16, textAlign: 'center' }}>
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
