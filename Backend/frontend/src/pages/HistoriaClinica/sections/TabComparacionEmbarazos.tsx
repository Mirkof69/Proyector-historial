import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Row, Col, Card, Space, Tag, Button, Table, Divider, Empty, Statistic, Alert, Typography } from 'antd';
import { TeamOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Embarazo } from '../types';
import { RIESGO_COLORS } from '../utils';
import { RIESGO_DOMAIN, RIESGO_TICKS, formatRiesgoTick } from '../historiaClinicaHelpers';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, ResponsiveContainer,
} from '../rechartsLazy';

const { Text } = Typography;

interface TabComparacionEmbarazosProps {
  embarazoActivo: Embarazo | null;
  historialEmbarazos: Embarazo[];
  navigate: ReturnType<typeof useNavigate>;
  pacienteId: string | undefined;
}
const TabComparacionEmbarazos: React.FC<TabComparacionEmbarazosProps> = ({ embarazoActivo, historialEmbarazos, navigate, pacienteId }) => {
  const todosLosEmbarazos = [embarazoActivo, ...historialEmbarazos].filter(Boolean);

  const riesgoChartData = useMemo(() => {
    const result: { embarazo: string; riesgo: number }[] = [];
    for (const e of todosLosEmbarazos) {
      if (e !== null && e !== undefined) {
        result.push({ embarazo: `#${result.length + 1}`, riesgo: e.riesgo === 'BAJO' ? 1 : e.riesgo === 'ALTO' ? 2 : 3 });
      }
    }
    return result.reverse();
  }, [todosLosEmbarazos]);

  if (todosLosEmbarazos.length === 0) {
    return (
      <Empty description="No hay embarazos registrados para mostrar" image={Empty.PRESENTED_IMAGE_SIMPLE}>
        <Button type="primary" onClick={() => navigate(`/embarazos/nuevo?paciente=${pacienteId}`)}>Registrar Primer Embarazo</Button>
      </Empty>
    );
  }

  return (
    <div>
      <Alert message="Análisis Comparativo de Embarazos" description={todosLosEmbarazos.length > 1 ? "Comparación entre embarazos de la paciente" : "Resumen del embarazo registrado"} type="info" showIcon style={{ marginBottom: 16 }} />
      <Table
        dataSource={todosLosEmbarazos}
        rowKey="id"
        columns={[
          { title: 'Embarazo', render: (_, e, idx) => (<Space>{idx === 0 && <Tag color="blue">ACTUAL</Tag>}<Text>#{(historialEmbarazos.length + 1) - idx}</Text></Space>) },
          { title: 'FUM', dataIndex: 'fecha_ultima_menstruacion', render: (t) => dayjs(t).format('DD/MM/YYYY') },
          { title: 'FPP', dataIndex: 'fecha_probable_parto', render: (t) => dayjs(t).format('DD/MM/YYYY') },
          { title: 'Paridad', render: (_, e) => e ? `G${e.gestas_previas || 0} P${e.partos_previos || 0} C${e.cesareas_previas || 0} A${e.abortos_previos || 0}` : '-' },
          { title: 'Riesgo', dataIndex: 'riesgo', render: (r: keyof typeof RIESGO_COLORS) => <Tag color={RIESGO_COLORS[r]}>{r}</Tag> },
          { title: 'Observaciones', dataIndex: 'observaciones', ellipsis: true }
        ]}
      />
      <Divider />
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Evolución del Riesgo" size="small">
            {todosLosEmbarazos.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={riesgoChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="embarazo" />
                  <YAxis domain={RIESGO_DOMAIN} ticks={RIESGO_TICKS} tickFormatter={formatRiesgoTick} />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="riesgo" stroke="#ff4d4f" strokeWidth={2} dot={{ r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : <Empty description="No hay datos para graficar" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Resumen Estadístico" size="small">
            <Statistic title="Total de Embarazos" value={todosLosEmbarazos.length} />
            <Divider />
            <Statistic title="Partos Vaginales" value={todosLosEmbarazos.filter((e): e is Embarazo => e !== null && e !== undefined && e.id !== embarazoActivo?.id).reduce((acc, e) => acc + (e.partos_previos || 0), 0)} prefix={<TeamOutlined />} />
            <Divider />
            <Statistic title="Cesáreas" value={todosLosEmbarazos.filter((e): e is Embarazo => e !== null && e !== undefined && e.id !== embarazoActivo?.id).reduce((acc, e) => acc + (e.cesareas_previas || 0), 0)} prefix={<MedicineBoxOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default TabComparacionEmbarazos;
