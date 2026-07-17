/**
 * Resumen de completitud de la historia clínica — "de un vistazo".
 * No solo muestra lo que EXISTE: dice explícitamente qué le FALTA a la
 * paciente (antecedentes sin registrar, laboratorio vacío, última ecografía
 * demasiado vieja, etc.), para que el médico lo vea sin recorrer las tabs.
 */
import React, { useMemo, useState } from 'react';
import { Card, Col, Progress, Row, Space, Tag, Tooltip, Typography } from 'antd';
import {
  CheckCircleOutlined, ClockCircleOutlined, MinusCircleOutlined, RightOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;

type EstadoItem = 'completo' | 'desactualizado' | 'faltante';

interface ItemCompletitud {
  clave: string;
  etiqueta: string;
  estado: EstadoItem;
  detalle: string;
  /** Tab de la historia clínica a la que salta el click. */
  tab?: string;
}

interface ResumenCompletitudProps {
  embarazoActivo: { id: number } | null;
  controles: Array<{ fecha_control?: string }>;
  ecografias: Array<{ fecha_realizacion?: string; fecha?: string }>;
  laboratorios: Array<{ fecha_toma?: string }>;
  notas: Array<{ fecha_hora?: string }>;
  vacunas: unknown[];
  antecedenteGineco: unknown | null;
  antecedentePatologico: unknown | null;
  onIrATab?: (tabKey: string) => void;
}

const CONFIG_ESTADO: Record<EstadoItem, { color: string; icono: React.ReactNode; texto: string }> = {
  completo: { color: 'green', icono: <CheckCircleOutlined />, texto: 'Completo' },
  desactualizado: { color: 'orange', icono: <ClockCircleOutlined />, texto: 'Desactualizado' },
  faltante: { color: 'red', icono: <MinusCircleOutlined />, texto: 'Sin registros' },
};

const diasDesde = (fecha?: string): number | null => {
  if (!fecha) return null;
  const d = dayjs(fecha);
  return d.isValid() ? dayjs().diff(d, 'day') : null;
};

const masReciente = (fechas: Array<string | undefined>): number | null => {
  const dias = fechas.map(diasDesde).filter((d): d is number => d !== null);
  return dias.length ? Math.min(...dias) : null;
};

/** "· último hace N días" — u omitido si no hay fecha parseable. */
const sufijoHace = (dias: number | null, etiqueta = 'último'): string =>
  dias === null ? '' : ` · ${etiqueta} hace ${dias} días`;

const ResumenCompletitud: React.FC<ResumenCompletitudProps> = ({
  embarazoActivo, controles, ecografias, laboratorios, notas, vacunas,
  antecedenteGineco, antecedentePatologico, onIrATab,
}) => {
  const [colapsado, setColapsado] = useState(false);

  const items = useMemo<ItemCompletitud[]>(() => {
    const conEmbarazo = Boolean(embarazoActivo);
    const lista: ItemCompletitud[] = [];

    // Antecedentes: son la base de la anamnesis; si no están, están faltando.
    const tieneAntecedentes = Boolean(antecedenteGineco) || Boolean(antecedentePatologico);
    lista.push({
      clave: 'antecedentes',
      etiqueta: 'Antecedentes',
      estado: tieneAntecedentes ? 'completo' : 'faltante',
      detalle: tieneAntecedentes
        ? [antecedenteGineco && 'gineco-obstétricos', antecedentePatologico && 'patológicos'].filter(Boolean).join(' + ')
        : 'Sin anamnesis registrada',
      tab: 'antecedentes',
    });

    // Controles prenatales: con embarazo activo, >30 días sin control es atraso
    // (el esquema mínimo MSP es mensual hasta la semana 28).
    const diasControl = masReciente(controles.map((c) => c.fecha_control));
    lista.push({
      clave: 'controles',
      etiqueta: 'Controles prenatales',
      estado: controles.length === 0
        ? (conEmbarazo ? 'faltante' : 'completo')
        : (conEmbarazo && diasControl !== null && diasControl > 30 ? 'desactualizado' : 'completo'),
      detalle: controles.length === 0
        ? (conEmbarazo ? 'Ninguno registrado con embarazo activo' : 'Sin embarazo activo')
        : `${controles.length} registrados${sufijoHace(diasControl)}`,
      tab: 'controles',
    });

    // Ecografías: >45 días con embarazo activo amerita revisión.
    const diasEco = masReciente(ecografias.map((e) => e.fecha_realizacion ?? e.fecha));
    lista.push({
      clave: 'ecografias',
      etiqueta: 'Ecografías',
      estado: ecografias.length === 0
        ? (conEmbarazo ? 'faltante' : 'completo')
        : (conEmbarazo && diasEco !== null && diasEco > 45 ? 'desactualizado' : 'completo'),
      detalle: ecografias.length === 0
        ? (conEmbarazo ? 'Ninguna registrada con embarazo activo' : 'Sin embarazo activo')
        : `${ecografias.length} registradas${sufijoHace(diasEco, 'última')}`,
      tab: 'ecografias',
    });

    lista.push({
      clave: 'laboratorio',
      etiqueta: 'Laboratorio',
      estado: laboratorios.length === 0 ? (conEmbarazo ? 'faltante' : 'completo') : 'completo',
      detalle: laboratorios.length === 0
        ? (conEmbarazo ? 'Sin exámenes con embarazo activo' : 'Sin exámenes')
        : `${laboratorios.length} exámenes`,
      tab: 'laboratorio',
    });

    lista.push({
      clave: 'vacunas',
      etiqueta: 'Vacunas',
      estado: vacunas.length === 0 ? 'faltante' : 'completo',
      detalle: vacunas.length === 0 ? 'Esquema sin registrar' : `${vacunas.length} dosis registradas`,
      tab: 'vacunas',
    });

    const diasNota = masReciente(notas.map((n) => n.fecha_hora));
    lista.push({
      clave: 'notas',
      etiqueta: 'Notas de evolución',
      estado: notas.length === 0 ? 'faltante' : 'completo',
      detalle: notas.length === 0 ? 'Sin notas' : `${notas.length} notas${sufijoHace(diasNota, 'última')}`,
      tab: 'notas',
    });

    return lista;
  }, [embarazoActivo, controles, ecografias, laboratorios, notas, vacunas, antecedenteGineco, antecedentePatologico]);

  const completos = items.filter((i) => i.estado === 'completo').length;
  const porcentaje = Math.round((completos / items.length) * 100);
  const faltantes = items.filter((i) => i.estado !== 'completo');

  return (
    <Card
      size="small"
      style={{ marginBottom: 16 }}
      title={
        <Space>
          <Text strong>Completitud de la historia clínica</Text>
          <Progress
            type="circle"
            size={28}
            percent={porcentaje}
            strokeColor={porcentaje === 100 ? '#52c41a' : porcentaje >= 60 ? '#faad14' : '#f5222d'}
          />
          {faltantes.length > 0 && (
            <Text type="secondary" style={{ fontWeight: 400 }}>
              faltan: {faltantes.map((f) => f.etiqueta.toLowerCase()).join(', ')}
            </Text>
          )}
        </Space>
      }
      extra={
        <a onClick={() => setColapsado(!colapsado)}>{colapsado ? 'Mostrar' : 'Ocultar'}</a>
      }
    >
      {!colapsado && (
        <Row gutter={[12, 12]}>
          {items.map((item) => {
            const cfg = CONFIG_ESTADO[item.estado];
            return (
              <Col xs={24} sm={12} md={8} key={item.clave}>
                <Tooltip title={item.tab ? 'Ir a la sección' : undefined}>
                  <div
                    role={item.tab ? 'button' : undefined}
                    onClick={() => item.tab && onIrATab?.(item.tab)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '8px 12px', borderRadius: 8,
                      background: 'var(--bg-secondary)',
                      cursor: item.tab ? 'pointer' : 'default',
                    }}
                  >
                    <Tag color={cfg.color} icon={cfg.icono} style={{ margin: 0 }}>{cfg.texto}</Tag>
                    <div style={{ minWidth: 0 }}>
                      <Text strong style={{ display: 'block', fontSize: 13 }}>{item.etiqueta}</Text>
                      <Text type="secondary" style={{ fontSize: 12 }} ellipsis>{item.detalle}</Text>
                    </div>
                    {item.tab && <RightOutlined style={{ marginLeft: 'auto', fontSize: 10, opacity: 0.45 }} />}
                  </div>
                </Tooltip>
              </Col>
            );
          })}
        </Row>
      )}
    </Card>
  );
};

export default ResumenCompletitud;
