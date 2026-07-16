import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Row,
  Col,
  Empty,
  Typography
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  FileSearchOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { vacunasService } from '../../services/vacunasService';
import { useAntdApp } from '../../hooks/useMessage';
import './Vacunas.css';
import {
  RegistroVacunaExtended,
  filtrosVacunasReducer,
} from './vacunasUtils';
import { buildColumnsVacunas } from './vacunasColumns';
import VacunasStats from './components/VacunasStats';
import VacunasFiltros from './components/VacunasFiltros';
import VacunasGraficas from './components/VacunasGraficas';
import CarnetVacunaDrawer from './components/CarnetVacunaDrawer';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

const Vacunas: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [vacunas, setVacunas] = useState<RegistroVacunaExtended[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [isDrawerVisible, setIsDrawerVisible] = useState<boolean>(false);
  const [selectedVacuna, setSelectedVacuna] = useState<RegistroVacunaExtended | null>(null);

  const [filtros, dispatchFiltros] = useReducer(filtrosVacunasReducer, {
    searchText: '',
    dateRange: null,
    filtroVacuna: 'todas',
    filtroEstado: 'todas',
  });

  const cargarVacunas = useCallback(async () => {
    try {
      setLoading(true);
      const response = await vacunasService.getRegistros({ page_size: 1000 });
      const data = response.results || response;

      if (Array.isArray(data)) {
        setVacunas(data as RegistroVacunaExtended[]);
      } else {
        setVacunas([]);
      }
    } catch (error) {
      message.error('Error al cargar el historial de inmunizaciones');
      setVacunas([]);
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    cargarVacunas();
  }, [cargarVacunas]);

  const filteredVacunas = useMemo(() => {
    let filtered = [...vacunas];

    if (filtros.searchText) {
      const searchLower = filtros.searchText.toLowerCase();
      filtered = filtered.filter(v =>
        v.paciente_info?.nombre_completo?.toLowerCase().includes(searchLower) ||
        v.tipo_vacuna_info?.nombre?.toLowerCase().includes(searchLower) ||
        v.paciente_nombre?.toLowerCase().includes(searchLower) ||
        v.tipo_vacuna_nombre?.toLowerCase().includes(searchLower) ||
        v.lote?.toLowerCase().includes(searchLower) ||
        v.laboratorio?.toLowerCase().includes(searchLower)
      );
    }

    if (filtros.dateRange && filtros.dateRange[0] && filtros.dateRange[1]) {
      const [start, end] = filtros.dateRange;
      filtered = filtered.filter(v => {
        const fecha = dayjs(v.fecha_aplicacion);
        return (fecha.isAfter(start.startOf('day')) || fecha.isSame(start.startOf('day'))) &&
          (fecha.isBefore(end.endOf('day')) || fecha.isSame(end.endOf('day')));
      });
    }

    if (filtros.filtroVacuna !== 'todas') {
      const filtroLower = filtros.filtroVacuna.toLowerCase();
      filtered = filtered.filter(v =>
        v.tipo_vacuna_info?.nombre?.toLowerCase().includes(filtroLower) ||
        v.tipo_vacuna_nombre?.toLowerCase().includes(filtroLower)
      );
    }

    if (filtros.filtroEstado !== 'todas') {
      if (filtros.filtroEstado === 'pendientes') {
        filtered = filtered.filter(v => v.proxima_dosis_fecha);
      } else if (filtros.filtroEstado === 'completas') {
        filtered = filtered.filter(v => !v.proxima_dosis_fecha);
      } else if (filtros.filtroEstado === 'vencidas') {
        filtered = filtered.filter(v =>
          v.proxima_dosis_fecha && dayjs(v.proxima_dosis_fecha).isBefore(dayjs().startOf('day'))
        );
      }
    }

    return filtered;
  }, [vacunas, filtros]);

  const stats = useMemo(() => {
    const total = filteredVacunas.length;
    const conProximaDosis = filteredVacunas.filter(v => v.proxima_dosis_fecha).length;
    const conReacciones = filteredVacunas.filter(v => v.reacciones_adversas).length;
    const esteMes = filteredVacunas.filter(v =>
      dayjs(v.fecha_aplicacion).isSame(dayjs(), 'month')
    ).length;

    const vencidas = filteredVacunas.filter(v =>
      v.proxima_dosis_fecha && dayjs(v.proxima_dosis_fecha).isBefore(dayjs().startOf('day'))
    ).length;

    const proximaSemana = filteredVacunas.filter(v =>
      v.proxima_dosis_fecha &&
      dayjs(v.proxima_dosis_fecha).isAfter(dayjs()) &&
      dayjs(v.proxima_dosis_fecha).isBefore(dayjs().add(7, 'days'))
    ).length;

    return { total, conProximaDosis, conReacciones, esteMes, vencidas, proximaSemana };
  }, [filteredVacunas]);

  const graficoPorTipo = useMemo(() => {
    const conteo: { [key: string]: number } = {};
    filteredVacunas.forEach(v => {
      const tipo = v.tipo_vacuna_info?.nombre || v.tipo_vacuna_nombre || 'Desconocido';
      conteo[tipo] = (conteo[tipo] || 0) + 1;
    });
    return Object.entries(conteo).map(([name, value]) => ({ name, value }));
  }, [filteredVacunas]);

  const graficoPorMes = useMemo(() => {
    const conteo: { [key: string]: number } = {};
    filteredVacunas.forEach(v => {
      const mes = dayjs(v.fecha_aplicacion).format('MMM YYYY');
      conteo[mes] = (conteo[mes] || 0) + 1;
    });
    return Object.entries(conteo).map(([mes, cantidad]) => ({ mes, cantidad }));
  }, [filteredVacunas]);

  // Handlers
  const handleNuevaVacuna = useCallback(() => {
    navigate('/dashboard/vacunas/nuevo');
  }, [navigate]);

  const handleVerDetalle = useCallback((id: number) => {
    navigate(`/dashboard/vacunas/${id}`);
  }, [navigate]);

  const handleEditar = useCallback((id: number) => {
    navigate(`/dashboard/vacunas/${id}/editar`);
  }, [navigate]);

  const handleEliminar = useCallback((vacuna: RegistroVacunaExtended) => {
    modal.confirm({
      title: 'Confirmar Eliminación',
      icon: <WarningOutlined style={{ color: 'red' }} />,
      content: `¿Desea eliminar el registro de vacunación de ${vacuna.tipo_vacuna_nombre || vacuna.tipo_vacuna_info?.nombre} para el paciente ${vacuna.paciente_nombre || vacuna.paciente_info?.nombre_completo}?`,
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await vacunasService.eliminarRegistro(vacuna.id);
          message.success('Registro de vacunación eliminado');
          cargarVacunas();
        } catch (error) {
          message.error('No se pudo eliminar el registro');
        }
      }
    });
  }, [modal, message, cargarVacunas]);

  const handleVerCarnet = useCallback((vacuna: RegistroVacunaExtended) => {
    setSelectedVacuna(vacuna);
    setIsDrawerVisible(true);
  }, []);

  // Columnas de la tabla
  const columns = useMemo(
    () => buildColumnsVacunas({ handleVerCarnet, handleVerDetalle, handleEditar, handleEliminar }),
    [handleVerCarnet, handleVerDetalle, handleEditar, handleEliminar]
  );

  return (
    <div className="animate-fade-in" style={{ padding: '24px' }}>
      <Card className="shadow-card overflow-hidden">
        {/* HEADER SECTION */}
        <div className="blue-gradient-header" style={{ margin: '-24px -24px 24px -24px', padding: '32px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Space align="center" size="large">
                <div className="header-icon-container">
                  <MedicineBoxOutlined style={{ fontSize: '32px', color: '#fff' }} />
                </div>
                <div>
                  <Title level={2} style={{ color: '#fff', margin: 0 }}>Gestión de Vacunas e Inmunizaciones</Title>
                  <Text style={{ color: 'rgba(255,255,255,0.85)' }}>Control clínico de esquemas y cronogramas de vacunación</Text>
                </div>
              </Space>
            </Col>
            <Col>
              <Space>
                <Button
                  size="large"
                  icon={<FileSearchOutlined />}
                  onClick={() => navigate('/dashboard/vacunas/tipos')}
                >
                  Catálogo
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlusOutlined />}
                  onClick={handleNuevaVacuna}
                  className="btn-success-gradient"
                >
                  Registrar Vacuna
                </Button>
                <Button
                  size="large"
                  icon={<ReloadOutlined />}
                  onClick={cargarVacunas}
                  loading={loading}
                />
              </Space>
            </Col>
          </Row>
        </div>

        <VacunasStats stats={stats} />

        <VacunasFiltros filtros={filtros} dispatchFiltros={dispatchFiltros} />

        {/* CHARTS COLLAPSIBLE */}
        <VacunasGraficas graficoPorMes={graficoPorMes} graficoPorTipo={graficoPorTipo} />

        {/* TABLE SECTION */}
        <Table
          columns={columns}
          dataSource={filteredVacunas}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            className: "custom-pagination",
            showTotal: (total) => `Total ${total} inmunizaciones`
          }}
          className="premium-table"
          locale={{
            emptyText: (
              <Empty
                description="No hay vacunas registradas"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" icon={<PlusOutlined />} onClick={handleNuevaVacuna}>
                  Registrar primera vacuna
                </Button>
              </Empty>
            )
          }}
        />
      </Card>

      {/* CARNET DRAWER */}
      <CarnetVacunaDrawer
        isDrawerVisible={isDrawerVisible}
        selectedVacuna={selectedVacuna}
        setIsDrawerVisible={setIsDrawerVisible}
        handleEditar={handleEditar}
      />
    </div>
  );
};

export default Vacunas;
