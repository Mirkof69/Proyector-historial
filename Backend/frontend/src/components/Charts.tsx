/**
 * =============================================================================
 * CHARTS - COMPONENTE DE GRÁFICAS REUTILIZABLE
 * =============================================================================
 * Wrapper de Recharts con configuraciones predefinidas para el sistema médico
 * Soporte para múltiples tipos de gráficas con temas
 * =============================================================================
 */

import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  AreaChart, Area, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import './Charts.css';

// ==========================================
// TIPOS E INTERFACES
// ==========================================

type ChartType =
    | 'line'
    | 'bar'
    | 'area'
    | 'pie'
    | 'radar'
    | 'scatter'
    | 'composed';

interface ChartDataPoint {
    [key: string]: string | number;
}

interface ChartSeries {
    dataKey: string;
    name?: string;
    color?: string;
    type?: 'line' | 'bar' | 'area';
    strokeWidth?: number;
    fill?: boolean;
}

interface ChartConfig {
    type: ChartType;
    data: ChartDataPoint[];
    series: ChartSeries[];
    xAxisKey?: string;
    yAxisKey?: string;
    title?: string;
    subtitle?: string;
    height?: number;
    loading?: boolean;
    showGrid?: boolean;
    showLegend?: boolean;
    showTooltip?: boolean;
    colors?: string[];
    customTooltip?: (props: any) => React.ReactNode;
    onDataClick?: (data: any) => void;
    animate?: boolean;
    stacked?: boolean;
}

// ==========================================
// COLORES PREDEFINIDOS
// ==========================================

// Animación de entrada consistente para todas las gráficas: suave y breve
// (no distrae al médico que revisa datos bajo presión de tiempo).
const CHART_ANIM = {
    animationDuration: 800,
    animationBegin: 0,
    animationEasing: 'ease-out' as const,
};

const CHART_COLORS = {
    primary: ['#1890ff', '#40a9ff', '#69c0ff', '#91d5ff', '#bae7ff'],
    medical: ['#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff'],
    success: ['#52c41a', '#73d13d', '#95de64', '#b7eb8f', '#d9f7be'],
    warning: ['#faad14', '#ffc53d', '#ffd666', '#ffe58f', '#fff1b8'],
    error: ['#f5222d', '#ff4d4f', '#ff7875', '#ffa39e', '#ffccc7'],
    info: ['#13c2c2', '#36cfc9', '#5cdbd3', '#87e8de', '#b5f5ec'],
    gradient: ['#1890ff', '#722ed1', '#eb2f96', '#f5222d', '#fa8c16'],
    prenatal: ['#722ed1', '#9254de', '#b37feb', '#d3adf7', '#efdbff'],
    laboratorio: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#13c2c2']
};

// ==========================================
// TOOLTIPS PERSONALIZADOS
// ==========================================

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    return (
        <div className="chart-tooltip">
            <p className="chart-tooltip__label">{label}</p>
            {payload.map((entry: any) => (
                <div key={`item-${entry.name}`} className="chart-tooltip__item">
                    <span
                        className="chart-tooltip__dot"
                        style={{ backgroundColor: entry.color }}
                    />
                    <span className="chart-tooltip__name">{entry.name}:</span>
                    <span className="chart-tooltip__value">{entry.value}</span>
                </div>
            ))}
        </div>
    );
};

// ==========================================
// COMPONENTE LINE CHART
// ==========================================

// ==========================================
// UTILS
// ==========================================

/**
 * Valida y sanitiza los datos para evitar errores de NaN en Recharts
 * Reemplaza valores nulos/undefined/NaN con 0 o filtra si es necesario
 */
const validateAndSanitizeData = (data: ChartDataPoint[]): ChartDataPoint[] => {
    if (!data || !Array.isArray(data)) return [];

    return data.map(item => {
        const newItem: ChartDataPoint = { ...item };
        Object.keys(newItem).forEach(key => {
            const value = newItem[key];
            if (typeof value === 'number' && (isNaN(value) || value === null || value === undefined)) {
                newItem[key] = 0; // Reemplazar NaN/null con 0 para evitar crasheos
            }
        });
        return newItem;
    });
};

// ==========================================
// COMPONENTE LINE CHART
// ==========================================

