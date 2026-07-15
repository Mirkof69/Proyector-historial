import React, { useMemo, Suspense } from 'react';
import { Empty, Spin } from 'antd';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
    ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    Tooltip, Legend
} from 'recharts';
import { ChartConfig } from './chartTypes';
import { CHART_COLORS } from './chartConstants';
import { validateAndSanitizeData } from './chartUtils';

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

export default MedicalRadarChart;
