import React from 'react';
import { Modal, Tabs, Card, Alert, Row, Col, Statistic, Divider, Table, Typography, Progress, Space } from 'antd';
import { BarChartOutlined, UserOutlined, WarningOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { Paciente, PacienteStats } from '../pacientesTypes';

const { Text } = Typography;

interface AnalisisDemograficoModalProps {
  visible: boolean;
  onClose: () => void;
  pacientes: Paciente[];
  stats: PacienteStats;
  token: any;
}

const AnalisisDemograficoModal: React.FC<AnalisisDemograficoModalProps> = ({
  visible, onClose, pacientes, stats, token,
}) => (
  <Modal
    title={<Space><BarChartOutlined /> Panel de Análisis Demográfico</Space>}
    open={visible}
    onCancel={onClose}
    width={1200}
    footer={null}
  >
    <Tabs
      items={[
        {
          key: '1',
          label: 'Distribución por Edad',
          children: (
            <Card>
              <Alert
                message="Pirámide Poblacional"
                description={`Análisis de ${stats.total} pacientes. Edad promedio: ${stats.promedioEdad} años.`}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic title="Menores de 20" value={pacientes.filter(p => (p.edad || 0) < 20).length} suffix="pacientes" />
                </Col>
                <Col span={8}>
                  <Statistic title="20-35 años" value={pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) <= 35).length} suffix="pacientes" />
                </Col>
                <Col span={8}>
                  <Statistic title="Mayores de 35" value={pacientes.filter(p => (p.edad || 0) > 35).length} suffix="pacientes" />
                </Col>
              </Row>
              <Divider />
              <Table
                size="small"
                columns={[
                  { title: 'Rango Etario', dataIndex: 'rango', key: 'rango' },
                  { title: 'Cantidad', dataIndex: 'cantidad', key: 'cantidad' },
                  { title: 'Porcentaje', dataIndex: 'porcentaje', key: 'porcentaje', render: (v: number) => `${v.toFixed(1)}%` }
                ]}
                dataSource={[
                  { key: '1', rango: '< 15 años', cantidad: pacientes.filter(p => (p.edad || 0) < 15).length, porcentaje: (pacientes.filter(p => (p.edad || 0) < 15).length / stats.total) * 100 },
                  { key: '2', rango: '15-19 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 15 && (p.edad || 0) < 20).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 15 && (p.edad || 0) < 20).length / stats.total) * 100 },
                  { key: '3', rango: '20-24 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) < 25).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 20 && (p.edad || 0) < 25).length / stats.total) * 100 },
                  { key: '4', rango: '25-29 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 25 && (p.edad || 0) < 30).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 25 && (p.edad || 0) < 30).length / stats.total) * 100 },
                  { key: '5', rango: '30-34 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 30 && (p.edad || 0) < 35).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 30 && (p.edad || 0) < 35).length / stats.total) * 100 },
                  { key: '6', rango: '35-39 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 35 && (p.edad || 0) < 40).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 35 && (p.edad || 0) < 40).length / stats.total) * 100 },
                  { key: '7', rango: '≥ 40 años', cantidad: pacientes.filter(p => (p.edad || 0) >= 40).length, porcentaje: (pacientes.filter(p => (p.edad || 0) >= 40).length / stats.total) * 100 }
                ]}
                pagination={false}
              />
            </Card>
          ),
        },
        {
          key: '2',
          label: 'Distribución Geográfica',
          children: (
            <Card title="Pacientes por Ciudad">
              <Text>Mapa de distribución demográfica por ubicación geográfica:</Text>
              <Divider />
              {['La Paz', 'Cochabamba', 'Santa Cruz', 'Oruro', 'Potosí', 'Tarija', 'Beni', 'Pando', 'Chuquisaca'].map((ciudad) => {
                const count = pacientes.filter(p => p.ciudad?.toLowerCase().includes(ciudad.toLowerCase())).length;
                const percent = (count / stats.total) * 100;
                return (
                  <div key={ciudad} style={{ marginBottom: 16 }}>
                    <Row justify="space-between">
                      <Col><Text strong>{ciudad}</Text></Col>
                      <Col><Text>{count} pacientes ({percent.toFixed(1)}%)</Text></Col>
                    </Row>
                    <Progress percent={percent} strokeColor={token.colorPrimary} showInfo={false} />
                  </div>
                );
              })}
            </Card>
          ),
        },
        {
          key: '3',
          label: 'Grupos de Riesgo',
          children: (
            <Card title="Análisis de Poblaciones Vulnerables">
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="Identificación de Grupos Prioritarios"
                  description="Detección automática de pacientes que requieren atención especializada"
                  type="warning"
                  showIcon
                />

                <Card size="small" title="Adolescentes (< 20 años)">
                  <Statistic
                    value={pacientes.filter(p => (p.edad || 0) < 20).length}
                    suffix={`/ ${stats.total}`}
                    prefix={<UserOutlined />}
                  />
                  <Text type="secondary">Requieren seguimiento psicosocial</Text>
                </Card>

                <Card size="small" title="Gestantes Añosas (≥ 35 años)">
                  <Statistic
                    value={pacientes.filter(p => (p.edad || 0) >= 35 && p.embarazos_activos).length}
                    suffix="casos"
                    prefix={<WarningOutlined />}
                    valueStyle={{ color: token.colorError }}
                  />
                  <Text type="secondary">Mayor riesgo obstétrico</Text>
                </Card>

                <Card size="small" title="Multigestantes con Cesáreas Previas">
                  <Statistic
                    value={0}
                    suffix="identificadas"
                    prefix={<MedicineBoxOutlined />}
                  />
                  <Text type="secondary">Requieren evaluación quirúrgica especializada</Text>
                </Card>
              </Space>
            </Card>
          ),
        },
        {
          key: '4',
          label: 'Tendencias Temporales',
          children: (
            <Card title="Evolución de Registros">
              <Alert
                message="Análisis de Captación"
                description={`Se han registrado ${stats.nuevosMes} nuevos pacientes este mes. Tendencia: ${stats.nuevosMes > 10 ? 'CRECIENTE' : 'ESTABLE'}`}
                type={stats.nuevosMes > 10 ? 'success' : 'info'}
                showIcon
              />
              <Divider />
              <Row gutter={16}>
                {['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'].map((mes) => (
                  <Col span={6} key={mes}>
                    <Card size="small" style={{ textAlign: 'center', marginBottom: 8 }}>
                      <Statistic title={mes} value={0} valueStyle={{ fontSize: 18 }} />
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          ),
        },
      ]}
    />
  </Modal>
);

export default AnalisisDemograficoModal;
