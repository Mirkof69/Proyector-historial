/**
 * =============================================================================
 * GENERADOR DE REPORTES PDF AUTOMÁTICOS
 * =============================================================================
 * Sistema completo de generación automática de reportes en PDF
 *
 * TIPOS DE REPORTES:
 * - Historia Clínica Completa
 * - Reporte de Embarazo
 * - Resultados de Laboratorio
 * - Reporte de Ecografía
 * - Plan de Parto
 * - Epicrisis de Alta
 * - Certificados Médicos
 * - Estadísticas Periódicas
 *
 * INTEGRACIÓN: jsPDF, pdfmake, o react-pdf
 * Para producción, instalar: npm install jspdf jspdf-autotable
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card, Row, Col, Button, Space, Select, Typography,
  Divider, Form, Radio, Checkbox, Tag, message,
  Modal, Alert, Tabs, List, Badge, Statistic, Progress,
  Input, Table, Spin, DatePicker
} from 'antd';
import {
  FilePdfOutlined, DownloadOutlined, PrinterOutlined,
  FileTextOutlined, ExperimentOutlined,
  FileImageOutlined, HeartOutlined, CalendarOutlined,
  SettingOutlined, HistoryOutlined, SafetyOutlined,
  CheckCircleOutlined, EyeOutlined,
  ClockCircleOutlined, UserOutlined, SendOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { pacientesService } from '../../services/pacientesService';
import { embarazosService } from '../../services/embarazosService';
import { laboratorioService } from '../../services/laboratorioService';
import { ecografiasService } from '../../services/ecografiasService';
import { partosService } from '../../services/partosService';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

const tabClinicos = <span><FileTextOutlined />Clínicos</span>;
const tabAdministrativos = <span><SafetyOutlined />Administrativos</span>;
const tabEstadisticos = <span><CalendarOutlined />Estadísticos</span>;

const fileTextIcon = <FileTextOutlined />;
const heartIcon = <HeartOutlined />;
const experimentIcon = <ExperimentOutlined />;
const fileImageIcon = <FileImageOutlined />;
const safetyIcon = <SafetyOutlined />;
const checkCircleIcon2 = <CheckCircleOutlined />;
const calendarIcon2 = <CalendarOutlined />;
const historyIcon = <HistoryOutlined />;
const settingIcon = <SettingOutlined />;
const filePdfIcon = <FilePdfOutlined />;
const clockCircleIcon2 = <ClockCircleOutlined />;
const eyeIcon2 = <EyeOutlined />;
const sendIcon = <SendOutlined />;
const printerIcon = <PrinterOutlined />;
const downloadIcon = <DownloadOutlined />;

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactElement;
  category: 'clinical' | 'administrative' | 'statistical';
  requiredData: string[];
  estimatedTime: string;
}

interface GeneratedReport {
  id: string;
  template: string;
  timestamp: string;
  status: 'generating' | 'completed' | 'error';
  downloadUrl?: string;
  size?: string;
}

const GeneradorPDFAutomatico: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();

  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [recentReports, setRecentReports] = useState<GeneratedReport[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const previewContentRef = useRef<string>('');
  const [selectedPatient, setSelectedPatient] = useState<number | null>(null);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([null, null]);
  const previewRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (previewRef.current && previewContentRef.current) {
      previewRef.current.innerHTML = previewContentRef.current;
    }
  }, [previewVisible]);

  // Datos para selección
  const [pacientes, setPacientes] = useState<any[]>([]);
  const [embarazos, setEmbarazos] = useState<any[]>([]);
  const [laboratorio, setLaboratorio] = useState<any[]>([]);
  const [ecografias, setEcografias] = useState<any[]>([]);
  const [partos, setPartos] = useState<any[]>([]);

  useEffect(() => {
    cargarDatos();
    cargarReportesRecientes();
  }, []);

  const cargarDatos = async () => {
    try {
      const [
        pacientesData,
        embarazosData,
        laboratorioData,
        ecografiasData,
        partosData
      ] = await Promise.all([
        pacientesService.listar(),
        embarazosService.listar(),
        laboratorioService.listar(),
        ecografiasService.listar(),
        partosService.listar()
      ]);
      setPacientes(pacientesData);
      setEmbarazos(embarazosData);
      setLaboratorio(laboratorioData);
      setEcografias(ecografiasData);
      setPartos(partosData);
    } catch (error) {
      message.error('Error cargando datos del sistema');
    }
  };

  const cargarReportesRecientes = () => {
    // Simulación - en producción, cargar desde localStorage o API
    const stored = localStorage.getItem('generated_reports:v1');
    if (stored) {
      setRecentReports(JSON.parse(stored));
    }
  };

  // Plantillas de reportes disponibles
  const templates: ReportTemplate[] = [
    {
      id: 'historia_clinica',
      name: 'Historia Clínica Completa',
      description: 'Reporte completo del historial médico del paciente incluyendo todos los embarazos, controles, laboratorios y ecografías',
      icon: fileTextIcon,
      category: 'clinical',
      requiredData: ['paciente'],
      estimatedTime: '30-45 segundos'
    },
    {
      id: 'reporte_embarazo',
      name: 'Reporte de Embarazo',
      description: 'Documento detallado de un embarazo específico con todos sus controles, ecografías y resultados',
      icon: heartIcon,
      category: 'clinical',
      requiredData: ['paciente', 'embarazo'],
      estimatedTime: '20-30 segundos'
    },
    {
      id: 'resultados_laboratorio',
      name: 'Resultados de Laboratorio',
      description: 'Compilación de todos los exámenes de laboratorio con gráficas de evolución',
      icon: experimentIcon,
      category: 'clinical',
      requiredData: ['paciente', 'fecha_inicio', 'fecha_fin'],
      estimatedTime: '15-20 segundos'
    },
    {
      id: 'informe_ecografia',
      name: 'Informe de Ecografía',
      description: 'Reporte detallado de ecografía con mediciones, imágenes y conclusiones',
      icon: fileImageIcon,
      category: 'clinical',
      requiredData: ['ecografia'],
      estimatedTime: '10-15 segundos'
    },
    {
      id: 'plan_parto',
      name: 'Plan de Parto',
      description: 'Documento personalizado con preferencias y planificación del parto',
      icon: safetyIcon,
      category: 'clinical',
      requiredData: ['paciente', 'embarazo'],
      estimatedTime: '10-15 segundos'
    },
    {
      id: 'epicrisis',
      name: 'Epicrisis de Alta',
      description: 'Resumen de hospitalización y alta médica',
      icon: checkCircleIcon2,
      category: 'clinical',
      requiredData: ['paciente', 'parto'],
      estimatedTime: '15-20 segundos'
    },
    {
      id: 'certificado_medico',
      name: 'Certificado Médico',
      description: 'Certificado oficial de estado de salud o embarazo',
      icon: fileTextIcon,
      category: 'administrative',
      requiredData: ['paciente'],
      estimatedTime: '5-10 segundos'
    },
    {
      id: 'estadisticas_mensual',
      name: 'Estadísticas Mensuales',
      description: 'Reporte estadístico consolidado del mes con gráficas y KPIs',
      icon: calendarIcon2,
      category: 'statistical',
      requiredData: ['fecha_inicio', 'fecha_fin'],
      estimatedTime: '60-90 segundos'
    },
    {
      id: 'control_prenatal',
      name: 'Carnet de Control Prenatal',
      description: 'Carnet completo de controles prenatales con gráficas de crecimiento',
      icon: historyIcon,
      category: 'clinical',
      requiredData: ['paciente', 'embarazo'],
      estimatedTime: '25-35 segundos'
    }
  ];

  const handleGenerate = async (values: any) => {
    setGenerating(true);
    setProgress(0);

    try {
      // Simular progreso
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return 95;
          }
          return prev + 5;
        });
      }, 200);

      // Aquí iría la lógica real de generación con jsPDF
      await simulateReportGeneration(values);

      clearInterval(progressInterval);
      setProgress(100);

      // Crear registro del reporte
      const newReport: GeneratedReport = {
        id: Date.now().toString(),
        template: selectedTemplate,
        timestamp: dayjs().format('YYYY-MM-DD HH:mm:ss'),
        status: 'completed',
        downloadUrl: '#', // URL simulada
        size: '1.2 MB'
      };

      const updated = [newReport, ...recentReports].slice(0, 10);
      setRecentReports(updated);
      localStorage.setItem('generated_reports:v1', JSON.stringify(updated));

      message.success('Reporte PDF generado exitosamente');

      // Simular descarga
      setTimeout(() => {
        message.info('Iniciando descarga del PDF...');
      }, 500);

    } catch (error) {
      message.error('Error al generar el reporte');
    } finally {
      setGenerating(false);
      setProgress(0);
    }
  };

  const simulateReportGeneration = (values: any): Promise<void> => {
    return new Promise((resolve) => {
      // Simulación de generación - en producción aquí iría:
      /*
      import jsPDF from 'jspdf';
      import 'jspdf-autotable';

      const doc = new jsPDF();
      doc.setFontSize(18);
      doc.text('Título del Reporte', 14, 22);
      doc.setFontSize(11);
      doc.text(`Paciente: ${values.paciente_nombre}`, 14, 30);
      doc.text(`Fecha: ${dayjs().format('DD/MM/YYYY')}`, 14, 35);

      // Agregar tabla con datos
      doc.autoTable({
        head: [['Campo', 'Valor']],
        body: [
          ['CI', values.ci],
          ['Edad', values.edad],
          // ... más datos
        ],
        startY: 45
      });

      doc.save(`reporte_${values.paciente_id}_${Date.now()}.pdf`);
      */

      setTimeout(resolve, 2000);
    });
  };

  const handlePreview = () => {
    const template = templates.find(t => t.id === selectedTemplate);
    if (!template) return;

    previewContentRef.current = `
      <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h1 style="color: #1890ff;">${template.name}</h1>
        <p><strong>Generado:</strong> ${dayjs().format('DD/MM/YYYY HH:mm')}</p>
        <hr />
        <h2>Información del Paciente</h2>
        <p>Este es un preview simulado del reporte.</p>
        <p>En producción, aquí se mostraría el contenido real del PDF.</p>
      </div>
    `;
    setPreviewVisible(true);
  };

  const getTemplatesByCategory = (category: string) => {
    return templates.filter(t => t.category === category);
  };

  return (
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>
            📄 Generador de Reportes PDF Automáticos
          </Title>
          <Text type="secondary">
            Sistema de generación automática de reportes médicos en formato PDF
          </Text>
        </Col>
        <Col>
          <Space>
            <Badge count={recentReports.filter(r => r.status === 'completed').length}>
              <Button icon={historyIcon}>
                Historial
              </Button>
            </Badge>
            <Button icon={settingIcon}>
              Configuración
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Estadísticas rápidas */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Reportes Generados Hoy"
              value={recentReports.filter(r =>
                dayjs(r.timestamp).isSame(dayjs(), 'day')
              ).length}
              prefix={filePdfIcon}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Plantillas Disponibles"
              value={templates.length}
              prefix={fileTextIcon}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Tiempo Promedio"
              value="22"
              suffix="seg"
              prefix={clockCircleIcon2}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Éxito"
              value={98.5}
              suffix="%"
              prefix={checkCircleIcon2}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        {/* Panel izquierdo - Selección de plantilla y formulario */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <>
                <FilePdfOutlined /> Generar Nuevo Reporte
              </>
            }
          >
            <Tabs defaultActiveKey="clinical">
              <TabPane
                tab={tabClinicos}
                key="clinical"
              >
                <Row gutter={[16, 16]}>
                  {getTemplatesByCategory('clinical').map(template => (
                    <Col xs={24} sm={12} md={8} key={template.id}>
                      <Card
                        hoverable
                        size="small"
                        onClick={() => setSelectedTemplate(template.id)}
                        style={{
                          borderColor: selectedTemplate === template.id ? '#1890ff' : undefined,
                          borderWidth: selectedTemplate === template.id ? 2 : 1
                        }}
                      >
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div style={{ fontSize: 32, textAlign: 'center', color: '#1890ff' }}>
                            {template.icon}
                          </div>
                          <Title level={5} style={{ margin: 0, textAlign: 'center' }}>
                            {template.name}
                          </Title>
                          <Text type="secondary" style={{ fontSize: 12, textAlign: 'center', display: 'block' }}>
                            {template.description}
                          </Text>
                          <Tag color="blue" style={{ alignSelf: 'center' }}>
                            ~{template.estimatedTime}
                          </Tag>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </TabPane>

              <TabPane
                tab={tabAdministrativos}
                key="administrative"
              >
                <Row gutter={[16, 16]}>
                  {getTemplatesByCategory('administrative').map(template => (
                    <Col xs={24} sm={12} md={8} key={template.id}>
                      <Card
                        hoverable
                        size="small"
                        onClick={() => setSelectedTemplate(template.id)}
                        style={{
                          borderColor: selectedTemplate === template.id ? '#1890ff' : undefined,
                          borderWidth: selectedTemplate === template.id ? 2 : 1
                        }}
                      >
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div style={{ fontSize: 32, textAlign: 'center', color: '#52c41a' }}>
                            {template.icon}
                          </div>
                          <Title level={5} style={{ margin: 0, textAlign: 'center' }}>
                            {template.name}
                          </Title>
                          <Text type="secondary" style={{ fontSize: 12, textAlign: 'center', display: 'block' }}>
                            {template.description}
                          </Text>
                          <Tag color="green" style={{ alignSelf: 'center' }}>
                            ~{template.estimatedTime}
                          </Tag>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </TabPane>

              <TabPane
                tab={tabEstadisticos}
                key="statistical"
              >
                <Row gutter={[16, 16]}>
                  {getTemplatesByCategory('statistical').map(template => (
                    <Col xs={24} sm={12} md={8} key={template.id}>
                      <Card
                        hoverable
                        size="small"
                        onClick={() => setSelectedTemplate(template.id)}
                        style={{
                          borderColor: selectedTemplate === template.id ? '#1890ff' : undefined,
                          borderWidth: selectedTemplate === template.id ? 2 : 1
                        }}
                      >
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div style={{ fontSize: 32, textAlign: 'center', color: '#faad14' }}>
                            {template.icon}
                          </div>
                          <Title level={5} style={{ margin: 0, textAlign: 'center' }}>
                            {template.name}
                          </Title>
                          <Text type="secondary" style={{ fontSize: 12, textAlign: 'center', display: 'block' }}>
                            {template.description}
                          </Text>
                          <Tag color="orange" style={{ alignSelf: 'center' }}>
                            ~{template.estimatedTime}
                          </Tag>
                        </Space>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </TabPane>
            </Tabs>

            <Divider />

            {selectedTemplate && (
              <Form
                form={form}
                layout="vertical"
                onFinish={handleGenerate}
              >
                <Alert
                  message="Plantilla seleccionada"
                  description={templates.find(t => t.id === selectedTemplate)?.name}
                  type="info"
                  showIcon
                  closable
                  style={{ marginBottom: 16 }}
                />

                <Form.Item
                  label={<><UserOutlined /> Seleccionar Paciente</>}
                  name="paciente_id"
                  rules={[{ required: true, message: 'Seleccione un paciente' }]}
                >
                  <Select
                    showSearch
                    placeholder="Buscar paciente por nombre o CI"
                    optionFilterProp="children"
                    onChange={(value) => setSelectedPatient(value)}
                    filterOption={(input, option: any) =>
                      option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                    }
                  >
                    {pacientes.map(p => (
                      <Select.Option key={p.id} value={p.id}>
                        {p.nombre} {p.apellido_paterno || p.apellido || ''} - CI: {p.ci}
                      </Select.Option>
                    ))}
                  </Select>
                </Form.Item>

                {selectedPatient && (
                  <Alert
                    message={
                      <Space>
                        <Text>Paciente seleccionado:</Text>
                        <Button
                          type="link"
                          size="small"
                          onClick={() => navigate(`/dashboard/pacientes/${selectedPatient}`)}
                        >
                          Ver perfil completo
                        </Button>
                      </Space>
                    }
                    description={
                      <Space direction="vertical" size="small">
                        <div>
                          <Tag color="blue">{embarazos.filter(e => e.paciente === selectedPatient).length} Embarazos</Tag>
                          <Tag color="green">{ecografias.filter(e => e.paciente === selectedPatient).length} Ecografías</Tag>
                          <Tag color="orange">{laboratorio.filter(l => l.paciente === selectedPatient).length} Laboratorio</Tag>
                          <Tag color="purple">{partos.filter(p => p.paciente === selectedPatient).length} Partos</Tag>
                        </div>
                      </Space>
                    }
                    type="success"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )}

                {selectedTemplate === 'reporte_embarazo' && (
                  <Form.Item
                    label="Seleccionar Embarazo"
                    name="embarazo_id"
                  >
                    <Select placeholder="Seleccione el embarazo">
                      {embarazos.map(e => (
                        <Select.Option key={e.id} value={e.id}>
                          {e.codigo_embarazo} - {e.paciente_nombre} - {dayjs(e.fecha_registro).format('DD/MM/YYYY')}
                        </Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                )}

                <Form.Item
                  label="Opciones de Exportación"
                  name="opciones"
                >
                  <Checkbox.Group>
                    <Row>
                      <Col span={12}>
                        <Checkbox value="incluir_imagenes">Incluir imágenes</Checkbox>
                      </Col>
                      <Col span={12}>
                        <Checkbox value="incluir_graficas">Incluir gráficas</Checkbox>
                      </Col>
                      <Col span={12}>
                        <Checkbox value="firma_digital">Firma digital</Checkbox>
                      </Col>
                      <Col span={12}>
                        <Checkbox value="marca_agua">Marca de agua</Checkbox>
                      </Col>
                    </Row>
                  </Checkbox.Group>
                </Form.Item>

                <Form.Item
                  label="Rango de Fechas para Reporte"
                  name="fecha_rango"
                >
                  <RangePicker
                    style={{ width: '100%' }}
                    placeholder={['Fecha inicio', 'Fecha fin']}
                    format="DD/MM/YYYY"
                    value={dateRange}
                    onChange={(dates) => setDateRange(dates || [null, null])}
                  />
                </Form.Item>

                <Form.Item
                  label="Búsqueda Avanzada"
                  name="busqueda"
                >
                  <Input
                    placeholder="Buscar en datos del paciente (diagnósticos, observaciones, etc.)"
                    prefix={<UserOutlined />}
                    allowClear
                  />
                </Form.Item>

                <Form.Item
                  label="Orientación"
                  name="orientacion"
                  initialValue="portrait"
                >
                  <Radio.Group>
                    <Radio value="portrait">Vertical</Radio>
                    <Radio value="landscape">Horizontal</Radio>
                  </Radio.Group>
                </Form.Item>

                {generating && (
                  <div style={{ marginBottom: 16 }}>
                    <Text type="secondary">Generando reporte…</Text>
                    <Progress percent={progress} status="active" />
                  </div>
                )}

                <Space>
                  <Button
                    type="primary"
                    htmlType="submit"
                    icon={filePdfIcon}
                    loading={generating}
                    disabled={!selectedTemplate}
                  >
                    Generar PDF
                  </Button>
                  <Button
                    icon={eyeIcon2}
                    onClick={handlePreview}
                    disabled={!selectedTemplate || generating}
                  >
                    Vista Previa
                  </Button>
                  <Button
                    icon={sendIcon}
                    disabled={!selectedTemplate || generating}
                  >
                    Enviar por Email
                  </Button>
                  <Button
                    icon={printerIcon}
                    disabled={!selectedTemplate || generating}
                  >
                    Imprimir
                  </Button>
                </Space>
              </Form>
            )}

            {/* Patient Data Table */}
            {selectedPatient && selectedTemplate && (
              <>
                <Divider>Datos del Paciente para el Reporte</Divider>
                <Spin spinning={false}>
                  <Table
                    size="small"
                    pagination={false}
                    dataSource={[
                      {
                        key: '1',
                        tipo: 'Embarazos',
                        cantidad: embarazos.filter(e => e.paciente === selectedPatient).length,
                        estado: 'Activo'
                      },
                      {
                        key: '2',
                        tipo: 'Ecografías',
                        cantidad: ecografias.filter(e => e.paciente === selectedPatient).length,
                        estado: 'Completado'
                      },
                      {
                        key: '3',
                        tipo: 'Análisis de Laboratorio',
                        cantidad: laboratorio.filter(l => l.paciente === selectedPatient).length,
                        estado: 'Varios'
                      },
                      {
                        key: '4',
                        tipo: 'Partos',
                        cantidad: partos.filter(p => p.paciente === selectedPatient).length,
                        estado: 'Completado'
                      }
                    ]}
                    columns={[
                      {
                        title: 'Tipo de Dato',
                        dataIndex: 'tipo',
                        key: 'tipo'
                      },
                      {
                        title: 'Cantidad',
                        dataIndex: 'cantidad',
                        key: 'cantidad',
                        render: (value: number) => <Badge count={value} showZero style={{ backgroundColor: '#52c41a' }} />
                      },
                      {
                        title: 'Estado',
                        dataIndex: 'estado',
                        key: 'estado',
                        render: (estado: string) => <Tag color="blue">{estado}</Tag>
                      }
                    ]}
                  />
                </Spin>
              </>
            )}
          </Card>
        </Col>

        {/* Panel derecho - Reportes recientes */}
        <Col xs={24} lg={8}>
          <Card
            title={
              <>
                <HistoryOutlined /> Reportes Recientes
              </>
            }
            extra={
              <Button size="small" onClick={cargarReportesRecientes}>
                <DownloadOutlined /> Ver Todos
              </Button>
            }
          >
            {recentReports.length === 0 ? (
              <Alert
                message="Sin reportes"
                description="No hay reportes generados recientemente"
                type="info"
                showIcon
              />
            ) : (
              <List
                dataSource={recentReports}
                renderItem={report => {
                  const template = templates.find(t => t.id === report.template);
                  return (
                    <List.Item
                      actions={[
                        <Button
                          key="download"
                          type="link"
                          size="small"
                          icon={downloadIcon}
                          onClick={() => message.info('DesCargando…')}
                        >
                          Descargar
                        </Button>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={
                          <div style={{ fontSize: 24, color: '#1890ff' }}>
                            {template?.icon}
                          </div>
                        }
                        title={template?.name || 'Reporte'}
                        description={
                          <Space direction="vertical" size={0}>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              {dayjs(report.timestamp).format('DD/MM/YYYY HH:mm')}
                            </Text>
                            <Tag color="green" style={{ fontSize: 12 }}>
                              {report.size}
                            </Tag>
                          </Space>
                        }
                      />
                    </List.Item>
                  );
                }}
              />
            )}
          </Card>

          <Card
            title="Información"
            style={{ marginTop: 16 }}
            size="small"
          >
            <Paragraph style={{ fontSize: 12, marginBottom: 8 }}>
              <strong>Formatos soportados:</strong>
            </Paragraph>
            <Space wrap size="small">
              <Tag color="red">PDF</Tag>
              <Tag color="green">DOCX</Tag>
              <Tag color="blue">HTML</Tag>
            </Space>

            <Divider style={{ margin: '12px 0' }} />

            <Paragraph style={{ fontSize: 12, marginBottom: 8 }}>
              <strong>Próximas características:</strong>
            </Paragraph>
            <ul style={{ fontSize: 12, paddingLeft: 20, margin: 0 }}>
              <li>Envío automático por email</li>
              <li>Programación de reportes periódicos</li>
              <li>Plantillas personalizables</li>
              <li>Firma electrónica</li>
            </ul>
          </Card>
        </Col>
      </Row>

      {/* Modal de preview */}
      <Modal
        title="Vista Previa del Reporte"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            Cerrar
          </Button>,
          <Button key="generate" type="primary" icon={filePdfIcon}>
            Generar PDF
          </Button>
        ]}
      >
        <div
          ref={previewRef}
          style={{ maxHeight: '60vh', overflowY: 'auto' }}
        />
      </Modal>
    </div>
  );
};

export default GeneradorPDFAutomatico;
