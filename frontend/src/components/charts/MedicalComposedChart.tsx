import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
    ResponsiveContainer, ComposedChart, Line, Bar, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import { ChartConfig } from './chartTypes';
import { CHART_ANIM, CHART_COLORS } from './chartConstants';
import { validateAndSanitizeData } from './chartUtils';
import CustomTooltip from './CustomTooltip';

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

export default MedicalComposedChart;
