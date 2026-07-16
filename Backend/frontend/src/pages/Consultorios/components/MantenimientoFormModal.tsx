import React from 'react';
import { Modal, Form, Select, DatePicker, Input, Space, Button } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';

const { Option } = Select;
const { TextArea } = Input;
const saveIcon = <SaveOutlined />;

interface MantenimientoFormModalProps {
  modalMantenimientoVisible: boolean;
  formMantenimiento: FormInstance;
  onClose: () => void;
  handleGuardarMantenimiento: (values: any) => void;
}

const MantenimientoFormModal: React.FC<MantenimientoFormModalProps> = ({
  modalMantenimientoVisible, formMantenimiento, onClose, handleGuardarMantenimiento,
}) => (
  <Modal
    title="Programar Mantenimiento"
    open={modalMantenimientoVisible}
    onCancel={onClose}
    footer={null}
    destroyOnHidden
  >
    <Form form={formMantenimiento} layout="vertical" onFinish={handleGuardarMantenimiento}>
      <Form.Item
        label="Tipo de Mantenimiento"
        name="tipo_mantenimiento"
        rules={[{ required: true, message: 'Seleccione el tipo' }]}
      >
        <Select placeholder="Seleccione tipo">
          <Option value="preventivo">Preventivo</Option>
          <Option value="correctivo">Correctivo</Option>
          <Option value="limpieza_profunda">Limpieza Profunda</Option>
          <Option value="desinfeccion">Desinfección</Option>
        </Select>
      </Form.Item>

      <Form.Item
        label="Fecha Programada"
        name="fecha_programada"
        rules={[{ required: true, message: 'Seleccione la fecha' }]}
      >
        <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
      </Form.Item>

      <Form.Item
        label="Descripción"
        name="descripcion"
        rules={[{ required: true, message: 'Ingrese la descripción' }]}
      >
        <TextArea rows={3} placeholder="Descripción del mantenimiento" />
      </Form.Item>

      <Form.Item label="Observaciones" name="observaciones">
        <TextArea rows={2} placeholder="Observaciones adicionales" />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={saveIcon}>
            Programar
          </Button>
          <Button onClick={onClose}>Cancelar</Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);

export default MantenimientoFormModal;
