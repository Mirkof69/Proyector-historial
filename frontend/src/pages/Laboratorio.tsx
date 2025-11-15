/**
 * =============================================================================
 * PÁGINA DE LABORATORIO
 * =============================================================================
 * Gestión completa de exámenes de laboratorio
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
  Space,
  message,
  Drawer,
  Descriptions,
  Tag,
  Upload,
  Row,
  Col,
  InputNumber,
  Card,
  Divider,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UploadOutlined,
  DownloadOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import laboratorioService, { ExamenLaboratorio } from '../services/laboratorioService';
import embarazosService, { Embarazo } from '../services/embarazosService';

const { Option } = Select;
const { TextArea } = Input;

const Laboratorio: React.FC = () => {
  const [data, setData] = useState<ExamenLaboratorio[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<ExamenLaboratorio | null>(null);
  const [fileList, setFileList] = useState<any[]>([]);
  const [form] = Form.useForm();

  // Filtros
  const [filters, setFilters] = useState({
    embarazo: undefined as number | undefined,
    tipo_examen: undefined as string | undefined,
    estado: undefined as string | undefined,
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
      const response = await laboratorioService.getAll(filters);
      setData(response);
    } catch (error) {
      message.error('Error al cargar exámenes de laboratorio');
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
    setFileList([]);
    setModalVisible(true);
  };

  const handleEdit = (record: ExamenLaboratorio) => {
    setEditingId(record.id);
    form.setFieldsValue({
      ...record,
      fecha_solicitud: dayjs(record.fecha_solicitud),
      fecha_resultado: record.fecha_resultado ? dayjs(record.fecha_resultado) : null,
    });
    setFileList([]);
    setModalVisible(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '¿Confirmar eliminación?',
      content: '¿Está seguro que desea eliminar este examen de laboratorio?',
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await laboratorioService.delete(id);
          message.success('Examen eliminado correctamente');
          fetchData();
        } catch (error) {
          message.error('Error al eliminar examen');
        }
      },
    });
  };

  const handleView = (record: ExamenLaboratorio) => {
    setSelectedRecord(record);
    setDrawerVisible(true);
  };

  const handleSubmit = async (values: any) => {
    try {
      const formData: any = {
        ...values,
        fecha_solicitud: values.fecha_solicitud.format('YYYY-MM-DD'),
        fecha_resultado: values.fecha_resultado ? values.fecha_resultado.format('YYYY-MM-DD') : null,
      };

      if (fileList.length > 0 && fileList[0].originFileObj) {
        formData.archivo_resultado = fileList[0].originFileObj;
      }

      if (editingId) {
        await laboratorioService.update(editingId, formData);
        message.success('Examen actualizado correctamente');
      } else {
        await laboratorioService.create(formData);
        message.success('Examen registrado correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      setFileList([]);
      fetchData();
    } catch (error) {
      message.error('Error al guardar examen');
    }
  };

  const handleDownloadFile = async (record: ExamenLaboratorio) => {
    try {
      const blob = await laboratorioService.downloadResultado(record.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `examen_${record.id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('Archivo descargado correctamente');
    } catch (error) {
      message.error('Error al descargar archivo');
    }
  };

  const columns: ColumnsType<ExamenLaboratorio> = [
    {
      title: 'Fecha Solicitud',
      dataIndex: 'fecha_solicitud',
      key: 'fecha_solicitud',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
      sorter: (a, b) => dayjs(a.fecha_solicitud).unix() - dayjs(b.fecha_solicitud).unix(),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_examen',
      key: 'tipo_examen',
      render: (tipo: string) => {
        const tipos: Record<string, string> = {
          hematologia: 'Hematología',
          quimica: 'Química',
          serologia: 'Serología',
          orina: 'Orina',
          cultivo: 'Cultivo',
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
          completado: 'green',
        };
        const labels: Record<string, string> = {
          pendiente: 'Pendiente',
          completado: 'Completado',
        };
        return <Tag color={colors[estado]}>{labels[estado]}</Tag>;
      },
    },
    {
      title: 'Hemoglobina',
      dataIndex: 'hemoglobina',
      key: 'hemoglobina',
      render: (value: number) => (value ? `${value} g/dL` : '-'),
    },
    {
      title: 'Glucosa',
      dataIndex: 'glucosa',
      key: 'glucosa',
      render: (value: number) => (value ? `${value} mg/dL` : '-'),
    },
    {
      title: 'Grupo/Rh',
      key: 'sangre',
      render: (record: ExamenLaboratorio) => {
        if (record.grupo_sanguineo && record.factor_rh) {
          return `${record.grupo_sanguineo} ${record.factor_rh}`;
        }
        return '-';
      },
    },
    {
      title: 'Archivo',
      key: 'archivo',
      render: (record: ExamenLaboratorio) =>
        record.archivo_resultado ? (
          <Button
            type="link"
            icon={<DownloadOutlined />}
            onClick={() => handleDownloadFile(record)}
          >
            Descargar
          </Button>
        ) : (
          '-'
        ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (record: ExamenLaboratorio) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record)}
          />
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
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
        <h1>Exámenes de Laboratorio</h1>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Nuevo Examen
        </Button>
      </div>

      {/* Filtros */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16}>
          <Col span={6}>
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
          <Col span={6}>
            <Select
              placeholder="Filtrar por tipo"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters({ ...filters, tipo_examen: value })}
            >
              <Option value="hematologia">Hematología</Option>
              <Option value="quimica">Química</Option>
              <Option value="serologia">Serología</Option>
              <Option value="orina">Orina</Option>
              <Option value="cultivo">Cultivo</Option>
              <Option value="otro">Otro</Option>
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
              <Option value="completado">Completado</Option>
            </Select>
          </Col>
          <Col span={6}>
            <DatePicker
              placeholder="Fecha desde"
              style={{ width: '100%' }}
              onChange={(date) =>
                setFilters({ ...filters, fecha_desde: date ? date.format('YYYY-MM-DD') : undefined })
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
        title={editingId ? 'Editar Examen' : 'Nuevo Examen'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        footer={null}
        width={1000}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Row gutter={16}>
            <Col span={12}>
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
            <Col span={6}>
              <Form.Item
                name="fecha_solicitud"
                label="Fecha Solicitud"
                rules={[{ required: true, message: 'Ingrese fecha de solicitud' }]}
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="fecha_resultado" label="Fecha Resultado">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="tipo_examen"
                label="Tipo de Examen"
                rules={[{ required: true, message: 'Seleccione tipo de examen' }]}
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="hematologia">Hematología</Option>
                  <Option value="quimica">Química</Option>
                  <Option value="serologia">Serología</Option>
                  <Option value="orina">Orina</Option>
                  <Option value="cultivo">Cultivo</Option>
                  <Option value="otro">Otro</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="estado"
                label="Estado"
                rules={[{ required: true, message: 'Seleccione estado' }]}
              >
                <Select placeholder="Seleccione estado">
                  <Option value="pendiente">Pendiente</Option>
                  <Option value="completado">Completado</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="laboratorio" label="Laboratorio">
                <Input placeholder="Nombre del laboratorio" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Hemograma</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="hemoglobina" label="Hemoglobina (g/dL)">
                <InputNumber min={0} max={20} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="hematocrito" label="Hematocrito (%)">
                <InputNumber min={0} max={100} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="leucocitos" label="Leucocitos (/mm³)">
                <InputNumber min={0} max={50000} step={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="plaquetas" label="Plaquetas (/mm³)">
                <InputNumber min={0} max={1000000} step={1000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Química Sanguínea</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="glucosa" label="Glucosa (mg/dL)">
                <InputNumber min={0} max={500} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="urea" label="Urea (mg/dL)">
                <InputNumber min={0} max={200} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="creatinina" label="Creatinina (mg/dL)">
                <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="acido_urico" label="Ácido Úrico (mg/dL)">
                <InputNumber min={0} max={20} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="proteinas_totales" label="Proteínas Totales (g/dL)">
                <InputNumber min={0} max={15} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="albumina" label="Albúmina (g/dL)">
                <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="globulina" label="Globulina (g/dL)">
                <InputNumber min={0} max={10} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="bilirrubina_total" label="Bilirrubina Total (mg/dL)">
                <InputNumber min={0} max={30} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="tgo" label="TGO (U/L)">
                <InputNumber min={0} max={1000} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="tgp" label="TGP (U/L)">
                <InputNumber min={0} max={1000} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="fosfatasa_alcalina" label="Fosfatasa Alcalina (U/L)">
                <InputNumber min={0} max={1000} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Grupo Sanguíneo y Serología</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="grupo_sanguineo" label="Grupo Sanguíneo">
                <Select placeholder="Seleccione grupo">
                  <Option value="A">A</Option>
                  <Option value="B">B</Option>
                  <Option value="AB">AB</Option>
                  <Option value="O">O</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="factor_rh" label="Factor Rh">
                <Select placeholder="Seleccione factor">
                  <Option value="positivo">Positivo</Option>
                  <Option value="negativo">Negativo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="vdrl" label="VDRL">
                <Select placeholder="Resultado VDRL">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="vih" label="VIH">
                <Select placeholder="Resultado VIH">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="hepatitis_b" label="Hepatitis B">
                <Select placeholder="Resultado HBsAg">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="toxoplasmosis_igg" label="Toxoplasmosis IgG">
                <Select placeholder="Resultado IgG">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="toxoplasmosis_igm" label="Toxoplasmosis IgM">
                <Select placeholder="Resultado IgM">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="rubeola_igg" label="Rubéola IgG">
                <Select placeholder="Resultado IgG">
                  <Option value="no_reactivo">No Reactivo</Option>
                  <Option value="reactivo">Reactivo</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Examen de Orina</Divider>
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="orina_color" label="Color">
                <Input placeholder="Color de la orina" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="orina_aspecto" label="Aspecto">
                <Input placeholder="Aspecto de la orina" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="orina_ph" label="pH">
                <InputNumber min={0} max={14} step={0.5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="orina_densidad" label="Densidad">
                <InputNumber min={1.000} max={1.050} step={0.001} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="orina_glucosa" label="Glucosa">
                <Select placeholder="Glucosa en orina">
                  <Option value="negativo">Negativo</Option>
                  <Option value="positivo">Positivo</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="orina_proteinas" label="Proteínas">
                <Select placeholder="Proteínas en orina">
                  <Option value="negativo">Negativo</Option>
                  <Option value="trazas">Trazas</Option>
                  <Option value="positivo_1">+ (Positivo 1)</Option>
                  <Option value="positivo_2">++ (Positivo 2)</Option>
                  <Option value="positivo_3">+++ (Positivo 3)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="orina_leucocitos" label="Leucocitos (/campo)">
                <InputNumber min={0} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="orina_hematies" label="Hematíes (/campo)">
                <InputNumber min={0} max={100} step={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="orina_celulas_epiteliales" label="Células Epiteliales">
                <Input placeholder="Células epiteliales" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="orina_bacterias" label="Bacterias">
                <Select placeholder="Presencia de bacterias">
                  <Option value="ausente">Ausente</Option>
                  <Option value="escaso">Escaso</Option>
                  <Option value="moderado">Moderado</Option>
                  <Option value="abundante">Abundante</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Cultivos</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="urocultivo" label="Urocultivo">
                <TextArea rows={2} placeholder="Resultado de urocultivo" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="antibiograma" label="Antibiograma">
                <TextArea rows={2} placeholder="Resultado de antibiograma" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Otros</Divider>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="observaciones" label="Observaciones">
                <TextArea rows={3} placeholder="Observaciones adicionales" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="archivo_resultado" label="Archivo de Resultado">
                <Upload
                  maxCount={1}
                  fileList={fileList}
                  beforeUpload={(file) => {
                    setFileList([file]);
                    return false;
                  }}
                  onRemove={() => setFileList([])}
                >
                  <Button icon={<UploadOutlined />}>Subir Archivo (PDF/Imagen)</Button>
                </Upload>
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
        title="Detalles del Examen"
        placement="right"
        width={720}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedRecord && (
          <>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="Fecha Solicitud" span={1}>
                {dayjs(selectedRecord.fecha_solicitud).format('DD/MM/YYYY')}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha Resultado" span={1}>
                {selectedRecord.fecha_resultado
                  ? dayjs(selectedRecord.fecha_resultado).format('DD/MM/YYYY')
                  : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Tipo" span={1}>
                {selectedRecord.tipo_examen}
              </Descriptions.Item>
              <Descriptions.Item label="Estado" span={1}>
                <Tag color={selectedRecord.estado === 'completado' ? 'green' : 'orange'}>
                  {selectedRecord.estado === 'completado' ? 'Completado' : 'Pendiente'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Laboratorio" span={2}>
                {selectedRecord.laboratorio || '-'}
              </Descriptions.Item>
            </Descriptions>

            {/* Hemograma */}
            {(selectedRecord.hemoglobina || selectedRecord.hematocrito) && (
              <>
                <Divider>Hemograma</Divider>
                <Descriptions bordered column={2} size="small">
                  {selectedRecord.hemoglobina && (
                    <Descriptions.Item label="Hemoglobina">
                      {selectedRecord.hemoglobina} g/dL
                    </Descriptions.Item>
                  )}
                  {selectedRecord.hematocrito && (
                    <Descriptions.Item label="Hematocrito">
                      {selectedRecord.hematocrito}%
                    </Descriptions.Item>
                  )}
                  {selectedRecord.leucocitos && (
                    <Descriptions.Item label="Leucocitos">
                      {selectedRecord.leucocitos} /mm³
                    </Descriptions.Item>
                  )}
                  {selectedRecord.plaquetas && (
                    <Descriptions.Item label="Plaquetas">
                      {selectedRecord.plaquetas} /mm³
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </>
            )}

            {/* Química */}
            {(selectedRecord.glucosa || selectedRecord.urea || selectedRecord.creatinina) && (
              <>
                <Divider>Química Sanguínea</Divider>
                <Descriptions bordered column={2} size="small">
                  {selectedRecord.glucosa && (
                    <Descriptions.Item label="Glucosa">
                      {selectedRecord.glucosa} mg/dL
                    </Descriptions.Item>
                  )}
                  {selectedRecord.urea && (
                    <Descriptions.Item label="Urea">
                      {selectedRecord.urea} mg/dL
                    </Descriptions.Item>
                  )}
                  {selectedRecord.creatinina && (
                    <Descriptions.Item label="Creatinina">
                      {selectedRecord.creatinina} mg/dL
                    </Descriptions.Item>
                  )}
                  {selectedRecord.acido_urico && (
                    <Descriptions.Item label="Ácido Úrico">
                      {selectedRecord.acido_urico} mg/dL
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </>
            )}

            {/* Grupo Sanguíneo */}
            {(selectedRecord.grupo_sanguineo || selectedRecord.vdrl || selectedRecord.vih) && (
              <>
                <Divider>Grupo Sanguíneo y Serología</Divider>
                <Descriptions bordered column={2} size="small">
                  {selectedRecord.grupo_sanguineo && (
                    <Descriptions.Item label="Grupo Sanguíneo">
                      {selectedRecord.grupo_sanguineo}
                    </Descriptions.Item>
                  )}
                  {selectedRecord.factor_rh && (
                    <Descriptions.Item label="Factor Rh">
                      {selectedRecord.factor_rh}
                    </Descriptions.Item>
                  )}
                  {selectedRecord.vdrl && (
                    <Descriptions.Item label="VDRL">{selectedRecord.vdrl}</Descriptions.Item>
                  )}
                  {selectedRecord.vih && (
                    <Descriptions.Item label="VIH">{selectedRecord.vih}</Descriptions.Item>
                  )}
                  {selectedRecord.hepatitis_b && (
                    <Descriptions.Item label="Hepatitis B">
                      {selectedRecord.hepatitis_b}
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </>
            )}

            {selectedRecord.observaciones && (
              <>
                <Divider>Observaciones</Divider>
                <p>{selectedRecord.observaciones}</p>
              </>
            )}

            {selectedRecord.archivo_resultado && (
              <>
                <Divider>Archivo</Divider>
                <Button
                  type="primary"
                  icon={<FileTextOutlined />}
                  onClick={() => handleDownloadFile(selectedRecord)}
                >
                  Descargar Archivo de Resultado
                </Button>
              </>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
};

export default Laboratorio;
