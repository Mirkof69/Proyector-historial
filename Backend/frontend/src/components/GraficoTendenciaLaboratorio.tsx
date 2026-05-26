/**
 * =============================================================================
 * GRÁFICO DE TENDENCIA DE LABORATORIO
 * =============================================================================
 * Componente para visualizar evolución temporal de parámetros de labor atorio
 * - Gráfico de línea con valores históricos
 * - Líneas de referencia para rangos normales
 * - Área sombreada para rango de normalidad
 * - Estadísticas: promedio, tendencia, variación
 * =============================================================================
 */

import React, { lazy, Suspense, useCallback } from 'react';
const LineChart = lazy(() => import('recharts').then(m => ({ default: m.LineChart })) as any);
const Line = lazy(() => import('recharts').then(m => ({ default: m.Line })) as any);
const XAxis = lazy(() => import('recharts').then(m => ({ default: m.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(m => ({ default: m.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(m => ({ default: m.CartesianGrid })) as any);
const Tooltip = lazy(() => import('recharts').then(m => ({ default: m.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(m => ({ default: m.Legend })) as any);
const ReferenceLine = lazy(() => import('recharts').then(m => ({ default: m.ReferenceLine })) as any);
const Area = lazy(() => import('recharts').then(m => ({ default: m.Area })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(m => ({ default: m.ResponsiveContainer })) as any);
const ReferenceArea = lazy(() => import('recharts').then(m => ({ default: m.ReferenceArea })) as any);
const ComposedChart = lazy(() => import('recharts').then(m => ({ default: m.ComposedChart })) as any);
import {
    Card,
    Statistic,
    Row,
    Col,
    Tag,
    Space,
    Typography,
    Alert,
    Spin,
} from 'antd';
import {
    RiseOutlined,
    FallOutlined,
    MinusOutlined,
    TrophyOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text, Title } = Typography;

interface HistoricoData {
    fecha: string;
    valor: number | null;
}

interface Props {
    parametro: string;
    historico: HistoricoData[];
    valorMinimo?: number;
    valorMaximo?: number;
    criticoBajo?: number;
    criticoAlto?: number;
    unidad?: string;
}

// ==========================================================================
// TOOLTIP PERSONALIZADO (Extraído para evitar re-renders)
// ==========================================================================
const CustomTooltip = ({ active, payload, unidad, valorMinimo, valorMaximo }: any) => {
    if (active && payload && payload.length) {
        const data = payload[0].payload;
        return (
            <div
                style={{
                    backgroundColor: 'white',
                    padding: '10px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '4px',
                }}
            >
                <p style={{ margin: 0, fontWeight: 'bold' }}>
                    {data.fechaCompleta}
                </p>
                <p style={{ margin: '5px 0 0 0', color: '#1890ff' }}>
                    Valor: <strong>{data.valor?.toFixed(2)} {unidad}</strong>
                </p>
                {valorMinimo && valorMaximo && (
                    <p style={{ margin: '5px 0 0 0', fontSize: '12px', color: '#8c8c8c' }}>
                        Rango: {valorMinimo} - {valorMaximo} {unidad}
                    </p>
                )}
            </div>
        );
    }
    return null;
};


const GraficoTendenciaLaboratorio: React.FC<Props> = ({
    parametro,
    historico,
    valorMinimo,
    valorMaximo,
    criticoBajo,
    criticoAlto,
    unidad = '',
}) => {
    // ==========================================================================
    // TRANSFORMAR DATOS PARA EL GRÁFICO
    // ==========================================================================
    const data = historico
        .reduce((acc: any[], h) => {
            if (h.valor !== null) {
                acc.push({
                    fecha: dayjs(h.fecha).format('DD/MM/YY'),
                    fechaCompleta: dayjs(h.fecha).format('DD/MM/YYYY'),
                    valor: h.valor,
                    minimo: valorMinimo,
                    maximo: valorMaximo,
                });
            }
            return acc;
        }, [])
        .reverse(); // Más antiguo primero

    // ==========================================================================
    // CÁLCULOS ESTADÍSTICOS
    // ==========================================================================
    const calcularPromedio = () => {
        if (data.length === 0) return 0;
        const suma = data.reduce((acc, d) => acc + (d.valor || 0), 0);
        return suma / data.length;
    };

    const calcularTendencia = () => {
        if (data.length < 2) return 0;

        const primerValor = data[0].valor || 0;
        const ultimoValor = data[data.length - 1].valor || 0;

        return ((ultimoValor - primerValor) / primerValor) * 100;
    };

    const calcularUltimaVariacion = () => {
        if (data.length < 2) return 0;

        const penultimoValor = data[data.length - 2].valor || 0;
        const ultimoValor = data[data.length - 1].valor || 0;

        if (penultimoValor === 0) return 0;

        return ((ultimoValor - penultimoValor) / penultimoValor) * 100;
    };

    const getTendenciaIcono = () => {
        const tendencia = calcularTendencia();

        if (Math.abs(tendencia) < 5) {
            return <MinusOutlined style={{ color: '#1890ff' }} />;
        }

        return tendencia > 0 ? (
            <RiseOutlined style={{ color: '#f5222d' }} />
        ) : (
            <FallOutlined style={{ color: '#52c41a' }} />
        );
    };

    const getColorVariacion = () => {
        const variacion = calcularUltimaVariacion();

        if (Math.abs(variacion) < 5) return '#1890ff';
        return variacion > 0 ? '#f5222d' : '#52c41a';
    };

    const getEstadoActual = () => {
        if (data.length === 0) return 'sin-datos';

        const ultimoValor = data[data.length - 1].valor || 0;

        if (criticoBajo && ultimoValor < criticoBajo) return 'critico-bajo';
        if (criticoAlto && ultimoValor > criticoAlto) return 'critico-alto';
        if (valorMinimo && ultimoValor < valorMinimo) return 'bajo';
        if (valorMaximo && ultimoValor > valorMaximo) return 'alto';

        return 'normal';
    };

    const promedio = calcularPromedio();
    const tendencia = calcularTendencia();
    const ultimaVariacion = calcularUltimaVariacion();
    const estadoActual = getEstadoActual();

    const formatTooltipValue = useCallback((value: any) => {
        const num = Number(value);
        return [`${!isNaN(num) ? num.toFixed(2) : '-'} ${unidad}`, 'Valor'];
    }, [unidad]);


    // ==========================================================================
    // RENDER
    // ==========================================================================
    if (data.length === 0) {
        return (
            <Card>
                <Alert
                    message="Sin Datos Históricos"
                    description={`No hay datos históricos suficientes para mostrar la evolución de ${parametro}.`}
                    type="info"
                    showIcon
                />
            </Card>
        );
    }

    return (
        <Card
            title={
                <Space>
                    <TrophyOutlined />
                    <Title level={4} style={{ margin: 0 }}>Evolución de {parametro}</Title>
                </Space>
            }
        >
            {/* ESTADO ACTUAL */}
            {estadoActual !== 'normal' && estadoActual !== 'sin-datos' && (
                <Alert
                    message={
                        estadoActual.includes('critico')
                            ? '⚠️ Valor Actual en Rango Crítico'
                            : 'Valor Actual Fuera del Rango Normal'
                    }
                    description={
                        estadoActual === 'critico-bajo'
                            ? `El último valor está por debajo del límite crítico (< ${criticoBajo} ${unidad})`
                            : estadoActual === 'critico-alto'
                                ? `El último valor está por encima del límite crítico (> ${criticoAlto} ${unidad})`
                                : estadoActual === 'bajo'
                                    ? `El último valor está por debajo del mínimo normal (< ${valorMinimo} ${unidad})`
                                    : `El último valor está por encima del máximo normal (> ${valorMaximo} ${unidad})`
                    }
                    type={estadoActual.includes('critico') ? 'error' : 'warning'}
                    showIcon
                    style={{ marginBottom: 16 }}
                />
            )}

            {/* GRÁFICO */}
            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="fecha"
                        style={{ fontSize: 12 }}
                    />
                    <YAxis
                        style={{ fontSize: 12 }}
                        label={{ value: unidad, angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip content={<CustomTooltip unidad={unidad} valorMinimo={valorMinimo} valorMaximo={valorMaximo} />} />
                    <Legend />

                    {valorMinimo !== undefined && valorMaximo !== undefined && (
                        <ReferenceArea
                            y1={valorMinimo}
                            y2={valorMaximo}
                            fill="#52c41a"
                            fillOpacity={0.1}
                            label={{ value: 'Rango Normal', position: 'insideTopRight', fontSize: 12 }}
                        />
                    )}

                    {valorMinimo !== undefined && (
                        <ReferenceLine
                            y={valorMinimo}
                            stroke="#52c41a"
                            strokeDasharray="5 5"
                            label={{
                                value: `Mín: ${valorMinimo}`,
                                position: 'right',
                                fontSize: 12,
                                fill: '#52c41a'
                            }}
                        />
                    )}

                    {valorMaximo !== undefined && (
                        <ReferenceLine
                            y={valorMaximo}
                            stroke="#52c41a"
                            strokeDasharray="5 5"
                            label={{
                                value: `Máx: ${valorMaximo}`,
                                position: 'right',
                                fontSize: 12,
                                fill: '#52c41a'
                            }}
                        />
                    )}

                    {criticoBajo !== undefined && (
                        <ReferenceLine
                            y={criticoBajo}
                            stroke="#ff4d4f"
                            strokeDasharray="3 3"
                            label={{
                                value: `Crítico Bajo: ${criticoBajo}`,
                                position: 'right',
                                fontSize: 12,
                                fill: '#ff4d4f'
                            }}
                        />
                    )}

                    {criticoAlto !== undefined && (
                        <ReferenceLine
                            y={criticoAlto}
                            stroke="#ff4d4f"
                            strokeDasharray="3 3"
                            label={{
                                value: `Crítico Alto: ${criticoAlto}`,
                                position: 'right',
                                fontSize: 12,
                                fill: '#ff4d4f'
                            }}
                        />
                    )}

                    <ReferenceLine
                        y={promedio}
                        stroke="#1890ff"
                        strokeDasharray="10 5"
                        label={{
                            value: `Promedio: ${promedio.toFixed(2)}`,
                            position: 'left',
                            fontSize: 12,
                            fill: '#1890ff'
                        }}
                    />

                    <Area
                        type="monotone"
                        dataKey="valor"
                        fill="#8884d8"
                        fillOpacity={0.2}
                        stroke="none"
                        name={`Área de ${parametro}`}
                    />

                    <Line
                        type="monotone"
                        dataKey="valor"
                        stroke="#8884d8"
                        strokeWidth={3}
                        dot={{ r: 6, fill: '#8884d8' }}
                        activeDot={{ r: 8 }}
                        name={`${parametro} (${unidad})`}
                    />
                </ComposedChart>
            </ResponsiveContainer>
            </Suspense>

            {/* ESTADÍSTICAS */}
            <Row gutter={16} style={{ marginTop: 24 }}>
                <Col xs={24} sm={8}>
                    <Statistic
                        title="Valor Promedio"
                        value={promedio.toFixed(2)}
                        suffix={unidad}
                        precision={2}
                        valueStyle={{ color: '#1890ff' }}
                    />
                </Col>
                <Col xs={24} sm={8}>
                    <Statistic
                        title="Tendencia General"
                        value={Math.abs(tendencia).toFixed(1)}
                        suffix={`% ${getTendenciaIcono()}`}
                        precision={1}
                        valueStyle={{
                            color:
                                Math.abs(tendencia) < 5
                                    ? '#1890ff'
                                    : tendencia > 0
                                        ? '#f5222d'
                                        : '#52c41a',
                        }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        {Math.abs(tendencia) < 5
                            ? 'Estable'
                            : tendencia > 0
                                ? 'Tendencia al alza'
                                : 'Tendencia a la baja'}
                    </Text>
                </Col>
                <Col xs={24} sm={8}>
                    <Statistic
                        title="Última Variación"
                        value={Math.abs(ultimaVariacion).toFixed(1)}
                        suffix="%"
                        precision={1}
                        valueStyle={{ color: getColorVariacion() }}
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        {ultimaVariacion > 0 ? 'Aumento' : ultimaVariacion < 0 ? 'Disminución' : 'Sin cambio'} respecto al anterior
                    </Text>
                </Col>
            </Row>

            {/* INFORMACIÓN ADICIONAL */}
            <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#fafafa', borderRadius: '4px' }}>
                <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <Text strong>Interpretación:</Text>
                    <Text style={{ fontSize: 13 }}>
                        • Total de mediciones: <strong>{data.length}</strong>
                    </Text>
                    <Text style={{ fontSize: 13 }}>
                        • Rango de valores: <strong>
                            {Math.min(...data.map(d => d.valor || 0)).toFixed(2)} -
                            {Math.max(...data.map(d => d.valor || 0)).toFixed(2)} {unidad}
                        </strong>
                    </Text>
                    {valorMinimo && valorMaximo && (
                        <Text style={{ fontSize: 13 }}>
                            • Valores dentro del rango normal:{' '}
                            <strong>
                                {data.filter(d => {
                                    const v = d.valor || 0;
                                    return v >= valorMinimo && v <= valorMaximo;
                                }).length}{' '}
                                de {data.length}
                            </strong>
                            {' '}
                            <Tag color="green">
                                {((data.filter(d => {
                                    const v = d.valor || 0;
                                    return v >= valorMinimo && v <= valorMaximo;
                                }).length / data.length) * 100).toFixed(0)}%
                            </Tag>
                        </Text>
                    )}

                    {/* MINI GRÁFICO DE TENDENCIA SIMPLIFICADO */}
                    <div style={{ marginTop: 12 }}>
                        <Text strong style={{ fontSize: 12 }}>Vista Simplificada:</Text>
                        <Suspense fallback={<Spin size="small" />}>
                        <ResponsiveContainer width="100%" height={80}>
                            <LineChart data={data} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                                <Line
                                    type="monotone"
                                    dataKey="valor"
                                    stroke="#1890ff"
                                    strokeWidth={2}
                                    dot={false}
                                    name="Tendencia"
                                />
                                <Tooltip
                                    contentStyle={{ fontSize: 12 }}
                                    formatter={formatTooltipValue}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                        </Suspense>
                    </div>
                </Space>
            </div>
        </Card>
    );
};

export default GraficoTendenciaLaboratorio;
