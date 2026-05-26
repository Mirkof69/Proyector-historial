import React from 'react';
import { Card, Row, Col, Typography, Tag, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import {
  CalculatorOutlined,
  HeartOutlined,
  MedicineBoxOutlined,
  WarningOutlined,
  ExperimentOutlined,
  ThunderboltOutlined,
  LineChartOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import './IndiceCalculadoras.css';

const { Title, Paragraph } = Typography;

interface CalculadoraCard {
  id: string;
  titulo: string;
  descripcion: string;
  ruta: string;
  icono: React.ReactNode;
  color: string;
  tags: string[];
  lineas: number;
  graficas: number;
}

const IndiceCalculadoras: React.FC = () => {
  const navigate = useNavigate();

  const calculadoras: CalculadoraCard[] = [
    {
      id: 'bishop',
      titulo: 'Score de Bishop',
      descripcion: 'Evaluación completa de maduración cervical con 5 componentes. Predice éxito de inducción del parto.',
      ruta: '/dashboard/calculadoras/bishop',
      icono: <MedicineBoxOutlined style={{ fontSize: 48 }} />,
      color: '#1890ff',
      tags: ['Inducción', 'Cérvix', 'Parto'],
      lineas: 598,
      graficas: 4
    },
    {
      id: 'imc',
      titulo: 'IMC y Ganancia Ponderal',
      descripcion: 'Cálculo de IMC pregestacional y curvas de ganancia de peso según Atalah. Identifica riesgo nutricional.',
      ruta: '/dashboard/calculadoras/imc-ganancia',
      icono: <HeartOutlined style={{ fontSize: 48 }} />,
      color: '#52c41a',
      tags: ['Nutrición', 'Atalah', 'Peso'],
      lineas: 650,
      graficas: 5
    },
    {
      id: 'preeclampsia',
      titulo: 'Riesgo de Preeclampsia',
      descripcion: 'Modelo Bayesiano FMF con biomarcadores (PlGF, sFlt-1, PAPP-A, MAP, UtA-PI). Ratio sFlt-1/PlGF.',
      ruta: '/dashboard/calculadoras/preeclampsia',
      icono: <WarningOutlined style={{ fontSize: 48 }} />,
      color: '#ff4d4f',
      tags: ['FMF', 'Biomarcadores', 'Aspirina'],
      lineas: 683,
      graficas: 4
    },
    {
      id: 'crecimiento',
      titulo: 'Crecimiento Fetal',
      descripcion: '4 fórmulas Hadlock para EFW. Percentiles Intergrowth-21st. Detecta RCIU, PEG, GEG, macrosomía.',
      ruta: '/dashboard/calculadoras/crecimiento-fetal',
      icono: <LineChartOutlined style={{ fontSize: 48 }} />,
      color: '#722ed1',
      tags: ['Hadlock', 'EFW', 'Biometría'],
      lineas: 647,
      graficas: 5
    },
    {
      id: 'cromosomico',
      titulo: 'Riesgo Cromosómico',
      descripcion: 'Screening T21/T18/T13 con NT, PAPP-A, βhCG libre. Modelo Bayesiano FMF. Cutoff 1:250.',
      ruta: '/dashboard/calculadoras/riesgo-cromosomico',
      icono: <ExperimentOutlined style={{ fontSize: 48 }} />,
      color: '#722ed1',
      tags: ['Aneuploidías', 'NT', 'FMF'],
      lineas: 727,
      graficas: 5
    },
    {
      id: 'dosis',
      titulo: 'Dosis de Medicamentos',
      descripcion: '16 medicamentos obstétricos con ajuste renal (Cockcroft-Gault). FDA categories, contraindicaciones.',
      ruta: '/dashboard/calculadoras/dosis-medicamentos',
      icono: <MedicineBoxOutlined style={{ fontSize: 48 }} />,
      color: '#13c2c2',
      tags: ['Farmacología', 'CLCr', 'Seguridad'],
      lineas: 852,
      graficas: 4
    },
    {
      id: 'hemorragia',
      titulo: 'Hemorragia Obstétrica',
      descripcion: 'Protocolo 4 T\'s (Tono, Trauma, Tejido, Trombina). Shock Index. Protocolo Transfusión Masiva.',
      ruta: '/dashboard/calculadoras/hemorragia-obstetrica',
      icono: <ThunderboltOutlined style={{ fontSize: 48 }} />,
      color: '#ff4d4f',
      tags: ['HPP', '4 T\'s', 'PTM'],
      lineas: 983,
      graficas: 5
    },
    {
      id: 'sufrimiento',
      titulo: 'Sufrimiento Fetal',
      descripcion: 'CTG ACOG (Cat I/II/III), Perfil Biofísico Manning (0-10), Doppler (AU, ACM, DV, CPR).',
      ruta: '/dashboard/calculadoras/sufrimiento-fetal',
      icono: <SafetyOutlined style={{ fontSize: 48 }} />,
      color: '#eb2f96',
      tags: ['CTG', 'BPP', 'Doppler'],
      lineas: 1033,
      graficas: 5
    }
  ];

  const handleCardClick = (ruta: string) => {
    navigate(ruta);
  };

  return (
    <div className="indice-calculadoras-page">
      <div className="header-section">
        <Title level={2}>
          <CalculatorOutlined style={{ marginRight: 12, color: '#1890ff' }} />
          Panel de Calculadoras Médicas Avanzadas
        </Title>
        <Paragraph style={{ fontSize: 16, color: 'rgba(0, 0, 0, 0.65)' }}>
          Herramientas clínicas con cálculos validados, gráficas interactivas Recharts y recomendaciones basadas en evidencia.
          Total: <strong>{calculadoras.reduce((acc, c) => acc + c.lineas, 0).toLocaleString()} líneas de código</strong> | <strong>{calculadoras.reduce((acc, c) => acc + c.graficas, 0)} gráficas</strong>
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {calculadoras.map((calc) => (
          <Col xs={24} sm={12} lg={8} xl={6} key={calc.id}>
            <Card
              hoverable
              className="calculadora-card"
              style={{ borderTop: `4px solid ${calc.color}` }}
              onClick={() => handleCardClick(calc.ruta)}
              cover={
                <div
                  className="card-icon-container"
                  style={{ backgroundColor: `${calc.color}20` }}
                >
                  <div style={{ color: calc.color }}>
                    {calc.icono}
                  </div>
                </div>
              }
              actions={[
                <Button
                  key="abrir"
                  type="primary"
                  style={{ backgroundColor: calc.color, borderColor: calc.color }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCardClick(calc.ruta);
                  }}
                >
                  Abrir
                </Button>
              ]}
            >
              <Card.Meta
                title={
                  <div style={{ fontSize: 18, fontWeight: 'bold' }}>
                    {calc.titulo}
                  </div>
                }
                description={
                  <>
                    <Paragraph
                      style={{
                        fontSize: 14,
                        color: 'rgba(0, 0, 0, 0.65)',
                        marginBottom: 12,
                        minHeight: 60
                      }}
                    >
                      {calc.descripcion}
                    </Paragraph>
                    <div style={{ marginBottom: 12 }}>
                      {calc.tags.map((tag) => (
                        <Tag key={tag} color={calc.color} style={{ marginBottom: 4 }}>
                          {tag}
                        </Tag>
                      ))}
                    </div>
                    <div style={{ fontSize: 12, color: 'rgba(0, 0, 0, 0.45)' }}>
                      📊 {calc.graficas} gráficas · 💻 {calc.lineas} líneas
                    </div>
                  </>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ marginTop: 32 }}
        title="Características de las Calculadoras"
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Paragraph strong style={{ marginBottom: 4 }}>
                🎯 Cálculos Precisos
              </Paragraph>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                Fórmulas médicas validadas (FMF, Hadlock, ACOG, Atalah)
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Paragraph strong style={{ marginBottom: 4 }}>
                📊 Gráficas Interactivas
              </Paragraph>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                36 visualizaciones Recharts (BarChart, LineChart, PieChart)
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Paragraph strong style={{ marginBottom: 4 }}>
                📈 Estadísticas Real-Time
              </Paragraph>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                4+ métricas por calculadora con interpretaciones
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Paragraph strong style={{ marginBottom: 4 }}>
                📋 Historial
              </Paragraph>
              <Paragraph type="secondary" style={{ fontSize: 13 }}>
                Tabla de evaluaciones previas con tendencias
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default IndiceCalculadoras;
