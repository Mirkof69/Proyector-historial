/**
 * =============================================================================
 * GESTIÓN DE PARTOS - LISTADO PRINCIPAL
 * =============================================================================
 * Vista principal para la gestión de registros de partos: listado paginado,
 * filtros, estadísticas rápidas y acceso a crear/editar/detalle.
 * Stats, toolbar y columnas viven en ./components.
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import { Table, Card } from "antd";
import { WarningOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { partosService, Parto } from '../../services/partosService';
import { FRONTEND_ROUTES } from '../../config/routes';
import api from '../../services/api';
import { usePermissions } from '../../hooks/usePermissions';
import { exportarExcel } from '../../utils/excelExport';
import { filtrosPartosReducer } from './components/partosFiltrosReducer';
import { buildPartosColumns } from './components/partosColumns';
import PartosStats from './components/PartosStats';
import PartosToolbar from './components/PartosToolbar';
import './Partos.css';

const Partos: React.FC = () => {
  const { message, modal } = useAntdApp();
  const navigate = useNavigate();
  const { canAdd, canChange, canDelete } = usePermissions();
  const [loading, setLoading] = useState(false);
  const [partos, setPartos] = useState<Parto[]>([]);
  const [filtros, dispatchFiltros] = useReducer(filtrosPartosReducer, {
    searchText: '',
    dateRange: null,
    tipoPartoFilter: null,
  });
  const isMounted = useRef(true);

  const filteredPartos = useMemo(() => {
    let result = partos;

    if (filtros.searchText) {
      const lowerSearch = filtros.searchText.toLowerCase();
      result = result.filter((p) => {
        const pacienteNombre = p.paciente_info
          ? `${p.paciente_info.nombre} ${p.paciente_info.apellido_paterno} ${p.paciente_info.apellido_materno}`.toLowerCase()
          : '';
        const pacienteCI = p.paciente_info?.cedula_identidad?.toLowerCase() || '';
        const pacienteID = p.paciente_info?.id_clinico?.toLowerCase() || '';

        return (
          pacienteNombre.includes(lowerSearch) ||
          pacienteCI.includes(lowerSearch) ||
          pacienteID.includes(lowerSearch)
        );
      });
    }

    if (filtros.dateRange) {
      const [start, end] = filtros.dateRange;
      result = result.filter((p) => {
        const fechaParto = dayjs(p.fecha_parto);
        return fechaParto.isAfter(start.startOf('day')) && fechaParto.isBefore(end.endOf('day'));
      });
    }

    if (filtros.tipoPartoFilter) {
      result = result.filter((p) => p.tipo_parto === filtros.tipoPartoFilter);
    }

    return result;
  }, [partos, filtros]);

  useEffect(() => {
    isMounted.current = true;
    return () => { isMounted.current = false; };
  }, []);

  // ==========================================================================
  // CARGAR DATOS - OPTIMIZADA CON CARGA PARALELA
  // ==========================================================================
  const cargarPartos = useCallback(async () => {
    setLoading(true);

    try {

      // 🚀 PASO 1: Obtener primera página para saber cuántas páginas hay
      const firstPage = await api.get('/partos/?page=1&limit=200');

      const totalPartos = firstPage.data.count || 0;
      const totalPages = Math.ceil(totalPartos / 200);


      // 🚀 PASO 2: Crear array de promesas para TODAS las páginas
      const partosPromises = Array.from({ length: totalPages }, (_, i) =>
        api.get(`/partos/?page=${i + 1}&limit=200`)
      );

      // 🚀 PASO 3: Ejecutar TODAS las requests en PARALELO
      const partosResponses = await Promise.all(partosPromises);

      // 🚀 PASO 4: Combinar todos los resultados y agregar rowKey único
      const allPartos: any[] = [];
      for (const res of partosResponses) {
        for (const item of res.data.results || []) {
          allPartos.push({
            ...item,
            _uniqueRowKey: `parto-${item.id}-${allPartos.length}-${Date.now()}`
          });
        }
      }

      if (isMounted.current) {
        setPartos(allPartos);
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al cargar la lista de partos');
        setPartos([]);
      }
    } finally {
      if (isMounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarPartos();
  }, [cargarPartos]);

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
      title: '⚠️ ¿Confirmar eliminación permanente del parto?',
      icon: <WarningOutlined />,
      content: (
        <div>
          <p><strong>Se eliminará el parto:</strong></p>
          <ul style={{ marginLeft: 20 }}>
            <li>Paciente: {parto.paciente_nombre}</li>
            <li>Fecha: {parto.fecha_parto}</li>
            <li>Tipo: {parto.tipo_parto_display}</li>
          </ul>
          <p style={{ color: '#ff4d4f', fontWeight: 'bold', marginTop: 16 }}>
            ⚠️ ADVERTENCIA: Esta acción eliminará PERMANENTEMENTE:
          </p>
          <ul style={{ marginLeft: 20, color: '#ff4d4f' }}>
            <li>Registro completo del parto</li>
            <li>Datos de todos los recién nacidos</li>
            <li>Registros del partograma</li>
            <li>Complicaciones y observaciones</li>
          </ul>
          <p style={{ marginTop: 16 }}>
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
          cargarPartos();
        } catch (error) {
          message.error('Error al eliminar el registro');
        }
      },
    });
  };

  const handleExportExcel = () => {
    try {
      const columnas = {
        'id': 'ID',
        'paciente_nombre': 'Paciente',
        'fecha_parto': 'Fecha Parto',
        'tipo_parto_display': 'Tipo Parto',
        'edad_gestacional_semanas': 'Semanas',
        'presentacion': 'Presentación',
        'peso_recien_nacido': 'Peso RN (g)',
        'talla_recien_nacido': 'Talla RN (cm)',
        'apgar_1min': 'Apgar 1min',
        'apgar_5min': 'Apgar 5min',
        'sexo_recien_nacido': 'Sexo RN',
        'complicaciones': 'Complicaciones'
      };

      exportarExcel(
        partos,
        columnas,
        {
          filename: `partos_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Partos',
          title: `Registro de Partos - ${dayjs().format('DD/MM/YYYY')}`
        }
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  };

  const columns = buildPartosColumns(canChange, canDelete, handleView, handleEdit, handleDelete);

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="partos-container page-container">
      {/* HEADER Y ESTADÍSTICAS */}
      <PartosStats
        total={partos.length}
        cesareas={partos.filter(p => p.tipo_parto?.includes('cesarea')).length}
        vaginales={partos.filter(p => p.tipo_parto?.includes('vaginal')).length}
      />

      {/* BARRA DE HERRAMIENTAS */}
      <PartosToolbar
        filtros={filtros}
        dispatchFiltros={dispatchFiltros}
        onReload={cargarPartos}
        onExport={handleExportExcel}
        onNew={handleCreate}
        canAdd={canAdd('parto')}
      />

      {/* TABLA PRINCIPAL */}
      <Card className="table-card">
        <Table
          columns={columns}
          dataSource={filteredPartos}
          rowKey={(record: any) => record._uniqueRowKey || `parto-fallback-${record.id}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} registros`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          locale={{
            emptyText: 'No hay registros de partos',
          }}
        />
      </Card>
    </div>
  );
};

export default Partos;
