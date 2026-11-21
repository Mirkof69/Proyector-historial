import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card, Table, Empty, Button, Form, Spin, Typography
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { reportesService, AlertaMedica } from '../../services/reportesService';
import api from '../../services/api';
import type { ResumenAlertas } from './components/AlertasMedicasGraficas';
import dayjs from 'dayjs';
import './AlertasMedicas.css';
import { AlertasState } from './alertasMedicasUtils';
import { buildColumnsAlertasMedicas } from './alertasMedicasColumns';
import AlertasMedicasStats from './components/AlertasMedicasStats';
import AlertasMedicasGraficas from './components/AlertasMedicasGraficas';
import AlertasMedicasFiltros from './components/AlertasMedicasFiltros';
import AlertaMedicaDetalleDrawer from './components/AlertaMedicaDetalleDrawer';
import NuevaAlertaModal from './components/NuevaAlertaModal';
import { useListadoServidor } from '../../hooks/useListadoServidor';

const { Title, Text } = Typography;

const AlertasMedicas: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const navigate = useNavigate();
  const [state, setState] = useState<AlertasState>({
    selectedAlerta: null as AlertaMedica | null,
    drawerVisible: false,
    searchText: '',
    filterSeveridad: 'all',
    filterEstado: 'all',
    dateRange: null as any,
    modalNuevaAlerta: false
  });
  const {
    selectedAlerta,
    drawerVisible,
    searchText,
    filterSeveridad,
    filterEstado,
    dateRange,
    modalNuevaAlerta
  } = state;
  const mountedRef = useRef(false);
  useEffect(() => { mountedRef.current = true; }, []);
  const filtrosAvanzadosVisibleRef = useRef(false);
  const [form] = Form.useForm();

  // Cifras y gráficos de TODAS las alertas (el listado trae solo la página visible).
  const [resumen, setResumen] = useState<ResumenAlertas | null>(null);
  const cargarResumen = useCallback(() => {
    api.get<ResumenAlertas>('/reportes/alertas-medicas/estadisticas/').then(r => setResumen(r.data)).catch(() => setResumen(null));
  }, []);

  // En el servidor: antes se traían las primeras 200 y se filtraban aquí, así que
  // una paciente con alertas más antiguas no aparecía al buscarla.
  const listado = useListadoServidor<AlertaMedica>('/reportes/alertas-medicas/', {
    busqueda: searchText,
    tamanoInicial: 10,
    filtros: {
      prioridad: filterSeveridad === 'all' ? undefined : filterSeveridad,
      estado: filterEstado === 'all' ? undefined : filterEstado,
      fecha_desde: dateRange?.[0]?.format('YYYY-MM-DD'),
      fecha_hasta: dateRange?.[1]?.format('YYYY-MM-DD'),
    },
  });
  const alertas = listado.datos;
  const loading = listado.cargando;
  const cargarAlertas = () => { cargarResumen(); listado.recargar(); };

  useEffect(() => { cargarResumen(); }, [cargarResumen]);

  const handleCrearAlerta = async (values: any) => {
    try {
      await reportesService.crearAlerta({
        titulo: values.titulo,
        descripcion: values.descripcion,
        tipo: values.tipo,
        prioridad: values.prioridad,
        paciente_id: values.paciente_id ? parseInt(values.paciente_id, 10) : undefined,
        modulo_origen: values.modulo_origen,
        accion_recomendada: values.accion_recomendada,
        valor_actual: values.valor_actual,
        valor_umbral: values.valor_umbral,
      });
      message.success('Alerta creada correctamente');
      setState(prev => ({ ...prev, modalNuevaAlerta: false }));
      form.resetFields();
      cargarAlertas();
    } catch (error) {
      message.error('Error al crear la alerta');
    }
  };

  const filteredAlertas = alertas;

  const marcarResuelta = (id: number) => {
    modal.confirm({
      title: '¿Marcar como resuelta?',
      content: '¿Está seguro de que desea marcar esta alerta como resuelta?',
      okText: 'Sí, marcar',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await reportesService.marcarAlertaResuelta(id);
          message.success('Alerta marcada como resuelta');
          cargarAlertas();
        } catch (error) {
          message.error('Error al marcar la alerta como resuelta');
        }
      }
    });
  };

  const handleResolverTodas = () => {
    modal.confirm({
      title: '¿Marcar como resueltas las de esta página?',
      content: '¿Está seguro de marcar como resueltas las alertas pendientes que se ven en esta página?',
      okText: 'Sí',
      cancelText: 'No',
      onOk: async () => {
        const pendientes = filteredAlertas.filter(a => a.estado !== 'resuelta' && a.estado !== 'descartada');
        try {
          await Promise.all(pendientes.map(a => reportesService.marcarAlertaResuelta(a.id)));
          message.success('Alertas de esta página marcadas como resueltas');
          cargarAlertas();
        } catch (error) {
          message.error('Error al marcar algunas alertas como resueltas');
          cargarAlertas();
        }
      }
    });
  };

  const columns = buildColumnsAlertasMedicas({ setState, marcarResuelta });

  // Estadísticas
  const totalAlertas = resumen?.total_alertas ?? alertas.length;
  const alertasPendientes = resumen?.pendientes ?? alertas.filter(a => a.estado === 'activa' || a.estado === 'revisada' || a.estado === 'escalada').length;
  const alertasCriticas = resumen?.alertas_criticas_activas ?? alertas.filter(a => (a.prioridad === 'critica' || a.prioridad === 'emergencia') && a.estado !== 'resuelta' && a.estado !== 'descartada').length;
  const alertasHoy = resumen?.hoy ?? alertas.filter(a => dayjs(a.fecha_creacion).isSame(dayjs(), 'day')).length;

  return (
    <div className="alertas-page page-container" suppressHydrationWarning>
      {/* Header */}
      <header className="alertas-page__cabecera">
        <div>
          <Title level={2}>Alertas Médicas</Title>
          <Text type="secondary">Monitoreo y gestión de alertas clínicas del sistema</Text>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}
        >
          Nueva Alerta
        </Button>
      </header>

      {/* Estadísticas */}
      <AlertasMedicasStats
        totalAlertas={totalAlertas}
        alertasPendientes={alertasPendientes}
        alertasCriticas={alertasCriticas}
        alertasHoy={alertasHoy}
      />

      {/* Gráficas */}
      <AlertasMedicasGraficas alertas={alertas} resumen={resumen} />

      {/* Filtros */}
      <AlertasMedicasFiltros
        searchText={searchText}
        filterSeveridad={filterSeveridad}
        filterEstado={filterEstado}
        dateRange={dateRange}
        setState={setState}
        cargarAlertas={cargarAlertas}
        filteredAlertas={filteredAlertas}
        filtrosAvanzadosVisibleRef={filtrosAvanzadosVisibleRef}
        handleResolverTodas={handleResolverTodas}
      />

      {/* Tabla */}
      <Card>
        <Spin spinning={loading} tip="Cargando alertas…">
          {filteredAlertas.length === 0 && !loading ? (
            <Empty
              description="No se encontraron alertas con los filtros aplicados"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button icon={<PlusOutlined />} onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}>
                Crear Primera Alerta
              </Button>
            </Empty>
          ) : (
            <Table
              columns={columns}
              dataSource={filteredAlertas}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay alertas médicas registradas" /> }}
              loading={false}
              rowKey="id"
              pagination={listado.paginacion}
              onChange={listado.onChange}
              rowClassName={(record) => record.estado === 'activa' && (record.prioridad === 'critica' || record.prioridad === 'emergencia') ? 'alerta-critica-row' : ''}
              scroll={{ x: 1100 }}
            />
          )}
        </Spin>
      </Card>

      {/* Drawer de Detalle */}
      <AlertaMedicaDetalleDrawer
        drawerVisible={drawerVisible}
        selectedAlerta={selectedAlerta}
        setState={setState}
        marcarResuelta={marcarResuelta}
        navigate={navigate}
      />

      {/* Modal para Nueva Alerta */}
      <NuevaAlertaModal
        modalNuevaAlerta={modalNuevaAlerta}
        setState={setState}
        form={form}
        handleCrearAlerta={handleCrearAlerta}
      />
    </div>
  );
};

export default AlertasMedicas;
