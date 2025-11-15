// ===========================================
// VISTA DETALLADA DE USUARIO
// ===========================================
// Componente para visualizar información completa del usuario
// Incluye historial de actividad y estadísticas

import React, { useEffect, useState } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Tag,
  Spin,
  message,
  Tabs,
  Empty,
  Row,
  Col,
  Statistic,
  Alert
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  UserOutlined,
  SafetyOutlined,
  IdcardOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { UsuariosService } from '../../services/api';
import { Usuario } from '../../types';
import dayjs from 'dayjs';

const { TabPane } = Tabs;

// Componente principal de detalle
const UsuarioDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [loading, setLoading] = useState(true);
  const [estadisticas, setEstadisticas] = useState<any>(null);

  useEffect(() => {
    fetchUsuario();
    fetchEstadisticas();
  }, [id]);

  // Obtener datos del usuario
  const fetchUsuario = async () => {
    setLoading(true);
    try {
      const response = await UsuariosService.getById(Number(id));
      setUsuario(response.data);
    } catch (error) {
      message.error('Error al cargar datos del usuario');
      navigate('/usuarios');
    } finally {
      setLoading(false);
    }
  };

  // Obtener estadísticas del usuario
  const fetchEstadisticas = async () => {
    try {
      const response = await UsuariosService.getEstadisticas(Number(id));
      setEstadisticas(response.data);
    } catch (error) {
      console.error('Error al cargar estadísticas:', error);
    }
  };

  if (loading || !usuario) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Obtener color del rol
  const getRolColor = (rol: string) => {
    const colors = {
      administrador: 'red',
      medico: 'blue',
      enfermera: 'green',
      recepcionista: 'orange',
    };
    return colors[rol as keyof typeof colors] || 'default';
  };

  // Obtener color del estado
  const getEstadoColor = (estado: string) => {
    const colors = {
      activo: 'green',
      inactivo: 'default',
      bloqueado: 'red',
    };
    return colors[estado as keyof typeof colors] || 'default';
  };

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/usuarios')}
              style={{ marginRight: 16 }}
            />
            Detalle del Usuario
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/usuarios/${id}/edit`)}
          >
            Editar
          </Button>
        }
      >
        {usuario.estado === 'bloqueado' && (
          <Alert
            message="Usuario Bloqueado"
            description="Este usuario se encuentra bloqueado y no puede acceder al sistema"
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {usuario.estado === 'inactivo' && (
          <Alert
            message="Usuario Inactivo"
            description="Este usuario está inactivo en el sistema"
            type="warning"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Tabs defaultActiveKey="1">
          {/* Tab 1: Información General */}
          <TabPane tab={<span><UserOutlined /> Información General</span>} key="1">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Rol"
                    value={usuario.rol.toUpperCase()}
                    prefix={<IdcardOutlined />}
                    valueStyle={{ color: getRolColor(usuario.rol) === 'red' ? '#cf1322' : '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Estado"
                    value={usuario.estado.toUpperCase()}
                    prefix={<SafetyOutlined />}
                    valueStyle={{
                      color: usuario.estado === 'activo' ? '#3f8600' :
                             usuario.estado === 'bloqueado' ? '#cf1322' : '#8c8c8c'
                    }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="ID de Usuario"
                    value={usuario.id}
                  />
                </Card>
              </Col>
            </Row>

            <Descriptions bordered column={{ xs: 1, sm: 2, md: 2 }}>
              <Descriptions.Item label="Nombre de Usuario">
                <strong>{usuario.username}</strong>
              </Descriptions.Item>

              <Descriptions.Item label="Nombre Completo">
                {usuario.nombre_completo}
              </Descriptions.Item>

              <Descriptions.Item label="Email">
                {usuario.email}
              </Descriptions.Item>

              <Descriptions.Item label="Rol">
                <Tag color={getRolColor(usuario.rol)}>
                  {usuario.rol.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Estado">
                <Tag color={getEstadoColor(usuario.estado)}>
                  {usuario.estado.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              {usuario.cedula_identidad && (
                <Descriptions.Item label="Cédula de Identidad">
                  {usuario.cedula_identidad}
                </Descriptions.Item>
              )}

              {usuario.telefono && (
                <Descriptions.Item label="Teléfono">
                  {usuario.telefono}
                </Descriptions.Item>
              )}

              {usuario.especialidad && (
                <Descriptions.Item label="Especialidad" span={2}>
                  {usuario.especialidad}
                </Descriptions.Item>
              )}

              {usuario.numero_registro_profesional && (
                <Descriptions.Item label="Registro Profesional" span={2}>
                  {usuario.numero_registro_profesional}
                </Descriptions.Item>
              )}

              {usuario.fecha_creacion && (
                <Descriptions.Item label="Fecha de Creación">
                  {dayjs(usuario.fecha_creacion).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}

              {usuario.fecha_actualizacion && (
                <Descriptions.Item label="Última Actualización">
                  {dayjs(usuario.fecha_actualizacion).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}

              {usuario.ultimo_login && (
                <Descriptions.Item label="Último Acceso" span={2}>
                  {dayjs(usuario.ultimo_login).format('DD/MM/YYYY HH:mm')}
                </Descriptions.Item>
              )}
            </Descriptions>

            {usuario.observaciones && (
              <Card title="Observaciones" style={{ marginTop: 16 }}>
                <p>{usuario.observaciones}</p>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: Estadísticas */}
          <TabPane tab="Estadísticas" key="2">
            {estadisticas ? (
              <div>
                <Row gutter={16}>
                  <Col xs={24} sm={12} md={6}>
                    <Card>
                      <Statistic
                        title="Total Registros"
                        value={estadisticas.total_registros || 0}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Card>
                      <Statistic
                        title="Este Mes"
                        value={estadisticas.registros_mes || 0}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Card>
                      <Statistic
                        title="Esta Semana"
                        value={estadisticas.registros_semana || 0}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={12} md={6}>
                    <Card>
                      <Statistic
                        title="Hoy"
                        value={estadisticas.registros_hoy || 0}
                      />
                    </Card>
                  </Col>
                </Row>
              </div>
            ) : (
              <Empty description="Estadísticas no disponibles" />
            )}
          </TabPane>

          {/* Tab 3: Permisos y Accesos */}
          <TabPane tab={<span><SafetyOutlined /> Permisos</span>} key="3">
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Rol del Sistema">
                <Tag color={getRolColor(usuario.rol)}>
                  {usuario.rol.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Permisos">
                {usuario.rol === 'administrador' && (
                  <div>
                    <Tag color="red">Acceso Total</Tag>
                    <Tag color="red">Gestión de Usuarios</Tag>
                    <Tag color="red">Configuración del Sistema</Tag>
                  </div>
                )}
                {usuario.rol === 'medico' && (
                  <div>
                    <Tag color="blue">Gestión de Pacientes</Tag>
                    <Tag color="blue">Gestión de Embarazos</Tag>
                    <Tag color="blue">Gestión de Partos</Tag>
                    <Tag color="blue">Controles Prenatales</Tag>
                  </div>
                )}
                {usuario.rol === 'enfermera' && (
                  <div>
                    <Tag color="green">Ver Pacientes</Tag>
                    <Tag color="green">Registrar Controles</Tag>
                    <Tag color="green">Ver Embarazos</Tag>
                  </div>
                )}
                {usuario.rol === 'recepcionista' && (
                  <div>
                    <Tag color="orange">Registro de Pacientes</Tag>
                    <Tag color="orange">Ver Citas</Tag>
                    <Tag color="orange">Gestión de Turnos</Tag>
                  </div>
                )}
              </Descriptions.Item>

              <Descriptions.Item label="Estado de Acceso">
                {usuario.estado === 'activo' ? (
                  <Tag color="green">PERMITIDO</Tag>
                ) : usuario.estado === 'bloqueado' ? (
                  <Tag color="red">BLOQUEADO</Tag>
                ) : (
                  <Tag color="default">INACTIVO</Tag>
                )}
              </Descriptions.Item>
            </Descriptions>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default UsuarioDetail;
