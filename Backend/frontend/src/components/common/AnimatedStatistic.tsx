import React from 'react';
import { Statistic } from 'antd';
import { useCountUp } from '../../hooks/useCountUp';

/**
 * Statistic de antd con conteo animado (premium micro-feedback).
 *
 * Anima el valor numérico desde el valor anterior hasta el nuevo con
 * requestAnimationFrame + easeOutCubic. Respeta prefers-reduced-motion
 * (vía useCountUp). Uso: reemplazo drop-in de <Statistic value={n} />
 * cuando `value` es numérico.
 */
const AnimatedStatistic: React.FC<
  React.ComponentProps<typeof Statistic> & { value: number; decimals?: number }
> = ({ value, decimals = 0, ...rest }) => {
  const animated = useCountUp(value, 900, decimals);
  return <Statistic {...rest} value={animated} />;
};

export default AnimatedStatistic;
