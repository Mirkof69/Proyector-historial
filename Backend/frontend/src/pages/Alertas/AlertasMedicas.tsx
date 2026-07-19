import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  Card, Table, Empty, Button, Form, Spin
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  WarningOutlined, PlusOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { reportesService, AlertaMedica } from '../../services/reportesService';
import dayjs from 'dayjs';
import './AlertasMedicas.css';
import { AlertasState } from './alertasMedicasUtils';
import { buildColumnsAlertasMedicas } from './alertasMedicasColumns';
import AlertasMedicasStats from './components/AlertasMedicasStats';
import AlertasMedicasGraficas from './components/AlertasMedicasGraficas';
import AlertasMedicasFiltros from './components/AlertasMedicasFiltros';
import AlertaMedicaDetalleDrawer from './components/AlertaMedicaDetalleDrawer';
import NuevaAlertaModal from './components/NuevaAlertaModal';
import { incluyeTexto } from '../../utils/texto';

const AlertasMedicas: React.FC = () => {
  const {modal,  message } = useAntdApp();
  const navigate = useNavigate();
  const [state, setState] = useState<AlertasState>({
    alertas: [] as AlertaMedica[],
    loading: false,
    selectedAlerta: null as AlertaMedica | null,
    drawerVisible: false,
    searchText: '',
    filterSeveridad: 'all',
    filterEstado: 'all',
    dateRange: null as any,
    modalNuevaAlerta: false
  });
  const {
    alertas,
    loading,
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

  const handleCrearAlerta = useCallback(async (values: any) => {
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
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [form, message]);

  const cargarAlertas = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }));
    try {
      const data = await reportesService.listarAlertas();
      setState(prev => ({ ...prev, alertas: data }));
    } catch (error) {
      message.error('Error al cargar alertas');
    } finally {
      setState(prev => ({ ...prev, loading: false }));
    }
  }, [message]);

  useEffect(() => {
    cargarAlertas();
    // eslint-disable-next-line react-doctor/exhaustive-deps
  }, [cargarAlertas]);

  const filteredAlertas = useMemo(() => {
    let filtered = [...alertas];

    // Filtro por texto
    if (searchText) {
      filtered = filtered.filter(alerta =>
        incluyeTexto(alerta.paciente_nombre, searchText) ||
        incluyeTexto(alerta.titulo, searchText) ||
        incluyeTexto(alerta.descripcion, searchText)
      );
    }

    // Filtro por prioridad
    if (filterSeveridad !== 'all') {
      filtered = filtered.filter(alerta => alerta.prioridad === filterSeveridad);
    }

    // Filtro por estado
    if (filterEstado !== 'all') {
      filtered = filtered.filter(alerta => alerta.estado === filterEstado);
    }

    // Filtro por rango de fechas
    if (dateRange && dateRange[0] && dateRange[1]) {
      filtered = filtered.filter(alerta => {
        const fecha = dayjs(alerta.fecha_creacion);
        return fecha.isAfter(dateRange[0]) && fecha.isBefore(dateRange[1]);
      });
    }

    return filtered;
  }, [alertas, searchText, filterSeveridad, filterEstado, dateRange]);

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
      title: '¿Marcar todas como resueltas?',
      content: '¿Está seguro de marcar todas las alertas pendientes (filtradas) como resueltas?',
      okText: 'Sí',
      cancelText: 'No',
      onOk: async () => {
        const pendientes = filteredAlertas.filter(a => a.estado !== 'resuelta' && a.estado !== 'descartada');
        try {
          await Promise.all(pendientes.map(a => reportesService.marcarAlertaResuelta(a.id)));
          message.success('Todas las alertas filtradas marcadas como resueltas');
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
  const totalAlertas = alertas.length;
  const alertasPendientes = alertas.filter(a => a.estado === 'activa' || a.estado === 'revisada' || a.estado === 'escalada').length;
  const alertasCriticas = alertas.filter(a => (a.prioridad === 'critica' || a.prioridad === 'emergencia') && a.estado !== 'resuelta' && a.estado !== 'descartada').length;
  const alertasHoy = alertas.filter(a => dayjs(a.fecha_creacion).isSame(dayjs(), 'day')).length;

  return (
    <div className="alertas-page page-container" style={{ padding: 24 }} suppressHydrationWarning>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1><WarningOutlined style={{ color: '#fa8c16' }} /> Alertas Médicas</h1>
        <p style={{ color: '#666' }}>Monitoreo y gestión de alertas clínicas del sistema</p>
      </div>

      {/* Estadísticas */}
      <AlertasMedicasStats
        totalAlertas={totalAlertas}
        alertasPendientes={alertasPendientes}
        alertasCriticas={alertasCriticas}
        alertasHoy={alertasHoy}
      />

      {/* Gráficas */}
      <AlertasMedicasGraficas alertas={alertas} />

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
              <Button type="primary" icon={<PlusOutlined />} onClick={() => setState(prev => ({ ...prev, modalNuevaAlerta: true }))}>
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
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showTotal: (total) => `Total: ${total} alertas`
              }}
              rowClassName={(record) => record.estado === 'activa' && (record.prioridad === 'critica' || record.prioridad === 'emergencia') ? 'alerta-critica-row' : ''}
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
