import { useEffect, useRef, useState } from 'react';

/**
 * Hook de conteo animado para KPIs/estadísticas (premium micro-feedback).
 *
 * Anima el valor desde 0 (o desde el valor anterior) hasta `target` usando
 * requestAnimationFrame con easing easeOutCubic. Respeta
 * `prefers-reduced-motion`: en ese caso devuelve el valor final sin animar.
 *
 * @param target   Valor final a mostrar.
 * @param duration Duración de la animación en ms (default 900).
 * @param decimals Cantidad de decimales del valor devuelto (default 0).
 */
export function useCountUp(target: number, duration = 900, decimals = 0): number {
  const [value, setValue] = useState(0);
  const fromRef = useRef(0);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    const safeTarget = Number.isFinite(target) ? target : 0;

    // Accesibilidad: sin animación si el usuario redujo el movimiento
    const reduceMotion =
      typeof window !== 'undefined' &&
      window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    if (reduceMotion || duration <= 0) {
      fromRef.current = safeTarget;
      setValue(safeTarget);
      return;
    }

    const from = fromRef.current;
    const start = performance.now();
    const factor = 10 ** decimals;

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - (1 - progress) ** 3; // easeOutCubic
      const current = from + (safeTarget - from) * eased;
      setValue(Math.round(current * factor) / factor);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        fromRef.current = safeTarget;
      }
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [target, duration, decimals]);

  return value;
}

export default useCountUp;
