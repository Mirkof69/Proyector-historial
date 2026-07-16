/**
 * =============================================================================
 * DATE RANGE SELECTOR - Componente Reutilizable de Selección de Fechas
 * =============================================================================
 * Selector de rango de fechas con presets y modo personalizado
 * =============================================================================
 */

import React, { useState, useCallback } from 'react';
import { DatePicker, Button, Space, Radio, Tag } from 'antd';
import { CalendarOutlined, ClockCircleOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import './DateRangeSelector.css';

const { RangePicker } = DatePicker;

type PeriodPreset = 'today' | 'week' | 'month' | 'quarter' | 'year' | 'custom';

export interface DateRange {
    startDate: string; // YYYY-MM-DD
    endDate: string;   // YYYY-MM-DD
    preset: PeriodPreset;
}

interface DateRangeSelectorProps {
    onChange: (range: DateRange) => void;
    defaultPreset?: PeriodPreset;
    showCompare?: boolean;
}

const presets = [
    { key: 'today', label: 'Hoy', icon: <ClockCircleOutlined /> },
    { key: 'week', label: 'Última Semana', icon: <CalendarOutlined /> },
    { key: 'month', label: 'Último Mes', icon: <CalendarOutlined /> },
    { key: 'quarter', label: 'Último Trimestre', icon: <CalendarOutlined /> },
    { key: 'year', label: 'Último Año', icon: <CalendarOutlined /> },
];

const DateRangeSelector: React.FC<DateRangeSelectorProps> = ({
    onChange,
    defaultPreset = 'month',
    showCompare = false
}) => {
    const [userSelectedPreset, setUserSelectedPreset] = useState<PeriodPreset | null>(null);
    const selectedPreset = userSelectedPreset ?? defaultPreset;
    const [customRange, setCustomRange] = useState<[Dayjs, Dayjs] | null>(null);
    const [compareMode, setCompareMode] = useState(false);

    const calculateRange = useCallback((preset: PeriodPreset): DateRange => {
        const today = dayjs();
        let startDate: Dayjs;
        let endDate: Dayjs = today;

        switch (preset) {
            case 'today':
                startDate = today;
                break;
            case 'week':
                startDate = today.subtract(7, 'day');
                break;
            case 'month':
                startDate = today.subtract(1, 'month');
                break;
            case 'quarter':
                startDate = today.subtract(3, 'month');
                break;
            case 'year':
                startDate = today.subtract(1, 'year');
                break;
            case 'custom':
                if (customRange) {
                    return {
                        startDate: customRange[0].format('YYYY-MM-DD'),
                        endDate: customRange[1].format('YYYY-MM-DD'),
                        preset: 'custom'
                    };
                }
                startDate = today.subtract(1, 'month');
                break;
            default:
                startDate = today.subtract(1, 'month');
        }

        return {
            startDate: startDate.format('YYYY-MM-DD'),
            endDate: endDate.format('YYYY-MM-DD'),
            preset
        };
    }, [customRange]);

    const handlePresetChange = (preset: PeriodPreset) => {
        setUserSelectedPreset(preset);
        const range = calculateRange(preset);
        onChange(range);
    };

    const handleCustomRangeChange = (dates: any) => {
        if (dates && dates[0] && dates[1]) {
            setCustomRange([dates[0], dates[1]]);
            setUserSelectedPreset('custom');
            onChange({
                startDate: dates[0].format('YYYY-MM-DD'),
                endDate: dates[1].format('YYYY-MM-DD'),
                preset: 'custom'
            });
        }
    };



    return (
        <div className="date-range-selector">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {/* Presets rápidos */}
                <div className="date-range-presets">
                    <Space wrap>
                        {presets.map(preset => (
                            <Button
                                key={preset.key}
                                type={selectedPreset === preset.key ? 'primary' : 'default'}
                                icon={preset.icon}
                                onClick={() => handlePresetChange(preset.key as PeriodPreset)}
                                className={`preset-button ${selectedPreset === preset.key ? 'active' : ''}`}
                            >
                                {preset.label}
                            </Button>
                        ))}
                    </Space>
                </div>

                {/* Selector personalizado */}
                <div className="date-range-custom">
                    <Space>
                        <RangePicker
                            value={customRange}
                            onChange={handleCustomRangeChange}
                            format="DD/MM/YYYY"
                            placeholder={['Fecha Inicio', 'Fecha Fin']}
                            style={{ width: 300 }}
                            allowClear
                        />
                        {selectedPreset === 'custom' && customRange && (
                            <Tag color="blue">
                                Personalizado: {customRange[0].format('DD/MM/YYYY')} - {customRange[1].format('DD/MM/YYYY')}
                            </Tag>
                        )}
                    </Space>
                </div>

                {/* Modo comparación (opcional) */}
                {showCompare && (
                    <div className="date-range-compare">
                        <Radio.Group
                            value={compareMode}
                            onChange={(e) => setCompareMode(e.target.value)}
                            buttonStyle="solid"
                            size="small"
                        >
                            <Radio.Button value={false}>Sin Comparación</Radio.Button>
                            <Radio.Button value={true}>Comparar con Período Anterior</Radio.Button>
                        </Radio.Group>
                    </div>
                )}
            </Space>
        </div>
    );
};

export default DateRangeSelector;
