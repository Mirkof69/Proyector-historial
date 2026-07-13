import React from 'react';
import { useLocation } from 'react-router-dom';
import { useReducedMotion } from 'framer-motion';
import { useReducedMotionHook } from '../../hooks/useReducedMotion';

interface PageTransitionProps {
  children: React.ReactNode;
}

const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  const location = useLocation();
  const framerReduced = useReducedMotion();
  const prefersReducedMotion = useReducedMotionHook();
  const shouldReduceMotion = framerReduced || prefersReducedMotion;

  const style: React.CSSProperties = shouldReduceMotion
    ? {}
    : {
        animation: 'pageSlideUp 0.25s ease-out',
      };

  // key por ruta: reinicia la animación en CADA navegación (antes solo corría
  // una vez al montar el layout, no al cambiar de pantalla).
  return (
    <div key={location.pathname} style={style}>
      {children}
    </div>
  );
};

export default PageTransition;
