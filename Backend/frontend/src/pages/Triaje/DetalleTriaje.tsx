import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Card, Button, Alert, Row, Col, Skeleton } from 'antd';
import { useNavigate, useParams } from 'react-router-dom';
import { triajeService, TriajeEnfermeria } from '../../services/triajeService';
import { useAntdApp } from '../../hooks/useMessage';
import {
  getClasificacionIMC,
  getClasificacionPresion,
  computarAlertasTriaje,
} from './components/triajeUtils';
import TriajeHeader from './components/TriajeHeader';
import TriajeAlertasClinicas from './components/TriajeAlertasClinicas';
import EvaluacionClinicaTriaje from './components/EvaluacionClinicaTriaje';
import PanelRiesgoClinico from './components/PanelRiesgoClinico';

const DetalleTriaje: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { message } = useAntdApp();

  const [loading, setLoading] = useState(true);
  const [triaje, setTriaje] = useState<TriajeEnfermeria | null>(null);

  const cargarTriaje = useCallback(async (triajeId: number) => {
    setLoading(true);
    try {
      const data = await triajeService.getById(triajeId);
      setTriaje(data);
    } catch (error) {
      message.error('Error al cargar la información del triaje');
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    if (id) cargarTriaje(parseInt(id));
  }, [id, cargarTriaje]);

  const alertas = useMemo(() => (triaje ? computarAlertasTriaje(triaje) : []), [triaje]);

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Card className="shadow-card">
          <Skeleton active avatar paragraph={{ rows: 10 }} />
        </Card>
      </div>
    );
  }

  if (!triaje) {
    return (
      <div style={{ padding: 24 }}>
        <Alert
          message="Triaje no encontrado"
          description="No se pudo encontrar el registro solicitado o ha sido eliminado."
          type="error"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/dashboard/triaje')}>
              Volver a la lista
            </Button>
          }
        />
      </div>
    );
  }

  const clasificacionIMC = triaje.imc ? getClasificacionIMC(Number(triaje.imc)) : null;
  const clasificacionPresion = getClasificacionPresion(triaje.presion_sistolica, triaje.presion_diastolica);

  return (
    <div className="animate-fade-in" style={{ padding: 24 }}>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card className="shadow-card overflow-hidden">
            <TriajeHeader
              triaje={triaje}
              onVolver={() => navigate('/dashboard/triaje')}
              onEditar={() => navigate(`/dashboard/triaje/${triaje.id}/editar`)}
            />

            <TriajeAlertasClinicas alertas={alertas} />

            <Row gutter={[24, 24]}>
              <Col xs={24} lg={16}>
                <EvaluacionClinicaTriaje
                  triaje={triaje}
                  clasificacionIMC={clasificacionIMC}
                  clasificacionPresion={clasificacionPresion}
                />
              </Col>

              <Col xs={24} lg={8}>
                <PanelRiesgoClinico
                  triaje={triaje}
                  onVerHistorial={() => navigate(`/dashboard/pacientes/${triaje.paciente}`)}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DetalleTriaje;
