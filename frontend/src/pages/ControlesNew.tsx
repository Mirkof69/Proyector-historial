/**
 * =============================================================================
 * CRUD COMPLETO DE CONTROLES PRENATALES CON ALERTAS
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Modal, Form, Input, Select, Space, message, Tag, Popconfirm,
  Card, Row, Col, Statistic, Drawer, Descriptions, Badge, DatePicker, InputNumber,
  Alert as AntAlert,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, MedicineBoxOutlined,
  WarningOutlined, ReloadOutlined, HeartOutlined, EyeOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { controlesService } from '../services/controlesService';
import { embarazosService } from '../services/embarazosService';
import type { ControlPrenatal, Embarazo, Alert } from '../types';

const { Option } = Select;
const { TextArea } = Input;

const ControlesNew: React.FC = () => {
  const [controles, setControles] = useState<ControlPrenatal[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingControl, setEditingControl] = useState<ControlPrenatal | null>(null);
  const [selectedControl, setSelectedControl] = useState<ControlPrenatal | null>(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [controlesRes, embarazosRes] = await Promise.all([
        controlesService.list(),
        embarazosService.listActivos(),
      ]);
      setControles(controlesRes.results || controlesRes);
      setEmbarazos(embarazosRes);
    } catch (error: any) {
      message.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingControl(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (control: ControlPrenatal) => {
    setEditingControl(control);
    form.setFieldsValue({
      ...control,
      fecha_control: dayjs(control.fecha_control),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await controlesService.delete(id);
      message.success('Control eliminado correctamente');
      loadData();
    } catch (error: any) {
      message.error('Error al eliminar control');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        fecha_control: values.fecha_control.format('YYYY-MM-DD'),
      };

      if (editingControl) {
        await controlesService.update(editingControl.id, data);
        message.success('Control actualizado correctamente');
      } else {
        await controlesService.create(data);
        message.success('Control creado correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error: any) {
      message.error(error.message || 'Error al guardar control');
    }
  };

  const handleViewDetails = (control: ControlPrenatal) => {
    setSelectedControl(control);
    setDrawerVisible(true);
  };

  const getSeverityColor = (severidad?: string) => {
    const colors: Record<string, string> = {
      critica: 'error',
      alta: 'warning',
      moderada: 'processing',
      leve: 'default',
    };
    return colors[severidad || ''] || 'default';
  };

  const columns = [
    {
      title: 'N° Control',
      dataIndex: 'numero_control',
      key: 'numero_control',
      width: 100,
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      render: (fecha: string) => new Date(fecha).toLocaleDateString('es-ES'),
    },
    {
      title: 'EG',
      key: 'eg',
      render: (_: any, record: ControlPrenatal) => `${record.eg_semanas}s ${record.eg_dias}d`,
    },
    {
      title: 'Peso (kg)',
      dataIndex: 'peso',
      key: 'peso',
    },
    {
      title: 'PA',
      key: 'pa',
      render: (_: any, record: ControlPrenatal) =>
        `${record.presion_arterial_sistolica}/${record.presion_arterial_diastolica}`,
    },
    {
      title: 'FCF',
      dataIndex: 'fcf',
      key: 'fcf',
      render: (fcf?: number) => (fcf ? `${fcf} lpm` : '-'),
    },
    {
      title: 'Alertas',
      dataIndex: 'alertas',
      key: 'alertas',
      render: (alertas?: Alert[]) => {
        if (!alertas || alertas.length === 0) {
          return <Tag color="green">Sin alertas</Tag>;
        }
        const maxSeveridad = alertas.reduce((max, a) => {
          const severidades = ['leve', 'moderada', 'alta', 'critica'];
          return severidades.indexOf(a.severidad) > severidades.indexOf(max.severidad) ? a : max;
        }, alertas[0]);
        return (
          <Badge count={alertas.length}>
            <Tag color={getSeverityColor(maxSeveridad.severidad)}>
              {maxSeveridad.severidad.toUpperCase()}
            </Tag>
          </Badge>
        );
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 200,
      render: (_: any, record: ControlPrenatal) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
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
            title="¿Eliminar este control?"
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

  const total = controles.length;
  const conAlertas = controles.filter((c) => c.alertas && c.alertas.length > 0).length;

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic title="Total Controles" value={total} prefix={<MedicineBoxOutlined />} />
          </Col>
          <Col span={8}>
            <Statistic title="Con Alertas" value={conAlertas} prefix={<WarningOutlined />} valueStyle={{ color: '#ff4d4f' }} />
          </Col>
          <Col span={8}>
            <Statistic title="Sin Alertas" value={total - conAlertas} prefix={<HeartOutlined />} valueStyle={{ color: '#52c41a' }} />
          </Col>
        </Row>
      </Card>

      <Card
        title="Gestión de Controles Prenatales"
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={loadData}>
              Actualizar
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
              Nuevo Control
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={controles}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* MODAL CREAR/EDITAR */}
      <Modal
        title={editingControl ? 'Editar Control' : 'Nuevo Control Prenatal'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="embarazo"
                label="Embarazo"
                rules={[{ required: true, message: 'Seleccione un embarazo' }]}
              >
                <Select placeholder="Seleccione un embarazo">
                  {embarazos.map((e) => (
                    <Option key={e.id} value={e.id}>
                      {e.paciente_nombre} - EG: {e.semanas_dias}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="fecha_control"
                label="Fecha del Control"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="eg_semanas"
                label="EG Semanas"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={0} max={42} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="eg_dias"
                label="EG Días"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={0} max={6} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="peso"
                label="Peso (kg)"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={30} max={200} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="presion_arterial_sistolica"
                label="PA Sistólica"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={60} max={250} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="presion_arterial_diastolica"
                label="PA Diastólica"
                rules={[{ required: true, message: 'Requerido' }]}
              >
                <InputNumber min={40} max={150} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="frecuencia_cardiaca" label="FC Materna">
                <InputNumber min={40} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="fcf" label="FCF (lpm)">
                <InputNumber min={90} max={200} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="altura_uterina" label="Altura Uterina (cm)">
                <InputNumber min={0} max={50} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="observaciones" label="Observaciones">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
              <Button type="primary" htmlType="submit">
                {editingControl ? 'Actualizar' : 'Crear'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* DRAWER DETALLES */}
      <Drawer
        title="Detalles del Control Prenatal"
        placement="right"
        width={700}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedControl && (
          <>
            {selectedControl.alertas && selectedControl.alertas.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                {selectedControl.alertas.map((alerta, index) => (
                  <AntAlert
                    key={index}
                    type={getSeverityColor(alerta.severidad) as any}
                    message={alerta.mensaje}
                    description={alerta.accion}
                    showIcon
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </div>
            )}

            <Descriptions column={2} bordered>
              <Descriptions.Item label="N° Control" span={2}>
                {selectedControl.numero_control}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha">
                {new Date(selectedControl.fecha_control).toLocaleDateString('es-ES')}
              </Descriptions.Item>
              <Descriptions.Item label="EG">
                {selectedControl.eg_semanas}s {selectedControl.eg_dias}d
              </Descriptions.Item>
              <Descriptions.Item label="Peso">{selectedControl.peso} kg</Descriptions.Item>
              <Descriptions.Item label="Talla">{selectedControl.talla || '-'} cm</Descriptions.Item>
              <Descriptions.Item label="IMC">{selectedControl.imc || '-'}</Descriptions.Item>
              <Descriptions.Item label="PA">
                {selectedControl.presion_arterial_sistolica}/{selectedControl.presion_arterial_diastolica} mmHg
              </Descriptions.Item>
              <Descriptions.Item label="PAM">{selectedControl.pam || '-'}</Descriptions.Item>
              <Descriptions.Item label="FC Materna">{selectedControl.frecuencia_cardiaca || '-'} lpm</Descriptions.Item>
              <Descriptions.Item label="FCF">{selectedControl.fcf || '-'} lpm</Descriptions.Item>
              <Descriptions.Item label="Altura Uterina">{selectedControl.altura_uterina || '-'} cm</Descriptions.Item>
              <Descriptions.Item label="Presentación">{selectedControl.presentacion_fetal || '-'}</Descriptions.Item>
              <Descriptions.Item label="Mov. Fetales">
                {selectedControl.movimientos_fetales ? 'Sí' : 'No'}
              </Descriptions.Item>
              <Descriptions.Item label="Observaciones" span={2}>
                {selectedControl.observaciones || '-'}
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Drawer>
    </div>
  );
};

export default ControlesNew;
