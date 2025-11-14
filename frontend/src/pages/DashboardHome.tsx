/**
 * =============================================================================
 * DASHBOARD HOME - ESTADÍSTICAS EN TIEMPO REAL
 * =============================================================================
 * Página principal del dashboard con métricas y gráficos
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Typography, Space, Table, Tag, Spin, Alert } from 'antd';
import {
  UserOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  RiseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { dashboardService } from '../services/dashboardService';
import type { EstadisticasGenerales, AlertaReciente } from '../types';
import './DashboardHome.css';

const { Title, Text } = Typography;

const DashboardHome: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [estadisticas, setEstadisticas] = useState<EstadisticasGenerales | null>(null);
  const [alertas, setAlertas] = useState<AlertaReciente[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    // Actualizar cada 30 segundos
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [stats, alertasRecientes] = await Promise.all([
        dashboardService.getEstadisticasGenerales(),
        dashboardService.getAlertasRecientes(10),
      ]);

      setEstadisticas(stats);
      setAlertas(alertasRecientes);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severidad: string) => {
    const colors: Record<string, string> = {
      critica: 'error',
      alta: 'warning',
      moderada: 'processing',
      leve: 'default',
    };
    return colors[severidad] || 'default';
  };

  const alertasColumns = [
    {
      title: 'Paciente',
      dataIndex: 'paciente',
      key: 'paciente',
      width: 200,
    },
    {
      title: 'Tipo de Alerta',
      dataIndex: 'tipo',
      key: 'tipo',
      width: 180,
      render: (tipo: string) => <Text code>{tipo}</Text>,
    },
    {
      title: 'Severidad',
      dataIndex: 'severidad',
      key: 'severidad',
      width: 120,
      render: (severidad: string) => (
        <Tag color={getSeverityColor(severidad)}>
          {severidad.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Mensaje',
      dataIndex: 'mensaje',
      key: 'mensaje',
      ellipsis: true,
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      width: 150,
      render: (fecha: string) => new Date(fecha).toLocaleDateString('es-ES'),
    },
  ];

  if (loading && !estadisticas) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="Cargando estadísticas..." />
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <div className="dashboard-home">
      {/* HEADER */}
      <div className="dashboard-header">
        <Title level={2}>Dashboard</Title>
        <Text type="secondary">
          Estadísticas en tiempo real del sistema
        </Text>
      </div>

      {/* ESTADÍSTICAS PRINCIPALES */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card stat-card-blue">
            <Statistic
              title="Total Pacientes"
              value={estadisticas?.total_pacientes || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div className="stat-footer">
              <RiseOutlined /> Activos en el sistema
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card stat-card-red">
            <Statistic
              title="Embarazos Activos"
              value={estadisticas?.embarazos_activos || 0}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
            <div className="stat-footer">
              De {estadisticas?.total_embarazos || 0} totales
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card stat-card-orange">
            <Statistic
              title="Alto Riesgo"
              value={estadisticas?.embarazos_alto_riesgo || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
            <div className="stat-footer">
              Requieren atención especial
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card stat-card-green">
            <Statistic
              title="Controles del Mes"
              value={estadisticas?.controles_mes_actual || 0}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div className="stat-footer">
              <ClockCircleOutlined /> {estadisticas?.proximos_controles || 0} próximos
            </div>
          </Card>
        </Col>
      </Row>

      {/* ALERTAS RECIENTES */}
      <Card
        title={
          <Space>
            <WarningOutlined style={{ color: '#fa8c16' }} />
            <Text strong>Alertas Médicas Recientes</Text>
          </Space>
        }
        extra={
          <Tag color="processing">
            Tiempo Real
          </Tag>
        }
      >
        <Table
          dataSource={alertas}
          columns={alertasColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
          size="small"
        />
      </Card>

      {/* INFORMACIÓN ADICIONAL */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card
            title="Resumen del Día"
            bordered={false}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div className="summary-item">
                <Text>Nuevos Pacientes:</Text>
                <Text strong>0</Text>
              </div>
              <div className="summary-item">
                <Text>Controles Realizados:</Text>
                <Text strong>0</Text>
              </div>
              <div className="summary-item">
                <Text>Alertas Generadas:</Text>
                <Text strong>{alertas.length}</Text>
              </div>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card
            title="Acciones Rápidas"
            bordered={false}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <a href="/dashboard/pacientes">➕ Registrar Nuevo Paciente</a>
              <a href="/dashboard/embarazos">➕ Registrar Nuevo Embarazo</a>
              <a href="/dashboard/controles">➕ Registrar Control Prenatal</a>
              <a href="/dashboard/calculadoras">🧮 Usar Calculadoras FMF</a>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardHome;
