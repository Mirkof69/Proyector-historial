/**
 * =============================================================================
 * GESTIÓN DE PARTOS - LISTADO PRINCIPAL
 * =============================================================================
 * Vista principal para la gestión de registros de partos: listado paginado,
 * filtros, estadísticas rápidas y acceso a crear/editar/detalle.
 * Stats, toolbar y columnas viven en ./components.
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { Alert, Table, Card, Button, Typography } from "antd";
import { WarningOutlined, PlusOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { partosService, Parto } from '../../services/partosService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { usePermissions } from '../../hooks/usePermissions';
import { aQuery, contarEnServidor, limpiarFiltros, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import { filtrosPartosReducer } from './components/partosFiltrosReducer';
import { buildPartosColumns } from './components/partosColumns';
import PartosStats from './components/PartosStats';
import PartosToolbar from './components/PartosToolbar';
import './Partos.css';

const { Title, Text } = Typography;

const CESAREAS = 'cesarea_electiva,cesarea_urgencia,cesarea_emergencia';
const VAGINALES = 'vaginal_espontaneo,vaginal_instrumentado';

const Partos: React.FC = () => {
  const { message, modal } = useAntdApp();
  const navigate = useNavigate();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [filtros, dispatchFiltros] = useReducer(filtrosPartosReducer, {
    searchText: '',
    dateRange: null,
    tipoPartoFilter: null,
  });
  const [stats, setStats] = useState({ total: 0, cesareas: 0, vaginales: 0 });

  // Búsqueda, fechas y tipo los filtra el SERVIDOR: antes se bajaban todos los
  // partos en bucle y se filtraba en el navegador.
  const filtrosServidor = useMemo(() => ({
    tipo_parto: filtros.tipoPartoFilter,
    fecha_parto__gte: filtros.dateRange?.[0].startOf('day').toISOString(),
    fecha_parto__lte: filtros.dateRange?.[1].endOf('day').toISOString(),
  }), [filtros.tipoPartoFilter, filtros.dateRange]);

  const listado = useListadoServidor<Parto>('/partos/', {
    filtros: filtrosServidor, busqueda: filtros.searchText, ordenInicial: '-fecha_parto',
  });

  const cargarStats = async () => {
    try {
      const [total, cesareas, vaginales] = await Promise.all([
        contarEnServidor('/partos/'),
        contarEnServidor('/partos/', { tipo_parto__in: CESAREAS }),
        contarEnServidor('/partos/', { tipo_parto__in: VAGINALES }),
      ]);
      setStats({ total, cesareas, vaginales });
    } catch {
      // Las cifras de cabecera no deben impedir usar el listado.
    }
  };
  useEffect(() => { cargarStats(); }, []);

  const recargar = () => { listado.recargar(); cargarStats(); };

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleCreate = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS_CREAR);
  };

  const handleEdit = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS_EDITAR(id));
  };

  const handleView = (id: number) => {
    navigate(FRONTEND_ROUTES.DASHBOARD.PARTOS_DETALLE(id));
  };

  const handleDelete = (parto: any) => {
    modal.confirm({
      title: '¿Confirmar eliminación permanente del parto?',
      icon: <WarningOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará el parto:</strong></p>
          <ul className="partos-borrado__lista">
            <li>Paciente: {parto.paciente_nombre}</li>
            <li>Fecha: {parto.fecha_parto}</li>
            <li>Tipo: {parto.tipo_parto_display}</li>
          </ul>
          <p className="partos-borrado__advertencia">
            ADVERTENCIA: Esta acción eliminará PERMANENTEMENTE:
          </p>
          <ul className="partos-borrado__lista partos-borrado__lista--peligro">
            <li>Registro completo del parto</li>
            <li>Datos de todos los recién nacidos</li>
            <li>Registros del partograma</li>
            <li>Complicaciones y observaciones</li>
          </ul>
          <p className="partos-arriba">
            <strong>Esta acción NO se puede deshacer.</strong>
          </p>
        </div>
      ),
      okText: 'Sí, eliminar permanentemente',
      okType: 'danger',
      cancelText: 'Cancelar',
      width: 600,
      onOk: async () => {
        try {
          await partosService.delete(parto.id);
          message.success('Registro eliminado correctamente');
          recargar();
        } catch (error) {
          message.error('Error al eliminar el registro');
        }
      },
    });
  };

  const handleExportExcel = async () => {
    // El Excel lo arma el servidor con TODOS los partos que cumplen los
    // filtros, no solo la página visible (y queda auditado).
    const params = { ...limpiarFiltros(filtrosServidor), ...(filtros.searchText ? { search: filtros.searchText } : {}) };
    try {
      await descargarArchivo(`/partos/exportar-excel/${aQuery(params)}`, `partos_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`);
    } catch {
      message.error('No se pudo generar el Excel de partos');
    }
  };

  const columns = buildPartosColumns(canChange, canDelete, handleView, handleEdit, handleDelete);

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="partos-page page-container">
      <header className="partos-page__cabecera">
        <div>
          <Title level={2}>Partos</Title>
          <Text type="secondary">Registro de partos, abortos y recién nacidos.</Text>
        </div>
        {canAdd('parto') && (
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            Registrar Nuevo Parto
          </Button>
        )}
      </header>

      {/* ESTADÍSTICAS */}
      <PartosStats total={stats.total} cesareas={stats.cesareas} vaginales={stats.vaginales} />

      {/* BARRA DE HERRAMIENTAS */}
      <PartosToolbar
        filtros={filtros}
        dispatchFiltros={dispatchFiltros}
        onReload={recargar}
        onExport={handleExportExcel}
      />

      {/* TABLA PRINCIPAL */}
      <Card>
        {listado.error && <Alert type="error" showIcon message={listado.error} className="partos-separado-sm" />}
        <Table
          columns={columns}
          dataSource={listado.datos}
          rowKey="id"
          loading={listado.cargando}
          pagination={listado.paginacion}
          onChange={listado.onChange}
          locale={{
            emptyText: 'No hay registros de partos',
          }}
          scroll={{ x: 1100 }}
        />
      </Card>
    </div>
  );
};

export default Partos;
