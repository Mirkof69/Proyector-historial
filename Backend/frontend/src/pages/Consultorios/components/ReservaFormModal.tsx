import React from 'react';
import { Modal, Form, DatePicker, Row, Col, Input, Space, Button } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';

const { TextArea } = Input;
const saveIcon = <SaveOutlined />;

interface ReservaFormModalProps {
  modalReservaVisible: boolean;
  formReserva: FormInstance;
  onClose: () => void;
  handleGuardarReserva: (values: any) => void;
}

const ReservaFormModal: React.FC<ReservaFormModalProps> = ({
  modalReservaVisible, formReserva, onClose, handleGuardarReserva,
}) => (
  <Modal
    title="Nueva Reserva"
    open={modalReservaVisible}
    onCancel={onClose}
    footer={null}
    destroyOnHidden
  >
    <Form form={formReserva} layout="vertical" onFinish={handleGuardarReserva}>
      <Form.Item
        label="Fecha de Reserva"
        name="fecha_reserva"
        rules={[{ required: true, message: 'Seleccione la fecha' }]}
      >
        <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
      </Form.Item>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            label="Hora Inicio"
            name="hora_inicio"
            rules={[{ required: true, message: 'Seleccione hora inicio' }]}
          >
            <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="Hora Fin"
            name="hora_fin"
            rules={[{ required: true, message: 'Seleccione hora fin' }]}
          >
            <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        label="Motivo"
        name="motivo"
        rules={[{ required: true, message: 'Ingrese el motivo' }]}
      >
        <Input placeholder="Motivo de la reserva" />
      </Form.Item>

      <Form.Item label="Tipo de Actividad" name="tipo_actividad">
        <Input placeholder="Ej: Consulta especial, Procedimiento" />
      </Form.Item>

      <Form.Item label="Observaciones" name="observaciones">
        <TextArea rows={3} placeholder="Observaciones adicionales" />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={saveIcon}>
            Crear Reserva
          </Button>
          <Button onClick={onClose}>Cancelar</Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);

export default ReservaFormModal;
