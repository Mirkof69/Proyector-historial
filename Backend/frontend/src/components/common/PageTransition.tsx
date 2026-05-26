import React from 'react';
import { useReducedMotion } from 'framer-motion';
import { useReducedMotionHook } from '../../hooks/useReducedMotion';

interface PageTransitionProps {
  children: React.ReactNode;
}

const PageTransition: React.FC<PageTransitionProps> = ({ children }) => {
  const framerReduced = useReducedMotion();
  const prefersReducedMotion = useReducedMotionHook();
  const shouldReduceMotion = framerReduced || prefersReducedMotion;

  const style: React.CSSProperties = shouldReduceMotion
    ? {}
    : {
        animation: 'pageSlideUp 0.25s ease-out',
      };

  return <div style={style}>{children}</div>;
};

export default PageTransition;
