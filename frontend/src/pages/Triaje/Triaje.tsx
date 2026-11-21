import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { Alert, Empty, Table, Button, Card, Typography, Space } from 'antd';
import {
  PlusOutlined, PrinterOutlined, ExportOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import { useAntdApp } from '../../hooks/useMessage';
import api from '../../services/api';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';
import { descargarArchivo } from '../../utils/descargarArchivo';
import dayjs from 'dayjs';
import es from 'dayjs/locale/es';
import TriajeStats from './components/TriajeStats';
import TriajeFiltros from './components/TriajeFiltros';
import { buildTriajeColumns } from './components/triajeColumns';
import './Triaje.css';

dayjs.locale(es);
const { Title, Text } = Typography;
const URL_TRIAJES = '/triaje/triajes/';
const RESUMEN_VACIO = { total: 0, pendiente: 0, completado: 0, urgente: 0, presion_alta: 0 };

const Triaje: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [searchText, setSearchText] = useState('');
  const [filterState, setFilterState] = useState<string>('');
  const [filterPriority, setFilterPriority] = useState<string>('');
  const [filterDate, setFilterDate] = useState<any>(null);

  // Filtros, búsqueda y cifras en el SERVIDOR. Antes se contaba y filtraba en
  // el navegador sobre la primera página (200 como mucho).
  const filtrosServidor = useMemo(() => ({
    estado: filterState || undefined,
    prioridad: filterPriority || undefined,
    fecha_registro__gte: filterDate ? dayjs(filterDate).startOf('day').toISOString() : undefined,
    fecha_registro__lte: filterDate ? dayjs(filterDate).endOf('day').toISOString() : undefined,
  }), [filterState, filterPriority, filterDate]);
  const listado = useListadoServidor<TriajeEnfermeria>(URL_TRIAJES, {
    filtros: filtrosServidor, busqueda: searchText, tamanoInicial: 10,
  });
  const { parametros, recargar } = listado;
  const [stats, setStats] = useState(RESUMEN_VACIO);
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get(`${URL_TRIAJES}resumen/`, { params: parametros() });
      setStats(r.data);
    } catch {
      setStats(RESUMEN_VACIO);
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);
  const loadTriajes = useCallback(() => { recargar(); cargarResumen(); }, [recargar, cargarResumen]);

  const handleDelete = useCallback(async (id: number) => {
    modal.confirm({
      title: '¿Eliminar triaje?',
      content: 'Esta acción no se puede deshacer y eliminará permanentemente el registro de triaje.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await triajeService.eliminar(id);
          message.success('Triaje eliminado correctamente');
          loadTriajes();
        } catch (error) {
          message.error('Error al eliminar triaje');
        }
      }
    });
  }, [loadTriajes, message, modal]);

  const handleMarkComplete = useCallback(async (id: number) => {
    try {
      await triajeService.actualizar(id, { estado: 'completado' });
      message.success('Triaje marcado como completado');
      loadTriajes();
    } catch (error) {
      message.error('Error al actualizar triaje');
    }
  }, [loadTriajes, message]);

  // Excel desde el SERVIDOR con todos los triajes filtrados (y auditado).
  const handleExportExcel = useCallback(() => {
    descargarArchivo(`${URL_TRIAJES}exportar-excel/${aQuery(parametros())}`, `triaje_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`)
      .catch(() => message.error('No se pudo generar el Excel de triaje'));
  }, [parametros, message]);

  const columns = useMemo(
    () => buildTriajeColumns(navigate, handleMarkComplete, handleDelete),
    [navigate, handleMarkComplete, handleDelete]
  );

  return (
    <div className="triaje-pagina">
      <header className="pagina-encabezado">
        <div className="pagina-encabezado__texto">
          <Title level={2} className="pagina-encabezado__titulo">
            <MedicineBoxOutlined /> Gestión de Triaje
          </Title>
          <Text className="pagina-encabezado__descripcion">Evaluación inicial de pacientes y signos vitales</Text>
        </div>
                <Space wrap>
                  <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                    Imprimir
                  </Button>
                  <Button
                    icon={<ExportOutlined />}
                    onClick={handleExportExcel}
                  >
                    Exportar
                  </Button>
                  <Button
                    type="primary"
                    size="large"
                    icon={<PlusOutlined />}
                    onClick={() => navigate('/dashboard/triaje/nuevo')}
                  >
                    Nuevo Triaje
                  </Button>
                </Space>
      </header>

      <TriajeStats
        total={stats.total}
        pendiente={stats.pendiente}
        completado={stats.completado}
        urgente={stats.urgente}
        presionAlta={stats.presion_alta}
      />

      <TriajeFiltros
        searchText={searchText}
        filterState={filterState}
        filterPriority={filterPriority}
        filterDate={filterDate}
        onSearchChange={setSearchText}
        onStateChange={setFilterState}
        onPriorityChange={setFilterPriority}
        onDateChange={setFilterDate}
        onLimpiar={() => {
          setSearchText('');
          setFilterState('');
          setFilterPriority('');
          setFilterDate(null);
        }}
      />

      {listado.error && <Alert type="error" showIcon message={listado.error} />}
      <Card className="triaje-tabla" styles={{ body: { padding: 0 } }}>
      <Table
        columns={columns}
        dataSource={listado.datos}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay registros de triaje" /> }}
        rowKey="id"
        loading={listado.cargando}
        pagination={listado.paginacion}
        onChange={listado.onChange}
        scroll={{ x: 1000 }}
        onRow={(record) => ({
          onDoubleClick: () => navigate(`/dashboard/triaje/${record.id}`),
        })}
      />
      </Card>
    </div>
  );
};

export default Triaje;
