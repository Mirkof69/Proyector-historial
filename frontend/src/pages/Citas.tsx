/**
 * =============================================================================
 * PÁGINA DE CITAS
 * =============================================================================
 * Gestión completa de citas médicas y agenda
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
  Card,
  Calendar,
  Badge,
  List,
  Divider,
  Alert,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckOutlined,
  CloseOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs, { Dayjs } from 'dayjs';
import citasService, { Cita } from '../services/citasService';
import pacientesService, { Paciente } from '../services/pacientesService';

const { Option } = Select;
const { TextArea } = Input;

const Citas: React.FC = () => {
  const [data, setData] = useState<Cita[]>([]);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [calendarVisible, setCalendarVisible] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<Cita | null>(null);
  const [selectedDate, setSelectedDate] = useState<Dayjs>(dayjs());
  const [citasDelDia, setCitasDelDia] = useState<Cita[]>([]);
  const [form] = Form.useForm();

  // Filtros
  const [filters, setFilters] = useState({
    paciente: undefined as number | undefined,
    estado: undefined as string | undefined,
    tipo_cita: undefined as string | undefined,
    fecha_desde: undefined as string | undefined,
    fecha_hasta: undefined as string | undefined,
  });

  useEffect(() => {
    fetchData();
    fetchPacientes();
  }, [filters]);

  useEffect(() => {
    if (calendarVisible) {
      fetchCitasDelDia(selectedDate);
    }
  }, [selectedDate, calendarVisible]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await citasService.getAll(filters);
      setData(response);
    } catch (error) {
      message.error('Error al cargar citas');
    } finally {
      setLoading(false);
    }
  };

  const fetchPacientes = async () => {
    try {
      const response = await pacientesService.getAll({ activo: true });
      setPacientes(response);
    } catch (error) {
      message.error('Error al cargar pacientes');
    }
  };

  const fetchCitasDelDia = async (fecha: Dayjs) => {
    try {
      const response = await citasService.getByFecha(fecha.format('YYYY-MM-DD'));
      setCitasDelDia(response);
    } catch (error) {
      message.error('Error al cargar citas del día');
    }
  };

  const handleCreate = () => {
    setEditingId(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: Cita) => {
    setEditingId(record.id);
    const fechaHora = dayjs(record.fecha_hora);
    form.setFieldsValue({
      ...record,
      fecha_cita: fechaHora,
      hora_cita: fechaHora,
    });
    setModalVisible(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '¿Confirmar eliminación?',
      content: '¿Está seguro que desea eliminar esta cita?',
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await citasService.delete(id);
          message.success('Cita eliminada correctamente');
          fetchData();
        } catch (error) {
          message.error('Error al eliminar cita');
        }
      },
    });
  };

  const handleView = (record: Cita) => {
    setSelectedRecord(record);
    setDrawerVisible(true);
  };

  const handleConfirmar = async (id: number) => {
    try {
      await citasService.confirmar(id);
      message.success('Cita confirmada correctamente');
      fetchData();
    } catch (error) {
      message.error('Error al confirmar cita');
    }
  };

  const handleCancelar = (id: number) => {
    Modal.confirm({
      title: '¿Cancelar cita?',
      content: (
        <Form.Item label="Motivo de cancelación" name="motivo_cancelacion">
          <TextArea rows={3} placeholder="Ingrese el motivo de la cancelación" />
        </Form.Item>
      ),
      okText: 'Cancelar Cita',
      okType: 'danger',
      cancelText: 'Volver',
      onOk: async () => {
        try {
          const motivo = form.getFieldValue('motivo_cancelacion');
          await citasService.cancelar(id, motivo);
          message.success('Cita cancelada correctamente');
          fetchData();
        } catch (error) {
          message.error('Error al cancelar cita');
        }
      },
    });
  };

  const handleSubmit = async (values: any) => {
    try {
      // Combinar fecha y hora en fecha_hora
      const fechaStr = values.fecha_cita.format('YYYY-MM-DD');
      const horaStr = values.hora_cita.format('HH:mm:ss');
      const fecha_hora = `${fechaStr}T${horaStr}`;

      const formData = {
        ...values,
        fecha_hora,
      };

      // Eliminar campos temporales del formulario
      delete formData.fecha_cita;
      delete formData.hora_cita;

      if (editingId) {
        await citasService.update(editingId, formData);
        message.success('Cita actualizada correctamente');
      } else {
        await citasService.create(formData);
        message.success('Cita registrada correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      fetchData();
    } catch (error) {
      message.error('Error al guardar cita');
    }
  };

  const getListData = (value: Dayjs) => {
    const fechaStr = value.format('YYYY-MM-DD');
    const citasDelDia = data.filter((cita) => dayjs(cita.fecha_hora).format('YYYY-MM-DD') === fechaStr);
    return citasDelDia.map((cita) => ({
      type: cita.estado === 'confirmada' ? 'success' : cita.estado === 'cancelada' ? 'error' : 'warning',
      content: `${dayjs(cita.fecha_hora).format('HH:mm')} - ${cita.paciente_nombre}`,
    }));
  };

  const dateCellRender = (value: Dayjs) => {
    const listData = getListData(value);
    return (
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {listData.map((item, index) => (
          <li key={index}>
            <Badge status={item.type as any} text={item.content} />
          </li>
        ))}
      </ul>
    );
  };

  const columns: ColumnsType<Cita> = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_hora',
      key: 'fecha_hora',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
      sorter: (a, b) => dayjs(a.fecha_hora).unix() - dayjs(b.fecha_hora).unix(),
    },
    {
      title: 'Hora',
      dataIndex: 'fecha_hora',
      key: 'hora',
      render: (fecha_hora: string) => dayjs(fecha_hora).format('HH:mm'),
      sorter: (a, b) => dayjs(a.fecha_hora).unix() - dayjs(b.fecha_hora).unix(),
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
    },
    {
      title: 'Tipo de Cita',
      dataIndex: 'tipo_cita',
      key: 'tipo_cita',
      render: (tipo: string) => {
        const tipos: Record<string, string> = {
          control_prenatal: 'Control Prenatal',
          ecografia: 'Ecografía',
          laboratorio: 'Laboratorio',
          urgencia: 'Urgencia',
          consulta: 'Consulta',
          otro: 'Otro',
        };
        return tipos[tipo] || tipo;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors: Record<string, string> = {
          pendiente: 'orange',
          confirmada: 'green',
          cancelada: 'red',
          completada: 'blue',
        };
        const labels: Record<string, string> = {
          pendiente: 'Pendiente',
          confirmada: 'Confirmada',
          cancelada: 'Cancelada',
          completada: 'Completada',
        };
        return <Tag color={colors[estado]}>{labels[estado]}</Tag>;
      },
    },
    {
      title: 'Médico',
      dataIndex: 'medico_nombre',
      key: 'medico_nombre',
      render: (medico: string) => medico || '-',
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (record: Cita) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => handleView(record)} />
          {record.estado === 'pendiente' && (
            <>
              <Button
                type="link"
                icon={<CheckOutlined />}
                onClick={() => handleConfirmar(record.id)}
                style={{ color: 'green' }}
                title="Confirmar"
              />
              <Button
                type="link"
                icon={<CloseOutlined />}
                onClick={() => handleCancelar(record.id)}
                style={{ color: 'red' }}
                title="Cancelar"
              />
            </>
          )}
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
        <h1>Gestión de Citas</h1>
        <Space>
          <Button
            icon={<CalendarOutlined />}
            onClick={() => setCalendarVisible(!calendarVisible)}
          >
            {calendarVisible ? 'Ver Lista' : 'Ver Calendario'}
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Nueva Cita
          </Button>
        </Space>
      </div>

      {/* Filtros */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={6}>
            <Select
              placeholder="Filtrar por paciente"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, paciente: value })}
              showSearch
              optionFilterProp="children"
            >
              {pacientes.map((pac) => (
                <Option key={pac.id} value={pac.id}>
                  {`${pac.nombre} ${pac.apellido}`}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <Select
              placeholder="Filtrar por estado"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, estado: value })}
            >
              <Option value="pendiente">Pendiente</Option>
              <Option value="confirmada">Confirmada</Option>
              <Option value="cancelada">Cancelada</Option>
              <Option value="completada">Completada</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Select
              placeholder="Filtrar por tipo"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, tipo_cita: value })}
            >
              <Option value="control_prenatal">Control Prenatal</Option>
              <Option value="ecografia">Ecografía</Option>
              <Option value="laboratorio">Laboratorio</Option>
              <Option value="urgencia">Urgencia</Option>
              <Option value="consulta">Consulta</Option>
              <Option value="otro">Otro</Option>
            </Select>
          </Col>
          <Col span={6}>
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

      {/* Vista de Calendario o Tabla */}
      {calendarVisible ? (
        <Row gutter={16}>
          <Col span={18}>
            <Card>
              <Calendar
                dateCellRender={dateCellRender}
                onSelect={(date) => {
                  setSelectedDate(date);
                  fetchCitasDelDia(date);
                }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card title={`Citas del ${selectedDate.format('DD/MM/YYYY')}`}>
              <List
                dataSource={citasDelDia}
                renderItem={(cita) => (
                  <List.Item>
                    <List.Item.Meta
                      title={
                        <Space>
                          <ClockCircleOutlined />
                          {dayjs(cita.fecha_hora).format('HH:mm')}
                        </Space>
                      }
                      description={
                        <>
                          <div>{cita.paciente_nombre}</div>
                          <Tag
                            color={
                              cita.estado === 'confirmada'
                                ? 'green'
                                : cita.estado === 'cancelada'
                                ? 'red'
                                : 'orange'
                            }
                            style={{ marginTop: '4px' }}
                          >
                            {cita.estado}
                          </Tag>
                        </>
                      }
                    />
                  </List.Item>
                )}
              />
            </Card>
          </Col>
        </Row>
      ) : (
        <Table
          columns={columns}
          dataSource={data}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      )}

      {/* Modal de Creación/Edición */}
      <Modal
        title={editingId ? 'Editar Cita' : 'Nueva Cita'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="paciente"
                label="Paciente"
                rules={[{ required: true, message: 'Seleccione un paciente' }]}
              >
                <Select
                  placeholder="Seleccione paciente"
                  showSearch
                  optionFilterProp="children"
                >
                  {pacientes.map((pac) => (
                    <Option key={pac.id} value={pac.id}>
                      {`${pac.nombre} ${pac.apellido} - DNI: ${pac.dni}`}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="fecha_cita"
                label="Fecha de Cita"
                rules={[{ required: true, message: 'Ingrese fecha de cita' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="hora_cita"
                label="Hora de Cita"
                rules={[{ required: true, message: 'Ingrese hora de cita' }]}
              >
                <TimePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="duracion_minutos" label="Duración (minutos)">
                <Select placeholder="Seleccione duración">
                  <Option value={15}>15 minutos</Option>
                  <Option value={30}>30 minutos</Option>
                  <Option value={45}>45 minutos</Option>
                  <Option value={60}>1 hora</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="tipo_cita"
                label="Tipo de Cita"
                rules={[{ required: true, message: 'Seleccione tipo de cita' }]}
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="control_prenatal">Control Prenatal</Option>
                  <Option value="ecografia">Ecografía</Option>
                  <Option value="laboratorio">Laboratorio</Option>
                  <Option value="urgencia">Urgencia</Option>
                  <Option value="consulta">Consulta</Option>
                  <Option value="otro">Otro</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="estado"
                label="Estado"
                rules={[{ required: true, message: 'Seleccione estado' }]}
              >
                <Select placeholder="Seleccione estado">
                  <Option value="pendiente">Pendiente</Option>
                  <Option value="confirmada">Confirmada</Option>
                  <Option value="cancelada">Cancelada</Option>
                  <Option value="completada">Completada</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="motivo" label="Motivo de la Cita">
                <TextArea rows={3} placeholder="Describa el motivo de la cita" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="observaciones" label="Observaciones">
                <TextArea rows={2} placeholder="Observaciones adicionales" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="recordatorio_enviado" label="¿Enviar recordatorio?" valuePropName="checked">
                <Select placeholder="Enviar recordatorio">
                  <Option value={true}>Sí</Option>
                  <Option value={false}>No</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="sala" label="Sala/Consultorio">
                <Input placeholder="Número de sala o consultorio" />
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
        title="Detalles de la Cita"
        placement="right"
        width={640}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedRecord && (
          <>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Paciente">
                {selectedRecord.paciente_nombre}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha">
                {dayjs(selectedRecord.fecha_hora).format('DD/MM/YYYY')}
              </Descriptions.Item>
              <Descriptions.Item label="Hora">
                {dayjs(selectedRecord.fecha_hora).format('HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="Tipo de Cita">
                {selectedRecord.tipo_cita}
              </Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag
                  color={
                    selectedRecord.estado === 'confirmada'
                      ? 'green'
                      : selectedRecord.estado === 'cancelada'
                      ? 'red'
                      : selectedRecord.estado === 'completada'
                      ? 'blue'
                      : 'orange'
                  }
                >
                  {selectedRecord.estado}
                </Tag>
              </Descriptions.Item>
              {selectedRecord.duracion_minutos && (
                <Descriptions.Item label="Duración Estimada">
                  {selectedRecord.duracion_minutos} minutos
                </Descriptions.Item>
              )}
              {selectedRecord.medico_nombre && (
                <Descriptions.Item label="Médico">
                  {selectedRecord.medico_nombre}
                </Descriptions.Item>
              )}
              {selectedRecord.sala && (
                <Descriptions.Item label="Sala/Consultorio">
                  {selectedRecord.sala}
                </Descriptions.Item>
              )}
              {selectedRecord.motivo && (
                <Descriptions.Item label="Motivo">{selectedRecord.motivo}</Descriptions.Item>
              )}
              {selectedRecord.observaciones && (
                <Descriptions.Item label="Observaciones">
                  {selectedRecord.observaciones}
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedRecord.estado === 'pendiente' && (
              <>
                <Divider />
                <Space>
                  <Button
                    type="primary"
                    icon={<CheckOutlined />}
                    onClick={() => {
                      handleConfirmar(selectedRecord.id);
                      setDrawerVisible(false);
                    }}
                  >
                    Confirmar Cita
                  </Button>
                  <Button
                    danger
                    icon={<CloseOutlined />}
                    onClick={() => {
                      handleCancelar(selectedRecord.id);
                      setDrawerVisible(false);
                    }}
                  >
                    Cancelar Cita
                  </Button>
                </Space>
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
};

export default Citas;
