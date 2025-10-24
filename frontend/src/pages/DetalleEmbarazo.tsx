import React, { useState, useEffect } from 'react';
import { Card, Descriptions, Button, Tag, Spin, message, Timeline, Empty, Progress } from 'antd';
import { ArrowLeftOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import axios from 'axios';
import { authService } from '../services/authService';
import dayjs from 'dayjs';

interface DetalleEmbarazoProps {
  embarazoId: number;
  onBack: () => void;
  onEdit: (id: number) => void;
}

interface Embarazo {
  id: number;
  paciente: number;
  paciente_nombre: string;
  numero_gesta: number;
  fecha_ultima_menstruacion: string;
  fecha_probable_parto: string;
  tipo_embarazo: string;
  riesgo_embarazo: string;
  estado: string;
  notas: string;
  semanas_gestacion: string;
  fecha_registro: string;
}

const DetalleEmbarazo: React.FC<DetalleEmbarazoProps> = ({ embarazoId, onBack, onEdit }) => {
  const [embarazo, setEmbarazo] = useState<Embarazo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmbarazo();
  }, [embarazoId]);

  const fetchEmbarazo = async () => {
    setLoading(true);
    try {
      const token = authService.getToken();
      const response = await axios.get(`http://127.0.0.1:8000/api/embarazos/${embarazoId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEmbarazo(response.data);
    } catch (error) {
      message.error('Error al cargar datos del embarazo');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calcularSemanasGestacion = (fum: string) => {
    const hoy = dayjs();
    const fechaFum = dayjs(fum);
    const diasDiferencia = hoy.diff(fechaFum, 'day');
    const semanas = Math.floor(diasDiferencia / 7);
    const dias = diasDiferencia % 7;
    return { semanas, dias, texto: `${semanas} semanas + ${dias} días` };
  };

  const calcularDiasRestantes = (fpp: string) => {
    const hoy = dayjs();
    const fechaFpp = dayjs(fpp);
    const diasRestantes = fechaFpp.diff(hoy, 'day');
    return diasRestantes > 0 ? diasRestantes : 0;
  };

  const calcularProgreso = (fum: string) => {
    const hoy = dayjs();
    const fechaFum = dayjs(fum);
    const diasTranscurridos = hoy.diff(fechaFum, 'day');
    const progreso = Math.min((diasTranscurridos / 280) * 100, 100);
    return Math.round(progreso);
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!embarazo) {
    return (
      <div style={{ padding: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
          Volver a la lista
        </Button>
        <Card>
          <p>Embarazo no encontrado</p>
        </Card>
      </div>
    );
  }

  const getEstadoColor = (estado: string) => {
    if (estado === 'finalizado') return 'green';
    if (estado === 'perdida') return 'red';
    return 'blue';
  };

  const getRiesgoColor = (riesgo: string) => {
    if (riesgo === 'alto') return 'red';
    if (riesgo === 'medio') return 'orange';
    return 'green';
  };

  const eg = calcularSemanasGestacion(embarazo.fecha_ultima_menstruacion);
  const diasRestantes = calcularDiasRestantes(embarazo.fecha_probable_parto);
  const progreso = calcularProgreso(embarazo.fecha_ultima_menstruacion);

  return (
    <div style={{ padding: 24 }}>
      <Button icon={<ArrowLeftOutlined />} onClick={onBack} style={{ marginBottom: 16 }}>
        Volver a la lista
      </Button>

      <Card
        title={`Embarazo #${embarazo.id}`}
        extra={
          <Button 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => onEdit(embarazo.id)}
          >
            Editar
          </Button>
        }
      >
        <Descriptions bordered column={2}>
          <Descriptions.Item label="Paciente" span={2}>
            {embarazo.paciente_nombre}
          </Descriptions.Item>

          <Descriptions.Item label="Número de Gesta">
            {embarazo.numero_gesta}
          </Descriptions.Item>
          <Descriptions.Item label="Tipo de Embarazo">
            {embarazo.tipo_embarazo?.charAt(0).toUpperCase() + embarazo.tipo_embarazo?.slice(1)}
          </Descriptions.Item>

          <Descriptions.Item label="Estado">
            <Tag color={getEstadoColor(embarazo.estado)}>
              {embarazo.estado?.toUpperCase()}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Nivel de Riesgo">
            <Tag color={getRiesgoColor(embarazo.riesgo_embarazo)}>
              {embarazo.riesgo_embarazo?.toUpperCase()}
            </Tag>
          </Descriptions.Item>

          <Descriptions.Item label="FUM">
            {dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
          </Descriptions.Item>
          <Descriptions.Item label="FPP">
            {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
          </Descriptions.Item>

          <Descriptions.Item label="Edad Gestacional" span={2}>
            <strong style={{ fontSize: '16px', color: '#1890ff' }}>{eg.texto}</strong>
          </Descriptions.Item>

          <Descriptions.Item label="Progreso del Embarazo" span={2}>
            <Progress percent={progreso} status="active" />
            <div style={{ marginTop: 8 }}>
              <strong>{diasRestantes} días restantes</strong> hasta la FPP
            </div>
          </Descriptions.Item>

          <Descriptions.Item label="Fecha de Registro" span={2}>
            {dayjs(embarazo.fecha_registro).format('DD/MM/YYYY HH:mm')}
          </Descriptions.Item>

          {embarazo.notas && (
            <Descriptions.Item label="Notas" span={2}>
              {embarazo.notas}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      <Card 
        title="Controles Prenatales" 
        style={{ marginTop: 16 }}
        extra={<Button type="primary" icon={<PlusOutlined />} size="small">Nuevo Control</Button>}
      >
        <Empty description="No hay controles registrados" />
      </Card>

      <Card title="Historial de Eventos" style={{ marginTop: 16 }}>
        <Timeline>
          <Timeline.Item color="green">
            {dayjs(embarazo.fecha_registro).format('DD/MM/YYYY')} - Embarazo registrado
          </Timeline.Item>
          <Timeline.Item color="blue">
            {dayjs().format('DD/MM/YYYY')} - Edad gestacional: {eg.texto}
          </Timeline.Item>
        </Timeline>
      </Card>
    </div>
  );
};

export default DetalleEmbarazo; 