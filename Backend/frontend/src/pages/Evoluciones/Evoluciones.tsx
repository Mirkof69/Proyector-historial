import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Table,
  Button,
  Tag,
  Tooltip,
  Space,
  Card,
  Empty,
  Spin,
  Tabs,
  Typography,
  Avatar
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  SearchOutlined,
  RiseOutlined,
  UserOutlined,
  CalendarOutlined,
  MedicineBoxOutlined,
  FileTextOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  HistoryOutlined,
  UnorderedListOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import relativeTime from 'dayjs/plugin/relativeTime';
import { evolucionesService, EvolucionEmbarazo } from '../../services/evolucionesService';
import { useAntdApp } from '../../hooks/useMessage';
import TimelineEvoluciones from './TimelineEvoluciones';
import EvolucionesHeader from './components/EvolucionesHeader';
import EvolucionesStats from './components/EvolucionesStats';
import EvolucionesFilters from './components/EvolucionesFilters';
import { exportarExcel } from '../../utils/excelExport';
import './Evoluciones.css';
import { incluyeTexto } from '../../utils/texto';

dayjs.extend(relativeTime);
dayjs.locale('es');

const { Title, Text } = Typography;

interface FiltrosState {
  searchText: string;
  filterType: string;
  filterDate: dayjs.Dayjs | null;
}

type FiltrosAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_FILTER_TYPE'; payload: string }
  | { type: 'SET_FILTER_DATE'; payload: dayjs.Dayjs | null }
  | { type: 'RESET' };

const filtrosReducer = (state: FiltrosState, action: FiltrosAction): FiltrosState => {
  switch (action.type) {
    case 'SET_SEARCH':
      return { ...state, searchText: action.payload };
    case 'SET_FILTER_TYPE':
      return { ...state, filterType: action.payload };
    case 'SET_FILTER_DATE':
      return { ...state, filterDate: action.payload };
    case 'RESET':
      return { searchText: '', filterType: 'todos', filterDate: null };
    default:
      return state;
  }
};

