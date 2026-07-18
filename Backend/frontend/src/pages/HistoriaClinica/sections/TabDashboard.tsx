import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Row, Col, Card, Space, Tag, Progress, Descriptions, Empty, Button, Timeline,
  Typography, Statistic, Alert,
} from 'antd';
import {
  HistoryOutlined, ScanOutlined, WomanOutlined, ExperimentOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { useAntdApp } from '../../../hooks/useMessage';
import GraficoPesoMaterno from '../../../components/graficos/GraficoPesoMaterno';
import GraficoAlturaUterina from '../../../components/graficos/GraficoAlturaUterina';
import GraficoPresionArterial from '../../../components/graficos/GraficoPresionArterial';
import { AlertaClinica, Embarazo, ControlPrenatal } from '../types';
import { RIESGO_COLORS, safeNum } from '../utils';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid, RechartsTooltip, Legend,
  ResponsiveContainer, Area,
} from '../rechartsLazy';

const { Text } = Typography;

interface DashboardObstetricoProps {
  alertasClinicas: AlertaClinica[];
  embarazoActivo: Embarazo | null;
  controles: ControlPrenatal[];
  laboratorios: any[];
  ecografias: any[];
  calcularEGActual: () => { semanas: number; dias: number };
  datosGraficas: any[];
  pacienteId: string | undefined;
  navigate: ReturnType<typeof useNavigate>;
}

