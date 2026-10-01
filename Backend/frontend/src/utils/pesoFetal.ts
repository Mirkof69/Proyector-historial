/**
 * Peso fetal estimado (Hadlock 1985), igual que `ecografias/peso_fetal.py`.
 *
 * Las medidas se reciben en MILÍMETROS (como las pide el formulario y las
 * guarda el sistema) y se pasan a centímetros, que es en lo que están los
 * coeficientes publicados. Antes había dos calculadoras y ninguna funcionaba:
 *  - la «básica» metía milímetros en la fórmula de centímetros → ~0 g;
 *  - la «avanzada» tenía los coeficientes cambiados (0,0064·CA + 0,0424·DBP
 *    donde va 0,0064·CC + 0,0424·CA) y no usaba la circunferencia cefálica;
 *  - la de crecimiento fetal y la de la historia clínica también metían
 *    milímetros (y la segunda usaba `Math.exp` en vez de 10^x).
 *
 * Devuelve `null` —nunca 0— si falta una medida o el resultado no es
 * fisiológico (unidades equivocadas). Error declarado de la fórmula: ±15 %.
 */

const PESO_MIN_G = 50;
const PESO_MAX_G = 6500;

const cm = (mm: number | null | undefined): number | null =>
  mm === null || mm === undefined || Number.isNaN(Number(mm)) || Number(mm) <= 0 ? null : Number(mm) / 10;

const validar = (peso: number): number | null =>
  Number.isFinite(peso) && peso >= PESO_MIN_G && peso <= PESO_MAX_G ? Math.round(peso) : null;

/** Hadlock 1985 de 4 parámetros (DBP, CC, CA, LF en mm). */
export const hadlock4p = (dbpMm?: number | null, ccMm?: number | null, caMm?: number | null, lfMm?: number | null): number | null => {
  const [dbp, cc, ca, lf] = [cm(dbpMm), cm(ccMm), cm(caMm), cm(lfMm)];
  if (dbp === null || cc === null || ca === null || lf === null) return null;
  // Hadlock et al., AJOG 1985;151:333
  const log = 1.3596 - 0.00386 * ca * lf + 0.0064 * cc + 0.00061 * dbp * ca + 0.0424 * ca + 0.174 * lf;
  return validar(10 ** log);
};

/** Hadlock 1985 de 3 parámetros (sin CC): cuando la cabeza no se pudo medir. */
export const hadlock3p = (dbpMm?: number | null, caMm?: number | null, lfMm?: number | null): number | null => {
  const [dbp, ca, lf] = [cm(dbpMm), cm(caMm), cm(lfMm)];
  if (dbp === null || ca === null || lf === null) return null;
  const log = 1.335 - 0.0034 * ca * lf + 0.0316 * dbp + 0.0457 * ca + 0.1623 * lf;
  return validar(10 ** log);
};

/** Hadlock 1985 solo con CA y LF (mm). */
export const hadlockCaLf = (caMm?: number | null, lfMm?: number | null): number | null => {
  const [ca, lf] = [cm(caMm), cm(lfMm)];
  if (ca === null || lf === null) return null;
  return validar(10 ** (1.304 + 0.05281 * ca + 0.1938 * lf - 0.004 * ca * lf));
};

/** Hadlock 1985 con CC, CA y LF (mm). */
export const hadlockCcCaLf = (ccMm?: number | null, caMm?: number | null, lfMm?: number | null): number | null => {
  const [cc, ca, lf] = [cm(ccMm), cm(caMm), cm(lfMm)];
  if (cc === null || ca === null || lf === null) return null;
  return validar(10 ** (1.326 - 0.00326 * ca * lf + 0.0107 * cc + 0.0438 * ca + 0.158 * lf));
};

/** El más preciso disponible: 4 parámetros si hay CC, si no 3. */
export const pesoFetalEstimado = (m: { dbp?: number | null; cc?: number | null; ca?: number | null; lf?: number | null }) => {
  const con4 = hadlock4p(m.dbp, m.cc, m.ca, m.lf);
  if (con4 !== null) return { peso: con4, formula: 'Hadlock 1985 (DBP, CC, CA, LF)' };
  const con3 = hadlock3p(m.dbp, m.ca, m.lf);
  if (con3 !== null) return { peso: con3, formula: 'Hadlock 1985 (DBP, CA, LF)' };
  return null;
};
