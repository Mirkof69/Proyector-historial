/**
 * =============================================================================
 * LISTA DE HISTORIALES CLÍNICOS
 * =============================================================================
 * Vista principal que muestra todos los pacientes con estado de Historia Clínica
 * Permite ver quién tiene HC, quién no, y acceder a crear/editar
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {
  Empty,Card, Table, Button, Input, Tag, Space, Tooltip, Badge,
  Row, Col, Statistic} from 'antd';
import {
  FileTextOutlined, EyeOutlined, PlusOutlined, SearchOutlined,
  CheckCircleOutlined, WarningOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { pacientesService, Paciente } from '../../services/pacientesService';

const ListaHistoriasClinicas: React.FC = () => {
  const { message } = useAntdApp();
  const navigate = useNavigate();
  const [pacientes, setPacientes] = useState<Paciente[] | undefined>(undefined);
  const [loading, setLoading] = useState<boolean | undefined>(undefined);
  const [searchText, setSearchText] = useState('');

  // Estadísticas
  const stats = {
    total: pacientes?.length || 0,
    conHistoria: pacientes?.filter(p => p.tiene_historia_clinica).length || 0,
    sinHistoria: pacientes?.filter(p => !p.tiene_historia_clinica).length || 0,
    embarazadas: pacientes?.filter(p => p.embarazo_activo).length || 0,
  };

  // eslint-disable-next-line react-doctor/no-initialize-state
  useEffect(() => {
    cargarPacientes();
  }, []);

  const cargarPacientes = async () => {
    setLoading(true);
    try {
      const data = await pacientesService.listar({ activo: true });

      // FIX: Mapear campos del backend a los que necesita la tabla
      const pacientesMapeados = data.map(p => ({
        ...p,
        numero_documento: p.numero_documento || p.ci,           // Usar CI si no tiene numero_documento
        numero_historia: p.numero_historia || p.id_clinico,     // Usar id_clinico como número de historia
        tiene_historia_clinica: p.tiene_historia_clinica || false,  // Por defecto false si no viene del backend
        embarazo_activo: p.embarazo_activo || (p.embarazos_activos && p.embarazos_activos > 0) || false,
        fecha_modificacion: p.fecha_modificacion || p.fecha_actualizacion || p.fecha_registro,
      }));

      setPacientes(pacientesMapeados);
    } catch (error) {
      message.error('Error al cargar pacientes');
    } finally {
      setLoading(false);
    }
  };

  const filteredPacientes = (pacientes || []).filter(p =>
    p.nombre_completo?.toLowerCase().includes(searchText.toLowerCase()) ||
    p.numero_documento?.includes(searchText) ||
    p.numero_historia?.includes(searchText)
  );

  const columns = [
    {
      title: 'N° Historia',
      dataIndex: 'numero_historia',
      key: 'numero_historia',
      width: 120,
      render: (text: string) => <strong>{text || '-'}</strong>,
    },
    {
      title: 'Documento',
      dataIndex: 'numero_documento',
      key: 'numero_documento',
      width: 120,
    },
    {
      title: 'Nombre Completo',
      dataIndex: 'nombre_completo',
      key: 'nombre_completo',
      width: 250,
      render: (text: string, record: Paciente) => (
        <Space direction="vertical" size={0}>
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.embarazo_activo && (
            <Tag color="purple" style={{ fontSize: 12 }}>Embarazo Activo</Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Estado HC',
      key: 'estado_hc',
      width: 180,
      filters: [
        { text: 'Con Historia Clínica', value: 'con' },
        { text: 'Sin Historia Clínica', value: 'sin' },
      ],
      onFilter: (value: any, record: Paciente) =>
        value === 'con' ? (record.tiene_historia_clinica || false) : !(record.tiene_historia_clinica || false),
      render: (_: any, record: Paciente) => {
        if (record.tiene_historia_clinica) {
          return (
            <Tag icon={<CheckCircleOutlined />} color="success">
              HC Completa
            </Tag>
          );
        } else {
          return (
            <Tag icon={<WarningOutlined />} color="warning">
              Sin HC
            </Tag>
          );
        }
      },
    },
    {
      title: 'Última Actualización',
      dataIndex: 'fecha_modificacion',
      key: 'fecha_modificacion',
      width: 150,
      render: (fecha: string) =>
        fecha ? new Date(fecha).toISOString().slice(0, 10) : '-',
      sorter: (a: Paciente, b: Paciente) => {
        if (!a.fecha_modificacion) return 1;
        if (!b.fecha_modificacion) return -1;
        return new Date(a.fecha_modificacion).getTime() - new Date(b.fecha_modificacion).getTime();
      },
    },
    {
      title: 'Acciones',
      key: 'acciones',
      fixed: 'right' as const,
      width: 150,
      render: (_: any, record: Paciente) => (
        <Space>
          {record.tiene_historia_clinica ? (
            <Tooltip title="Ver Historia Clínica">
              <Button
                type="primary"
                icon={<EyeOutlined />}
                size="small"
                onClick={() => navigate(`/dashboard/pacientes/${record.id}/historia`)}
              >
                Ver HC
              </Button>
            </Tooltip>
          ) : (
            <Tooltip title="Crear Historia Clínica">
              <Button
                type="primary"
                icon={<PlusOutlined />}
                size="small"
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                onClick={() => navigate(`/dashboard/pacientes/${record.id}/historia`)}
              >
                Crear HC
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="page-container" style={{ padding: 24 }}>
      {/* Header */}
      <Card style={{ marginBottom: 24 }}>
        <Row align="middle" justify="space-between">
          <Col>
            <Space align="center">
              <FileTextOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <div>
                <h2 style={{ margin: 0 }}>Gestión de Historiales Clínicos</h2>
                <p style={{ margin: 0, color: '#8c8c8c' }}>
                  Visualiza y administra las historias clínicas de todos los pacientes
                </p>
              </div>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Estadísticas */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Pacientes"
              value={stats.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Con Historia Clínica"
              value={stats.conHistoria}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Sin Historia Clínica"
              value={stats.sinHistoria}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix={`/ ${stats.total}`}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Embarazos Activos"
              value={stats.embarazadas}
              prefix={<Badge status="processing" />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Búsqueda */}
      <Card style={{ marginBottom: 16 }}>
        <Input
          placeholder="Buscar por nombre, documento o N° historia..."
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          size="large"
          allowClear
        />
      </Card>

      {/* Tabla */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredPacientes}
          locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No hay historias clínicas registradas" /> }}
          loading={loading}
          rowKey="id"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total: ${total} pacientes`,
          }}
          scroll={{ x: 1200 }}
          rowClassName={(record) =>
            !record.tiene_historia_clinica ? 'sin-historia-clinica' : ''
          }
        />
      </Card>

      <style>{`
        .sin-historia-clinica {
          background-color: #fffbe6;
        }
        .dark .sin-historia-clinica {
          background-color: rgba(250, 173, 20, 0.1);
        }
      `}</style>
    </div>
  );
};

export default ListaHistoriasClinicas;
