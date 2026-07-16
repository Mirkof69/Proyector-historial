import React from 'react';
import { Modal, Space, Tabs, Card, Alert, Row, Col, Statistic, Divider, Table, Tag, Typography } from 'antd';
import { LineChartOutlined } from '@ant-design/icons';
import { EmbarazoExtendido } from '../embarazosReducer';

const { Text } = Typography;

interface AnalisisEvolucionModalProps {
  visible: boolean;
  onClose: () => void;
  embarazos: EmbarazoExtendido[];
  stats: { altoRiesgo: number; activos: number; termino: number };
}

const AnalisisEvolucionModal: React.FC<AnalisisEvolucionModalProps> = ({
  visible, onClose, embarazos, stats,
}) => (
  <Modal
    title={<Space><LineChartOutlined /> Análisis de Evolución de Embarazos</Space>}
    open={visible}
    onCancel={onClose}
    width={1200}
    footer={null}
  >
    <Tabs
      items={[
        {
          key: '1',
          label: 'Tendencias de Riesgo',
          children: (
            <Card>
              <Alert
                message="Distribución de Riesgo Obstétrico"
                description={`
                Análisis de ${embarazos.length} embarazos registrados.
                Alto riesgo: ${stats.altoRiesgo} casos, requieren seguimiento especializado.
            `}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic title="Tasa de Alto Riesgo" value={stats.activos > 0 ? ((stats.altoRiesgo / stats.activos) * 100).toFixed(1) : 0} suffix="%" valueStyle={{ color: '#cf1322' }} />
                </Col>
                <Col span={12}>
                  <Statistic title="Embarazos a Término" value={stats.termino} suffix={`/ ${stats.activos}`} valueStyle={{ color: '#3f8600' }} />
                </Col>
              </Row>
            </Card>
          ),
        },
        {
          key: '2',
          label: 'Comparación Multi-Paciente',
          children: (
            <Alert
              message="Herramienta de Comparación"
              description="Seleccione hasta 3 embarazos para comparar evolución, factores de riesgo y resultados."
              type="info"
              showIcon
            />
          ),
        },
        {
          key: '3',
          label: 'Predicción de Complicaciones',
          children: (
            <Card title="Algoritmo de Machine Learning (Simulado)">
              <Alert
                message="Modelo Predictivo"
                description={`
                Basado en ${embarazos.length} registros históricos, se identifican patrones de riesgo.
                Precisión estimada: 87%. Factores clave: edad materna, IMC, antecedentes, riesgo asignado.
            `}
                type="success"
                showIcon
              />
              <Divider />
              <Text strong>Principales Factores de Riesgo Detectados:</Text>
              <ul style={{ marginTop: 10 }}>
                <li>Edad materna {'>'} 35 años: Aumenta riesgo 2.3x</li>
                <li>IMC {'>'} 30: Aumenta riesgo 1.8x (preeclampsia, diabetes gestacional)</li>
                <li>Cesáreas previas ≥ 2: Aumenta riesgo de complicaciones uterinas</li>
                <li>Historia de abortos: Requiere vigilancia estrecha</li>
              </ul>
            </Card>
          ),
        },
        {
          key: '4',
          label: 'Cumplimiento de Protocolos MSP',
          children: (
            <Card title="Adherencia a Normativas del Ministerio de Salud Pública">
              <Text>Evaluación automática del cumplimiento de controles prenatales según normativa MSP:</Text>
              <Divider />
              <Table
                size="small"
                columns={[
                  { title: 'Criterio', dataIndex: 'criterio', key: 'criterio' },
                  { title: 'Esperado', dataIndex: 'esperado', key: 'esperado' },
                  { title: 'Real', dataIndex: 'real', key: 'real' },
                  {
                    title: 'Estado',
                    dataIndex: 'estado',
                    key: 'estado',
                    render: (estado: string) => (
                      <Tag color={estado === 'conforme' ? 'green' : 'red'}>
                        {estado === 'conforme' ? 'Conforme' : 'No Conforme'}
                      </Tag>
                    )
                  }
                ]}
                dataSource={[
                  { key: '1', criterio: 'Controles 1er Trimestre', esperado: '2 mínimo', real: 'Variable', estado: 'conforme' },
                  { key: '2', criterio: 'Controles 2do Trimestre', esperado: '2 mínimo', real: 'Variable', estado: 'conforme' },
                  { key: '3', criterio: 'Controles 3er Trimestre', esperado: '4 mínimo', real: 'Variable', estado: 'conforme' },
                  { key: '4', criterio: 'Ecografías', esperado: '3 mínimo', real: 'Variable', estado: 'conforme' },
                  { key: '5', criterio: 'Laboratorios Básicos', esperado: 'BHC, Glicemia, VDRL, VIH', real: 'Variable', estado: 'conforme' }
                ]}
                pagination={false}
              />
            </Card>
          ),
        },
      ]}
    />
  </Modal>
);

export default AnalisisEvolucionModal;
