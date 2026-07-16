import React from 'react';

// ==========================================
// TIPOS E INTERFACES
// ==========================================

export type ChartType =
    | 'line'
    | 'bar'
    | 'area'
    | 'pie'
    | 'radar'
    | 'scatter'
    | 'composed';

export interface ChartDataPoint {
    [key: string]: string | number;
}

export interface ChartSeries {
    dataKey: string;
    name?: string;
    color?: string;
    type?: 'line' | 'bar' | 'area';
    strokeWidth?: number;
    fill?: boolean;
}

export interface ChartConfig {
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
