import { ChartDataPoint } from './chartTypes';

// ==========================================
// UTILS
// ==========================================

/**
 * Valida y sanitiza los datos para evitar errores de NaN en Recharts
 * Reemplaza valores nulos/undefined/NaN con 0 o filtra si es necesario
 */
export const validateAndSanitizeData = (data: ChartDataPoint[]): ChartDataPoint[] => {
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
