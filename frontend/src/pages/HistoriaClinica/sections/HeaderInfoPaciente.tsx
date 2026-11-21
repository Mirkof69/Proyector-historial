import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Avatar, Tag, Space, Button, Dropdown, Typography } from 'antd';
import {
  UserOutlined, CalendarOutlined, PhoneOutlined, PlusOutlined, CalculatorOutlined,
  FilePdfOutlined, PrinterOutlined, WarningOutlined, SafetyCertificateOutlined,
  HistoryOutlined, LineChartOutlined, EditOutlined, EllipsisOutlined,
} from '@ant-design/icons';
import { Paciente, Embarazo } from '../types';
import { verticalDivider } from '../historiaClinicaHelpers';

const { Title, Text } = Typography;

interface HeaderInfoPacienteProps {
  paciente: Paciente | null;
  embarazoActivo: Embarazo | null;
  pacienteId: string | undefined;
  navigate: ReturnType<typeof useNavigate>;
  setDrawerCalculadoraVisible: (v: boolean) => void;
  setModalExportarVisible: (v: boolean) => void;
  setModalRiesgoVisible: (v: boolean) => void;
  setModalProtocolosVisible: (v: boolean) => void;
  setDrawerTimelineVisible: (v: boolean) => void;
  setModalComparacionVisible: (v: boolean) => void;
  setDrawerAlertasVisible: (v: boolean) => void;
}
const HeaderInfoPaciente: React.FC<HeaderInfoPacienteProps> = React.memo(({
  paciente, embarazoActivo, pacienteId, navigate,
  setDrawerCalculadoraVisible, setModalExportarVisible, setModalRiesgoVisible,
  setModalProtocolosVisible, setDrawerTimelineVisible, setModalComparacionVisible,
  setDrawerAlertasVisible,
}) => (
  <Card className="header-paciente">
    <Row align="middle" gutter={[24, 16]}>
      <Col flex="none">
        <Avatar size={64} icon={<UserOutlined />} src={paciente?.foto_perfil} className="header-paciente__avatar" />
      </Col>
      <Col flex="auto" className="header-paciente__datos">
        <Title level={2} className="header-paciente__nombre">
          {paciente?.nombre} {paciente?.apellido_paterno || paciente?.apellidos || ''}
          <Tag color={paciente?.activo ? 'success' : 'error'} className="header-paciente__tag-estado">
            {paciente?.activo ? 'ACTIVA' : 'INACTIVA'}
          </Tag>
        </Title>
        <Space split={verticalDivider} wrap className="header-paciente__info">
          <Text><CalendarOutlined /> {paciente?.edad} años</Text>
          <Text>CI: <span className="texto-mono">{paciente?.ci}</span></Text>
          <Text>GS: <Tag>{(paciente as any)?.grupo_sanguineo || paciente?.tipo_sangre} {paciente?.factor_rh}</Tag></Text>
          <Text><PhoneOutlined /> {paciente?.telefono}</Text>
        </Space>
        <div className="header-paciente__alergias">
          <Text type="secondary">Alergias: </Text>
          {paciente?.alergias ? <Tag color="error">{paciente.alergias}</Tag> : <Tag>Niega</Tag>}
        </div>
      </Col>
      <Col>
        <Space direction="vertical" align="end" className="header-paciente__actions">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/dashboard/controles/nuevo?embarazo=${embarazoActivo?.id}`)} disabled={!embarazoActivo}>
            Nuevo Control
          </Button>
          <Dropdown menu={{
            items: [
              { key: 'calc', label: 'Calculadora Obstétrica', icon: <CalculatorOutlined />, onClick: () => setDrawerCalculadoraVisible(true) },
              { key: 'print', label: 'Imprimir Historia', icon: <FilePdfOutlined />, onClick: () => window.print() },
              { key: 'export', label: 'Exportar PDF', icon: <PrinterOutlined />, onClick: () => setModalExportarVisible(true) },
              { key: 'riesgo', label: 'Recalificar Riesgo', icon: <WarningOutlined />, onClick: () => setModalRiesgoVisible(true) },
              { type: 'divider' },
              { key: 'protocols', label: 'Ver Protocolos', icon: <SafetyCertificateOutlined />, onClick: () => setModalProtocolosVisible(true) },
              { key: 'timeline', label: 'Línea de Tiempo', icon: <HistoryOutlined />, onClick: () => setDrawerTimelineVisible(true) },
              { key: 'compare', label: 'Comparar Datos', icon: <LineChartOutlined />, onClick: () => setModalComparacionVisible(true) },
              { key: 'alerts', label: 'Panel de Alertas', icon: <WarningOutlined />, onClick: () => setDrawerAlertasVisible(true) },
              { type: 'divider' },
              { key: 'edit', label: 'Editar Paciente', icon: <EditOutlined />, onClick: () => navigate(`/dashboard/pacientes/${pacienteId}/editar`) },
            ]
          }}>
            <Button>Acciones <EllipsisOutlined /></Button>
          </Dropdown>
        </Space>
      </Col>
    </Row>
  </Card>
));

export default HeaderInfoPaciente;
