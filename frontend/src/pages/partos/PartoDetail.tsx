// ===========================================
// VISTA DETALLADA DE PARTO
// ===========================================
// Componente para visualizar información completa del parto
// Incluye datos del parto, recién nacidos y complicaciones

import React, { useEffect, useState } from 'react';
import {
  Card,
  Descriptions,
  Button,
  Tag,
  Spin,
  message,
  Tabs,
  Table,
  Empty,
  Row,
  Col,
  Statistic,
  Alert
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  BabyCarriageOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { PartosService } from '../../services/api';
import { Parto } from '../../types';
import dayjs from 'dayjs';

const { TabPane } = Tabs;

// Componente principal de detalle
const PartoDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [parto, setParto] = useState<Parto | null>(null);
  const [loading, setLoading] = useState(true);
  const [recienNacidos, setRecienNacidos] = useState<any[]>([]);
  const [complicacionesList, setComplicacionesList] = useState<any[]>([]);

  useEffect(() => {
    fetchParto();
    fetchRecienNacidos();
    fetchComplicaciones();
  }, [id]);

  // Obtener datos del parto
  const fetchParto = async () => {
    setLoading(true);
    try {
      const response = await PartosService.getById(Number(id));
      setParto(response.data);
    } catch (error) {
      message.error('Error al cargar datos del parto');
      navigate('/partos');
    } finally {
      setLoading(false);
    }
  };

  // Obtener recién nacidos
  const fetchRecienNacidos = async () => {
    try {
      const response = await PartosService.getRecienNacidos(Number(id));
      setRecienNacidos(response.data || []);
    } catch (error) {
      console.error('Error al cargar recién nacidos:', error);
    }
  };

  // Obtener complicaciones
  const fetchComplicaciones = async () => {
    try {
      const response = await PartosService.getComplicaciones(Number(id));
      setComplicacionesList(response.data || []);
    } catch (error) {
      console.error('Error al cargar complicaciones:', error);
    }
  };

  if (loading || !parto) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Columnas para tabla de recién nacidos
  const recienNacidosColumns = [
    {
      title: 'Nombre',
      dataIndex: 'nombre',
      key: 'nombre',
    },
    {
      title: 'Sexo',
      dataIndex: 'sexo',
      key: 'sexo',
      render: (sexo: string) => (
        <Tag color={sexo === 'masculino' ? 'blue' : 'pink'}>
          {sexo.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Peso (g)',
      dataIndex: 'peso',
      key: 'peso',
      render: (peso: number) => `${peso} g`,
    },
    {
      title: 'Talla (cm)',
      dataIndex: 'talla',
      key: 'talla',
      render: (talla: number) => `${talla} cm`,
    },
    {
      title: 'APGAR 1min',
      dataIndex: 'apgar_1min',
      key: 'apgar_1min',
      render: (apgar: number) => (
        <Tag color={apgar >= 7 ? 'green' : apgar >= 4 ? 'orange' : 'red'}>
          {apgar}
        </Tag>
      ),
    },
    {
      title: 'APGAR 5min',
      dataIndex: 'apgar_5min',
      key: 'apgar_5min',
      render: (apgar: number) => (
        <Tag color={apgar >= 7 ? 'green' : apgar >= 4 ? 'orange' : 'red'}>
          {apgar}
        </Tag>
      ),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors = {
          vivo: 'green',
          fallecido: 'red',
          critico: 'orange',
        };
        return <Tag color={colors[estado as keyof typeof colors]}>{estado.toUpperCase()}</Tag>;
      },
    },
  ];

  // Columnas para tabla de complicaciones
  const complicacionesColumns = [
    {
      title: 'Tipo',
      dataIndex: 'tipo_complicacion',
      key: 'tipo_complicacion',
      render: (tipo: string) => tipo.toUpperCase().replace('_', ' '),
    },
    {
      title: 'Momento',
      dataIndex: 'momento',
      key: 'momento',
      render: (momento: string) => momento.toUpperCase().replace('_', ' '),
    },
    {
      title: 'Severidad',
      dataIndex: 'severidad',
      key: 'severidad',
      render: (severidad: string) => {
        const colors = {
          leve: 'green',
          moderada: 'orange',
          severa: 'red',
          critica: 'volcano',
        };
        return <Tag color={colors[severidad as keyof typeof colors]}>{severidad.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/partos')}
              style={{ marginRight: 16 }}
            />
            Detalle del Parto
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/partos/${id}/edit`)}
          >
            Editar
          </Button>
        }
      >
        {parto.complicaciones && (
          <Alert
            message="Parto con Complicaciones"
            description={parto.descripcion_complicaciones}
            type="warning"
            showIcon
            icon={<WarningOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Tabs defaultActiveKey="1">
          {/* Tab 1: Información General */}
          <TabPane tab="Información del Parto" key="1">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Tipo de Parto"
                    value={parto.tipo_parto.toUpperCase()}
                    prefix={<BabyCarriageOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Edad Gestacional"
                    value={`${parto.edad_gestacional_semanas}+${parto.edad_gestacional_dias}`}
                    suffix="semanas"
                    prefix={<ClockCircleOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Estado"
                    value={parto.estado.toUpperCase().replace('_', ' ')}
                    valueStyle={{
                      color: parto.estado === 'finalizado' ? '#3f8600' :
                             parto.estado === 'complicado' ? '#cf1322' : '#1890ff'
                    }}
                  />
                </Card>
              </Col>
            </Row>

            <Descriptions bordered column={{ xs: 1, sm: 2, md: 2 }}>
              <Descriptions.Item label="ID Parto">
                <strong>#{parto.id}</strong>
              </Descriptions.Item>

              <Descriptions.Item label="Estado">
                <Tag color={
                  parto.estado === 'finalizado' ? 'green' :
                  parto.estado === 'complicado' ? 'red' : 'blue'
                }>
                  {parto.estado.toUpperCase().replace('_', ' ')}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Paciente" span={2}>
                {parto.paciente_nombre || `ID: ${parto.embarazo}`}
              </Descriptions.Item>

              <Descriptions.Item label="Fecha del Parto">
                {dayjs(parto.fecha_parto).format('DD/MM/YYYY')}
              </Descriptions.Item>

              <Descriptions.Item label="Hora de Nacimiento">
                {parto.hora_nacimiento || 'N/A'}
              </Descriptions.Item>

              <Descriptions.Item label="Tipo de Parto">
                <Tag color={parto.tipo_parto === 'eutocico' ? 'green' : 'orange'}>
                  {parto.tipo_parto.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Vía del Parto">
                <Tag>{parto.via_parto.toUpperCase()}</Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Edad Gestacional">
                {parto.edad_gestacional_semanas} semanas + {parto.edad_gestacional_dias} días
              </Descriptions.Item>

              {parto.metodo_determinacion_eg && (
                <Descriptions.Item label="Método Determinación EG">
                  {parto.metodo_determinacion_eg.toUpperCase()}
                </Descriptions.Item>
              )}

              {parto.presentacion_fetal && (
                <Descriptions.Item label="Presentación Fetal">
                  {parto.presentacion_fetal.toUpperCase()}
                </Descriptions.Item>
              )}

              {parto.hora_inicio_trabajo_parto && (
                <Descriptions.Item label="Inicio Trabajo de Parto">
                  {parto.hora_inicio_trabajo_parto}
                </Descriptions.Item>
              )}

              {parto.duracion_trabajo_parto && (
                <Descriptions.Item label="Duración Trabajo Parto">
                  {parto.duracion_trabajo_parto} minutos
                </Descriptions.Item>
              )}

              {parto.liquido_amniotico && (
                <Descriptions.Item label="Líquido Amniótico">
                  <Tag color={parto.liquido_amniotico === 'claro' ? 'green' : 'orange'}>
                    {parto.liquido_amniotico.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
              )}
            </Descriptions>

            {parto.observaciones && (
              <Card title="Observaciones" style={{ marginTop: 16 }}>
                <p>{parto.observaciones}</p>
              </Card>
            )}

            {parto.notas && (
              <Card title="Notas Médicas" style={{ marginTop: 16 }}>
                <p>{parto.notas}</p>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: Placenta y Alumbramiento */}
          <TabPane tab="Placenta y Alumbramiento" key="2">
            <Descriptions bordered column={{ xs: 1, sm: 2 }}>
              {parto.alumbramiento_placenta && (
                <Descriptions.Item label="Tipo de Alumbramiento">
                  <Tag>{parto.alumbramiento_placenta.toUpperCase()}</Tag>
                </Descriptions.Item>
              )}

              {parto.peso_placenta && (
                <Descriptions.Item label="Peso de la Placenta">
                  {parto.peso_placenta} gramos
                </Descriptions.Item>
              )}

              {parto.liquido_amniotico && (
                <Descriptions.Item label="Aspecto Líquido Amniótico" span={2}>
                  <Tag color={parto.liquido_amniotico === 'claro' ? 'green' : 'orange'}>
                    {parto.liquido_amniotico.toUpperCase()}
                  </Tag>
                </Descriptions.Item>
              )}
            </Descriptions>

            {(!parto.alumbramiento_placenta && !parto.peso_placenta && !parto.liquido_amniotico) && (
              <Empty description="Información de placenta no registrada" />
            )}
          </TabPane>

          {/* Tab 3: Recién Nacidos */}
          <TabPane tab={<span><HeartOutlined /> Recién Nacidos</span>} key="3">
            {recienNacidos.length > 0 ? (
              <div>
                <Alert
                  message={`Total de recién nacidos: ${recienNacidos.length}`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Table
                  columns={recienNacidosColumns}
                  dataSource={recienNacidos}
                  rowKey="id"
                  pagination={false}
                />
              </div>
            ) : (
              <Empty description="Sin recién nacidos registrados" />
            )}
          </TabPane>

          {/* Tab 4: Complicaciones */}
          <TabPane tab={<span><WarningOutlined /> Complicaciones</span>} key="4">
            {parto.complicaciones ? (
              <div>
                <Alert
                  message="Este parto presentó complicaciones"
                  description={parto.descripcion_complicaciones}
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {complicacionesList.length > 0 ? (
                  <Table
                    columns={complicacionesColumns}
                    dataSource={complicacionesList}
                    rowKey="id"
                    pagination={false}
                  />
                ) : (
                  <Empty description="Sin complicaciones detalladas registradas" />
                )}
              </div>
            ) : (
              <Alert
                message="Parto sin complicaciones"
                type="success"
                showIcon
              />
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default PartoDetail;
