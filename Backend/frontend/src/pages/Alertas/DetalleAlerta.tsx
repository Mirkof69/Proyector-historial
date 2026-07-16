import React, { useState, useEffect, useCallback } from 'react';
import { Card, Descriptions, Tag, Button, Spin, Alert, Typography, Badge } from 'antd';
import { ArrowLeftOutlined, BellOutlined, CheckOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import { useAntdApp } from '../../hooks/useMessage';
import { reportesService, AlertaMedica } from '../../services/reportesService';

const { Text } = Typography;

const prioridadColors: Record<string, string> = {
  baja: 'blue',
  media: 'orange',
  alta: 'red',
  critica: 'magenta',
  emergencia: 'red',
};

const DetalleAlerta: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const [alerta, setAlerta] = useState<AlertaMedica | null>(null);
  const [loading, setLoading] = useState(true);
  const [resolviendo, setResolviendo] = useState(false);

  const cargarAlerta = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = await reportesService.obtenerAlerta(Number(id));
      setAlerta(data);
    } catch {
      setAlerta(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarAlerta();
  }, [cargarAlerta]);

  const handleResolver = async () => {
    if (!alerta) return;
    setResolviendo(true);
    try {
      await reportesService.marcarAlertaResuelta(alerta.id);
      message.success('Alerta marcada como resuelta');
      cargarAlerta();
    } catch {
      message.error('Error al marcar la alerta como resuelta');
    } finally {
      setResolviendo(false);
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  if (!alerta) return <Card><Alert message="Alerta no encontrada" type="error" showIcon /></Card>;

  const resuelta = alerta.estado === 'resuelta';
  const descartada = alerta.estado === 'descartada';

  return (
    <div>
      <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} style={{ marginBottom: 16 }}>Volver</Button>
      <Card title={<span><BellOutlined style={{ marginRight: 8 }} />Detalle de Alerta #{alerta.id}</span>}>
        <Descriptions column={{ xs: 1, sm: 2 }} bordered>
          <Descriptions.Item label="Título" span={2}><Text strong>{alerta.titulo}</Text></Descriptions.Item>
          <Descriptions.Item label="Paciente">{alerta.paciente_nombre || '—'}</Descriptions.Item>
          <Descriptions.Item label="Tipo de Alerta">{alerta.tipo_display || alerta.tipo}</Descriptions.Item>
          <Descriptions.Item label="Prioridad">
            <Tag color={prioridadColors[alerta.prioridad]}>{(alerta.prioridad_display || alerta.prioridad).toUpperCase()}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Módulo Origen">{alerta.modulo_origen_display || alerta.modulo_origen}</Descriptions.Item>
          <Descriptions.Item label="Fecha de Creación">{dayjs(alerta.fecha_creacion).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
          <Descriptions.Item label="Estado">
            <Badge
              status={resuelta ? 'success' : descartada ? 'default' : 'error'}
              text={alerta.estado_display || alerta.estado}
            />
          </Descriptions.Item>
          <Descriptions.Item label="Descripción" span={2}>
            <Alert message={alerta.descripcion} type={(alerta.prioridad === 'critica' || alerta.prioridad === 'emergencia') ? 'error' : 'warning'} showIcon />
          </Descriptions.Item>
          {alerta.accion_recomendada && (
            <Descriptions.Item label="Acción Recomendada" span={2}>{alerta.accion_recomendada}</Descriptions.Item>
          )}
          {(alerta.valor_actual || alerta.valor_umbral) && (
            <Descriptions.Item label="Valor Actual / Umbral">{alerta.valor_actual || '—'} / {alerta.valor_umbral || '—'}</Descriptions.Item>
          )}
          {resuelta && (
            <>
              <Descriptions.Item label="Fecha Resolución">{alerta.fecha_resolucion ? dayjs(alerta.fecha_resolucion).format('DD/MM/YYYY HH:mm') : '—'}</Descriptions.Item>
              <Descriptions.Item label="Comentario de Resolución">{alerta.comentario_resolucion || '—'}</Descriptions.Item>
            </>
          )}
        </Descriptions>

        {!resuelta && !descartada && (
          <div style={{ marginTop: 24 }}>
            <Button type="primary" icon={<CheckOutlined />} loading={resolviendo} onClick={handleResolver}>
              Marcar como Resuelta
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DetalleAlerta;
