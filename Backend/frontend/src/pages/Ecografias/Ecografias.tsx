/**
 * =============================================================================
 * ECOGRAFÍAS - LISTA COMPLETA
 * =============================================================================
 * Lista de todas las ecografías registradas en el sistema.
 * - Filtros por tipo, trimestre, fecha
 * - Búsqueda por paciente
 * - Paginación y ordenamiento
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import { exportarExcel } from '../../utils/excelExport';
import {
  Empty,Card,
  Table,
  Button,
  Space,
  Modal,
  Row,
  Col,
  Alert} from 'antd';
import {
  EyeOutlined,
  EditOutlined,
  PlusOutlined,
  ReloadOutlined,
  FileImageOutlined,
  ExclamationCircleOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import DICOMViewer from '../../components/DICOMViewer';
import PDFGenerator from '../../components/PDFGenerator';
import { useAuth } from '../../hooks/useAuth';
import apiClient from '../../services/api';
import './Ecografias.css';
import { filtrosEcografiaReducer, calcularEstadisticas } from './ecografiasUtils';
import { buildColumnsEcografias } from './ecografiasColumns';
import EcografiasStats from './components/EcografiasStats';
import EcografiasFiltros from './components/EcografiasFiltros';
import EcografiaVistaRapidaDrawer from './components/EcografiaVistaRapidaDrawer';

const Ecografias: React.FC = () => {
  const { message, modal } = useAntdApp();
  const navigate = useNavigate();
  const { canAdd, canChange, canDelete } = usePermissions();
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ecografias, setEcografias] = useState<Ecografia[]>([]);
  const [filtros, dispatchFiltros] = useReducer(filtrosEcografiaReducer, {
    busqueda: '',
    filtroTipo: '',
    filtroFecha: null,
  });
  const [drawerVistaRapidaVisible, setDrawerVistaRapidaVisible] = useState(false);
  const [ecografiaSeleccionada, setEcografiaSeleccionada] = useState<Ecografia | null>(null);
  const [dicomViewerVisible, setDicomViewerVisible] = useState(false);
  const [pdfGeneratorVisible, setPdfGeneratorVisible] = useState(false);


  const estadisticas = useMemo(() => calcularEstadisticas(ecografias), [ecografias]);

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarEcografias = useCallback(async () => {
    setLoading(true);
    try {

      // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
      const firstPageResponse = await apiClient.get('/ecografias/', { params: { page: 1, limit: 200 } });
      const firstPageData = firstPageResponse.data;
      const totalEcografias = firstPageData.count || 0;
      const totalPages = Math.ceil(totalEcografias / 200);


      // 🚀 PASO 2: Crear array de promesas para TODAS las páginas
      const ecografiasPromises = Array.from({ length: totalPages }, (_, i) =>
        apiClient.get('/ecografias/', { params: { page: i + 1, limit: 200 } }).then(res => res.data)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const allResponses = await Promise.all(ecografiasPromises);

      // 🚀 PASO 4: Combinar todos los resultados y agregar _uniqueRowKey
      const allEcografias: any[] = [];
      for (const res of allResponses) {
        for (const item of res.results || []) {
          allEcografias.push({
            ...item,
            _uniqueRowKey: `ecografia-${item.id}-${allEcografias.length}-${Date.now()}`
          });
        }
      }

      setEcografias(allEcografias);
      setLoadError(null);
    } catch (error) {
      setLoadError('No se pudieron cargar las ecografías. Verifique su conexión e intente nuevamente.');
      setEcografias([]);
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    cargarEcografias();
  }, [cargarEcografias]);

  const ecografiasFiltradas = useMemo(() => {
    let resultado = [...ecografias];

    if (filtros.busqueda) {
      resultado = resultado.filter(
        (eco) =>
          eco.tipo_ecografia?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.paciente_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.diagnostico?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          eco.observaciones?.toLowerCase().includes(filtros.busqueda.toLowerCase())
      );
    }

    if (filtros.filtroTipo) {
      resultado = resultado.filter((eco) => eco.tipo_ecografia === filtros.filtroTipo);
    }

    if (filtros.filtroFecha) {
      resultado = resultado.filter((eco) => {
        const fecha = dayjs(eco.fecha_ecografia);
        return fecha.isAfter(filtros.filtroFecha![0]) && fecha.isBefore(filtros.filtroFecha![1]);
      });
    }

    return resultado;
  }, [filtros, ecografias]);

  const limpiarFiltros = () => {
    dispatchFiltros({ type: 'LIMPIAR' });
  };

  // ==========================================================================
  // ACCIONES
  // ==========================================================================
  const handleNuevo = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_NUEVO);
  };

  const handleVer = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_DETALLE(id));
  };

  // ✨ NUEVA FUNCIÓN PARA VISTA RÁPIDA CON DRAWER
  const handleVerVistaRapida = (ecografia: Ecografia) => {
    setEcografiaSeleccionada(ecografia);
    setDrawerVistaRapidaVisible(true);
  };

  const handleEditar = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(id));
  };

  const handleEliminar = (ecografia: any) => {
    modal.confirm({
      title: '⚠️ ¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará la ecografía:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {ecografia.paciente_nombre || 'No especificado'}</li>
            <li>Fecha: {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}</li>
            <li>Tipo: {ecografia.tipo_ecografia || 'No especificado'}</li>
            <li>Edad Gestacional: {ecografia.edad_gestacional_semanas || 0}+{ecografia.edad_gestacional_dias || 0} semanas</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p style={{ marginTop: 16 }}>
            Se perderán todos los datos de esta ecografía obstétrica, incluyendo mediciones fetales, diagnósticos y observaciones.
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await ecografiasService.delete(ecografia.id);
          message.success('Ecografía eliminada correctamente');
          cargarEcografias();
        } catch (error) {
          message.error('Error al eliminar la ecografía');
        }
      },
    });
  };

  const handleExportExcel = () => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'fecha_ecografia': 'Fecha',
        'tipo_ecografia': 'Tipo',
        'edad_gestacional_semanas': 'Semanas',
        'edad_gestacional_dias': 'Días',
        'peso_fetal_estimado': 'Peso Est. (g)',
        'biometria_dbp': 'DBP (mm)',
        'biometria_cc': 'CC (mm)',
        'biometria_ca': 'CA (mm)',
        'biometria_lf': 'LF (mm)',
        'liquido_amniotico': 'Líquido',
        'placenta_localizacion': 'Placenta',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        ecografias,
        columnas,
        {
          filename: `ecografias_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Ecografías',
          title: `Ecografías Obstétricas - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  };

  // ==========================================================================
  // COLUMNAS DE LA TABLA
  // ==========================================================================
  const columns = buildColumnsEcografias({ handleVerVistaRapida, handleEditar, handleEliminar, canChange, canDelete });

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="ecografias-container page-container">
      {/* ESTADÍSTICAS */}
      <EcografiasStats estadisticas={estadisticas} />

      {/* TABLA */}
      <Card
        title={
          <Space>
            <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span>Ecografías Registradas</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={cargarEcografias}>
              Actualizar
            </Button>
            <Button
              icon={<FileExcelOutlined />}
              onClick={handleExportExcel}
              style={{ backgroundColor: '#52c41a', color: 'white', borderColor: '#52c41a' }}
            >
              Exportar Excel
            </Button>
            <Button
              icon={<FileImageOutlined />}
              onClick={() => setDicomViewerVisible(true)}
              style={{ backgroundColor: '#722ed1', color: 'white', borderColor: '#722ed1' }}
            >
              🔬 Visor DICOM
            </Button>
            <Button
              icon={<FileImageOutlined />}
              onClick={() => setPdfGeneratorVisible(true)}
              style={{ backgroundColor: '#ff4d4f', color: 'white', borderColor: '#ff4d4f' }}
            >
              📄 Generar PDF
            </Button>
            {canAdd('ecografia') && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
                Nueva Ecografía
              </Button>
            )}
          </Space>
        }
      >
        {/* FILTROS */}
        <EcografiasFiltros filtros={filtros} dispatchFiltros={dispatchFiltros} limpiarFiltros={limpiarFiltros} />

        {loadError && (
          <Alert
            type="error"
            showIcon
            message="Error al cargar las ecografías"
            description={loadError}
            action={
              <Button size="small" icon={<ReloadOutlined />} onClick={cargarEcografias}>
                Reintentar
              </Button>
            }
            style={{ marginBottom: 16 }}
          />
        )}

        <Table
          columns={columns}
          dataSource={ecografiasFiltradas}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay ecografías registradas" /> }}
          rowKey={(record: any) => record._uniqueRowKey || `ecografia-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} ecografías`,
          }}
          scroll={{ x: 1200 }}
          bordered
        />
      </Card>

      {/* ========================================================================
          DRAWER DE VISTA RÁPIDA CON NAVEGACIÓN CROSS-MODULE
         ======================================================================== */}
      <EcografiaVistaRapidaDrawer
        drawerVistaRapidaVisible={drawerVistaRapidaVisible}
        setDrawerVistaRapidaVisible={setDrawerVistaRapidaVisible}
        ecografiaSeleccionada={ecografiaSeleccionada}
        handleVer={handleVer}
        navigate={navigate}
        canChange={canChange}
      />

      {/* ✨ MODAL CON VISOR DICOM */}
      <Modal
        title="Visor de Imágenes DICOM"
        open={dicomViewerVisible}
        onCancel={() => setDicomViewerVisible(false)}
        width={1400}
        footer={null}
        style={{ top: 20 }}
      >
        {ecografiaSeleccionada && (
          <DICOMViewer
            patientName={`Paciente ID: ${ecografiaSeleccionada.paciente}`}
            studyDate={ecografiaSeleccionada.fecha_ecografia}
            modality="US"
            imageUrl="/path-to-ultrasound-image.jpg"
          />
        )}
      </Modal>

      {/* ✨ MODAL CON GENERADOR DE PDF */}
      <PDFGenerator
        open={pdfGeneratorVisible}
        onCancel={() => setPdfGeneratorVisible(false)}
        pacienteData={ecografiaSeleccionada ? { id: ecografiaSeleccionada.paciente } : null}
        embarazoData={ecografiaSeleccionada ? { id: ecografiaSeleccionada.embarazo } : null}
        moduloOrigen="ecografias"
      />
    </div>
  );
};

export default Ecografias;
