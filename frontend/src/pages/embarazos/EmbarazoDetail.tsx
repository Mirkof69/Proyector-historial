// ===========================================
// VISTA DETALLADA DE EMBARAZO
// ===========================================
// Componente para visualizar información completa del embarazo
// Incluye curva de crecimiento, controles y cálculos obstétricos

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
  Progress
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  CalendarOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { EmbarazosService } from '../../services/api';
import { Embarazo } from '../../types';
import dayjs from 'dayjs';

const { TabPane } = Tabs;

// Componente principal de detalle
const EmbarazoDetail: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [embarazo, setEmbarazo] = useState<Embarazo | null>(null);
  const [loading, setLoading] = useState(true);
  const [controles, setControles] = useState<any[]>([]);
  const [calculosObstetricos, setCalculosObstetricos] = useState<any>(null);

  useEffect(() => {
    fetchEmbarazo();
    fetchControles();
    fetchCalculosObstetricos();
  }, [id]);

  // Obtener datos del embarazo
  const fetchEmbarazo = async () => {
    setLoading(true);
    try {
      const response = await EmbarazosService.getById(Number(id));
      setEmbarazo(response.data);
    } catch (error) {
      message.error('Error al cargar datos del embarazo');
      navigate('/embarazos');
    } finally {
      setLoading(false);
    }
  };

  // Obtener controles prenatales
  const fetchControles = async () => {
    try {
      const response = await EmbarazosService.getControles(Number(id));
      setControles(response.data || []);
    } catch (error) {
      console.error('Error al cargar controles:', error);
    }
  };

  // Obtener cálculos obstétricos
  const fetchCalculosObstetricos = async () => {
    try {
      const response = await EmbarazosService.getCalculosObstetricos(Number(id));
      setCalculosObstetricos(response.data);
    } catch (error) {
      console.error('Error al cargar cálculos:', error);
    }
  };

  if (loading || !embarazo) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Calcular progreso del embarazo
  const calcularProgreso = () => {
    if (!calculosObstetricos?.edad_gestacional_dias_total) return 0;
    const diasTotal = calculosObstetricos.edad_gestacional_dias_total;
    return Math.min((diasTotal / 280) * 100, 100);
  };

  // Columnas para tabla de controles
  const controlesColumns = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_control',
      key: 'fecha_control',
      render: (fecha: string) => dayjs(fecha).format('DD/MM/YYYY'),
    },
    {
      title: 'EG',
      key: 'edad_gestacional',
      render: (_: any, record: any) =>
        `${record.semanas_gestacion || 0}+${record.dias_gestacion || 0}`,
    },
    {
      title: 'Peso (kg)',
      dataIndex: 'peso',
      key: 'peso',
    },
    {
      title: 'PA',
      key: 'presion',
      render: (_: any, record: any) =>
        record.presion_sistolica && record.presion_diastolica ?
        `${record.presion_sistolica}/${record.presion_diastolica}` : 'N/A',
    },
    {
      title: 'AU (cm)',
      dataIndex: 'altura_uterina',
      key: 'altura_uterina',
    },
    {
      title: 'FCF',
      dataIndex: 'frecuencia_cardiaca_fetal',
      key: 'frecuencia_cardiaca_fetal',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <div>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/embarazos')}
              style={{ marginRight: 16 }}
            />
            Detalle del Embarazo - Gesta {embarazo.numero_gesta}
          </div>
        }
        extra={
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/embarazos/${id}/edit`)}
          >
            Editar
          </Button>
        }
      >
        <Tabs defaultActiveKey="1">
          {/* Tab 1: Información General */}
          <TabPane tab="Información General" key="1">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Edad Gestacional"
                    value={calculosObstetricos?.edad_gestacional_texto || 'N/A'}
                    prefix={<CalendarOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Progreso"
                    value={calcularProgreso().toFixed(0)}
                    suffix="%"
                    prefix={<CheckCircleOutlined />}
                  />
                  <Progress
                    percent={calcularProgreso()}
                    showInfo={false}
                    strokeColor="#52c41a"
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Nivel de Riesgo"
                    value={embarazo.riesgo_embarazo.toUpperCase()}
                    valueStyle={{
                      color: embarazo.riesgo_embarazo === 'alto' ? '#cf1322' :
                             embarazo.riesgo_embarazo === 'medio' ? '#fa8c16' : '#3f8600'
                    }}
                    prefix={<WarningOutlined />}
                  />
                </Card>
              </Col>
            </Row>

            <Descriptions bordered column={{ xs: 1, sm: 2, md: 2 }}>
              <Descriptions.Item label="ID Embarazo">
                <strong>#{embarazo.id}</strong>
              </Descriptions.Item>

              <Descriptions.Item label="Estado">
                <Tag color={
                  embarazo.estado === 'activo' ? 'blue' :
                  embarazo.estado === 'finalizado' ? 'green' : 'red'
                }>
                  {embarazo.estado.toUpperCase()}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Paciente" span={2}>
                {embarazo.paciente_nombre || `ID: ${embarazo.paciente}`}
              </Descriptions.Item>

              <Descriptions.Item label="Número de Gesta">
                {embarazo.numero_gesta}
              </Descriptions.Item>

              <Descriptions.Item label="Tipo de Embarazo">
                <Tag>{embarazo.tipo_embarazo.toUpperCase()}</Tag>
              </Descriptions.Item>

              <Descriptions.Item label="FUM">
                {dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
              </Descriptions.Item>

              <Descriptions.Item label="FPP">
                {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
              </Descriptions.Item>

              {embarazo.fecha_inicio_control && (
                <Descriptions.Item label="Inicio Control" span={2}>
                  {dayjs(embarazo.fecha_inicio_control).format('DD/MM/YYYY')}
                </Descriptions.Item>
              )}

              <Descriptions.Item label="Embarazo Planificado">
                <Tag color={embarazo.embarazo_planificado ? 'green' : 'default'}>
                  {embarazo.embarazo_planificado ? 'SÍ' : 'NO'}
                </Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Riesgo">
                <Tag color={
                  embarazo.riesgo_embarazo === 'alto' ? 'red' :
                  embarazo.riesgo_embarazo === 'medio' ? 'orange' : 'green'
                }>
                  {embarazo.riesgo_embarazo.toUpperCase()}
                </Tag>
              </Descriptions.Item>
            </Descriptions>

            {embarazo.observaciones && (
              <Card title="Observaciones" style={{ marginTop: 16 }}>
                <p>{embarazo.observaciones}</p>
              </Card>
            )}

            {embarazo.notas && (
              <Card title="Notas Médicas" style={{ marginTop: 16 }}>
                <p>{embarazo.notas}</p>
              </Card>
            )}
          </TabPane>

          {/* Tab 2: Antecedentes Obstétricos */}
          <TabPane tab="Antecedentes Obstétricos" key="2">
            <Card title="GPAC - Historia Obstétrica">
              <Row gutter={16}>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Gestas (G)"
                    value={embarazo.numero_gesta}
                    prefix="G"
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Partos (P)"
                    value={embarazo.numero_para || 0}
                    prefix="P"
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Abortos (A)"
                    value={embarazo.numero_aborto || 0}
                    prefix="A"
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title="Cesáreas (C)"
                    value={embarazo.numero_cesarea || 0}
                    prefix="C"
                  />
                </Col>
              </Row>

              {embarazo.hijos_vivos !== undefined && (
                <div style={{ marginTop: 16 }}>
                  <Statistic
                    title="Hijos Vivos"
                    value={embarazo.hijos_vivos}
                  />
                </div>
              )}
            </Card>
          </TabPane>

          {/* Tab 3: Controles Prenatales */}
          <TabPane tab="Controles Prenatales" key="3">
            {controles.length > 0 ? (
              <Table
                columns={controlesColumns}
                dataSource={controles}
                rowKey="id"
                pagination={false}
              />
            ) : (
              <Empty description="Sin controles prenatales registrados" />
            )}
          </TabPane>

          {/* Tab 4: Cálculos Obstétricos */}
          <TabPane tab="Cálculos Obstétricos" key="4">
            {calculosObstetricos ? (
              <div>
                <Card title="Edad Gestacional" style={{ marginBottom: 16 }}>
                  <Descriptions bordered column={2}>
                    <Descriptions.Item label="Edad Gestacional">
                      {calculosObstetricos.edad_gestacional_texto}
                    </Descriptions.Item>
                    <Descriptions.Item label="Días Totales">
                      {calculosObstetricos.edad_gestacional_dias_total} días
                    </Descriptions.Item>
                    <Descriptions.Item label="Trimestre">
                      {calculosObstetricos.trimestre}° Trimestre
                    </Descriptions.Item>
                    <Descriptions.Item label="Días Restantes">
                      {calculosObstetricos.dias_restantes} días
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card title="Fechas Importantes">
                  <Descriptions bordered column={1}>
                    <Descriptions.Item label="Fecha Última Menstruación (FUM)">
                      {dayjs(embarazo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}
                    </Descriptions.Item>
                    <Descriptions.Item label="Fecha Probable de Parto (FPP)">
                      {dayjs(embarazo.fecha_probable_parto).format('DD/MM/YYYY')}
                    </Descriptions.Item>
                    {calculosObstetricos.fecha_concepcion && (
                      <Descriptions.Item label="Fecha Estimada de Concepción">
                        {dayjs(calculosObstetricos.fecha_concepcion).format('DD/MM/YYYY')}
                      </Descriptions.Item>
                    )}
                  </Descriptions>
                </Card>
              </div>
            ) : (
              <Empty description="Cálculos no disponibles" />
            )}
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default EmbarazoDetail;
