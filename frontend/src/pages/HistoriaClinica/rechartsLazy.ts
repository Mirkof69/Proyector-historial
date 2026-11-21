import { lazy } from 'react';

// Recharts cargado de forma lazy (idéntico al baseline: sin Suspense propio).
export const ComposedChart = lazy(() => import('recharts').then(mod => ({ default: mod.ComposedChart })) as any);
export const Line = lazy(() => import('recharts').then(mod => ({ default: mod.Line })) as any);
export const Bar = lazy(() => import('recharts').then(mod => ({ default: mod.Bar })) as any);
export const XAxis = lazy(() => import('recharts').then(mod => ({ default: mod.XAxis })) as any);
export const YAxis = lazy(() => import('recharts').then(mod => ({ default: mod.YAxis })) as any);
export const CartesianGrid = lazy(() => import('recharts').then(mod => ({ default: mod.CartesianGrid })) as any);
export const RechartsTooltip = lazy(() => import('recharts').then(mod => ({ default: mod.Tooltip })) as any);
export const Legend = lazy(() => import('recharts').then(mod => ({ default: mod.Legend })) as any);
export const ResponsiveContainer = lazy(() => import('recharts').then(mod => ({ default: mod.ResponsiveContainer })) as any);
export const ReferenceArea = lazy(() => import('recharts').then(mod => ({ default: mod.ReferenceArea })) as any);
export const Area = lazy(() => import('recharts').then(mod => ({ default: mod.Area })) as any);
