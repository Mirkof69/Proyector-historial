/**
 * =============================================================================
 * CHARTS - COMPONENTE DE GRÁFICAS REUTILIZABLE
 * =============================================================================
 * Wrapper de Recharts con configuraciones predefinidas para el sistema médico
 * Soporte para múltiples tipos de gráficas con temas
 * =============================================================================
 */

import React, { useMemo, Suspense } from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  PieChart, Pie, RadarChart, Radar, ScatterChart, Scatter,
  ComposedChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { Empty, Spin } from 'antd';
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
                        isAnimationActive={animate}
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
                        isAnimationActive={animate}
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
                        isAnimationActive={animate}
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
                    data={data}
                    dataKey={dataKey}
                    nameKey={nameKey}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label
                >
                    {data.map((entry, index) => (
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
                        isAnimationActive={animate}
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
                                isAnimationActive={animate}
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
                                isAnimationActive={animate}
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
                                isAnimationActive={animate}
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

// ==========================================
// GRÁFICAS PREDEFINIDAS ESPECÍFICAS
// ==========================================

/**
 * Gráfica de Curva de Peso Fetal
 */
export const FetaWeightChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="area"
        data={data}
        series={[
            { dataKey: 'peso', name: 'Peso (g)', color: '#722ed1' },
            { dataKey: 'pesoMinimo', name: 'Mínimo P10', color: '#ffc53d' },
            { dataKey: 'pesoMaximo', name: 'Máximo P90', color: '#ffc53d' }
        ]}
        xAxisKey="semana"
        title="Curva de Peso Fetal"
        subtitle="Evolución del peso estimado del feto"
        colors={CHART_COLORS.prenatal}
        height={350}
    />
);

/**
 * Gráfica de Presión Arterial
 */
export const BloodPressureChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="line"
        data={data}
        series={[
            { dataKey: 'sistolica', name: 'Sistólica', color: '#f5222d' },
            { dataKey: 'diastolica', name: 'Diastólica', color: '#1890ff' }
        ]}
        xAxisKey="fecha"
        title="Presión Arterial"
        subtitle="Evolución de la presión arterial"
        height={300}
    />
);

/**
 * Gráfica de Altura Uterina
 */
export const UterineHeightChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="area"
        data={data}
        series={[
            { dataKey: 'altura', name: 'Altura Uterina (cm)', color: '#722ed1' }
        ]}
        xAxisKey="semana"
        title="Altura Uterina"
        subtitle="Crecimiento en centímetros por semana"
        colors={CHART_COLORS.prenatal}
        height={300}
    />
);

/**
 * Gráfica de Resultados de Laboratorio
 */
export const LabResultsChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="bar"
        data={data}
        series={[
            { dataKey: 'hemoglobina', name: 'Hemoglobina', color: '#f5222d' },
            { dataKey: 'hematocrito', name: 'Hematocrito', color: '#1890ff' },
            { dataKey: 'glucosa', name: 'Glucosa', color: '#52c41a' }
        ]}
        xAxisKey="fecha"
        title="Resultados de Laboratorio"
        subtitle="Comparativa de valores"
        colors={CHART_COLORS.laboratorio}
        height={350}
    />
);

/**
 * Gráfica de Distribución de Partos
 */
export const BirthDistributionChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="pie"
        data={data}
        series={[{ dataKey: 'value', name: 'name' }]}
        title="Distribución de Vías de Parto"
        subtitle="Porcentaje por tipo de parto"
        colors={['#52c41a', '#1890ff', '#faad14', '#f5222d']}
        height={300}
    />
);

/**
 * Gráfica de Evolución del IMC
 */
export const BMIEvolutionChart: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="line"
        data={data}
        series={[
            { dataKey: 'imc', name: 'IMC', color: '#1890ff' }
        ]}
        xAxisKey="fecha"
        title="Evolución del IMC"
        subtitle="Índice de masa corporal durante el embarazo"
        height={300}
    />
);

/**
 * Gráfica de Corre lación Peso-Talla Fetal (Scatter)
 */
export const FetalWeightHeightCorrelation: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="scatter"
        data={data}
        series={[
            { dataKey: 'peso', name: 'Peso vs Talla', color: '#722ed1' }
        ]}
        xAxisKey="talla"
        yAxisKey="peso"
        title="Correlación Peso-Talla Fetal"
        subtitle="Análisis de dispersión peso vs altura"
        colors={CHART_COLORS.prenatal}
        height={350}
    />
);

/**
 * Gráfica Combinada de Evolución Prenatal (Composed)
 */
export const PrenatalEvolutionComposed: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="composed"
        data={data}
        series={[
            { dataKey: 'peso', name: 'Peso Materno (kg)', color: '#1890ff', type: 'bar' },
            { dataKey: 'presionSistolica', name: 'PA Sistólica', color: '#f5222d', type: 'line' },
            { dataKey: 'alturaUterina', name: 'Altura Uterina (cm)', color: '#722ed1', type: 'area' }
        ]}
        xAxisKey="semana"
        title="Evolución Prenatal Integral"
        subtitle="Combinación de indicadores clave"
        colors={CHART_COLORS.prenatal}
        height={400}
    />
);

/**
 * Gráfica de Análisis de Riesgo (Scatter)
 */
export const RiskAnalysisScatter: React.FC<{ data: ChartDataPoint[] }> = ({ data }) => (
    <Charts
        type="scatter"
        data={data}
        series={[
            { dataKey: 'riesgo', name: 'Nivel de Riesgo', color: '#f5222d' }
        ]}
        xAxisKey="edad"
        yAxisKey="imc"
        title="Análisis de Factores de Riesgo"
        subtitle="Edad vs IMC con nivel de riesgo"
        colors={CHART_COLORS.error}
        height={350}
    />
);

export default Charts;
