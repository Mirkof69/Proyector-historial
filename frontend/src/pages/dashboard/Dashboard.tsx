// ===========================================
// PÁGINA DE DASHBOARD PRINCIPAL
// ===========================================

import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Spin } from 'antd';
import {
  UserOutlined,
  HeartOutlined,
  BabyCarriageOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { PacientesService, EmbarazosService, PartosService, UsuariosService } from '../../services/api';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalPacientes: 0,
    totalEmbarazos: 0,
    embarazosActivos: 0,
    totalPartos: 0,
    totalUsuarios: 0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [pacientes, embarazos, partos, usuarios] = await Promise.all([
          PacientesService.getEstadisticas(),
          EmbarazosService.getEstadisticas(),
          PartosService.getEstadisticas(),
          UsuariosService.getEstadisticas(),
        ]);

        setStats({
          totalPacientes: pacientes.data.estadisticas.total_pacientes || 0,
          totalEmbarazos: embarazos.data.estadisticas.total_embarazos || 0,
          embarazosActivos: embarazos.data.estadisticas.embarazos_activos || 0,
          totalPartos: partos.data.total_partos || 0,
          totalUsuarios: usuarios.data.estadisticas.total_usuarios || 0,
        });
      } catch (error) {
        console.error('Error cargando estadísticas:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Total Pacientes"
              value={stats.totalPacientes}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Embarazos Activos"
              value={stats.embarazosActivos}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Total Partos"
              value={stats.totalPartos}
              prefix={<BabyCarriageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={6}>
          <Card>
            <Statistic
              title="Usuarios Sistema"
              value={stats.totalUsuarios}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
