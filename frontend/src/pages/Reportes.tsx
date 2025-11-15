/**
 * =============================================================================
 * PÁGINA DE REPORTES
 * =============================================================================
 * Generación de reportes médicos en PDF
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Form,
  Select,
  Button,
  DatePicker,
  Space,
  message,
  Tabs,
  Divider,
  Alert,
  List,
  Tag,
  Radio,
} from 'antd';
import {
  FilePdfOutlined,
  DownloadOutlined,
  PrinterOutlined,
  FileTextOutlined,
  BarChartOutlined,
  MedicineBoxOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import reportesService from '../services/reportesService';
import pacientesService, { Paciente } from '../services/pacientesService';
import embarazosService, { Embarazo } from '../services/embarazosService';

const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const Reportes: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [activeReport, setActiveReport] = useState<string>('historial');

  const [formHistorial] = Form.useForm();
  const [formCarnet] = Form.useForm();
  const [formEstadisticas] = Form.useForm();
  const [formControlPrenatal] = Form.useForm();
  const [formCertificadoNacimiento] = Form.useForm();
  const [formResumenParto] = Form.useForm();
  const [formEvoluciones] = Form.useForm();

  useEffect(() => {
    fetchPacientes();
    fetchEmbarazos();
  }, []);

  const fetchPacientes = async () => {
    try {
      const response = await pacientesService.getAll({ activo: true });
      setPacientes(response);
    } catch (error) {
      message.error('Error al cargar pacientes');
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

  const downloadPDF = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleGenerarHistorial = async (values: any) => {
    setLoading(true);
    try {
      const params = {
        paciente_id: values.paciente_id,
        fecha_desde: values.fecha_rango ? values.fecha_rango[0].format('YYYY-MM-DD') : undefined,
        fecha_hasta: values.fecha_rango ? values.fecha_rango[1].format('YYYY-MM-DD') : undefined,
        incluir_controles: values.incluir_controles || false,
        incluir_ecografias: values.incluir_ecografias || false,
        incluir_laboratorio: values.incluir_laboratorio || false,
        incluir_embarazos: values.incluir_embarazos || false,
      };

      const blob = await reportesService.generarHistorialPaciente(params);
      downloadPDF(blob, `historial_paciente_${values.paciente_id}.pdf`);
      message.success('Reporte generado correctamente');
    } catch (error) {
      message.error('Error al generar reporte');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarCarnet = async (values: any) => {
    setLoading(true);
    try {
      const blob = await reportesService.generarCarnetPerinatal(values.embarazo_id);
      downloadPDF(blob, `carnet_perinatal_${values.embarazo_id}.pdf`);
      message.success('Carnet generado correctamente');
    } catch (error) {
      message.error('Error al generar carnet');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarEstadisticas = async (values: any) => {
    setLoading(true);
    try {
      const params = {
        fecha_desde: values.fecha_rango[0].format('YYYY-MM-DD'),
        fecha_hasta: values.fecha_rango[1].format('YYYY-MM-DD'),
        tipo_reporte: values.tipo_reporte,
        agrupar_por: values.agrupar_por || 'mes',
      };

      const blob = await reportesService.generarEstadisticas(params);
      downloadPDF(blob, `estadisticas_${params.tipo_reporte}.pdf`);
      message.success('Reporte estadístico generado correctamente');
    } catch (error) {
      message.error('Error al generar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarControlPrenatal = async (values: any) => {
    setLoading(true);
    try {
      const blob = await reportesService.generarControlPrenatal(values.control_id);
      downloadPDF(blob, `control_prenatal_${values.control_id}.pdf`);
      message.success('Reporte de control prenatal generado');
    } catch (error) {
      message.error('Error al generar reporte de control');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarCertificadoNacimiento = async (values: any) => {
    setLoading(true);
    try {
      const blob = await reportesService.generarCertificadoNacimiento(values.parto_id);
      downloadPDF(blob, `certificado_nacimiento_${values.parto_id}.pdf`);
      message.success('Certificado de nacimiento generado');
    } catch (error) {
      message.error('Error al generar certificado');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarResumenParto = async (values: any) => {
    setLoading(true);
    try {
      const blob = await reportesService.generarResumenParto(values.parto_id);
      downloadPDF(blob, `resumen_parto_${values.parto_id}.pdf`);
      message.success('Resumen de parto generado');
    } catch (error) {
      message.error('Error al generar resumen');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerarEvoluciones = async (values: any) => {
    setLoading(true);
    try {
      const params = {
        embarazo_id: values.embarazo_id,
        fecha_desde: values.fecha_rango ? values.fecha_rango[0].format('YYYY-MM-DD') : undefined,
        fecha_hasta: values.fecha_rango ? values.fecha_rango[1].format('YYYY-MM-DD') : undefined,
      };

      const blob = await reportesService.generarEvoluciones(params);
      downloadPDF(blob, `evoluciones_${values.embarazo_id}.pdf`);
      message.success('Reporte de evoluciones generado');
    } catch (error) {
      message.error('Error al generar evoluciones');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1>Generación de Reportes</h1>
      <p>Genere reportes médicos en formato PDF</p>

      <Alert
        message="Información"
        description="Los reportes se descargarán automáticamente en formato PDF. Asegúrese de permitir las descargas en su navegador."
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />

      <Tabs
        activeKey={activeReport}
        onChange={(key) => setActiveReport(key)}
      >
        {/* Historial Completo del Paciente */}
        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              Historial Paciente
            </span>
          }
          key="historial"
        >
          <Card>
            <Form form={formHistorial} layout="vertical" onFinish={handleGenerarHistorial}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="paciente_id"
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
                          {`${pac.nombre} ${pac.apellido} - CI: ${pac.ci}`}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item name="fecha_rango" label="Rango de Fechas (opcional)">
                    <RangePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Divider>Secciones a Incluir</Divider>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="incluir_embarazos" valuePropName="checked">
                    <Radio.Group>
                      <Radio value={true}>Incluir Embarazos</Radio>
                      <Radio value={false}>Excluir Embarazos</Radio>
                    </Radio.Group>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="incluir_controles" valuePropName="checked">
                    <Radio.Group>
                      <Radio value={true}>Incluir Controles Prenatales</Radio>
                      <Radio value={false}>Excluir Controles</Radio>
                    </Radio.Group>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="incluir_ecografias" valuePropName="checked">
                    <Radio.Group>
                      <Radio value={true}>Incluir Ecografías</Radio>
                      <Radio value={false}>Excluir Ecografías</Radio>
                    </Radio.Group>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="incluir_laboratorio" valuePropName="checked">
                    <Radio.Group>
                      <Radio value={true}>Incluir Laboratorio</Radio>
                      <Radio value={false}>Excluir Laboratorio</Radio>
                    </Radio.Group>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<FilePdfOutlined />}
                  size="large"
                >
                  Generar Historial Completo
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Carnet Perinatal */}
        <TabPane
          tab={
            <span>
              <MedicineBoxOutlined />
              Carnet Perinatal
            </span>
          }
          key="carnet"
        >
          <Card>
            <Form form={formCarnet} layout="vertical" onFinish={handleGenerarCarnet}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="embarazo_id"
                    label="Embarazo"
                    rules={[{ required: true, message: 'Seleccione un embarazo' }]}
                  >
                    <Select placeholder="Seleccione embarazo">
                      {embarazos.map((emb) => (
                        <Option key={emb.id} value={emb.id}>
                          {`${emb.paciente_nombre} - Embarazo ${emb.numero_embarazo} - FUR: ${dayjs(
                            emb.fecha_ultima_regla
                          ).format('DD/MM/YYYY')}`}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Alert
                message="Carnet Perinatal"
                description="El carnet perinatal incluye todos los datos del embarazo actual, controles prenatales, ecografías y exámenes de laboratorio."
                type="info"
                showIcon
                style={{ marginBottom: '16px' }}
              />

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<FilePdfOutlined />}
                  size="large"
                >
                  Generar Carnet Perinatal
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Estadísticas */}
        <TabPane
          tab={
            <span>
              <BarChartOutlined />
              Estadísticas
            </span>
          }
          key="estadisticas"
        >
          <Card>
            <Form form={formEstadisticas} layout="vertical" onFinish={handleGenerarEstadisticas}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="fecha_rango"
                    label="Rango de Fechas"
                    rules={[{ required: true, message: 'Seleccione rango de fechas' }]}
                  >
                    <RangePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="tipo_reporte"
                    label="Tipo de Reporte"
                    rules={[{ required: true, message: 'Seleccione tipo de reporte' }]}
                  >
                    <Select placeholder="Seleccione tipo">
                      <Option value="general">Estadísticas Generales</Option>
                      <Option value="embarazos">Embarazos</Option>
                      <Option value="partos">Partos</Option>
                      <Option value="consultas">Consultas</Option>
                      <Option value="laboratorio">Laboratorio</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="agrupar_por" label="Agrupar Por">
                    <Select placeholder="Seleccione agrupación">
                      <Option value="dia">Día</Option>
                      <Option value="semana">Semana</Option>
                      <Option value="mes">Mes</Option>
                      <Option value="anio">Año</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<FilePdfOutlined />}
                  size="large"
                >
                  Generar Reporte Estadístico
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* Resumen de Parto */}
        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              Resumen Parto
            </span>
          }
          key="parto"
        >
          <Card>
            <Alert
              message="Reportes de Parto"
              description="Genere certificados de nacimiento o resúmenes detallados de parto"
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />

            <Divider>Certificado de Nacimiento</Divider>
            <Form form={formCertificadoNacimiento} layout="vertical" onFinish={handleGenerarCertificadoNacimiento}>
              <Row gutter={16}>
                <Col span={18}>
                  <Form.Item
                    name="parto_id"
                    label="Seleccionar Parto"
                    rules={[{ required: true, message: 'Seleccione un parto' }]}
                  >
                    <Select placeholder="Seleccione parto">
                      <Option value={1}>Parto 1 - María García - 15/10/2024</Option>
                      <Option value={2}>Parto 2 - Ana López - 20/10/2024</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label=" ">
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<FilePdfOutlined />}
                      block
                    >
                      Generar Certificado
                    </Button>
                  </Form.Item>
                </Col>
              </Row>
            </Form>

            <Divider>Resumen de Parto</Divider>
            <Form form={formResumenParto} layout="vertical" onFinish={handleGenerarResumenParto}>
              <Row gutter={16}>
                <Col span={18}>
                  <Form.Item
                    name="parto_id"
                    label="Seleccionar Parto"
                    rules={[{ required: true, message: 'Seleccione un parto' }]}
                  >
                    <Select placeholder="Seleccione parto">
                      <Option value={1}>Parto 1 - María García - 15/10/2024</Option>
                      <Option value={2}>Parto 2 - Ana López - 20/10/2024</Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label=" ">
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<FilePdfOutlined />}
                      block
                    >
                      Generar Resumen
                    </Button>
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </TabPane>

        {/* Evoluciones y Controles */}
        <TabPane
          tab={
            <span>
              <PrinterOutlined />
              Evoluciones
            </span>
          }
          key="evoluciones"
        >
          <Card>
            <Form form={formEvoluciones} layout="vertical" onFinish={handleGenerarEvoluciones}>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item
                    name="embarazo_id"
                    label="Embarazo"
                    rules={[{ required: true, message: 'Seleccione un embarazo' }]}
                  >
                    <Select placeholder="Seleccione embarazo">
                      {embarazos.map((emb) => (
                        <Option key={emb.id} value={emb.id}>
                          {`${emb.paciente_nombre} - Embarazo ${emb.numero_embarazo}`}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item name="fecha_rango" label="Rango de Fechas (opcional)">
                    <RangePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Alert
                message="Reporte de Evoluciones"
                description="Incluye todos los controles prenatales, ecografías y notas de evolución del embarazo seleccionado."
                type="info"
                showIcon
                style={{ marginBottom: '16px' }}
              />

              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<FilePdfOutlined />}
                  size="large"
                >
                  Generar Reporte de Evoluciones
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>

      <Divider />

      <Card title="Reportes Disponibles" style={{ marginTop: '24px' }}>
        <List
          dataSource={[
            {
              title: 'Historial Completo del Paciente',
              description: 'Incluye todos los datos médicos del paciente con filtros personalizables',
              icon: <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />,
            },
            {
              title: 'Carnet Perinatal',
              description: 'Documento estándar con todos los datos del embarazo actual',
              icon: <MedicineBoxOutlined style={{ fontSize: '24px', color: '#52c41a' }} />,
            },
            {
              title: 'Estadísticas Institucionales',
              description: 'Reportes estadísticos agrupados por período de tiempo',
              icon: <BarChartOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />,
            },
            {
              title: 'Certificados y Resúmenes de Parto',
              description: 'Documentos oficiales del nacimiento y resumen clínico del parto',
              icon: <FilePdfOutlined style={{ fontSize: '24px', color: '#eb2f96' }} />,
            },
            {
              title: 'Evoluciones y Controles',
              description: 'Historial de controles prenatales y evolución del embarazo',
              icon: <PrinterOutlined style={{ fontSize: '24px', color: '#722ed1' }} />,
            },
          ]}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                avatar={item.icon}
                title={<strong>{item.title}</strong>}
                description={item.description}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default Reportes;
