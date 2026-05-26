/**
 * =============================================================================
 * CONSULTORIOS - VISTA PRINCIPAL DE LISTADO
 * =============================================================================
 * Lista completa de consultorios con filtros, búsqueda y estadísticas
 * =============================================================================
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Card, Row, Col, Table, Button, Input, Select, Space, Statistic,
  Tag, message, Popconfirm, Tooltip, Modal, Form, InputNumber, Switch,
  Divider, Drawer, Descriptions, List, DatePicker, Badge, Tabs
} from 'antd';
import {
  PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined,
  EyeOutlined, HomeOutlined, ToolOutlined, CheckCircleOutlined,
  CloseCircleOutlined, SaveOutlined, CalendarOutlined, BarChartOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { consultoriosService, Consultorio, TipoConsultorio, EstadoConsultorio, ReservaConsultorio, MantenimientoConsultorio } from '../../services/consultoriosService';
import dayjs from 'dayjs';

const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;

const tabVistaLista = <span><HomeOutlined /> Vista de Lista</span>;
const tabVistaPorEstado = <span><CheckCircleOutlined /> Vista por Estado</span>;
const tabPanelControl = <span><ToolOutlined /> Panel de Control</span>;

const checkCircleIcon = <CheckCircleOutlined />;
const homeIcon = <HomeOutlined />;
const closeCircleIcon = <CloseCircleOutlined />;
const eyeIcon = <EyeOutlined />;
const editIcon = <EditOutlined />;
const calendarIcon = <CalendarOutlined />;
const toolIcon = <ToolOutlined />;
const barChartIcon = <BarChartOutlined />;
const clockCircleIcon = <ClockCircleOutlined />;
const deleteIcon = <DeleteOutlined />;
const plusIcon = <PlusOutlined />;
const saveIcon = <SaveOutlined />;
const searchIcon = <SearchOutlined />;

const Consultorios: React.FC = () => {
  const [consultorios, setConsultorios] = useState<Consultorio[]>([]);
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
  const [reservas, setReservas] = useState<ReservaConsultorio[]>([]);
  const [loadingReservas, setLoadingReservas] = useState(false);
  const [modalReservaVisible, setModalReservaVisible] = useState(false);
  const [formReserva] = Form.useForm();

  // NUEVOS ESTADOS PARA MANTENIMIENTO
  const [drawerMantenimientoVisible, setDrawerMantenimientoVisible] = useState(false);
  const [consultorioMantenimiento, setConsultorioMantenimiento] = useState<Consultorio | null>(null);
  const [mantenimientos, setMantenimientos] = useState<MantenimientoConsultorio[]>([]);
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
      capacidad: 1,
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
        solicitado_por: 1, // TODO: usar usuario actual
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
      // Datos mock en caso de error
      setEstadisticas({
        consultorio_id: consultorioId,
        consultorio_nombre: 'Consultorio',
        periodo: {
          inicio: dayjs().subtract(30, 'days').format('YYYY-MM-DD'),
          fin: dayjs().format('YYYY-MM-DD')
        },
        horas_totales_disponibles: 240,
        horas_ocupadas: 180,
        horas_libres: 60,
        tasa_ocupacion: 75,
        total_consultas: 45,
        total_procedimientos: 12,
        total_emergencias: 3,
        medicos_usuarios: 5,
        total_mantenimientos: 2,
        horas_mantenimiento: 4,
        promedio_ocupacion_dia: 6,
      });
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
      // Mock result en caso de error
      setResultadoDisponibilidad({
        disponible: true,
        motivo: 'Verificación simulada (backend no disponible)'
      });
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
      consultorio.nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
      consultorio.codigo?.toLowerCase().includes(searchText.toLowerCase()) ||
      consultorio.area?.toLowerCase().includes(searchText.toLowerCase());

    const matchTipo = !filtroTipo || consultorio.tipo === filtroTipo;
    const matchEstado = !filtroEstado || consultorio.estado === filtroEstado;

    return matchSearch && matchTipo && matchEstado;
  });

  // Columnas de la tabla
  const columns = [
    {
      title: 'Código',
      dataIndex: 'codigo',
      key: 'codigo',
      width: 120,
      sorter: (a: Consultorio, b: Consultorio) => (a.codigo || '').localeCompare(b.codigo || ''),
    },
    {
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
      sorter: (a: Consultorio, b: Consultorio) => (a.nombre || '').localeCompare(b.nombre || ''),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 150,
      render: (tipo: TipoConsultorio) => {
        const colors: Record<string, string> = {
          'general': 'blue',
          'especializado': 'purple',
          'procedimientos': 'orange',
          'consulta_rapida': 'cyan',
          'emergencias': 'red',
        };
        return <Tag color={colors[tipo] || 'default'}>{tipo}</Tag>;
      },
    },
    {
      title: 'Ubicación',
      key: 'ubicacion',
      render: (_: any, record: Consultorio) => (
        <span>
          {record.area && `${record.area}`}
          {record.piso && ` - Piso ${record.piso}`}
        </span>
      ),
    },
    {
      title: 'Capacidad',
      dataIndex: 'capacidad',
      key: 'capacidad',
      width: 100,
      align: 'center' as const,
    },
    {
      title: 'Equipamiento',
      key: 'equipamiento',
      render: (_: any, record: Consultorio) => (
        <Space size="small">
          {record.tiene_camilla && <Tooltip title="Camilla"><Tag color="green">C</Tag></Tooltip>}
          {record.tiene_escritorio && <Tooltip title="Escritorio"><Tag color="blue">E</Tag></Tooltip>}
          {record.tiene_computadora && <Tooltip title="Computadora"><Tag color="purple">PC</Tag></Tooltip>}
        </Space>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 130,
      render: (estado: EstadoConsultorio) => {
        const configs: Record<string, { color: string; icon: React.ReactElement; text: string }> = {
          'disponible': { color: 'success', icon: checkCircleIcon, text: 'Disponible' },
          'ocupado': { color: 'processing', icon: homeIcon, text: 'Ocupado' },
          'mantenimiento': { color: 'warning', icon: toolIcon, text: 'Mantenimiento' },
          'reservado': { color: 'default', icon: homeIcon, text: 'Reservado' },
          'inactivo': { color: 'error', icon: closeCircleIcon, text: 'Inactivo' },
        };
        const config = configs[estado] || configs['inactivo'];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 280,
      fixed: 'right' as const,
      render: (_: any, record: Consultorio) => (
        <Space size="small" wrap>
          <Tooltip title="Ver detalle">
            <Button
              type="text"
              size="small"
              icon={eyeIcon}
              onClick={() => navigate(`/consultorios/${record.id}`)}
            />
          </Tooltip>
          <Tooltip title="Editar en modal">
            <Button
              type="text"
              size="small"
              icon={editIcon}
              onClick={() => handleAbrirModalEditar(record)}
            />
          </Tooltip>
          <Tooltip title="Reservas">
            <Button
              type="text"
              size="small"
              icon={calendarIcon}
              onClick={() => handleAbrirReservas(record)}
            />
          </Tooltip>
          <Tooltip title="Mantenimiento">
            <Button
              type="text"
              size="small"
              icon={toolIcon}
              onClick={() => handleAbrirMantenimiento(record)}
            />
          </Tooltip>
          <Tooltip title="Estadísticas">
            <Button
              type="text"
              size="small"
              icon={barChartIcon}
              onClick={() => handleAbrirEstadisticas(record)}
            />
          </Tooltip>
          <Tooltip title="Verificar disponibilidad">
            <Button
              type="text"
              size="small"
              icon={clockCircleIcon}
              onClick={() => handleAbrirDisponibilidad(record)}
            />
          </Tooltip>
          <Tooltip title="Eliminar">
            <Popconfirm
              title="¿Está seguro de eliminar este consultorio?"
              onConfirm={() => handleEliminar(record.id!)}
              okText="Sí"
              cancelText="No"
            >
              <Button
                type="text"
                size="small"
                danger
                icon={deleteIcon}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Estadísticas */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Consultorios"
              value={stats.total}
              prefix={<HomeOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Disponibles"
              value={stats.disponibles}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="En Mantenimiento"
              value={stats.enMantenimiento}
              prefix={<ToolOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Inactivos"
              value={stats.inactivos}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

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
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Row gutter={16}>
                  <Col span={12}>
                    <Card title="Disponibles" size="small">
                      <List
                        dataSource={consultorios.filter(c => c.estado === 'disponible')}
                        renderItem={(item) => (<List.Item key={item.id} actions={[
                              <Button key={`btn-ocupado-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'ocupado')}>Marcar Ocupado</Button>
                            ]}
                          >
                            <List.Item.Meta title={item.nombre} description={item.codigo} />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="En Mantenimiento" size="small">
                      <List
                        dataSource={consultorios.filter(c => c.estado === 'mantenimiento')}
                        renderItem={(item) => (<List.Item key={item.id} actions={[
                              <Button key={`btn-disponible-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'disponible')}>Marcar Disponible</Button>
                            ]}
                          >
                            <List.Item.Meta title={item.nombre} description={item.codigo} />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                </Row>
                <Row gutter={16}>
                  <Col span={12}>
                    <Card title="Ocupados" size="small">
                      <List
                        dataSource={consultorios.filter(c => c.estado === 'ocupado')}
                        renderItem={(item) => (<List.Item key={item.id} actions={[
                              <Button key={`btn-liberar-${item.id}`} size="small" onClick={() => handleCambiarEstado(item.id!, 'disponible')}>Liberar</Button>
                            ]}
                          >
                            <List.Item.Meta title={item.nombre} description={item.codigo} />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="Reservados" size="small">
                      <List
                        dataSource={consultorios.filter(c => c.estado === 'reservado')}
                        renderItem={(item) => (<List.Item key={item.id} actions={[
                              <Button key={`btn-reservas-${item.id}`} size="small" onClick={() => handleAbrirReservas(item)}>Ver Reservas</Button>
                            ]}
                          >
                            <List.Item.Meta title={item.nombre} description={item.codigo} />
                          </List.Item>
                        )}
                      />
                    </Card>
                  </Col>
                </Row>
              </Space>
            ),
          },
          {
            key: 'control',
            label: tabPanelControl,
            children: (
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Card title="Cambio Rápido de Estado" size="small">
                  <Row gutter={16}>
                    <Col span={24}>
                      <Space direction="vertical" style={{ width: '100%' }}>
                        {consultorios.slice(0, 10).map(c => (
                          <Card key={c.id} size="small">
                            <Row align="middle">
                              <Col flex="auto">
                                <strong>{c.nombre}</strong> - {c.codigo}
                              </Col>
                              <Col>
                                <Space>
                                  <Button size="small" type={c.estado === 'disponible' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'disponible')}>Disponible</Button>
                                  <Button size="small" type={c.estado === 'ocupado' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'ocupado')}>Ocupado</Button>
                                  <Button size="small" type={c.estado === 'mantenimiento' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'mantenimiento')}>Mantenimiento</Button>
                                  <Button size="small" type={c.estado === 'reservado' ? 'primary' : 'default'} onClick={() => handleCambiarEstado(c.id!, 'reservado')}>Reservado</Button>
                                </Space>
                              </Col>
                            </Row>
                          </Card>
                        ))}
                      </Space>
                    </Col>
                  </Row>
                </Card>
              </Space>
            ),
          },
        ]} />
      </Card>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* MODAL DE CREACIÓN/EDICIÓN DE CONSULTORIO */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <Modal
        title={
          <Space>
            {modalMode === 'create' ? <PlusOutlined /> : <EditOutlined />}
            {modalMode === 'create' ? 'Crear Nuevo Consultorio' : 'Editar Consultorio'}
          </Space>
        }
        open={modalVisible}
        onCancel={handleCerrarModal}
        footer={null}
        width={900}
        destroyOnHidden
      >
        <Form
          form={formModal}
          layout="vertical"
          onFinish={handleGuardarModal}
          initialValues={{
            activo: true,
            tiene_camilla: false,
            tiene_escritorio: false,
            tiene_computadora: false,
            tiene_lavamanos: false,
            tiene_oxigeno: false,
            tiene_aspirador: false,
            estado: 'disponible',
            capacidad: 1,
          }}
        >
          <Divider orientation="left">Información Básica</Divider>
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item
                label="Código"
                name="codigo"
                rules={[
                  { required: true, message: 'El código es requerido' },
                  { max: 20, message: 'Máximo 20 caracteres' },
                ]}
              >
                <Input placeholder="Ej: CONS-001" />
              </Form.Item>
            </Col>
            <Col xs={24} md={16}>
              <Form.Item
                label="Nombre"
                name="nombre"
                rules={[
                  { required: true, message: 'El nombre es requerido' },
                  { max: 100, message: 'Máximo 100 caracteres' },
                ]}
              >
                <Input placeholder="Ej: Consultorio de Ginecología 1" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item
                label="Tipo"
                name="tipo"
                rules={[{ required: true, message: 'El tipo es requerido' }]}
              >
                <Select placeholder="Seleccione tipo">
                  <Option value="consulta">Consulta</Option>
                  <Option value="procedimientos">Procedimientos</Option>
                  <Option value="emergencia">Emergencia</Option>
                  <Option value="multifuncional">Multifuncional</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item label="Estado" name="estado">
                <Select placeholder="Seleccione estado">
                  <Option value="disponible">Disponible</Option>
                  <Option value="ocupado">Ocupado</Option>
                  <Option value="mantenimiento">Mantenimiento</Option>
                  <Option value="limpieza">Limpieza</Option>
                  <Option value="reservado">Reservado</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Form.Item label="Área" name="area">
                <Input placeholder="Ej: Maternidad" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Piso" name="piso">
                <InputNumber min={0} max={20} style={{ width: '100%' }} placeholder="0" />
              </Form.Item>
            </Col>
            <Col xs={24} md={8}>
              <Form.Item label="Capacidad" name="capacidad">
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Equipamiento</Divider>
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Form.Item label="Tipo de Equipamiento" name="equipamiento">
                <Select placeholder="Seleccione equipamiento" allowClear>
                  <Option value="basico">Básico</Option>
                  <Option value="intermedio">Intermedio</Option>
                  <Option value="avanzado">Avanzado</Option>
                  <Option value="quirurgico">Quirúrgico</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={12} md={6}>
              <Form.Item label="Camilla" name="tiene_camilla" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Escritorio" name="tiene_escritorio" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Computadora" name="tiene_computadora" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Lavamanos" name="tiene_lavamanos" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={12} md={6}>
              <Form.Item label="Oxígeno" name="tiene_oxigeno" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Aspirador" name="tiene_aspirador" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col xs={12} md={6}>
              <Form.Item label="Activo" name="activo" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Descripción</Divider>
          <Row gutter={16}>
            <Col xs={24}>
              <Form.Item label="Descripción" name="descripcion">
                <TextArea rows={2} placeholder="Descripción del consultorio" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col xs={24}>
              <Form.Item label="Observaciones" name="observaciones">
                <TextArea rows={2} placeholder="Notas adicionales" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={saveIcon} loading={guardando}>
                {modalMode === 'create' ? 'Crear' : 'Actualizar'} Consultorio
              </Button>
              <Button onClick={handleCerrarModal}>Cancelar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* DRAWER DE RESERVAS */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <Drawer
        title={
          <Space>
            <CalendarOutlined />
            Reservas - {consultorioReservas?.nombre}
          </Space>
        }
        placement="right"
        onClose={() => setDrawerReservasVisible(false)}
        open={drawerReservasVisible}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Button
            type="primary"
            icon={plusIcon}
            onClick={handleAbrirModalReserva}
            block
          >
            Nueva Reserva
          </Button>

          <List
            loading={loadingReservas}
            dataSource={reservas}
            renderItem={(reserva) => (
              <List.Item
                actions={[
                  reserva.estado === 'pendiente' && (
                    <Button
                      key="aprobar"
                      type="link"
                      size="small"
                      onClick={() => handleAprobarReserva(reserva.id!)}
                    >
                      Aprobar
                    </Button>
                  ),
                  reserva.estado === 'pendiente' && (
                    <Button
                      key="rechazar"
                      type="link"
                      size="small"
                      danger
                      onClick={() => handleRechazarReserva(reserva.id!)}
                    >
                      Rechazar
                    </Button>
                  ),
                  (reserva.estado === 'aprobada' || reserva.estado === 'pendiente') && (
                    <Button
                      key="cancelar"
                      type="link"
                      size="small"
                      onClick={() => handleCancelarReserva(reserva.id!)}
                    >
                      Cancelar
                    </Button>
                  ),
                ].filter(Boolean)}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{reserva.motivo}</span>
                      <Tag
                        color={
                          reserva.estado === 'aprobada'
                            ? 'success'
                            : reserva.estado === 'rechazada'
                            ? 'error'
                            : reserva.estado === 'cancelada'
                            ? 'default'
                            : 'processing'
                        }
                      >
                        {reserva.estado}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <div>
                        Fecha: {dayjs(reserva.fecha_reserva).format('DD/MM/YYYY')}
                      </div>
                      <div>
                        Horario: {reserva.hora_inicio} - {reserva.hora_fin}
                      </div>
                      {reserva.solicitado_por_nombre && (
                        <div>Solicitado por: {reserva.solicitado_por_nombre}</div>
                      )}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Space>
      </Drawer>

      {/* Modal para crear reserva */}
      <Modal
        title="Nueva Reserva"
        open={modalReservaVisible}
        onCancel={() => setModalReservaVisible(false)}
        footer={null}
        destroyOnHidden
      >
        <Form form={formReserva} layout="vertical" onFinish={handleGuardarReserva}>
          <Form.Item
            label="Fecha de Reserva"
            name="fecha_reserva"
            rules={[{ required: true, message: 'Seleccione la fecha' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Hora Inicio"
                name="hora_inicio"
                rules={[{ required: true, message: 'Seleccione hora inicio' }]}
              >
                <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Hora Fin"
                name="hora_fin"
                rules={[{ required: true, message: 'Seleccione hora fin' }]}
              >
                <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Motivo"
            name="motivo"
            rules={[{ required: true, message: 'Ingrese el motivo' }]}
          >
            <Input placeholder="Motivo de la reserva" />
          </Form.Item>

          <Form.Item label="Tipo de Actividad" name="tipo_actividad">
            <Input placeholder="Ej: Consulta especial, Procedimiento" />
          </Form.Item>

          <Form.Item label="Observaciones" name="observaciones">
            <TextArea rows={3} placeholder="Observaciones adicionales" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={saveIcon}>
                Crear Reserva
              </Button>
              <Button onClick={() => setModalReservaVisible(false)}>Cancelar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* DRAWER DE MANTENIMIENTO */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <Drawer
        title={
          <Space>
            <ToolOutlined />
            Mantenimiento - {consultorioMantenimiento?.nombre}
          </Space>
        }
        placement="right"
        onClose={() => setDrawerMantenimientoVisible(false)}
        open={drawerMantenimientoVisible}
        width={600}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Button
            type="primary"
            icon={plusIcon}
            onClick={handleAbrirModalMantenimiento}
            block
          >
            Programar Mantenimiento
          </Button>

          <List
            loading={loadingMantenimientos}
            dataSource={mantenimientos}
            renderItem={(mantenimiento) => (
              <List.Item
                actions={[
                  mantenimiento.estado === 'programado' && (
                    <Button
                      key="completar"
                      type="link"
                      size="small"
                      onClick={() => handleCompletarMantenimiento(mantenimiento.id!)}
                    >
                      Completar
                    </Button>
                  ),
                ]}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <span>{mantenimiento.tipo_mantenimiento}</span>
                      <Tag
                        color={
                          mantenimiento.estado === 'completado'
                            ? 'success'
                            : mantenimiento.estado === 'en_proceso'
                            ? 'processing'
                            : 'default'
                        }
                      >
                        {mantenimiento.estado}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <div>
                        Programado: {dayjs(mantenimiento.fecha_programada).format('DD/MM/YYYY')}
                      </div>
                      {mantenimiento.fecha_realizada && (
                        <div>
                          Realizado: {dayjs(mantenimiento.fecha_realizada).format('DD/MM/YYYY')}
                        </div>
                      )}
                      <div>{mantenimiento.descripcion}</div>
                      {mantenimiento.costo && <div>Costo: ${mantenimiento.costo}</div>}
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Space>
      </Drawer>

      {/* Modal para programar mantenimiento */}
      <Modal
        title="Programar Mantenimiento"
        open={modalMantenimientoVisible}
        onCancel={() => setModalMantenimientoVisible(false)}
        footer={null}
        destroyOnHidden
      >
        <Form form={formMantenimiento} layout="vertical" onFinish={handleGuardarMantenimiento}>
          <Form.Item
            label="Tipo de Mantenimiento"
            name="tipo_mantenimiento"
            rules={[{ required: true, message: 'Seleccione el tipo' }]}
          >
            <Select placeholder="Seleccione tipo">
              <Option value="preventivo">Preventivo</Option>
              <Option value="correctivo">Correctivo</Option>
              <Option value="limpieza_profunda">Limpieza Profunda</Option>
              <Option value="desinfeccion">Desinfección</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Fecha Programada"
            name="fecha_programada"
            rules={[{ required: true, message: 'Seleccione la fecha' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
          </Form.Item>

          <Form.Item
            label="Descripción"
            name="descripcion"
            rules={[{ required: true, message: 'Ingrese la descripción' }]}
          >
            <TextArea rows={3} placeholder="Descripción del mantenimiento" />
          </Form.Item>

          <Form.Item label="Observaciones" name="observaciones">
            <TextArea rows={2} placeholder="Observaciones adicionales" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" icon={saveIcon}>
                Programar
              </Button>
              <Button onClick={() => setModalMantenimientoVisible(false)}>Cancelar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* DRAWER DE ESTADÍSTICAS */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <Drawer
        title={
          <Space>
            <BarChartOutlined />
            Estadísticas - {consultorioEstadisticas?.nombre}
          </Space>
        }
        placement="right"
        onClose={() => setDrawerEstadisticasVisible(false)}
        open={drawerEstadisticasVisible}
        width={700}
      >
        {loadingEstadisticas ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>Cargando estadísticas…</div>
        ) : estadisticas ? (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card>
              <Statistic
                title="Período"
                value={`${dayjs(estadisticas.periodo?.inicio).format('DD/MM/YYYY')} - ${dayjs(
                  estadisticas.periodo?.fin
                ).format('DD/MM/YYYY')}`}
                valueStyle={{ fontSize: 14 }}
              />
            </Card>

            <Row gutter={16}>
              <Col span={12}>
                <Card>
                  <Statistic
                    title="Tasa de Ocupación"
                    value={estadisticas.tasa_ocupacion || 0}
                    suffix="%"
                    valueStyle={{
                      color:
                        (estadisticas.tasa_ocupacion || 0) >= 80
                          ? '#cf1322'
                          : (estadisticas.tasa_ocupacion || 0) >= 60
                          ? '#faad14'
                          : '#3f8600',
                    }}
                  />
                </Card>
              </Col>
              <Col span={12}>
                <Card>
                  <Statistic
                    title="Horas Ocupadas"
                    value={estadisticas.horas_ocupadas || 0}
                    suffix={`/ ${estadisticas.horas_totales_disponibles || 0}h`}
                  />
                </Card>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="Consultas"
                    value={estadisticas.total_consultas || 0}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="Procedimientos"
                    value={estadisticas.total_procedimientos || 0}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="Emergencias"
                    value={estadisticas.total_emergencias || 0}
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
            </Row>

            <Card title="Uso y Mantenimiento">
              <Descriptions column={2} bordered size="small">
                <Descriptions.Item label="Médicos Usuarios">
                  {estadisticas.medicos_usuarios || 0}
                </Descriptions.Item>
                <Descriptions.Item label="Promedio Ocupación/Día">
                  {estadisticas.promedio_ocupacion_dia || 0}h
                </Descriptions.Item>
                <Descriptions.Item label="Total Mantenimientos">
                  {estadisticas.total_mantenimientos || 0}
                </Descriptions.Item>
                <Descriptions.Item label="Horas Mantenimiento">
                  {estadisticas.horas_mantenimiento || 0}h
                </Descriptions.Item>
                {estadisticas.dia_mas_ocupado && (
                  <Descriptions.Item label="Día Más Ocupado" span={2}>
                    {estadisticas.dia_mas_ocupado}
                  </Descriptions.Item>
                )}
                {estadisticas.hora_pico && (
                  <Descriptions.Item label="Hora Pico" span={2}>
                    {estadisticas.hora_pico}
                  </Descriptions.Item>
                )}
                {estadisticas.medico_mas_frecuente && (
                  <Descriptions.Item label="Médico Más Frecuente" span={2}>
                    {estadisticas.medico_mas_frecuente}
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          </Space>
        ) : (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            No hay estadísticas disponibles
          </div>
        )}
      </Drawer>

      {/* ═══════════════════════════════════════════════════════════════════ */}
      {/* MODAL DE VERIFICAR DISPONIBILIDAD */}
      {/* ═══════════════════════════════════════════════════════════════════ */}
      <Modal
        title={
          <Space>
            <ClockCircleOutlined />
            Verificar Disponibilidad - {consultorioDisponibilidad?.nombre}
          </Space>
        }
        open={modalDisponibilidadVisible}
        onCancel={() => setModalDisponibilidadVisible(false)}
        footer={null}
        destroyOnHidden
      >
        <Form form={formDisponibilidad} layout="vertical" onFinish={handleVerificarDisponibilidad}>
          <Form.Item
            label="Fecha"
            name="fecha"
            rules={[{ required: true, message: 'Seleccione la fecha' }]}
          >
            <DatePicker style={{ width: '100%' }} format="DD/MM/YYYY" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Hora Inicio"
                name="hora_inicio"
                rules={[{ required: true, message: 'Seleccione hora inicio' }]}
              >
                <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Hora Fin"
                name="hora_fin"
                rules={[{ required: true, message: 'Seleccione hora fin' }]}
              >
                <DatePicker.TimePicker style={{ width: '100%' }} format="HH:mm" />
              </Form.Item>
            </Col>
          </Row>

          {resultadoDisponibilidad && (
            <Card
              style={{ marginBottom: 16 }}
              size="small"
              type={resultadoDisponibilidad.disponible ? 'inner' : 'inner'}
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {resultadoDisponibilidad.disponible ? (
                    <Badge status="success" text="DISPONIBLE" />
                  ) : (
                    <Badge status="error" text="NO DISPONIBLE" />
                  )}
                </div>
                {resultadoDisponibilidad.motivo && (
                  <div style={{ fontSize: 12, color: '#666' }}>
                    {resultadoDisponibilidad.motivo}
                  </div>
                )}
              </Space>
            </Card>
          )}

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={searchIcon}
                loading={verificandoDisponibilidad}
              >
                Verificar
              </Button>
              <Button onClick={() => setModalDisponibilidadVisible(false)}>Cerrar</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Consultorios;
