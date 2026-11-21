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
  SafetyOutlined,
  AimOutlined,
  BarChartOutlined,
  RiseOutlined,
  HistoryOutlined
} from '@ant-design/icons';
import './IndiceCalculadoras.css';

const { Title, Paragraph, Text } = Typography;

interface CalculadoraCard {
  id: string;
  titulo: string;
  descripcion: string;
  ruta: string;
  icono: React.ReactNode;
  tags: string[];
  lineas: number;
  graficas: number;
}

const calculadoras: CalculadoraCard[] = [
    {
      id: 'bishop',
      titulo: 'Score de Bishop',
      descripcion: 'Evaluación completa de maduración cervical con 5 componentes. Predice éxito de inducción del parto.',
      ruta: '/dashboard/calculadoras/bishop',
      icono: <MedicineBoxOutlined />,
      tags: ['Inducción', 'Cérvix', 'Parto'],
      lineas: 598,
      graficas: 4
    },
    {
      id: 'imc',
      titulo: 'IMC y Ganancia Ponderal',
      descripcion: 'Cálculo de IMC pregestacional y curvas de ganancia de peso según Atalah. Identifica riesgo nutricional.',
      ruta: '/dashboard/calculadoras/imc-ganancia',
      icono: <HeartOutlined />,
      tags: ['Nutrición', 'Atalah', 'Peso'],
      lineas: 650,
      graficas: 5
    },
    {
      id: 'preeclampsia',
      titulo: 'Riesgo de Preeclampsia',
      descripcion: 'Modelo Bayesiano FMF con biomarcadores (PlGF, sFlt-1, PAPP-A, MAP, UtA-PI). Ratio sFlt-1/PlGF.',
      ruta: '/dashboard/calculadoras/preeclampsia',
      icono: <WarningOutlined />,
      tags: ['FMF', 'Biomarcadores', 'Aspirina'],
      lineas: 683,
      graficas: 4
    },
    {
      id: 'crecimiento',
      titulo: 'Crecimiento Fetal',
      descripcion: '4 fórmulas Hadlock para EFW. Percentiles Intergrowth-21st. Detecta RCIU, PEG, GEG, macrosomía.',
      ruta: '/dashboard/calculadoras/crecimiento-fetal',
      icono: <LineChartOutlined />,
      tags: ['Hadlock', 'EFW', 'Biometría'],
      lineas: 647,
      graficas: 5
    },
    {
      id: 'cromosomico',
      titulo: 'Riesgo Cromosómico',
      descripcion: 'Screening T21/T18/T13 con NT, PAPP-A, βhCG libre. Modelo Bayesiano FMF. Cutoff 1:250.',
      ruta: '/dashboard/calculadoras/riesgo-cromosomico',
      icono: <ExperimentOutlined />,
      tags: ['Aneuploidías', 'NT', 'FMF'],
      lineas: 727,
      graficas: 5
    },
    {
      id: 'dosis',
      titulo: 'Dosis de Medicamentos',
      descripcion: '16 medicamentos obstétricos con ajuste renal (Cockcroft-Gault). FDA categories, contraindicaciones.',
      ruta: '/dashboard/calculadoras/dosis-medicamentos',
      icono: <MedicineBoxOutlined />,
      tags: ['Farmacología', 'CLCr', 'Seguridad'],
      lineas: 852,
      graficas: 4
    },
    {
      id: 'hemorragia',
      titulo: 'Hemorragia Obstétrica',
      descripcion: 'Protocolo 4 T\'s (Tono, Trauma, Tejido, Trombina). Shock Index. Protocolo Transfusión Masiva.',
      ruta: '/dashboard/calculadoras/hemorragia-obstetrica',
      icono: <ThunderboltOutlined />,
      tags: ['HPP', '4 T\'s', 'PTM'],
      lineas: 983,
      graficas: 5
    },
    {
      id: 'sufrimiento',
      titulo: 'Sufrimiento Fetal',
      descripcion: 'CTG ACOG (Cat I/II/III), Perfil Biofísico Manning (0-10), Doppler (AU, ACM, DV, CPR).',
      ruta: '/dashboard/calculadoras/sufrimiento-fetal',
      icono: <SafetyOutlined />,
      tags: ['CTG', 'BPP', 'Doppler'],
      lineas: 1033,
      graficas: 5
    }
  ];

const IndiceCalculadoras: React.FC = () => {
  const navigate = useNavigate();

  const handleCardClick = (ruta: string) => {
    navigate(ruta);
  };

  return (
    <div className="indice-calculadoras-page">
      <div className="indice-calc__cabecera">
        <Title level={2} className="indice-calc__titulo">
          <CalculatorOutlined className="indice-calc__titulo-icono" />
          Panel de Calculadoras Médicas Avanzadas
        </Title>
        <Paragraph className="indice-calc__descripcion">
          Herramientas clínicas con cálculos validados, gráficas interactivas Recharts y recomendaciones basadas en evidencia.
          Total: <strong>{calculadoras.reduce((acc, c) => acc + c.lineas, 0).toLocaleString()} líneas de código</strong> | <strong>{calculadoras.reduce((acc, c) => acc + c.graficas, 0)} gráficas</strong>
        </Paragraph>
      </div>

      <Row gutter={[16, 16]}>
        {calculadoras.map((calc) => (
          <Col xs={24} sm={12} lg={8} xl={6} key={calc.id}>
            <Card
              hoverable
              className="calculadora-card"
              onClick={() => handleCardClick(calc.ruta)}
              actions={[
                <Button
                  key="abrir"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCardClick(calc.ruta);
                  }}
                >
                  Abrir
                </Button>
              ]}
            >
              <div className="card-icon-container">{calc.icono}</div>
              <Card.Meta
                title={calc.titulo}
                description={
                  <>
                    <Paragraph className="indice-calc__texto">
                      {calc.descripcion}
                    </Paragraph>
                    <div className="indice-calc__etiquetas">
                      {calc.tags.map((tag) => (
                        <Tag key={tag}>{tag}</Tag>
                      ))}
                    </div>
                    <Text type="secondary" className="indice-calc__metricas">
                      {calc.graficas} gráficas · {calc.lineas} líneas
                    </Text>
                  </>
                }
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        className="indice-calc__caracteristicas"
        title="Características de las Calculadoras"
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <div className="indice-calc__rasgo">
              <Paragraph strong className="indice-calc__rasgo-titulo">
                <AimOutlined /> Cálculos Precisos
              </Paragraph>
              <Paragraph type="secondary" className="indice-calc__rasgo-texto">
                Fórmulas médicas validadas (FMF, Hadlock, ACOG, Atalah)
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="indice-calc__rasgo">
              <Paragraph strong className="indice-calc__rasgo-titulo">
                <BarChartOutlined /> Gráficas Interactivas
              </Paragraph>
              <Paragraph type="secondary" className="indice-calc__rasgo-texto">
                36 visualizaciones Recharts (BarChart, LineChart, PieChart)
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="indice-calc__rasgo">
              <Paragraph strong className="indice-calc__rasgo-titulo">
                <RiseOutlined /> Estadísticas Real-Time
              </Paragraph>
              <Paragraph type="secondary" className="indice-calc__rasgo-texto">
                4+ métricas por calculadora con interpretaciones
              </Paragraph>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="indice-calc__rasgo">
              <Paragraph strong className="indice-calc__rasgo-titulo">
                <HistoryOutlined /> Historial
              </Paragraph>
              <Paragraph type="secondary" className="indice-calc__rasgo-texto">
                Tabla de evaluaciones previas con tendencias
              </Paragraph>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default IndiceCalculadoras;
