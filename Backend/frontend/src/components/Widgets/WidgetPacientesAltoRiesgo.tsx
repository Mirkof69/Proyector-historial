/**
 * =============================================================================
 * WIDGET: PACIENTES DE ALTO RIESGO
 * =============================================================================
 * Widget para mostrar pacientes embarazadas de alto riesgo en el Dashboard
 * =============================================================================
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  List,
  Avatar,
  Tag,
  Space,
  Typography,
  Badge,
  Button,
  Spin,
  Empty,
  Tooltip,
  Progress
} from 'antd';
import {
  WarningOutlined,
  UserOutlined,
  EyeOutlined,
  AlertOutlined,
  MedicineBoxOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Text } = Typography;

interface PacienteAltoRiesgo {
  id: number;
  nombre_completo: string;
  ci: string;
  embarazo_id: number;
  riesgo: 'alto' | 'critico';
  edad_gestacional: number;
  factores_riesgo: string[];
  score_riesgo: number;
  ultima_actualizacion: string;
}

const WidgetPacientesAltoRiesgo: React.FC = () => {
  const navigate = useNavigate();
  const [pacientes, setPacientes] = useState<PacienteAltoRiesgo[]>([]);
  const loadingRef = useRef(true);
  const [totalAltoRiesgo, setTotalAltoRiesgo] = useState(0);

  useEffect(() => {
    cargarPacientesAltoRiesgo();
  }, []);

  const cargarPacientesAltoRiesgo = async () => {
    loadingRef.current = true;
    try {
      // Obtener embarazos activos de alto riesgo usando el servicio API
      const response: any = await api.get('/embarazos/', {
        params: {
          estado: 'activo',
          riesgo_embarazo: 'alto'
        }
      });

      //  FIX: Validar que sea array
      const embarazosData = response?.results || response || [];
      const embarazosAltoRiesgo = Array.isArray(embarazosData) ? embarazosData : [];
      setTotalAltoRiesgo(embarazosAltoRiesgo.length);

      // Procesar y formatear datos
      const pacientesFormateados = embarazosAltoRiesgo.slice(0, 5).map((embarazo: any) => {
        // Detectar factores de riesgo
        const factores = [];

        if (embarazo.gestas_previas && embarazo.gestas_previas >= 5) {
          factores.push('Gran multÃƒÂ­para');
        }
        if (embarazo.cesareas_previas && embarazo.cesareas_previas >= 2) {
          factores.push('Ã¢â€°Â¥2 CesÃƒÂ¡reas');
        }
        if (embarazo.abortos_previos && embarazo.abortos_previos >= 2) {
          factores.push('Abortos recurrentes');
        }

        // Calcular edad gestacional desde FUM
        const edadGestacional = embarazo.fecha_ultima_menstruacion
          ? dayjs().diff(dayjs(embarazo.fecha_ultima_menstruacion), 'weeks')
          : 0;

        // Score de riesgo simplificado (0-100)
        let score = 50; // Base alto riesgo
        if (embarazo.cesareas_previas >= 2) score += 15;
        if (embarazo.abortos_previos >= 2) score += 10;
        if (embarazo.gestas_previas >= 5) score += 10;
        if (edadGestacional > 37) score += 15;

        return {
          id: embarazo.paciente,
          nombre_completo: embarazo.paciente_info?.nombre_completo || 'Sin nombre',
          ci: embarazo.paciente_info?.ci || 'Sin CI',
          embarazo_id: embarazo.id,
          riesgo: score >= 70 ? 'critico' as const : 'alto' as const,
          edad_gestacional: edadGestacional,
          factores_riesgo: factores.length > 0 ? factores : ['Alto riesgo obstÃƒÂ©trico'],
          score_riesgo: Math.min(score, 100),
          ultima_actualizacion: embarazo.fecha_actualizacion || embarazo.fecha_registro
        };
      });

      setPacientes(pacientesFormateados);
    } catch (error) {
      console.error('Error cargando pacientes de alto riesgo:', error);
      setPacientes([]);
    } finally {
      loadingRef.current = false;
    }
  };

  const handleVerPaciente = (pacienteId: number) => {
    navigate(`/dashboard/historia-clinica/${pacienteId}`);
  };

  const getRiesgoColor = (riesgo: 'alto' | 'critico') => {
    return riesgo === 'critico' ? '#cf1322' : '#fa8c16';
  };

  const getRiesgoIcon = (riesgo: 'alto' | 'critico') => {
    return riesgo === 'critico' ? <AlertOutlined /> : <WarningOutlined />;
  };

  if (loadingRef.current && pacientes.length === 0) {
    return (
      <Card title="Pacientes de Alto Riesgo" className="shadow-card">
        <div style={{ textAlign: 'center', padding: 40 }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>Cargando pacientes…</p>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <Badge count={totalAltoRiesgo} offset={[10, 0]}>
            <WarningOutlined style={{ fontSize: 20, color: '#fa8c16' }} />
          </Badge>
          <span>Pacientes de Alto Riesgo</span>
        </Space>
      }
      extra={
        <Tag color="orange" icon={<WarningOutlined />}>
          {totalAltoRiesgo} Total
        </Tag>
      }
      className="shadow-card"
      actions={[
        <Button
          key="view-all"
          type="link"
          onClick={() => navigate('/dashboard/embarazos', { state: { filtro: 'alto_riesgo' } })}
        >
          Ver todos los casos
        </Button>
      ]}
    >
      {pacientes.length === 0 ? (
        <Empty
          description="No hay pacientes de alto riesgo actualmente"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <List
          dataSource={pacientes}
          renderItem={(paciente) => (
            <List.Item
              key={`paciente-riesgo-${paciente.embarazo_id}`}
              actions={[
                <Tooltip title="Ver Historia ClÃƒÂ­nica" key="view">
                  <Button
                    type="primary"
                    size="small"
                    icon={<EyeOutlined />}
                    onClick={() => handleVerPaciente(paciente.id)}
                  >
                    Ver
                  </Button>
                </Tooltip>
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Badge
                    dot
                    status={paciente.riesgo === 'critico' ? 'error' : 'warning'}
                  >
                    <Avatar
                      icon={<UserOutlined />}
                      style={{
                        backgroundColor: getRiesgoColor(paciente.riesgo)
                      }}
                    />
                  </Badge>
                }
                title={
                  <Space direction="vertical" size={2}>
                    <Space>
                      <Text strong>{paciente.nombre_completo}</Text>
                      <Tag
                        color={getRiesgoColor(paciente.riesgo)}
                        icon={getRiesgoIcon(paciente.riesgo)}
                      >
                        {paciente.riesgo === 'critico' ? 'CRÃƒ TICO' : 'ALTO'}
                      </Tag>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      CI: {paciente.ci} Ã¢â‚¬Â¢ EG: {paciente.edad_gestacional} sem
                    </Text>
                  </Space>
                }
                description={
                  <Space direction="vertical" size={4} style={{ width: '100%' }}>
                    <div>
                      <Text strong style={{ fontSize: 12 }}>Score de Riesgo:</Text>
                      <Progress
                        percent={paciente.score_riesgo}
                        strokeColor={{
                          '0%': '#fa8c16',
                          '100%': '#cf1322',
                        }}
                        size="small"
                        status={paciente.score_riesgo >= 70 ? 'exception' : 'normal'}
                      />
                    </div>
                    <div>
                      <Text strong style={{ fontSize: 12 }}>Factores de Riesgo:</Text>
                      <div style={{ marginTop: 4 }}>
                        {paciente.factores_riesgo.map((factor) => (
                          <Tag
                            key={`factor-${paciente.embarazo_id}-${factor}`}
                            icon={<MedicineBoxOutlined />}
                            color="warning"
                            style={{ marginBottom: 4 }}
                          >
                            {factor}
                          </Tag>
                        ))}
                      </div>
                    </div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      Última actualización: {dayjs(paciente.ultima_actualizacion).fromNow()}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default WidgetPacientesAltoRiesgo;

