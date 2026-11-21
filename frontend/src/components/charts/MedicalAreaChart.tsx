import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
    ResponsiveContainer, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { ChartConfig } from './chartTypes';
import { CHART_ANIM, CHART_COLORS } from './chartConstants';
import { validateAndSanitizeData } from './chartUtils';
import CustomTooltip from './CustomTooltip';

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

export default MedicalAreaChart;
