import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Tag, Input, Card, message, Modal, Form, DatePicker, Select, Row, Col } from 'antd';
import { PlusOutlined, SearchOutlined, EditOutlined, EyeOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import { pacientesService } from '../services/pacientesService';
import FormularioPaciente from './FormularioPaciente';
import DetallePaciente from './DetallePaciente';
import dayjs from 'dayjs';

interface Paciente {
  id: number;
  nombre: string;
  apellido_paterno: string;
  apellido_materno: string;
  fecha_nacimiento: string;
  telefono_principal: string;
  email: string;
  activo: boolean;
  id_clinico: string;
  genero: string;
  cedula_identidad: string;
  direccion: string;
}

const Pacientes: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [showDetalle, setShowDetalle] = useState(false);
  const [selectedPacienteId, setSelectedPacienteId] = useState<number | null>(null);
  
  // Modal de eliminación
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
  const [pacienteToDelete, setPacienteToDelete] = useState<number | null>(null);
  
  // Modal de edición
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [pacienteToEdit, setPacienteToEdit] = useState<number | null>(null);
  const [editForm] = Form.useForm();
  const [loadingEdit, setLoadingEdit] = useState(false);

  useEffect(() => {
    fetchPacientes();
  }, []);

  const fetchPacientes = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      const response = await axios.get('http://127.0.0.1:8000/api/pacientes/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPacientes(response.data);
    } catch (error) {
      console.error('Error al cargar pacientes:', error);
      message.error('Error al cargar pacientes');
    } finally {
      setLoading(false);
    }
  };

  const handleSuccess = () => {
    setShowForm(false);
    fetchPacientes();
  };

  const handleVerDetalle = (id: number) => {
    setSelectedPacienteId(id);
    setShowDetalle(true);
  };

  // ========== EDITAR ==========
  const handleEdit = async (id: number) => {
    console.log('🟡 Abriendo modal de edición para ID:', id);
    
    // Si estamos en la vista de detalle, cerramos primero
    if (showDetalle) {
      setShowDetalle(false);
    }
    
    setPacienteToEdit(id);
    setIsEditModalVisible(true);
    
    // Cargar datos del paciente
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/pacientes/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const paciente = response.data;
      editForm.setFieldsValue({
        nombre: paciente.nombre,
        apellido_paterno: paciente.apellido_paterno,
        apellido_materno: paciente.apellido_materno,
        genero: paciente.genero,
        id_clinico: paciente.id_clinico,
        fecha_nacimiento: dayjs(paciente.fecha_nacimiento),
        telefono: paciente.telefono_principal,
        email: paciente.email,
        cedula_identidad: paciente.cedula_identidad,
        direccion: paciente.direccion
      });
    } catch (error) {
      message.error('Error al cargar datos del paciente');
      console.error(error);
    }
  };

  const confirmarEdicion = async () => {
    try {
      const values = await editForm.validateFields();
      setLoadingEdit(true);
      
      const token = authService.getToken();
      await axios.put(
        `http://127.0.0.1:8000/api/pacientes/${pacienteToEdit}/`,
        {
          ...values,
          fecha_nacimiento: dayjs(values.fecha_nacimiento).format('YYYY-MM-DD'),
          telefono_principal: values.telefono
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      message.success('Paciente actualizado correctamente');
      setIsEditModalVisible(false);
      setPacienteToEdit(null);
      editForm.resetFields();
      fetchPacientes();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('Por favor complete todos los campos requeridos');
      } else {
        message.error('Error al actualizar paciente');
        console.error(error);
      }
    } finally {
      setLoadingEdit(false);
    }
  };

  const cancelarEdicion = () => {
    setIsEditModalVisible(false);
    setPacienteToEdit(null);
    editForm.resetFields();
  };

  // ========== ELIMINAR ==========
  const handleDelete = (id: number) => {
    console.log('🔴 Abriendo modal para eliminar ID:', id);
    setPacienteToDelete(id);
    setIsDeleteModalVisible(true);
  };

  const confirmarEliminacion = async () => {
    if (!pacienteToDelete) return;

    try {
      const response = await pacientesService.deletePaciente(pacienteToDelete);
      console.log('✅ Respuesta del servidor:', response);
      message.success('Paciente eliminado correctamente');
      setIsDeleteModalVisible(false);
      setPacienteToDelete(null);
      fetchPacientes();
    } catch (error: any) {
      console.error('❌ Error:', error);
      message.error('Error al eliminar paciente');
    }
  };

  const cancelarEliminacion = () => {
    setIsDeleteModalVisible(false);
    setPacienteToDelete(null);
  };

 const columns = [
  {
    title: 'ID Clínico',
    dataIndex: 'id_clinico',
    key: 'id_clinico',
    width: 120,
  },
    {
      title: 'Nombre Completo',
      key: 'nombre_completo',
      render: (record: Paciente) => 
        `${record.nombre} ${record.apellido_paterno} ${record.apellido_materno || ''}`,
    },
    {
      title: 'Fecha Nacimiento',
      dataIndex: 'fecha_nacimiento',
      key: 'fecha_nacimiento',
    },
    {
      title: 'Teléfono',
      dataIndex: 'telefono_principal',
      key: 'telefono_principal',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean) => (
        <Tag color={activo ? 'green' : 'red'}>
          {activo ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as 'right',
      width: 250,
      render: (record: Paciente) => (
        <Space>
          <Button 
            icon={<EyeOutlined />} 
            size="small"
            onClick={() => handleVerDetalle(record.id)}
          >
            Ver
          </Button>
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            type="primary"
            onClick={() => handleEdit(record.id)}
          >
            Editar
          </Button>
          <Button 
            icon={<DeleteOutlined />} 
            size="small" 
            danger
            onClick={() => handleDelete(record.id)}
          >
            Eliminar
          </Button>
        </Space>
      ),
    },
  ];

  const filteredPacientes = pacientes.filter(p =>
    `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno}`.toLowerCase().includes(searchText.toLowerCase())
  );

  if (showForm) {
    return <FormularioPaciente onCancel={() => setShowForm(false)} onSuccess={handleSuccess} />;
  }

  if (showDetalle && selectedPacienteId) {
    return (
      <DetallePaciente 
        pacienteId={selectedPacienteId} 
        onBack={() => setShowDetalle(false)}
        onEdit={handleEdit}
      />
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <h2>Lista de Pacientes</h2>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowForm(true)}>
            Nuevo Paciente
          </Button>
        </div>

        <Input
          placeholder="Buscar por nombre..."
          prefix={<SearchOutlined />}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ marginBottom: 16, width: 300 }}
        />

        <Table
          columns={columns}
          dataSource={filteredPacientes}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* Modal de ELIMINAR */}
      <Modal
        title="Confirmar Eliminación"
        open={isDeleteModalVisible}
        onOk={confirmarEliminacion}
        onCancel={cancelarEliminacion}
        okText="Sí, eliminar"
        cancelText="Cancelar"
        okButtonProps={{ danger: true }}
      >
        <p>
          <ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
          ¿Está seguro de que desea eliminar este paciente?
        </p>
        <p><strong>Esta acción es PERMANENTE y no se puede deshacer.</strong></p>
      </Modal>

      {/* Modal de EDITAR */}
      <Modal
        title="Editar Paciente"
        open={isEditModalVisible}
        onOk={confirmarEdicion}
        onCancel={cancelarEdicion}
        okText="Guardar Cambios"
        cancelText="Cancelar"
        confirmLoading={loadingEdit}
        width={800}
      >
        <Form form={editForm} layout="vertical">
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="nombre" label="Nombre" rules={[{ required: true, message: 'Campo requerido' }]}>
                <Input placeholder="Nombre" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="apellido_paterno" label="Apellido Paterno" rules={[{ required: true, message: 'Campo requerido' }]}>
                <Input placeholder="Apellido Paterno" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="apellido_materno" label="Apellido Materno">
                <Input placeholder="Apellido Materno" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="genero" label="Género" rules={[{ required: true, message: 'Campo requerido' }]}>
                <Select placeholder="Seleccionar género">
                  <Select.Option value="femenino">Femenino</Select.Option>
                  <Select.Option value="masculino">Masculino</Select.Option>
                  <Select.Option value="otro">Otro</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="id_clinico" label="ID Clínico">
                <Input placeholder="ID Clínico" disabled />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="fecha_nacimiento" label="Fecha de Nacimiento" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="telefono" label="Teléfono">
                <Input placeholder="Teléfono" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Email inválido' }]}>
                <Input placeholder="Email" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="cedula_identidad" label="Cédula de Identidad">
                <Input placeholder="CI" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="direccion" label="Dirección">
                <Input placeholder="Dirección" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default Pacientes;