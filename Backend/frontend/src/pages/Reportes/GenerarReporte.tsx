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
  Button,
  Space,
  Divider,
  Typography,
  Steps,
} from "antd";
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  SettingOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { reportesService, TipoReporteConfig } from '../../services/reportesService';
import { FRONTEND_ROUTES } from '../../config/routes';
import './GenerarReporte.css';
import { FormValues } from './generarReporteUtils';
import PasoTipoReporte from './components/PasoTipoReporte';
import PasoConfiguracion from './components/PasoConfiguracion';
import PasoVistaPrevia from './components/PasoVistaPrevia';
import PasoGeneracion from './components/PasoGeneracion';

const { Step } = Steps;

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
          {pasoActual === 0 && (
            <PasoTipoReporte
              cargandoTipos={cargandoTipos}
              tiposReporte={tiposReporte}
              tipoSeleccionado={tipoSeleccionado}
              handleTipoReporteChange={handleTipoReporteChange}
            />
          )}
          {pasoActual === 1 && <PasoConfiguracion tipoDetalle={tipoDetalle} />}
          {pasoActual === 2 && <PasoVistaPrevia loading={loading} vistaPrevia={vistaPrevia} />}
          {pasoActual === 3 && (
            <PasoGeneracion
              generando={generando}
              progresoGeneracion={progresoGeneracion}
              reporteGenerado={reporteGenerado}
              handleDescargarReporte={handleDescargarReporte}
              handleGenerarOtro={handleGenerarOtro}
              handleVolver={handleVolver}
            />
          )}
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
