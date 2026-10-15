import React from 'react';
import { Alert, Row, Col, Card, Typography, Button, Divider, List } from 'antd';
import { UserAddOutlined, MedicineBoxOutlined, PrinterOutlined, RightOutlined, VideoCameraOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const AyudaGuiasRapidas: React.FC = () => {
  const navigate = useNavigate();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  const handleKeyDown = (e: React.KeyboardEvent, path: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleNavigate(path);
    }
  };

  return (
    <div className="ayuda-page__seccion">
      <Alert
        message="Novedad: Versión 2.5"
        description="Ahora puede adjuntar archivos PDF directamente en la sección de Laboratorios."
        type="info"
        showIcon
        closable
        className="ayuda-page__novedad"
      />

      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card
            hoverable
            className="ayuda-page__guia"
            onClick={() => handleNavigate('/pacientes/nuevo')}
            tabIndex={0}
            onKeyDown={(e) => handleKeyDown(e, '/pacientes/nuevo')}
          >
            <span className="ayuda-page__guia-icono"><UserAddOutlined /></span>
            <Title level={4}>Registrar Nuevo Paciente</Title>
            <Paragraph type="secondary">Paso a paso para crear una ficha clínica desde cero, incluyendo antecedentes.</Paragraph>
            <Button type="link" className="ayuda-page__enlace">Ver tutorial <RightOutlined /></Button>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            className="ayuda-page__guia"
            onClick={() => handleNavigate('/controles')}
            tabIndex={0}
            onKeyDown={(e) => handleKeyDown(e, '/controles')}
          >
            <span className="ayuda-page__guia-icono"><MedicineBoxOutlined /></span>
            <Title level={4}>Control Prenatal</Title>
            <Paragraph type="secondary">Guía rápida para llenar el formulario de control y entender las curvas de crecimiento.</Paragraph>
            <Button type="link" className="ayuda-page__enlace">Ver tutorial <RightOutlined /></Button>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card
            hoverable
            className="ayuda-page__guia"
            onClick={() => handleNavigate('/reportes')}
            tabIndex={0}
            onKeyDown={(e) => handleKeyDown(e, '/reportes')}
          >
            <span className="ayuda-page__guia-icono"><PrinterOutlined /></span>
            <Title level={4}>Generar Reportes</Title>
            <Paragraph type="secondary">Cómo exportar estadísticas mensuales y listados de pacientes a Excel/PDF.</Paragraph>
            <Button type="link" className="ayuda-page__enlace">Ver tutorial <RightOutlined /></Button>
          </Card>
        </Col>
      </Row>

      <Divider orientation="left">Videos de Capacitación</Divider>
      <List
        grid={{ gutter: 16, xs: 1, sm: 1, md: 2, column: 2 }}
        dataSource={[
          { title: 'Introducción al Sistema HCGO', duration: '5:30 min' },
          { title: 'Módulo de Ecografías Avanzadas', duration: '12:15 min' },
          { title: 'Gestión de Agenda y Citas', duration: '8:45 min' },
          { title: 'Interpretación de Alertas Clínicas', duration: '6:20 min' }
        ]}
        renderItem={item => (
          <List.Item key={item.title}>
            <Card size="small">
              <List.Item.Meta
                avatar={<VideoCameraOutlined className="ayuda-page__video-icono" />}
                title={<span className="ayuda-page__titulo-enlace">{item.title}</span>}
                description={`Duración: ${item.duration}`}
              />
            </Card>
          </List.Item>
        )}
      />
    </div>
  );
};

export default AyudaGuiasRapidas;
