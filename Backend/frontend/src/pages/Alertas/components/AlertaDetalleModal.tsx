import React from 'react';
import { Row, Col, Button, Space, Modal, Divider, Alert } from 'antd';
import { CheckCircleOutlined, AlertOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { AlertaMedica, AlertAction } from '../sistemaAlertasUtils';

interface AlertaDetalleModalProps {
  modalVisible: boolean;
  alertaSeleccionada: AlertaMedica | null;
  dispatch: React.Dispatch<AlertAction>;
  handleResolverAlerta: (id: number) => void;
  navigate: (path: string) => void;
}

const AlertaDetalleModal: React.FC<AlertaDetalleModalProps> = ({
  modalVisible, alertaSeleccionada, dispatch, handleResolverAlerta, navigate,
}) => (
  <Modal
    title={
      <Space>
        <AlertOutlined />
        Detalle de Alerta
      </Space>
    }
    open={modalVisible}
    onCancel={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}
    footer={[
      <Button key="close" onClick={() => dispatch({ type: 'SET_MODAL_VISIBLE', payload: false })}>
        Cerrar
      </Button>,
      alertaSeleccionada?.estado === 'activa' && (
        <Button
          key="resolver"
          type="primary"
          icon={<CheckCircleOutlined />}
          onClick={() => alertaSeleccionada && handleResolverAlerta(alertaSeleccionada.id)}
        >
          Resolver Alerta
        </Button>
      ),
    ]}
    width={700}
  >
    {alertaSeleccionada && (
      <div>
        <Alert
          message={alertaSeleccionada.titulo}
          description={alertaSeleccionada.descripcion}
          type={alertaSeleccionada.tipo === 'critica' ? 'error' : alertaSeleccionada.tipo === 'alta' ? 'warning' : 'info'}
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Divider orientation="left">Información del Paciente</Divider>
        <Row gutter={16}>
          <Col span={12}>
            <p><strong>Nombre:</strong> {alertaSeleccionada.paciente_nombre || 'N/A'}</p>
          </Col>
          <Col span={12}>
            <p>
              <strong>ID:</strong> {alertaSeleccionada.paciente_id || 'N/A'}
              {alertaSeleccionada.paciente_id && (
                <Button
                  type="link"
                  size="small"
                  onClick={() => navigate(`/dashboard/pacientes/${alertaSeleccionada.paciente_id}`)}
                >
                  Ver Paciente
                </Button>
              )}
            </p>
          </Col>
        </Row>

        <Divider orientation="left">Detalles de la Alerta</Divider>
        <Row gutter={16}>
          <Col span={12}>
            <p><strong>Categoría:</strong> {alertaSeleccionada.categoria}</p>
          </Col>
          <Col span={12}>
            <p><strong>Prioridad:</strong> {alertaSeleccionada.prioridad}</p>
          </Col>
          <Col span={12}>
            <p><strong>Creada:</strong> {dayjs(alertaSeleccionada.fecha_creacion).format('DD/MM/YYYY HH:mm')}</p>
          </Col>
          <Col span={12}>
            <p><strong>Asignado a:</strong> {alertaSeleccionada.asignado_a || 'Sin asignar'}</p>
          </Col>
        </Row>

        {alertaSeleccionada.notas && (
          <>
            <Divider orientation="left">Notas</Divider>
            <p>{alertaSeleccionada.notas}</p>
          </>
        )}
      </div>
    )}
  </Modal>
);

export default AlertaDetalleModal;
