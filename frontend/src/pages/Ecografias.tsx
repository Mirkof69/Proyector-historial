import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Input,
  Card,
  message,
  Modal,
  Form,
  DatePicker,
  Select,
  Row,
  Col,
  InputNumber,
  Switch,
  Upload,
  Image,
  Drawer,
  Descriptions,
  Divider,
  Statistic,
} from 'antd';
import {
  PlusOutlined,
  SearchOutlined,
  EditOutlined,
  EyeOutlined,
  DeleteOutlined,
  FileImageOutlined,
  DownloadOutlined,
  PrinterOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { ecografiasService, type Ecografia, type EcografiaForm } from '../services/ecografiasService';
import { embarazosService } from '../services/embarazosService';

const { Option } = Select;
const { TextArea } = Input;

const Ecografias: React.FC = () => {
  const [ecografias, setEcografias] = useState<Ecografia[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedEcografia, setSelectedEcografia] = useState<Ecografia | null>(null);
  const [embarazos, setEmbarazos] = useState<any[]>([]);
  const [fileList, setFileList] = useState<any[]>([]);
  const [form] = Form.useForm();

  // Filtros
  const [filtroEmbarazo, setFiltroEmbarazo] = useState<number | undefined>();
  const [filtroTipo, setFiltroTipo] = useState<string | undefined>();
  const [filtroFechaDesde, setFiltroFechaDesde] = useState<string | undefined>();
  const [filtroFechaHasta, setFiltroFechaHasta] = useState<string | undefined>();

  useEffect(() => {
    fetchEcografias();
    fetchEmbarazos();
  }, [filtroEmbarazo, filtroTipo, filtroFechaDesde, filtroFechaHasta]);

  const fetchEcografias = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (filtroEmbarazo) params.embarazo = filtroEmbarazo;
      if (filtroTipo) params.tipo_ecografia = filtroTipo;
      if (filtroFechaDesde) params.fecha_desde = filtroFechaDesde;
      if (filtroFechaHasta) params.fecha_hasta = filtroFechaHasta;

      const response = await ecografiasService.list(params);
      setEcografias(response.results || response);
    } catch (error) {
      message.error('Error al cargar ecografías');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmbarazos = async () => {
    try {
      const response = await embarazosService.list();
      setEmbarazos(response.results || response);
    } catch (error) {
      console.error('Error al cargar embarazos:', error);
    }
  };

  const handleCreate = () => {
    setEditingId(null);
    form.resetFields();
    setFileList([]);
    setModalVisible(true);
  };

  const handleEdit = async (id: number) => {
    try {
      const ecografia = await ecografiasService.get(id);
      setEditingId(id);
      form.setFieldsValue({
        ...ecografia,
        fecha_ecografia: ecografia.fecha_ecografia ? dayjs(ecografia.fecha_ecografia) : null,
      });
      setModalVisible(true);
    } catch (error) {
      message.error('Error al cargar datos de la ecografía');
    }
  };

  const handleView = async (id: number) => {
    try {
      const ecografia = await ecografiasService.get(id);
      setSelectedEcografia(ecografia);
      setDrawerVisible(true);
    } catch (error) {
      message.error('Error al cargar detalles');
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '¿Está seguro de eliminar esta ecografía?',
      content: 'Esta acción no se puede deshacer',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await ecografiasService.delete(id);
          message.success('Ecografía eliminada correctamente');
          fetchEcografias();
        } catch (error) {
          message.error('Error al eliminar ecografía');
        }
      },
    });
  };

  const handleSubmit = async (values: any) => {
    try {
      const formData: any = {
        ...values,
        fecha_ecografia: values.fecha_ecografia.format('YYYY-MM-DD'),
      };

      if (fileList.length > 0 && fileList[0].originFileObj) {
        formData.imagen = fileList[0].originFileObj;
      }

      if (editingId) {
        await ecografiasService.update(editingId, formData);
        message.success('Ecografía actualizada correctamente');
      } else {
        await ecografiasService.create(formData);
        message.success('Ecografía creada correctamente');
      }

      setModalVisible(false);
      form.resetFields();
      setFileList([]);
      fetchEcografias();
    } catch (error: any) {
      message.error(error.response?.data?.message || 'Error al guardar ecografía');
    }
  };

  const handleDownloadImagen = async (id: number) => {
    try {
      const blob = await ecografiasService.downloadImagen(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ecografia_${id}.jpg`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('Error al descargar imagen');
    }
  };

  const uploadProps = {
    beforeUpload: (file: any) => {
      setFileList([file]);
      return false;
    },
    fileList,
    onRemove: () => {
      setFileList([]);
    },
  };

  const columns: ColumnsType<Ecografia> = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_ecografia',
      key: 'fecha_ecografia',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
      sorter: (a, b) => dayjs(a.fecha_ecografia).unix() - dayjs(b.fecha_ecografia).unix(),
    },
    {
      title: 'Paciente',
      dataIndex: 'paciente_nombre',
      key: 'paciente_nombre',
      ellipsis: true,
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_ecografia',
      key: 'tipo_ecografia',
      render: (tipo: string) => {
        const colors: Record<string, string> = {
          'primer_trimestre': 'blue',
          'segundo_trimestre': 'green',
          'tercer_trimestre': 'orange',
          'genetica': 'purple',
          'doppler': 'red',
        };
        return <Tag color={colors[tipo] || 'default'}>{tipo.replace(/_/g, ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'EG',
      key: 'edad_gestacional',
      render: (_, record) => `${record.edad_gestacional_semanas}s ${record.edad_gestacional_dias}d`,
    },
    {
      title: 'Peso Fetal',
      dataIndex: 'peso_fetal_estimado',
      key: 'peso_fetal_estimado',
      render: (peso: number) => peso ? `${peso}g` : '-',
    },
    {
      title: 'Fetos',
      dataIndex: 'numero_fetos',
      key: 'numero_fetos',
      align: 'center',
    },
    {
      title: 'LCF',
      dataIndex: 'latidos_cardiacos',
      key: 'latidos_cardiacos',
      align: 'center',
      render: (lcf: boolean, record) => (
        <Space direction="vertical" size="small">
          {lcf ? <Tag color="success">Positivo</Tag> : <Tag color="error">Negativo</Tag>}
          {record.frecuencia_cardiaca && <span>{record.frecuencia_cardiaca} lpm</span>}
        </Space>
      ),
    },
    {
      title: 'Imagen',
      key: 'imagen',
      align: 'center',
      render: (_, record) => record.imagen ? <FileImageOutlined style={{ fontSize: 20, color: '#1890ff' }} /> : '-',
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right',
      width: 200,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleView(record.id)}
          >
            Ver
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record.id)}
          >
            Editar
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            Eliminar
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="Ecografías Obstétricas"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Nueva Ecografía
          </Button>
        }
      >
        {/* Filtros */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Filtrar por embarazo"
              allowClear
              style={{ width: '100%' }}
              onChange={setFiltroEmbarazo}
            >
              {embarazos.map(e => (
                <Option key={e.id} value={e.id}>
                  {e.paciente_nombre} - Gesta {e.numero_gesta}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Select
              placeholder="Tipo de ecografía"
              allowClear
              style={{ width: '100%' }}
              onChange={setFiltroTipo}
            >
              <Option value="primer_trimestre">Primer Trimestre</Option>
              <Option value="segundo_trimestre">Segundo Trimestre</Option>
              <Option value="tercer_trimestre">Tercer Trimestre</Option>
              <Option value="genetica">Genética</Option>
              <Option value="doppler">Doppler</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <DatePicker
              placeholder="Desde"
              style={{ width: '100%' }}
              onChange={(date) => setFiltroFechaDesde(date ? date.format('YYYY-MM-DD') : undefined)}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <DatePicker
              placeholder="Hasta"
              style={{ width: '100%' }}
              onChange={(date) => setFiltroFechaHasta(date ? date.format('YYYY-MM-DD') : undefined)}
            />
          </Col>
        </Row>

        {/* Tabla */}
        <Table
          columns={columns}
          dataSource={ecografias}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showTotal: (total) => `Total: ${total} ecografías`,
          }}
        />
      </Card>

      {/* Modal Crear/Editar */}
      <Modal
        title={editingId ? 'Editar Ecografía' : 'Nueva Ecografía'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        onOk={() => form.submit()}
        width={900}
        okText="Guardar"
        cancelText="Cancelar"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            numero_fetos: 1,
            latidos_cardiacos: true,
            movimientos_fetales: true,
            anatomia_normal: true,
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="embarazo"
                label="Embarazo"
                rules={[{ required: true, message: 'Seleccione el embarazo' }]}
              >
                <Select placeholder="Seleccione embarazo">
                  {embarazos.map(e => (
                    <Option key={e.id} value={e.id}>
                      {e.paciente_nombre} - Gesta {e.numero_gesta}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="fecha_ecografia"
                label="Fecha"
                rules={[{ required: true, message: 'Ingrese la fecha' }]}
              >
                <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="tipo_ecografia"
                label="Tipo de Ecografía"
                rules={[{ required: true }]}
              >
                <Select>
                  <Option value="primer_trimestre">Primer Trimestre</Option>
                  <Option value="segundo_trimestre">Segundo Trimestre</Option>
                  <Option value="tercer_trimestre">Tercer Trimestre</Option>
                  <Option value="genetica">Genética</Option>
                  <Option value="doppler">Doppler</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="edad_gestacional_semanas"
                label="EG Semanas"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={42} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                name="edad_gestacional_dias"
                label="EG Días"
                rules={[{ required: true }]}
              >
                <InputNumber min={0} max={6} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Biometría Fetal</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="longitud_cefalocaudal" label="LCC (mm)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="diametro_biparietal" label="DBP (mm)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="circunferencia_cefalica" label="CC (mm)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="circunferencia_abdominal" label="CA (mm)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="longitud_femur" label="LF (mm)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="peso_fetal_estimado" label="Peso Fetal (g)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>Placenta y Líquido Amniótico</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="placenta_localizacion" label="Localización Placenta">
                <Select>
                  <Option value="anterior">Anterior</Option>
                  <Option value="posterior">Posterior</Option>
                  <Option value="fundica">Fúndica</Option>
                  <Option value="lateral">Lateral</Option>
                  <Option value="previa">Previa</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="placenta_grado" label="Grado Placenta">
                <Select>
                  <Option value="0">Grado 0</Option>
                  <Option value="I">Grado I</Option>
                  <Option value="II">Grado II</Option>
                  <Option value="III">Grado III</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="liquido_amniotico" label="Líquido Amniótico">
                <Select>
                  <Option value="normal">Normal</Option>
                  <Option value="oligohidramnios">Oligohidramnios</Option>
                  <Option value="polihidramnios">Polihidramnios</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="indice_liquido_amniotico" label="ILA (cm)">
                <InputNumber min={0} max={30} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="presentacion_fetal" label="Presentación">
                <Select>
                  <Option value="cefalica">Cefálica</Option>
                  <Option value="podalica">Podálica</Option>
                  <Option value="transversa">Transversa</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="sexo_fetal" label="Sexo Fetal">
                <Select>
                  <Option value="masculino">Masculino</Option>
                  <Option value="femenino">Femenino</Option>
                  <Option value="indeterminado">Indeterminado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider>Evaluación Fetal</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="numero_fetos" label="Número de Fetos">
                <InputNumber min={1} max={5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="latidos_cardiacos" label="Latidos Cardíacos" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="frecuencia_cardiaca" label="FC (lpm)">
                <InputNumber min={0} max={220} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="movimientos_fetales" label="Movimientos Fetales" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="anatomia_normal" label="Anatomía Normal" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="hallazgos" label="Hallazgos">
            <TextArea rows={3} placeholder="Describa hallazgos relevantes" />
          </Form.Item>

          <Form.Item name="observaciones" label="Observaciones">
            <TextArea rows={2} placeholder="Observaciones adicionales" />
          </Form.Item>

          <Form.Item label="Imagen de Ecografía">
            <Upload {...uploadProps} listType="picture" maxCount={1}>
              <Button icon={<FileImageOutlined />}>Seleccionar Imagen</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>

      {/* Drawer Detalles */}
      <Drawer
        title="Detalles de Ecografía"
        placement="right"
        width={700}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedEcografia && (
          <>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="Paciente" span={2}>
                {selectedEcografia.paciente_nombre}
              </Descriptions.Item>
              <Descriptions.Item label="Fecha">
                {dayjs(selectedEcografia.fecha_ecografia).format('DD/MM/YYYY')}
              </Descriptions.Item>
              <Descriptions.Item label="Tipo">
                {selectedEcografia.tipo_ecografia?.replace(/_/g, ' ').toUpperCase()}
              </Descriptions.Item>
              <Descriptions.Item label="EG" span={2}>
                {selectedEcografia.edad_gestacional_semanas} semanas {selectedEcografia.edad_gestacional_dias} días
              </Descriptions.Item>
            </Descriptions>

            <Divider>Biometría Fetal</Divider>
            <Row gutter={16}>
              {selectedEcografia.longitud_cefalocaudal && (
                <Col span={8}>
                  <Statistic title="LCC" value={selectedEcografia.longitud_cefalocaudal} suffix="mm" />
                </Col>
              )}
              {selectedEcografia.diametro_biparietal && (
                <Col span={8}>
                  <Statistic title="DBP" value={selectedEcografia.diametro_biparietal} suffix="mm" />
                </Col>
              )}
              {selectedEcografia.circunferencia_cefalica && (
                <Col span={8}>
                  <Statistic title="CC" value={selectedEcografia.circunferencia_cefalica} suffix="mm" />
                </Col>
              )}
            </Row>
            <Row gutter={16} style={{ marginTop: 16 }}>
              {selectedEcografia.circunferencia_abdominal && (
                <Col span={8}>
                  <Statistic title="CA" value={selectedEcografia.circunferencia_abdominal} suffix="mm" />
                </Col>
              )}
              {selectedEcografia.longitud_femur && (
                <Col span={8}>
                  <Statistic title="LF" value={selectedEcografia.longitud_femur} suffix="mm" />
                </Col>
              )}
              {selectedEcografia.peso_fetal_estimado && (
                <Col span={8}>
                  <Statistic title="Peso Fetal" value={selectedEcografia.peso_fetal_estimado} suffix="g" />
                </Col>
              )}
            </Row>

            <Divider>Evaluación</Divider>
            <Descriptions column={2} bordered size="small">
              <Descriptions.Item label="Número de Fetos">
                {selectedEcografia.numero_fetos}
              </Descriptions.Item>
              <Descriptions.Item label="LCF">
                {selectedEcografia.latidos_cardiacos ? (
                  <Tag color="success">Positivo ({selectedEcografia.frecuencia_cardiaca} lpm)</Tag>
                ) : (
                  <Tag color="error">Negativo</Tag>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Movimientos Fetales">
                {selectedEcografia.movimientos_fetales ? <Tag color="success">Sí</Tag> : <Tag color="error">No</Tag>}
              </Descriptions.Item>
              <Descriptions.Item label="Anatomía Normal">
                {selectedEcografia.anatomia_normal ? <Tag color="success">Sí</Tag> : <Tag color="warning">No</Tag>}
              </Descriptions.Item>
              {selectedEcografia.presentacion_fetal && (
                <Descriptions.Item label="Presentación">
                  {selectedEcografia.presentacion_fetal}
                </Descriptions.Item>
              )}
              {selectedEcografia.sexo_fetal && (
                <Descriptions.Item label="Sexo Fetal">
                  {selectedEcografia.sexo_fetal}
                </Descriptions.Item>
              )}
            </Descriptions>

            {selectedEcografia.hallazgos && (
              <>
                <Divider>Hallazgos</Divider>
                <p>{selectedEcografia.hallazgos}</p>
              </>
            )}

            {selectedEcografia.imagen && (
              <>
                <Divider>Imagen</Divider>
                <Image
                  src={selectedEcografia.imagen}
                  alt="Ecografía"
                  style={{ width: '100%' }}
                />
                <Button
                  icon={<DownloadOutlined />}
                  onClick={() => handleDownloadImagen(selectedEcografia.id)}
                  style={{ marginTop: 8 }}
                >
                  Descargar Imagen
                </Button>
              </>
            )}

            <Divider />
            <Space>
              <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                Imprimir
              </Button>
            </Space>
          </>
        )}
      </Drawer>
    </div>
  );
};

export default Ecografias;
