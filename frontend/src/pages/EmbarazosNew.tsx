/**
 * =============================================================================
 * CRUD COMPLETO DE EMBARAZOS
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Space, message, Tag, Popconfirm,
  Card, Row, Col, Statistic, Drawer, Descriptions, Badge, DatePicker, Switch, InputNumber,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, HeartOutlined,
  WarningOutlined, ReloadOutlined, CheckCircleOutlined, CloseCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { embarazosService } from '../services/embarazosService';
import { pacientesService } from '../services/pacientesService';
import type { Embarazo, Paciente } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const EmbarazosNew: React.FC = () => {
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingEmbarazo, setEditingEmbarazo] = useState<Embarazo | null>(null);
  const [selectedEmbarazo, setSelectedEmbarazo] = useState<Embarazo | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [embarazosRes, pacientesRes] = await Promise.all([
        embarazosService.list(),
        pacientesService.list(),
      ]);
      setEmbarazos(embarazosRes.results || embarazosRes);
      setPacientes(pacientesRes.results || pacientesRes);
    } catch (error: any) {
      message.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingEmbarazo(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (embarazo: Embarazo) => {
    setEditingEmbarazo(embarazo);
    form.setFieldsValue({
      ...embarazo,
      fur: dayjs(embarazo.fur),
      fpp: dayjs(embarazo.fpp),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await embarazosService.delete(id);
      message.success('Embarazo eliminado correctamente');
      loadData();
    } catch (error: any) {
      message.error('Error al eliminar embarazo');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        fur: values.fur.format('YYYY-MM-DD'),
        fpp: values.fpp.format('YYYY-MM-DD'),
      };

      if (editingEmbarazo) {
        await embarazosService.update(editingEmbarazo.id, data);
        message.success('Embarazo actualizado correctamente');
      } else {
        await embarazosService.create(data);
        message.success('Embarazo creado correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error: any) {
      message.error(error.message || 'Error al guardar embarazo');
    }
  };

  const handleViewDetails = (embarazo: Embarazo) => {
    setSelectedEmbarazo(embarazo);
    setDrawerVisible(true);
  };

  const columns = [
    {
      title: 'Paciente',
      key: 'paciente',
      render: (_: any, record: Embarazo) => record.paciente_nombre || 'Sin nombre',
      filteredValue: [searchText],
      onFilter: (value: any, record: Embarazo) => {
        const search = value.toLowerCase();
        return (record.paciente_nombre || '').toLowerCase().includes(search);
      },
    },
    {
      title: 'FUR',
      dataIndex: 'fur',
      key: 'fur',
      render: (fur: string) => new Date(fur).toLocaleDateString('es-ES'),
    },
    {
      title: 'FPP',
      dataIndex: 'fpp',
      key: 'fpp',
      render: (fpp: string) => new Date(fpp).toLocaleDateString('es-ES'),
    },
    {
      title: 'EG Actual',
      dataIndex: 'semanas_dias',
      key: 'eg',
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_: any, record: Embarazo) => (
        <Tag color={record.embarazo_multiple ? 'purple' : 'blue'}>
          {record.embarazo_multiple ? `Múltiple (${record.numero_fetos})` : 'Único'}
        </Tag>
      ),
    },
    {
      title: 'Riesgo',
      dataIndex: 'alto_riesgo',
      key: 'riesgo',
      render: (alto_riesgo: boolean) => (
        <Tag color={alto_riesgo ? 'red' : 'green'}>
          {alto_riesgo ? 'ALTO RIESGO' : 'NORMAL'}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors: Record<string, string> = {
          activo: 'green',
          finalizado: 'blue',
          perdida: 'red',
        };
        return <Tag color={colors[estado]}>{estado.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 200,
      render: (_: any, record: Embarazo) => (
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
          <Popconfirm
            title="¿Eliminar este embarazo?"
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

  const total = embarazos.length;
  const activos = embarazos.filter((e) => e.estado === 'activo').length;
  const altoRiesgo = embarazos.filter((e) => e.alto_riesgo).length;

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="Total Embarazos" value={total} prefix={<HeartOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="Activos" value={activos} prefix={<CheckCircleOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="Alto Riesgo" value={altoRiesgo} prefix={<WarningOutlined />} valueStyle={{ color: '#ff4d4f' }} />
          </Col>
          <Col span={6}>
            <Statistic title="Finalizados" value={total - activos} prefix={<CloseCircleOutlined />} />
          </Col>
        </Row>
      </Card>

      <Card
        title="Gestión de Embarazos"
        extra={
          <Space>
            <Input
              placeholder="Buscar..."
              prefix={<SearchOutlined />}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button icon={<ReloadOutlined />} onClick={loadData}>
              Actualizar
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              Nuevo Embarazo
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={embarazos}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* MODAL CREAR/EDITAR */}
      <Modal
        title={editingEmbarazo ? 'Editar Embarazo' : 'Nuevo Embarazo'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item
            name="paciente"
            label="Paciente"
            rules={[{ required: true, message: 'Seleccione una paciente' }]}
          >
            <Select
              showSearch
              placeholder="Seleccione una paciente"
              optionFilterProp="children"
              filterOption={(input, option: any) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {pacientes.map((p) => (
                <Option key={p.id} value={p.id}>
                  {p.nombre} {p.apellido} - {p.dni}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="fur"
                label="Fecha Última Regla (FUR)"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="fpp"
                label="Fecha Probable de Parto (FPP)"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="embarazo_multiple" label="¿Embarazo Múltiple?" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="numero_fetos" label="Número de Fetos">
                <InputNumber min={1} max={5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="alto_riesgo" label="¿Alto Riesgo?" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="estado" label="Estado">
                <Select>
                  <Option value="activo">Activo</Option>
                  <Option value="finalizado">Finalizado</Option>
                  <Option value="perdida">Pérdida</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="factores_riesgo" label="Factores de Riesgo">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
              <Button type="primary" htmlType="submit">
                {editingEmbarazo ? 'Actualizar' : 'Crear'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* DRAWER DETALLES */}
      <Drawer
        title="Detalles del Embarazo"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedEmbarazo && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="Paciente">{selectedEmbarazo.paciente_nombre}</Descriptions.Item>
            <Descriptions.Item label="FUR">
              {new Date(selectedEmbarazo.fur).toLocaleDateString('es-ES')}
            </Descriptions.Item>
            <Descriptions.Item label="FPP">
              {new Date(selectedEmbarazo.fpp).toLocaleDateString('es-ES')}
            </Descriptions.Item>
            <Descriptions.Item label="EG Actual">{selectedEmbarazo.semanas_dias}</Descriptions.Item>
            <Descriptions.Item label="Tipo de Embarazo">
              <Tag color={selectedEmbarazo.embarazo_multiple ? 'purple' : 'blue'}>
                {selectedEmbarazo.embarazo_multiple
                  ? `Múltiple (${selectedEmbarazo.numero_fetos} fetos)`
                  : 'Único'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Nivel de Riesgo">
              <Tag color={selectedEmbarazo.alto_riesgo ? 'red' : 'green'}>
                {selectedEmbarazo.alto_riesgo ? 'ALTO RIESGO' : 'NORMAL'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Factores de Riesgo">
              {selectedEmbarazo.factores_riesgo || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="Estado">
              <Tag>{selectedEmbarazo.estado.toUpperCase()}</Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  );
};

export default EmbarazosNew;
