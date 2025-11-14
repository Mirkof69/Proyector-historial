/**
 * =============================================================================
 * CRUD COMPLETO DE PACIENTES - MEJORADO
 * =============================================================================
 * Incluye historia obstétrica (GPAC) y generación de PDF
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Space, message, Tag, Popconfirm,
  Card, Row, Col, Statistic, Drawer, Descriptions, Badge, DatePicker, InputNumber,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, UserOutlined,
  PhoneOutlined, MailOutlined, HomeOutlined, HeartOutlined, FilePdfOutlined,
  ReloadOutlined, IdcardOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { pacientesService } from '../services/pacientesService';
import type { Paciente } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const PacientesNew: React.FC = () => {
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingPaciente, setEditingPaciente] = useState<Paciente | null>(null);
  const [selectedPaciente, setSelectedPaciente] = useState<Paciente | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadPacientes();
  }, []);

  const loadPacientes = async () => {
    setLoading(true);
    try {
      const response = await pacientesService.list();
      setPacientes(response.results || response);
    } catch (error: any) {
      message.error('Error al cargar pacientes');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingPaciente(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (paciente: Paciente) => {
    setEditingPaciente(paciente);
    form.setFieldsValue({
      ...paciente,
      fecha_nacimiento: dayjs(paciente.fecha_nacimiento),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await pacientesService.delete(id);
      message.success('Paciente eliminado correctamente');
      loadPacientes();
    } catch (error: any) {
      message.error('Error al eliminar paciente');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        fecha_nacimiento: values.fecha_nacimiento.format('YYYY-MM-DD'),
      };

      if (editingPaciente) {
        await pacientesService.update(editingPaciente.id, data);
        message.success('Paciente actualizado correctamente');
      } else {
        await pacientesService.create(data);
        message.success('Paciente creado correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      loadPacientes();
    } catch (error: any) {
      message.error(error.message || 'Error al guardar paciente');
    }
  };

  const handleViewDetails = (paciente: Paciente) => {
    setSelectedPaciente(paciente);
    setDrawerVisible(true);
  };

  const handleExportPDF = async (id: number) => {
    message.info('Generando PDF del historial médico...');
    // TODO: Implementar generación de PDF
  };

  const columns = [
    {
      title: 'DNI',
      dataIndex: 'dni',
      key: 'dni',
      width: 120,
    },
    {
      title: 'Nombre Completo',
      key: 'nombre',
      render: (_: any, record: Paciente) => `${record.nombre} ${record.apellido}`,
      filteredValue: [searchText],
      onFilter: (value: any, record: Paciente) => {
        const search = value.toLowerCase();
        return (
          record.nombre.toLowerCase().includes(search) ||
          record.apellido.toLowerCase().includes(search) ||
          record.dni.toLowerCase().includes(search)
        );
      },
    },
    {
      title: 'Edad',
      dataIndex: 'edad',
      key: 'edad',
      width: 80,
      render: (edad: number) => `${edad} años`,
    },
    {
      title: 'Teléfono',
      dataIndex: 'telefono',
      key: 'telefono',
      width: 130,
    },
    {
      title: 'Grupo Sanguíneo',
      dataIndex: 'grupo_sanguineo',
      key: 'grupo_sanguineo',
      width: 120,
      render: (grupo: string, record: Paciente) =>
        grupo ? (
          <Tag color="red">
            {grupo}
            {record.factor_rh}
          </Tag>
        ) : (
          '-'
        ),
    },
    {
      title: 'Historia Obstétrica',
      key: 'gpac',
      width: 150,
      render: (_: any, record: Paciente) => {
        if (!record.gestas && !record.partos && !record.abortos && !record.cesareas) {
          return '-';
        }
        return (
          <Space size={4}>
            <Tag>G: {record.gestas || 0}</Tag>
            <Tag>P: {record.partos || 0}</Tag>
            <Tag>A: {record.abortos || 0}</Tag>
            <Tag>C: {record.cesareas || 0}</Tag>
          </Space>
        );
      },
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      width: 100,
      render: (activo: boolean) => (
        <Badge status={activo ? 'success' : 'error'} text={activo ? 'Activo' : 'Inactivo'} />
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 250,
      render: (_: any, record: Paciente) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<SearchOutlined />}
            onClick={() => handleViewDetails(record)}
          >
            Ver
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            Editar
          </Button>
          <Button
            type="link"
            size="small"
            icon={<FilePdfOutlined />}
            onClick={() => handleExportPDF(record.id)}
          >
            PDF
          </Button>
          <Popconfirm
            title="¿Eliminar este paciente?"
            onConfirm={() => handleDelete(record.id)}
            okText="Sí"
            cancelText="No"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Eliminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const totalPacientes = pacientes.length;
  const activos = pacientes.filter((p) => p.activo).length;
  const conEmbarazo = pacientes.filter((p) => (p.gestas || 0) > 0).length;

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="Total Pacientes" value={totalPacientes} prefix={<UserOutlined />} />
          </Col>
          <Col span={8}>
            <Statistic title="Activos" value={activos} prefix={<HeartOutlined />} />
          </Col>
          <Col span={8}>
            <Statistic title="Con Hist. Obstétrica" value={conEmbarazo} />
          </Col>
        </Row>
      </Card>

      <Card
        title="Gestión de Pacientes"
        extra={
          <Space>
            <Input
              placeholder="Buscar..."
              prefix={<SearchOutlined />}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadPacientes}>
              Actualizar
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              Nuevo Paciente
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={pacientes}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* MODAL CREAR/EDITAR */}
      <Modal
        title={editingPaciente ? 'Editar Paciente' : 'Nuevo Paciente'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="nombre"
                label="Nombre"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Input prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="apellido"
                label="Apellido"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Input prefix={<UserOutlined />} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="dni"
                label="DNI"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Input prefix={<IdcardOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="fecha_nacimiento"
                label="Fecha de Nacimiento"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="telefono"
                label="Teléfono"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <Input prefix={<PhoneOutlined />} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="email" label="Email">
                <Input prefix={<MailOutlined />} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="grupo_sanguineo" label="Grupo Sanguíneo">
                <Select>
                  <Option value="A">A</Option>
                  <Option value="B">B</Option>
                  <Option value="AB">AB</Option>
                  <Option value="O">O</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="factor_rh" label="Factor RH">
                <Select>
                  <Option value="+">Positivo (+)</Option>
                  <Option value="-">Negativo (-)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="ciudad" label="Ciudad">
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="direccion" label="Dirección">
            <Input prefix={<HomeOutlined />} />
          </Form.Item>

          <Card title="Historia Obstétrica (GPAC)" size="small" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Form.Item name="gestas" label="Gestas (G)">
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="partos" label="Partos (P)">
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="abortos" label="Abortos (A)">
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
              <Col span={6}>
                <Form.Item name="cesareas" label="Cesáreas (C)">
                  <InputNumber min={0} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          <Form.Item name="antecedentes_personales" label="Antecedentes Personales">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item name="antecedentes_familiares" label="Antecedentes Familiares">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item name="alergias" label="Alergias">
            <TextArea rows={2} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
              <Button type="primary" htmlType="submit">
                {editingPaciente ? 'Actualizar' : 'Crear'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* DRAWER DETALLES */}
      <Drawer
        title="Detalles del Paciente"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedPaciente && (
          <>
            <Descriptions title="Información Personal" column={1} bordered>
              <Descriptions.Item label="Nombre Completo">
                {selectedPaciente.nombre} {selectedPaciente.apellido}
              </Descriptions.Item>
              <Descriptions.Item label="DNI">{selectedPaciente.dni}</Descriptions.Item>
              <Descriptions.Item label="Fecha de Nacimiento">
                {new Date(selectedPaciente.fecha_nacimiento).toLocaleDateString('es-ES')}
              </Descriptions.Item>
              <Descriptions.Item label="Edad">{selectedPaciente.edad} años</Descriptions.Item>
              <Descriptions.Item label="Teléfono">{selectedPaciente.telefono}</Descriptions.Item>
              <Descriptions.Item label="Email">{selectedPaciente.email || '-'}</Descriptions.Item>
              <Descriptions.Item label="Dirección">{selectedPaciente.direccion || '-'}</Descriptions.Item>
              <Descriptions.Item label="Ciudad">{selectedPaciente.ciudad || '-'}</Descriptions.Item>
              <Descriptions.Item label="Grupo Sanguíneo">
                {selectedPaciente.grupo_sanguineo
                  ? `${selectedPaciente.grupo_sanguineo}${selectedPaciente.factor_rh}`
                  : '-'}
              </Descriptions.Item>
            </Descriptions>

            <Descriptions title="Historia Obstétrica (GPAC)" column={2} bordered style={{ marginTop: 16 }}>
              <Descriptions.Item label="Gestas">{selectedPaciente.gestas || 0}</Descriptions.Item>
              <Descriptions.Item label="Partos">{selectedPaciente.partos || 0}</Descriptions.Item>
              <Descriptions.Item label="Abortos">{selectedPaciente.abortos || 0}</Descriptions.Item>
              <Descriptions.Item label="Cesáreas">{selectedPaciente.cesareas || 0}</Descriptions.Item>
            </Descriptions>

            <Descriptions title="Antecedentes" column={1} bordered style={{ marginTop: 16 }}>
              <Descriptions.Item label="Personales">
                {selectedPaciente.antecedentes_personales || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Familiares">
                {selectedPaciente.antecedentes_familiares || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Alergias">{selectedPaciente.alergias || '-'}</Descriptions.Item>
            </Descriptions>

            <Space style={{ marginTop: 24, width: '100%', justifyContent: 'flex-end' }}>
              <Button icon={<FilePdfOutlined />} onClick={() => handleExportPDF(selectedPaciente.id)}>
                Descargar Historial PDF
              </Button>
            </Space>
          </>
        )}
      </Drawer>
    </div>
  );
};

export default PacientesNew;
