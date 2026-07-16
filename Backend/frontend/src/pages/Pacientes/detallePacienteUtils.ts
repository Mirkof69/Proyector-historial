import dayjs from 'dayjs';

export const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

export const renderVacunaLabel = (entry: any) => `${entry.name}: ${entry.value}`;

export const getEstadoCivilConGenero = (estadoCivil: string | undefined, genero: string | undefined): string => {
  if (!estadoCivil) return '-';
  const esFemenino = genero === 'femenino';
  switch (estadoCivil) {
    case 'soltero': return esFemenino ? 'Soltera' : 'Soltero';
    case 'casado': return esFemenino ? 'Casada' : 'Casado';
    case 'divorciado': return esFemenino ? 'Divorciada' : 'Divorciado';
    case 'viudo': return esFemenino ? 'Viuda' : 'Viudo';
    case 'union_libre': return 'Unión Libre';
    default: return estadoCivil;
  }
};

// Datos para gráficas
export const getTriajesTimeline = (triajes: any[]) => {
  return triajes
    .slice(-10)
    .map(t => ({
      fecha: dayjs(t.fecha_hora || t.fecha_registro).format('DD/MM'),
      PA_Sistolica: t.presion_sistolica || 0,
      PA_Diastolica: t.presion_diastolica || 0,
      FC: t.frecuencia_cardiaca || 0,
      Temp: t.temperatura || 0,
    }));
};

export const getEstadisticasVacunas = (vacunas: any[]) => {
  const conteo: { [key: string]: number } = {};
  vacunas.forEach(v => {
    const tipo = v.tipo_vacuna_nombre || v.tipo_vacuna_info?.nombre || 'Desconocida';
    conteo[tipo] = (conteo[tipo] || 0) + 1;
  });
  return Object.entries(conteo).map(([name, value]) => ({ name, value }));
};

export const getNotasPorTipo = (notasEvolucion: any[], tipo: string) => {
  const conteo: { [key: string]: number } = {};
  notasEvolucion.forEach(n => {
    const tipo = n.tipo_consulta || 'otro';
    conteo[tipo] = (conteo[tipo] || 0) + 1;
  });
  return Object.entries(conteo).map(([tipo, cantidad]) => ({ tipo, cantidad }));
};
