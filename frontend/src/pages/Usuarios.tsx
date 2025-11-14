/**
 * =============================================================================
 * CRUD COMPLETO DE USUARIOS
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Space, message, Tag, Popconfirm, Card,
  Row, Col, Statistic, Drawer, Descriptions, Badge,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  UserOutlined, LockOutlined, MailOutlined, PhoneOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ReloadOutlined,
} from '@ant-design/icons';
import { usuariosService } from '../services/usuariosService';
import type { Usuario } from '../types';

const { Option } = Select;

const Usuarios: React.FC = () => {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingUsuario, setEditingUsuario] = useState<Usuario | null>(null);
  const [selectedUsuario, setSelectedUsuario] = useState<Usuario | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadUsuarios();
  }, []);

  const loadUsuarios = async () => {
    setLoading(true);
    try {
      const response = await usuariosService.list();
      setUsuarios(response.results || response);
    } catch (error: any) {
      message.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUsuario(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (usuario: Usuario) => {
    setEditingUsuario(usuario);
    form.setFieldsValue(usuario);
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await usuariosService.delete(id);
      message.success('Usuario eliminado correctamente');
      loadUsuarios();
    } catch (error: any) {
      message.error('Error al eliminar usuario');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingUsuario) {
        await usuariosService.update(editingUsuario.id, values);
        message.success('Usuario actualizado correctamente');
      } else {
        await usuariosService.create(values);
        message.success('Usuario creado correctamente');
      }
      setModalVisible(false);
      form.resetFields();
      loadUsuarios();
    } catch (error: any) {
      message.error(error.message || 'Error al guardar usuario');
    }
  };

  const handleToggleActive = async (usuario: Usuario) => {
    try {
      if (usuario.activo) {
        await usuariosService.deactivate(usuario.id);
        message.success('Usuario desactivado');
      } else {
        await usuariosService.activate(usuario.id);
        message.success('Usuario activado');
      }
      loadUsuarios();
    } catch (error) {
      message.error('Error al cambiar estado');
    }
  };

  const handleViewDetails = (usuario: Usuario) => {
    setSelectedUsuario(usuario);
    setDrawerVisible(true);
  };

  const columns = [
    {
      title: 'Nombre',
      key: 'nombre',
      render: (_: any, record: Usuario) => `${record.nombre} ${record.apellido}`,
      filteredValue: [searchText],
      onFilter: (value: any, record: Usuario) => {
        const search = value.toLowerCase();
        return (
          record.nombre.toLowerCase().includes(search) ||
          record.apellido.toLowerCase().includes(search) ||
          record.username.toLowerCase().includes(search) ||
          record.email.toLowerCase().includes(search)
        );
      },
    },
    {
      title: 'Usuario',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Rol',
      dataIndex: 'rol',
      key: 'rol',
      render: (rol: string) => {
        const colors: Record<string, string> = {
          admin: 'red',
          medico: 'blue',
          enfermero: 'green',
          paciente: 'default',
        };
        return <Tag color={colors[rol] || 'default'}>{rol.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean) => (
        <Badge
          status={activo ? 'success' : 'error'}
          text={activo ? 'Activo' : 'Inactivo'}
        />
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Usuario) => (
        <Space>
          <Button
            type="link"
            icon={<SearchOutlined />}
            onClick={() => handleViewDetails(record)}
          >
            Ver
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Editar
          </Button>
          <Button
            type="link"
            icon={record.activo ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
            onClick={() => handleToggleActive(record)}
          >
            {record.activo ? 'Desactivar' : 'Activar'}
          </Button>
          <Popconfirm
            title="¿Está seguro de eliminar este usuario?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sí"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const activos = usuarios.filter((u) => u.activo).length;
  const medicos = usuarios.filter((u) => u.rol === 'medico').length;
  const enfermeros = usuarios.filter((u) => u.rol === 'enfermero').length;

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="Total Usuarios" value={usuarios.length} prefix={<UserOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="Activos" value={activos} prefix={<CheckCircleOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="Médicos" value={medicos} />
          </Col>
          <Col span={6}>
            <Statistic title="Enfermeros" value={enfermeros} />
          </Col>
        </Row>
      </Card>

      <Card
        title="Gestión de Usuarios"
        extra={
          <Space>
            <Input
              placeholder="Buscar..."
              prefix={<SearchOutlined />}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadUsuarios}>
              Actualizar
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              Nuevo Usuario
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={usuarios}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* MODAL CREAR/EDITAR */}
      <Modal
        title={editingUsuario ? 'Editar Usuario' : 'Nuevo Usuario'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="nombre"
                label="Nombre"
                rules={[{ required: true, message: 'Ingrese el nombre' }]}
              >
                <Input prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="apellido"
                label="Apellido"
                rules={[{ required: true, message: 'Ingrese el apellido' }]}
              >
                <Input prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="username"
            label="Nombre de Usuario"
            rules={[{ required: true, message: 'Ingrese el username' }]}
          >
            <Input prefix={<UserOutlined />} />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Ingrese el email' },
              { type: 'email', message: 'Email inválido' },
            ]}
          >
            <Input prefix={<MailOutlined />} />
          </Form.Item>

          {!editingUsuario && (
            <Form.Item
              name="password"
              label="Contraseña"
              rules={[
                { required: true, message: 'Ingrese la contraseña' },
                { min: 8, message: 'Mínimo 8 caracteres' },
              ]}
            >
              <Input.Password prefix={<LockOutlined />} />
            </Form.Item>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="rol"
                label="Rol"
                rules={[{ required: true, message: 'Seleccione el rol' }]}
              >
                <Select>
                  <Option value="admin">Administrador</Option>
                  <Option value="medico">Médico</Option>
                  <Option value="enfermero">Enfermero</Option>
                  <Option value="paciente">Paciente</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="telefono" label="Teléfono">
                <Input prefix={<PhoneOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="especialidad" label="Especialidad">
            <Input />
          </Form.Item>

          <Form.Item name="matricula" label="Matrícula Profesional">
            <Input />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
              <Button type="primary" htmlType="submit">
                {editingUsuario ? 'Actualizar' : 'Crear'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* DRAWER DETALLES */}
      <Drawer
        title="Detalles del Usuario"
        placement="right"
        width={500}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedUsuario && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="Nombre">
              {selectedUsuario.nombre} {selectedUsuario.apellido}
            </Descriptions.Item>
            <Descriptions.Item label="Usuario">{selectedUsuario.username}</Descriptions.Item>
            <Descriptions.Item label="Email">{selectedUsuario.email}</Descriptions.Item>
            <Descriptions.Item label="Rol">
              <Tag color={selectedUsuario.rol === 'admin' ? 'red' : 'blue'}>
                {selectedUsuario.rol.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Teléfono">{selectedUsuario.telefono || '-'}</Descriptions.Item>
            <Descriptions.Item label="Especialidad">
              {selectedUsuario.especialidad || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Matrícula">{selectedUsuario.matricula || '-'}</Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Badge
                status={selectedUsuario.activo ? 'success' : 'error'}
                text={selectedUsuario.activo ? 'Activo' : 'Inactivo'}
              />
            </Descriptions.Item>
            <Descriptions.Item label="Fecha de Creación">
              {new Date(selectedUsuario.fecha_creacion).toLocaleString('es-ES')}
            </Descriptions.Item>
            <Descriptions.Item label="Último Acceso">
              {selectedUsuario.ultimo_acceso
                ? new Date(selectedUsuario.ultimo_acceso).toLocaleString('es-ES')
                : 'Nunca'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
};

export default Usuarios;
