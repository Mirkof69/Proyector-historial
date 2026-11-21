import React from 'react';
import { Drawer, Space, Button, List, Tag } from 'antd';
import { CalendarOutlined, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Consultorio, ReservaConsultorio } from '../../../services/consultoriosService';

const plusIcon = <PlusOutlined />;

interface ReservasDrawerProps {
  drawerReservasVisible: boolean;
  consultorioReservas: Consultorio | null;
  reservas: ReservaConsultorio[];
  loadingReservas: boolean;
  onClose: () => void;
  handleAbrirModalReserva: () => void;
  handleAprobarReserva: (reservaId: number) => void;
  handleRechazarReserva: (reservaId: number) => void;
  handleCancelarReserva: (reservaId: number) => void;
}

const ReservasDrawer: React.FC<ReservasDrawerProps> = ({
  drawerReservasVisible, consultorioReservas, reservas, loadingReservas, onClose,
  handleAbrirModalReserva, handleAprobarReserva, handleRechazarReserva, handleCancelarReserva,
}) => (
  <Drawer
    title={
      <Space>
        <CalendarOutlined />
        Reservas - {consultorioReservas?.nombre}
      </Space>
    }
    placement="right"
    onClose={onClose}
    open={drawerReservasVisible}
    width={600}
  >
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      <Button
        type="primary"
        icon={plusIcon}
        onClick={handleAbrirModalReserva}
        block
      >
        Nueva Reserva
      </Button>

      <List
        loading={loadingReservas}
        dataSource={reservas}
        renderItem={(reserva) => (
          <List.Item
            actions={[
              reserva.estado === 'pendiente' && (
                <Button
                  key="aprobar"
                  type="link"
                  size="small"
                  onClick={() => handleAprobarReserva(reserva.id!)}
                >
                  Aprobar
                </Button>
              ),
              reserva.estado === 'pendiente' && (
                <Button
                  key="rechazar"
                  type="link"
                  size="small"
                  danger
                  onClick={() => handleRechazarReserva(reserva.id!)}
                >
                  Rechazar
                </Button>
              ),
              (reserva.estado === 'aprobada' || reserva.estado === 'pendiente') && (
                <Button
                  key="cancelar"
                  type="link"
                  size="small"
                  onClick={() => handleCancelarReserva(reserva.id!)}
                >
                  Cancelar
                </Button>
              ),
            ].filter(Boolean)}
          >
            <List.Item.Meta
              title={
                <Space>
                  <span>{reserva.motivo}</span>
                  <Tag
                    color={
                      reserva.estado === 'aprobada'
                        ? 'success'
                        : reserva.estado === 'rechazada'
                        ? 'error'
                        : reserva.estado === 'cancelada'
                        ? 'default'
                        : 'processing'
                    }
                  >
                    {reserva.estado}
                  </Tag>
                </Space>
              }
              description={
                <Space direction="vertical" size="small">
                  <div>
                    Fecha: {dayjs(reserva.fecha_reserva).format('DD/MM/YYYY')}
                  </div>
                  <div>
                    Horario: {reserva.hora_inicio} - {reserva.hora_fin}
                  </div>
                  {reserva.solicitado_por_nombre && (
                    <div>Solicitado por: {reserva.solicitado_por_nombre}</div>
                  )}
                </Space>
              }
            />
          </List.Item>
        )}
      />
    </Space>
  </Drawer>
);

export default ReservasDrawer;
