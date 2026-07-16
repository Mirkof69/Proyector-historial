import React from 'react';
import {
  Modal, Space, Form, Divider, Row, Col, Input, Select, InputNumber, Switch, Button,
} from 'antd';
import { PlusOutlined, EditOutlined, SaveOutlined } from '@ant-design/icons';
import type { FormInstance } from 'antd';

const { Option } = Select;
const { TextArea } = Input;

const saveIcon = <SaveOutlined />;

interface ConsultorioFormModalProps {
  modalVisible: boolean;
  modalMode: 'create' | 'edit';
  formModal: FormInstance;
  guardando: boolean;
  handleCerrarModal: () => void;
  handleGuardarModal: (values: any) => void;
}

const ConsultorioFormModal: React.FC<ConsultorioFormModalProps> = ({
  modalVisible, modalMode, formModal, guardando, handleCerrarModal, handleGuardarModal,
}) => (
  <Modal
    title={
      <Space>
        {modalMode === 'create' ? <PlusOutlined /> : <EditOutlined />}
        {modalMode === 'create' ? 'Crear Nuevo Consultorio' : 'Editar Consultorio'}
      </Space>
    }
    open={modalVisible}
    onCancel={handleCerrarModal}
    footer={null}
    width={900}
    destroyOnHidden
  >
    <Form
      form={formModal}
      layout="vertical"
      onFinish={handleGuardarModal}
      initialValues={{
        activo: true,
        tiene_camilla: false,
        tiene_escritorio: false,
        tiene_computadora: false,
        tiene_lavamanos: false,
        tiene_oxigeno: false,
        tiene_aspirador: false,
        estado: 'disponible',
        capacidad_personas: 1,
      }}
    >
      <Divider orientation="left">Información Básica</Divider>
      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Form.Item
            label="Código"
            name="codigo"
            rules={[
              { required: true, message: 'El código es requerido' },
              { max: 20, message: 'Máximo 20 caracteres' },
            ]}
          >
            <Input placeholder="Ej: CONS-001" />
          </Form.Item>
        </Col>
        <Col xs={24} md={16}>
          <Form.Item
            label="Nombre"
            name="nombre"
            rules={[
              { required: true, message: 'El nombre es requerido' },
              { max: 100, message: 'Máximo 100 caracteres' },
            ]}
          >
            <Input placeholder="Ej: Consultorio de Ginecología 1" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item
            label="Tipo"
            name="tipo"
            rules={[{ required: true, message: 'El tipo es requerido' }]}
          >
            <Select placeholder="Seleccione tipo">
              <Option value="consulta">Consulta</Option>
              <Option value="procedimientos">Procedimientos</Option>
              <Option value="emergencia">Emergencia</Option>
              <Option value="multifuncional">Multifuncional</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item label="Estado" name="estado">
            <Select placeholder="Seleccione estado">
              <Option value="disponible">Disponible</Option>
              <Option value="ocupado">Ocupado</Option>
              <Option value="mantenimiento">Mantenimiento</Option>
              <Option value="limpieza">Limpieza</Option>
              <Option value="reservado">Reservado</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={8}>
          <Form.Item label="Área" name="area">
            <Input placeholder="Ej: Maternidad" />
          </Form.Item>
        </Col>
        <Col xs={24} md={8}>
          <Form.Item label="Piso" name="piso">
            <InputNumber min={0} max={20} style={{ width: '100%' }} placeholder="0" />
          </Form.Item>
        </Col>
        <Col xs={24} md={8}>
          <Form.Item label="Capacidad" name="capacidad_personas">
            <InputNumber min={1} max={20} style={{ width: '100%' }} />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Equipamiento</Divider>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Form.Item label="Tipo de Equipamiento" name="equipamiento">
            <Select placeholder="Seleccione equipamiento" allowClear>
              <Option value="basico">Básico</Option>
              <Option value="intermedio">Intermedio</Option>
              <Option value="avanzado">Avanzado</Option>
              <Option value="quirurgico">Quirúrgico</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={12} md={6}>
          <Form.Item label="Camilla" name="tiene_camilla" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item label="Escritorio" name="tiene_escritorio" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item label="Computadora" name="tiene_computadora" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item label="Lavamanos" name="tiene_lavamanos" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={12} md={6}>
          <Form.Item label="Oxígeno" name="tiene_oxigeno" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item label="Aspirador" name="tiene_aspirador" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col xs={12} md={6}>
          <Form.Item label="Activo" name="activo" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
      </Row>

      <Divider orientation="left">Descripción</Divider>
      <Row gutter={16}>
        <Col xs={24}>
          <Form.Item label="Descripción" name="descripcion">
            <TextArea rows={2} placeholder="Descripción del consultorio" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24}>
          <Form.Item label="Observaciones" name="observaciones">
            <TextArea rows={2} placeholder="Notas adicionales" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" icon={saveIcon} loading={guardando}>
            {modalMode === 'create' ? 'Crear' : 'Actualizar'} Consultorio
          </Button>
          <Button onClick={handleCerrarModal}>Cancelar</Button>
        </Space>
      </Form.Item>
    </Form>
  </Modal>
);

export default ConsultorioFormModal;
