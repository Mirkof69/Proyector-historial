import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';

dayjs.extend(isBetween);

// Colores para gráficas
export const COLORS = {
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
export const PIE_COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#fa8c16', '#eb2f96'];

// Helper de sanitización de datos
export const safeNum = (value: any): number => {
  if (value === null || value === undefined) return 0;
  const num = typeof value === 'string' ? parseFloat(value) : Number(value);
  return isNaN(num) ? 0 : num;
};

export const renderPieLabel = (entry: any) => `${entry.name}: ${entry.value}`;
export const renderPartosLabel = (entry: any) => `${entry.tipo}: ${entry.cantidad}`;
export const RADAR_DOMAIN = [0, 100];

// ========== KPIs CALCULADOS ==========
export const computeKpis = (
  pacientes: any[] | undefined,
  embarazos: any[] | undefined,
  citas: any[] | undefined,
  partos: any[] | undefined,
  ecografias: any[] | undefined,
  laboratorio: any[] | undefined,
) => {
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
};

export type DashboardKpis = ReturnType<typeof computeKpis>;

// Gráfica: Pacientes por mes (últimos 6 meses)
export const computePacientesPorMes = (pacientes: any[] | undefined) => {
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
};

// Gráfica: Embarazos por trimestre
export const computeEmbarazosPorTrimestre = (embarazos: any[] | undefined) => {
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
};

// Gráfica: Distribución de riesgos
export const computeDistribucionRiesgos = (embarazos: any[] | undefined) => {
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
};

// Gráfica: Citas por estado
export const computeCitasPorEstado = (citas: any[] | undefined) => {
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
};

// Gráfica: Partos por tipo
export const computePartosPorTipo = (partos: any[] | undefined) => {
  if (!partos) return [];
  const normal = partos.filter(p => p.tipo_parto === 'vaginal' || p.tipo_parto === 'normal').length;
  const cesarea = partos.filter(p => p.tipo_parto === 'cesarea').length;
  const instrumental = partos.filter(p => p.tipo_parto === 'instrumental').length;

  return [
    { tipo: 'Normal/Vaginal', cantidad: normal, color: COLORS.success },
    { tipo: 'Cesárea', cantidad: cesarea, color: COLORS.warning },
    { tipo: 'Instrumental', cantidad: instrumental, color: COLORS.purple }
  ].filter(item => item.cantidad > 0);
};

// Gráfica: Ecografías por tipo (últimos 3 meses)
export const computeEcografiasPorTipo = (ecografias: any[] | undefined) => {
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
};

// Gráfica: Evoluciones por semana (últimas 8 semanas)
export const computeEvolucionesPorSemana = (evoluciones: any[] | undefined) => {
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
};

// Gráfica: Laboratorio por estado
export const computeLaboratorioPorEstado = (laboratorio: any[] | undefined) => {
  if (!laboratorio) return [];
  const pendiente = laboratorio.filter(l => l.estado === 'pendiente').length;
  const proceso = laboratorio.filter(l => l.estado === 'en_proceso').length;
  const completado = laboratorio.filter(l => l.estado === 'completado' || l.estado === 'finalizado').length;

  return [
    { name: 'Pendiente', value: pendiente, color: COLORS.warning },
    { name: 'En Proceso', value: proceso, color: COLORS.primary },
    { name: 'Completado', value: completado, color: COLORS.success }
  ].filter(item => item.value > 0);
};

// Gráfica: Radar Chart - Indicadores de Rendimiento del Sistema
export const computeRadarData = (kpis: DashboardKpis) => {
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
};

// Gráfica: Distribución de Pacientes por Grupo Etario - USANDO PIE_COLORS
export const computePacientesPorEdad = (pacientes: any[] | undefined) => {
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
};
