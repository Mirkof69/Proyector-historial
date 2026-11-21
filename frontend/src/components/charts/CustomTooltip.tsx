import React from 'react';

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

export default CustomTooltip;
