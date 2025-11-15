// ===========================================
// VISTA DETALLADA DE PACIENTE
// ===========================================
// Componente para visualizar información completa del paciente
// Incluye datos personales, historial médico y acciones

import React, { useEffect, useState } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Space,
  Tag,
  Spin,
  message,
  Tabs,
  Table,
  Empty,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  HeartOutlined,
  BabyCarriageOutlined,
  WarningOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PacientesService } from '../../services/api';
import { Paciente } from '../../types';
import dayjs from 'dayjs';

const { TabPane } = Tabs;

// Componente principal de detalle
const PacienteDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [loading, setLoading] = useState(true);
  const [historial, setHistorial] = useState<any>(null);
  const [perfilRiesgo, setPerfilRiesgo] = useState<any>(null);

  useEffect(() => {
    fetchPaciente();
    fetchHistorial();
    fetchPerfilRiesgo();
  }, [id]);

  // Obtener datos del paciente
  const fetchPaciente = async () => {
    setLoading(true);
    try {
      const response = await PacientesService.getById(Number(id));
      setPaciente(response.data);
    } catch (error) {
      message.error('Error al cargar datos del paciente');
      navigate('/pacientes');
    } finally {
      setLoading(false);
    }
  };

  // Obtener historial completo
  const fetchHistorial = async () => {
    try {
      const response = await PacientesService.getHistorial(Number(id));
      setHistorial(response.data);
    } catch (error) {
      console.error('Error al cargar historial:', error);
    }
  };

  // Obtener perfil de riesgo
  const fetchPerfilRiesgo = async () => {
    try {
      const response = await PacientesService.getPerfilRiesgo(Number(id));
      setPerfilRiesgo(response.data);
    } catch (error) {
      console.error('Error al cargar perfil de riesgo:', error);
    }
  };

  if (loading || !paciente) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Columnas para tabla de embarazos
  const embarazosColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Gesta',
      dataIndex: 'numero_gesta',
      key: 'numero_gesta',
    },
    {
      title: 'FUM',
      dataIndex: 'fecha_ultima_menstruacion',
      key: 'fecha_ultima_menstruacion',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
    },
    {
      title: 'FPP',
      dataIndex: 'fecha_probable_parto',
      key: 'fecha_probable_parto',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
    },
    {
      title: 'Riesgo',
      dataIndex: 'riesgo_embarazo',
      key: 'riesgo_embarazo',
      render: (riesgo: string) => {
        const colors = {
          bajo: 'green',
          medio: 'orange',
          alto: 'red',
        };
        return <Tag color={colors[riesgo as keyof typeof colors]}>{riesgo.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => (
        <Tag color={estado === 'activo' ? 'blue' : 'default'}>{estado.toUpperCase()}</Tag>
      ),
    },
  ];

  // Columnas para tabla de partos
  const partosColumns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha_parto',
      key: 'fecha_parto',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY HH:mm'),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_parto',
      key: 'tipo_parto',
      render: (tipo: string) => tipo.toUpperCase(),
    },
    {
      title: 'Vía',
      dataIndex: 'via_parto',
      key: 'via_parto',
      render: (via: string) => via.toUpperCase(),
    },
    {
      title: 'Complicaciones',
      dataIndex: 'complicaciones',
      key: 'complicaciones',
      render: (complicaciones: boolean) => (
        <Tag color={complicaciones ? 'red' : 'green'}>
          {complicaciones ? 'SÍ' : 'NO'}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/pacientes')}
              style={{ marginRight: 16 }}
            />
            Detalle del Paciente
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/pacientes/${id}/edit`)}
          >
            Editar
          </Button>
        }
      >
        <Tabs defaultActiveKey="1">
          {/* Tab 1: Información General */}
          <TabPane tab="Información General" key="1">
            <Descriptions bordered column={{ xs: 1, sm: 2, md: 2 }}>
              <Descriptions.Item label="ID Clínico">
                <strong>{paciente.id_clinico}</strong>
              </Descriptions.Item>

              <Descriptions.Item label="Estado">
                <Tag color={paciente.activo ? 'green' : 'red'}>
                  {paciente.activo ? 'ACTIVO' : 'INACTIVO'}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Nombre Completo" span={2}>
                {paciente.nombre_completo}
              </Descriptions.Item>

              <Descriptions.Item label="Cédula de Identidad">
                {paciente.cedula_identidad || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Pasaporte">
                {paciente.pasaporte || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Fecha de Nacimiento">
                {dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY')}
              </Descriptions.Item>

              <Descriptions.Item label="Edad">
                {paciente.edad} años
              </Descriptions.Item>

              <Descriptions.Item label="Género">
                <Tag color={paciente.genero === 'femenino' ? 'pink' : 'blue'}>
                  {paciente.genero.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Estado Civil">
                {paciente.estado_civil ? paciente.estado_civil.replace('_', ' ').toUpperCase() : 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Grupo Sanguíneo">
                {paciente.grupo_sanguineo || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Factor RH">
                {paciente.factor_rh ? paciente.factor_rh.toUpperCase() : 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Teléfono Principal" span={2}>
                {paciente.telefono_principal || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Teléfono Secundario" span={2}>
                {paciente.telefono_secundario || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Email" span={2}>
                {paciente.email || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Dirección" span={2}>
                {paciente.direccion || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Ocupación">
                {paciente.ocupacion || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Nivel de Educación">
                {paciente.nivel_educacion ? paciente.nivel_educacion.toUpperCase() : 'N/A'}
              </Descriptions.Item>

              {paciente.observaciones && (
                <Descriptions.Item label="Observaciones" span={2}>
                  {paciente.observaciones}
                </Descriptions.Item>
              )}
            </Descriptions>
          </TabPane>

          {/* Tab 2: Historial Médico */}
          <TabPane tab={<span><HeartOutlined /> Historial Médico</span>} key="2">
            {historial ? (
              <div>
                <Row gutter={16} style={{ marginBottom: 24 }}>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Total Embarazos"
                        value={historial.total_embarazos || 0}
                        prefix={<HeartOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Total Partos"
                        value={historial.total_partos || 0}
                        prefix={<BabyCarriageOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} sm={8}>
                    <Card>
                      <Statistic
                        title="Embarazos Activos"
                        value={historial.embarazos_activos || 0}
                        valueStyle={{ color: '#3f8600' }}
                      />
                    </Card>
                  </Col>
                </Row>

                <h3>Embarazos</h3>
                {historial.embarazos && historial.embarazos.length > 0 ? (
                  <Table
                    columns={embarazosColumns}
                    dataSource={historial.embarazos}
                    rowKey="id"
                    pagination={false}
                    style={{ marginBottom: 24 }}
                  />
                ) : (
                  <Empty description="Sin embarazos registrados" style={{ marginBottom: 24 }} />
                )}

                <h3>Partos</h3>
                {historial.partos && historial.partos.length > 0 ? (
                  <Table
                    columns={partosColumns}
                    dataSource={historial.partos}
                    rowKey="id"
                    pagination={false}
                  />
                ) : (
                  <Empty description="Sin partos registrados" />
                )}
              </div>
            ) : (
              <Empty description="Cargando historial médico..." />
            )}
          </TabPane>

          {/* Tab 3: Perfil de Riesgo */}
          <TabPane tab={<span><WarningOutlined /> Perfil de Riesgo</span>} key="3">
            {perfilRiesgo ? (
              <div>
                <Card style={{ marginBottom: 16 }}>
                  <Statistic
                    title="Nivel de Riesgo"
                    value={perfilRiesgo.nivel_riesgo?.toUpperCase() || 'N/A'}
                    valueStyle={{
                      color: perfilRiesgo.nivel_riesgo === 'alto' ? '#cf1322' :
                             perfilRiesgo.nivel_riesgo === 'medio' ? '#fa8c16' : '#3f8600'
                    }}
                  />
                </Card>

                {perfilRiesgo.factores_riesgo && perfilRiesgo.factores_riesgo.length > 0 ? (
                  <div>
                    <h3>Factores de Riesgo Identificados:</h3>
                    <ul>
                      {perfilRiesgo.factores_riesgo.map((factor: string, index: number) => (
                        <li key={index}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <Empty description="Sin factores de riesgo identificados" />
                )}

                {perfilRiesgo.recomendaciones && (
                  <div>
                    <h3>Recomendaciones:</h3>
                    <p>{perfilRiesgo.recomendaciones}</p>
                  </div>
                )}
              </div>
            ) : (
              <Empty description="Cargando perfil de riesgo..." />
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default PacienteDetail;
