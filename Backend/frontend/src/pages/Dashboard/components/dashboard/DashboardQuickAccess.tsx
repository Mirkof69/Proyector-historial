import React from 'react';
import { Row, Col, Card, Button } from 'antd';
import { UserOutlined, MedicineBoxOutlined, CalendarOutlined, FileTextOutlined, CalculatorOutlined, TeamOutlined, RobotOutlined } from '@ant-design/icons';

interface DashboardQuickAccessProps {
  showQuickAccess: (cardTitle: string) => boolean;
  onNavigate: (path: string, cardTitle: string) => void;
}

const DashboardQuickAccess: React.FC<DashboardQuickAccessProps> = ({ showQuickAccess, onNavigate }) => (
  <Row gutter={[16, 16]}>
    <Col span={24}>
      <Card title="Accesos Rápidos" className="shadow-card">
        <Row gutter={[16, 16]}>
          {showQuickAccess('Pacientes') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<UserOutlined />} onClick={() => onNavigate('/dashboard/pacientes', 'Pacientes')}>Pacientes</Button>
            </Col>
          )}
          {showQuickAccess('Controles') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<MedicineBoxOutlined />} onClick={() => onNavigate('/dashboard/controles', 'Controles')}>Controles</Button>
            </Col>
          )}
          {showQuickAccess('Agenda de Citas') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<CalendarOutlined />} onClick={() => onNavigate('/dashboard/citas', 'Agenda de Citas')}>Agenda</Button>
            </Col>
          )}
          {showQuickAccess('Reportes') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<FileTextOutlined />} onClick={() => onNavigate('/dashboard/reportes', 'Reportes')}>Reportes</Button>
            </Col>
          )}
          {showQuickAccess('Calculadoras') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<CalculatorOutlined />} onClick={() => onNavigate('/dashboard/calculadoras', 'Calculadoras')}>Calc. Médica</Button>
            </Col>
          )}
          {showQuickAccess('Gestión de Usuarios') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<TeamOutlined />} onClick={() => onNavigate('/dashboard/usuarios', 'Gestión de Usuarios')}>Personal</Button>
            </Col>
          )}
          {showQuickAccess('Triaje') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<MedicineBoxOutlined />} onClick={() => onNavigate('/dashboard/triaje', 'Triaje')}>Triaje</Button>
            </Col>
          )}
          {showQuickAccess('Vacunas') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<MedicineBoxOutlined />} onClick={() => onNavigate('/dashboard/vacunas', 'Vacunas')}>Vacunas</Button>
            </Col>
          )}
          {showQuickAccess('Notas de evolución') && (
            <Col span={6} xs={12} sm={6}>
              <Button block size="large" className="btn-quick" icon={<FileTextOutlined />} onClick={() => onNavigate('/dashboard/notas-evolucion', 'Notas de evolución')}>Notas de evolución</Button>
            </Col>
          )}
          <Col span={6} xs={12} sm={6}>
            <Button block size="large" className="btn-quick" icon={<RobotOutlined />} onClick={() => onNavigate('/ia-asistente', 'IA Assistant')}>IA Assistant</Button>
          </Col>
        </Row>
      </Card>
    </Col>
  </Row>
);

export default DashboardQuickAccess;
