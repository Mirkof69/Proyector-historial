/**
 * =============================================================================
 * CONSULTORIOS - VISTA PRINCIPAL DE LISTADO
 * =============================================================================
 * Lista completa de consultorios con filtros, búsqueda y estadísticas
 * =============================================================================
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useAuth } from "../../hooks/useAuth";
import { Empty, Card, Row, Col, Table, Button, Input, Select, Space, Form, Tabs } from 'antd';
import {
  PlusOutlined, SearchOutlined, HomeOutlined, ToolOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { consultoriosService, Consultorio, EstadoConsultorio } from '../../services/consultoriosService';
import dayjs from 'dayjs';
import { buildConsultoriosColumns } from './consultoriosColumns';
import ConsultoriosStats from './components/ConsultoriosStats';
import VistaPorEstadoTab from './components/VistaPorEstadoTab';
import PanelControlTab from './components/PanelControlTab';
import ConsultorioFormModal from './components/ConsultorioFormModal';
import ReservasDrawer from './components/ReservasDrawer';
import ReservaFormModal from './components/ReservaFormModal';
import MantenimientoDrawer from './components/MantenimientoDrawer';
import MantenimientoFormModal from './components/MantenimientoFormModal';
import EstadisticasDrawer from './components/EstadisticasDrawer';
import DisponibilidadModal from './components/DisponibilidadModal';
import { incluyeTexto } from '../../utils/texto';

const { Search } = Input;
const { Option } = Select;

const tabVistaLista = <span><HomeOutlined /> Vista de Lista</span>;
const tabVistaPorEstado = <span><CheckCircleOutlined /> Vista por Estado</span>;
const tabPanelControl = <span><ToolOutlined /> Panel de Control</span>;

const Consultorios: React.FC = () => {
  const [consultorios, setConsultorios] = useState<Consultorio[]>([]);
  const { message } = useAntdApp();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [filtroTipo, setFiltroTipo] = useState<string>('');
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const navigate = useNavigate();

  // NUEVOS ESTADOS PARA MODAL DE CREACIÓN/EDICIÓN
  const [modalVisible, setModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const consultorioEditandoRef = useRef<Consultorio | null>(null);
  const [formModal] = Form.useForm();
  const [guardando, setGuardando] = useState(false);

  // NUEVOS ESTADOS PARA RESERVAS
  const [drawerReservasVisible, setDrawerReservasVisible] = useState(false);
  const [consultorioReservas, setConsultorioReservas] = useState<Consultorio | null>(null);
  const [reservas, setReservas] = useState<any[]>([]);
  const [loadingReservas, setLoadingReservas] = useState(false);
  const [modalReservaVisible, setModalReservaVisible] = useState(false);
  const [formReserva] = Form.useForm();

  // NUEVOS ESTADOS PARA MANTENIMIENTO
  const [drawerMantenimientoVisible, setDrawerMantenimientoVisible] = useState(false);
  const [consultorioMantenimiento, setConsultorioMantenimiento] = useState<Consultorio | null>(null);
  const [mantenimientos, setMantenimientos] = useState<any[]>([]);
  const [loadingMantenimientos, setLoadingMantenimientos] = useState(false);
  const [modalMantenimientoVisible, setModalMantenimientoVisible] = useState(false);
  const [formMantenimiento] = Form.useForm();

  // NUEVOS ESTADOS PARA ESTADÍSTICAS
  const [drawerEstadisticasVisible, setDrawerEstadisticasVisible] = useState(false);
  const [consultorioEstadisticas, setConsultorioEstadisticas] = useState<Consultorio | null>(null);
  const [estadisticas, setEstadisticas] = useState<any>(null);
  const [loadingEstadisticas, setLoadingEstadisticas] = useState(false);

  // NUEVOS ESTADOS PARA DISPONIBILIDAD
  const [modalDisponibilidadVisible, setModalDisponibilidadVisible] = useState(false);
  const [consultorioDisponibilidad, setConsultorioDisponibilidad] = useState<Consultorio | null>(null);
  const [formDisponibilidad] = Form.useForm();
  const [verificandoDisponibilidad, setVerificandoDisponibilidad] = useState(false);
  const [resultadoDisponibilidad, setResultadoDisponibilidad] = useState<any>(null);

  // ✨ NUEVO ESTADO PARA TABS DE ORGANIZACIÓN
  const [activeTab, setActiveTab] = useState('lista');

  // Cargar consultorios con useCallback para evitar warnings
  const cargarConsultorios = useCallback(async () => {
    setLoading(true);
    try {
      const data = await consultoriosService.getAll();

      // FIX: Asegurar que data sea array (el servicio ya normaliza, pero por seguridad)
      const consultoriosArray = Array.isArray(data) ? data : [];
      setConsultorios(consultoriosArray);

      if (consultoriosArray.length > 0) {
      }
    } catch (error) {
      message.error('Error cargando consultorios');
      setConsultorios([]); // FIX: Asegurar array vacío en caso de error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarConsultorios();
  }, [cargarConsultorios]);

  const handleEliminar = async (id: number) => {
    try {
      await consultoriosService.delete(id);
      message.success('Consultorio eliminado exitosamente');
      cargarConsultorios();
    } catch (error) {
      message.error('Error eliminando consultorio');
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA MODAL DE CREACIÓN/EDICIÓN
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAbrirModalCrear = () => {
    setModalMode('create');
    consultorioEditandoRef.current = null;
    formModal.resetFields();
    formModal.setFieldsValue({
      activo: true,
      tiene_camilla: false,
      tiene_escritorio: false,
      tiene_computadora: false,
      tiene_lavamanos: false,
      tiene_oxigeno: false,
      tiene_aspirador: false,
      estado: 'disponible',
      capacidad_personas: 1,
    });
    setModalVisible(true);
  };

  const handleAbrirModalEditar = async (consultorio: Consultorio) => {
    setModalMode('edit');
    consultorioEditandoRef.current = consultorio;

    // Cargar datos completos del consultorio
    try {
      const data = await consultoriosService.getById(consultorio.id!);
      formModal.setFieldsValue(data);
      setModalVisible(true);
    } catch (error) {
      message.error('Error cargando datos del consultorio');
    }
  };

  const handleGuardarModal = async (values: any) => {
    setGuardando(true);
    try {
      // Validar datos antes de enviar
      const validacion = consultoriosService.validarDatosConsultorio(values);
      if (!validacion.valido) {
        validacion.errores.forEach(err => message.error(err));
        setGuardando(false);
        return;
      }

      if (modalMode === 'create') {
        await consultoriosService.create(values);
        message.success('Consultorio creado exitosamente');
      } else {
        await consultoriosService.update(consultorioEditandoRef.current!.id!, values);
        message.success('Consultorio actualizado exitosamente');
      }

      setModalVisible(false);
      formModal.resetFields();
      cargarConsultorios();
    } catch (error: any) {
      const errorMsg = modalMode === 'create'
        ? 'Error creando consultorio'
        : 'Error actualizando consultorio';
      message.error(errorMsg);
    } finally {
      setGuardando(false);
    }
  };

  const handleCerrarModal = () => {
    setModalVisible(false);
    formModal.resetFields();
    consultorioEditandoRef.current = null;
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA RESERVAS
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAbrirReservas = async (consultorio: Consultorio) => {
    setConsultorioReservas(consultorio);
    setDrawerReservasVisible(true);
    cargarReservas(consultorio.id!);
  };

  const cargarReservas = async (consultorioId: number) => {
    setLoadingReservas(true);
    try {
      const data = await consultoriosService.listarReservas({ consultorio: consultorioId });
      setReservas(data);
    } catch (error) {
      message.error('Error cargando reservas');
    } finally {
      setLoadingReservas(false);
    }
  };

  const handleAbrirModalReserva = () => {
    formReserva.resetFields();
    formReserva.setFieldsValue({
      consultorio: consultorioReservas?.id,
      fecha_reserva: dayjs(),
      estado: 'pendiente'
    });
    setModalReservaVisible(true);
  };

  const handleGuardarReserva = async (values: any) => {
    try {
      const dataToSend = {
        ...values,
        consultorio: consultorioReservas?.id,
        fecha_reserva: values.fecha_reserva.format('YYYY-MM-DD'),
        hora_inicio: values.hora_inicio.format('HH:mm'),
        hora_fin: values.hora_fin.format('HH:mm'),
        solicitado_por: user?.id,
      };

      await consultoriosService.crearReserva(dataToSend);
      message.success('Reserva creada exitosamente');
      setModalReservaVisible(false);
      formReserva.resetFields();
      cargarReservas(consultorioReservas!.id!);
    } catch (error) {
      message.error('Error creando reserva');
    }
  };

  const handleAprobarReserva = async (reservaId: number) => {
    try {
      await consultoriosService.aprobarReserva(reservaId);
      message.success('Reserva aprobada exitosamente');
      cargarReservas(consultorioReservas!.id!);
    } catch (error) {
      message.error('Error aprobando reserva');
    }
  };

  const handleRechazarReserva = async (reservaId: number) => {
    try {
      await consultoriosService.rechazarReserva(reservaId, 'Rechazado por administrador');
      message.success('Reserva rechazada');
      cargarReservas(consultorioReservas!.id!);
    } catch (error) {
      message.error('Error rechazando reserva');
    }
  };

  const handleCancelarReserva = async (reservaId: number) => {
    try {
      await consultoriosService.cancelarReserva(reservaId, 'Cancelado por administrador');
      message.success('Reserva cancelada');
      cargarReservas(consultorioReservas!.id!);
    } catch (error) {
      message.error('Error cancelando reserva');
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA MANTENIMIENTO
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAbrirMantenimiento = async (consultorio: Consultorio) => {
    setConsultorioMantenimiento(consultorio);
    setDrawerMantenimientoVisible(true);
    cargarMantenimientos(consultorio.id!);
  };

  const cargarMantenimientos = async (consultorioId: number) => {
    setLoadingMantenimientos(true);
    try {
      const data = await consultoriosService.listarMantenimientos({ consultorio: consultorioId });
      setMantenimientos(data);
    } catch (error) {
      message.error('Error cargando mantenimientos');
    } finally {
      setLoadingMantenimientos(false);
    }
  };

  const handleAbrirModalMantenimiento = () => {
    formMantenimiento.resetFields();
    formMantenimiento.setFieldsValue({
      consultorio: consultorioMantenimiento?.id,
      fecha_programada: dayjs(),
      estado: 'programado',
      tipo_mantenimiento: 'preventivo'
    });
    setModalMantenimientoVisible(true);
  };

  const handleGuardarMantenimiento = async (values: any) => {
    try {
      const dataToSend = {
        ...values,
        consultorio: consultorioMantenimiento?.id,
        fecha_programada: values.fecha_programada.format('YYYY-MM-DD'),
      };

      await consultoriosService.programarMantenimiento(dataToSend);
      message.success('Mantenimiento programado exitosamente');
      setModalMantenimientoVisible(false);
      formMantenimiento.resetFields();
      cargarMantenimientos(consultorioMantenimiento!.id!);
    } catch (error) {
      message.error('Error programando mantenimiento');
    }
  };

  const handleCompletarMantenimiento = async (mantenimientoId: number) => {
    try {
      await consultoriosService.completarMantenimiento(mantenimientoId, {
        trabajo_realizado: 'Mantenimiento completado',
        observaciones: 'Completado desde el listado'
      });
      message.success('Mantenimiento completado');
      cargarMantenimientos(consultorioMantenimiento!.id!);
    } catch (error) {
      message.error('Error completando mantenimiento');
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA ESTADÍSTICAS
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAbrirEstadisticas = async (consultorio: Consultorio) => {
    setConsultorioEstadisticas(consultorio);
    setDrawerEstadisticasVisible(true);
    cargarEstadisticas(consultorio.id!);
  };

  const cargarEstadisticas = async (consultorioId: number) => {
    setLoadingEstadisticas(true);
    try {
      const data = await consultoriosService.obtenerEstadisticas(consultorioId, {
        fecha_inicio: dayjs().subtract(30, 'days').format('YYYY-MM-DD'),
        fecha_fin: dayjs().format('YYYY-MM-DD')
      });
      setEstadisticas(data);
    } catch (error) {
      message.error('Error cargando estadísticas');
    } finally {
      setLoadingEstadisticas(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA VERIFICAR DISPONIBILIDAD
  // ═══════════════════════════════════════════════════════════════════════════

  const handleAbrirDisponibilidad = (consultorio: Consultorio) => {
    setConsultorioDisponibilidad(consultorio);
    formDisponibilidad.resetFields();
    formDisponibilidad.setFieldsValue({
      fecha: dayjs(),
    });
    setResultadoDisponibilidad(null);
    setModalDisponibilidadVisible(true);
  };

  const handleVerificarDisponibilidad = async (values: any) => {
    setVerificandoDisponibilidad(true);
    try {
      const resultado = await consultoriosService.verificarDisponibilidad(
        consultorioDisponibilidad!.id!,
        values.fecha.format('YYYY-MM-DD'),
        values.hora_inicio.format('HH:mm'),
        values.hora_fin.format('HH:mm')
      );
      setResultadoDisponibilidad(resultado);

      if (resultado.disponible) {
        message.success('El consultorio está disponible en ese horario');
      } else {
        message.warning(`No disponible: ${resultado.motivo || 'Horario ocupado'}`);
      }
    } catch (error) {
      message.error('Error verificando disponibilidad');
    } finally {
      setVerificandoDisponibilidad(false);
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // NUEVOS HANDLERS PARA CAMBIO RÁPIDO DE ESTADO
  // ═══════════════════════════════════════════════════════════════════════════

  const handleCambiarEstado = async (consultorioId: number, nuevoEstado: EstadoConsultorio) => {
    try {
      await consultoriosService.actualizarParcial(consultorioId, { estado: nuevoEstado });
      message.success(`Estado cambiado a: ${nuevoEstado}`);
      cargarConsultorios();
    } catch (error) {
      message.error('Error cambiando estado');
    }
  };

  // Estadísticas calculadas
  const stats = {
    total: consultorios.length,
    disponibles: consultorios.filter(c => c.estado === 'disponible').length,
    enMantenimiento: consultorios.filter(c => c.estado === 'mantenimiento').length,
    inactivos: consultorios.filter(c => !c.activo).length,
  };

  // Filtrado
  const consultoriosFiltrados = consultorios.filter(consultorio => {
    const matchSearch = !searchText ||
      incluyeTexto(consultorio.nombre, searchText) ||
      incluyeTexto(consultorio.codigo, searchText) ||
      incluyeTexto(consultorio.area, searchText);

    const matchTipo = !filtroTipo || consultorio.tipo === filtroTipo;
    const matchEstado = !filtroEstado || consultorio.estado === filtroEstado;

    return matchSearch && matchTipo && matchEstado;
  });

  // Columnas de la tabla
  const columns = buildConsultoriosColumns({
    navigate,
    handleAbrirModalEditar,
    handleAbrirReservas,
    handleAbrirMantenimiento,
    handleAbrirEstadisticas,
    handleAbrirDisponibilidad,
    handleEliminar,
  });

  return (
    <div className="page-container" style={{ padding: '24px' }}>
      {/* Estadísticas */}
      <ConsultoriosStats stats={stats} />

      {/* Tabla con Tabs de Organización */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
          {
            key: 'lista',
            label: tabVistaLista,
            children: (
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                {/* Filtros y acciones */}
                <Row gutter={16} align="middle">
                  <Col flex="auto">
                    <Space>
                      <Search
                        placeholder="Buscar por código, nombre o área"
                        allowClear
                        style={{ width: 300 }}
                        onChange={(e) => setSearchText(e.target.value)}
                        prefix={<SearchOutlined />}
                      />
                      <Select
                        placeholder="Tipo"
                        allowClear
                        style={{ width: 180 }}
                        onChange={(value) => setFiltroTipo(value || '')}
                      >
                        <Option value="general">General</Option>
                        <Option value="especializado">Especializado</Option>
                        <Option value="procedimientos">Procedimientos</Option>
                        <Option value="consulta_rapida">Consulta Rápida</Option>
                        <Option value="emergencias">Emergencias</Option>
                      </Select>
                      <Select
                        placeholder="Estado"
                        allowClear
                        style={{ width: 150 }}
                        onChange={(value) => setFiltroEstado(value || '')}
                      >
                        <Option value="disponible">Disponible</Option>
                        <Option value="ocupado">Ocupado</Option>
                        <Option value="mantenimiento">Mantenimiento</Option>
                        <Option value="reservado">Reservado</Option>
                        <Option value="inactivo">Inactivo</Option>
                      </Select>
                    </Space>
                  </Col>
                  <Col>
                    <Space>
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleAbrirModalCrear}
                      >
                        Nuevo Consultorio (Modal)
                      </Button>
                      <Button
                        icon={<PlusOutlined />}
                        onClick={() => navigate('/consultorios/nuevo')}
                      >
                        Nuevo (Página)
                      </Button>
                    </Space>
                  </Col>
                </Row>

                {/* Tabla */}
                <Table
                  columns={columns}
                  dataSource={consultoriosFiltrados}
                  locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay consultorios registrados" /> }}
                  rowKey="id"
                  loading={loading}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} consultorios`,
                  }}
                  scroll={{ x: 1200 }}
                />
              </Space>
            ),
          },
          {
            key: 'estado',
            label: tabVistaPorEstado,
            children: (
              <VistaPorEstadoTab
                consultorios={consultorios}
                handleCambiarEstado={handleCambiarEstado}
                handleAbrirReservas={handleAbrirReservas}
              />
            ),
          },
          {
            key: 'control',
            label: tabPanelControl,
            children: (
              <PanelControlTab
                consultorios={consultorios}
                handleCambiarEstado={handleCambiarEstado}
              />
            ),
          },
        ]} />
      </Card>

      {/* MODAL DE CREACIÓN/EDICIÓN DE CONSULTORIO */}
      <ConsultorioFormModal
        modalVisible={modalVisible}
        modalMode={modalMode}
        formModal={formModal}
        guardando={guardando}
        handleCerrarModal={handleCerrarModal}
        handleGuardarModal={handleGuardarModal}
      />

      {/* DRAWER DE RESERVAS */}
      <ReservasDrawer
        drawerReservasVisible={drawerReservasVisible}
        consultorioReservas={consultorioReservas}
        reservas={reservas}
        loadingReservas={loadingReservas}
        onClose={() => setDrawerReservasVisible(false)}
        handleAbrirModalReserva={handleAbrirModalReserva}
        handleAprobarReserva={handleAprobarReserva}
        handleRechazarReserva={handleRechazarReserva}
        handleCancelarReserva={handleCancelarReserva}
      />

      {/* Modal para crear reserva */}
      <ReservaFormModal
        modalReservaVisible={modalReservaVisible}
        formReserva={formReserva}
        onClose={() => setModalReservaVisible(false)}
        handleGuardarReserva={handleGuardarReserva}
      />

      {/* DRAWER DE MANTENIMIENTO */}
      <MantenimientoDrawer
        drawerMantenimientoVisible={drawerMantenimientoVisible}
        consultorioMantenimiento={consultorioMantenimiento}
        mantenimientos={mantenimientos}
        loadingMantenimientos={loadingMantenimientos}
        onClose={() => setDrawerMantenimientoVisible(false)}
        handleAbrirModalMantenimiento={handleAbrirModalMantenimiento}
        handleCompletarMantenimiento={handleCompletarMantenimiento}
      />

      {/* Modal para programar mantenimiento */}
      <MantenimientoFormModal
        modalMantenimientoVisible={modalMantenimientoVisible}
        formMantenimiento={formMantenimiento}
        onClose={() => setModalMantenimientoVisible(false)}
        handleGuardarMantenimiento={handleGuardarMantenimiento}
      />

      {/* DRAWER DE ESTADÍSTICAS */}
      <EstadisticasDrawer
        drawerEstadisticasVisible={drawerEstadisticasVisible}
        consultorioEstadisticas={consultorioEstadisticas}
        loadingEstadisticas={loadingEstadisticas}
        estadisticas={estadisticas}
        onClose={() => setDrawerEstadisticasVisible(false)}
      />

      {/* MODAL DE VERIFICAR DISPONIBILIDAD */}
      <DisponibilidadModal
        modalDisponibilidadVisible={modalDisponibilidadVisible}
        consultorioDisponibilidad={consultorioDisponibilidad}
        formDisponibilidad={formDisponibilidad}
        verificandoDisponibilidad={verificandoDisponibilidad}
        resultadoDisponibilidad={resultadoDisponibilidad}
        onClose={() => setModalDisponibilidadVisible(false)}
        handleVerificarDisponibilidad={handleVerificarDisponibilidad}
      />
    </div>
  );
};

export default Consultorios;
