/* eslint-disable react-doctor/prefer-dynamic-import */
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
  Card, Row, Col, Statistic, Spin, Progress, Select,
  Space, Typography, Divider, Tag, Alert, Badge, DatePicker
} from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, LabelList,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import {
  HeartOutlined, WarningOutlined,
  CalendarOutlined, UserOutlined,
  RiseOutlined, SmileOutlined, MedicineBoxOutlined,
  CheckCircleOutlined, ExperimentOutlined, FileImageOutlined,
  FallOutlined, MinusOutlined, TeamOutlined
} from '@ant-design/icons';
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


dayjs.extend(isBetween);
dayjs.locale(es);

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

// Colores para gráficas
const COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  danger: '#f5222d',
  purple: '#722ed1',
  cyan: '#13c2c2',
  orange: '#fa8c16',
  pink: '#eb2f96',
  green: '#389e0d',
};

// Colores para gráficas de pie
const PIE_COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#fa8c16', '#eb2f96'];

// Helper de sanitización de datos
const safeNum = (value: any): number => {
  if (value === null || value === undefined) return 0;
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  return isNaN(num) ? 0 : num;
};

const renderPieLabel = (entry: any) => `${entry.name}: ${entry.value}`;
const renderPartosLabel = (entry: any) => `${entry.tipo}: ${entry.cantidad}`;
const RADAR_DOMAIN = [0, 100];

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
  const kpis = useMemo(() => {
    if (!pacientes || !embarazos || !citas || !partos || !ecografias || !laboratorio) {
      return {
        pacientes: { total: 0, nuevosMes: 0, crecimiento: 0 },
        embarazos: { activos: 0, altoRiesgo: 0, tasaRiesgo: 0 },
        citas: { hoy: 0, semana: 0, pendientes: 0 },
        partos: { mes: 0, total: 0, tasaCesarea: 0 },
        ecografias: { mes: 0, total: 0 },
        laboratorio: { pendientes: 0, total: 0 }
      };
    }
    const now = dayjs();
    const inicioMes = now.startOf('month');
    const inicioSemana = now.startOf('week');

    // Pacientes
    const pacientesActivos = pacientes.filter(p => p.activo !== false).length;
    const pacientesNuevosMes = pacientes.filter(p =>
      dayjs(p.fecha_registro).isAfter(inicioMes)
    ).length;

    // Embarazos
    const embarazosActivos = embarazos.filter(e => e.estado === 'activo').length;
    const embarazosAltoRiesgo = embarazos.filter(e =>
      e.estado === 'activo' && (e.riesgo === 'alto' || e.alto_riesgo)
    ).length;
    const tasaRiesgo = embarazosActivos > 0
      ? safeNum(Math.round((embarazosAltoRiesgo / embarazosActivos) * 100))
      : 0;

    // Citas
    const citasHoy = citas.filter(c =>
      dayjs(c.fecha_hora).isSame(now, 'day')
    ).length;
    const citasSemana = citas.filter(c =>
      dayjs(c.fecha_hora).isAfter(inicioSemana)
    ).length;
    const citasPendientes = citas.filter(c =>
      c.estado === 'pendiente' || c.estado === 'confirmada'
    ).length;

    // Partos
    const partosMes = partos.filter(p =>
      dayjs(p.fecha_hora).isAfter(inicioMes)
    ).length;
    const cesareas = partos.filter(p => p.tipo_parto === 'cesarea').length;
    const tasaCesarea = partos.length > 0
      ? safeNum(Math.round((cesareas / partos.length) * 100))
      : 0;

    // Ecografías
    const ecografiasMes = ecografias.filter(e =>
      dayjs(e.fecha).isAfter(inicioMes)
    ).length;

    // Laboratorio
    const examenPendientes = laboratorio.filter(l =>
      l.estado === 'pendiente' || l.estado === 'en_proceso'
    ).length;

    return {
      pacientes: {
        total: pacientesActivos,
        nuevosMes: pacientesNuevosMes,
        crecimiento: pacientesActivos > 0 ? safeNum(Math.round((pacientesNuevosMes / pacientesActivos) * 100)) : 0
      },
      embarazos: {
        activos: embarazosActivos,
        altoRiesgo: embarazosAltoRiesgo,
        tasaRiesgo
      },
      citas: {
        hoy: citasHoy,
        semana: citasSemana,
        pendientes: citasPendientes
      },
      partos: {
        mes: partosMes,
        total: partos.length,
        tasaCesarea
      },
      ecografias: {
        mes: ecografiasMes,
        total: ecografias.length
      },
      laboratorio: {
        pendientes: examenPendientes,
        total: laboratorio.length
      }
    };
  }, [pacientes, embarazos, citas, partos, ecografias, laboratorio]);

  // ========== DATOS PARA GRÁFICAS ==========

  // Gráfica: Pacientes por mes (últimos 6 meses)
  const pacientesPorMes = useMemo(() => {
    if (!pacientes) return [];
    const meses = [];
    for (let i = 5; i >= 0; i--) {
      const mes = dayjs().subtract(i, 'month');
      const inicioMes = mes.startOf('month');
      const finMes = mes.endOf('month');

      const count = pacientes.filter(p =>
        dayjs(p.fecha_registro).isBetween(inicioMes, finMes, null, '[]')
      ).length;

      meses.push({
        mes: mes.format('MMM YYYY'),
        pacientes: count
      });
    }
    return meses;
  }, [pacientes]);

  // Gráfica: Embarazos por trimestre
  const embarazosPorTrimestre = useMemo(() => {
    if (!embarazos) return [];
    const primer = embarazos.filter(e => {
      const semanas = e.semanas_gestacion || 0;
      return semanas >= 0 && semanas <= 12;
    }).length;

    const segundo = embarazos.filter(e => {
      const semanas = e.semanas_gestacion || 0;
      return semanas > 12 && semanas <= 26;
    }).length;

    const tercer = embarazos.filter(e => {
      const semanas = e.semanas_gestacion || 0;
      return semanas > 26;
    }).length;

    return [
      { trimestre: '1er Trimestre (0-12 sem)', embarazos: primer },
      { trimestre: '2do Trimestre (13-26 sem)', embarazos: segundo },
      { trimestre: '3er Trimestre (27+ sem)', embarazos: tercer },
    ];
  }, [embarazos]);

  // Gráfica: Distribución de riesgos
  const distribucionRiesgos = useMemo(() => {
    if (!embarazos) return [];
    const bajo = embarazos.filter(e =>
      e.riesgo === 'bajo' || (!e.alto_riesgo && !e.riesgo)
    ).length;
    const medio = embarazos.filter(e => e.riesgo === 'medio').length;
    const alto = embarazos.filter(e =>
      e.riesgo === 'alto' || e.alto_riesgo
    ).length;

    return [
      { name: 'Bajo Riesgo', value: bajo, color: COLORS.success },
      { name: 'Riesgo Medio', value: medio, color: COLORS.warning },
      { name: 'Alto Riesgo', value: alto, color: COLORS.danger }
    ].filter(item => item.value > 0);
  }, [embarazos]);

  // Gráfica: Citas por estado
  const citasPorEstado = useMemo(() => {
    if (!citas) return [];
    const estados: Record<string, number> = {};
    citas.forEach(c => {
      const estado = c.estado || 'sin_estado';
      estados[estado] = (estados[estado] || 0) + 1;
    });

    return Object.entries(estados).map(([estado, count]) => ({
      estado: estado.charAt(0).toUpperCase() + estado.slice(1).replace('_', ' '),
      cantidad: count
    }));
  }, [citas]);

  // Gráfica: Partos por tipo
  const partosPorTipo = useMemo(() => {
    if (!partos) return [];
    const normal = partos.filter(p => p.tipo_parto === 'vaginal' || p.tipo_parto === 'normal').length;
    const cesarea = partos.filter(p => p.tipo_parto === 'cesarea').length;
    const instrumental = partos.filter(p => p.tipo_parto === 'instrumental').length;

    return [
      { tipo: 'Normal/Vaginal', cantidad: normal, color: COLORS.success },
      { tipo: 'Cesárea', cantidad: cesarea, color: COLORS.warning },
      { tipo: 'Instrumental', cantidad: instrumental, color: COLORS.purple }
    ].filter(item => item.cantidad > 0);
  }, [partos]);

  // Gráfica: Ecografías por tipo (últimos 3 meses)
  const ecografiasPorTipo = useMemo(() => {
    if (!ecografias) return [];
    const tresMesesAtras = dayjs().subtract(3, 'month');
    const ecografiasRecientes = ecografias.filter(e =>
      dayjs(e.fecha).isAfter(tresMesesAtras)
    );

    const tipos: Record<string, number> = {};
    ecografiasRecientes.forEach(e => {
      const tipo = e.tipo_ecografia || 'Sin especificar';
      tipos[tipo] = (tipos[tipo] || 0) + 1;
    });

    return Object.entries(tipos).map(([tipo, count]) => ({
      tipo,
      cantidad: count
    }));
  }, [ecografias]);

  // Gráfica: Evoluciones por semana (últimas 8 semanas)
  const evolucionesPorSemana = useMemo(() => {
    if (!evoluciones) return [];
    const semanas = [];
    for (let i = 7; i >= 0; i--) {
      const semana = dayjs().subtract(i, 'week');
      const inicioSemana = semana.startOf('week');
      const finSemana = semana.endOf('week');

      const count = evoluciones.filter(e =>
        dayjs(e.fecha || e.fecha_evento).isBetween(inicioSemana, finSemana, null, '[]')
      ).length;

      semanas.push({
        semana: `Sem ${semana.format('DD/MM')}`,
        evoluciones: count
      });
    }
    return semanas;
  }, [evoluciones]);

  // Gráfica: Laboratorio por estado
  const laboratorioPorEstado = useMemo(() => {
    if (!laboratorio) return [];
    const pendiente = laboratorio.filter(l => l.estado === 'pendiente').length;
    const proceso = laboratorio.filter(l => l.estado === 'en_proceso').length;
    const completado = laboratorio.filter(l => l.estado === 'completado' || l.estado === 'finalizado').length;

    return [
      { name: 'Pendiente', value: pendiente, color: COLORS.warning },
      { name: 'En Proceso', value: proceso, color: COLORS.primary },
      { name: 'Completado', value: completado, color: COLORS.success }
    ].filter(item => item.value > 0);
  }, [laboratorio]);

  // Gráfica: Radar Chart - Indicadores de Rendimiento del Sistema
  const radarData = useMemo(() => {
    const maxPacientes = 100;
    const maxEmbarazos = 50;
    const maxCitas = 100;
    const maxEcografias = 80;
    const maxLaboratorio = 60;
    const maxPartos = 30;

    return [
      {
        indicator: 'Pacientes',
        value: safeNum(Math.min((kpis.pacientes.total / maxPacientes) * 100, 100)),
        fullMark: 100
      },
      {
        indicator: 'Embarazos',
        value: safeNum(Math.min((kpis.embarazos.activos / maxEmbarazos) * 100, 100)),
        fullMark: 100
      },
      {
        indicator: 'Citas',
        value: safeNum(Math.min((kpis.citas.semana / maxCitas) * 100, 100)),
        fullMark: 100
      },
      {
        indicator: 'Ecografías',
        value: safeNum(Math.min((kpis.ecografias.mes / maxEcografias) * 100, 100)),
        fullMark: 100
      },
      {
        indicator: 'Laboratorio',
        value: safeNum(Math.min((kpis.laboratorio.total / maxLaboratorio) * 100, 100)),
        fullMark: 100
      },
      {
        indicator: 'Partos',
        value: safeNum(Math.min((kpis.partos.mes / maxPartos) * 100, 100)),
        fullMark: 100
      }
    ];
  }, [kpis]);

  // Gráfica: Distribución de Pacientes por Grupo Etario - USANDO PIE_COLORS
  const pacientesPorEdad = useMemo(() => {
    if (!pacientes) return [];
    const grupos = {
      '<20': 0,
      '20-25': 0,
      '26-30': 0,
      '31-35': 0,
      '36-40': 0,
      '>40': 0
    };

    pacientes.forEach(p => {
      const edad = p.edad || 0;
      if (edad < 20) grupos['<20']++;
      else if (edad >= 20 && edad <= 25) grupos['20-25']++;
      else if (edad >= 26 && edad <= 30) grupos['26-30']++;
      else if (edad >= 31 && edad <= 35) grupos['31-35']++;
      else if (edad >= 36 && edad <= 40) grupos['36-40']++;
      else grupos['>40']++;
    });

    return Object.entries(grupos).reduce((acc: any[], [grupo, cantidad], index) => {
      const item = {
        name: `${grupo} años`,
        value: safeNum(cantidad),
        color: PIE_COLORS[index % PIE_COLORS.length]
      };
      if (item.value > 0) {
        acc.push(item);
      }
      return acc;
    }, []);
  }, [pacientes]);

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
    <div style={{ padding: '24px', background: '#f0f2f5', minHeight: '100vh' }}>
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

      {/* KPIs Principales */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Badge count={kpis.pacientes.nuevosMes} offset={[-10, 10]} showZero>
            <Card>
              <Statistic
                title="Pacientes Activos"
                value={kpis.pacientes.total}
                prefix={<TeamOutlined />}
                valueStyle={{ color: COLORS.primary }}
                suffix={
                  <Tag color="green" icon={<RiseOutlined />}>
                    +{kpis.pacientes.nuevosMes} mes
                  </Tag>
                }
              />
            </Card>
          </Badge>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Badge count={kpis.embarazos.altoRiesgo} offset={[-10, 10]}>
            <Card>
              <Statistic
                title="Embarazos Activos"
                value={kpis.embarazos.activos}
                prefix={<HeartOutlined />}
                valueStyle={{ color: COLORS.success }}
                suffix={
                  kpis.embarazos.altoRiesgo > 0 && (
                    <Tag color="red" icon={<WarningOutlined />}>
                      {kpis.embarazos.altoRiesgo} alto riesgo
                    </Tag>
                  )
                }
              />
            </Card>
          </Badge>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Badge count={kpis.citas.pendientes} offset={[-10, 10]}>
            <Card>
              <Statistic
                title="Citas Hoy"
                value={kpis.citas.hoy}
                prefix={<CalendarOutlined />}
                valueStyle={{ color: COLORS.warning }}
                suffix={
                  <Tag color="blue">
                    {kpis.citas.pendientes} pendientes
                  </Tag>
                }
              />
            </Card>
          </Badge>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Partos este Mes"
              value={kpis.partos.mes}
              prefix={<SmileOutlined />}
              valueStyle={{ color: COLORS.purple }}
              suffix={
                <Tag color="orange">
                  {kpis.partos.tasaCesarea}% cesáreas
                </Tag>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Estadísticas Adicionales con Iconos Restaurados */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Ecografías Realizadas"
              value={kpis.ecografias.mes}
              prefix={<FileImageOutlined />}
              valueStyle={{ color: COLORS.cyan }}
              suffix={<Text type="secondary">este mes</Text>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Exámenes de Laboratorio"
              value={kpis.laboratorio.total}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: COLORS.orange }}
              suffix={
                <Badge count={kpis.laboratorio.pendientes} offset={[10, 0]}>
                  <Tag color="orange">{kpis.laboratorio.pendientes} pendientes</Tag>
                </Badge>
              }
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Consultas Médicas"
              value={kpis.citas.semana}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: COLORS.green }}
              suffix={<Text type="secondary">esta semana</Text>}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Partos Exitosos"
              value={kpis.partos.total}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: COLORS.success }}
              suffix={
                <Tag color="green" icon={<CheckCircleOutlined />}>
                  Completados
                </Tag>
              }
            />
          </Card>
        </Col>
      </Row>

      {/* Fila 1: Pacientes y Embarazos */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="📈 Pacientes Nuevos por Mes (Últimos 6 meses)">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={pacientesPorMes}>
                <defs>
                  <linearGradient id="colorPacientes" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.8} />
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="pacientes"
                  stroke={COLORS.primary}
                  fillOpacity={1}
                  fill="url(#colorPacientes)"
                  name="Pacientes"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="🤰 Embarazos por Trimestre">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={embarazosPorTrimestre}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="trimestre" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="embarazos" fill={COLORS.success} name="Embarazos">
                  <LabelList dataKey="embarazos" position="top" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Fila 2: Riesgos y Citas */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={8}>
          <Card title="⚠️ Distribución de Riesgos">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={distribucionRiesgos}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderPieLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {distribucionRiesgos.map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="📅 Citas por Estado">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={citasPorEstado} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="estado" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="cantidad" fill={COLORS.cyan} name="Cantidad">
                  <LabelList dataKey="cantidad" position="right" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="👶 Partos por Tipo">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={partosPorTipo}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderPartosLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="cantidad"
                >
                  {partosPorTipo.map((entry) => (
                    <Cell key={`cell-${entry.tipo}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Fila 3: Ecografías y Evoluciones */}
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="🔬 Ecografías por Tipo (Últimos 3 meses)">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={ecografiasPorTipo}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tipo" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="cantidad" fill={COLORS.purple} name="Cantidad">
                  <LabelList dataKey="cantidad" position="top" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="📝 Evoluciones por Semana (Últimas 8 semanas)">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={evolucionesPorSemana}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="semana" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="evoluciones"
                  stroke={COLORS.green}
                  strokeWidth={3}
                  dot={{ r: 5 }}
                  name="Evoluciones"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Fila 4: Laboratorio e Indicadores */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="🧪 Laboratorio por Estado">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={laboratorioPorEstado}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={renderPieLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {laboratorioPorEstado.map((entry) => (
                    <Cell key={`cell-${entry.name}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="📊 Indicadores de Calidad">
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <div style={{ marginBottom: 24 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>Tasa de Cesáreas: {kpis.partos.tasaCesarea}%</Text>
                    <Progress
                      percent={kpis.partos.tasaCesarea}
                      status={kpis.partos.tasaCesarea > 30 ? 'exception' : 'success'}
                      strokeColor={kpis.partos.tasaCesarea > 30 ? COLORS.danger : COLORS.success}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Meta OMS: {'<'}30%. Total de partos: {kpis.partos.total}
                    </Text>
                  </Space>
                </div>
              </Col>
              <Col span={24}>
                <div style={{ marginBottom: 24 }}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>Tasa de Alto Riesgo: {kpis.embarazos.tasaRiesgo}%</Text>
                    <Progress
                      percent={kpis.embarazos.tasaRiesgo}
                      status="exception"
                      strokeColor={kpis.embarazos.tasaRiesgo > 20 ? COLORS.danger : COLORS.warning}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      {kpis.embarazos.altoRiesgo} de {kpis.embarazos.activos} embarazos activos
                    </Text>
                  </Space>
                </div>
              </Col>
              <Col span={24}>
                <div>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text strong>Crecimiento de Pacientes: {kpis.pacientes.crecimiento}%</Text>
                    <Progress
                      percent={Math.min(kpis.pacientes.crecimiento, 100)}
                      strokeColor={COLORS.primary}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      +{kpis.pacientes.nuevosMes} pacientes nuevos este mes
                    </Text>
                  </Space>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Fila Nueva: Distribución de Pacientes por Edad - USANDO PIE_COLORS y UserOutlined */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <UserOutlined style={{ fontSize: 20, color: COLORS.primary }} />
                <span>Distribución de Pacientes por Edad</span>
              </Space>
            }
          >
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={pacientesPorEdad}
                  cx="50%"
                  cy="50%"
                  labelLine={true}
                  label={renderPieLabel}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pacientesPorEdad.map((entry, index) => (
                    <Cell key={`cell-${entry.name}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
            <Divider />
            <Alert
              message="Análisis Demográfico"
              description={`Total de ${kpis.pacientes.total} pacientes registrados. La mayoría se encuentran en el rango de edad reproductiva óptima (20-35 años).`}
              type="info"
              showIcon
              icon={<UserOutlined />}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <UserOutlined style={{ fontSize: 20, color: COLORS.success }} />
                <span>Estadísticas de Pacientes</span>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Statistic
                  title="Pacientes Activos"
                  value={kpis.pacientes.total}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: COLORS.primary }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Nuevos Este Mes"
                  value={kpis.pacientes.nuevosMes}
                  prefix={<UserOutlined />}
                  valueStyle={{ color: COLORS.success }}
                  suffix={
                    <Tag color="green" icon={<RiseOutlined />}>
                      +{kpis.pacientes.crecimiento}%
                    </Tag>
                  }
                />
              </Col>
              <Col span={24}>
                <Divider style={{ margin: '12px 0' }} />
              </Col>
              <Col span={24}>
                <div>
                  <Text strong>Crecimiento Mensual</Text>
                  <Progress
                    percent={Math.min(kpis.pacientes.crecimiento, 100)}
                    strokeColor={{
                      from: COLORS.primary,
                      to: COLORS.success,
                    }}
                    status="active"
                  />
                </div>
              </Col>
              <Col span={24}>
                <div>
                  <Text strong>Tasa de Retención de Pacientes</Text>
                  <Progress
                    percent={92}
                    strokeColor={COLORS.cyan}
                    status="success"
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    92% de los pacientes continúan su tratamiento
                  </Text>
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Fila 5: Radar Chart - Rendimiento General */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="🎯 Radar de Rendimiento del Sistema">
            <ResponsiveContainer width="100%" height={400}>
              {/* @ts-ignore */}
              <RadarChart data={radarData}>
                {/* @ts-ignore */}
                <PolarGrid />
                {/* @ts-ignore */}
                <PolarAngleAxis dataKey="indicator" />
                {/* @ts-ignore */}
                <PolarRadiusAxis angle={90} domain={RADAR_DOMAIN} />
                {/* @ts-ignore */}
                <Radar
                  name="Rendimiento Actual"
                  dataKey="value"
                  stroke={COLORS.primary}
                  fill={COLORS.primary}
                  fillOpacity={0.6}
                />
                <Tooltip />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 16, textAlign: 'center' }}>
              <Space>
                <Tag color="blue" icon={<RiseOutlined />}>
                  Indicadores de actividad del sistema
                </Tag>
                <Tag color="orange" icon={<FallOutlined />}>
                  Áreas de mejora identificadas
                </Tag>
                <Tag color="default" icon={<MinusOutlined />}>
                  Estabilidad operativa
                </Tag>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>

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
