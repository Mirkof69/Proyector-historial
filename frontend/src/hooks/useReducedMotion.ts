import { useReducedMotion } from 'framer-motion';
import { useState } from 'react';
import { useIsomorphicLayoutEffect } from 'framer-motion';

/**
 * Hook para detectar preferencia de movimiento reducido del usuario.
 * Combina framer-motion's useReducedMotion con CSS media query fallback.
 * WCAG 2.3.3 - Animation from Interactions
 */
export const useReducedMotionHook = (): boolean => {
  const framerReduced = useReducedMotion();
  const [prefersReduced, setPrefersReduced] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  useIsomorphicLayoutEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReduced(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return framerReduced || prefersReduced;
};
