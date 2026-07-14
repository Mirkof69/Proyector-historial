import React from 'react';
import { Modal, List, Button, Space, Tag, Badge, Typography } from 'antd';
import { CalendarOutlined, UserOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import { CitaDelDia, getEstadoColor, getTipoColor, getEstadoBadge } from './calendarioCitasUtils';

const { Text } = Typography;

interface ModalCitasDelDiaProps {
  open: boolean;
  dia: Dayjs;
  citas: CitaDelDia[];
  onClose: () => void;
  onVerDetalle: (citaId: number) => void;
}

const ModalCitasDelDia: React.FC<ModalCitasDelDiaProps> = ({ open, dia, citas, onClose, onVerDetalle }) => (
  <Modal
    title={
      <Space>
        <CalendarOutlined />
        Citas del {dia.format('DD/MM/YYYY')}
      </Space>
    }
    open={open}
    onCancel={onClose}
    footer={[
      <Button key="close" onClick={onClose}>
        Cerrar
      </Button>,
    ]}
    width={700}
  >
    <List
      dataSource={citas}
      renderItem={(cita) => (
        <List.Item
          actions={[
            <Button type="link" onClick={() => onVerDetalle(cita.id)} key="ver">
              Ver Detalle
            </Button>,
          ]}
        >
          <List.Item.Meta
            avatar={
              <div className="cita-avatar" style={{ background: getEstadoColor(cita.estado) }}>
                {cita.hora}
              </div>
            }
            title={
              <Space>
                <UserOutlined />
                <Text strong>{cita.paciente}</Text>
                <Tag color={getTipoColor(cita.tipo)}>
                  {cita.tipo.replace('_', ' ').toUpperCase()}
                </Tag>
              </Space>
            }
            description={
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <Badge status={getEstadoBadge(cita.estado)} />
                  <Text>{cita.estado.toUpperCase()}</Text>
                </Space>
                {cita.motivo && (
                  <Text type="secondary" ellipsis>
                    {cita.motivo}
                  </Text>
                )}
              </Space>
            }
          />
        </List.Item>
      )}
    />
  </Modal>
);

export default ModalCitasDelDia;
