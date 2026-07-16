/**
 * Lógica pura del gráfico de tendencia de laboratorio: transformación de datos
 * y cálculos estadísticos. Extraído de GraficoTendenciaLaboratorio para testeo
 * aislado (sin estado ni JSX).
 */
import dayjs from 'dayjs';

export interface HistoricoData {
  fecha: string;
  valor: number | null;
}

export interface PuntoGrafico {
  fecha: string;
  fechaCompleta: string;
  valor: number;
  minimo?: number;
  maximo?: number;
}

export const transformarHistorico = (
  historico: HistoricoData[],
  valorMinimo?: number,
  valorMaximo?: number,
): PuntoGrafico[] =>
  historico
    .reduce((acc: PuntoGrafico[], h) => {
      if (h.valor !== null) {
        acc.push({
          fecha: dayjs(h.fecha).format('DD/MM/YY'),
          fechaCompleta: dayjs(h.fecha).format('DD/MM/YYYY'),
          valor: h.valor,
          minimo: valorMinimo,
          maximo: valorMaximo,
        });
      }
      return acc;
    }, [])
    .reverse(); // Más antiguo primero

export const calcularPromedio = (data: PuntoGrafico[]): number => {
  if (data.length === 0) return 0;
  const suma = data.reduce((acc, d) => acc + (d.valor || 0), 0);
  return suma / data.length;
};

export const calcularTendencia = (data: PuntoGrafico[]): number => {
  if (data.length < 2) return 0;
  const primerValor = data[0].valor || 0;
  const ultimoValor = data[data.length - 1].valor || 0;
  return ((ultimoValor - primerValor) / primerValor) * 100;
};

export const calcularUltimaVariacion = (data: PuntoGrafico[]): number => {
  if (data.length < 2) return 0;
  const penultimoValor = data[data.length - 2].valor || 0;
  const ultimoValor = data[data.length - 1].valor || 0;
  if (penultimoValor === 0) return 0;
  return ((ultimoValor - penultimoValor) / penultimoValor) * 100;
};

interface RangosEstado {
  valorMinimo?: number;
  valorMaximo?: number;
  criticoBajo?: number;
  criticoAlto?: number;
}

export const getEstadoActual = (data: PuntoGrafico[], rangos: RangosEstado): string => {
  if (data.length === 0) return 'sin-datos';
  const ultimoValor = data[data.length - 1].valor || 0;
  const { valorMinimo, valorMaximo, criticoBajo, criticoAlto } = rangos;
  if (criticoBajo && ultimoValor < criticoBajo) return 'critico-bajo';
  if (criticoAlto && ultimoValor > criticoAlto) return 'critico-alto';
  if (valorMinimo && ultimoValor < valorMinimo) return 'bajo';
  if (valorMaximo && ultimoValor > valorMaximo) return 'alto';
  return 'normal';
};
