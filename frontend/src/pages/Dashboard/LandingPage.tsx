/**
 * =============================================================================
 * LANDING PAGE - FETAL MEDICAL FOUNDATION
 * =============================================================================
 * Página de bienvenida profesional con información del sistema
 * Diseño de dos columnas con hero, características y calculadoras
 * =============================================================================
 */

import React from 'react';
import { Layout } from 'antd';
import {
  HeartOutlined,
  SafetyOutlined,
  BarChartOutlined,
  MedicineBoxOutlined,
  UserOutlined,
  CalendarOutlined,
  FundProjectionScreenOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  FileProtectOutlined,
  CloudServerOutlined,
  LineChartOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { FRONTEND_ROUTES } from '../../config/routes';
import LandingHeader from './components/LandingHeader';
import HeroSection from './components/HeroSection';
import FeaturesSection from './components/FeaturesSection';
import CalculadorasSection from './components/CalculadorasSection';
import BeneficiosSection from './components/BeneficiosSection';
import StatsSection from './components/StatsSection';
import FinalCTA from './components/FinalCTA';
import LandingFooter from './components/LandingFooter';
import './LandingPage.css';

const { Content } = Layout;

const features = [
  {
    icon: <HeartOutlined />,
    title: 'Seguimiento Prenatal Completo',
    description:
      'Control integral de embarazos con alertas médicas automáticas, evaluación de riesgos en tiempo real y seguimiento continuo de la salud materno-fetal.',
  },
  {
    icon: <BarChartOutlined />,
    title: '15+ Calculadoras FMF',
    description:
      'Algoritmos validados científicamente de la Fetal Medicine Foundation para predicción de preeclampsia, trisomías, restricción del crecimiento y más.',
  },
  {
    icon: <SafetyOutlined />,
    title: 'Alertas Inteligentes',
    description:
      'Sistema automático de detección de signos de alarma con clasificación por severidad crítica, advertencia e información, con recomendaciones específicas.',
  },
  {
    icon: <MedicineBoxOutlined />,
    title: 'Historia Clínica Digital',
    description:
      'Registro electrónico completo de pacientes, embarazos, controles prenatales, ecografías y laboratorios con acceso instantáneo desde cualquier dispositivo.',
  },
  {
    icon: <FundProjectionScreenOutlined />,
    title: 'Dashboard en Tiempo Real',
    description:
      'Estadísticas y métricas actualizadas automáticamente con visualizaciones interactivas, gráficas de evolución y reportes para toma de decisiones informadas.',
  },
  {
    icon: <TeamOutlined />,
    title: 'Gestión Colaborativa',
    description:
      'Control de usuarios, roles y permisos diferenciados para médicos, enfermeros y personal administrativo con historial compartido y trazabilidad completa.',
  },
  {
    icon: <UserOutlined />,
    title: 'Gestión de Pacientes',
    description:
      'Sistema completo de registro y seguimiento de pacientes con historial médico integrado, búsqueda avanzada y perfiles detallados para un manejo personalizado.',
  },
  {
    icon: <CalendarOutlined />,
    title: 'Agenda de Citas Inteligente',
    description:
      'Calendario interactivo con disponibilidad en tiempo real, recordatorios automáticos, gestión de horarios y vista mensual completa para optimizar la atención.',
  },
];

const calculadoras = [
  { nombre: 'Predicción de Preeclampsia', categoria: 'Riesgo Materno' },
  { nombre: 'Screening de Trisomías (21, 18, 13)', categoria: 'Genética' },
  { nombre: 'Predicción de SGA (Pequeño para Edad Gestacional)', categoria: 'Crecimiento Fetal' },
  { nombre: 'Diabetes Gestacional', categoria: 'Riesgo Metabólico' },
  { nombre: 'Parto Pretérmino', categoria: 'Riesgo Obstétrico' },
  { nombre: 'Peso Fetal Estimado', categoria: 'Biometría' },
  { nombre: 'Curvas de Crecimiento Fetal', categoria: 'Seguimiento' },
  { nombre: 'Translucencia Nucal', categoria: 'Primer Trimestre' },
  { nombre: 'Doppler Fetal', categoria: 'Hemodinámica' },
  { nombre: 'IP Arterias Uterinas', categoria: 'Doppler Materno' },
  { nombre: 'Presión Arterial Media', categoria: 'Monitoreo' },
  { nombre: 'Biomarcadores (sFlt-1/PlGF)', categoria: 'Laboratorio' },
  { nombre: 'Índice de Líquido Amniótico', categoria: 'Bienestar Fetal' },
  { nombre: 'Test No Estresante (NST)', categoria: 'Monitoreo Fetal' },
  { nombre: 'Score de Bishop', categoria: 'Inducción' },
];

const beneficios = [
  { icon: <ClockCircleOutlined />, titulo: 'Acceso 24/7', descripcion: 'Disponible en cualquier momento desde cualquier lugar' },
  { icon: <FileProtectOutlined />, titulo: 'Seguridad Garantizada', descripcion: 'Cumplimiento de Ley 3871 y encriptación de datos' },
  { icon: <CloudServerOutlined />, titulo: 'Respaldo Automático', descripcion: 'Backup diario de toda la información médica' },
  { icon: <LineChartOutlined />, titulo: 'Reportes Detallados', descripcion: 'Estadísticas y análisis para gestión clínica' },
];

const scrollToSection = (sectionId: string) => {
  const element = document.getElementById(sectionId);
  if (element) element.scrollIntoView({ behavior: 'smooth' });
};

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleLogin = () => navigate(FRONTEND_ROUTES.LOGIN);

  return (
    <Layout className="landing-page">
      <LandingHeader onLogin={handleLogin} onScrollToSection={scrollToSection} />
      <Content>
        <HeroSection onLogin={handleLogin} onScrollToFeatures={() => scrollToSection('features')} />
        <FeaturesSection features={features} />
        <CalculadorasSection calculadoras={calculadoras} onLogin={handleLogin} />
        <BeneficiosSection beneficios={beneficios} />
        <StatsSection />
        <FinalCTA onLogin={handleLogin} />
      </Content>
      <LandingFooter />
    </Layout>
  );
};

export default LandingPage;
