/**
 * =============================================================================
 * DROPDOWN DE NOTIFICACIONES
 * =============================================================================
 * Componente para mostrar notificaciones en el header
 * =============================================================================
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Dropdown, List, Button, Typography, Space, Tag, Empty, Spin } from 'antd';
import {
  BellOutlined, InfoCircleOutlined, WarningOutlined, CalendarOutlined, ClockCircleOutlined,
  ExperimentOutlined, ExclamationCircleOutlined, NotificationOutlined, RightOutlined,
} from '@ant-design/icons';
import { Notificacion } from '../../services/notificacionesService';
import { useNotifications } from '../../contexts/NotificationsContext';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/es';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text } = Typography;

// El tipo real viene del servidor (alerta_critica, examen_listo, recordatorio_control…):
// antes se buscaba info/warning/error, nunca coincidía y la etiqueta mostraba el código.
const iconoDe = (tipo: string): React.ReactNode => {
  if (tipo.startsWith('examen')) return <ExperimentOutlined />;
  if (tipo.startsWith('cita')) return <CalendarOutlined />;
  if (tipo.startsWith('recordatorio')) return <ClockCircleOutlined />;
  if (tipo === 'alerta_critica') return <WarningOutlined />;
  if (tipo === 'alerta_advertencia') return <ExclamationCircleOutlined />;
  if (tipo.startsWith('alerta')) return <InfoCircleOutlined />;
  return <NotificationOutlined />;
};

const NIVEL: Record<string, { clase: string; color: string }> = {
  critica: { clase: 'error', color: 'error' },
  alta: { clase: 'warning', color: 'warning' },
  media: { clase: 'info', color: 'processing' },
  baja: { clase: 'success', color: 'default' },
};

const nivelDe = (item: Notificacion) =>
  NIVEL[item.prioridad ?? ''] ?? (item.tipo.includes('critic') ? NIVEL.critica : NIVEL.media);

const getTipoIcon = (item: Notificacion): React.ReactNode => (
  <span className={`notif-panel__icono notif-panel__icono--${nivelDe(item).clase}`} aria-hidden="true">
    {iconoDe(item.tipo)}
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
  const navigate = useNavigate();
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

  // Abre lo que la notificación anuncia (antes el clic solo la marcaba leída).
  const abrir = (item: Notificacion) => {
    if (!item.leida) markAsRead(item.id);
    setOpen(false);
    navigate(item.enlace || '/dashboard/notificaciones');
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
              onClick={() => abrir(item)}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); abrir(item); } }}
              role="button"
              tabIndex={0}
              extra={<RightOutlined className="notif-panel__ir" aria-hidden="true" />}
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.leida}>
                    {getTipoIcon(item)}
                  </Badge>
                }
                title={
                  <Space>
                    <Text strong>{item.titulo}</Text>
                    <Tag color={nivelDe(item).color}>
                      {item.tipo_display ?? item.tipo.replace(/_/g, ' ')}
                    </Tag>
                  </Space>
                }
                description={
                  <div>
                    {item.mensaje && <Text type="secondary" className="notif-panel__mensaje">{item.mensaje}</Text>}
                    <Text type="secondary" className="notif-panel__fecha">
                      {dayjs(item.fecha_creacion).fromNow()}
                    </Text>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
      <div className="notif-panel__pie">
        <Button type="link" size="small" onClick={() => { setOpen(false); navigate('/dashboard/notificaciones'); }}>
          Ver todas
        </Button>
      </div>
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
