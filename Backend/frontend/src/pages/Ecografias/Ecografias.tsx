/**
 * =============================================================================
 * ECOGRAFÍAS - LISTA COMPLETA
 * =============================================================================
 * Lista de todas las ecografías registradas en el sistema.
 * - Filtros por tipo y fecha, búsqueda por paciente/diagnóstico
 * - Paginación, orden, cifras y Excel resueltos EN EL SERVIDOR
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import {
  Empty,
  Card,
  Table,
  Button,
  Modal,
  Alert,
  Typography,
} from 'antd';
import {
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
import api from '../../services/api';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import '../Embarazos/paginaClinica.css';
import './Ecografias.css';
import { filtrosEcografiaReducer } from './ecografiasUtils';
import { buildColumnsEcografias } from './ecografiasColumns';
import EcografiasStats from './components/EcografiasStats';
import EcografiasFiltros from './components/EcografiasFiltros';
import EcografiaVistaRapidaDrawer from './components/EcografiaVistaRapidaDrawer';

const { Title } = Typography;

const URL_ECOGRAFIAS = '/ecografias/';

interface ResumenEcografias {
  total: number;
  primer_trimestre: number;
  segundo_trimestre: number;
  tercer_trimestre: number;
}
const RESUMEN_VACIO: ResumenEcografias = { total: 0, primer_trimestre: 0, segundo_trimestre: 0, tercer_trimestre: 0 };

const Ecografias: React.FC = () => {
  const { message, modal } = useAntdApp();
  const navigate = useNavigate();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [filtros, dispatchFiltros] = useReducer(filtrosEcografiaReducer, {
    busqueda: '',
    filtroTipo: '',
    filtroFecha: null,
  });
  const [drawerVistaRapidaVisible, setDrawerVistaRapidaVisible] = useState(false);
  const [ecografiaSeleccionada, setEcografiaSeleccionada] = useState<Ecografia | null>(null);
  const [dicomViewerVisible, setDicomViewerVisible] = useState(false);

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  // Antes se descargaban TODAS las ecografías (una petición por cada 200) y
  // se filtraba y contaba en el navegador. Ahora se pide solo la página
  // visible; filtros, búsqueda (que entiende los nombres cifrados) y orden
  // los resuelve el servidor. `fecha_ecografia` es un DateField: va como
  // fecha local YYYY-MM-DD (un ISO en UTC correría al día siguiente el
  // extremo «hasta»).
  const filtrosServidor = useMemo(() => ({
    tipo_ecografia: filtros.filtroTipo || undefined,
    fecha_ecografia__gte: filtros.filtroFecha?.[0]?.format('YYYY-MM-DD'),
    fecha_ecografia__lte: filtros.filtroFecha?.[1]?.format('YYYY-MM-DD'),
  }), [filtros.filtroTipo, filtros.filtroFecha]);

  // Sin `ordenInicial`: el orden por defecto del servidor (fecha desc + id)
  // desempata y no repite filas entre páginas; `?ordering=` lo reemplazaría.
  const listado = useListadoServidor<Ecografia>(URL_ECOGRAFIAS, {
    filtros: filtrosServidor, busqueda: filtros.busqueda, tamanoInicial: 10,
  });
  const { parametros, recargar } = listado;

  // Las tarjetas cuentan TODAS las ecografías que cumplen los filtros, no
  // solo la página visible.
  const [resumen, setResumen] = useState<ResumenEcografias>(RESUMEN_VACIO);
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get(`${URL_ECOGRAFIAS}resumen/`, { params: parametros() });
      setResumen(r.data);
    } catch {
      // Las cifras de cabecera no deben impedir usar el listado.
      setResumen(RESUMEN_VACIO);
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);

  const cargarEcografias = useCallback(() => {
    recargar();
    cargarResumen();
  }, [recargar, cargarResumen]);

  const estadisticas = {
    total: resumen.total,
    primerTrimestre: resumen.primer_trimestre,
    segundoTrimestre: resumen.segundo_trimestre,
    tercerTrimestre: resumen.tercer_trimestre,
  };

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

  // NUEVA FUNCIÓN PARA VISTA RÁPIDA CON DRAWER
  const handleVerVistaRapida = (ecografia: Ecografia) => {
    setEcografiaSeleccionada(ecografia);
    setDrawerVistaRapidaVisible(true);
  };

  const handleEditar = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(id));
  };

  const handleEliminar = (ecografia: any) => {
    modal.confirm({
      className: 'capa-clinica',
      title: '¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará la ecografía:</strong></p>
          <ul className="u-ml-5">
            <li>Paciente: {ecografia.paciente_nombre || 'No especificado'}</li>
            <li>Fecha: {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}</li>
            <li>Tipo: {ecografia.tipo_ecografia || 'No especificado'}</li>
            <li>Edad Gestacional: {ecografia.edad_gestacional_semanas || 0}+{ecografia.edad_gestacional_dias || 0} semanas</li>
          </ul>
          <p className="u-c-peligro u-fuerte u-mt-4">
            ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p className="u-mt-4">
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

  const handleExportExcel = async () => {
    // El Excel lo arma el servidor con TODAS las ecografías que cumplen los
    // filtros (no solo la página visible) y queda auditado. Antes había dos
    // botones: uno exportaba en el navegador todo SIN filtros y el otro una
    // vista sin auditar.
    try {
      await descargarArchivo(`${URL_ECOGRAFIAS}exportar-excel/${aQuery(parametros())}`,
        `ecografias_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`);
    } catch {
      message.error('No se pudo generar el Excel de ecografías');
    }
  };

  // ==========================================================================
  // COLUMNAS DE LA TABLA
  // ==========================================================================
  const columns = buildColumnsEcografias({
    handleVerVistaRapida, handleEditar, handleEliminar, canChange, canDelete,
    handleDescargarPdf: (id: number) => {
      ecografiasService.descargarPdf(id)
        .catch(() => message.error('No se pudo generar el PDF de la ecografía.'));
    },
  });

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="pagina-clinica ecografias-page page-container">
      {/* ENCABEZADO DE PÁGINA */}
      <div className="pc-cabecera">
        <div className="pc-cabecera__texto">
          <Title level={2} className="pc-cabecera__titulo">
            <FileImageOutlined className="pc-cabecera__icono" />
            Ecografías Registradas
          </Title>
          <p className="pc-cabecera__descripcion">
            Estudios ecográficos obstétricos por trimestre, con biometría e imágenes.
          </p>
        </div>
        <div className="pc-cabecera__acciones">
          <Button icon={<ReloadOutlined />} onClick={cargarEcografias}>
            Actualizar
          </Button>
          <Button
            icon={<FileExcelOutlined />}
            onClick={handleExportExcel}
          >
            Exportar Excel
          </Button>
          <Button
            icon={<FileImageOutlined />}
            onClick={() => setDicomViewerVisible(true)}
          >
            Visor DICOM
          </Button>
          {canAdd('ecografia') && (
            <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
              Nueva Ecografía
            </Button>
          )}
        </div>
      </div>

      {/* ESTADÍSTICAS */}
      <EcografiasStats estadisticas={estadisticas} />

      {/* TABLA */}
      <Card>
        {/* FILTROS */}
        <EcografiasFiltros filtros={filtros} dispatchFiltros={dispatchFiltros} limpiarFiltros={limpiarFiltros} />

        {listado.error && (
          <Alert
            type="error"
            showIcon
            message="Error al cargar las ecografías"
            description={listado.error}
            action={
              <Button size="small" icon={<ReloadOutlined />} onClick={cargarEcografias}>
                Reintentar
              </Button>
            }
            className="u-mb-4"
          />
        )}

        <Table
          columns={columns}
          dataSource={listado.datos}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay ecografías registradas" /> }}
          rowKey="id"
          loading={listado.cargando}
          pagination={listado.paginacion}
          onChange={listado.onChange}
          scroll={{ x: 1200 }}
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

      {/* MODAL CON VISOR DICOM */}
      <Modal rootClassName="capa-clinica"
        title="Visor de Imágenes DICOM"
        open={dicomViewerVisible}
        onCancel={() => setDicomViewerVisible(false)}
        width={1400}
        footer={null}
        className="ecografias-modal-alto"
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

    </div>
  );
};

export default Ecografias;
