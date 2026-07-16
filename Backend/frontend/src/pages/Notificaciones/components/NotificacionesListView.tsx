import React from 'react';
import { List, Button, Badge, Space, Empty, Avatar, Typography, Tooltip, Popconfirm, Tag } from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Notificacion } from '../../../services/notificacionesService';
import { getTypeIcon, getTypeLabel, getTypeClass } from '../notificacionesUtils';

const { Text } = Typography;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;

interface NotificacionesListViewProps {
  dataSource: Notificacion[];
  loading: boolean;
  handleViewDetails: (notificacion: Notificacion) => void;
  handleMarkAsRead: (id: number) => void;
  handleDelete: (id: number) => void;
}

const NotificacionesListView: React.FC<NotificacionesListViewProps> = ({
  dataSource, loading, handleViewDetails, handleMarkAsRead, handleDelete,
}) => (
  <List
    itemLayout="horizontal"
    dataSource={dataSource}
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
);

export default NotificacionesListView;
