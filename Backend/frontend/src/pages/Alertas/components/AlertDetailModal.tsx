import React from 'react';
import { Modal, Button, Space, Alert, Divider, Row, Col } from 'antd';
import { AlertOutlined, CheckCircleOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { useNavigate } from 'react-router-dom';

interface AlertaMedica {
  id: number;
  titulo: string;
  descripcion: string;
  tipo: string;
  paciente_id?: number;
  paciente_nombre?: string;
  estado: string;
  fecha_creacion: string;
  categoria: string;
  asignado_a?: string;
  notas?: string;
  prioridad: number;
}

interface AlertDetailModalProps {
  visible: boolean;
  alerta: AlertaMedica | null;
  onClose: () => void;
  onResolve: (id: number) => void;
}

const AlertDetailModal: React.FC<AlertDetailModalProps> = ({ visible, alerta, onClose, onResolve }) => {
  const navigate = useNavigate();

  if (!alerta) return null;

  return (
    <Modal
      title={<Space><AlertOutlined />Detalle de Alerta</Space>}
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" onClick={onClose}>Cerrar</Button>,
        alerta.estado === 'activa' && (
          <Button key="resolver" type="primary" icon={<CheckCircleOutlined />} onClick={() => onResolve(alerta.id)}>
            Resolver Alerta
          </Button>
        ),
      ]}
      width={700}
    >
      <Alert
        message={alerta.titulo}
        description={alerta.descripcion}
        type={alerta.tipo === 'critica' ? 'error' : alerta.tipo === 'alta' ? 'warning' : 'info'}
        showIcon
        style={{ marginBottom: 16 }}
      />
      <Divider orientation="left">Información del Paciente</Divider>
      <Row gutter={16}>
        <Col span={12}><p><strong>Nombre:</strong> {alerta.paciente_nombre || 'N/A'}</p></Col>
        <Col span={12}>
          <p><strong>ID:</strong> {alerta.paciente_id || 'N/A'}
            {alerta.paciente_id && (
              <Button type="link" size="small" onClick={() => navigate(`/dashboard/pacientes/${alerta.paciente_id}`)}>
                Ver Paciente
              </Button>
            )}
          </p>
        </Col>
      </Row>
      <Divider orientation="left">Detalles de la Alerta</Divider>
      <Row gutter={16}>
        <Col span={12}><p><strong>Categoría:</strong> {alerta.categoria}</p></Col>
        <Col span={12}><p><strong>Prioridad:</strong> {alerta.prioridad}</p></Col>
        <Col span={12}><p><strong>Creada:</strong> {dayjs(alerta.fecha_creacion).format('DD/MM/YYYY HH:mm')}</p></Col>
        <Col span={12}><p><strong>Asignado a:</strong> {alerta.asignado_a || 'Sin asignar'}</p></Col>
      </Row>
      {alerta.notas && (
        <>
          <Divider orientation="left">Notas</Divider>
          <p>{alerta.notas}</p>
        </>
      )}
    </Modal>
  );
};

export default AlertDetailModal;
