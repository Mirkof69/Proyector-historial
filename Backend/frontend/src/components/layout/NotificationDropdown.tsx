/**
 * =============================================================================
 * DROPDOWN DE NOTIFICACIONES
 * =============================================================================
 * Componente para mostrar notificaciones en el header
 * =============================================================================
 */

import React, { useState } from 'react';
import { Badge, Dropdown, List, Button, Typography, Space, Tag, Empty, Spin } from 'antd';
import { BellOutlined } from '@ant-design/icons';
import { Notificacion } from '../../services/notificacionesService';
import { useNotifications } from '../../contexts/NotificationsContext';
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

/**
 * La campana del encabezado.
 *
 * Antes este componente cargaba las notificaciones SOLO al abrir el
 * desplegable, y el número del badge salía de contar esa lista. Como la lista
 * empezaba vacía, **el badge mostraba 0 hasta que alguien hacía clic**: la
 * campana no avisaba de nada. Había que abrirla para enterarse de que había
 * una alerta médica esperando, que es justo lo contrario de para lo que sirve.
 *
 * Ahora se alimenta del contexto de notificaciones, que ya trae el conteo del
 * servidor desde que carga la página y lo actualiza por WebSocket en cuanto
 * llega algo nuevo. El desplegable no pide nada al abrirse: lo que muestra ya
 * está cargado.
 */
const NotificationDropdown: React.FC = () => {
  const [open, setOpen] = useState(false);
  const {
    notifications: notificaciones,
    unreadCount: noLeidas,
    urgentCount: urgentes,
    loading,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
  };

  const handleMarcarLeida = async (id: number) => {
    await markAsRead(id);
  };

  const handleMarcarTodasLeidas = async () => {
    await markAllAsRead();
  };

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
      onOpenChange={handleOpenChange}
      placement="bottomRight"
      arrow
    >
      <Button type="text" shape="circle" icon={<BellOutlined />} style={{ position: 'relative' }}>
        {noLeidas > 0 && (
          <Badge
            count={noLeidas}
            // `overflowCount` porque el numero real puede ser de miles: sin
            // esto el badge escribe "7135" encima del icono y lo deforma.
            overflowCount={99}
            // Rojo si hay alguna urgente o critica; naranja si solo hay
            // pendientes normales. El color dice si hay que mirar AHORA.
            title={
              urgentes > 0
                ? `${noLeidas} pendientes, ${urgentes} urgentes`
                : `${noLeidas} pendientes`
            }
            style={{
              position: 'absolute',
              top: -4,
              right: -4,
              backgroundColor: urgentes > 0 ? '#ff4d4f' : '#fa8c16',
            }}
          />
        )}
      </Button>
    </Dropdown>
  );
};

export default NotificationDropdown;
