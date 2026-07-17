/**
 * =============================================================================
 * DASHBOARD CON GRÁFICAS REALES
 * =============================================================================
 * Dashboard completo con gráficas y estadísticas calculadas desde datos reales
 * NO depende de endpoints de API - usa directamente los servicios del frontend
 * =============================================================================
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Row, Col, Spin, Select,
  Space, Typography, Divider, Alert, DatePicker
} from 'antd';
import { pacientesService } from '../../services/pacientesService';
import { embarazosService } from '../../services/embarazosService';
import { partosService } from '../../services/partosService';
import { citasService } from '../../services/citasService';
import { ecografiasService } from '../../services/ecografiasService';
import { laboratorioService } from '../../services/laboratorioService';
import { evolucionesService } from '../../services/evolucionesService';
import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';
import es from 'dayjs/locale/es';
import {
  computeKpis, computePacientesPorMes, computeEmbarazosPorTrimestre,
  computeDistribucionRiesgos, computeCitasPorEstado, computePartosPorTipo,
  computeEcografiasPorTipo, computeEvolucionesPorSemana, computeLaboratorioPorEstado,
  computeRadarData, computePacientesPorEdad,
} from './dashboardGraficasUtils';
import DashboardGraficasKpis from './components/DashboardGraficasKpis';
import DashboardGraficasCharts from './components/DashboardGraficasCharts';


dayjs.extend(isBetween);
dayjs.locale(es);

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const DashboardGraficasReales: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null]>([null, null]);

  // Estados para datos
  const [pacientes, setPacientes] = useState<any[] | undefined>(undefined);
  const [embarazos, setEmbarazos] = useState<any[] | undefined>(undefined);
  const [partos, setPartos] = useState<any[] | undefined>(undefined);
  const [citas, setCitas] = useState<any[] | undefined>(undefined);
  const [ecografias, setEcografias] = useState<any[] | undefined>(undefined);
  const [laboratorio, setLaboratorio] = useState<any[] | undefined>(undefined);
  const [evoluciones, setEvoluciones] = useState<any[] | undefined>(undefined);

  // eslint-disable-next-line react-doctor/no-initialize-state
  useEffect(() => {
    cargarTodosDatos();
  }, []);

  const cargarTodosDatos = async () => {
    try {
      const [
        pacientesData,
        embarazosData,
        partosData,
        citasData,
        ecografiasData,
        laboratorioData,
        evolucionesData
      ] = await Promise.all([
        pacientesService.listar(),
        embarazosService.listar(),
        partosService.listar(),
        citasService.listar(),
        ecografiasService.listar(),
        laboratorioService.listar(),
        evolucionesService.listar()
      ]);

      setPacientes(pacientesData);
      setEmbarazos(embarazosData);
      setPartos(partosData);
      setCitas(citasData);
      setEcografias(ecografiasData);
      setLaboratorio(laboratorioData);
      setEvoluciones(evolucionesData);
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };

  // ========== KPIs CALCULADOS ==========
  const kpis = useMemo(
    () => computeKpis(pacientes, embarazos, citas, partos, ecografias, laboratorio),
    [pacientes, embarazos, citas, partos, ecografias, laboratorio]
  );

  // ========== DATOS PARA GRÁFICAS ==========
  const pacientesPorMes = useMemo(() => computePacientesPorMes(pacientes), [pacientes]);
  const embarazosPorTrimestre = useMemo(() => computeEmbarazosPorTrimestre(embarazos), [embarazos]);
  const distribucionRiesgos = useMemo(() => computeDistribucionRiesgos(embarazos), [embarazos]);
  const citasPorEstado = useMemo(() => computeCitasPorEstado(citas), [citas]);
  const partosPorTipo = useMemo(() => computePartosPorTipo(partos), [partos]);
  const ecografiasPorTipo = useMemo(() => computeEcografiasPorTipo(ecografias), [ecografias]);
  const evolucionesPorSemana = useMemo(() => computeEvolucionesPorSemana(evoluciones), [evoluciones]);
  const laboratorioPorEstado = useMemo(() => computeLaboratorioPorEstado(laboratorio), [laboratorio]);
  const radarData = useMemo(() => computeRadarData(kpis), [kpis]);
  const pacientesPorEdad = useMemo(() => computePacientesPorEdad(pacientes), [pacientes]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Cargando datos del sistema…</Text>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container" style={{ padding: '24px', background: 'var(--bg-secondary)', minHeight: '100vh' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2} style={{ margin: 0 }}>
            📊 Dashboard con Gráficas Reales
          </Title>
          <Text type="secondary">
            Estadísticas calculadas en tiempo real desde los datos del sistema
          </Text>
        </Col>
        <Col>
          <Space>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates || [null, null])}
              format="DD/MM/YYYY"
              placeholder={['Fecha inicio', 'Fecha fin']}
            />
            <Select
              value={selectedPeriod}
              onChange={setSelectedPeriod}
              style={{ width: 150 }}
              options={[
                { label: 'Esta semana', value: 'week' },
                { label: 'Este mes', value: 'month' },
                { label: 'Este trimestre', value: 'quarter' },
                { label: 'Este año', value: 'year' }
              ]}
            />
          </Space>
        </Col>
      </Row>

      <DashboardGraficasKpis kpis={kpis} />

      <DashboardGraficasCharts
        kpis={kpis}
        pacientesPorMes={pacientesPorMes}
        embarazosPorTrimestre={embarazosPorTrimestre}
        distribucionRiesgos={distribucionRiesgos}
        citasPorEstado={citasPorEstado}
        partosPorTipo={partosPorTipo}
        ecografiasPorTipo={ecografiasPorTipo}
        evolucionesPorSemana={evolucionesPorSemana}
        laboratorioPorEstado={laboratorioPorEstado}
        radarData={radarData}
        pacientesPorEdad={pacientesPorEdad}
      />

      <Divider />

      {/* Footer con información */}
      <Alert
        message="Datos en Tiempo Real"
        description={`Última actualización: ${dayjs().format('DD/MM/YYYY HH:mm:ss')}. Todas las gráficas se calculan directamente desde los datos del sistema.`}
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </div>
  );
};

export default DashboardGraficasReales;
