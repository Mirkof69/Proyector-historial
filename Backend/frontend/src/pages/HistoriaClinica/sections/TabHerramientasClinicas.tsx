import React from 'react';
import { Row, Col, Card, Button, Divider, Typography, Form, Input, Select, DatePicker } from 'antd';
import {
  CalculatorOutlined, LineChartOutlined, ExperimentOutlined, ClockCircleOutlined,
  WomanOutlined, DownloadOutlined,
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { useAntdApp } from '../../../hooks/useMessage';
import { Laboratorio } from '../types';

const { Text } = Typography;
const { Option } = Select;

interface TabHerramientasClinicasProps {
  handleCalcularRiesgo: () => void;
  handleCalcularIMCGanancia: () => void;
  handleVerTendenciasLaboratorio: () => void;
  handleGenerarRecordatorios: () => void;
  handleCalcularPesoFetal: (dbt: number, ca: number, lf: number) => void;
  setModalExportarVisible: (v: boolean) => void;
  laboratorios: Laboratorio[];
  calcularEG: (fum: string) => { semanas: number; dias: number; texto: string };
  calcularFPP: (fum: string) => string;
  interpretarNST: (fcf: number, acel: number, decel: number, variab: 'AUSENTE' | 'MINIMA' | 'MODERADA' | 'MARCADA') => any;
  notification: any;
}
const TabHerramientasClinicas: React.FC<TabHerramientasClinicasProps> = ({
  handleCalcularRiesgo, handleCalcularIMCGanancia, handleVerTendenciasLaboratorio,
  handleGenerarRecordatorios, handleCalcularPesoFetal, setModalExportarVisible, laboratorios,
  calcularEG, calcularFPP, interpretarNST, notification
}) => {
  const { modal, message } = useAntdApp();
  return (
  <div>
    <Row gutter={[16, 16]}>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Calculadora de Riesgo" extra={<CalculatorOutlined />}
          actions={[<Button key="calc" type="primary" block onClick={handleCalcularRiesgo}>Evaluar Riesgo Preeclampsia</Button>]}>
          <p>Evalúa el riesgo de preeclampsia basado en factores clínicos y antecedentes.</p>
          <Divider /><Text type="secondary">Factores considerados:</Text>
          <ul style={{ fontSize: 12 }}><li>Edad materna</li><li>IMC</li><li>Presión arterial</li><li>Antecedentes médicos</li></ul>
        </Card>
      </Col>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Análisis de Peso e IMC" extra={<LineChartOutlined />}
          actions={[<Button key="calc-imc" type="primary" block onClick={handleCalcularIMCGanancia}>Calcular IMC y Ganancia</Button>]}>
          <p>Calcula el IMC y analiza la ganancia de peso según recomendaciones OMS.</p>
          <Divider /><Text type="secondary">Incluye:</Text>
          <ul style={{ fontSize: 12 }}><li>IMC pre-gestacional</li><li>IMC actual</li><li>Ganancia de peso recomendada</li><li>Comparación con valores reales</li></ul>
        </Card>
      </Col>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Tendencias de Laboratorio" extra={<ExperimentOutlined />}
          actions={[<Button key="tendencias" type="primary" block onClick={handleVerTendenciasLaboratorio} disabled={laboratorios.length < 2}>Ver Tendencias</Button>]}>
          <p>Analiza la evolución temporal de los resultados de laboratorio.</p>
          <Divider /><Text type="secondary">Muestra:</Text>
          <ul style={{ fontSize: 12 }}><li>Gráficas de evolución</li><li>Tendencia (mejorando/empeorando)</li><li>Valores de referencia</li></ul>
        </Card>
      </Col>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Recordatorios Clínicos" extra={<ClockCircleOutlined />}
          actions={[<Button key="recordatorios" type="primary" block onClick={handleGenerarRecordatorios}>Generar Recordatorios</Button>]}>
          <p>Genera recordatorios automáticos basados en protocolos de atención prenatal.</p>
          <Divider /><Text type="secondary">Incluye:</Text>
          <ul style={{ fontSize: 12 }}><li>Próximos controles</li><li>Vacunas pendientes</li><li>Exámenes de protocolo</li><li>Seguimiento de tratamientos</li></ul>
        </Card>
      </Col>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Peso Fetal Estimado" extra={<WomanOutlined />}
          actions={[<Button key="peso-fetal" type="primary" block onClick={() => {
            modal.info({
              title: 'Calculadora de Peso Fetal (Hadlock)',
              content: (
                <Form layout="vertical" onFinish={(values) => {
                  handleCalcularPesoFetal(values.dbt, values.ca, values.lf);
                }}>
                  <Form.Item name="dbt" label="Diámetro Biparietal (mm)" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 85" /></Form.Item>
                  <Form.Item name="ca" label="Circunferencia Abdominal (mm)" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 280" /></Form.Item>
                  <Form.Item name="lf" label="Longitud Femoral (mm)" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 65" /></Form.Item>
                  <Button type="primary" htmlType="submit" block>Calcular Peso</Button>
                </Form>
              )
            });
          }}>Calcular Peso Fetal</Button>]}>
          <p>Estima el peso fetal usando la fórmula de Hadlock basada en biometría ecográfica.</p>
          <Divider /><Text type="secondary">Requiere:</Text>
          <ul style={{ fontSize: 12 }}><li>Diámetro biparietal</li><li>Circunferencia abdominal</li><li>Longitud femoral</li></ul>
        </Card>
      </Col>
      <Col xs={24} md={12} lg={8}>
        <Card hoverable title="Exportar Historia Clínica" extra={<DownloadOutlined />}
          actions={[<Button key="export" type="primary" block onClick={() => setModalExportarVisible(true)}>Exportar</Button>]}>
          <p>Exporta la historia clínica completa en diferentes formatos.</p>
          <Divider /><Text type="secondary">Formatos disponibles:</Text>
          <ul style={{ fontSize: 12 }}><li>PDF (Informe imprimible)</li><li>Excel (Análisis de datos)</li><li>JSON (Respaldo digital)</li></ul>
        </Card>
      </Col>
    </Row>
    <Divider />
    <Card title="Calculadora Gestacional Rápida" size="small">
      <Row gutter={16}>
        <Col span={12}>
          <Text strong>Calcular Edad Gestacional por FUM:</Text>
          <DatePicker style={{ width: '100%', marginTop: 8 }} placeholder="Seleccionar FUM"
            onChange={(date: Dayjs | null) => {
              if (date) {
                const eg = calcularEG(date.format('YYYY-MM-DD'));
                const fpp = calcularFPP(date.format('YYYY-MM-DD'));
                notification.info({ message: 'Resultado del Cálculo', description: (<div><p><strong>Edad Gestacional:</strong> {eg.texto}</p><p><strong>FPP (Regla de Naegele):</strong> {dayjs(fpp).format('DD/MM/YYYY')}</p><p><strong>Días hasta FPP:</strong> {dayjs(fpp).diff(dayjs(), 'days')} días</p></div>), duration: 0 });
              }
            }} />
        </Col>
        <Col span={12}>
          <Text strong>Interpretación de NST:</Text>
          <Button style={{ width: '100%', marginTop: 8 }} onClick={() => {
            modal.info({
              title: 'Interpretador de Monitoreo Fetal (NST)', width: 600,
              content: (
                <Form layout="vertical" onFinish={(values) => {
                  const resultado = interpretarNST(values.fcf_basal, values.aceleraciones, values.deceleraciones, values.variabilidad);
                  modal.success({ title: resultado.interpretacion, content: (<div><p><strong>Reactivo:</strong> {resultado.reactivo ? 'SÍ' : 'NO'}</p><Divider /><p><strong>Conducta Recomendada:</strong></p><p>{resultado.conducta}</p></div>) });
                }}>
                  <Form.Item name="fcf_basal" label="FCF Basal (lpm)" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 140" /></Form.Item>
                  <Form.Item name="aceleraciones" label="Número de Aceleraciones (>15 lpm)" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 2" /></Form.Item>
                  <Form.Item name="deceleraciones" label="Número de Deceleraciones" rules={[{ required: true }]}><Input type="number" placeholder="Ej: 0" /></Form.Item>
                  <Form.Item name="variabilidad" label="Variabilidad" rules={[{ required: true }]}>
                    <Select>
                      <Option value="AUSENTE">Ausente (&lt;5 lpm)</Option>
                      <Option value="MINIMA">Mínima (5-10 lpm)</Option>
                      <Option value="MODERADA">Moderada (10-25 lpm)</Option>
                      <Option value="MARCADA">Marcada (&gt;25 lpm)</Option>
                    </Select>
                  </Form.Item>
                  <Button type="primary" htmlType="submit" block>Interpretar NST</Button>
                </Form>
              )
            });
          }}>Interpretar NST</Button>
        </Col>
      </Row>
    </Card>
  </div>
  );
};

export default TabHerramientasClinicas;
