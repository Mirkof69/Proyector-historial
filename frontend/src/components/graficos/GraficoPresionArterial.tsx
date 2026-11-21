/**
 * Gráfico: Evolución de Presión Arterial
 * Muestra la evolución de la presión arterial sistólica y diastólica
 * durante el embarazo con alertas para hipertensión gestacional y preeclampsia
 */
import React, { Suspense, useCallback, useMemo } from 'react';
import { Card, Typography, Alert, Space, Tag, Spin } from 'antd';
import { WarningOutlined } from '@ant-design/icons';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  ResponsiveContainer, LineChart, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ReferenceArea, ReferenceLine, Line
} from 'recharts';

const { Title, Text } = Typography;

interface DataPoint {
    semana: number;
    sistolica: number;
    diastolica: number;
    fecha?: string;
}

interface Props {
    data: DataPoint[];
    title?: string;
}

/**
 * Clasifica la presión arterial según criterios obstétricos
 */
const clasificarPresion = (sistolica: number, diastolica: number) => {
    // Preeclampsia severa: ≥ 160/110
    if (sistolica >= 160 || diastolica >= 110) {
        return {
            categoria: 'Preeclampsia Severa',
            color: 'error',
            riesgo: 'crítico',
            accion: 'Hospitalización inmediata - Riesgo de eclampsia'
        };
    }

    // Hipertensión moderada: ≥ 140/90
    if (sistolica >= 140 || diastolica >= 90) {
        return {
            categoria: 'Hipertensión Gestacional',
            color: 'error',
            riesgo: 'alto',
            accion: 'Control en 48-72h - Descartar preeclampsia'
        };
    }

    // Pre-hipertensión: 130-139 / 85-89
    if ((sistolica >= 130 && sistolica < 140) || (diastolica >= 85 && diastolica < 90)) {
        return {
            categoria: 'Pre-hipertensión',
            color: 'warning',
            riesgo: 'moderado',
            accion: 'Monitoreo frecuente - Control en 1 semana'
        };
    }

    // Normal: < 130/85
    return {
        categoria: 'Normal',
        color: 'success',
        riesgo: 'bajo',
        accion: 'Continuar controles rutinarios'
    };
};

const safeNum = (value: any): number => {
    if (value === null || value === undefined) return 0;
    const num = typeof value === 'string' ? parseFloat(value) : Number(value);
    return isNaN(num) ? 0 : num;
};

