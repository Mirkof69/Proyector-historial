/**
 * Una sola clasificación del índice de líquido amniótico (ILA, en cm).
 *
 * Copia exacta de backend/ecografias/liquido_amniotico.py: las dos
 * calculadoras tenían umbrales propios y distintos del backend, y la misma
 * medida salía normal en una pantalla y patológica en otra.
 *
 *   ILA ≤ 5        oligohidramnios
 *   5 < ILA < 8    límite bajo
 *   8 ≤ ILA < 25   normal
 *   ILA ≥ 25       polihidramnios: leve < 30, moderado < 35, severo ≥ 35
 */
export type CodigoIla = 'oligohidramnios' | 'limite_bajo' | 'normal' | 'polihidramnios';
export type SeveridadIla = 'normal' | 'alerta' | 'critica';

export interface ClasificacionIla {
  codigo: CodigoIla;
  grado: 'leve' | 'moderado' | 'severo' | null;
  severidad: SeveridadIla;
  texto: string;
  color: 'green' | 'orange' | 'red';
}

const COLOR: Record<SeveridadIla, ClasificacionIla['color']> = {
  normal: 'green',
  alerta: 'orange',
  critica: 'red',
};

export function clasificarIla(ilaCm: number): ClasificacionIla {
  const crear = (
    codigo: CodigoIla,
    severidad: SeveridadIla,
    texto: string,
    grado: ClasificacionIla['grado'] = null,
  ): ClasificacionIla => ({ codigo, grado, severidad, texto, color: COLOR[severidad] });

  if (ilaCm <= 5) return crear('oligohidramnios', 'critica', 'Oligohidramnios');
  if (ilaCm < 8) return crear('limite_bajo', 'alerta', 'ILA en límite bajo');
  if (ilaCm < 25) return crear('normal', 'normal', 'Normal');
  if (ilaCm < 30) return crear('polihidramnios', 'alerta', 'Polihidramnios leve', 'leve');
  if (ilaCm < 35) return crear('polihidramnios', 'critica', 'Polihidramnios moderado', 'moderado');
  return crear('polihidramnios', 'critica', 'Polihidramnios severo', 'severo');
}
