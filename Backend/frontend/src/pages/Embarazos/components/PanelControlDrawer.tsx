import React from 'react';
import { Drawer, Row, Col, Card, Space, Statistic, Progress, Typography, Divider, List, Button } from 'antd';
import {
  RiseOutlined, CheckCircleOutlined, PlusOutlined, CalendarOutlined,
  FileExcelOutlined, PrinterOutlined, SettingOutlined, QuestionCircleOutlined,
  BookOutlined, SafetyCertificateOutlined, DatabaseOutlined, TeamOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { EmbarazoResumido } from '../embarazosReducer';

const { Text } = Typography;

const plusOutlinedIcon9 = <PlusOutlined />;
const calendarOutlinedIcon8 = <CalendarOutlined />;
const fileExcelIcon = <FileExcelOutlined />;
const printerOutlinedIcon5 = <PrinterOutlined />;
const settingOutlinedIcon2 = <SettingOutlined />;
const questionCircleOutlinedIcon3 = <QuestionCircleOutlined />;

interface PanelControlDrawerProps {
  visible: boolean;
  onClose: () => void;
  /** Los 5 partos más cercanos (30 días), calculados en el servidor sobre todos los activos. */
  proximosPartos: EmbarazoResumido[];
  /** Trimestres de los embarazos ACTIVOS, contados en el servidor (no sobre una página). */
  stats: { primerTrimestre: number; segundoTrimestre: number; tercerTrimestre: number };
  canAdd: (perm: string) => boolean;
  handleOpenCreate: () => void;
}

const PanelControlDrawer: React.FC<PanelControlDrawerProps> = ({
  visible, onClose, proximosPartos, stats, canAdd, handleOpenCreate,
}) => (
  <Drawer
    title="Panel de Control Obstétrico"
    placement="bottom"
    height="80%"
    open={visible}
    onClose={onClose}
    closable={true}
  >
    <Row gutter={[24, 24]}>
      <Col span={8}>
        <Card title="Indicadores Clave (KPI)" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Statistic title="Tasa de Captación Temprana" value={78} suffix="%" prefix={<RiseOutlined />} />
            <Progress percent={78} status="active" />
            <Text type="secondary">Meta MSP: ≥ 80%</Text>

            <Divider />

            <Statistic title="Promedio Controles por Embarazo" value={6.4} prefix={<CheckCircleOutlined />} />
            <Progress percent={(6.4 / 8) * 100} status="active" strokeColor="#52c41a" />
            <Text type="secondary">Meta MSP: ≥ 5 controles</Text>

            <Divider />

            <Statistic title="Tasa de Complicaciones" value={12} suffix="%" valueStyle={{ color: '#cf1322' }} />
            <Progress percent={12} status="exception" />
            <Text type="secondary">Objetivo: {'<'} 15%</Text>
          </Space>
        </Card>
      </Col>

      <Col span={8}>
        <Card title="Análisis Temporal" size="small">
          <Text strong>Embarazos por Trimestre Actual:</Text>
          <div style={{ marginTop: 16 }}>
            <Row gutter={8}>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center', background: '#e6f7ff' }}>
                  <Statistic title="1T" value={stats.primerTrimestre} valueStyle={{ fontSize: 24 }} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center', background: '#f0f5ff' }}>
                  <Statistic title="2T" value={stats.segundoTrimestre} valueStyle={{ fontSize: 24 }} />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small" style={{ textAlign: 'center', background: '#fff7e6' }}>
                  <Statistic title="3T" value={stats.tercerTrimestre} valueStyle={{ fontSize: 24 }} />
                </Card>
              </Col>
            </Row>
          </div>

          <Divider />

          <Text strong>Próximos Partos Estimados (30 días):</Text>
          <List
            size="small"
            dataSource={proximosPartos}
            renderItem={(item: EmbarazoResumido) => (
              <List.Item key={`fpp-${item.id}`}>
                <Text>{item.paciente_nombre}</Text>
                <Text type="secondary">{dayjs(item.fecha_probable_parto).format('DD/MM')}</Text>
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col span={8}>
        <Card title="Acciones Rápidas" size="small">
          <Space direction="vertical" style={{ width: '100%' }}>
            {canAdd('embarazo') && (
              <Button icon={plusOutlinedIcon9} type="primary" block onClick={handleOpenCreate}>
                Nuevo Embarazo
              </Button>
            )}
            <Button icon={calendarOutlinedIcon8} block>
              Programar Controles Masivos
            </Button>
            <Button icon={fileExcelIcon} block>
              Exportar Base de Datos
            </Button>
            <Button icon={printerOutlinedIcon5} block>
              Imprimir Listado del Día
            </Button>
            <Divider />
            <Button icon={settingOutlinedIcon2} block>
              Configuración de Alertas
            </Button>
            <Button icon={questionCircleOutlinedIcon3} block>
              Ayuda y Manuales
            </Button>
          </Space>
        </Card>
      </Col>
    </Row>

    <Divider orientation="left">Recursos Adicionales</Divider>

    <Row gutter={[16, 16]}>
      <Col span={6}>
        <Card size="small" hoverable style={{ textAlign: 'center' }}>
          <BookOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
          <div><Text strong>Protocolos MSP</Text></div>
          <div><Text type="secondary" style={{ fontSize: 12 }}>Guías Clínicas</Text></div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" hoverable style={{ textAlign: 'center' }}>
          <SafetyCertificateOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
          <div><Text strong>Normativas OMS</Text></div>
          <div><Text type="secondary" style={{ fontSize: 12 }}>Referencias Internacionales</Text></div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" hoverable style={{ textAlign: 'center' }}>
          <DatabaseOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 8 }} />
          <div><Text strong>Base de Datos</Text></div>
          <div><Text type="secondary" style={{ fontSize: 12 }}>Estadísticas Históricas</Text></div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" hoverable style={{ textAlign: 'center' }}>
          <TeamOutlined style={{ fontSize: 32, color: '#fa8c16', marginBottom: 8 }} />
          <div><Text strong>Equipo Médico</Text></div>
          <div><Text type="secondary" style={{ fontSize: 12 }}>Contactos y Turnos</Text></div>
        </Card>
      </Col>
    </Row>
  </Drawer>
);

export default PanelControlDrawer;
