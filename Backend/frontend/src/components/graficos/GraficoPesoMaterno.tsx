/**
 * Gráfico: Evolución de Peso Materno
 * Muestra la evolución del peso materno a lo largo del embarazo con rangos esperados según IMC
 */
import React, { lazy, Suspense, useCallback, useMemo } from 'react';
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const ReferenceLine = lazy(() => import('recharts').then(m => ({ default: m.ReferenceLine })) as any);
const Area = lazy(() => import('recharts').then(m => ({ default: m.Area })) as any);
const AreaChart = lazy(() => import('recharts').then(m => ({ default: m.AreaChart })) as any);
import { Card, Typography, Alert, Spin } from 'antd';

const { Title, Text } = Typography;

interface DataPoint {
    semana: number;
    peso_actual: number;
    peso_esperado_min?: number;
    peso_esperado_max?: number;
    imc_pregestacional?: number;
}

interface Props {
    data: DataPoint[];
    pesoPregestacional: number;
    tallaMaterna: number;
    title?: string;
}

/**
 * Calcula el IMC pregestacional y la ganancia de peso recomendada
 * según las guías del IOM (Institute of Medicine)
 */
const calcularIMC = (peso: number, talla: number): number => {
    const tallaMetros = talla / 100;
    return peso / (tallaMetros * tallaMetros);
};

const obtenerRangoGananciaPeso = (imc: number): { min: number; max: number; categoria: string } => {
    if (imc < 18.5) {
        return { min: 12.5, max: 18, categoria: 'Bajo peso' };
    } else if (imc >= 18.5 && imc < 25) {
        return { min: 11.5, max: 16, categoria: 'Peso normal' };
    } else if (imc >= 25 && imc < 30) {
        return { min: 7, max: 11.5, categoria: 'Sobrepeso' };
    } else {
        return { min: 5, max: 9, categoria: 'Obesidad' };
    }
};

const safeNum = (value: any): number => {
    if (value === null || value === undefined) return 0;
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    return isNaN(num) ? 0 : num;
};

const GraficoPesoMaterno: React.FC<Props> = ({
    data,
    pesoPregestacional,
    tallaMaterna,
    title = 'Evolución de Peso Materno'
}) => {
    const imcPregestacional = calcularIMC(safeNum(pesoPregestacional), safeNum(tallaMaterna));
    const rangoGanancia = obtenerRangoGananciaPeso(safeNum(imcPregestacional));

    // Calcular peso esperado para cada semana según IMC
    const dataConRangos = data.map(punto => {
        const semanasGestacion = safeNum(punto.semana);
        // Ganancia de peso esperada por semana (aproximada)
        const gananciaMinSemanal = safeNum(rangoGanancia.min) / 40;
        const gananciaMaxSemanal = safeNum(rangoGanancia.max) / 40;

        return {
            ...punto,
            semana: semanasGestacion,
            peso_actual: safeNum(punto.peso_actual),
            peso_esperado_min: safeNum(pesoPregestacional) + (gananciaMinSemanal * semanasGestacion),
            peso_esperado_max: safeNum(pesoPregestacional) + (gananciaMaxSemanal * semanasGestacion),
        };
    });

    const pesoActual = data.length > 0 ? safeNum(data[data.length - 1].peso_actual) : safeNum(pesoPregestacional);
    const gananciaTotal = pesoActual - safeNum(pesoPregestacional);
    const fueraDeRango = gananciaTotal < safeNum(rangoGanancia.min) || gananciaTotal > safeNum(rangoGanancia.max);

    const formatTooltip = useCallback((value: any, name: any) => {
        if (name === 'peso_actual') return [`${value.toFixed(1)} kg`, 'Peso Actual'];
        if (name === 'peso_esperado_min') return [`${value.toFixed(1)} kg`, 'Mínimo Esperado'];
        if (name === 'peso_esperado_max') return [`${value.toFixed(1)} kg`, 'Máximo Esperado'];
        return [value, name || ''];
    }, []);

    const formatLabel = useCallback((label: string | number) => `Semana ${label}`, []);

    return (
        <Card>
            <Title level={5}>{title}</Title>
            <div style={{ marginBottom: 16 }}>
                <Text type="secondary">
                    IMC Pregestacional: <Text strong>{safeNum(imcPregestacional).toFixed(1)} kg/m²</Text> ({rangoGanancia.categoria})
                </Text>
                <br />
                <Text type="secondary">
                    Ganancia recomendada: <Text strong>{safeNum(rangoGanancia.min)} - {safeNum(rangoGanancia.max)} kg</Text>
                </Text>
                <br />
                <Text type="secondary">
                    Ganancia actual: <Text strong style={{ color: fueraDeRango ? '#ff4d4f' : '#52c41a' }}>
                        {safeNum(gananciaTotal).toFixed(1)} kg
                    </Text>
                </Text>
            </div>

            {fueraDeRango && (
                <Alert
                    message="Ganancia de peso fuera del rango recomendado"
                    description={gananciaTotal < safeNum(rangoGanancia.min)
                        ? "La ganancia de peso es menor a la recomendada. Considerar valoración nutricional."
                        : "La ganancia de peso excede lo recomendado. Considerar intervención nutricional."
                    }
                    type="warning"
                    showIcon
                    style={{ marginBottom: 16 }}
                />
            )}

            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={dataConRangos} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="colorRangoPeso" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#52c41a" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#52c41a" stopOpacity={0.1} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="semana"
                        label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                        label={{ value: 'Peso (kg)', angle: -90, position: 'insideLeft' }}
                        domain={useMemo(() => [
                            Math.floor(safeNum(pesoPregestacional) - 5),
                            Math.ceil(safeNum(pesoPregestacional) + safeNum(rangoGanancia.max) + 5)
                        ], [pesoPregestacional, rangoGanancia.max])}
                    />
                    <Tooltip
                        formatter={formatTooltip}
                        labelFormatter={formatLabel}
                    />
                    <Legend />

                    <Area
                        type="monotone"
                        dataKey="peso_esperado_max"
                        stroke="none"
                        fill="url(#colorRangoPeso)"
                        name="Rango Esperado"
                    />
                    <Area
                        type="monotone"
                        dataKey="peso_esperado_min"
                        stroke="none"
                        fill="#fff"
                        name=""
                    />

                    <Line
                        type="monotone"
                        dataKey="peso_actual"
                        stroke="#1890ff"
                        strokeWidth={3}
                        dot={{ r: 5, fill: '#1890ff' }}
                        name="Peso Actual"
                    />

                    <ReferenceLine
                        y={pesoPregestacional}
                        stroke="#722ed1"
                        strokeDasharray="3 3"
                        label="Peso Pregestacional"
                    />
                </AreaChart>
            </ResponsiveContainer>
            </Suspense>
        </Card>
    );
};

export default GraficoPesoMaterno;
