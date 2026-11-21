import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
    ResponsiveContainer, ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { ChartConfig } from './chartTypes';
import { CHART_ANIM, CHART_COLORS } from './chartConstants';
import { validateAndSanitizeData } from './chartUtils';
import CustomTooltip from './CustomTooltip';

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

export default MedicalScatterChart;
