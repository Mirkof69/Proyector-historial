/**
 * =============================================================================
 * DROPDOWN DE NOTIFICACIONES
 * =============================================================================
 * Componente para mostrar notificaciones en el header
 * =============================================================================
 */

import React, { useState } from 'react';
import { Badge, Dropdown, List, Button, Typography, Space, Tag, Empty, Spin } from 'antd';
import {
  BellOutlined, InfoCircleOutlined, WarningOutlined, CheckCircleOutlined,
  CloseCircleOutlined, NotificationOutlined,
} from '@ant-design/icons';
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

const TIPO_ICONO: Record<string, React.ReactNode> = {
  info: <InfoCircleOutlined />,
  warning: <WarningOutlined />,
  success: <CheckCircleOutlined />,
  error: <CloseCircleOutlined />,
};

const getTipoIcon = (tipo: string): React.ReactNode => (
  <span className={`notif-panel__icono notif-panel__icono--${tipo}`} aria-hidden="true">
    {TIPO_ICONO[tipo] ?? <NotificationOutlined />}
  </span>
);

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
    <div className="notif-panel">
      <div className="notif-panel__cabecera">
        <Text strong>Notificaciones</Text>
        {noLeidas > 0 && (
          <Button type="link" size="small" onClick={handleMarcarTodasLeidas}>
            Marcar todas como leídas
          </Button>
        )}
      </div>

      {loading ? (
        <div className="notif-panel__vacio">
          <Spin />
        </div>
      ) : notificaciones.length === 0 ? (
        <div className="notif-panel__vacio">
          <Empty description="No hay notificaciones" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        </div>
      ) : (
        <List
          dataSource={notificaciones}
          renderItem={(item) => (
            <List.Item
              className={`notif-panel__item${item.leida ? '' : ' notif-panel__item--no-leida'}`}
              onClick={() => !item.leida && handleMarcarLeida(item.id)}
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.leida}>
                    {getTipoIcon(item.tipo)}
                  </Badge>
                }
                title={
                  <Space>
                    <Text strong>{item.titulo}</Text>
                    <Tag color={getTipoColor(item.tipo)}>
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
    >
      <Button
        type="text"
        className="site-header__boton"
        icon={<BellOutlined />}
        style={{ position: 'relative' }}
        aria-label={noLeidas > 0 ? `Notificaciones: ${noLeidas} pendientes` : 'Notificaciones'}
      >
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
            className={`notif-badge ${urgentes > 0 ? 'notif-badge--urgente' : 'notif-badge--normal'}`}
          />
        )}
      </Button>
    </Dropdown>
  );
};

export default NotificationDropdown;
