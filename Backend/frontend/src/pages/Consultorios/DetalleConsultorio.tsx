/**
 * =============================================================================
 * CONSULTORIOS - VISTA DE DETALLE
 * =============================================================================
 * Vista completa de información de un consultorio
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card, Descriptions, Button, Space, Tag, Statistic, Row, Col, Spin, Empty} from "antd";
import {
  ArrowLeftOutlined, EditOutlined, HomeOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ToolOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { consultoriosService, Consultorio, EstadoConsultorio } from '../../services/consultoriosService';

const getEstadoConfig = (estado: EstadoConsultorio | string) => {
  const configs: Record<string, { color: string; icon: React.ReactElement; text: string }> = {
    'disponible': { color: 'success', icon: <CheckCircleOutlined />, text: 'Disponible' },
    'ocupado': { color: 'processing', icon: <HomeOutlined />, text: 'Ocupado' },
    'mantenimiento': { color: 'warning', icon: <ToolOutlined />, text: 'En Mantenimiento' },
    'reservado': { color: 'default', icon: <ClockCircleOutlined />, text: 'Reservado' },
    'inactivo': { color: 'error', icon: <CloseCircleOutlined />, text: 'Inactivo' },
  };
  return configs[estado] || configs['inactivo'];
};

const DetalleConsultorio: React.FC = () => {
  const { message } = useAntdApp();
  const [consultorio, setConsultorio] = useState<Consultorio | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const cargarConsultorio = async (consultorioId: number) => {
    setLoading(true);
    try {
      const data = await consultoriosService.getById(consultorioId);
      setConsultorio(data);
    } catch (error) {
      message.error('Error cargando consultorio');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) cargarConsultorio(parseInt(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!consultorio) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <Empty description="Consultorio no encontrado" />
          <Button onClick={() => navigate('/consultorios')}>
            Volver al listado
          </Button>
        </Card>
      </div>
    );
  }

  const estadoConfig = getEstadoConfig(consultorio.estado || 'inactivo');

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/consultorios')}
            >
              Volver
            </Button>
            <h2 style={{ margin: 0 }}>
              {consultorio.nombre}
            </h2>
            <Tag color={estadoConfig.color} icon={estadoConfig.icon}>
              {estadoConfig.text}
            </Tag>
            {consultorio.activo ? (
              <Tag color="success">Activo</Tag>
            ) : (
              <Tag color="error">Inactivo</Tag>
            )}
          </Space>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/consultorios/editar/${consultorio.id}`)}
          >
            Editar
          </Button>
        </Space>
      </Card>

      {/* Estadísticas rápidas */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Código"
              value={consultorio.codigo}
              prefix={<HomeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Capacidad"
              value={consultorio.capacidad_personas || 0}
              suffix="personas"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Piso"
              value={consultorio.piso || 0}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Citas Hoy"
              value={consultorio.total_citas_hoy || 0}
            />
          </Card>
        </Col>
      </Row>

      {/* Información General */}
      <Card title="Información General" style={{ marginBottom: 16 }}>
        <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }}>
          <Descriptions.Item label="Código">
            {consultorio.codigo}
          </Descriptions.Item>
          <Descriptions.Item label="Nombre">
            {consultorio.nombre}
          </Descriptions.Item>
          <Descriptions.Item label="Tipo">
            <Tag color="blue">{consultorio.tipo}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Área">
            {consultorio.area || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Piso">
            {consultorio.piso || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Capacidad">
            {consultorio.capacidad_personas || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Descripción" span={3}>
            {consultorio.descripcion || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Equipamiento */}
      <Card title="Equipamiento" style={{ marginBottom: 16 }}>
        <Descriptions bordered column={{ xs: 1, sm: 2 }}>
          <Descriptions.Item label="Tipo de Equipamiento">
            {consultorio.equipamiento ? (
              <Tag color="purple">{consultorio.equipamiento}</Tag>
            ) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Características">
            <Space wrap>
              {consultorio.tiene_camilla && <Tag color="green" icon={<CheckCircleOutlined />}>Camilla</Tag>}
              {consultorio.tiene_escritorio && <Tag color="blue" icon={<CheckCircleOutlined />}>Escritorio</Tag>}
              {consultorio.tiene_computadora && <Tag color="purple" icon={<CheckCircleOutlined />}>Computadora</Tag>}
              {consultorio.tiene_lavamanos && <Tag color="cyan" icon={<CheckCircleOutlined />}>Lavamanos</Tag>}
              {consultorio.tiene_oxigeno && <Tag color="orange" icon={<CheckCircleOutlined />}>Oxígeno</Tag>}
              {consultorio.tiene_aspirador && <Tag color="geekblue" icon={<CheckCircleOutlined />}>Aspirador</Tag>}
              {!consultorio.tiene_camilla && !consultorio.tiene_escritorio &&
               !consultorio.tiene_computadora && !consultorio.tiene_lavamanos &&
               !consultorio.tiene_oxigeno && !consultorio.tiene_aspirador && '-'}
            </Space>
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Observaciones */}
      {consultorio.observaciones && (
        <Card title="Observaciones">
          <p>{consultorio.observaciones}</p>
        </Card>
      )}
    </div>
  );
};

export default DetalleConsultorio;
