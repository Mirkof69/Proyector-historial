import React, { useState, useReducer, useEffect } from 'react';
import { notificacionesService, Notificacion } from '../../services/notificacionesService';
import {
  Card, List, Button, Badge, Space, Dropdown,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Menu, message, Empty, Avatar, Typography,
  Drawer, Descriptions, DatePicker, Select, Input, Tooltip, Popconfirm, Row, Col, Table,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  Tag, Statistic, Spin as _Spin
} from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  BellOutlined,
  MailOutlined,
  PhoneOutlined,
  SearchOutlined,
  FilterOutlined,
  ReloadOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';

import './Notificaciones.css';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Text, Title } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;
const FILTER_ICON_3 = <FilterOutlined />;
const RELOAD_ICON_3 = <ReloadOutlined />;
const BELL_ICON_2 = <BellOutlined />;

  const Notificaciones: React.FC = () => {
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);
  const [loading, setLoading] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedNotification, setSelectedNotification] = useState<Notificacion | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'list'>('table');

  interface FiltrosNotifState {
    searchText: string;
    filterType: string | undefined;
    filterRead: string | undefined;
    dateRange: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
  }

  type FiltrosNotifAction =
    | { type: 'SET_SEARCH'; payload: string }
    | { type: 'SET_TYPE'; payload: string | undefined }
    | { type: 'SET_READ'; payload: string | undefined }
    | { type: 'SET_DATE_RANGE'; payload: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null }
    | { type: 'LIMPIAR' };

  const filtrosNotifReducer = (state: FiltrosNotifState, action: FiltrosNotifAction): FiltrosNotifState => {
    switch (action.type) {
      case 'SET_SEARCH': return { ...state, searchText: action.payload };
      case 'SET_TYPE': return { ...state, filterType: action.payload };
      case 'SET_READ': return { ...state, filterRead: action.payload };
      case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
      case 'LIMPIAR': return { searchText: '', filterType: undefined, filterRead: 'todas', dateRange: null };
      default: return state;
    }
  };

  const [filtros, dispatchFiltros] = useReducer(filtrosNotifReducer, {
    searchText: '',
    filterType: undefined,
    filterRead: 'todas',
    dateRange: null,
  });

  // Estadísticas
  const stats = {
    total: notificaciones.length,
    nuevas: notificaciones.filter(n => !n.leida).length,
    alertas: notificaciones.filter(n => n.tipo === 'error' || n.tipo === 'warning').length,
    info: notificaciones.filter(n => n.tipo === 'info' || n.tipo === 'success').length,
  };

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
  const filteredNotificaciones = notificaciones.filter(item => {
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

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'error': return <WarningOutlined />;
      case 'warning': return <WarningOutlined />;
      case 'success': return <CheckOutlined />;
      case 'cita': return <CalendarOutlined />;
      case 'examen': return <MedicineBoxOutlined />;
      case 'documento': return <FileTextOutlined />;
      case 'info':
      default: return <MessageOutlined />;
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'error': return 'Alerta';
      case 'warning': return 'Advertencia';
      case 'success': return 'Éxito';
      case 'cita': return 'Cita';
      case 'examen': return 'Examen';
      case 'documento': return 'Documento';
      case 'info': return 'Información';
      default: return type;
    }
  };

  const getTypeClass = (type: string) => {
    switch (type) {
      case 'error': return 'alerta';
      case 'warning': return 'alerta';
      case 'success': return 'mensaje';
      case 'cita': return 'cita';
      case 'examen': return 'examen';
      case 'documento': return 'recordatorio';
      case 'info': return 'mensaje';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 150,
      render: (tipo: string) => (
        <Space>
          <Avatar
            icon={getTypeIcon(tipo)}
            style={{
              backgroundColor:
                tipo === 'error' || tipo === 'warning' ? '#ff4d4f' :
                tipo === 'success' ? '#52c41a' :
                tipo === 'cita' ? '#1890ff' :
                tipo === 'examen' ? '#faad14' : '#13c2c2'
            }}
          />
          <Tag color={
            tipo === 'error' || tipo === 'warning' ? 'red' :
            tipo === 'success' ? 'green' :
            tipo === 'cita' ? 'blue' :
            tipo === 'examen' ? 'orange' : 'cyan'
          }>
            {getTypeLabel(tipo)}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Contenido',
      key: 'contenido',
      render: (_: any, record: Notificacion) => (
        <button
          type="button"
          onClick={() => handleViewDetails(record)}
          style={{ cursor: 'pointer', background: 'none', border: 'none', padding: 0, textAlign: 'left', width: '100%' }}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleViewDetails(record); } }}
        >
          <Text strong={!record.leida} style={{ display: 'block', marginBottom: 4 }}>
            {record.titulo}
          </Text>
          <Text type="secondary" style={{ fontSize: 13 }}>
            {record.mensaje}
          </Text>
        </button>
      ),
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_creacion',
      key: 'fecha',
      width: 150,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('DD/MM/YYYY HH:mm:ss')}>
          <span style={{ color: 'var(--text-tertiary)', fontSize: 13 }}>
            <ClockCircleOutlined style={{ marginRight: 6 }} />
            {dayjs(date).fromNow()}
          </span>
        </Tooltip>
      ),
      sorter: (a: Notificacion, b: Notificacion) =>
        new Date(a.fecha_creacion).getTime() - new Date(b.fecha_creacion).getTime(),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 100,
      render: (_: any, record: Notificacion) => (
        <Space>
          {!record.leida && (
            <Tooltip title="Marcar como leída">
              <Button
                type="text"
                className="action-btn read"
                icon={CHECK_ICON_2}
                onClick={() => handleMarkAsRead(record.id)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="¿Eliminar notificación?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sí"
            cancelText="No"
          >
            <Tooltip title="Eliminar">
              <Button
                type="text"
                className="action-btn delete"
                icon={DELETE_ICON_6}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

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

      <Row gutter={[16, 16]} className="notification-stats-row">
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Notificaciones"
              value={stats.total}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Badge count={stats.nuevas} overflowCount={99}>
            <Card style={{ width: '100%' }}>
              <Statistic
                title="No Leídas"
                value={stats.nuevas}
                prefix={<MailOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Badge>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Alertas Urgentes"
              value={stats.alertas}
              prefix={<PhoneOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
              suffix={<Tag color="red">Urgente</Tag>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Informativas"
              value={stats.info}
              prefix={<InfoCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={<Tag color="green">Info</Tag>}
            />
          </Card>
        </Col>
      </Row>

      <Card className="filters-card" bodyStyle={{ padding: '16px 24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={6}>
            <Input
              prefix={<SearchOutlined style={{ color: 'var(--text-tertiary)' }} />}
              placeholder="Buscar en notificaciones..."
              value={filtros.searchText}
              onChange={e => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
              allowClear
            />
          </Col>
          <Col xs={24} md={6}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['Fecha inicio', 'Fecha fin']}
              value={filtros.dateRange}
              onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates })}
              format="DD/MM/YYYY"
            />
          </Col>
          <Col xs={24} md={4}>
            <Select
              placeholder="Tipo"
              style={{ width: '100%' }}
              allowClear
              value={filtros.filterType}
              onChange={(val) => dispatchFiltros({ type: 'SET_TYPE', payload: val })}
            >
              <Option value="info">Información</Option>
              <Option value="warning">Advertencia</Option>
              <Option value="error">Alerta</Option>
              <Option value="success">Éxito</Option>
              <Option value="cita">Citas</Option>
              <Option value="examen">Exámenes</Option>
            </Select>
          </Col>
          <Col xs={24} md={4}>
            <Select
              placeholder="Estado"
              style={{ width: '100%' }}
              value={filtros.filterRead}
              onChange={(val) => dispatchFiltros({ type: 'SET_READ', payload: val })}
            >
              <Option value="todas">Todas</Option>
              <Option value="nuevas">No leídas</Option>
              <Option value="leidas">Leídas</Option>
            </Select>
          </Col>
          <Col xs={24} md={4} style={{ textAlign: 'right' }}>
            <Text type="secondary">
              Mostrando {filteredNotificaciones.length} de {notificaciones.length}
            </Text>
          </Col>
        </Row>
      </Card>

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
          <List
            itemLayout="horizontal"
            dataSource={filteredNotificaciones}
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} items`
            }}
            locale={{
              emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No se encontraron notificaciones" />
            }}
            renderItem={(item) => (
              <List.Item
                key={item.id}
                className={`notification-list-item ${getTypeClass(item.tipo)} ${!item.leida ? 'unread' : ''}`}
                actions={[
                  !item.leida && (
                    <Tooltip title="Marcar como leída" key="read">
                      <Button
                        type="text"
            icon={CHECK_ICON_2}
                        onClick={() => handleMarkAsRead(item.id)}
                      />
                    </Tooltip>
                  ),
                  <Popconfirm
                    key="delete"
                    title="¿Eliminar notificación?"
                    onConfirm={() => handleDelete(item.id)}
                    okText="Sí"
                    cancelText="No"
                  >
                    <Tooltip title="Eliminar">
                      <Button type="text" danger icon={DELETE_ICON_6} />
                    </Tooltip>
                  </Popconfirm>
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Badge dot={!item.leida}>
                      <Avatar
                        icon={getTypeIcon(item.tipo)}
                        style={{
                          backgroundColor:
                            ['error', 'warning'].includes(item.tipo) ? '#ff4d4f' :
                            item.tipo === 'success' ? '#52c41a' :
                            ['cita'].includes(item.tipo) ? '#1890ff' :
                            ['examen'].includes(item.tipo) ? '#faad14' : '#13c2c2'
                        }}
                      />
                    </Badge>
                  }
                  title={
                    <Space>
                      <button type="button" onClick={() => handleViewDetails(item)} style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleViewDetails(item); } }}><Text strong={!item.leida}>
                        {item.titulo}
                      </Text></button>
                      <Tag color={
                        ['error', 'warning'].includes(item.tipo) ? 'red' :
                        item.tipo === 'success' ? 'green' :
                        ['cita'].includes(item.tipo) ? 'blue' :
                        ['examen'].includes(item.tipo) ? 'orange' : 'cyan'
                      }>
                        {getTypeLabel(item.tipo)}
                      </Tag>
                    </Space>
                  }
                  description={
                    <div>
                      <Text type="secondary">{item.mensaje}</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        <ClockCircleOutlined style={{ marginRight: 4 }} />
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

      <Drawer
        title={
          <Space>
            <Avatar icon={selectedNotification ? getTypeIcon(selectedNotification.tipo) : <BellOutlined />} />
            <Text strong>Detalles de Notificación</Text>
          </Space>
        }
        placement="right"
        width={500}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedNotification && (
          <div>
            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Tipo">
                <Tag color={
                  ['error', 'warning'].includes(selectedNotification.tipo) ? 'red' :
                  selectedNotification.tipo === 'success' ? 'green' :
                  ['cita'].includes(selectedNotification.tipo) ? 'blue' :
                  ['examen'].includes(selectedNotification.tipo) ? 'orange' : 'cyan'
                }>
                  {getTypeLabel(selectedNotification.tipo)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={selectedNotification.leida ? 'default' : 'gold'}>
                  {selectedNotification.leida ? 'Leída' : 'No Leída'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Título">
                <Text strong>{selectedNotification.titulo}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Mensaje">
                {selectedNotification.mensaje}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha de Creación">
                <Space direction="vertical" size={0}>
                  <Text>{dayjs(selectedNotification.fecha_creacion).format('DD/MM/YYYY HH:mm:ss')}</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    ({dayjs(selectedNotification.fecha_creacion).fromNow()})
                  </Text>
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="ID de Notificación">
                <Text code>{selectedNotification.id}</Text>
              </Descriptions.Item>
            </Descriptions>

            <Space style={{ marginTop: 24, width: '100%', justifyContent: 'flex-end' }}>
              {!selectedNotification.leida && (
                <Button
                  type="primary"
                  icon={CHECK_ICON_2}
                  onClick={() => {
                    handleMarkAsRead(selectedNotification.id);
                    setDrawerVisible(false);
                  }}
                >
                  Marcar como leída
                </Button>
              )}
              <Button
                danger
                icon={DELETE_ICON_6}
                onClick={() => {
                  handleDelete(selectedNotification.id);
                  setDrawerVisible(false);
                }}
              >
                Eliminar
              </Button>
            </Space>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default Notificaciones;
