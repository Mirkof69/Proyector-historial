/**
 * =============================================================================
 * LABORATORIO - LISTA COMPLETA
 * =============================================================================
 * Lista de todos los exámenes de laboratorio registrados
 * Con filtros avanzados, estadísticas y alertas
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import { Alert, Empty, Card, Table, Button, Space, Typography } from 'antd';
import './Laboratorio.css';
import {
  PlusOutlined, ReloadOutlined,
  ExclamationCircleOutlined, FileExcelOutlined, UploadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { laboratorioService, ExamenLaboratorio } from '../../services/laboratorioService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { useAntdApp } from '../../hooks/useMessage';
import api from '../../services/api';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import { filtrosReducer } from './components/laboratorioFiltrosReducer';
import LaboratorioStats from './components/LaboratorioStats';
import LaboratorioFiltros from './components/LaboratorioFiltros';
import { buildLaboratorioColumns } from './components/laboratorioColumns';
import ImportarLaboratorioModal from './components/ImportarLaboratorioModal';

const URL_EXAMENES = '/laboratorios/examenes/';
const RESUMEN_VACIO = { total: 0, solicitados: 0, en_proceso: 0, completados: 0, con_anormales: 0, con_criticos: 0 };

const Laboratorio: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [importando, setImportando] = useState(false);
  const [filtros, dispatchFiltros] = useReducer(filtrosReducer, {
    busqueda: '',
    filtroCategoria: undefined,
    filtroEstado: undefined,
    filtroFecha: null,
  });

  // Todo lo filtra y cuenta el SERVIDOR. Antes los exámenes se guardaban en
  // un `ref` que no volvía a pintar: la tabla quedaba vacía y las cifras en 0
  // hasta tocar un filtro.
  const filtrosServidor = useMemo(() => ({
    categoria: filtros.filtroCategoria,
    estado: filtros.filtroEstado,
    fecha_desde: filtros.filtroFecha?.[0]?.startOf('day').toISOString(),
    fecha_hasta: filtros.filtroFecha?.[1]?.endOf('day').toISOString(),
  }), [filtros.filtroCategoria, filtros.filtroEstado, filtros.filtroFecha]);

  const listado = useListadoServidor<ExamenLaboratorio>(URL_EXAMENES, {
    filtros: filtrosServidor, busqueda: filtros.busqueda, tamanoInicial: 10, ordenInicial: '-fecha_solicitud',
  });
  const { parametros, recargar } = listado;

  const [estadisticas, setEstadisticas] = useState(RESUMEN_VACIO);
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get(`${URL_EXAMENES}resumen/`, { params: parametros() });
      setEstadisticas(r.data);
    } catch {
      setEstadisticas(RESUMEN_VACIO);
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);

  const cargarExamenes = useCallback(() => {
    recargar();
    cargarResumen();
  }, [recargar, cargarResumen]);

  const limpiarFiltros = useCallback(() => {
    dispatchFiltros({ type: 'LIMPIAR' });
  }, []);

  // ==========================================================================
  // ACCIONES
  // ==========================================================================
  const handleNuevo = useCallback(() => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_NUEVO);
  }, [navigate]);

  const handleVer = useCallback((id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_DETALLE(id));
  }, [navigate]);

  const handleEditar = useCallback((id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.LABORATORIO_EDITAR(id));
  }, [navigate]);

  const handleEliminar = useCallback((examen: any) => {
    modal.confirm({
      title: '¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará el examen de laboratorio:</strong></p>
          <ul className="laboratorio-modal__lista">
            <li>Paciente: {examen.paciente_nombre || 'No especificado'}</li>
            <li>Tipo de Examen: {examen.tipo_examen_nombre || 'No especificado'}</li>
            <li>Fecha Solicitud: {examen.fecha_solicitud ? dayjs(examen.fecha_solicitud).format('DD/MM/YYYY') : 'No especificado'}</li>
          </ul>
          <p className="laboratorio-modal__advertencia">
            ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p className="laboratorio-arriba">
            Se perderán todos los datos de este examen de laboratorio, incluyendo resultados, valores de referencia e interpretaciones.
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await laboratorioService.delete(examen.id);
          message.success('Examen eliminado correctamente');
          cargarExamenes();
        } catch (error) {
          message.error('Error al eliminar el examen');
        }
      },
    });
  }, [modal, message, cargarExamenes]);

  const handleExportExcel = useCallback(async () => {
    // El servidor arma el Excel con TODOS los exámenes filtrados (auditado).
    try {
      await descargarArchivo(`${URL_EXAMENES}exportar-excel/${aQuery(parametros())}`,
        `laboratorio_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`);
    } catch {
      message.error('No se pudo generar el Excel de laboratorio');
    }
  }, [parametros, message]);

  const columns = useMemo(
    () => buildLaboratorioColumns(canChange, canDelete, handleVer, handleEditar, handleEliminar),
    [canChange, canDelete, handleVer, handleEditar, handleEliminar]
  );

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="laboratorio-page page-container">
      <header className="laboratorio-page__cabecera">
        <div>
          <Typography.Title level={2}>Exámenes de Laboratorio</Typography.Title>
          <Typography.Text type="secondary">Solicitudes, resultados y valores fuera de rango de cada paciente.</Typography.Text>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={cargarExamenes}>
            Actualizar
          </Button>
          <Button icon={<FileExcelOutlined />} onClick={handleExportExcel}>
            Exportar Excel
          </Button>
          {canAdd('examenlaboratorio') && (
            <Button icon={<UploadOutlined />} onClick={() => setImportando(true)}>
              Importar Excel o CSV
            </Button>
          )}
          {canAdd('examenlaboratorio') && (
            <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
              Nuevo Examen
            </Button>
          )}
        </Space>
      </header>

      {/* ESTADÍSTICAS */}
      <LaboratorioStats
        total={estadisticas.total}
        solicitados={estadisticas.solicitados}
        en_proceso={estadisticas.en_proceso}
        completados={estadisticas.completados}
        con_anormales={estadisticas.con_anormales}
        con_criticos={estadisticas.con_criticos}
      />

      {/* TABLA */}
      <Card>
        {/* FILTROS */}
        <LaboratorioFiltros
          filtros={filtros}
          dispatchFiltros={dispatchFiltros}
          onLimpiar={limpiarFiltros}
        />

        {listado.error && <Alert type="error" showIcon message={listado.error} className="laboratorio-separado-sm" />}
        <Table
          columns={columns}
          dataSource={listado.datos}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay exámenes de laboratorio registrados" /> }}
          rowKey="id"
          loading={listado.cargando}
          pagination={listado.paginacion}
          onChange={listado.onChange}
          scroll={{ x: 1300 }}
        />
      </Card>
      <ImportarLaboratorioModal
        open={importando}
        onClose={() => setImportando(false)}
        onImportado={cargarExamenes}
      />
    </div>
  );
};

export default Laboratorio;
