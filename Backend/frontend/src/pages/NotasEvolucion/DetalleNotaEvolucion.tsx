import React, { useState, useEffect, useCallback } from 'react';
import { Card, Descriptions, Tag, Button, Space, Spin, Alert, Typography, Divider } from 'antd';
import { ArrowLeftOutlined, EditOutlined, FileTextOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { notasEvolucionService, NotaEvolucion } from '../../services/notasEvolucionService';

const { Title, Text } = Typography;

const tipoConsultaColors: Record<string, string> = {
  control_prenatal: 'blue',
  urgencia: 'red',
  seguimiento: 'green',
  primera_vez: 'purple',
};

const DetalleNotaEvolucion: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [nota, setNota] = useState<NotaEvolucion | null>(null);
  const [loading, setLoading] = useState(true);

  const cargarNota = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await notasEvolucionService.getNotaById(Number(id));
      setNota(data);
    } catch {
      setNota(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarNota();
  }, [cargarNota]);

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  if (!nota) return <Card><Alert message="Nota de evolución no encontrada" type="error" showIcon /></Card>;

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dashboard/notas-evolucion')}>Volver</Button>
        <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/dashboard/notas-evolucion/${id}/editar`)}>Editar</Button>
      </Space>
      <Card title={<span><FileTextOutlined style={{ marginRight: 8 }} />Nota de Evolución</span>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Paciente"><Text strong>{nota.paciente_nombre || nota.paciente}</Text></Descriptions.Item>
          <Descriptions.Item label="Tipo Consulta">
            <Tag color={tipoConsultaColors[nota.tipo_consulta] || 'default'}>
              {nota.tipo_consulta?.replace(/_/g, ' ').toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Fecha">{dayjs(nota.fecha_consulta || nota.fecha_creacion).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
          <Descriptions.Item label="Médico">{nota.medico_nombre || nota.revisado_por_nombre || 'No especificado'}</Descriptions.Item>
        </Descriptions>

        <Divider />
        <Title level={5}>Motivo de Consulta</Title>
        <Text>{nota.motivo_consulta || 'No especificado'}</Text>

        <Divider />
        <Title level={5}>Evolución</Title>
        <Text>{nota.examen_fisico || 'Sin descripción'}</Text>

        <Divider />
        <Title level={5}>Plan</Title>
        <Text>{nota.plan_tratamiento || 'Sin plan registrado'}</Text>

        {nota.diagnosticos && (
          <>
            <Divider />
            <Title level={5}>Diagnósticos</Title>
            <Text>{nota.diagnosticos}</Text>
          </>
        )}

        {nota.observaciones && (
          <>
            <Divider />
            <Title level={5}>Observaciones</Title>
            <Text>{nota.observaciones}</Text>
          </>
        )}
      </Card>
    </div>
  );
};

export default DetalleNotaEvolucion;
