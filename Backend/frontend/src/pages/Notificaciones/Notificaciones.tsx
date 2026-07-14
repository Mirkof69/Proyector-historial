import React, { useState, useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { notificacionesService, Notificacion } from '../../services/notificacionesService';
import { Card, Button, Space, Dropdown, Empty, Typography, Table } from "antd";
import {
  DeleteOutlined,
  CheckOutlined,
  BellOutlined,
  FilterOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';

import './Notificaciones.css';
import { filtrosNotifReducer } from './notificacionesUtils';
import NotificacionesStats from './components/NotificacionesStats';
import NotificacionesFiltros from './components/NotificacionesFiltros';
import { buildColumnsNotificaciones } from './components/columnsNotificaciones';
import NotificacionesListView from './components/NotificacionesListView';
import NotificacionDrawer from './components/NotificacionDrawer';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text, Title } = Typography;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;
const FILTER_ICON_3 = <FilterOutlined />;
const RELOAD_ICON_3 = <ReloadOutlined />;
const BELL_ICON_2 = <BellOutlined />;

  const Notificaciones: React.FC = () => {
  const [notificaciones, setNotificaciones] = useState<Notificacion[] | undefined>(undefined);
  const { message } = useAntdApp();
  const [loading, setLoading] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notificacion | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'list'>('table');

  const [filtros, dispatchFiltros] = useReducer(filtrosNotifReducer, {
    searchText: '',
    filterType: undefined,
    filterRead: 'todas',
    dateRange: null,
  });

  // Estadísticas
  const stats = {
    total: notificaciones?.length || 0,
    nuevas: notificaciones?.filter(n => !n.leida).length || 0,
    alertas: notificaciones?.filter(n => n.tipo === 'error' || n.tipo === 'warning').length || 0,
    info: notificaciones?.filter(n => n.tipo === 'info' || n.tipo === 'success').length || 0,
  };

  // eslint-disable-next-line react-doctor/no-initialize-state
  useEffect(() => {
    loadNotificaciones();
  }, []);

  const loadNotificaciones = async () => {
    setLoading(true);
    try {
      const data = await notificacionesService.listar();
      // Ordenar por fecha descendente
      const sorted = data.sort((a, b) =>
        new Date(b.fecha_creacion).getTime() - new Date(a.fecha_creacion).getTime()
      );
      setNotificaciones(sorted);
    } catch (error) {
      message.error('Error al cargar notificaciones');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificacionesService.marcarLeida(id);
      setNotificaciones(prev =>
        prev.map(n => n.id === id ? { ...n, leida: true } : n)
      );
      message.success('Marcada como leída');
    } catch (error) {
      message.error('Error al actualizar');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await notificacionesService.eliminar(id);
      setNotificaciones(prev => prev.filter(n => n.id !== id));
      message.success('Notificación eliminada');
    } catch (error) {
      message.error('Error al eliminar');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificacionesService.marcarTodasLeidas();
      setNotificaciones(prev => prev.map(n => ({ ...n, leida: true })));
      message.success('Todas marcadas como leídas');
    } catch (error) {
      message.error('Error al actualizar');
    }
  };

  const handleViewDetails = (notificacion: Notificacion) => {
    setSelectedNotification(notificacion);
    setDrawerVisible(true);
    if (!notificacion.leida) {
      handleMarkAsRead(notificacion.id);
    }
  };

  // Filtrado
  const filteredNotificaciones = (notificaciones || []).filter(item => {
    const matchesSearch = filtros.searchText
      ? item.titulo.toLowerCase().includes(filtros.searchText.toLowerCase()) ||
      item.mensaje.toLowerCase().includes(filtros.searchText.toLowerCase())
      : true;

    const matchesType = filtros.filterType ? item.tipo === filtros.filterType : true;

    let matchesRead = true;
    if (filtros.filterRead === 'nuevas') matchesRead = !item.leida;
    if (filtros.filterRead === 'leidas') matchesRead = item.leida;

    let matchesDate = true;
    if (filtros.dateRange && filtros.dateRange[0] && filtros.dateRange[1]) {
      const itemDate = dayjs(item.fecha_creacion);
      matchesDate = itemDate.isAfter(filtros.dateRange[0]) && itemDate.isBefore(filtros.dateRange[1]);
    }

    return matchesSearch && matchesType && matchesRead && matchesDate;
  });

  const columns = buildColumnsNotificaciones({ handleViewDetails, handleMarkAsRead, handleDelete });

  return (
    <div className="notifications-page fade-in">
      <div className="notifications-header">
        <div>
          <Title level={2}>Centro de Notificaciones</Title>
          <Text type="secondary">
            Gestiona tus alertas y mensajes del sistema
          </Text>
        </div>
        <Space>
          <Dropdown
            menu={{
              items: [
                {
                  key: '1',
                  icon: CHECK_ICON_2,
                  label: 'Marcar todas como leídas',
                  onClick: handleMarkAllAsRead
                },
                {
                  key: '2',
                  icon: BELL_ICON_2,
                  label: `Cambiar vista a ${viewMode === 'table' ? 'Lista' : 'Tabla'}`,
                  onClick: () => setViewMode(viewMode === 'table' ? 'list' : 'table')
                },
                {
                  type: 'divider'
                },
                {
                  key: '3',
                  icon: DELETE_ICON_6,
                  label: 'Eliminar todas leídas',
                  danger: true,
                  onClick: () => {
                    for (const n of (notificaciones || []).filter(n => n.leida)) {
                      handleDelete(n.id);
                    }
                  }
                }
              ]
            }}
            trigger={['click']}
          >
            <Button icon={FILTER_ICON_3}>
              Acciones
            </Button>
          </Dropdown>
          <Button
            icon={RELOAD_ICON_3}
            onClick={loadNotificaciones}
            loading={loading}
          >
            Actualizar
          </Button>
          <Button
            type="primary"
            icon={CHECK_ICON_2}
            onClick={handleMarkAllAsRead}
            disabled={stats.nuevas === 0}
          >
            Marcar todo leído
          </Button>
        </Space>
      </div>

      <NotificacionesStats stats={stats} />

      <NotificacionesFiltros
        filtros={filtros}
        dispatchFiltros={dispatchFiltros}
        filteredCount={filteredNotificaciones.length}
        total={notificaciones.length}
      />

      <div className="notifications-table-card">
        {viewMode === 'table' ? (
          <Table
            columns={columns}
            dataSource={filteredNotificaciones}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} items`
            }}
            rowClassName={(record) => !record.leida ? 'notification-row-unread' : ''}
            locale={{
              emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No se encontraron notificaciones" />
            }}
          />
        ) : (
          <NotificacionesListView
            dataSource={filteredNotificaciones}
            loading={loading}
            handleViewDetails={handleViewDetails}
            handleMarkAsRead={handleMarkAsRead}
            handleDelete={handleDelete}
          />
        )}
      </div>

      <NotificacionDrawer
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        selectedNotification={selectedNotification}
        handleMarkAsRead={handleMarkAsRead}
        handleDelete={handleDelete}
      />
    </div>
  );
};

export default Notificaciones;
