/**
 * Gráfico: Evolución de Altura Uterina
 * Muestra la evolución de la altura uterina a lo largo del embarazo
 * comparada con la curva esperada (altura ≈ semanas ± 2cm)
 */
import React, { lazy, Suspense, useCallback, useMemo } from 'react';
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const ReferenceLine = lazy(() => import('recharts').then(m => ({ default: m.ReferenceLine })) as any);
const Area = lazy(() => import('recharts').then(m => ({ default: m.Area })) as any);
const AreaChart = lazy(() => import('recharts').then(m => ({ default: m.AreaChart })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
import { Card, Typography, Alert, Spin } from 'antd';

const { Title, Text } = Typography;

interface DataPoint {
    semana: number;
    altura_uterina: number;
    altura_esperada?: number;
    limite_inferior?: number;
    limite_superior?: number;
}

interface Props {
    data: DataPoint[];
    title?: string;
}

/**
 * Calcula la altura uterina esperada según la edad gestacional
 * Regla general: Altura Uterina (cm) ≈ Semanas de gestación ± 2cm
 */
const calcularAlturaEsperada = (semanas: number) => {
    return {
        altura_esperada: semanas,
        limite_inferior: semanas - 2,
        limite_superior: semanas + 2,
    };
};

const safeNum = (value: any): number => {
    if (value === null || value === undefined) return 0;
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    return isNaN(num) ? 0 : num;
};

const GraficoAlturaUterina: React.FC<Props> = ({
    data,
    title = 'Evolución de Altura Uterina'
}) => {
    // Agregar altura esperada y límites a cada punto
    const dataConRangos = (data || []).map(punto => ({
        ...punto,
        semana: safeNum(punto.semana),
        altura_uterina: safeNum(punto.altura_uterina),
        ...calcularAlturaEsperada(safeNum(punto.semana)),
    }));

    // Detectar discordancia (altura muy diferente a edad gestacional)
    const ultimoControl = dataConRangos.length > 0 ? dataConRangos[dataConRangos.length - 1] : null;
    const discordancia = ultimoControl
        ? Math.abs(safeNum(ultimoControl.altura_uterina) - safeNum(ultimoControl.semana))
        : 0;
    const hayDiscordancia = discordancia > 3;

    // Determinar si es RCIU (Restricción de Crecimiento Intrauterino) o Macrosomía
    const esRCIU = ultimoControl
        ? safeNum(ultimoControl.altura_uterina) < (safeNum(ultimoControl.semana) - 3)
        : false;
    const esMacrosomia = ultimoControl
        ? safeNum(ultimoControl.altura_uterina) > (safeNum(ultimoControl.semana) + 3)
        : false;

    // Protección para el dominio del YAxis
    const minVal = dataConRangos.length > 0
        ? Math.min(...dataConRangos.map(d => safeNum(d.limite_inferior || d.altura_uterina)))
        : 0;
    const maxVal = dataConRangos.length > 0
        ? Math.max(...dataConRangos.map(d => safeNum(d.limite_superior || d.altura_uterina)))
        : 40;

    const formatTooltip = useCallback((value: any, name: any) => {
        if (name === 'altura_uterina') return [`${value} cm`, 'Altura Uterina'];
        if (name === 'altura_esperada') return [`${value} cm`, 'Esperada'];
        if (name === 'limite_inferior') return [`${value} cm`, 'Mínimo'];
        if (name === 'limite_superior') return [`${value} cm`, 'Máximo'];
        return [value, name || ''];
    }, []);

    const formatLabel = useCallback((label: string | number) => `Semana ${label}`, []);

    return (
        <Card>
            <Title level={5}>{title}</Title>
            {ultimoControl && (
                <div style={{ marginBottom: 16 }}>
                    <Text type="secondary">
                        Último control (Semana {safeNum(ultimoControl.semana)}): <Text strong>{safeNum(ultimoControl.altura_uterina)} cm</Text>
                    </Text>
                    <br />
                    <Text type="secondary">
                        Altura esperada: <Text strong>{safeNum(ultimoControl.semana)} cm (± 2 cm)</Text>
                    </Text>
                    <br />
                    <Text type="secondary">
                        Diferencia: <Text strong style={{ color: hayDiscordancia ? '#ff4d4f' : '#52c41a' }}>
                            {discordancia > 0 ? '+' : ''}{(safeNum(ultimoControl.altura_uterina) - safeNum(ultimoControl.semana)).toFixed(1)} cm
                        </Text>
                    </Text>
                </div>
            )}

            {hayDiscordancia && (
                <Alert
                    message={esRCIU ? "Posible Restricción de Crecimiento Intrauterino (RCIU)" : esMacrosomia ? "Posible Macrosomía Fetal" : "Discordancia de Altura Uterina"}
                    description={
                        esRCIU
                            ? "La altura uterina está significativamente por debajo de lo esperado. Considerar ecografía Doppler y biometría fetal."
                            : esMacrosomia
                            ? "La altura uterina está significativamente por encima de lo esperado. Descartar polihidramnios, macrosomía o embarazo múltiple."
                            : "La altura uterina presenta una discordancia con la edad gestacional. Se recomienda evaluación complementaria."
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
                        <linearGradient id="colorRangoAU" x1="0" y1="0" x2="0" y2="1">
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
                        label={{ value: 'Altura Uterina (cm)', angle: -90, position: 'insideLeft' }}
                        domain={useMemo(() => [
                            Math.max(0, minVal - 2),
                            maxVal + 2
                        ], [minVal, maxVal])}
                    />
                    <Tooltip
                        formatter={formatTooltip}
                        labelFormatter={formatLabel}
                    />
                    <Legend />

                    <Area
                        type="monotone"
                        dataKey="limite_superior"
                        stroke="none"
                        fill="url(#colorRangoAU)"
                        name="Rango Normal (±2cm)"
                    />
                    <Area
                        type="monotone"
                        dataKey="limite_inferior"
                        stroke="none"
                        fill="#fff"
                        name=""
                    />

                    <Line
                        type="monotone"
                        dataKey="altura_esperada"
                        stroke="#52c41a"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={false}
                        name="Altura Esperada"
                    />

                    <Line
                        type="monotone"
                        dataKey="altura_uterina"
                        stroke="#1890ff"
                        strokeWidth={3}
                        dot={{ r: 5, fill: '#1890ff' }}
                        name="Altura Uterina"
                    />

                    {ultimoControl && ultimoControl.semana >= 20 && (
                        <>
                            <ReferenceLine
                                y={ultimoControl.semana - 4}
                                stroke="#ff4d4f"
                                strokeDasharray="3 3"
                                label={{ value: 'Alerta RCIU', position: 'left' }}
                            />
                            <ReferenceLine
                                y={ultimoControl.semana + 4}
                                stroke="#ff4d4f"
                                strokeDasharray="3 3"
                                label={{ value: 'Alerta Macrosomía', position: 'left' }}
                            />
                        </>
                    )}
                </AreaChart>
            </ResponsiveContainer>
            </Suspense>

            <div style={{ marginTop: 16, fontSize: '12px', color: '#8c8c8c' }}>
                <Text type="secondary">
                    <strong>Nota:</strong> La altura uterina debe medirse desde el borde superior de la sínfisis púbica
                    hasta el fondo uterino con la paciente en decúbito supino y vejiga vacía.
                </Text>
            </div>
        </Card>
    );
};

export default GraficoAlturaUterina;
