import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Spin, Alert } from 'antd';
import { ReloadOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Title, Text } = Typography;

interface RegistroPartograma {
  id: number;
  hora_registro: string;
  dilatacion_cm?: number;
  borramiento?: number;
  frecuencia_cardiaca_fetal?: number;
  frecuencia_contracciones?: number;
  presion_arterial_sistolica?: number;
  presion_arterial_diastolica?: number;
  observaciones?: string;
}

const Partograma: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [registros, setRegistros] = useState<RegistroPartograma[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarRegistros = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await api.get(`/partos/${id}/partograma/`);
      const data = response.data?.results || response.data || [];
      setRegistros(Array.isArray(data) ? data : []);
    } catch {
      setRegistros([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarRegistros();
  }, [cargarRegistros]);

  const columns = [
    { title: 'Fecha/Hora', dataIndex: 'hora_registro', key: 'hora_registro', render: (f: string) => dayjs(f).format('DD/MM/YYYY HH:mm') },
    { title: 'Dilatación (cm)', dataIndex: 'dilatacion_cm', key: 'dilatacion_cm', render: (v: number) => v != null ? <Tag color="blue">{v} cm</Tag> : '-' },
    { title: 'Borramiento (%)', dataIndex: 'borramiento', key: 'borramiento', render: (v: number) => v != null ? `${v}%` : '-' },
    { title: 'FCF (lpm)', dataIndex: 'frecuencia_cardiaca_fetal', key: 'fcf', render: (v: number) => v != null ? v : '-' },
    { title: 'Contracciones (/10min)', dataIndex: 'frecuencia_contracciones', key: 'contracciones', render: (v: number) => v != null ? v : '-' },
    { title: 'PA (mmHg)', key: 'pa', render: (_: unknown, r: RegistroPartograma) =>
      r.presion_arterial_sistolica ? `${r.presion_arterial_sistolica}/${r.presion_arterial_diastolica}` : '-'
    },
    { title: 'Observaciones', dataIndex: 'observaciones', key: 'observaciones', ellipsis: true },
  ];

  return (
    <Card
      title={<span><MedicineBoxOutlined style={{ marginRight: 8 }} />Partograma</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarRegistros} loading={loading}>Recargar</Button>}
    >
      {id ? (
        <>
          <Title level={5}>Registro de Trabajo de Parto</Title>
          <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
            Seguimiento gráfico de la evolución del trabajo de parto.
          </Text>
          <Table
            columns={columns}
            dataSource={registros}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: 'No hay registros de partograma' }}
          />
        </>
      ) : (
        <Alert message="Seleccione un parto" description="Navegue a un detalle de parto para ver su partograma." type="info" showIcon />
      )}
    </Card>
  );
};

export default Partograma;