const GraficoPresionArterial: React.FC<Props> = ({
    data,
    title = 'Evolución de Presión Arterial'
}) => {

    // Sanitize data
    const sanitizedData = (data || []).map(d => ({
        ...d,
        semana: safeNum(d.semana),
        sistolica: safeNum(d.sistolica),
        diastolica: safeNum(d.diastolica)
    }));

    // Obtener última medición
    const ultimaMedicion = sanitizedData.length > 0 ? sanitizedData[sanitizedData.length - 1] : null;
    const clasificacion = ultimaMedicion
        ? clasificarPresion(safeNum(ultimaMedicion.sistolica), safeNum(ultimaMedicion.diastolica))
        : null;

    // Detectar tendencia al alza (últimos 3 controles)
    const ultimos3 = sanitizedData.slice(-3);
    const tendenciaAlAlza = ultimos3.length >= 3 && (
        safeNum(ultimos3[2].sistolica) > safeNum(ultimos3[1].sistolica) &&
        safeNum(ultimos3[1].sistolica) > safeNum(ultimos3[0].sistolica)
    );

    // Detectar si hubo alguna crisis hipertensiva
    const huboCrisis = sanitizedData.some(d => safeNum(d.sistolica) >= 160 || safeNum(d.diastolica) >= 110);

    const formatTooltip = useCallback((value: any, name: any) => {
        if (name === 'sistolica') return [`${value} mmHg`, 'Sistólica'];
        if (name === 'diastolica') return [`${value} mmHg`, 'Diastólica'];
        return [value, name || ''];
    }, []);

    const formatLabel = useCallback((label: string | number) => `Semana ${label}`, []);



    return (
        <Card>
            <Title level={5}>{title}</Title>

            {ultimaMedicion && clasificacion && (
                <Space direction="vertical" size="small" style={{ marginBottom: 16, width: '100%' }}>
                    <div>
                        <Text type="secondary">Última medición (Semana {safeNum(ultimaMedicion.semana)}): </Text>
                        <Tag color={clasificacion.color}>
                            {safeNum(ultimaMedicion.sistolica)}/{safeNum(ultimaMedicion.diastolica)} mmHg
                        </Tag>
                        <Tag color={clasificacion.color}>{clasificacion.categoria}</Tag>
                    </div>

                    {tendenciaAlAlza && (
                        <Alert
                            message="Tendencia al alza detectada"
                            description="Se observa incremento progresivo en la presión arterial. Intensificar vigilancia."
                            type="warning"
                            showIcon
                            icon={<WarningOutlined />}
                        />
                    )}

                    {clasificacion.riesgo !== 'bajo' && (
                        <Alert
                            message={clasificacion.categoria}
                            description={clasificacion.accion}
                            type={clasificacion.riesgo === 'crítico' ? 'error' : 'warning'}
                            showIcon
                        />
                    )}
                </Space>
            )}

            <Suspense fallback={<div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>}>
            <ResponsiveContainer width="100%" height={400}>
                <LineChart data={sanitizedData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="semana"
                        label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                        label={{ value: 'Presión Arterial (mmHg)', angle: -90, position: 'insideLeft' }}
                        domain={useMemo(() => [60, 180], [])}
                    />
                    <Tooltip
                        formatter={formatTooltip}
                        labelFormatter={formatLabel}
                    />
                    <Legend />

                    <ReferenceArea
                        y1={160}
                        y2={180}
                        fill="var(--color-peligro)"
                        fillOpacity={0.1}
                        label={{ value: 'Preeclampsia Severa', position: 'insideTopRight' }}
                    />

                    <ReferenceArea
                        y1={140}
                        y2={160}
                        fill="var(--color-peligro)"
                        fillOpacity={0.1}
                    />

                    <ReferenceArea
                        y1={130}
                        y2={140}
                        fill="var(--color-aviso)"
                        fillOpacity={0.1}
                    />

                    <ReferenceLine
                        y={140}
                        stroke="var(--color-peligro)"
                        strokeDasharray="3 3"
                        label={{ value: 'Hipertensión (140)', position: 'right' }}
                    />
                    <ReferenceLine
                        y={90}
                        stroke="var(--color-peligro)"
                        strokeDasharray="3 3"
                        label={{ value: 'Hipertensión (90)', position: 'right' }}
                    />
                    <ReferenceLine
                        y={160}
                        stroke="var(--color-peligro)"
                        strokeDasharray="5 5"
                        label={{ value: 'Severa (160)', position: 'right' }}
                    />

                    <Line
                        type="monotone"
                        dataKey="sistolica"
                        stroke="var(--grafico-5)"
                        strokeWidth={3}
                        dot={{ r: 5, fill: 'var(--grafico-5)' }}
                        name="Presión Sistólica"
                    />
                    <Line
                        type="monotone"
                        dataKey="diastolica"
                        stroke="var(--color-primario)"
                        strokeWidth={3}
                        dot={{ r: 5, fill: 'var(--color-primario)' }}
                        name="Presión Diastólica"
                    />
                </LineChart>
            </ResponsiveContainer>
            </Suspense>

            <div style={{ marginTop: 16, fontSize: '12px', color: 'var(--color-texto-2)' }}>
                <Space direction="vertical" size={4}>
                    <Text type="secondary">
                        <strong>Criterios diagnósticos:</strong>
                    </Text>
                    <Text type="secondary">• Normal: {'<'}130/85 mmHg</Text>
                    <Text type="secondary">• Pre-hipertensión: 130-139/85-89 mmHg</Text>
                    <Text type="secondary">• Hipertensión gestacional: ≥140/90 mmHg (después de 20 semanas)</Text>
                    <Text type="secondary">• Preeclampsia severa: ≥160/110 mmHg + proteinuria</Text>
                </Space>
            </div>

            {huboCrisis && (
                <Alert
                    message="Registro de crisis hipertensiva"
                    description="Se ha registrado al menos una medición en rango de preeclampsia severa. Verificar protocolo de manejo."
                    type="error"
                    showIcon
                    style={{ marginTop: 16 }}
                />
            )}
        </Card>
    );
};

export default GraficoPresionArterial;
