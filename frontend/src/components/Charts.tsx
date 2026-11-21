/**
 * =============================================================================
 * CHARTS - COMPONENTE DE GRÁFICAS REUTILIZABLE
 * =============================================================================
 * Wrapper de Recharts con configuraciones predefinidas para el sistema médico
 * Soporte para múltiples tipos de gráficas con temas
 * =============================================================================
 */

import React, { useMemo } from 'react';
import './Charts.css';
import { ChartConfig } from './charts/chartTypes';
import MedicalLineChart from './charts/MedicalLineChart';
import MedicalBarChart from './charts/MedicalBarChart';
import { MedicalAreaChart } from './charts/MedicalAreaChart';
import MedicalPieChart from './charts/MedicalPieChart';
import MedicalRadarChart from './charts/MedicalRadarChart';
import MedicalScatterChart from './charts/MedicalScatterChart';
import MedicalComposedChart from './charts/MedicalComposedChart';

// Re-export para compatibilidad con importaciones existentes { MedicalAreaChart }
export { MedicalAreaChart };

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
