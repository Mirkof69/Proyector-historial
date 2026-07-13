/**
 * =============================================================================
 * GENERAR REPORTE - CONFIGURACIÓN Y GENERACIÓN
 * =============================================================================
 * Formulario para configurar parámetros y generar reportes
 * - Selección de tipo de reporte
 * - Configuración de parámetros (fechas, filtros)
 * - Selección de formato (PDF/Excel)
 * - Vista previa de datos
 * - Generación asíncrona
 * - Conexión: POST /reportes/generar/
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card,
  Form,
  Input,
  Button,
  Select,
  DatePicker,
  Space,
  Row,
  Col,
  Divider,
  Alert,
  Radio,
  Spin,
  Modal,
  Typography,
  Steps,
  Checkbox,
  Progress,
  Timeline,
  Tag,
  Descriptions,
} from "antd";
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  BarChartOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { reportesService, TipoReporteConfig } from '../../services/reportesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './GenerarReporte.css';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const { Step } = Steps;

interface FormValues {
  tipo_reporte: number;
  nombre: string;
  descripcion?: string;
  formato: string;
  rango_fechas?: [dayjs.Dayjs, dayjs.Dayjs];
  incluir_graficos?: boolean;
  incluir_estadisticas?: boolean;
  agrupar_por?: string;
  filtros_adicionales?: string[];
}

const iconoPorCategoria: Record<string, React.ReactElement> = {
  estadistico: <BarChartOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
  paciente: <FileTextOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
  institucional: <FileTextOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
  regulatorio: <FileTextOutlined style={{ fontSize: 48, color: '#fa8c16' }} />,
  clinico: <FileTextOutlined style={{ fontSize: 48, color: '#ff4d4f' }} />,
  financiero: <BarChartOutlined style={{ fontSize: 48, color: '#13c2c2' }} />,
};

const GenerarReportePage: React.FC = () => {
  const { modal, message } = useAntdApp();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const tipoReporteParam = searchParams.get('tipo');
  const [form] = Form.useForm();

  const [loading, setLoading] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [pasoActual, setPasoActual] = useState(0);
  const [tiposReporte, setTiposReporte] = useState<TipoReporteConfig[]>([]);
  const [cargandoTipos, setCargandoTipos] = useState(true);
  const [tipoSeleccionado, setTipoSeleccionado] = useState<number | null>(null);
  const [progresoGeneracion, setProgresoGeneracion] = useState(0);
  const [reporteGenerado, setReporteGenerado] = useState<any>(null);
  const [vistaPrevia, setVistaPrevia] = useState<any>(null);
  const [tipoDetalle, setTipoDetalle] = useState<TipoReporteConfig | null>(null);

  useEffect(() => {
    let activo = true;
    (async () => {
      try {
        const tipos = await reportesService.listarTiposReporte(true);
        if (!activo) return;
        setTiposReporte(tipos);

        const tipoIdParam = tipoReporteParam ? Number(tipoReporteParam) : null;
        const tipoEncontrado = tipoIdParam ? tipos.find((t) => t.id === tipoIdParam) : null;
        if (tipoEncontrado) {
          setTipoSeleccionado(tipoEncontrado.id);
          form.setFieldsValue({
            tipo_reporte: tipoEncontrado.id,
            nombre: tipoEncontrado.nombre,
            descripcion: tipoEncontrado.descripcion,
            formato: 'pdf',
            rango_fechas: [dayjs().startOf('month'), dayjs().endOf('month')],
          });
          setPasoActual(1);
          reportesService.obtenerTipoReporte(tipoEncontrado.id)
            .then(setTipoDetalle)
            .catch(() => setTipoDetalle(null));
        }
      } catch {
        message.error('Error al cargar los tipos de reporte configurados');
      } finally {
        if (activo) setCargandoTipos(false);
      }
    })();
    return () => { activo = false; };
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, []);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    if (generando) {
      modal.confirm({
        title: '¿Cancelar generación?',
        content: 'El reporte se está generando. ¿Desea cancelar?',
        okText: 'Sí, cancelar',
        cancelText: 'No',
        onOk: () => navigate(FRONTEND_ROUTES.DASHBOARD.REPORTES),
      });
    } else {
      navigate(FRONTEND_ROUTES.DASHBOARD.REPORTES);
    }
  };

  const handleTipoReporteChange = async (tipoId: number) => {
    const tipo = tiposReporte.find((t) => t.id === tipoId);
    if (tipo) {
      setTipoSeleccionado(tipoId);
      form.setFieldsValue({
        nombre: tipo.nombre,
        descripcion: tipo.descripcion,
      });
    }
    try {
      const detalle = await reportesService.obtenerTipoReporte(tipoId);
      setTipoDetalle(detalle);
    } catch {
      setTipoDetalle(null);
    }
  };

  const handleSiguientePaso = async () => {
    try {
      if (pasoActual === 0) {
        // Validar selección de tipo
        const tipoReporte = form.getFieldValue('tipo_reporte');
        if (!tipoReporte) {
          message.error('Seleccione un tipo de reporte');
          return;
        }
        setPasoActual(1);
      } else if (pasoActual === 1) {
        // Validar configuración
        await form.validateFields([
          'nombre',
          'formato',
          'rango_fechas',
        ]);
        setPasoActual(2);
        generarVistaPrevia();
      } else if (pasoActual === 2) {
        // Generar reporte
        generarReporte();
      }
    } catch (error) {
    }
  };

  const handlePasoAnterior = () => {
    if (pasoActual > 0) {
      setPasoActual(prev => prev - 1);
    }
  };

  const generarVistaPrevia = async () => {
    setLoading(true);
    try {
      const values = form.getFieldsValue();
      const preview = await reportesService.getReportePreview(values);
      setVistaPrevia(preview);
      message.success('Vista previa generada');
    } catch (error) {
      message.error('Error al generar vista previa');
    } finally {
      setLoading(false);
    }
  };

  const generarReporte = async () => {
    setGenerando(true);
    setProgresoGeneracion(0);

    try {
      const values: FormValues = await form.validateFields();
      const { tipo_reporte, formato, rango_fechas, nombre, descripcion, ...opciones } = values;

      setProgresoGeneracion(50);

      const resultado = await reportesService.generateReporte(
        tipo_reporte,
        {
          fecha_inicio: rango_fechas ? rango_fechas[0].format('YYYY-MM-DD') : undefined,
          fecha_fin: rango_fechas ? rango_fechas[1].format('YYYY-MM-DD') : undefined,
          nombre,
          descripcion,
          ...opciones,
        },
        formato as any
      );
      setProgresoGeneracion(100);
      setReporteGenerado(resultado);

      message.success('Solicitud de reporte creada correctamente');
      setPasoActual(3);
    } catch (error: any) {
      message.error(
        error?.response?.data?.error || error?.message || 'Error al generar el reporte'
      );
    } finally {
      setGenerando(false);
    }
  };

  const handleDescargarReporte = async () => {
    if (!reporteGenerado) return;

    try {
      const blob = await reportesService.downloadReporte(reporteGenerado.id);
      const extension = reporteGenerado.formato === 'pdf' ? 'pdf' : 'xlsx';
      reportesService.descargarArchivo(blob, `reporte_${reporteGenerado.id}.${extension}`);
      message.success('Reporte descargado correctamente');
    } catch (error: any) {
      if (error?.response?.status === 409) {
        message.warning('El reporte todavía se está procesando, intente descargarlo más tarde');
      } else {
        message.error('Error al descargar el reporte');
      }
    }
  };

  const handleGenerarOtro = () => {
    form.resetFields();
    setTipoSeleccionado(null);
    setTipoDetalle(null);
    setPasoActual(0);
    setReporteGenerado(null);
    setVistaPrevia(null);
    setProgresoGeneracion(0);
  };

  // ==========================================================================
  // RENDER DE PASOS
  // ==========================================================================
  const renderPaso0 = () => {
    return (
      <div>
        <Title level={4}>Seleccione el tipo de reporte</Title>
        <Paragraph type="secondary">
          Elija el tipo de reporte que desea generar
        </Paragraph>

        {cargandoTipos ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin />
          </div>
        ) : tiposReporte.length === 0 ? (
          <Alert
            type="warning"
            showIcon
            message="No hay tipos de reporte configurados"
            description="Un administrador debe crear al menos un Tipo de Reporte activo antes de poder generar reportes."
          />
        ) : (
          <Form.Item
            name="tipo_reporte"
            rules={[{ required: true, message: 'Seleccione un tipo de reporte' }]}
          >
            <Radio.Group
              style={{ width: '100%' }}
              onChange={(e) => handleTipoReporteChange(e.target.value)}
            >
              <Row gutter={[16, 16]}>
                {tiposReporte.map((tipo) => (
                  <Col xs={24} sm={12} md={8} key={tipo.id}>
                    <Card
                      hoverable
                      className={
                        tipoSeleccionado === tipo.id ? 'reporte-card-selected' : ''
                      }
                    >
                      <Radio value={tipo.id} style={{ width: '100%' }}>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div style={{ textAlign: 'center' }}>
                            {iconoPorCategoria[tipo.categoria] || <FileTextOutlined style={{ fontSize: 48 }} />}
                          </div>
                          <Title level={5} style={{ marginBottom: 8 }}>
                            {tipo.nombre}
                          </Title>
                          <Paragraph
                            type="secondary"
                            style={{ marginBottom: 8, fontSize: 12 }}
                          >
                            {tipo.descripcion}
                          </Paragraph>
                          <Tag color={tipo.categoria === 'estadistico' ? 'blue' : 'green'}>
                            {tipo.categoria_display || tipo.categoria}
                          </Tag>
                        </Space>
                      </Radio>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Radio.Group>
          </Form.Item>
        )}
      </div>
    );
  };

  const renderPaso1 = () => {
    const formatosDisponibles = tipoDetalle
      ? [
          tipoDetalle.formato_pdf !== false && 'pdf',
          tipoDetalle.formato_excel !== false && 'excel',
        ].filter(Boolean)
      : ['pdf', 'excel'];
    const requiereFechas = tipoDetalle?.incluir_fecha_inicio || tipoDetalle?.incluir_fecha_fin;

    return (
      <div>
        <Title level={4}>Configure los parámetros del reporte</Title>
        <Paragraph type="secondary">
          Complete la información necesaria para generar el reporte
        </Paragraph>

        <Row gutter={[16, 0]}>
          <Col xs={24}>
            <Form.Item
              name="nombre"
              label="Nombre del Reporte"
              rules={[{ required: true, message: 'Ingrese el nombre' }]}
              tooltip="Nombre descriptivo para identificar el reporte"
            >
              <Input
                placeholder="Ej: Partos Enero 2025"
                size="large"
                prefix={<FileTextOutlined />}
              />
            </Form.Item>
          </Col>

          <Col xs={24}>
            <Form.Item
              name="descripcion"
              label={
                <Space>
                  Descripción (Opcional)
                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                </Space>
              }
              tooltip="Descripción adicional del reporte"
            >
              <TextArea
                rows={3}
                placeholder="Descripción detallada del reporte..."
                showCount
                maxLength={200}
              />
            </Form.Item>
          </Col>

          <Col xs={24} md={12}>
            <Form.Item
              name="formato"
              label="Formato de Salida"
              rules={[{ required: true, message: 'Seleccione el formato' }]}
            >
              <Radio.Group size="large">
                {formatosDisponibles.includes('pdf') && (
                  <Radio value="pdf">
                    <Space>
                      <FilePdfOutlined style={{ color: '#ff4d4f' }} />
                      PDF
                    </Space>
                  </Radio>
                )}
                {formatosDisponibles.includes('excel') && (
                  <Radio value="excel">
                    <Space>
                      <FileExcelOutlined style={{ color: '#52c41a' }} />
                      Excel
                    </Space>
                  </Radio>
                )}
              </Radio.Group>
            </Form.Item>
          </Col>

          {requiereFechas && (
            <Col xs={24} md={12}>
              <Form.Item
                name="rango_fechas"
                label="Rango de Fechas"
                rules={[{ required: true, message: 'Seleccione el rango' }]}
                tooltip="Período de tiempo para el reporte"
              >
                <RangePicker
                  style={{ width: '100%' }}
                  format="DD/MM/YYYY"
                  size="large"
                />
              </Form.Item>
            </Col>
          )}

          <Col xs={24}>
            <Divider>Opciones Adicionales</Divider>
            <Form.Item name="incluir_graficos" valuePropName="checked">
              <Checkbox>Incluir gráficos estadísticos</Checkbox>
            </Form.Item>
            <Form.Item name="incluir_estadisticas" valuePropName="checked">
              <Checkbox>Incluir resumen estadístico</Checkbox>
            </Form.Item>
            <Form.Item
              name="agrupar_por"
              label="Agrupar por"
              tooltip="Criterio de agrupación de datos"
            >
              <Select placeholder="Seleccione criterio" allowClear>
                <Option value="semana">Semana</Option>
                <Option value="mes">Mes</Option>
                <Option value="medico">Médico</Option>
                <Option value="tipo">Tipo</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
      </div>
    );
  };

  const renderPaso2 = () => {
    return (
      <div>
        <Title level={4}>Vista Previa</Title>
        <Paragraph type="secondary">
          Revise la configuración antes de generar el reporte
        </Paragraph>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>Generando vista previa…</div>
          </div>
        ) : vistaPrevia ? (
          <Card>
            <Descriptions column={{ xs: 1, sm: 2 }} bordered>
              <Descriptions.Item label="Tipo de Reporte">
                {vistaPrevia.tipo_nombre}
              </Descriptions.Item>
              <Descriptions.Item label="Formato">
                <Tag color={vistaPrevia.formato === 'pdf' ? 'red' : 'green'}>
                  {vistaPrevia.formato?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Rango de Fechas">
                {vistaPrevia.fecha_inicio && vistaPrevia.fecha_fin
                  ? `${dayjs(vistaPrevia.fecha_inicio).format('DD/MM/YYYY')} - ${dayjs(vistaPrevia.fecha_fin).format('DD/MM/YYYY')}`
                  : 'Sin restricción de fechas'}
              </Descriptions.Item>
              <Descriptions.Item label="Registros a Incluir">
                <Text strong>{vistaPrevia.total_registros}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="Tamaño Estimado">
                {vistaPrevia.tamanio_estimado_kb >= 1024
                  ? `${(vistaPrevia.tamanio_estimado_kb / 1024).toFixed(1)} MB`
                  : `${vistaPrevia.tamanio_estimado_kb} KB`}
              </Descriptions.Item>
            </Descriptions>

            <Alert
              message="Información"
              description={`El reporte incluirá ${vistaPrevia.total_registros} registros del período seleccionado.`}
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>
        ) : (
          <Alert
            message="No se pudo generar la vista previa"
            type="warning"
            showIcon
          />
        )}
      </div>
    );
  };

  const renderPaso3 = () => {
    return (
      <div>
        {generando ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <LoadingOutlined style={{ fontSize: 64, color: '#1890ff' }} />
            <Title level={3} style={{ marginTop: 24 }}>
              Generando Reporte…
            </Title>
            <Paragraph type="secondary">
              Por favor espere mientras se genera el reporte
            </Paragraph>
            <Progress
              percent={progresoGeneracion}
              status="active"
              strokeColor={{ from: '#108ee9', to: '#87d068' }}
              style={{ marginBottom: 32 }}
            />

            <Timeline
              mode="alternate"
              style={{ textAlign: 'left', marginTop: 24 }}
              items={[
                {
                  color: progresoGeneracion > 0 ? 'green' : 'gray',
                  children: (
                    <>
                      <Text strong>Validando datos</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 0 ? '✓ Completado' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 30 ? 'green' : progresoGeneracion > 0 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Consultando base de datos</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 30 ? '✓ Completado' : progresoGeneracion > 0 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 60 ? 'green' : progresoGeneracion > 30 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Procesando información</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 60 ? '✓ Completado' : progresoGeneracion > 30 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion > 90 ? 'green' : progresoGeneracion > 60 ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>Generando archivo</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion > 90 ? '✓ Completado' : progresoGeneracion > 60 ? '⟳ En proceso...' : 'En espera...'}
                      </Text>
                    </>
                  )
                },
                {
                  color: progresoGeneracion === 100 ? 'green' : 'gray',
                  children: (
                    <>
                      <Text strong>Finalizado</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {progresoGeneracion === 100 ? '✓ Listo para descargar' : 'En espera...'}
                      </Text>
                    </>
                  )
                }
              ]}
            />
          </div>
        ) : reporteGenerado ? (
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <CheckCircleOutlined
              style={{ fontSize: 64, color: reporteGenerado.estado === 'completado' ? '#52c41a' : '#1890ff', marginBottom: 24 }}
            />
            <Title level={3}>
              {reporteGenerado.estado === 'completado' ? '¡Reporte Listo!' : 'Solicitud de Reporte Creada'}
            </Title>
            <Paragraph type="secondary">
              {reporteGenerado.estado === 'completado'
                ? 'El reporte se generó correctamente y está listo para descargar.'
                : 'La solicitud se registró correctamente y se está procesando. Podrá descargarlo cuando el estado cambie a "Completado".'}
            </Paragraph>

            <Card style={{ marginTop: 24, textAlign: 'left' }}>
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Tipo de Reporte">
                  {reporteGenerado.tipo_reporte_nombre}
                </Descriptions.Item>
                <Descriptions.Item label="Formato">
                  <Tag color={reporteGenerado.formato === 'pdf' ? 'red' : 'green'}>
                    {reporteGenerado.formato?.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Estado">
                  <Tag color={reporteGenerado.estado === 'completado' ? 'success' : reporteGenerado.estado === 'error' ? 'error' : 'processing'}>
                    {reporteGenerado.estado_display || reporteGenerado.estado}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Fecha de Solicitud">
                  {dayjs(reporteGenerado.fecha_solicitud).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Space size="large" style={{ marginTop: 32 }}>
              <Button
                type="primary"
                size="large"
                icon={<DownloadOutlined />}
                disabled={reporteGenerado.estado !== 'completado'}
                onClick={handleDescargarReporte}
              >
                Descargar Reporte
              </Button>
              <Button size="large" onClick={handleGenerarOtro}>
                Generar Otro Reporte
              </Button>
              <Button size="large" onClick={handleVolver}>
                Volver al Listado
              </Button>
            </Space>
          </div>
        ) : null}
      </div>
    );
  };

  // ==========================================================================
  // RENDER PRINCIPAL
  // ==========================================================================
  return (
    <div className="generar-reporte-container">
      <Card
        title={
          <Space>
            <FileTextOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>Generar Reporte</span>
          </Space>
        }
        extra={
          <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
            Volver
          </Button>
        }
      >
        <Steps current={pasoActual} style={{ marginBottom: 32 }}>
          <Step
            title="Tipo de Reporte"
            icon={<FileTextOutlined />}
            description="Seleccione el tipo"
          />
          <Step
            title="Configuración"
            icon={<SettingOutlined />}
            description="Configure parámetros"
          />
          <Step
            title="Vista Previa"
            icon={<EyeOutlined />}
            description="Revise antes de generar"
          />
          <Step
            title="Generación"
            icon={generando ? <LoadingOutlined /> : <CheckCircleOutlined />}
            description="Genere el reporte"
          />
        </Steps>

        <Form form={form} layout="vertical">
          {pasoActual === 0 && renderPaso0()}
          {pasoActual === 1 && renderPaso1()}
          {pasoActual === 2 && renderPaso2()}
          {pasoActual === 3 && renderPaso3()}
        </Form>

        {pasoActual < 3 && (
          <>
            <Divider />
            <Space>
              {pasoActual > 0 && (
                <Button size="large" onClick={handlePasoAnterior}>
                  Anterior
                </Button>
              )}
              <Button
                type="primary"
                size="large"
                onClick={handleSiguientePaso}
                loading={loading || generando}
              >
                {pasoActual === 2 ? 'Generar Reporte' : 'Siguiente'}
              </Button>
            </Space>
          </>
        )}
      </Card>
    </div>
  );
};

export default GenerarReportePage;
