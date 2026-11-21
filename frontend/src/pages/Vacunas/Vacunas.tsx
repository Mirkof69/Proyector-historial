import React, { useState, useReducer, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Empty,
  Typography
} from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  WarningOutlined,
  FileSearchOutlined,
  FileExcelOutlined,
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
import { descargarArchivo } from '../../utils/descargarArchivo';
import api from '../../services/api';
import { aQuery, useListadoServidor } from '../../hooks/useListadoServidor';

interface ResumenVacunas {
  total: number;
  con_proxima_dosis: number;
  con_reacciones: number;
  este_mes: number;
  vencidas: number;
  proxima_semana: number;
  por_tipo: { name: string; value: number }[];
  por_mes: { mes: string; cantidad: number }[];
}
const RESUMEN_VACIO: ResumenVacunas = {
  total: 0, con_proxima_dosis: 0, con_reacciones: 0, este_mes: 0, vencidas: 0, proxima_semana: 0,
  por_tipo: [], por_mes: [],
};

dayjs.extend(relativeTime);

const { Title, Text } = Typography;

const Vacunas: React.FC = () => {
  const navigate = useNavigate();
  const { message, modal } = useAntdApp();

  const [isDrawerVisible, setIsDrawerVisible] = useState<boolean>(false);
  const [selectedVacuna, setSelectedVacuna] = useState<RegistroVacunaExtended | null>(null);

  const [filtros, dispatchFiltros] = useReducer(filtrosVacunasReducer, {
    searchText: '',
    dateRange: null,
    filtroVacuna: 'todas',
    filtroEstado: 'todas',
  });

  // Filtros, cifras y gráficas los calcula el SERVIDOR sobre todos los
  // registros. Antes se pedían 1.000, el servidor cortaba en 200 y la pantalla
  // contaba solo esos 200 sin avisar.
  const filtrosServidor = useMemo(() => ({
    vacuna: filtros.filtroVacuna !== 'todas' ? filtros.filtroVacuna : undefined,
    estado_dosis: filtros.filtroEstado !== 'todas' ? filtros.filtroEstado : undefined,
    fecha_aplicacion__gte: filtros.dateRange?.[0]?.startOf('day').toISOString(),
    fecha_aplicacion__lte: filtros.dateRange?.[1]?.endOf('day').toISOString(),
  }), [filtros.filtroVacuna, filtros.filtroEstado, filtros.dateRange]);

  const listado = useListadoServidor<RegistroVacunaExtended>('/vacunas/registros/', {
    filtros: filtrosServidor, busqueda: filtros.searchText, tamanoInicial: 10, ordenInicial: '-fecha_aplicacion',
  });
  const loading = listado.cargando;
  const { parametros, recargar } = listado;

  const [resumen, setResumen] = useState<ResumenVacunas>(RESUMEN_VACIO);
  const cargarResumen = useCallback(async () => {
    try {
      const r = await api.get('/vacunas/registros/resumen/', { params: parametros() });
      setResumen(r.data);
    } catch {
      setResumen(RESUMEN_VACIO);
    }
  }, [parametros]);
  useEffect(() => { cargarResumen(); }, [cargarResumen]);

  const cargarVacunas = useCallback(() => {
    recargar();
    cargarResumen();
  }, [recargar, cargarResumen]);

  const stats = {
    total: resumen.total,
    conProximaDosis: resumen.con_proxima_dosis,
    conReacciones: resumen.con_reacciones,
    esteMes: resumen.este_mes,
    vencidas: resumen.vencidas,
    proximaSemana: resumen.proxima_semana,
  };
  const graficoPorTipo = resumen.por_tipo;
  const graficoPorMes = resumen.por_mes.map(m => ({ mes: dayjs(`${m.mes}-01`).format('MMM YYYY'), cantidad: m.cantidad }));

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
      icon: <WarningOutlined className="vacunas-icono-peligro" />,
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
    <div className="vacunas-page page-container">
      <header className="vacunas-page__cabecera">
        <div>
          <Title level={2}>Gestión de Vacunas e Inmunizaciones</Title>
          <Text type="secondary">Control clínico de esquemas y cronogramas de vacunación</Text>
        </div>
        <Space wrap>
          <Button
            icon={<FileSearchOutlined />}
            onClick={() => navigate('/dashboard/vacunas/tipos')}
          >
            Catálogo
          </Button>
          <Button
            icon={<FileExcelOutlined />}
            onClick={() => descargarArchivo(`/vacunas/registros/exportar-excel/${aQuery(listado.parametros())}`, `vacunas_${dayjs().format('YYYYMMDD')}.xlsx`)
              .catch(() => message.error('No se pudo exportar el Excel'))}
          >
            Exportar Excel
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={cargarVacunas}
            loading={loading}
            aria-label="Actualizar"
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleNuevaVacuna}
          >
            Registrar Vacuna
          </Button>
        </Space>
      </header>

      <VacunasStats stats={stats} />

      <VacunasFiltros filtros={filtros} dispatchFiltros={dispatchFiltros} />

      {/* GRÁFICAS */}
      <VacunasGraficas graficoPorMes={graficoPorMes} graficoPorTipo={graficoPorTipo} />

      {/* TABLA */}
      <Card>
        <Table
          columns={columns}
          dataSource={listado.datos}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={listado.paginacion}
          onChange={listado.onChange}
          locale={{
            emptyText: (
              <Empty
                description="No hay vacunas registradas"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button icon={<PlusOutlined />} onClick={handleNuevaVacuna}>
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
