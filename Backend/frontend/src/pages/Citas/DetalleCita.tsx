/**
 * ==================================================================================
 * DETALLE DE CITA - VISTA COMPLETA
 * ==================================================================================
 * Vista detallada de una cita médica con toda la información
 * Incluye: datos del paciente, médico, fecha/hora, estado, historial
 * ==================================================================================
 */

import React, { useState, useRef } from 'react';
import {
  Card,
  Button,
  Space,
  message,
  Spin,
  Alert,
  Row,
  Col,
  Modal,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  CalendarOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { citasService, Cita, EstadoCita } from '../../services/citasService';
import { getEstadoTag } from './utils/citasUtils';
import DetalleCitaInfo from './components/DetalleCitaInfo';
import DetalleCitaSidebar from './components/DetalleCitaSidebar';

const DetalleCita: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [cita, setCita] = useState<Cita | null>(null);

  const cargarCita = async (citaId: number) => {
    setLoading(true);
    try {
      const data = await citasService.getById(citaId);
      setCita(data);
    } catch (error) {
      message.error('Error al cargar la cita');
    } finally {
      setLoading(false);
    }
  };

  const loadedIdRef = useRef<number | null>(null);
  if (id && loadedIdRef.current !== parseInt(id)) {
    loadedIdRef.current = parseInt(id);
    cargarCita(parseInt(id));
  }

  const handleVolver = () => {
    navigate('/dashboard/citas');
  };

  const handleEditar = () => {
    navigate(`/dashboard/citas/${id}/editar`);
  };

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Cargando información de la cita…</div>
      </div>
    );
  }

  if (!cita) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="Cita no encontrada"
          description="No se pudo encontrar la información de la cita solicitada."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver a Citas
        </Button>
      </div>
    );
  }

  const esAtrasada = dayjs(cita.fecha_cita).isBefore(dayjs(), 'day') &&
    ['agendada', 'confirmada'].includes(cita.estado);

  const esHoy = dayjs(cita.fecha_cita).isSame(dayjs(), 'day');

  return (
    <div style={{ padding: 24 }}>
      {esAtrasada && (
        <Alert
          message="⚠️ Cita Atrasada"
          description="Esta cita ya pasó su fecha programada y aún no ha sido completada."
          type="error"
          showIcon
          icon={<WarningOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      {esHoy && !esAtrasada && ['agendada', 'confirmada', 'en_espera'].includes(cita.estado) && (
        <Alert
          message="📅 Cita de Hoy"
          description="Esta cita está programada para hoy."
          type="info"
          showIcon
          icon={<CalendarOutlined />}
          style={{ marginBottom: 16 }}
        />
      )}

      <Card
        title={
          <Space>
            <CalendarOutlined style={{ fontSize: 24, color: '#1890ff' }} />
            <span style={{ fontSize: 20, fontWeight: 600 }}>Detalle de Cita #{cita.id}</span>
            {getEstadoTag(cita.estado)}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
              Volver
            </Button>
            {!['completada', 'cancelada', 'no_asistio'].includes(cita.estado) && (
              <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
                Editar
              </Button>
            )}
          </Space>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={16}>
            <DetalleCitaInfo cita={cita} esHoy={esHoy} esAtrasada={esAtrasada} />
          </Col>
          <Col xs={24} lg={8}>
            <DetalleCitaSidebar
              cita={cita}
              onConfirmar={async () => {
                if (!cita?.id) return;
                try {
                  await citasService.confirmar(cita.id);
                  message.success('Cita confirmada correctamente');
                  cargarCita(cita.id);
                } catch (error) {
                  message.error('Error al confirmar la cita');
                }
              }}
              onCancelar={async () => {
                if (!cita?.id) return;
                Modal.confirm({
                  title: '¿Cancelar esta cita?',
                  content: '¿Está seguro de querer cancelar esta cita?',
                  okText: 'Sí, cancelar',
                  okType: 'danger',
                  cancelText: 'No',
                  onOk: async () => {
                    try {
                      await citasService.cancelar(cita.id!);
                      message.success('Cita cancelada correctamente');
                      cargarCita(cita.id!);
                    } catch (error) {
                      message.error('Error al cancelar la cita');
                    }
                  },
                });
              }}
              onEnviarRecordatorio={async () => {
                if (!cita?.id) return;
                try {
                  const result = await citasService.enviarRecordatorio(cita.id);
                  if (result.success) {
                    message.success(result.message || 'Recordatorio enviado');
                    cargarCita(cita.id);
                  }
                } catch (error) {
                  message.error('Error al enviar recordatorio');
                }
              }}
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default DetalleCita;
