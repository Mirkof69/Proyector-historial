/**
 * =============================================================================
 * FORMULARIO DE ECOGRAFÍA OBSTÉTRICA
 * =============================================================================
 * Formulario completo para el registro y edición de ecografías.
 * Estructura:
 * - Datos Generales: Paciente, embarazo, fecha, tipo, médico.
 * - Biometría Fetal: Mediciones (DBP, CC, CA, LF), peso estimado, percentiles.
 * - Anatomía Fetal: Evaluación detallada de órganos y sistemas.
 * - Anexos Fetales: Placenta, cordón, líquido amniótico, cérvix.
 * - Imágenes: Subida de múltiples imágenes con descripción.
 * - Conclusiones: Diagnóstico, observaciones, seguimiento.
 * =============================================================================
 */

import React, { useState, useRef } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  DatePicker,
  InputNumber,
  Row,
  Col,
  Space,
  Upload,
  message,
  Spin,
  Divider,
  Typography,
  Tabs,
  Checkbox,
  Alert,
  Radio,
  Tooltip,
  Modal,
} from 'antd';
import {
  SaveOutlined,
  ArrowLeftOutlined,
  UploadOutlined,
  FileImageOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  ScanOutlined,
  FileTextOutlined,
  InfoCircleOutlined,
  CalendarOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { citasService } from '../../services/citasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAuth } from '../../hooks/useAuth';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

const tabDatosGenerales = <span><ScanOutlined />Datos Generales</span>;
const tabBiometriaFetal = <span><MedicineBoxOutlined />Biometría Fetal</span>;
const tabAnatomiaFetal = <span><ExperimentOutlined />Anatomía Fetal</span>;
const tabAnexosFetales = (
  <span>
    <InfoCircleOutlined />
    Anexos Fetales
  </span>
);
const tabImagenesConclusiones = (
  <span>
    <FileImageOutlined />
    Imágenes y Conclusiones
  </span>
);

const ARROW_LEFT_ICON_5 = <ArrowLeftOutlined />;
const SAVE_ICON_4 = <SaveOutlined />;
const EYE_ICON_3 = <EyeOutlined />;
const CALENDAR_ICON_6 = <CalendarOutlined />;

const FormularioEcografia: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditing = !!id;
  const [form] = Form.useForm();
  const { user } = useAuth();

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [selectedPaciente, setSelectedPaciente] = useState<number | null>(null);
  const [selectedEmbarazo, setSelectedEmbarazo] = useState<Embarazo | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  // ==========================================================================
  // CARGAR DATOS INICIALES
  // ==========================================================================
  const cargarPacientes = async () => {
    try {
      const data = await pacientesService.getAll();
      setPacientes(data);
    } catch (error) {
      message.error('Error al cargar lista de pacientes');
    }
  };

  const cargarEmbarazos = async (pacienteId: number) => {
    try {
      const data = await embarazosService.getByPaciente(pacienteId) as Embarazo[];
      // Mostrar TODOS los embarazos sin importar el estado (activo, finalizado, interrumpido)
      // para permitir registrar ecografías de cualquier embarazo
      setEmbarazos(data);

      if (data.length === 0) {
        message.warning('Este paciente no tiene embarazos registrados');
      }
    } catch (error) {
      message.error('Error al cargar embarazos del paciente');
    }
  };

  const cargarEcografia = async (ecoId: number) => {
    setLoading(true);
    try {
      const data = await ecografiasService.getById(ecoId);
      form.setFieldsValue({
        ...data,
        fecha_ecografia: dayjs(data.fecha_ecografia),
        paciente: data.paciente,
        embarazo: data.embarazo,
        proxima_ecografia_recomendada: data.proxima_ecografia_recomendada ? dayjs(data.proxima_ecografia_recomendada) : null,
      });
      setSelectedPaciente(data.paciente || null);
      if (data.paciente) {
        const embarazosData = await embarazosService.getByPaciente(data.paciente) as Embarazo[];
        setEmbarazos(embarazosData);
        if (data.embarazo) {
          const embarazoSeleccionado = embarazosData.find(e => e.id === data.embarazo);
          if (embarazoSeleccionado) {
            setSelectedEmbarazo(embarazoSeleccionado);
          }
        }
      }
      if (data.imagenes && data.imagenes.length > 0) {
        setFileList(data.imagenes.map((img: any, index: number) => ({
          uid: String(img.id || index),
          name: img.titulo || `Imagen ${index + 1}`,
          status: 'done',
          url: img.url_imagen || img.imagen,
        })));
      }
    } catch (error) {
      message.error('Error al cargar datos de la ecografía');
      navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
    } finally {
      setLoading(false);
    }
  };

  const initializedRef = useRef(false);
  if (!initializedRef.current) {
    initializedRef.current = true;
    cargarPacientes();
    if (isEditing) {
      cargarEcografia(Number(id));
    }
  }

  const handlePacienteChange = (value: number | null) => {
    setSelectedPaciente(value);
    if (value) {
      cargarEmbarazos(value);
    } else {
      setEmbarazos([]);
      form.setFieldsValue({ embarazo: undefined });
    }
  };

  // ==========================================================================
  // CALCULAR EDAD GESTACIONAL
  // ==========================================================================
  const calcularEdadGestacional = (fumStr: string, fechaEcoStr: string) => {
    try {
      const fum = dayjs(fumStr);
      const fechaEco = dayjs(fechaEcoStr);

      if (!fum.isValid() || !fechaEco.isValid()) return { semanas: 0, dias: 0 };

      // Calcular días totales desde FUM hasta fecha de ecografía
      const diasTotales = fechaEco.diff(fum, 'days');

      if (diasTotales < 0) return { semanas: 0, dias: 0 };

      // Convertir a semanas y días
      const semanas = Math.floor(diasTotales / 7);
      const dias = diasTotales % 7;

      return { semanas, dias };
    } catch (error) {
      return { semanas: 0, dias: 0 };
    }
  };

  const actualizarEdadGestacional = (embarazoId?: number) => {
    // Obtener valores del formulario
    const idEmbarazo = embarazoId || form.getFieldValue('embarazo');
    let fechaEco = form.getFieldValue('fecha_ecografia');

    // Si no hay embarazo, no hacer nada
    if (!idEmbarazo) return;

    // Buscar el embarazo seleccionado
    const embarazoSeleccionado = embarazos.find(e => e.id === idEmbarazo);
    if (!embarazoSeleccionado?.fecha_ultima_menstruacion) {
      message.warning('El embarazo seleccionado no tiene fecha de última menstruación (FUM)');
      return;
    }

    // Guardar embarazo seleccionado en el estado
    setSelectedEmbarazo(embarazoSeleccionado);

    // Si no hay fecha de ecografía, usar la fecha actual
    if (!fechaEco) {
      fechaEco = dayjs();
      form.setFieldsValue({ fecha_ecografia: fechaEco });
    }

    // Calcular edad gestacional
    const { semanas, dias } = calcularEdadGestacional(
      embarazoSeleccionado.fecha_ultima_menstruacion,
      fechaEco.format('YYYY-MM-DD')
    );

    // Autocompletar campos (el usuario puede modificarlos después)
    form.setFieldsValue({
      edad_gestacional_semanas: semanas,
      edad_gestacional_dias: dias
    });

    // Mostrar mensaje de confirmación
    message.success(`✓ Edad gestacional autocompletada: ${semanas}+${dias} semanas`, 3);
  };

  // ==========================================================================
  // SUBMIT
  // ==========================================================================
  const onFinish = async (values: any) => {
    setSubmitting(true);
    try {
      // Preparar datos
      const ecografiaData: Partial<Ecografia> = {
        ...values,
        fecha_ecografia: values.fecha_ecografia.format('YYYY-MM-DD'),
        proxima_ecografia_recomendada: values.proxima_ecografia_recomendada?.format('YYYY-MM-DD'),
        // Las secciones anidadas (biometria, anatomia, anexos) ya vienen estructuradas gracias a los nombres de campos
      };

      // Manejar imágenes nuevas
      // Nota: El servicio `create` maneja FormData si hay imágenes en el array `imagenes`
      // Aquí transformamos el fileList de Antd al formato que espera el servicio
      const nuevasImagenes = fileList.reduce((acc, f) => {
        if (f.originFileObj) {
          acc.push({
            imagen: f.originFileObj as File,
            descripcion: f.name,
            orden: acc.length
          });
        }
        return acc;
      }, [] as any[]);

      if (nuevasImagenes.length > 0) {
        ecografiaData.imagenes = nuevasImagenes;
      }

      if (isEditing) {
        await ecografiasService.update(Number(id), ecografiaData);

        // Si hay imágenes nuevas en edición, subirlas en paralelo
        await Promise.all(
          nuevasImagenes.map((img) => ecografiasService.addImagen(Number(id), img))
        );

        message.success('Ecografía actualizada correctamente');
      } else {
        await ecografiasService.create(ecografiaData);
        message.success('Ecografía registrada correctamente');
      }

      navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
    } catch (error) {
      message.error('Error al guardar la ecografía. Verifique los datos.');
    } finally {
      setSubmitting(false);
    }
  };

  // ==========================================================================
  // IMAGE PREVIEW HANDLERS
  // ==========================================================================
  const getBase64 = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = (error) => reject(error);
    });

  const handlePreview = async (file: UploadFile) => {
    if (!file.url && !file.preview) {
      file.preview = await getBase64(file.originFileObj as File);
    }

    setPreviewImage(file.url || (file.preview as string));
    setPreviewVisible(true);
    setPreviewTitle(file.name || file.url!.substring(file.url!.lastIndexOf('/') + 1));
  };

  const handleCancelPreview = () => {
    setPreviewVisible(false);
  };

  // ==========================================================================
  // APPOINTMENT INTEGRATION
  // ==========================================================================
  const handleCrearCita = async () => {
    const proximaFecha = form.getFieldValue('proxima_ecografia_recomendada');
    const pacienteId = form.getFieldValue('paciente');
    const embarazoId = form.getFieldValue('embarazo');

    if (!proximaFecha) {
      message.warning('Por favor, seleccione una fecha para la próxima ecografía primero');
      return;
    }

    if (!pacienteId) {
      message.warning('Por favor, seleccione un paciente primero');
      return;
    }

    try {
      // Crear cita para la próxima ecografía
      const citaData = {
        paciente: pacienteId,
        fecha_cita: proximaFecha.format('YYYY-MM-DD'),
        hora_cita: '09:00:00', // Hora por defecto, el usuario puede modificarla luego
        tipo_cita: 'control' as const,
        estado: 'agendada' as const,
        motivo: 'Ecografía de control programada',
        observaciones: embarazoId ? `Seguimiento de embarazo ID: ${embarazoId}` : undefined,
        medico: user?.id || 1, // Usuario actual
      };

      await citasService.create(citaData);
      message.success('Cita creada en la agenda. Puede editarla desde el módulo de Citas');
    } catch (error) {
      message.error('Error al crear la cita en la agenda');
    }
  };

  // ==========================================================================
  // UPLOAD CONFIG
  // ==========================================================================
  const uploadProps: UploadProps = {
    onRemove: (file) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);

      // Si es edición y la imagen ya existía (tiene ID), habría que llamar a deleteImagen
      // Esto requeriría lógica adicional para identificar imágenes existentes vs nuevas
    },
    beforeUpload: async (file) => {
      const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'application/dicom';
      if (!isJpgOrPng) {
        message.error('Solo se permiten archivos JPG/PNG o DICOM');
        return Upload.LIST_IGNORE;
      }
      const isLt10M = file.size / 1024 / 1024 < 10;
      if (!isLt10M) {
        message.error('La imagen debe ser menor a 10MB');
        return Upload.LIST_IGNORE;
      }

      // Generar preview de la imagen
      try {
        const preview = await getBase64(file);
        const uploadFile: UploadFile = {
          uid: file.uid || String(Date.now()),
          name: file.name,
          status: 'done',
          originFileObj: file,
          thumbUrl: preview, // Vista previa en miniatura
          url: preview, // URL para preview
        };
        setFileList(prev => [...prev, uploadFile]);
      } catch (error) {
        setFileList(prev => [...prev, file]);
      }

      return false; // Manual upload
    },
    onPreview: handlePreview,
    fileList,
    listType: 'picture-card',
    multiple: true,
    showUploadList: {
      showPreviewIcon: true,
      showRemoveIcon: true,
      showDownloadIcon: false,
    },
    progress: {
      strokeColor: {
        '0%': '#108ee9',
        '100%': '#87d068',
      },
      strokeWidth: 3,
      format: (percent) => `${Math.round(percent || 0)}%`,
    },
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>;
  }

  return (
    <div className="formulario-ecografia-container">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* HEADER */}
        <Card>
          <Row justify="space-between" align="middle">
            <Col>
              <Space>
                <Button
                  icon={ARROW_LEFT_ICON_5}
                  onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS)}
                >
                  Volver
                </Button>
                <Title level={4} style={{ margin: 0 }}>
                  {isEditing ? 'Editar Ecografía' : 'Nueva Ecografía Obstétrica'}
                </Title>
              </Space>
            </Col>
            <Col>
              <Button
                type="primary"
                icon={SAVE_ICON_4}
                loading={submitting}
                onClick={() => form.submit()}
                size="large"
              >
                Guardar Ecografía
              </Button>
            </Col>
          </Row>
        </Card>

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          initialValues={{
            fecha_ecografia: dayjs(),
            tipo_ecografia: 'primer_trimestre',
            numero_fetos: 1,
            vitalidad_fetal: true,
            biometria: {
              percentil_peso: 50
            },
            anatomia: {
              craneo_normal: true,
              cerebro_normal: true,
              cerebelo_normal: true,
              perfil_facial_normal: true,
              labios_normales: true,
              corazon_normal: true,
              pulmones_normales: true,
              estomago_normal: true,
              rinones_normales: true,
              vejiga_normal: true,
              columna_normal: true,
              extremidades_superiores_normales: true,
              extremidades_inferiores_normales: true,
            },
            anexos: {
              liquido_amniotico_normal: true,
              numero_vasos_cordon: 3,
            }
          }}
        >
          <Tabs defaultActiveKey="1" type="card" size="large">

            {/* TAB 1: DATOS GENERALES */}
            <TabPane
              tab={tabDatosGenerales}
              key="1"
            >
              <Card className="shadow-sm">
                <Row gutter={24}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="paciente"
                      label="Paciente"
                      rules={[{ required: true, message: 'Seleccione un paciente' }]}
                    >
                      <Select
                        placeholder="Buscar paciente..."
                        showSearch
                        filterOption={(input, option) =>
                          (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                        }
                        onChange={handlePacienteChange}
                        options={pacientes.map((p) => ({
                          label: `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''} - ${p.id_clinico}`,
                          value: p.id,
                        }))}
                        disabled={isEditing}
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item
                      name="embarazo"
                      label="Embarazo Asociado"
                      rules={[{ required: true, message: 'Seleccione un embarazo' }]}
                    >
                      <Select
                        placeholder={selectedPaciente ? 'Seleccione embarazo...' : 'Primero seleccione paciente'}
                        disabled={!selectedPaciente || embarazos.length === 0 || isEditing}
                        onChange={actualizarEdadGestacional}
                        options={embarazos.map((e) => ({
                          label: `FUM: ${dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY')} - ${(e.estado || 'activo').toUpperCase()}`,
                          value: e.id,
                        }))}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={24}>
                  <Col xs={24} md={8}>
                    <Form.Item
                      name="fecha_ecografia"
                      label="Fecha del Estudio"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <DatePicker
                        style={{ width: '100%' }}
                        format="DD/MM/YYYY"
                        onChange={actualizarEdadGestacional}
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Form.Item
                      name="tipo_ecografia"
                      label="Tipo de Ecografía"
                      rules={[{ required: true, message: 'Requerido' }]}
                    >
                      <Select>
                        <Option value="primer_trimestre">Primer Trimestre (6-14 sem)</Option>
                        <Option value="segundo_trimestre">Segundo Trimestre (14-28 sem)</Option>
                        <Option value="tercer_trimestre">Tercer Trimestre (28-42 sem)</Option>
                        <Option value="doppler">Doppler</Option>
                        <Option value="morfologica">Morfológica</Option>
                        <Option value="genetica">Genética</Option>
                        <Option value="4d">Ecografía 4D</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Form.Item
                      name="indicacion"
                      label="Indicación Médica"
                    >
                      <Select>
                        <Option value="control_rutina">Control de Rutina</Option>
                        <Option value="sospecha_malformacion">Sospecha de Malformación</Option>
                        <Option value="control_crecimiento">Control de Crecimiento</Option>
                        <Option value="evaluacion_bienestar">Evaluación Bienestar Fetal</Option>
                        <Option value="sangrado">Sangrado</Option>
                        <Option value="screening_genetico">Screening Genético</Option>
                        <Option value="doppler_fetal">Doppler Fetal</Option>
                        <Option value="otro">Otro</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>

                <Divider orientation="left">Datos Básicos del Feto</Divider>

                {/* INFORMACIÓN DEL EMBARAZO SELECCIONADO */}
                {selectedEmbarazo && (
                  <Alert
                    message="Información del Embarazo"
                    description={
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Row gutter={16}>
                          <Col span={8}>
                            <Text strong>FUM:</Text> {dayjs(selectedEmbarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
                          </Col>
                          <Col span={8}>
                            <Text strong>FPP:</Text> {selectedEmbarazo.fecha_probable_parto ? dayjs(selectedEmbarazo.fecha_probable_parto).format('DD/MM/YYYY') : 'No calculada'}
                          </Col>
                          <Col span={8}>
                            <Text strong>Estado:</Text> {(selectedEmbarazo.estado || 'activo').toUpperCase()}
                          </Col>
                        </Row>
                        <Row gutter={16}>
                          <Col span={12}>
                            <Text strong>Semanas actuales:</Text> {selectedEmbarazo.semanas_gestacion || 'N/A'}
                          </Col>
                          <Col span={12}>
                            <Text strong>Tipo:</Text> {selectedEmbarazo.tipo_embarazo || 'único'}
                          </Col>
                        </Row>
                      </Space>
                    }
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                )}

                <Row gutter={24}>
                  <Col xs={24} md={6}>
                    <Form.Item
                      name="edad_gestacional_semanas"
                      label="Semanas (por Eco)"
                      rules={[{ required: true, message: 'Requerido' }]}
                      tooltip="Se autocompleta desde el embarazo, pero puede modificarse"
                    >
                      <InputNumber
                        min={4}
                        max={43}
                        style={{ width: '100%' }}
                        placeholder="Autocompleta desde embarazo"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item
                      name="edad_gestacional_dias"
                      label="Días"
                      initialValue={0}
                      tooltip="Se autocompleta desde el embarazo, pero puede modificarse"
                    >
                      <InputNumber
                        min={0}
                        max={6}
                        style={{ width: '100%' }}
                        placeholder="Días adicionales"
                      />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item
                      name="numero_fetos"
                      label="Número de Fetos"
                    >
                      <InputNumber min={1} max={5} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item
                      name="vitalidad_fetal"
                      label="Vitalidad Fetal"
                      valuePropName="checked"
                    >
                      <Checkbox>Presente</Checkbox>
                    </Form.Item>
                  </Col>
                </Row>
                <Row gutter={24}>
                  <Col xs={24} md={8}>
                    <Form.Item
                      name="frecuencia_cardiaca_fetal"
                      label="FCF (latidos/min)"
                      rules={[{ type: 'number', min: 0, max: 250 }]}
                    >
                      <InputNumber style={{ width: '100%' }} suffix="lpm" />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </TabPane>

            {/* TAB 2: BIOMETRÍA */}
            <TabPane
              tab={tabBiometriaFetal}
              key="2"
            >
              <Card className="shadow-sm">
                <Alert
                  message="Mediciones Biométricas"
                  description="Ingrese las medidas en milímetros (mm). El peso fetal se calculará automáticamente si no se especifica."
                  type="info"
                  showIcon
                  style={{ marginBottom: 24 }}
                />

                <Row gutter={24}>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'diametro_biparietal']} label="DBP (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Diámetro Biparietal" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'circunferencia_cefalica']} label="CC (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Circunferencia Cefálica" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'circunferencia_abdominal']} label="CA (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Circunferencia Abdominal" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'longitud_femur']} label="LF (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Longitud Fémur" />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={24}>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'diametro_occipito_frontal']} label="DOF (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Diámetro Occípito-Frontal" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'longitud_humero']} label="LH (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Longitud Húmero" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'diametro_transverso_cerebelo']} label="DTC (mm)">
                      <InputNumber style={{ width: '100%' }} placeholder="Diámetro Cerebelo" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={6}>
                    <Form.Item name={['biometria', 'cisterna_magna']} label="Cisterna Magna (mm)">
                      <InputNumber style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Row gutter={24}>
                  <Col xs={24} md={8}>
                    <Form.Item name={['biometria', 'peso_fetal_estimado']} label="Peso Fetal Estimado (g)">
                      <InputNumber style={{ width: '100%' }} suffix="g" />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Form.Item name={['biometria', 'percentil_peso']} label="Percentil de Peso">
                      <InputNumber min={1} max={100} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </TabPane>

            {/* TAB 3: ANATOMÍA */}
            <TabPane
              tab={tabAnatomiaFetal}
              key="3"
            >
              <Card className="shadow-sm">
                <Row gutter={24}>
                  <Col xs={24} md={8}>
                    <Title level={5}>Cabeza y Cuello</Title>
                    <Form.Item name={['anatomia', 'craneo_normal']} valuePropName="checked">
                      <Checkbox>Cráneo Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'cerebro_normal']} valuePropName="checked">
                      <Checkbox>Cerebro Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'cerebelo_normal']} valuePropName="checked">
                      <Checkbox>Cerebelo Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'perfil_facial_normal']} valuePropName="checked">
                      <Checkbox>Perfil Facial Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'labios_normales']} valuePropName="checked">
                      <Checkbox>Labios Normales</Checkbox>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Title level={5}>Tórax y Abdomen</Title>
                    <Form.Item name={['anatomia', 'corazon_normal']} valuePropName="checked">
                      <Checkbox>Corazón Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'pulmones_normales']} valuePropName="checked">
                      <Checkbox>Pulmones Normales</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'estomago_normal']} valuePropName="checked">
                      <Checkbox>Estómago Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'rinones_normales']} valuePropName="checked">
                      <Checkbox>Riñones Normales</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'vejiga_normal']} valuePropName="checked">
                      <Checkbox>Vejiga Normal</Checkbox>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Title level={5}>Esqueleto y Otros</Title>
                    <Form.Item name={['anatomia', 'columna_normal']} valuePropName="checked">
                      <Checkbox>Columna Vertebral Normal</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'extremidades_superiores_normales']} valuePropName="checked">
                      <Checkbox>Extremidades Superiores</Checkbox>
                    </Form.Item>
                    <Form.Item name={['anatomia', 'extremidades_inferiores_normales']} valuePropName="checked">
                      <Checkbox>Extremidades Inferiores</Checkbox>
                    </Form.Item>
                    <Divider />
                    <Form.Item name={['anatomia', 'sexo_fetal']} label="Sexo Fetal">
                      <Radio.Group>
                        <Radio value="masculino">Masculino</Radio>
                        <Radio value="femenino">Femenino</Radio>
                        <Radio value="indeterminado">Indeterminado</Radio>
                      </Radio.Group>
                    </Form.Item>
                  </Col>
                </Row>

                <Divider />

                <Row gutter={24}>
                  <Col xs={24} md={12}>
                    <Form.Item name={['anatomia', 'translucencia_nucal']} label="Translucencia Nucal (mm)">
                      <InputNumber step={0.1} style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Form.Item name={['anatomia', 'hueso_nasal_presente']} valuePropName="checked">
                      <Checkbox>Hueso Nasal Presente</Checkbox>
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item name={['anatomia', 'hallazgos_anormales']} label="Hallazgos Anormales / Observaciones Anatómicas">
                  <TextArea rows={3} />
                </Form.Item>
              </Card>
            </TabPane>

            {/* TAB 4: ANEXOS */}
            <TabPane
              tab={tabAnexosFetales}
              key="4"
            >
              <Card className="shadow-sm">
                <Row gutter={24}>
                  <Col xs={24} md={12}>
                    <Title level={5}>Placenta</Title>
                    <Form.Item name={['anexos', 'placenta_localizacion']} label="Localización">
                      <Select>
                        <Option value="anterior">Anterior</Option>
                        <Option value="posterior">Posterior</Option>
                        <Option value="fundica">Fúndica</Option>
                        <Option value="lateral_derecha">Lateral Derecha</Option>
                        <Option value="lateral_izquierda">Lateral Izquierda</Option>
                        <Option value="previa_marginal">Previa Marginal</Option>
                        <Option value="previa_oclusiva">Previa Oclusiva Total</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item name={['anexos', 'grado_madurez_placenta']} label="Grado de Madurez (Grannum)">
                      <Select>
                        <Option value={0}>Grado 0</Option>
                        <Option value={1}>Grado I</Option>
                        <Option value={2}>Grado II</Option>
                        <Option value={3}>Grado III</Option>
                      </Select>
                    </Form.Item>
                    <Form.Item name={['anexos', 'placenta_previa']} valuePropName="checked">
                      <Checkbox>Placenta Previa</Checkbox>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={12}>
                    <Title level={5}>Líquido Amniótico y Cordón</Title>
                    <Form.Item name={['anexos', 'liquido_amniotico_normal']} valuePropName="checked">
                      <Checkbox>Líquido Amniótico Normal</Checkbox>
                    </Form.Item>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item name="indice_liquido_amniotico" label="ILA (cm)">
                          <InputNumber step={0.1} style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item name="bolsillo_maximo" label="Bolsillo Máx (cm)">
                          <InputNumber step={0.1} style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Form.Item name={['anexos', 'numero_vasos_cordon']} label="Vasos del Cordón">
                      <Radio.Group>
                        <Radio value={3}>3 Vasos</Radio>
                        <Radio value={2}>2 Vasos (AUU)</Radio>
                      </Radio.Group>
                    </Form.Item>
                    <Form.Item name={['anexos', 'circular_cordon']} valuePropName="checked">
                      <Checkbox>Circular de Cordón</Checkbox>
                    </Form.Item>
                  </Col>
                </Row>
                <Divider />
                <Row gutter={24}>
                  <Col xs={24} md={12}>
                    <Form.Item name={['anexos', 'longitud_cervical']} label="Longitud Cervical (mm)">
                      <InputNumber style={{ width: '100%' }} />
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </TabPane>

            {/* TAB 5: IMÁGENES Y CONCLUSIONES */}
            <TabPane
              tab={tabImagenesConclusiones}
              key="5"
            >
              <Card className="shadow-sm" title="Imágenes de la Ecografía" style={{ marginBottom: 24 }}>
                <Upload {...uploadProps}>
                  <div>
                    <UploadOutlined style={{ fontSize: 24 }} />
                    <div style={{ marginTop: 8 }}>Click o arrastrar para subir</div>
                  </div>
                </Upload>
              </Card>

              <Card
                className="shadow-sm"
                title={
                  <Space>
                    <FileTextOutlined />
                    Conclusiones del Estudio
                  </Space>
                }
                extra={
                  <Tooltip title="Vista previa del diagnóstico">
                    <Button
                      type="text"
                      icon={EYE_ICON_3}
                      onClick={() => {
                        const diagnostico = form.getFieldValue('diagnostico');
                        const observaciones = form.getFieldValue('observaciones');
                        Modal.info({
                          title: 'Vista Previa de Conclusiones',
                          width: 600,
                          content: (
                            <div>
                              <div style={{ marginBottom: 16 }}>
                                <Text strong>Diagnóstico Ecográfico:</Text>
                                <div style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                                  <Text>{diagnostico || 'No se ha registrado diagnóstico aún...'}</Text>
                                </div>
                              </div>
                              <div>
                                <Text strong>Observaciones y Recomendaciones:</Text>
                                <div style={{ marginTop: 8, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                                  <Text>{observaciones || 'No se han registrado observaciones...'}</Text>
                                </div>
                              </div>
                            </div>
                          ),
                        });
                      }}
                    >
                      Vista Previa
                    </Button>
                  </Tooltip>
                }
              >
                <Form.Item name="diagnostico" label="Diagnóstico Ecográfico" rules={[{ required: true, message: 'Requerido' }]}>
                  <TextArea rows={4} placeholder="Ej: Embarazo de 20 semanas con biometría acorde..." />
                </Form.Item>

                <Form.Item name="observaciones" label="Observaciones y Recomendaciones">
                  <TextArea rows={3} />
                </Form.Item>

                <Row gutter={24}>
                  <Col xs={24} md={8}>
                    <Form.Item name="requiere_seguimiento" valuePropName="checked">
                      <Checkbox>Requiere Seguimiento Especial</Checkbox>
                    </Form.Item>
                  </Col>
                  <Col xs={24} md={8}>
                    <Form.Item
                      name="proxima_ecografia_recomendada"
                      label="Próxima Ecografía Sugerida"
                      tooltip="Seleccione una fecha y use el botón para agendar automáticamente"
                    >
                      <Space.Compact style={{ width: '100%' }}>
                        <DatePicker style={{ width: '70%' }} format="DD/MM/YYYY" />
                        <Tooltip title="Agendar cita en el calendario">
                          <Button
                            icon={CALENDAR_ICON_6}
                            onClick={handleCrearCita}
                            style={{ width: '30%' }}
                          >
                            Agendar
                          </Button>
                        </Tooltip>
                      </Space.Compact>
                    </Form.Item>
                  </Col>
                </Row>
              </Card>
            </TabPane>

          </Tabs>
        </Form>
      </Space>

      {/* MODAL DE VISTA PREVIA DE IMÁGENES */}
      <Modal
        open={previewVisible}
        title={previewTitle}
        footer={null}
        onCancel={handleCancelPreview}
        width="80%"
        style={{ top: 20 }}
        bodyStyle={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '24px',
          maxHeight: '80vh',
          overflow: 'auto',
        }}
      >
        <img
          alt={previewTitle}
          style={{
            width: '100%',
            maxWidth: '100%',
            height: 'auto',
            objectFit: 'contain',
          }}
          src={previewImage}
        />
      </Modal>
    </div>
  );
};

export default FormularioEcografia;

