import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Space, Tag, Avatar, Typography, Drawer, Descriptions } from 'antd';
import {
  DeleteOutlined,
  CheckOutlined,
  BellOutlined,
  ExportOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { Notificacion } from '../../../services/notificacionesService';
import { getTypeIcon, getTypeLabel, getTypeTagColor, getTypeAvatarClass } from '../notificacionesUtils';

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
}) => {
  const navigate = useNavigate();
  return (
  <Drawer
    title={
      <Space>
        <Avatar icon={selectedNotification ? getTypeIcon(selectedNotification.tipo) : <BellOutlined />} className={getTypeAvatarClass(selectedNotification?.tipo ?? '')} />
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
            <Tag color={getTypeTagColor(selectedNotification.tipo)}>
              {getTypeLabel(selectedNotification.tipo)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Tag color={selectedNotification.leida ? 'default' : 'warning'}>
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
              <Text type="secondary" className="notifications-page__fecha--xs">
                ({dayjs(selectedNotification.fecha_creacion).fromNow()})
              </Text>
            </Space>
          </Descriptions.Item>
          <Descriptions.Item label="ID de Notificación">
            <Text code>{selectedNotification.id}</Text>
          </Descriptions.Item>
        </Descriptions>

        <div className="notificacion-detalle__acciones">
          {selectedNotification.enlace && selectedNotification.enlace !== '/dashboard/notificaciones' && (
            <Button
              type="primary"
              icon={<ExportOutlined />}
              onClick={() => {
                if (!selectedNotification.leida) handleMarkAsRead(selectedNotification.id);
                onClose();
                navigate(selectedNotification.enlace as string);
              }}
            >
              {selectedNotification.url_texto || 'Abrir'}
            </Button>
          )}
          {!selectedNotification.leida && (
            <Button
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
        </div>
      </div>
    )}
  </Drawer>
  );
};

export default NotificacionDrawer;