const DashboardObstetrico: React.FC<DashboardObstetricoProps> = React.memo(({
  alertasClinicas,
  embarazoActivo,
  controles,
  laboratorios,
  ecografias,
  calcularEGActual,
  datosGraficas,
  pacienteId,
  navigate,
}) => {
  const { message, modal } = useAntdApp();
  const { semanas, dias } = calcularEGActual();
  const porcentaje = Math.min((semanas / 40) * 100, 100);

  return (
    <div className="dashboard-tab">
      {alertasClinicas.map((alerta) => (
        <Alert
          key={`${alerta.tipo}-${alerta.mensaje}`}
          message={alerta.mensaje}
          type={alerta.tipo === 'ERROR' ? 'error' : alerta.tipo === 'WARNING' ? 'warning' : 'info'}
          showIcon
          style={{ marginBottom: 12 }}
          action={
            alerta.acciones_recomendadas && alerta.acciones_recomendadas.length > 0 ? (
              <Button size="small" type="text" onClick={() => {
                modal.info({
                  title: 'Acciones Recomendadas',
                  content: (
                    <ul>
                      {alerta.acciones_recomendadas!.map((accion) => (
                        <li key={accion}>{accion}</li>
                      ))}
                    </ul>
                  )
                });
              }}>
                Ver Acciones
              </Button>
            ) : undefined
          }
        />
      ))}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card
            title={embarazoActivo?.estado === 'activo' ? "🤰 Embarazo Actual" : "📋 Embarazo Más Reciente"}
            className="card-shadow"
            extra={
              embarazoActivo ? (
                <Space>
                  {embarazoActivo.estado !== 'activo' && <Tag color="default">Histórico</Tag>}
                  <Tag color={RIESGO_COLORS[embarazoActivo?.riesgo || 'BAJO']}>{embarazoActivo?.riesgo}</Tag>
                </Space>
              ) : null
            }
          >
            {embarazoActivo ? (
              <div style={{ textAlign: 'center' }}>
                <Progress type="circle" percent={porcentaje} format={() => `${semanas}.${dias} sem`} size={120} strokeColor={embarazoActivo.estado === 'activo' ? "#1890ff" : "#8c8c8c"} />
                <div style={{ marginTop: 20, textAlign: 'left' }}>
                  <Descriptions column={1} size="small" bordered>
                    <Descriptions.Item label="FPP (FUM)">{dayjs(embarazoActivo.fecha_probable_parto).format('DD MMM YYYY')}</Descriptions.Item>
                    <Descriptions.Item label="FUM">{dayjs(embarazoActivo.fecha_ultima_menstruacion).format('DD/MM/YYYY')}</Descriptions.Item>
                    <Descriptions.Item label="Paridad">G{embarazoActivo.numero_gesta} P{embarazoActivo.partos_previos} C{embarazoActivo.cesareas_previas} A{embarazoActivo.abortos_previos}</Descriptions.Item>
                  </Descriptions>
                </div>
              </div>
            ) : (
              <Empty description="No hay embarazos registrados" image={Empty.PRESENTED_IMAGE_SIMPLE}>
                <Button type="primary" onClick={() => navigate(`/embarazos/nuevo?paciente=${pacienteId}`)}>Iniciar Embarazo</Button>
              </Empty>
            )}
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="📈 Evolución: Altura Uterina vs Semanas" className="card-shadow">
            {controles.length > 1 ? (
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={datosGraficas}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="semana" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="p90" stroke="none" fill="#e6f7ff" name="P90" />
                  <Area type="monotone" dataKey="p10" stroke="none" fill="#ffffff" name="P10" />
                  <Line type="monotone" dataKey="au" stroke="#ff4d4f" strokeWidth={2} name="Altura Uterina (cm)" dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="p50" stroke="#8c8c8c" strokeDasharray="5 5" name="Referencia P50" dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : <Empty description="Insuficientes datos para graficar" />}
          </Card>
        </Col>

        <Col xs={24}>
          <Card size="small" title="Últimos Signos Vitales Registrados">
            {controles.length > 0 ? (
              <UltimosSignosVitales control={controles[controles.length - 1]} />
            ) : <Text type="secondary">Sin registros de control prenatal aún.</Text>}
          </Card>
        </Col>

        {controles.length > 0 && (
          <>
            <Col xs={24} lg={12}>
              <GraficoPesoMaterno
                data={controles
                  .reduce((acc, c) => {
                    if (c.peso_actual) {
                      acc.push({
                        semana: safeNum(c.semanas_gestacion),
                        peso_actual: safeNum(c.peso_actual)
                      });
                    }
                    return acc;
                  }, [] as any[])
                  .sort((a, b) => a.semana - b.semana)
                }
                pesoPregestacional={safeNum(embarazoActivo?.peso_pregestacional) || 50}
                tallaMaterna={safeNum(embarazoActivo?.talla_materna) || 160}
              />
            </Col>

            <Col xs={24} lg={12}>
              <GraficoPresionArterial
                data={controles
                  .reduce((acc, c) => {
                    if (c.presion_arterial_sistolica && c.presion_arterial_diastolica) {
                      acc.push({
                        semana: safeNum(c.semanas_gestacion),
                        sistolica: safeNum(c.presion_arterial_sistolica),
                        diastolica: safeNum(c.presion_arterial_diastolica)
                      });
                    }
                    return acc;
                  }, [] as any[])
                  .sort((a, b) => a.semana - b.semana)
                }
              />
            </Col>

            <Col xs={24}>
              <GraficoAlturaUterina
                data={controles
                  .reduce((acc, c) => {
                    if (c.altura_uterina) {
                      acc.push({
                        semana: c.semanas_gestacion || 0,
                        altura_uterina: c.altura_uterina || 0
                      });
                    }
                    return acc;
                  }, [] as any[])
                  .sort((a, b) => a.semana - b.semana)
                }
              />
            </Col>
          </>
        )}

        <Col xs={24}>
          <Card title={<><HistoryOutlined /> Línea de Tiempo del Embarazo</>} className="card-shadow">
            {embarazoActivo ? (
              <Timeline
                mode="left"
                items={[
                  {
                    color: 'green',
                    label: dayjs(embarazoActivo.fecha_ultima_menstruacion).format('DD/MM/YYYY'),
                    children: (
                      <>
                        <strong>Inicio del Embarazo (FUM)</strong>
                        <div>Fecha de Última Menstruación</div>
                      </>
                    )
                  },
                  ...controles.map((control: any) => ({
                    key: `control-${control.id}`,
                    color: 'blue',
                    label: dayjs(control.fecha).format('DD/MM/YYYY'),
                    children: (
                      <>
                        <strong>Control Prenatal - {control.semanas_gestacion} sem</strong>
                        <div>
                          Peso: {control.peso_actual}kg | PA: {control.presion_arterial_sistolica}/{control.presion_arterial_diastolica} mmHg
                          {control.observaciones && <div style={{ fontSize: 12, color: '#8c8c8c' }}>{control.observaciones.substring(0, 80)}…</div>}
                        </div>
                      </>
                    )
                  })),
                  ...ecografias.map((eco: any) => ({
                    key: `eco-${eco.id}`,
                    color: 'purple',
                    label: dayjs(eco.fecha).format('DD/MM/YYYY'),
                    dot: <ScanOutlined style={{ fontSize: 16 }} />,
                    children: (
                      <>
                        <strong>Ecografía - {eco.tipo}</strong>
                        <div>
                          EG: {eco.edad_gestacional ?? eco.edad_gestacional_semanas ?? '-'} sem | Peso Fetal: {eco.peso_fetal_estimado ? `${eco.peso_fetal_estimado}g` : 'no medido'}
                        </div>
                      </>
                    )
                  })),
                  ...laboratorios.slice(0, 5).map((lab: any) => ({
                    key: `lab-${lab.id}`,
                    color: lab.es_anormal ? "red" : "green",
                    label: dayjs(lab.fecha_toma).format('DD/MM/YYYY'),
                    dot: <ExperimentOutlined style={{ fontSize: 16 }} />,
                    children: (
                      <>
                        <strong>Laboratorio - {lab.tipo_examen}</strong>
                        <div>
                          Resultado: {lab.resultado} {lab.es_anormal && <Tag color="error">Anormal</Tag>}
                        </div>
                      </>
                    )
                  })),
                  ...(embarazoActivo.estado === 'activo' ? [{
                    color: 'gold',
                    label: dayjs(embarazoActivo.fecha_probable_parto).format('DD/MM/YYYY'),
                    dot: <WomanOutlined style={{ fontSize: 16 }} />,
                    children: (
                      <>
                        <strong>Fecha Probable de Parto (FPP)</strong>
                        <div>Estimada por FUM - 40 semanas</div>
                      </>
                    )
                  }] : []),
                  ...(embarazoActivo.estado !== 'activo' && (embarazoActivo as any).fecha_fin ? [{
                    color: 'gray',
                    label: dayjs((embarazoActivo as any).fecha_fin).format('DD/MM/YYYY'),
                    children: (
                      <>
                        <strong>Fin del Embarazo</strong>
                        <div>Desenlace: {(embarazoActivo as any).tipo_desenlace || 'No especificado'}</div>
                      </>
                    )
                  }] : [])
                ]}
              />
            ) : (
              <Empty description="No hay embarazo activo para mostrar línea de tiempo" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
});

interface UltimosSignosVitalesProps {
  control: ControlPrenatal;
}
const UltimosSignosVitales: React.FC<UltimosSignosVitalesProps> = React.memo(({ control }) => (
  <Row gutter={16} style={{ textAlign: 'center' }}>
    <Col span={4}>
      <Statistic title="Peso" value={control.peso_actual || 0} suffix="kg" />
    </Col>
    <Col span={4}>
      <Statistic title="IMC" value={control.imc_actual || control.imc || 0} precision={1} />
    </Col>
    <Col span={4}>
      <Statistic
        title="Presión Arterial"
        value={
          control.presion_arterial_sistolica && control.presion_arterial_diastolica
            ? `${control.presion_arterial_sistolica}/${control.presion_arterial_diastolica}`
            : 'N/D'
        }
        valueStyle={{
          color: (control.presion_arterial_sistolica || 0) >= 140 ? 'red' : 'black'
        }}
      />
    </Col>
    <Col span={4}>
      <Statistic title="LCF" value={control.frecuencia_cardiaca_fetal || 0} suffix="lpm" />
    </Col>
    <Col span={4}>
      <Statistic title="AU" value={control.altura_uterina || 0} suffix="cm" />
    </Col>
    <Col span={4}>
      <Statistic
        title="Ganancia Total"
        value={control.ganancia_peso || 0}
        suffix="kg"
        prefix={(control.ganancia_peso || 0) > 0 ? '+' : ''}
      />
    </Col>
  </Row>
));

export default DashboardObstetrico;
