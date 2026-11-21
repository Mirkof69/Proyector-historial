import React, { useState, useReducer, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { notificacionesService, Notificacion, ResumenNotificaciones } from '../../services/notificacionesService';
import { Button, Card, Space, Dropdown, Empty, Typography, Table } from "antd";
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
import { useListadoServidor } from '../../hooks/useListadoServidor';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text, Title } = Typography;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;
const FILTER_ICON_3 = <FilterOutlined />;
const RELOAD_ICON_3 = <ReloadOutlined />;
const BELL_ICON_2 = <BellOutlined />;

  const Notificaciones: React.FC = () => {
  const { message } = useAntdApp();
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notificacion | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'list'>('table');

  const [filtros, dispatchFiltros] = useReducer(filtrosNotifReducer, {
    searchText: '',
    filterType: undefined,
    filterRead: 'todas',
    dateRange: null,
  });

  // Estadísticas de TODAS las notificaciones (resumen del servidor). Antes se
  // contaban sobre la primera página (máx. 200) y las urgentes se buscaban por
  // tipos «error»/«warning» que el sistema no usa: salían 200, 200, 0 y 0.
  const [resumen, setResumen] = useState<ResumenNotificaciones | null>(null);

  // En el servidor: antes se traían las primeras 200 y se buscaba solo en ellas.
  const listado = useListadoServidor<Notificacion>('/notificaciones/', {
    busqueda: filtros.searchText,
    tamanoInicial: 10,
    filtros: {
      tipo: filtros.filterType,
      leida: filtros.filterRead === 'nuevas' ? false : filtros.filterRead === 'leidas' ? true : undefined,
      fecha_desde: filtros.dateRange?.[0]?.format('YYYY-MM-DD'),
      fecha_hasta: filtros.dateRange?.[1]?.format('YYYY-MM-DD'),
    },
  });
  const notificaciones = listado.datos;
  const loading = listado.cargando;
  const refrescar = () => {
    notificacionesService.resumen().then(setResumen).catch(() => undefined);
    listado.recargar();
  };

  const stats = {
    total: resumen?.total ?? listado.total,
    nuevas: resumen?.pendientes ?? notificaciones.filter(n => !n.leida).length,
    alertas: resumen?.urgentes_total ?? 0,
    info: resumen?.informativas ?? 0,
  };

  // eslint-disable-next-line react-doctor/no-initialize-state
  useEffect(() => {
    notificacionesService.resumen().then(setResumen).catch(() => undefined);
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificacionesService.marcarLeida(id);
      refrescar();
      message.success('Marcada como leída');
    } catch (error) {
      message.error('Error al actualizar');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await notificacionesService.eliminar(id);
      refrescar();
      message.success('Notificación eliminada');
    } catch (error) {
      message.error('Error al eliminar');
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      await notificacionesService.marcarTodasLeidas();
      refrescar();
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

  const filteredNotificaciones = notificaciones;

  const columns = buildColumnsNotificaciones({ handleViewDetails, handleMarkAsRead, handleDelete });

  return (
    <div className="notifications-page page-container">
      <header className="notifications-page__cabecera">
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
                  label: 'Eliminar las leídas de esta página',
                  danger: true,
                  onClick: () => {
                    for (const n of notificaciones.filter(n => n.leida)) {
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
            onClick={refrescar}
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
      </header>

      <NotificacionesStats stats={stats} />

      <NotificacionesFiltros
        filtros={filtros}
        dispatchFiltros={dispatchFiltros}
        filteredCount={listado.total}
        total={stats.total}
      />

      <Card>
        {viewMode === 'table' ? (
          <Table
            columns={columns}
            dataSource={filteredNotificaciones}
            rowKey="id"
            loading={loading}
            pagination={listado.paginacion}
            onChange={listado.onChange}
            rowClassName={(record) => !record.leida ? 'notification-row-unread' : ''}
            locale={{
              emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No se encontraron notificaciones" />
            }}
            scroll={{ x: 760 }}
          />
        ) : (
          <NotificacionesListView
            dataSource={filteredNotificaciones}
            loading={loading}
            pagination={listado.paginacion}
            onCambiarPagina={(current, pageSize) => listado.onChange({ current, pageSize }, {}, {})}
            handleViewDetails={handleViewDetails}
            handleMarkAsRead={handleMarkAsRead}
            handleDelete={handleDelete}
          />
        )}
      </Card>

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