const Evoluciones: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [evoluciones, setEvoluciones] = useState<EvolucionEmbarazo[]>([]);
  const [loading, setLoading] = useState(false);
  const [filtros, dispatchFiltros] = useReducer(filtrosReducer, {
    searchText: '',
    filterType: 'todos',
    filterDate: null,
  });

  const loadEvoluciones = useCallback(async () => {
    setLoading(true);
    try {
      const data = await evolucionesService.listar();
      setEvoluciones(Array.isArray(data) ? data : []);
    } catch (error) {
      message.error('Error al sincronizar el historial de evoluciones');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    loadEvoluciones();
  }, [loadEvoluciones]);

  const stats = useMemo(() => {
    const total = evoluciones.length;
    const hoy = evoluciones.filter(e => dayjs(e.fecha || e.fecha_evento).isSame(dayjs(), 'day')).length;
    const semana = evoluciones.filter(e => dayjs(e.fecha || e.fecha_evento).isAfter(dayjs().subtract(7, 'day'))).length;

    // Distribución por tipo para stats
    const consultas = evoluciones.filter(e => (e.tipo || e.tipo_evento) === 'consulta').length;
    const urgencias = evoluciones.filter(e => (e.tipo || e.tipo_evento) === 'urgencia').length;

    return { total, hoy, semana, consultas, urgencias };
  }, [evoluciones]);

  const filteredEvoluciones = useMemo(() => {
    return evoluciones.filter(evol => {
      const matchSearch =
        incluyeTexto(evol.paciente_nombre, filtros.searchText) ||
        incluyeTexto(evol.diagnostico, filtros.searchText) ||
        incluyeTexto(evol.medico_nombre, filtros.searchText);

      const tipoReal = evol.tipo || evol.tipo_evento;
      const matchType = filtros.filterType === 'todos' || tipoReal === filtros.filterType;

      const matchDate = !filtros.filterDate || dayjs(evol.fecha || evol.fecha_evento).isSame(filtros.filterDate, 'day');

      return matchSearch && matchType && matchDate;
    });
  }, [evoluciones, filtros]);

  const handleExportExcel = useCallback(() => {
    try {
      const datos = filteredEvoluciones.map(e => ({
        fecha: dayjs(e.fecha || e.fecha_evento).format('DD/MM/YYYY HH:mm'),
        paciente: e.paciente_nombre || '-',
        medico: e.medico_nombre || '-',
        tipo: (e.tipo || e.tipo_evento || '-').toString().toUpperCase(),
        diagnostico: e.diagnostico || '-',
        descripcion: e.descripcion || e.resumen || '-',
        estado: e.estado?.toUpperCase() || '-',
      }));
      const columnas = {
        fecha: 'Fecha',
        paciente: 'Paciente',
        medico: 'Médico',
        tipo: 'Tipo de Evento',
        diagnostico: 'Diagnóstico',
        descripcion: 'Descripción',
        estado: 'Estado',
      };
      exportarExcel(
        datos,
        columnas,
        {
          filename: `evoluciones_${dayjs().format('YYYYMMDD_HHmmss')}.xlsx`,
          sheetName: 'Evoluciones',
          title: `Evolución Clínica - ${dayjs().format('DD/MM/YYYY')}`,
        },
      );
      message.success('Archivo Excel generado exitosamente');
    } catch (error) {
      message.error('Error al generar el archivo Excel');
    }
  }, [filteredEvoluciones, message]);

  const handleDelete = useCallback((id: number) => {
    modal.confirm({
      title: 'Confirmar eliminación',
      content: '¿Está seguro de que desea eliminar esta nota de evolución? Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await evolucionesService.eliminar(id);
          message.success('Evolución eliminada correctamente');
          loadEvoluciones();
        } catch (error) {
          message.error('No se pudo eliminar el registro');
        }
      }
    });
  }, [modal, message, loadEvoluciones]);

  const columns = useMemo(() => [
    {
      title: 'Paciente / Identificación',
      key: 'paciente',
      fixed: 'left' as const,
      width: 280,
      render: (_: any, record: EvolucionEmbarazo) => (
        <Space size="middle">
          <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#e6f7ff', color: '#1890ff' }} />
          <div>
            <button type="button" style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer' }} onClick={() => navigate(`/dashboard/evoluciones/${record.id}`)} onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); navigate(`/dashboard/evoluciones/${record.id}`); } }}>
              <Text strong className="block" style={{ color: '#096dd9', cursor: 'pointer' }}>
                {record.paciente_nombre || 'Paciente Sin Nombre'}
              </Text>
            </button>
            <Text type="secondary" style={{ fontSize: '0.85em' }}>ID: {record.paciente || '-'}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Fecha y Hora',
      dataIndex: 'fecha',
      key: 'fecha',
      width: 180,
      render: (text: string, record: EvolucionEmbarazo) => (
        <div>
          <div><CalendarOutlined style={{ marginRight: 6, color: '#8c8c8c' }} />{dayjs(text || record.fecha_evento).format('DD/MM/YYYY')}</div>
          <Text type="secondary" style={{ fontSize: '0.85em' }}>{dayjs(text || record.fecha_evento).format('HH:mm A')}</Text>
        </div>
      ),
      sorter: (a: any, b: any) => new Date(a.fecha || a.fecha_evento || '').getTime() - new Date(b.fecha || b.fecha_evento || '').getTime(),
    },
    {
      title: 'Tipo / Categoría',
      key: 'tipo',
      width: 150,
      render: (_: any, record: EvolucionEmbarazo) => {
        const tipo = record.tipo || record.tipo_evento;
        const color = tipo === 'urgencia' ? 'red' : tipo === 'control' ? 'green' : 'blue';
        return (
          <Tag color={color} style={{ borderRadius: '12px', padding: '0 12px' }}>
            {(tipo || 'CONSULTA').toUpperCase()}
          </Tag>
        );
      },
    },
    {
      title: 'Diagnóstico Principal',
      key: 'diagnostico',
      width: 300,
      render: (_: any, record: EvolucionEmbarazo) => (
        <Tooltip title={record.diagnostico}>
          <div style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            <RiseOutlined style={{ marginRight: 8, color: '#52c41a' }} />
            {record.diagnostico || 'Sin diagnóstico registrado'}
          </div>
        </Tooltip>
      ),
    },
    {
      title: 'Médico Tratante',
      dataIndex: 'medico_nombre',
      key: 'medico',
      width: 200,
      render: (text: string) => (
        <Space>
          <MedicineBoxOutlined style={{ color: '#8c8c8c' }} />
          {text || 'Dr. No Asignado'}
        </Space>
      )
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 160,
      align: 'center' as const,
      render: (_: any, record: EvolucionEmbarazo) => (
        <Space>
          <Tooltip title="Detalles Completos">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => navigate(`/dashboard/evoluciones/${record.id}`)}
              className="action-btn-view"
            />
          </Tooltip>
          <Tooltip title="Editar Nota">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => navigate(`/dashboard/evoluciones/${record.id}/editar`)}
              className="action-btn-edit"
            />
          </Tooltip>
          <Tooltip title="Eliminar">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => record.id && handleDelete(record.id)}
              className="action-btn-delete"
            />
          </Tooltip>
        </Space>
      ),
    },
  ], [navigate, handleDelete]);

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        <EvolucionesHeader loading={loading} onReload={loadEvoluciones} onExport={handleExportExcel} />

        <EvolucionesStats stats={stats} />

        <Spin spinning={loading} tip="Cargando evoluciones clínicas…" delay={300}>
          <Tabs
            defaultActiveKey="tabla"
            size="large"
            className="premium-tabs"
            items={[
              {
                key: 'tabla',
                label: (
                  <span>
                    <UnorderedListOutlined /> Vista de Listado
                  </span>
                ),
                children: (
                  <>
                    <EvolucionesFilters
                      filtros={filtros}
                      onSearchChange={(value) => dispatchFiltros({ type: 'SET_SEARCH', payload: value })}
                      onTypeChange={(val) => dispatchFiltros({ type: 'SET_FILTER_TYPE', payload: val })}
                      onDateChange={(val) => dispatchFiltros({ type: 'SET_FILTER_DATE', payload: val })}
                      onReset={() => dispatchFiltros({ type: 'RESET' })}
                    />

                    <Table
                      columns={columns}
                      dataSource={filteredEvoluciones}
                      rowKey="id"
                      loading={false}
                      pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} evoluciones clínicas`
                      }}
                      scroll={{ x: 1200 }}
                      className="premium-table"
                      locale={{
                        emptyText: <Empty description="No se han encontrado registros de evolución" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                      }}
                    />
                  </>
                ),
              },
              {
                key: 'timeline',
                label: (
                  <span>
                    <HistoryOutlined /> Línea de Tiempo
                  </span>
                ),
                children: (
                  <div style={{ padding: '20px', background: '#fff', borderRadius: '12px' }}>
                    <TimelineEvoluciones />
                  </div>
                ),
              },
            ]}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default Evoluciones;
