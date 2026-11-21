import React from 'react';
import { Modal, Tabs, Card, Alert, Row, Col, Statistic, Divider, Table, Typography, Progress, Space } from 'antd';
import { BarChartOutlined, UserOutlined, WarningOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { ResumenPacientes } from '../pacientesTypes';

const { Text } = Typography;

const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
const CIUDADES = ['La Paz', 'Cochabamba', 'Santa Cruz', 'Oruro', 'Potosí', 'Tarija', 'Beni', 'Pando', 'Chuquisaca'];

/** Minúsculas y sin tildes: «Potosi» y «Potosí» son la misma ciudad. */
const normalizar = (texto: string): string =>
  texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

interface AnalisisDemograficoModalProps {
  visible: boolean;
  onClose: () => void;
  /**
   * Cifras del servidor con los filtros de la pantalla. Antes el modal
   * contaba sobre la lista que la pantalla había descargado entera; ahora
   * la pantalla solo tiene la página visible y contar ahí mentiría.
   */
  resumen: ResumenPacientes;
  token: any;
}

const AnalisisDemograficoModal: React.FC<AnalisisDemograficoModalProps> = ({
  visible, onClose, resumen, token,
}) => {
  const { total, rangos_edad: r } = resumen;
  const pct = (n: number) => (total > 0 ? (n / total) * 100 : 0);
  const menores20 = r['<15'] + r['15-19'];
  const de20a34 = r['20-24'] + r['25-29'] + r['30-34'];
  const de35oMas = r['35-39'] + r['>=40'];
  const porCiudad = (ciudad: string) => resumen.por_ciudad
    .filter(c => normalizar(c.ciudad).includes(normalizar(ciudad)))
    .reduce((acc, c) => acc + c.total, 0);

  return (
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
                  description={`Análisis de ${total} pacientes. Edad promedio: ${resumen.promedio_edad} años.`}
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic title="Menores de 20" value={menores20} suffix="pacientes" />
                  </Col>
                  <Col span={8}>
                    <Statistic title="20-34 años" value={de20a34} suffix="pacientes" />
                  </Col>
                  <Col span={8}>
                    <Statistic title="35 años o más" value={de35oMas} suffix="pacientes" />
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
                    { key: '1', rango: '< 15 años', cantidad: r['<15'] },
                    { key: '2', rango: '15-19 años', cantidad: r['15-19'] },
                    { key: '3', rango: '20-24 años', cantidad: r['20-24'] },
                    { key: '4', rango: '25-29 años', cantidad: r['25-29'] },
                    { key: '5', rango: '30-34 años', cantidad: r['30-34'] },
                    { key: '6', rango: '35-39 años', cantidad: r['35-39'] },
                    { key: '7', rango: '≥ 40 años', cantidad: r['>=40'] },
                  ].map(fila => ({ ...fila, porcentaje: pct(fila.cantidad) }))}
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
                {CIUDADES.map((ciudad) => {
                  const count = porCiudad(ciudad);
                  const percent = pct(count);
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
                      value={menores20}
                      suffix={`/ ${total}`}
                      prefix={<UserOutlined />}
                    />
                    <Text type="secondary">Requieren seguimiento psicosocial</Text>
                  </Card>

                  <Card size="small" title="Gestantes Añosas (≥ 35 años)">
                    <Statistic
                      value={resumen.anosas_gestando}
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
                  description={`Se han registrado ${resumen.nuevos_mes} nuevos pacientes este mes. Tendencia: ${resumen.nuevos_mes > 10 ? 'CRECIENTE' : 'ESTABLE'}`}
                  type={resumen.nuevos_mes > 10 ? 'success' : 'info'}
                  showIcon
                />
                <Divider />
                {/* Registros reales por mes del año en curso (antes, 12 ceros fijos). */}
                <Row gutter={16}>
                  {MESES.map((mes, i) => (
                    <Col span={6} key={mes}>
                      <Card size="small" style={{ textAlign: 'center', marginBottom: 8 }}>
                        <Statistic title={mes} value={resumen.registros_por_mes[i] ?? 0} valueStyle={{ fontSize: 18 }} />
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
};

export default AnalisisDemograficoModal;
