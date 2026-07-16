import React from 'react';
import { Modal, Space, Form, DatePicker, Row, Col, Card, Badge, Button } from 'antd';
import { ClockCircleOutlined, SearchOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';
import { Consultorio } from '../../../services/consultoriosService';

const searchIcon = <SearchOutlined />;

interface DisponibilidadModalProps {
  modalDisponibilidadVisible: boolean;
  consultorioDisponibilidad: Consultorio | null;
  formDisponibilidad: FormInstance;
  verificandoDisponibilidad: boolean;
  resultadoDisponibilidad: any;
  onClose: () => void;
  handleVerificarDisponibilidad: (values: any) => void;
}

const DisponibilidadModal: React.FC<DisponibilidadModalProps> = ({
  modalDisponibilidadVisible, consultorioDisponibilidad, formDisponibilidad,
  verificandoDisponibilidad, resultadoDisponibilidad, onClose, handleVerificarDisponibilidad,
}) => (
  <Modal
    title={
      <Space>
        <ClockCircleOutlined />
        Verificar Disponibilidad - {consultorioDisponibilidad?.nombre}
      </Space>
    }
    open={modalDisponibilidadVisible}
    onCancel={onClose}
    footer={null}
    destroyOnHidden
  >
    <Form form={formDisponibilidad} layout="vertical" onFinish={handleVerificarDisponibilidad}>
      <Form.Item
        label="Fecha"
        name="fecha"
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

      {resultadoDisponibilidad && (
        <Card
          style={{ marginBottom: 16 }}
          size="small"
          type={resultadoDisponibilidad.disponible ? 'inner' : 'inner'}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {resultadoDisponibilidad.disponible ? (
                <Badge status="success" text="DISPONIBLE" />
              ) : (
                <Badge status="error" text="NO DISPONIBLE" />
              )}
            </div>
            {resultadoDisponibilidad.motivo && (
              <div style={{ fontSize: 12, color: '#666' }}>
                {resultadoDisponibilidad.motivo}
              </div>
            )}
          </Space>
        </Card>
      )}

      <Form.Item>
        <Space>
          <Button
            type="primary"
            htmlType="submit"
            icon={searchIcon}
            loading={verificandoDisponibilidad}
          >
            Verificar
          </Button>
          <Button onClick={onClose}>Cerrar</Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);

export default DisponibilidadModal;
