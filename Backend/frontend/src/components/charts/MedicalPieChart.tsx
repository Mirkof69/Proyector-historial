import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
    ResponsiveContainer, PieChart, Pie, Cell,
    Tooltip, Legend
} from 'recharts';
import { ChartConfig } from './chartTypes';
import { CHART_ANIM, CHART_COLORS } from './chartConstants';
import { validateAndSanitizeData } from './chartUtils';
import CustomTooltip from './CustomTooltip';

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

export default MedicalPieChart;
