/**
 * Curva del partograma con las líneas de alerta y de acción de la OMS
 * (partograma compuesto, OMS 1994): la fase activa empieza en el primer tacto
 * con 4 cm o más; desde ahí la línea de ALERTA avanza 1 cm por hora hasta
 * 10 cm, y la de ACCIÓN es la misma línea 4 horas a la derecha. Un tacto por
 * debajo de la alerta (a su derecha) indica progreso lento; por debajo de la
 * acción, que hay que intervenir.
 */
export const DILATACION_FASE_ACTIVA = 4;
export const HORAS_ALERTA_A_ACCION = 4;

export interface PuntoCurva { horas: number; dilatacion: number; fcf: number | null }
export interface Recta { horas: number; dilatacion: number }

export interface CurvaPartograma {
  puntos: PuntoCurva[];
  alerta: Recta[];
  accion: Recta[];
  cruzaAlerta: boolean;
  cruzaAccion: boolean;
  /** Avance medio en fase activa (cm/h), o null si hay menos de dos tactos en ella. */
  velocidadActiva: number | null;
}

interface Registro { hora_registro: string; dilatacion_cervical: number; fcf_baseline?: number | null }

const redondear = (v: number) => Math.round(v * 100) / 100;

export function curvaPartograma(registros: Registro[]): CurvaPartograma {
  const ordenados = [...registros]
    .filter((r) => r.hora_registro && Number.isFinite(Number(r.dilatacion_cervical)))
    .sort((a, b) => new Date(a.hora_registro).getTime() - new Date(b.hora_registro).getTime());
  if (ordenados.length === 0) {
    return { puntos: [], alerta: [], accion: [], cruzaAlerta: false, cruzaAccion: false, velocidadActiva: null };
  }
  const t0 = new Date(ordenados[0].hora_registro).getTime();
  const puntos = ordenados.map((r) => ({
    horas: redondear((new Date(r.hora_registro).getTime() - t0) / 3_600_000),
    dilatacion: Number(r.dilatacion_cervical),
    fcf: r.fcf_baseline ?? null,
  }));

  const inicio = puntos.find((p) => p.dilatacion >= DILATACION_FASE_ACTIVA);
  if (!inicio) {
    return { puntos, alerta: [], accion: [], cruzaAlerta: false, cruzaAccion: false, velocidadActiva: null };
  }
  const horasHasta10 = 10 - inicio.dilatacion;
  const alerta = [{ horas: inicio.horas, dilatacion: inicio.dilatacion },
    { horas: redondear(inicio.horas + horasHasta10), dilatacion: 10 }];
  const accion = alerta.map((p) => ({ horas: redondear(p.horas + HORAS_ALERTA_A_ACCION), dilatacion: p.dilatacion }));

  const esperada = (horas: number, desplazamiento: number) =>
    Math.min(10, inicio.dilatacion + (horas - inicio.horas - desplazamiento));
  const activos = puntos.filter((p) => p.horas >= inicio.horas);
  const cruzaAlerta = activos.some((p) => p.dilatacion < esperada(p.horas, 0) - 1e-9);
  const cruzaAccion = activos.some((p) => p.horas >= inicio.horas + HORAS_ALERTA_A_ACCION
    && p.dilatacion < esperada(p.horas, HORAS_ALERTA_A_ACCION) - 1e-9);
  const ultimo = activos[activos.length - 1];
  const velocidadActiva = activos.length >= 2 && ultimo.horas > inicio.horas
    ? redondear((ultimo.dilatacion - inicio.dilatacion) / (ultimo.horas - inicio.horas))
    : null;

  return { puntos, alerta, accion, cruzaAlerta, cruzaAccion, velocidadActiva };
}
