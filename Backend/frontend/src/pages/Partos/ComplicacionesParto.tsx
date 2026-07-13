import React from 'react';
import { Card, Table, Tag, Typography, Alert } from 'antd';
import { WarningOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface Complicacion {
  key: string;
  tipo: string;
  descripcion: string;
  severidad: 'baja' | 'media' | 'alta' | 'critica';
  manejo: string;
}

const data: Complicacion[] = [
  { key: '1', tipo: 'Desgarro Perineal', descripcion: 'Desgarro de segundo grado en pared vaginal posterior', severidad: 'media', manejo: 'Sutura con puntos separados' },
  { key: '2', tipo: 'Hemorragia Postparto', descripcion: 'Pérdida sanguínea estimada > 500 mL en parto vaginal', severidad: 'alta', manejo: 'Masaje uterino, oxitocina, ácido tranexámico' },
  { key: '3', tipo: 'Atonía Uterina', descripcion: 'Falta de contracción uterina adecuada post alumbramiento', severidad: 'critica', manejo: 'Oxitocina IV, masaje bimanual, prostaglandinas' },
  { key: '4', tipo: 'Infección Puerperal', descripcion: 'Endometritis con fiebre >38°C en las primeras 24h', severidad: 'alta', manejo: 'Antibióticos de amplio espectro, cultivo' },
  { key: '5', tipo: 'Laceración Cervical', descripcion: 'Laceración menor en cuello uterino', severidad: 'baja', manejo: 'Observación y sutura si es necesario' },
];

const severidadColor = { baja: 'blue', media: 'orange', alta: 'red', critica: 'magenta' };

const ComplicacionesParto: React.FC = () => {
  const columns = [
    { title: 'Tipo', dataIndex: 'tipo', key: 'tipo', render: (t: string) => <Text strong>{t}</Text> },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion' },
    {
      title: 'Severidad', dataIndex: 'severidad', key: 'severidad',
      render: (s: string) => <Tag color={severidadColor[s as keyof typeof severidadColor]}>{s.toUpperCase()}</Tag>,
    },
    { title: 'Manejo', dataIndex: 'manejo', key: 'manejo' },
  ];

  const criticas = data.filter(c => c.severidad === 'critica' || c.severidad === 'alta');

  return (
    <Card title={<span><WarningOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />Complicaciones del Parto</span>}>
      {criticas.length > 0 && (
        <Alert
          message={`${criticas.length} complicaciones de severidad alta o crítica detectadas`}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      <Table columns={columns} dataSource={data} rowKey="key" pagination={false} bordered />
    </Card>
  );
};

export default ComplicacionesParto;
