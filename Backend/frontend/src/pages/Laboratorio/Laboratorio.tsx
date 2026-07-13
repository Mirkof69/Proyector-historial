/**
 * =============================================================================
 * LABORATORIO - LISTA COMPLETA
 * =============================================================================
 * Lista de todos los exámenes de laboratorio registrados
 * Con filtros avanzados, estadísticas y alertas
 * =============================================================================
 */

import React, { useRef, useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePermissions } from '../../hooks/usePermissions';
import { Card, Table, Button, Space } from 'antd';
import {
  PlusOutlined, ReloadOutlined, ExperimentOutlined,
  ExclamationCircleOutlined, FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { laboratorioService, ExamenLaboratorio } from '../../services/laboratorioService';
import { FRONTEND_ROUTES } from '../../config/routes';
import { exportarExcel } from '../../utils/excelExport';
import { useAntdApp } from '../../hooks/useMessage';
import { GlobalLoader } from '../../components/common/GlobalLoader';
import { filtrosReducer } from './components/laboratorioFiltrosReducer';
import LaboratorioStats from './components/LaboratorioStats';
import LaboratorioFiltros from './components/LaboratorioFiltros';
import { buildLaboratorioColumns } from './components/laboratorioColumns';

const Laboratorio: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [loading, setLoading] = useState(false);
  const examenesRef = useRef<ExamenLaboratorio[]>([]);
  const [filtros, dispatchFiltros] = useReducer(filtrosReducer, {
    busqueda: '',
    filtroCategoria: undefined,
    filtroEstado: undefined,
    filtroFecha: null,
  });

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================

  const calcularEstadisticas = useCallback((data: ExamenLaboratorio[]) => {
    return {
      total: data.length,
      solicitados: data.filter((e) => e.estado === 'solicitado').length,
      en_proceso: data.filter((e) => e.estado === 'en_proceso').length,
      completados: data.filter((e) => e.estado === 'completado').length,
      con_anormales: data.filter((e) => e.resultados_anormales && e.resultados_anormales > 0).length,
      con_criticos: data.filter((e) => e.resumen && e.resumen.criticos > 0).length,
    };
  }, []);

  const estadisticas = useMemo(() => calcularEstadisticas(examenesRef.current), [calcularEstadisticas]);

  const cargarExamenes = useCallback(async () => {
    setLoading(true);

    try {

      // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
      const firstPage = await laboratorioService.api.get('/laboratorios/examenes/?page=1&limit=200');

      const totalCount = firstPage.data.count || 0;
      const totalPages = Math.ceil(totalCount / 200);


      // 🚀 PASO 2: Crear array de promesas para TODAS las páginas
      const promises = Array.from({ length: totalPages }, (_, i) =>
        laboratorioService.api.get(`/laboratorios/examenes/?page=${i + 1}&limit=200`)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const responses = await Promise.all(promises);

      // 🚀 PASO 4: Combinar todos los resultados y agregar rowKey único
      let index = 0;
      const allExamenes = [];
      for (const res of responses) {
        const results = res.data.results || [];
        for (const item of results) {
          allExamenes.push({
            ...item,
            _uniqueRowKey: `laboratorio-${item.id}-${index}-${Date.now()}`
          });
          index++;
        }
      }

      examenesRef.current = allExamenes;
    } catch (error) {
      message.error('Error al cargar los exámenes de laboratorio');
      examenesRef.current = [];
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarExamenes();
  }, [cargarExamenes]);

  // ==========================================================================
  // FILTROS
  // ==========================================================================
  const examenesFiltrados = useMemo(() => {
    let resultado = [...examenesRef.current];

    if (filtros.busqueda) {
      resultado = resultado.filter(
        (examen) =>
          examen.paciente_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          examen.tipo_examen_nombre?.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
          examen.indicaciones?.toLowerCase().includes(filtros.busqueda.toLowerCase())
      );
    }

    if (filtros.filtroCategoria) {
      resultado = resultado.filter((examen) => examen.categoria === filtros.filtroCategoria);
    }

    if (filtros.filtroEstado) {
      resultado = resultado.filter((examen) => examen.estado === filtros.filtroEstado);
    }

    if (filtros.filtroFecha) {
      resultado = resultado.filter((examen) => {
        const fecha = dayjs(examen.fecha_solicitud);
        return fecha.isAfter(filtros.filtroFecha![0]) && fecha.isBefore(filtros.filtroFecha![1]);
      });
    }

    return resultado;
  }, [filtros]);

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
      title: '⚠️ ¿Confirmar eliminación permanente?',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará el examen de laboratorio:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {examen.paciente_nombre || 'No especificado'}</li>
            <li>Tipo de Examen: {examen.tipo_examen_nombre || 'No especificado'}</li>
            <li>Fecha Solicitud: {examen.fecha_solicitud ? dayjs(examen.fecha_solicitud).format('DD/MM/YYYY') : 'No especificado'}</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción es permanente y NO se puede deshacer.
          </p>
          <p style={{ marginTop: 16 }}>
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

  const handleExportExcel = useCallback(() => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'tipo_examen_nombre': 'Tipo Examen',
        'fecha_solicitud': 'Fecha Solicitud',
        'hemoglobina': 'Hemoglobina',
        'hematocrito': 'Hematocrito',
        'glucosa': 'Glucosa',
        'grupo_sanguineo': 'Grupo Sang.',
        'factor_rh': 'RH',
        'vih': 'VIH',
        'vdrl': 'VDRL',
        'orina_proteinas': 'Proteínas',
        'observaciones': 'Observaciones'
      };

      exportarExcel(
        examenesFiltrados,
        columnas,
        {
          filename: `laboratorio_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Laboratorio',
          title: `Exámenes de Laboratorio - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  }, [examenesFiltrados, message]);

  const columns = useMemo(
    () => buildLaboratorioColumns(canChange, canDelete, handleVer, handleEditar, handleEliminar),
    [canChange, canDelete, handleVer, handleEditar, handleEliminar]
  );

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading && examenesRef.current.length === 0) {
    return <GlobalLoader tip="Cargando exámenes de laboratorio…" />;
  }

  return (
    <div className="laboratorio-container animate-fade-in">
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
      <Card
        title={
          <Space>
            <ExperimentOutlined style={{ fontSize: 24, color: '#722ed1' }} />
            <span>Exámenes de Laboratorio</span>
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ReloadOutlined />} onClick={cargarExamenes}>
              Actualizar
            </Button>
            <Button icon={<FileExcelOutlined />} onClick={handleExportExcel}>
              Exportar Excel
            </Button>
            {canAdd('examen') && (
              <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevo}>
                Nuevo Examen
              </Button>
            )}
          </Space>
        }
      >
        {/* FILTROS */}
        <LaboratorioFiltros
          filtros={filtros}
          dispatchFiltros={dispatchFiltros}
          onLimpiar={limpiarFiltros}
        />

        <Table
          columns={columns}
          dataSource={examenesFiltrados}
          rowKey={(record: any) => record._uniqueRowKey || `laboratorio-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} exámenes`,
          }}
          scroll={{ x: 1300 }}
          bordered
        />
      </Card>
    </div>
  );
};

export default Laboratorio;
