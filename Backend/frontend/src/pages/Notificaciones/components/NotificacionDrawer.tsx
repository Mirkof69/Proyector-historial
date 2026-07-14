import React from 'react';
import { Button, Space, Tag, Avatar, Typography, Drawer, Descriptions } from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  BellOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Notificacion } from '../../../services/notificacionesService';
import { getTypeIcon, getTypeLabel } from '../notificacionesUtils';

const { Text } = Typography;

const CHECK_ICON_2 = <CheckOutlined />;
const DELETE_ICON_6 = <DeleteOutlined />;

interface NotificacionDrawerProps {
  open: boolean;
  onClose: () => void;
  selectedNotification: Notificacion | null;
  handleMarkAsRead: (id: number) => void;
  handleDelete: (id: number) => void;
}

const NotificacionDrawer: React.FC<NotificacionDrawerProps> = ({
  open, onClose, selectedNotification, handleMarkAsRead, handleDelete,
}) => (
  <Drawer
    title={
      <Space>
        <Avatar icon={selectedNotification ? getTypeIcon(selectedNotification.tipo) : <BellOutlined />} />
        <Text strong>Detalles de Notificación</Text>
      </Space>
    }
    placement="right"
    width={500}
    onClose={onClose}
    open={open}
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
                onClose();
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
              onClose();
            }}
          >
            Eliminar
          </Button>
        </Space>
      </div>
    )}
  </Drawer>
);

export default NotificacionDrawer;
