/**
 * =============================================================================
 * PÁGINA DE PARTOS
 * =============================================================================
 * Gestión completa de registros de partos y nacimientos
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  TimePicker,
  Space,
  message,
  Drawer,
  Descriptions,
  Tag,
  Row,
  Col,
  InputNumber,
  Card,
  Divider,
  Checkbox,
  Alert,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  HeartOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import partosService, { Parto } from '../services/partosService';
import embarazosService, { Embarazo } from '../services/embarazosService';

const { Option } = Select;
const { TextArea } = Input;

const Partos: React.FC = () => {
  const [data, setData] = useState<Parto[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<Parto | null>(null);
  const [form] = Form.useForm();

  // Filtros
  const [filters, setFilters] = useState({
    embarazo: undefined as number | undefined,
    tipo_parto: undefined as string | undefined,
    fecha_desde: undefined as string | undefined,
    fecha_hasta: undefined as string | undefined,
  });

  useEffect(() => {
    fetchData();
    fetchEmbarazos();
  }, [filters]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await partosService.getAll(filters);
      setData(response);
    } catch (error) {
      message.error('Error al cargar registros de partos');
    } finally {
      setLoading(false);
    }
  };

  const fetchEmbarazos = async () => {
    try {
      const response = await embarazosService.getAll({ activo: true });
      setEmbarazos(response);
    } catch (error) {
      message.error('Error al cargar embarazos');
    }
  };

  const handleCreate = () => {
    setEditingId(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: Parto) => {
    setEditingId(record.id);
    const fechaHora = dayjs(record.fecha_hora_parto);
    form.setFieldsValue({
      ...record,
      fecha_parto: fechaHora,
      hora_parto: fechaHora,
    });
    setModalVisible(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '¿Confirmar eliminación?',
      content: '¿Está seguro que desea eliminar este registro de parto?',
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await partosService.delete(id);
          message.success('Registro de parto eliminado correctamente');
          fetchData();
        } catch (error) {
          message.error('Error al eliminar registro');
        }
      },
    });
  };

  const handleView = (record: Parto) => {
    setSelectedRecord(record);
    setDrawerVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const fechaParto = values.fecha_parto;
      const horaParto = values.hora_parto;

      const fechaHoraCombinada = fechaParto
        .hour(horaParto.hour())
        .minute(horaParto.minute())
        .second(0);

      const formData = {
        ...values,
        fecha_hora_parto: fechaHoraCombinada.format('YYYY-MM-DDTHH:mm:ss'),
      };

      delete formData.fecha_parto;
      delete formData.hora_parto;

      if (editingId) {
        await partosService.update(editingId, formData);
        message.success('Registro de parto actualizado correctamente');
      } else {
        await partosService.create(formData);
        message.success('Registro de parto guardado correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error('Error al guardar registro de parto');
    }
  };

  const getApgarColor = (apgar?: number) => {
    if (!apgar) return 'default';
    if (apgar >= 7) return 'green';
    if (apgar >= 4) return 'orange';
    return 'red';
  };

  const columns: ColumnsType<Parto> = [
    {
      title: 'Fecha y Hora',
      dataIndex: 'fecha_hora_parto',
      key: 'fecha_hora_parto',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm'),
      sorter: (a, b) => dayjs(a.fecha_hora_parto).unix() - dayjs(b.fecha_hora_parto).unix(),
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
    },
    {
      title: 'Tipo de Parto',
      dataIndex: 'tipo_parto',
      key: 'tipo_parto',
      render: (tipo: string) => {
        const tipos: Record<string, { label: string; color: string }> = {
          vaginal: { label: 'Vaginal', color: 'blue' },
          cesarea: { label: 'Cesárea', color: 'purple' },
          forceps: { label: 'Fórceps', color: 'orange' },
          ventosa: { label: 'Ventosa', color: 'orange' },
        };
        const tipo_info = tipos[tipo] || { label: tipo, color: 'default' };
        return <Tag color={tipo_info.color}>{tipo_info.label}</Tag>;
      },
    },
    {
      title: 'APGAR 1 min',
      dataIndex: 'apgar_1_min',
      key: 'apgar_1_min',
      render: (apgar: number) =>
        apgar ? <Tag color={getApgarColor(apgar)}>{apgar}</Tag> : '-',
    },
    {
      title: 'APGAR 5 min',
      dataIndex: 'apgar_5_min',
      key: 'apgar_5_min',
      render: (apgar: number) =>
        apgar ? <Tag color={getApgarColor(apgar)}>{apgar}</Tag> : '-',
    },
    {
      title: 'Peso RN (g)',
      dataIndex: 'peso_rn_gramos',
      key: 'peso_rn_gramos',
      render: (peso: number) => (peso ? `${peso} g` : '-'),
    },
    {
      title: 'Sexo RN',
      dataIndex: 'sexo_rn',
      key: 'sexo_rn',
      render: (sexo: string) => {
        const sexos: Record<string, { label: string; color: string }> = {
          masculino: { label: 'M', color: 'blue' },
          femenino: { label: 'F', color: 'pink' },
        };
        const sexo_info = sexos[sexo] || { label: '-', color: 'default' };
        return <Tag color={sexo_info.color}>{sexo_info.label}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (record: Parto) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleView(record)} />
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <h1>Registros de Partos</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Nuevo Registro de Parto
        </Button>
      </div>

      {/* Filtros */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Select
              placeholder="Filtrar por embarazo"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, embarazo: value })}
            >
              {embarazos.map((emb) => (
                <Option key={emb.id} value={emb.id}>
                  {`${emb.paciente_nombre} ${emb.paciente_apellido || ''} - FPP: ${dayjs(emb.fpp).format('DD/MM/YYYY')}`}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={8}>
            <Select
              placeholder="Filtrar por tipo de parto"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, tipo_parto: value })}
            >
              <Option value="vaginal">Vaginal</Option>
              <Option value="cesarea">Cesárea</Option>
              <Option value="forceps">Fórceps</Option>
              <Option value="ventosa">Ventosa</Option>
            </Select>
          </Col>
          <Col span={8}>
            <DatePicker
              placeholder="Fecha desde"
              style={{ width: '100%' }}
              onChange={(date) =>
                setFilters({
                  ...filters,
                  fecha_desde: date ? date.format('YYYY-MM-DD') : undefined,
                })
              }
            />
          </Col>
        </Row>
      </Card>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      {/* Modal de Creación/Edición */}
      <Modal
        title={editingId ? 'Editar Registro de Parto' : 'Nuevo Registro de Parto'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={1000}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="embarazo"
                label="Embarazo"
                rules={[{ required: true, message: 'Seleccione un embarazo' }]}
              >
                <Select placeholder="Seleccione embarazo">
                  {embarazos.map((emb) => (
                    <Option key={emb.id} value={emb.id}>
                      {`${emb.paciente_nombre} ${emb.paciente_apellido || ''} - FPP: ${dayjs(emb.fpp).format('DD/MM/YYYY')}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Datos del Parto</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="fecha_parto"
                label="Fecha del Parto"
                rules={[{ required: true, message: 'Ingrese fecha del parto' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="hora_parto"
                label="Hora del Parto"
                rules={[{ required: true, message: 'Ingrese hora del parto' }]}
              >
                <TimePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="tipo_parto"
                label="Tipo de Parto"
                rules={[{ required: true, message: 'Seleccione tipo de parto' }]}
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="vaginal">Vaginal</Option>
                  <Option value="cesarea">Cesárea</Option>
                  <Option value="forceps">Fórceps</Option>
                  <Option value="ventosa">Ventosa</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="presentacion" label="Presentación">
                <Select placeholder="Presentación fetal">
                  <Option value="cefalica">Cefálica</Option>
                  <Option value="podalica">Podálica</Option>
                  <Option value="transversa">Transversa</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="duracion_trabajo_parto_horas" label="Duración Trabajo Parto (horas)">
                <InputNumber min={0} max={72} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="edad_gestacional_parto_semanas" label="Edad Gestacional (semanas)">
                <InputNumber min={20} max={45} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Datos del Recién Nacido</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="apgar_1_min" label="APGAR 1 min">
                <InputNumber min={0} max={10} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="apgar_5_min" label="APGAR 5 min">
                <InputNumber min={0} max={10} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="peso_rn_gramos" label="Peso RN (gramos)">
                <InputNumber min={500} max={6000} step={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="talla_rn_cm" label="Talla RN (cm)">
                <InputNumber min={30} max={70} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="perimetro_cefalico_cm" label="Perímetro Cefálico (cm)">
                <InputNumber min={20} max={50} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="sexo_rn" label="Sexo RN">
                <Select placeholder="Sexo del recién nacido">
                  <Option value="masculino">Masculino</Option>
                  <Option value="femenino">Femenino</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="reanimacion_neonatal" label="Reanimación Neonatal" valuePropName="checked">
                <Checkbox>¿Requirió reanimación?</Checkbox>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Datos Adicionales</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="anestesia" label="Anestesia">
                <Select placeholder="Tipo de anestesia">
                  <Option value="ninguna">Ninguna</Option>
                  <Option value="local">Local</Option>
                  <Option value="epidural">Epidural</Option>
                  <Option value="raquidea">Raquídea</Option>
                  <Option value="general">General</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="episiotomia" label="Episiotomía" valuePropName="checked">
                <Checkbox>¿Se realizó episiotomía?</Checkbox>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="desgarros" label="Desgarros" valuePropName="checked">
                <Checkbox>¿Hubo desgarros?</Checkbox>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="alumbramiento" label="Alumbramiento">
                <Select placeholder="Tipo de alumbramiento">
                  <Option value="espontaneo">Espontáneo</Option>
                  <Option value="manual">Manual</Option>
                  <Option value="instrumental">Instrumental</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="anomalias_placenta" label="Anomalías Placenta">
                <Input placeholder="Describir anomalías si las hay" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Complicaciones</Divider>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="descripcion_complicaciones" label="Complicaciones">
                <TextArea
                  rows={2}
                  placeholder="Describir complicaciones si las hubo"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="observaciones" label="Observaciones">
                <TextArea rows={3} placeholder="Observaciones adicionales del parto" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="medico_atencion" label="Médico que Atendió">
                <Input placeholder="Nombre del médico" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="hospital" label="Hospital">
                <Input placeholder="Hospital, clínica, etc." />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingId ? 'Actualizar' : 'Registrar'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>Cancelar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Drawer de Detalles */}
      <Drawer
        title="Detalles del Parto"
        placement="right"
        width={720}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedRecord && (
          <>
            <Alert
              message={`Parto ${selectedRecord.tipo_parto}`}
              description={dayjs(selectedRecord.fecha_hora_parto).format('DD/MM/YYYY HH:mm')}
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />

            <Card title="Datos del Recién Nacido" style={{ marginBottom: '16px' }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="APGAR 1 min"
                    value={selectedRecord.apgar_1_min || '-'}
                    valueStyle={{
                      color: selectedRecord.apgar_1_min && selectedRecord.apgar_1_min >= 7 ? '#3f8600' : '#cf1322',
                    }}
                    prefix={<HeartOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="APGAR 5 min"
                    value={selectedRecord.apgar_5_min || '-'}
                    valueStyle={{
                      color: selectedRecord.apgar_5_min && selectedRecord.apgar_5_min >= 7 ? '#3f8600' : '#cf1322',
                    }}
                    prefix={<HeartOutlined />}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Peso (g)"
                    value={selectedRecord.peso_rn_gramos || '-'}
                    suffix="g"
                  />
                </Col>
              </Row>
            </Card>

            <Descriptions bordered column={2} size="small">
              <Descriptions.Item label="Tipo de Parto" span={2}>
                <Tag
                  color={
                    selectedRecord.tipo_parto === 'vaginal'
                      ? 'blue'
                      : selectedRecord.tipo_parto === 'cesarea'
                      ? 'purple'
                      : 'orange'
                  }
                >
                  {selectedRecord.tipo_parto}
                </Tag>
              </Descriptions.Item>

              {selectedRecord.presentacion && (
                <Descriptions.Item label="Presentación" span={1}>
                  {selectedRecord.presentacion}
                </Descriptions.Item>
              )}

              {selectedRecord.duracion_trabajo_parto_horas && (
                <Descriptions.Item label="Duración Trabajo Parto" span={1}>
                  {selectedRecord.duracion_trabajo_parto_horas} horas
                </Descriptions.Item>
              )}

              {selectedRecord.talla_rn_cm && (
                <Descriptions.Item label="Talla RN">{selectedRecord.talla_rn_cm} cm</Descriptions.Item>
              )}

              {selectedRecord.sexo_rn && (
                <Descriptions.Item label="Sexo RN">
                  <Tag color={selectedRecord.sexo_rn === 'masculino' ? 'blue' : 'pink'}>
                    {selectedRecord.sexo_rn}
                  </Tag>
                </Descriptions.Item>
              )}

              {selectedRecord.perimetro_cefalico_cm && (
                <Descriptions.Item label="Perímetro Cefálico">
                  {selectedRecord.perimetro_cefalico_cm} cm
                </Descriptions.Item>
              )}

              {selectedRecord.reanimacion_neonatal && (
                <Descriptions.Item label="Reanimación Neonatal" span={2}>
                  <Tag color="orange">Requirió Reanimación</Tag>
                </Descriptions.Item>
              )}

              {selectedRecord.anestesia && (
                <Descriptions.Item label="Anestesia" span={1}>
                  {selectedRecord.anestesia}
                </Descriptions.Item>
              )}

              {selectedRecord.alumbramiento && (
                <Descriptions.Item label="Alumbramiento" span={1}>
                  {selectedRecord.alumbramiento}
                </Descriptions.Item>
              )}

              {selectedRecord.episiotomia && (
                <Descriptions.Item label="Episiotomía" span={1}>
                  <Tag color="orange">Sí</Tag>
                </Descriptions.Item>
              )}

              {selectedRecord.desgarros && (
                <Descriptions.Item label="Desgarros" span={1}>
                  <Tag color="red">Sí</Tag>
                </Descriptions.Item>
              )}

              {selectedRecord.medico_nombre && (
                <Descriptions.Item label="Médico" span={1}>
                  {selectedRecord.medico_nombre}
                </Descriptions.Item>
              )}

              {selectedRecord.hospital && (
                <Descriptions.Item label="Hospital" span={2}>
                  {selectedRecord.hospital}
                </Descriptions.Item>
              )}

              {selectedRecord.descripcion_complicaciones && (
                <Descriptions.Item label="Complicaciones" span={2}>
                  <Alert message={selectedRecord.descripcion_complicaciones} type="warning" showIcon />
                </Descriptions.Item>
              )}

              {selectedRecord.observaciones && (
                <Descriptions.Item label="Observaciones" span={2}>
                  {selectedRecord.observaciones}
                </Descriptions.Item>
              )}
            </Descriptions>
          </>
        )}
      </Drawer>
    </div>
  );
};

export default Partos;
