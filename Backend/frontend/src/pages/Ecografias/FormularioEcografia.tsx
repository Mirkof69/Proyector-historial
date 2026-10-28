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

import React, { useState, useEffect } from 'react';
import {
  Form,
  Button,
  Upload,
  Spin,
  Typography,
  Tabs,
  Space,
  Modal,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  SaveOutlined,
  ArrowLeftOutlined,
  FileImageOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  ScanOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { leerContextoClinico } from '../../components/clinico/SelectoresClinicos';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { embarazosService, Embarazo } from '../../services/embarazosService';
import { citasService } from '../../services/citasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAuth } from '../../hooks/useAuth';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { calcularEdadGestacional, getBase64 } from './ecografiaFormUtils';
import TabDatosGeneralesEco from './components/TabDatosGeneralesEco';
import TabBiometriaEco from './components/TabBiometriaEco';
import TabAnatomiaEco from './components/TabAnatomiaEco';
import TabAnexosEco from './components/TabAnexosEco';
import TabImagenesConclusionesEco from './components/TabImagenesConclusionesEco';
import '../Embarazos/paginaClinica.css';
import './Ecografias.css';

const { Title } = Typography;

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

const FormularioEcografia: React.FC = () => {
  // message del hook (no el estático de antd): respeta el tema dinámico
  const { message } = useAntdApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [busqueda] = useSearchParams();
  const isEditing = !!id;
  const [form] = Form.useForm();
  const { user } = useAuth();

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [selectedPaciente, setSelectedPaciente] = useState<number | null>(null);
  const [selectedEmbarazo, setSelectedEmbarazo] = useState<Embarazo | null>(null);
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [pestana, setPestana] = useState('1');
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  // ==========================================================================
  // CARGAR DATOS INICIALES
  // ==========================================================================
  // Desde la ficha de la paciente o del embarazo se llega con ?paciente= o
  // ?embarazo=: quedan elegidos y la edad gestacional se calcula sola.
  const aplicarContextoDeUrl = async () => {
    const { pacienteId, embarazoId } = leerContextoClinico(busqueda);
    try {
      let paciente = pacienteId;
      if (embarazoId && !paciente) {
        const e = await embarazosService.obtener(embarazoId);
        paciente = typeof e.paciente === 'object' ? (e.paciente as { id: number }).id : e.paciente;
      }
      if (!paciente) return;
      form.setFieldsValue({ paciente });
      setSelectedPaciente(paciente);
      const lista = (await embarazosService.getByPaciente(paciente)) as Embarazo[];
      setEmbarazos(lista);
      const elegido = embarazoId ?? lista.find((e) => e.estado === 'activo')?.id;
      if (elegido) {
        form.setFieldsValue({ embarazo: elegido });
        actualizarEdadGestacional(elegido, lista);
      }
    } catch {
      message.error('No se pudo cargar la paciente indicada');
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

  useEffect(() => {
    if (isEditing) {
      cargarEcografia(Number(id));
    } else {
      aplicarContextoDeUrl();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handlePacienteChange = (value: number | null) => {
    setSelectedPaciente(value);
    if (value) {
      cargarEmbarazos(value);
    } else {
      setEmbarazos([]);
      form.setFieldsValue({ embarazo: undefined });
    }
  };

  const actualizarEdadGestacional = (embarazoId?: number, lista: Embarazo[] = embarazos) => {
    // Obtener valores del formulario
    const idEmbarazo = embarazoId || form.getFieldValue('embarazo');
    let fechaEco = form.getFieldValue('fecha_ecografia');

    // Si no hay embarazo, no hacer nada
    if (!idEmbarazo) return;

    // Buscar el embarazo seleccionado
    const embarazoSeleccionado = lista.find(e => e.id === idEmbarazo);
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
    // El tipo por trimestre se sugiere según la EG mientras no se haya tocado
    // (antes quedaba «Primer trimestre» aunque el embarazo fuera de 20 semanas).
    if (!form.isFieldTouched('tipo_ecografia')) {
      const tipo = semanas < 14 ? 'primer_trimestre' : semanas < 28 ? 'segundo_trimestre' : 'tercer_trimestre';
      form.setFieldsValue({ tipo_ecografia: tipo });
    }

    // Mostrar mensaje de confirmación
    message.success(`Edad gestacional autocompletada: ${semanas}+${dias} semanas`, 3);
  };

  // ==========================================================================
  // SUBMIT
  // ==========================================================================
  // Si falta un dato en otra pestaña (p. ej. el Diagnóstico, en la última), antes
  // «Guardar» no hacía nada y no decía por qué: se va a esa pestaña y se avisa.
  const PESTANA_DE: Record<string, string> = { biometria: '2', anatomia: '3', anexos: '4', diagnostico: '5',
    conclusiones: '5', recomendaciones: '5', proxima_ecografia_recomendada: '5', observaciones: '5' };
  const onFinishFailed = ({ errorFields }: { errorFields: { name: (string | number)[]; errors: string[] }[] }) => {
    if (!errorFields.length) return;
    const primero = errorFields[0];
    setPestana(PESTANA_DE[String(primero.name[0])] ?? '1');
    setTimeout(() => form.scrollToField(primero.name, { block: 'center' }), 50);
    const etiquetas = errorFields.map((e) => {
      const el = document.querySelector(`label[for="${e.name.join('_')}"]`);
      return el?.textContent?.trim() || String(e.name[e.name.length - 1]).replace(/_/g, ' ');
    });
    message.error(`Falta completar: ${[...new Set(etiquetas)].join(', ')}`);
  };

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
        // El alta no recoge imágenes (antes se enviaban dentro del mismo POST y
        // se perdían sin aviso): se crea la ecografía y luego se sube cada
        // imagen por subir_imagen, que además valida el contenido del archivo.
        const { imagenes: _sinImagenes, ...datos } = ecografiaData;
        const creada = await ecografiasService.create(datos);
        const resultados = await Promise.allSettled(
          nuevasImagenes.map((img) => ecografiasService.addImagen(Number(creada.id), img)),
        );
        const fallidas = resultados.filter((r) => r.status === 'rejected').length;
        if (fallidas) {
          message.warning(`Ecografía registrada, pero ${fallidas} imagen(es) no se pudieron subir. Revise el formato.`);
        } else {
          message.success('Ecografía registrada correctamente');
        }
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
      strokeColor: 'var(--color-primario)',
      strokeWidth: 3,
      format: (percent) => `${Math.round(percent || 0)}%`,
    },
  };

  if (loading) {
    return <div className="pagina-clinica pc-cargando"><Spin size="large" /></div>;
  }

  return (
    <div className="pagina-clinica ecografias-formulario">
      <Space direction="vertical" size="large" className="u-ancho">
        {/* ENCABEZADO DE PÁGINA */}
        <div className="pc-cabecera u-mb-0">
          <div className="pc-cabecera__texto">
            <Title level={2} className="pc-cabecera__titulo">
              {isEditing ? 'Editar Ecografía' : 'Nueva Ecografía Obstétrica'}
            </Title>
            <p className="pc-cabecera__descripcion">
              Datos generales, biometría, anatomía, anexos e imágenes del estudio.
            </p>
          </div>
          <div className="pc-cabecera__acciones">
            <Button
              icon={ARROW_LEFT_ICON_5}
              onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS)}
            >
              Volver
            </Button>
            <Button
              type="primary"
              icon={SAVE_ICON_4}
              loading={submitting}
              onClick={() => form.submit()}
            >
              Guardar Ecografía
            </Button>
          </div>
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={onFinish}
          onFinishFailed={onFinishFailed}
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
          <Tabs
            activeKey={pestana}
            onChange={setPestana}
            type="card"
            size="large"
            items={[
              {
                key: '1',
                forceRender: true,
                label: tabDatosGenerales,
                children: (
                  <TabDatosGeneralesEco
                    embarazos={embarazos}
                    selectedPaciente={selectedPaciente}
                    selectedEmbarazo={selectedEmbarazo}
                    isEditing={isEditing}
                    handlePacienteChange={handlePacienteChange}
                    actualizarEdadGestacional={actualizarEdadGestacional}
                  />
                ),
              },
              {
                key: '2',
                forceRender: true,
                label: tabBiometriaFetal,
                children: <TabBiometriaEco />,
              },
              {
                key: '3',
                forceRender: true,
                label: tabAnatomiaFetal,
                children: <TabAnatomiaEco />,
              },
              {
                key: '4',
                forceRender: true,
                label: tabAnexosFetales,
                children: <TabAnexosEco />,
              },
              {
                key: '5',
                forceRender: true,
                label: tabImagenesConclusiones,
                children: (
                  <TabImagenesConclusionesEco
                    uploadProps={uploadProps}
                    form={form}
                    handleCrearCita={handleCrearCita}
                  />
                ),
              },
            ]}
          />
        </Form>
      </Space>

      {/* MODAL DE VISTA PREVIA DE IMÁGENES */}
      <Modal rootClassName="capa-clinica"
        open={previewVisible}
        title={previewTitle}
        footer={null}
        onCancel={handleCancelPreview}
        width="80%"
        className="ecografias-modal-alto eco-vista-previa"
      >
        <img
          alt={previewTitle}
          className="eco-vista-previa__imagen"
          src={previewImage}
        />
      </Modal>
    </div>
  );
};

export default FormularioEcografia;
