import React from 'react';
import { Card, Table, Tag, Typography, Space } from 'antd';
import { HeartOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';

const { Title, Text } = Typography;

interface ApgarRow {
  key: string;
  signo: string;
  p0: string;
  p1: string;
  p2: string;
}

const getInterpretacion = (puntaje: number) => {
  if (puntaje >= 7) return { color: 'success', text: 'Normal' };
  if (puntaje >= 4) return { color: 'warning', text: 'Depresión Moderada' };
  return { color: 'error', text: 'Depresión Severa' };
};

const columns: ColumnsType<ApgarRow> = [
  { title: 'Signo', dataIndex: 'signo', key: 'signo' },
  { title: '0 puntos', dataIndex: 'p0', key: 'p0' },
  { title: '1 punto', dataIndex: 'p1', key: 'p1' },
  { title: '2 puntos', dataIndex: 'p2', key: 'p2' },
];

const data: ApgarRow[] = [
  { key: '1', signo: 'Frecuencia Cardíaca', p0: 'Ausente', p1: '<100 lpm', p2: '≥100 lpm' },
  { key: '2', signo: 'Respiración', p0: 'Ausente', p1: 'Débil/irregular', p2: 'Fuerte/llanto' },
  { key: '3', signo: 'Tono Muscular', p0: 'Flácido', p1: 'Flexión leve', p2: 'Movimiento activo' },
  { key: '4', signo: 'Reflejos/Irritabilidad', p0: 'Sin respuesta', p1: 'Mueca/gemido', p2: 'Estornudo/tos' },
  { key: '5', signo: 'Color', p0: 'Pálido/cianótico', p1: 'Cuerpo rosado/cianosis extremidades', p2: 'Completamente rosado' },
];

const ApgarScore: React.FC = () => {
  return (
    <Card
      title={
        <span>
          <HeartOutlined style={{ color: '#eb2f96', marginRight: 8 }} />
          Score de Apgar
        </span>
      }
    >
      <Title level={5}>Evaluación del Recién Nacido</Title>
      <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
        El puntaje Apgar evalúa cinco signos vitales al minuto y a los 5 minutos del nacimiento. Cada signo recibe 0, 1 o 2 puntos.
      </Text>

      <Table columns={columns} dataSource={data} pagination={false} bordered size="small" />

      <div style={{ marginTop: 24 }}>
        <Title level={5}>Interpretación</Title>
        <Space direction="vertical">
          <Tag color={getInterpretacion(10).color}>7–10: {getInterpretacion(10).text}</Tag>
          <Tag color={getInterpretacion(5).color}>4–6: {getInterpretacion(5).text}</Tag>
          <Tag color={getInterpretacion(3).color}>0–3: {getInterpretacion(3).text}</Tag>
        </Space>
      </div>
    </Card>
  );
};

export default ApgarScore;
