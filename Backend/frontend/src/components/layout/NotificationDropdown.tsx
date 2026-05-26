/**
 * =============================================================================
 * DROPDOWN DE NOTIFICACIONES
 * =============================================================================
 * Componente para mostrar notificaciones en el header
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Badge, Dropdown, List, Button, Typography, Space, Tag, Empty, Spin } from 'antd';
import { BellOutlined, CheckOutlined, DeleteOutlined } from '@ant-design/icons';
import { notificacionesService, Notificacion } from '../../services/notificacionesService';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text } = Typography;

const getTipoColor = (tipo: string): string => {
  const colors: Record<string, string> = {
    info: 'blue',
    warning: 'orange',
    success: 'green',
    error: 'red',
  };
  return colors[tipo] || 'default';
};

const getTipoIcon = (tipo: string): string => {
  const icons: Record<string, string> = {
    info: 'ℹ️',
    warning: '⚠️',
    success: '✅',
    error: '❌',
  };
  return icons[tipo] || '📢';
};

const NotificationDropdown: React.FC = () => {
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const cargarNotificaciones = async () => {
    setLoading(true);
    try {
      const data = await notificacionesService.listar();
      setNotificaciones(data.slice(0, 10));
    } catch (error) {
      console.error('Error cargando notificaciones:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      cargarNotificaciones();
    }
  }, [open]);

  const handleMarcarLeida = async (id: number) => {
    try {
      await notificacionesService.marcarLeida(id);
      setNotificaciones((prev) =>
        prev.map((n) => (n.id === id ? { ...n, leida: true } : n))
      );
    } catch (error) {
      console.error('Error marcando como leída:', error);
    }
  };

  const handleMarcarTodasLeidas = async () => {
    try {
      await notificacionesService.marcarTodasLeidas();
      setNotificaciones((prev) => prev.map((n) => ({ ...n, leida: true })));
    } catch (error) {
      console.error('Error marcando todas como leídas:', error);
    }
  };

  const noLeidas = notificaciones.filter((n) => !n.leida).length;

  const menuContent = (
    <div style={{ width: 380, maxHeight: 500, overflow: 'auto' }}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text strong>Notificaciones</Text>
        {noLeidas > 0 && (
          <Button type="link" size="small" onClick={handleMarcarTodasLeidas}>
            Marcar todas como leídas
          </Button>
        )}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 24 }}>
          <Spin />
        </div>
      ) : notificaciones.length === 0 ? (
        <div style={{ padding: 24 }}>
          <Empty description="No hay notificaciones" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      ) : (
        <List
          dataSource={notificaciones}
          renderItem={(item) => (
            <List.Item
              style={{
                backgroundColor: item.leida ? 'transparent' : '#f0f5ff',
                cursor: 'pointer',
                padding: '12px 16px',
              }}
              onClick={() => !item.leida && handleMarcarLeida(item.id)}
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.leida}>
                    <span style={{ fontSize: 18 }}>{getTipoIcon(item.tipo)}</span>
                  </Badge>
                }
                title={
                  <Space>
                    <Text strong style={{ fontSize: 14 }}>{item.titulo}</Text>
                    <Tag color={getTipoColor(item.tipo)} style={{ fontSize: 12 }}>
                      {item.tipo.toUpperCase()}
                    </Tag>
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {item.mensaje}
                    </Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {dayjs(item.fecha_creacion).fromNow()}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </div>
  );

  return (
    <Dropdown
      menu={{ items: [] }}
      popupRender={() => menuContent}
      trigger={['click']}
      open={open}
      onOpenChange={setOpen}
      placement="bottomRight"
      arrow
    >
      <Button type="text" shape="circle" icon={<BellOutlined />} style={{ position: 'relative' }}>
        {noLeidas > 0 && (
          <Badge
            count={noLeidas}
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              backgroundColor: '#ff4d4f',
            }}
          />
        )}
      </Button>
    </Dropdown>
  );
};

export default NotificationDropdown;