const MedicalLineChart: React.FC<ChartConfig> = ({
    data,
    series,
    xAxisKey = 'name',
    height = 300,
    loading = false,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick,
    animate = true
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <LineChart data={sanitizedData} onClick={onDataClick}>
                {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />}
                <XAxis
                    dataKey={xAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                />
                <YAxis stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} />
                )}
                {showLegend && <Legend />}
                {series.map((s, index) => (
                    <Line
                        key={s.dataKey}
                        type="monotone"
                        dataKey={s.dataKey}
                        name={s.name || s.dataKey}
                        stroke={s.color || colors[index % colors.length]}
                        strokeWidth={s.strokeWidth || 2}
                        dot={{ r: 4 }}
                        activeDot={{ r: 6 }}
                        isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                    />
                ))}
            </LineChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE BAR CHART
// ==========================================

const MedicalBarChart: React.FC<ChartConfig> = ({
    data,
    series,
    xAxisKey = 'name',
    height = 300,
    loading = false,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick,
    animate = true,
    stacked = false
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <BarChart data={sanitizedData} onClick={onDataClick}>
                {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />}
                <XAxis
                    dataKey={xAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                />
                <YAxis stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} />
                )}
                {showLegend && <Legend />}
                {series.map((s, index) => (
                    <Bar
                        key={s.dataKey}
                        dataKey={s.dataKey}
                        name={s.name || s.dataKey}
                        fill={s.color || colors[index % colors.length]}
                        stackId={stacked ? 'stack' : undefined}
                        isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                    />
                ))}
            </BarChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE AREA CHART
// ==========================================

export const MedicalAreaChart: React.FC<ChartConfig> = ({
    data,
    series,
    xAxisKey = 'name',
    height = 300,
    loading = false,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick,
    animate = true,
    stacked = false
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={sanitizedData} onClick={onDataClick}>
                {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />}
                <XAxis
                    dataKey={xAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                />
                <YAxis stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} />
                )}
                {showLegend && <Legend />}
                {series.map((s, index) => (
                    <Area
                        key={s.dataKey}
                        type="monotone"
                        dataKey={s.dataKey}
                        name={s.name || s.dataKey}
                        stroke={s.color || colors[index % colors.length]}
                        fill={s.color || colors[index % colors.length]}
                        fillOpacity={0.6}
                        stackId={stacked ? 'stack' : undefined}
                        isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                    />
                ))}
            </AreaChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE PIE CHART
// ==========================================

const MedicalPieChart: React.FC<ChartConfig> = ({
    data,
    series,
    height = 300,
    loading = false,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    const dataKey = series[0]?.dataKey || 'value';
    const nameKey = series[0]?.name || 'name';

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <PieChart onClick={onDataClick}>
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} />
                )}
                {showLegend && <Legend />}
                <Pie
                    data={sanitizedData}
                    dataKey={dataKey}
                    nameKey={nameKey}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                    isAnimationActive
                    animationDuration={CHART_ANIM.animationDuration}
                    animationBegin={CHART_ANIM.animationBegin}
                >
                    {sanitizedData.map((entry, index) => (
                        <Cell key={`cell-${entry.name || entry.dataKey || index}`} fill={colors[index % colors.length]} />
                    ))}
                </Pie>
            </PieChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE RADAR CHART
// ==========================================

