/**
 * =============================================================================
 * GESTIÓN DE PARTOS - LISTADO PRINCIPAL
 * =============================================================================
 * Vista principal para la gestión de registros de partos.
 * Funcionalidades:
 * - Listado paginado de partos
 * - Filtrado por fecha, paciente, tipo de parto
 * - Estadísticas rápidas (total partos, cesáreas, etc.)
 * - Acceso a creación, edición y detalle de partos
 * - Conexión: GET /partos/
 * =============================================================================
 */

import React, { useState, useReducer, useEffect, useCallback, useRef, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { useNavigate } from 'react-router-dom';
import {Table,
  Button,
  Input,
  Space,
  Card,
  Row,
  Col,
  Tag,
  Tooltip,
  Modal,
  DatePicker,
  Select,
  Statistic,
  Typography} from "antd";
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  MedicineBoxOutlined,
  ReloadOutlined,
  CalendarOutlined,
  WomanOutlined,
  WarningOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { partosService, Parto } from '../../services/partosService';
import { FRONTEND_ROUTES } from '../../config/routes';
import api from '../../services/api';
import { usePermissions } from '../../hooks/usePermissions';
import { exportarExcel } from '../../utils/excelExport';
import './Partos.css';

const { RangePicker } = DatePicker;
const { Option } = Select;
const { Text } = Typography;

interface FiltrosPartosState {
  searchText: string;
  dateRange: [dayjs.Dayjs, dayjs.Dayjs] | null;
  tipoPartoFilter: string | null;
}

type FiltrosPartosAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_DATE_RANGE'; payload: [dayjs.Dayjs, dayjs.Dayjs] | null }
  | { type: 'SET_TIPO_PARTO'; payload: string | null }
  | { type: 'LIMPIAR' };

const filtrosPartosReducer = (state: FiltrosPartosState, action: FiltrosPartosAction): FiltrosPartosState => {
  switch (action.type) {
    case 'SET_SEARCH': return { ...state, searchText: action.payload };
    case 'SET_DATE_RANGE': return { ...state, dateRange: action.payload };
    case 'SET_TIPO_PARTO': return { ...state, tipoPartoFilter: action.payload };
    case 'LIMPIAR': return { searchText: '', dateRange: null, tipoPartoFilter: null };
    default: return state;
  }
};

// ── Helpers puros (nivel de módulo: identidad estable entre renders) ─────────
const getViaPartoColor = (via: string) => {
  const colores: Record<string, string> = {
    vaginal_espontaneo: 'green',
    vaginal_instrumentado: 'blue',
    cesarea_electiva: 'orange',
    cesarea_urgencia: 'red',
    cesarea_emergencia: 'volcano',
  };
  return colores[via] || 'default';
};

const getViaPartoLabel = (via: string) => {
  return via?.replace(/_/g, ' ').toUpperCase() || 'NO ESPECIFICADO';
};

// Detectar si es aborto basado en edad gestacional
const esAborto = (edadGestacional: string | undefined) => {
  if (!edadGestacional) return false;
  try {
    const semanas = parseInt(edadGestacional.split('+')[0]);
    return semanas < 20;
  } catch {
    return false;
  }
};

// Obtener etiqueta de tipo de aborto
const getTipoAbortoLabel = (tipoAborto: string) => {
  const etiquetas: Record<string, string> = {
    espontaneo: 'Aborto Espontáneo',
    inducido: 'Aborto Inducido',
    incompleto: 'Aborto Incompleto',
    completo: 'Aborto Completo',
    diferido: 'Aborto Diferido/Retenido',
    inevitable: 'Aborto Inevitable',
  };
  return etiquetas[tipoAborto] || tipoAborto.toUpperCase();
};

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

  // Helpers puros hoisteados a nivel de módulo (ver arriba del componente).

  // ==========================================================================
  // COLUMNAS TABLA
  // ==========================================================================
  const columns = [
    {
      title: 'ID Parto',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: number) => <Tag color="blue">#{id}</Tag>,
    },
    {
      title: 'CI Paciente',
      key: 'ci_paciente',
      width: 120,
      render: (_: any, record: Parto) => (
        record.paciente_info?.cedula_identidad ? (
          <Tag color="geekblue">{record.paciente_info.cedula_identidad}</Tag>
        ) : <Text type="secondary">-</Text>
      ),
    },
    {
      title: 'Nombre Paciente',
      key: 'nombre_paciente',
      width: 200,
      render: (_: any, record: Parto) => (
        <Text strong>
          {record.paciente_info
            ? `${record.paciente_info.nombre} ${record.paciente_info.apellido_paterno}`
            : 'Paciente Desconocido'}
        </Text>
      ),
    },
    {
      title: 'Fecha de Parto',
      dataIndex: 'fecha_parto',
      key: 'fecha_parto',
      width: 160,
      render: (text: string) => (
        <Space>
          <CalendarOutlined style={{ color: '#1890ff' }} />
          {dayjs(text).format('DD/MM/YYYY HH:mm')}
        </Space>
      ),
      sorter: (a: Parto, b: Parto) => dayjs(a.fecha_parto).unix() - dayjs(b.fecha_parto).unix(),
      defaultSortOrder: 'descend' as const,
    },
    {
      title: 'Tipo de Parto',
      key: 'tipo_parto',
      width: 130,
      render: (_: any, record: Parto) => {
        // ✅ DETERMINAR SI ES ABORTO O PARTO SEGÚN LOS CAMPOS REGISTRADOS
        const tipoAborto = (record as any).tipo_aborto;
        const tipoParto = record.tipo_parto;

        // Si tiene tipo_aborto registrado, ES UN ABORTO
        if (tipoAborto) {
          return (
            <Tag color="orange">
              {getTipoAbortoLabel(tipoAborto)}
            </Tag>
          );
        }
        // Si tiene tipo_parto registrado, ES UN PARTO
        else if (tipoParto) {
          return (
            <Tag color={getViaPartoColor(tipoParto)}>
              {getViaPartoLabel(tipoParto)}
            </Tag>
          );
        }
        // Solo si no tiene ninguno, usar edad gestacional para determinar
        else {
          const isAborto = esAborto(record.edad_gestacional_parto);
          return (
            <Tag color={isAborto ? "orange" : "default"}>
              {isAborto ? 'ABORTO' : 'Sin clasificar'}
            </Tag>
          );
        }
      },
    },
    {
      title: 'Resultado',
      key: 'resultado',
      width: 120,
      render: (_: any, record: Parto) => {
        const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
        const apgar5 = rn?.apgar_5_minutos || record.apgar_5min;

        // Determinar resultado basado en Apgar 5
        if (!apgar5 && !rn) return <Tag color="default">Sin datos</Tag>;
        if (typeof apgar5 === 'number') {
          if (apgar5 >= 7) return <Tag color="success">Normal</Tag>;
          if (apgar5 >= 4) return <Tag color="warning">Moderado</Tag>;
          return <Tag color="error">Crítico</Tag>;
        }
        return <Tag color="processing">Evaluando</Tag>;
      },
    },
    {
      title: 'Sexo RN',
      key: 'sexo_rn',
      width: 110,
      render: (_: any, record: Parto) => {
        const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
        if (!rn || !rn.sexo) return <Text type="secondary">-</Text>;
        return (
          <Tag color={rn.sexo === 'masculino' ? 'blue' : 'magenta'}>
            {rn.sexo === 'masculino' ? 'Masculino' : 'Femenino'}
          </Tag>
        );
      },
    },
    {
      title: 'Peso RN (g)',
      key: 'peso_rn',
      width: 110,
      render: (_: any, record: Parto) => {
        const rn = record.recien_nacidos && record.recien_nacidos.length > 0 ? record.recien_nacidos[0] : null;
        if (!rn || !rn.peso_nacimiento) return <Text type="secondary">-</Text>;

        // Color según peso
        const peso = rn.peso_nacimiento;
        let color = 'default';
        if (peso < 2500) color = 'orange'; // Bajo peso
        else if (peso >= 2500 && peso <= 4000) color = 'green'; // Normal
        else color = 'red'; // Macrosomía

        return <Tag color={color}>{peso}g</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      render: (_: any, record: Parto) => (
        <Space>
          <Tooltip title="Ver detalles">
            <Button
              icon={<EyeOutlined />}
              onClick={() => handleView(record.id!)}
              size="small"
            />
          </Tooltip>
          {canChange('parto') && (
            <Tooltip title="Editar">
              <Button
                type="primary"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record.id!)}
                size="small"
                ghost
              />
            </Tooltip>
          )}
          {canDelete('parto') && (
            <Tooltip title="Eliminar">
              <Button
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(record)}
                size="small"
              />
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  // ==========================================================================
  // RENDER
  // ==========================================================================
  return (
    <div className="partos-container page-container">
      {/* HEADER Y ESTADÍSTICAS */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Partos Registrados"
              value={partos.length}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Cesáreas"
              value={partos.filter(p => p.tipo_parto?.includes('cesarea')).length}
              suffix={`/ ${partos.length}`}
              valueStyle={{ color: '#cf1322' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Partos Vaginales"
              value={partos.filter(p => p.tipo_parto?.includes('vaginal')).length}
              suffix={`/ ${partos.length}`}
              valueStyle={{ color: '#389e0d' }}
              prefix={<WomanOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* BARRA DE HERRAMIENTAS */}
      <Card className="toolbar-card" style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} justify="space-between" align="middle">
          <Col xs={24} md={16}>
            <Space wrap>
              <Input
                placeholder="Buscar paciente..."
                prefix={<SearchOutlined />}
                value={filtros.searchText}
                onChange={(e) => dispatchFiltros({ type: 'SET_SEARCH', payload: e.target.value })}
                style={{ width: 200 }}
              />
              <RangePicker
                onChange={(dates) => dispatchFiltros({ type: 'SET_DATE_RANGE', payload: dates as any })}
                placeholder={['Desde', 'Hasta']}
              />
              <Select
                placeholder="Tipo de parto"
                allowClear
                style={{ width: 180 }}
                value={filtros.tipoPartoFilter}
                onChange={(val) => dispatchFiltros({ type: 'SET_TIPO_PARTO', payload: val })}
              >
                <Option value="vaginal_espontaneo">Vaginal Espontáneo</Option>
                <Option value="vaginal_instrumentado">Vaginal Instrumentado</Option>
                <Option value="cesarea_electiva">Cesárea Electiva</Option>
                <Option value="cesarea_urgencia">Cesárea Urgencia</Option>
                <Option value="cesarea_emergencia">Cesárea Emergencia</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={cargarPartos}
                title="Recargar datos"
              />
              <Button
                icon={<FileExcelOutlined />}
                onClick={handleExportExcel}
                title="Exportar a Excel"
                type="primary"
                ghost
              >
                Exportar Excel
              </Button>
            </Space>
          </Col>
          <Col xs={24} md={8} style={{ textAlign: 'right' }}>
            {canAdd('parto') && (
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreate}
                size="large"
              >
                Registrar Nuevo Parto
              </Button>
            )}
          </Col>
        </Row>
      </Card>

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