const MedicalRadarChart: React.FC<ChartConfig> = ({
    data,
    series,
    height = 300,
    loading = false,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    const chartSeries = series.map(s => ({
        ...s,
        fill: s.color || colors[0]
    }));

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <RadarChart data={sanitizedData}>
                <PolarGrid stroke="#d9d9d9" />
                {/* @ts-ignore - Recharts type compatibility issue with TypeScript 5+ */}
                <PolarAngleAxis dataKey="subject" />
                {/* @ts-ignore - Recharts type compatibility issue with TypeScript 5+ */}
                <PolarRadiusAxis />
                {chartSeries.map((s) => (
                    <Radar
                        key={s.dataKey}
                        name={s.name}
                        dataKey={s.dataKey}
                        stroke={s.color}
                        fill={s.fill}
                        fillOpacity={0.6}
                    />
                ))}
                {showTooltip && (customTooltip ? <Tooltip content={customTooltip} /> : <Tooltip />)}
                {showLegend && <Legend />}
            </RadarChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE SCATTER CHART
// ==========================================

const MedicalScatterChart: React.FC<ChartConfig> = ({
    data,
    series,
    xAxisKey = 'x',
    yAxisKey = 'y',
    height = 300,
    loading = false,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick,
    animate = true
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <ScatterChart onClick={onDataClick}>
                {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />}
                <XAxis
                    dataKey={xAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                    name="X"
                />
                <YAxis
                    dataKey={yAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                    name="Y"
                />
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                )}
                {showLegend && <Legend />}
                {series.map((s, index) => (
                    <Scatter
                        key={s.dataKey}
                        name={s.name || s.dataKey}
                        data={data}
                        fill={s.color || colors[index % colors.length]}
                        isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                    />
                ))}
            </ScatterChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE COMPOSED CHART
// ==========================================

const MedicalComposedChart: React.FC<ChartConfig> = ({
    data,
    series,
    xAxisKey = 'name',
    height = 300,
    loading = false,
    showGrid = true,
    showLegend = true,
    showTooltip = true,
    colors = CHART_COLORS.primary,
    customTooltip,
    onDataClick,
    animate = true
}) => {
    // Sanitizar datos antes de renderizar
    const sanitizedData = useMemo(() => validateAndSanitizeData(data), [data]);

    if (loading) {
        return (
            <div className="chart-loading" style={{ height }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!sanitizedData || sanitizedData.length === 0) {
        return (
            <div className="chart-empty" style={{ height }}>
                <Empty description="No hay datos disponibles" />
            </div>
        );
    }

    return (
        <Suspense fallback={<div className="chart-loading" style={{ height }}><Spin size="large" /></div>}>
        <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={sanitizedData} onClick={onDataClick}>
                {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />}
                <XAxis
                    dataKey={xAxisKey}
                    stroke="var(--text-secondary)"
                    style={{ fontSize: '12px' }}
                />
                <YAxis stroke="var(--text-secondary)" style={{ fontSize: '12px' }} />
                {showTooltip && (
                    <Tooltip content={customTooltip || <CustomTooltip />} />
                )}
                {showLegend && <Legend />}
                {series.map((s, index) => {
                    const color = s.color || colors[index % colors.length];

                    if (s.type === 'bar') {
                        return (
                            <Bar
                                key={s.dataKey}
                                dataKey={s.dataKey}
                                name={s.name || s.dataKey}
                                fill={color}
                                isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                            />
                        );
                    } else if (s.type === 'area') {
                        return (
                            <Area
                                key={s.dataKey}
                                type="monotone"
                                dataKey={s.dataKey}
                                name={s.name || s.dataKey}
                                stroke={color}
                                fill={color}
                                fillOpacity={0.6}
                                isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                            />
                        );
                    } else {
                        return (
                            <Line
                                key={s.dataKey}
                                type="monotone"
                                dataKey={s.dataKey}
                                name={s.name || s.dataKey}
                                stroke={color}
                                strokeWidth={s.strokeWidth || 2}
                                isAnimationActive={animate} animationDuration={CHART_ANIM.animationDuration} animationEasing={CHART_ANIM.animationEasing}
                            />
                        );
                    }
                })}
            </ComposedChart>
        </ResponsiveContainer>
        </Suspense>
    );
};

// ==========================================
// COMPONENTE PRINCIPAL - CHART WRAPPER
// ==========================================

const Charts: React.FC<ChartConfig> = (props) => {
    const { type, title, subtitle } = props;

    const ChartComponent = useMemo(() => {
        switch (type) {
            case 'line':
                return <MedicalLineChart {...props} />;
            case 'bar':
                return <MedicalBarChart {...props} />;
            case 'area':
                return <MedicalAreaChart {...props} />;
            case 'pie':
                return <MedicalPieChart {...props} />;
            case 'radar':
                return <MedicalRadarChart {...props} />;
            case 'scatter':
                return <MedicalScatterChart {...props} />;
            case 'composed':
                return <MedicalComposedChart {...props} />;
            default:
                return <MedicalLineChart {...props} />;
        }
    }, [type, props]);

    return (
        <div className="medical-chart">
            {(title || subtitle) && (
                <div className="medical-chart__header">
                    {title && <h3 className="medical-chart__title">{title}</h3>}
                    {subtitle && <p className="medical-chart__subtitle">{subtitle}</p>}
                </div>
            )}
            <div className="medical-chart__body">{ChartComponent}</div>
        </div>
    );
};

export default Charts;
