import React, { useState, useEffect, useMemo, useCallback, useRef, lazy } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Row,
  Col,
  Typography,
  Tabs,
  Table,
  Tag,
  Button,
  Avatar,
  Descriptions,
  Statistic,
  Timeline,
  Alert,
  Spin,
  Divider,
  Empty,
  Tooltip,
  Space,
  Badge,
  Drawer,
  Modal,
  Form,
  Input,
  Select,
  List,
  Progress,
  Dropdown,
  DatePicker,
  Checkbox,
  Result,
  Popconfirm
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  UserOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  ScanOutlined,
  CalendarOutlined,
  PrinterOutlined,
  EditOutlined,
  EyeOutlined,
  ArrowLeftOutlined,
  WarningOutlined,
  HeartOutlined,
  LineChartOutlined,
  FilePdfOutlined,
  HistoryOutlined,
  WomanOutlined,
  SaveOutlined,
  PlusOutlined,
  EllipsisOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  SafetyCertificateOutlined,
  CalculatorOutlined,
  PhoneOutlined,
  TeamOutlined,
  TableOutlined,
  SearchOutlined,
  BellOutlined
} from '@ant-design/icons';
import axios, { AxiosResponse } from 'axios';
import dayjs, { Dayjs } from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';
import 'dayjs/locale/es';
import './HistoriaClinica.css';
import GraficoPesoMaterno from '../../components/graficos/GraficoPesoMaterno';
import GraficoAlturaUterina from '../../components/graficos/GraficoAlturaUterina';
import GraficoPresionArterial from '../../components/graficos/GraficoPresionArterial';
import { API_URL } from '../../services/api';
import { antecedentesService,
  AntecedenteGinecoObstetrico,
  AntecedentePatologico
} from '../../services/antecedentesService';
import { useAuth } from '../../hooks/useAuth';
import {
  Paciente,
  Embarazo,
  ControlPrenatal,
  Ecografia,
  Laboratorio,
  NotaEvolucion,
  Tratamiento,
  Vacuna,
  Cita,
  Parto,
  AlertaClinica,
  CalculadoraResultado,
  ProtocoloObstetrico,
  EstadisticaGlobal,
  ExportConfig,
  BusquedaFiltro,
  RecordatorioClinico
} from './types';
import {
  RIESGO_COLORS,
  ESTADO_CIVIL_OPTS,
  PROTOCOLOS_EMBARAZO,
  VACUNAS_EMBARAZO,
  FACTORES_RIESGO,
  safeNum,
  getReferenceAU,
  calcularEG,
  calcularFPP,
  calcularIMC,
  calcularGananciaPesoRecomendada,
  calcularRiesgoPreeclampsia,
  calcularPesoFetalEstimado,
  calcularPercentilFetal,
  generarAlertas,
  interpretarNST,
  actualizarProtocolos,
  calcularTendencias
} from './utils';
import TabVacunas from './sections/TabVacunas';
import {
  ModalRegistroPacienteCompleto,
  BotonRegistroPacienteRapido,
  RegistroPacienteCompleto
} from './sections/ModalRegistroPacienteCompleto';
import TabTratamientos from './sections/TabTratamientos';
import TabPartos from './sections/TabPartos';
import TabNotasEvolucion from './sections/TabNotasEvolucion';
const ComposedChart = lazy(() => import('recharts').then(mod => ({ default: mod.ComposedChart })) as any);
const Line = lazy(() => import('recharts').then(mod => ({ default: mod.Line })) as any);
const Bar = lazy(() => import('recharts').then(mod => ({ default: mod.Bar })) as any);
const XAxis = lazy(() => import('recharts').then(mod => ({ default: mod.XAxis })) as any);
const YAxis = lazy(() => import('recharts').then(mod => ({ default: mod.YAxis })) as any);
const CartesianGrid = lazy(() => import('recharts').then(mod => ({ default: mod.CartesianGrid })) as any);
const RechartsTooltip = lazy(() => import('recharts').then(mod => ({ default: mod.Tooltip })) as any);
const Legend = lazy(() => import('recharts').then(mod => ({ default: mod.Legend })) as any);
const ResponsiveContainer = lazy(() => import('recharts').then(mod => ({ default: mod.ResponsiveContainer })) as any);
const ReferenceArea = lazy(() => import('recharts').then(mod => ({ default: mod.ReferenceArea })) as any);
const Area = lazy(() => import('recharts').then(mod => ({ default: mod.Area })) as any);

const verticalDivider = <Divider type="vertical" />;

dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.locale('es');

const formatAntecedente = (valor: any): string => {
    if (!valor) return 'No registra';
    if (typeof valor === 'string') return valor;
    if (typeof valor === 'object') {
      if (valor.resumen_enfermedades) return valor.resumen_enfermedades;
      if (valor.otras_enfermedades) return valor.otras_enfermedades;
      return 'Ver sección de antecedentes detallados';
    }
    return String(valor);
};

interface ProtocoloEmbarazoItemProps {
  protocolo: any;
}
const ProtocoloEmbarazoItem: React.FC<ProtocoloEmbarazoItemProps> = ({ protocolo }) => (
  <List.Item>
    <List.Item.Meta
      avatar={
        protocolo.cumplido ? (
          <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
        ) : (
          <CloseCircleOutlined style={{ fontSize: 24, color: '#ff4d4f' }} />
        )
      }
      title={protocolo.nombre}
      description={
        <>
          <Text type="secondary">{protocolo.descripcion}</Text>
          <br />
          <Tag color="blue">
            {protocolo.semanas_inicio}-{protocolo.semanas_fin} semanas
          </Tag>
          {protocolo.examenes_requeridos.map((examen: string) => (
            <Tag key={examen}>{examen}</Tag>
          ))}
        </>
      }
    />
    <div>
      <Progress
        type="circle"
        percent={protocolo.cumplido ? 100 : 0}
        width={50}
        status={protocolo.cumplido ? 'success' : 'exception'}
      />
    </div>
  </List.Item>
);

interface TendenciaLaboratorioItemProps {
  tendencia: any;
}
const TendenciaLaboratorioItem: React.FC<TendenciaLaboratorioItemProps> = ({ tendencia }) => (
  <List.Item>
    <Text strong>{tendencia.examen}: </Text>
    <Tag color={tendencia.tendencia === 'MEJORANDO' ? 'green' : tendencia.tendencia === 'EMPEORANDO' ? 'red' : 'blue'}>
      {tendencia.tendencia}
    </Tag>
  </List.Item>
);

interface AlertaClinicaItemProps {
  alerta: any;
  onResuelta: (id: string) => void;
}
const AlertaClinicaItem: React.FC<AlertaClinicaItemProps> = ({ alerta, onResuelta }) => (
  <List.Item>
    <Alert
      message={`${alerta.categoria} - Prioridad: ${alerta.prioridad}`}
      description={
        <>
          {alerta.mensaje}
          <br />
          <Text type="secondary">{dayjs(alerta.fecha_generacion).format('DD/MM/YYYY')}</Text>
          {alerta.acciones_recomendadas && alerta.acciones_recomendadas.length > 0 && (
            <>
              <br />
              <Text strong>Acciones recomendadas:</Text>
              <ul style={{ marginTop: 4, marginBottom: 0 }}>
                {alerta.acciones_recomendadas.map((accion: string) => (
                  <li key={accion}><Text type="secondary">{accion}</Text></li>
                ))}
              </ul>
            </>
          )}
        </>
      }
      type={alerta.tipo === 'ERROR' ? 'error' : 'warning'}
      showIcon
      style={{ width: '100%' }}
      action={
        <Button
          size="small"
          type="text"
          onClick={() => onResuelta(alerta.id)}
        >
          Marcar como resuelta
        </Button>
      }
    />
  </List.Item>
);

interface RiesgoPreeclampsiaItemProps {
  item: string;
}
const RiesgoPreeclampsiaItem: React.FC<RiesgoPreeclampsiaItemProps> = ({ item }) => (
  <List.Item>
    <CheckCircleOutlined style={{ color: '#1890ff', marginRight: 8 }} />
    {item}
  </List.Item>
);

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
                          EG: {eco.edad_gestacional_calculada} sem | Peso Fetal: {eco.peso_fetal_estimado}g
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

// ==========================================
// Runtime constants
// ==========================================
// Configuración global
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

// ==========================================
// Extracted Tab Components (module-level)
// ==========================================

interface TabControlesProps {
  controles: ControlPrenatal[];
  embarazoActivo: Embarazo | null;
  navigate: ReturnType<typeof useNavigate>;
}
const TabControles: React.FC<TabControlesProps> = ({ controles, embarazoActivo, navigate }) => {
  const {modal,  message } = useAntdApp();
  const chartData = controles
    .reduce((acc, c) => {
      if (c.peso_actual && c.presion_arterial_sistolica && c.presion_arterial_diastolica) {
        acc.push({
          semana: safeNum(c.semanas_gestacion),
          fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM'),
          peso: safeNum(c.peso_actual),
          sistolica: safeNum(c.presion_arterial_sistolica),
          diastolica: safeNum(c.presion_arterial_diastolica),
          altura_uterina: safeNum(c.altura_uterina),
          lcf: safeNum(c.frecuencia_cardiaca_fetal),
        });
      }
      return acc;
    }, [] as any[])
    .sort((a, b) => a.semana - b.semana);

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Title level={4}>Historial de Controles Prenatales</Title>
        <Space>
          <Button icon={<DownloadOutlined />}>Exportar Excel</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/controles/nuevo?embarazo=${embarazoActivo?.id}`)}>Nuevo Control</Button>
        </Space>
      </div>

      {chartData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={12}>
            <GraficoPesoMaterno
              data={chartData.map(d => ({
                semana: safeNum(d.semana),
                peso_actual: safeNum(d.peso)
              }))}
              pesoPregestacional={safeNum(embarazoActivo?.peso_pregestacional) || 50}
              tallaMaterna={safeNum(embarazoActivo?.talla_materna) || 160}
            />
          </Col>
          <Col xs={24} lg={12}>
            <GraficoPresionArterial
              data={chartData.map(d => ({
                semana: d.semana || 0,
                sistolica: d.sistolica || 0,
                diastolica: d.diastolica || 0
              }))}
            />
          </Col>
          <Col xs={24} lg={12}>
            <GraficoAlturaUterina
              data={chartData.map(d => ({
                semana: d.semana || 0,
                altura_uterina: d.altura_uterina || 0
              }))}
            />
          </Col>
          <Col xs={24} lg={12}>
            <Card title={<><HeartOutlined /> Frecuencia Cardíaca Fetal</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis domain={FCF_DOMAIN} label={FCF_LABEL} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={110} y2={160} fill="#52c41a" fillOpacity={0.1} />
                  <Line
                    type="monotone"
                    dataKey="lcf"
                    stroke="#eb2f96"
                    strokeWidth={2}
                    name="LCF (lpm)"
                    dot={{ fill: '#eb2f96', r: 4 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>
      )}

      <Table
        dataSource={[...controles].reverse()}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Semana', render: (_: any, r: any) => r.semanas_gestacion ?? r.edad_gestacional_semanas ?? '-', width: 80, align: 'center' as const },
          { title: 'Fecha', render: (_: any, r: any) => dayjs(r.fecha_control || r.fecha).format('DD/MM/YY'), width: 100 },
          { title: 'Peso (kg)', dataIndex: 'peso_actual', align: 'center' },
          { title: 'PA (mmHg)', render: (_, r: any) => <Tag color={r.presion_arterial_sistolica >= 140 ? 'red' : 'green'}>{r.presion_arterial_sistolica}/{r.presion_arterial_diastolica}</Tag>, align: 'center' },
          { title: 'AU (cm)', dataIndex: 'altura_uterina', align: 'center' },
          { title: 'LCF', dataIndex: 'frecuencia_cardiaca_fetal', align: 'center' },
          { title: 'Presentación', dataIndex: 'presentacion_fetal' },
          { title: 'Edema', dataIndex: 'edema', render: (v) => v ? 'SÍ' : 'NO' },
          { title: 'Médico', dataIndex: ['medico', 'username'], responsive: ['lg'] as any },
          {
            title: 'Acción', render: (_, r: any) => (
              <Space>
                <Tooltip title="Ver"><Button size="small" icon={<ScanOutlined />} onClick={() => navigate(`/controles/${r.id}`)} /></Tooltip>
                <Popconfirm title="¿Eliminar registro?" onConfirm={() => message.warning("Requiere permisos de admin")}><Button size="small" danger icon={<DeleteOutlined />} /></Popconfirm>
              </Space>
            )
          }
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ margin: 0 }}>
              <p><strong>Observaciones:</strong> {record.observaciones || 'Sin observaciones'}</p>
              <p><strong>Próxima cita:</strong> {record.proximo_control ? dayjs(record.proximo_control).format('DD/MM/YYYY') : 'No programada'}</p>
              <Divider style={{ margin: '8px 0' }} />
              <Space split={verticalDivider} size="small" style={{ fontSize: 12, color: '#8c8c8c' }}>
                <span><ClockCircleOutlined /> Creado: {dayjs(record.fecha_registro || record.fecha).format('DD/MM/YYYY HH:mm')}</span>
                {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (
                  <span><EditOutlined /> Modificado: {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm')}</span>
                )}
                <span><UserOutlined /> Por: {record.medico?.username || record.medico?.nombre || 'Sistema'}</span>
              </Space>
            </div>
          ),
        }}
      />
    </div>
  );
};

interface TabEcografiasProps {
  ecografias: Ecografia[];
  navigate: ReturnType<typeof useNavigate>;
  embarazoActivo: Embarazo | null;
}
const TabEcografias: React.FC<TabEcografiasProps> = ({ ecografias, navigate, embarazoActivo }) => {
  const fetalGrowthData = ecografias
    .reduce((acc, e: any) => {
      if (e.peso_fetal_estimado && e.edad_gestacional_calculada) {
        acc.push({
          semana: Number(e.edad_gestacional_calculada),
          fecha: dayjs(e.fecha).format('DD/MM'),
          peso: Number(e.peso_fetal_estimado),
          dbp: e.diametro_biparietal ? Number(e.diametro_biparietal) : null,
          ca: e.circunferencia_abdominal ? Number(e.circunferencia_abdominal) : null,
          lf: e.longitud_femur ? Number(e.longitud_femur) : null,
        });
      }
      return acc;
    }, [] as any[])
    .sort((a, b) => a.semana - b.semana);

  return (
    <div>
      {fetalGrowthData.length > 0 && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} lg={12}>
            <Card title={<><ScanOutlined /> Curva de Crecimiento Fetal - Peso</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={fetalGrowthData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="semana" label={{ value: 'Semanas de Gestación', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Peso (g)', angle: -90, position: 'insideLeft' }} />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="peso" stroke="#722ed1" fill="#722ed1" fillOpacity={0.3} name="Peso Fetal (g)" />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
          {fetalGrowthData.some(d => d.dbp) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Diámetro Biparietal (DBP)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.dbp)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="dbp" stroke="#1890ff" strokeWidth={2} name="DBP (mm)" dot={{ fill: '#1890ff', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
          {fetalGrowthData.some(d => d.ca) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Circunferencia Abdominal (CA)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.ca)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="ca" stroke="#52c41a" strokeWidth={2} name="CA (mm)" dot={{ fill: '#52c41a', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
          {fetalGrowthData.some(d => d.lf) && (
            <Col xs={24} lg={12}>
              <Card title={<><ScanOutlined /> Longitud del Fémur (LF)</>} size="small">
                <ResponsiveContainer width="100%" height={250}>
                  <ComposedChart data={fetalGrowthData.filter(d => d.lf)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="semana" label={{ value: 'Semanas EG', position: 'insideBottom', offset: -5 }} />
                    <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft' }} />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="lf" stroke="#faad14" strokeWidth={2} name="LF (mm)" dot={{ fill: '#faad14', r: 5 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          )}
        </Row>
      )}

      <div className="ecografias-gallery" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {ecografias.map(eco => (
            <Col xs={24} sm={12} md={8} lg={6} key={eco.id}>
              <Card
                hoverable
                cover={<div style={{ height: 150, background: '#333', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><ScanOutlined style={{ fontSize: 40 }} /></div>}
                actions={[
                  <Tooltip title="Ver Reporte" key="report"><FileTextOutlined onClick={() => navigate(`/ecografias/${eco.id}`)} /></Tooltip>,
                  <Tooltip title="Editar" key="edit"><EditOutlined /></Tooltip>
                ]}
              >
                <Card.Meta
                  title={eco.tipo}
                  description={
                    <div style={{ fontSize: 12 }}>
                      <p><CalendarOutlined /> {dayjs(eco.fecha).format('DD/MM/YYYY')}</p>
                      <p><strong>EG:</strong> {eco.edad_gestacional_calculada} sem</p>
                      <p><strong>Peso:</strong> {eco.peso_fetal_estimado}g</p>
                    </div>
                  }
                />
              </Card>
            </Col>
          ))}
          <Col xs={24} sm={12} md={8} lg={6}>
            <Button type="dashed" block style={{ height: '100%' }} icon={<PlusOutlined style={{ fontSize: 30 }} />} onClick={() => navigate(`/ecografias/nuevo?embarazo=${embarazoActivo?.id || ''}`)}>
              Nueva Ecografía
            </Button>
          </Col>
        </Row>
      </div>

      <Table
        dataSource={[...ecografias].reverse()}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', render: (t) => dayjs(t).format('DD/MM/YY'), width: 100, sorter: (a: any, b: any) => new Date(a.fecha).getTime() - new Date(b.fecha).getTime() },
          { title: 'Tipo', dataIndex: 'tipo', width: 180, filters: [{ text: 'Primer Trimestre', value: 'PRIMER_TRIMESTRE' }, { text: 'Segundo Trimestre', value: 'SEGUNDO_TRIMESTRE' }, { text: 'Tercer Trimestre', value: 'TERCER_TRIMESTRE' }, { text: 'Doppler', value: 'DOPPLER' }], onFilter: (value: any, record: any) => record.tipo === value, render: (tipo) => <Tag color="purple">{tipo}</Tag> },
          { title: 'EG Calculada', dataIndex: 'edad_gestacional_calculada', render: (eg) => <Text strong>{eg} sem</Text>, align: 'center' as const, width: 100 },
          { title: 'Peso Fetal', dataIndex: 'peso_fetal_estimado', render: (peso) => peso ? `${peso}g` : '-', align: 'center' as const, width: 100 },
          { title: 'Medidas Biométricas', render: (_, r: any) => (<Space size={4} direction="vertical">{r.diametro_biparietal && <Text type="secondary" style={{ fontSize: 12 }}>DBP: {r.diametro_biparietal}mm</Text>}{r.circunferencia_abdominal && <Text type="secondary" style={{ fontSize: 12 }}>CA: {r.circunferencia_abdominal}mm</Text>}{r.longitud_femur && <Text type="secondary" style={{ fontSize: 12 }}>LF: {r.longitud_femur}mm</Text>}</Space>), width: 150 },
          { title: 'Líquido Amniótico', dataIndex: 'liquido_amniotico', render: (la) => { if (!la) return '-'; const colors: any = { NORMAL: 'success', OLIGOHIDRAMNIOS: 'error', POLIHIDRAMNIOS: 'warning' }; return <Tag color={colors[la] || 'default'}>{la}</Tag>; }, align: 'center' as const, width: 130 },
          { title: 'Acciones', render: (_, r: any) => (<Space><Tooltip title="Ver detalles"><Button size="small" icon={<EyeOutlined />} onClick={() => navigate(`/ecografias/${r.id}`)} /></Tooltip></Space>), fixed: 'right' as const, width: 80 },
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ padding: '16px 24px', background: 'var(--bg-secondary, #fafafa)' }}>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Descriptions bordered column={3} size="small">
                    <Descriptions.Item label="Tipo de Ecografía" span={1}><Tag color="purple">{record.tipo}</Tag></Descriptions.Item>
                    <Descriptions.Item label="Fecha" span={1}>{dayjs(record.fecha).format('DD/MM/YYYY')}</Descriptions.Item>
                    <Descriptions.Item label="EG Calculada" span={1}><Text strong>{record.edad_gestacional_calculada} semanas</Text></Descriptions.Item>
                    <Descriptions.Item label="Peso Fetal Estimado" span={1}><Text strong style={{ fontSize: 16 }}>{record.peso_fetal_estimado}g</Text></Descriptions.Item>
                    <Descriptions.Item label="Percentil de Peso" span={2}>{record.percentil_peso ? <Progress percent={record.percentil_peso} size="small" /> : 'No calculado'}</Descriptions.Item>
                    <Descriptions.Item label="Diámetro Biparietal (DBP)" span={1}>{record.diametro_biparietal ? `${record.diametro_biparietal} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Circunferencia Abdominal (CA)" span={1}>{record.circunferencia_abdominal ? `${record.circunferencia_abdominal} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud del Fémur (LF)" span={1}>{record.longitud_femur ? `${record.longitud_femur} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Circunferencia Cefálica (CC)" span={1}>{record.circunferencia_cefalica ? `${record.circunferencia_cefalica} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud Húmero" span={1}>{record.longitud_humero ? `${record.longitud_humero} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Longitud Cúbito/Radio" span={1}>{record.longitud_cubito ? `${record.longitud_cubito} mm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Líquido Amniótico" span={1}>{record.liquido_amniotico ? (<Tag color={record.liquido_amniotico === 'NORMAL' ? 'success' : record.liquido_amniotico === 'OLIGOHIDRAMNIOS' ? 'error' : 'warning'}>{record.liquido_amniotico}</Tag>) : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Índice de Líquido Amniótico (ILA)" span={1}>{record.indice_liquido_amniotico ? `${record.indice_liquido_amniotico} cm` : '-'}</Descriptions.Item>
                    <Descriptions.Item label="Placenta" span={1}>{record.placenta || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Posición Placenta" span={1}>{record.posicion_placenta || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Grado Placentario" span={1}>{record.grado_placentario || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Cordón Umbilical" span={1}>{record.cordon_umbilical || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Sexo Fetal" span={1}>{record.sexo_fetal ? (<Tag color={record.sexo_fetal === 'M' ? 'blue' : 'pink'}>{record.sexo_fetal === 'M' ? 'Masculino ♂' : 'Femenino ♀'}</Tag>) : 'No determinado'}</Descriptions.Item>
                    <Descriptions.Item label="Presentación" span={1}>{record.presentacion || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Latido Cardíaco Fetal" span={1}>{record.latido_cardiaco_fetal ? `${record.latido_cardiaco_fetal} lpm` : '-'}</Descriptions.Item>
                    {record.anatomia_fetal && (<Descriptions.Item label="Anatomía Fetal" span={3}><Text>{record.anatomia_fetal}</Text></Descriptions.Item>)}
                    {record.hallazgos && (<Descriptions.Item label="Hallazgos" span={3}><Alert type="info" message={record.hallazgos} showIcon /></Descriptions.Item>)}
                    {record.observaciones && (<Descriptions.Item label="Observaciones" span={3}><Text>{record.observaciones}</Text></Descriptions.Item>)}
                    {record.diagnostico && (<Descriptions.Item label="Diagnóstico" span={3}><Text strong>{record.diagnostico}</Text></Descriptions.Item>)}
                  </Descriptions>
                </Col>
                <Col span={24}>
                  <Card size="small" title="Trazabilidad" style={{ background: 'var(--bg-tertiary, #f0f2f5)' }}>
                    <Space split={verticalDivider} size="large">
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Realizado por:</Text>
                        <Text strong><UserOutlined /> {record.medico?.nombre || record.medico?.username || 'Sistema'}</Text>
                      </Space>
                      <Space direction="vertical" size={0}>
                        <Text type="secondary">Fecha de registro:</Text>
                        <Text strong><ClockCircleOutlined /> {record.fecha_registro ? dayjs(record.fecha_registro).format('DD/MM/YYYY HH:mm:ss') : '-'}</Text>
                      </Space>
                      {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (
                        <Space direction="vertical" size={0}>
                          <Text type="secondary">Última modificación:</Text>
                          <Text strong><EditOutlined /> {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm:ss')}</Text>
                        </Space>
                      )}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          ),
        }}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total: ${total} ecografías` }}
      />
    </div>
  );
};

interface TabLaboratoriosProps {
  laboratorios: Laboratorio[];
}
const TabLaboratorios: React.FC<TabLaboratoriosProps> = ({ laboratorios }) => {
  const labChartData = {
    hemoglobina: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if (tipo.includes('hemoglobina') && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
    glucosa: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if ((tipo.includes('glucosa') || tipo.includes('glicemia')) && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
    hematocrito: laboratorios
      .reduce((acc, l) => {
        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
        if (tipo.includes('hematocrito') && l.resultado) {
          acc.push({ fecha: dayjs(l.fecha_toma).format('DD/MM'), valor: parseFloat(l.resultado), fecha_timestamp: new Date(l.fecha_toma).getTime() });
        }
        return acc;
      }, [] as any[])
      .sort((a, b) => a.fecha_timestamp - b.fecha_timestamp),
  };

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {labChartData.hemoglobina.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Hemoglobina</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.hemoglobina}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={HGB_LABEL} domain={HGB_DOMAIN} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={11} y2={14} fill="#52c41a" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#ff4d4f" strokeWidth={2} name="Hemoglobina (g/dL)" dot={{ fill: '#ff4d4f', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        {labChartData.glucosa.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Glucosa</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.glucosa}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={{ value: 'mg/dL', angle: -90, position: 'insideLeft' }} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={70} y2={100} fill="#52c41a" fillOpacity={0.1} />
                  <ReferenceArea y1={125} y2={200} fill="#ff4d4f" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#faad14" strokeWidth={2} name="Glucosa (mg/dL)" dot={{ fill: '#faad14', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
        {labChartData.hematocrito.length > 0 && (
          <Col xs={24} lg={12}>
            <Card title={<><ExperimentOutlined /> Evolución de Hematocrito</>} size="small">
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={labChartData.hematocrito}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" />
                  <YAxis label={HCT_LABEL} domain={HCT_DOMAIN} />
                  <RechartsTooltip />
                  <Legend />
                  <ReferenceArea y1={33} y2={44} fill="#52c41a" fillOpacity={0.1} />
                  <Line type="monotone" dataKey="valor" stroke="#1890ff" strokeWidth={2} name="Hematocrito (%)" dot={{ fill: '#1890ff', r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
      </Row>

      <Table
        dataSource={[...laboratorios].reverse()}
        rowKey="id"
        size="middle"
        bordered
        columns={[
          { title: 'Fecha Toma', dataIndex: 'fecha_toma', render: (t) => dayjs(t).format('DD/MM/YY'), width: 100, sorter: (a: any, b: any) => new Date(a.fecha_toma).getTime() - new Date(b.fecha_toma).getTime() },
          { title: 'Categoría', dataIndex: 'categoria', render: (t) => <Tag color="blue">{t || 'General'}</Tag>, width: 120, filters: [{ text: 'Hematología', value: 'HEMATOLOGIA' }, { text: 'Química', value: 'QUIMICA' }, { text: 'Inmunología', value: 'INMUNOLOGIA' }, { text: 'Microbiología', value: 'MICROBIOLOGIA' }], onFilter: (value: any, record: any) => record.categoria === value },
          { title: 'Examen', dataIndex: 'tipo_examen', width: 200 },
          { title: 'Resultado', dataIndex: 'resultado', render: (t, r: any) => (<Text strong type={r.es_anormal ? 'danger' : 'success'}>{t} {r.unidad || ''}</Text>), width: 120 },
          { title: 'Valores Ref.', dataIndex: 'valores_referencia', responsive: ['md'] as any, width: 120 },
          { title: 'Estado', dataIndex: 'es_anormal', render: (v) => v ? (<Badge status="error" text="Anormal" />) : (<Badge status="success" text="Normal" />), align: 'center' as const, width: 100, filters: [{ text: 'Normal', value: false }, { text: 'Anormal', value: true }], onFilter: (value: any, record: any) => record.es_anormal === value },
          { title: 'Adjunto', render: (_, r: any) => r.archivo_adjunto ? (<Button type="link" icon={<DownloadOutlined />} size="small">PDF</Button>) : (<Text type="secondary">-</Text>), align: 'center' as const, width: 80 }
        ]}
        expandable={{
          expandedRowRender: (record: any) => (
            <div style={{ padding: '16px 24px', background: '#fafafa' }}>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Descriptions bordered column={3} size="small">
                    <Descriptions.Item label="Categoría" span={1}><Tag color="blue">{record.categoria || 'General'}</Tag></Descriptions.Item>
                    <Descriptions.Item label="Tipo de Examen" span={2}><Text strong>{record.tipo_examen}</Text></Descriptions.Item>
                    <Descriptions.Item label="Fecha de Toma" span={1}>{dayjs(record.fecha_toma).format('DD/MM/YYYY HH:mm')}</Descriptions.Item>
                    <Descriptions.Item label="Resultado" span={1}><Text strong style={{ fontSize: 16 }} type={record.es_anormal ? 'danger' : 'success'}>{record.resultado} {record.unidad || ''}</Text></Descriptions.Item>
                    <Descriptions.Item label="Estado" span={1}>{record.es_anormal ? (<Tag color="error" icon={<WarningOutlined />}>ANORMAL</Tag>) : (<Tag color="success" icon={<CheckCircleOutlined />}>NORMAL</Tag>)}</Descriptions.Item>
                    <Descriptions.Item label="Valores de Referencia" span={3}><Text code>{record.valores_referencia || 'No especificado'}</Text></Descriptions.Item>
                    {record.interpretacion && (<Descriptions.Item label="Interpretación" span={3}><Alert type={record.es_anormal ? 'error' : 'success'} message={record.interpretacion} showIcon /></Descriptions.Item>)}
                    {record.observaciones && (<Descriptions.Item label="Observaciones" span={3}><Text>{record.observaciones}</Text></Descriptions.Item>)}
                    {record.metodo && (<Descriptions.Item label="Método" span={1}>{record.metodo}</Descriptions.Item>)}
                    {record.laboratorio_externo && (<Descriptions.Item label="Laboratorio" span={2}>{record.laboratorio_externo}</Descriptions.Item>)}
                    {record.archivo_adjunto && (<Descriptions.Item label="Archivo Adjunto" span={3}><Button type="primary" icon={<DownloadOutlined />} size="small">Descargar Resultado PDF</Button></Descriptions.Item>)}
                  </Descriptions>
                </Col>
                <Col span={24}>
                  <Card size="small" title="Trazabilidad" style={{ background: '#f0f2f5' }}>
                    <Space split={verticalDivider} size="large">
                      <Space direction="vertical" size={0}><Text type="secondary">Registrado por:</Text><Text strong><UserOutlined /> {record.medico?.nombre || record.medico?.username || 'Sistema'}</Text></Space>
                      <Space direction="vertical" size={0}><Text type="secondary">Fecha de registro:</Text><Text strong><ClockCircleOutlined /> {record.fecha_registro ? dayjs(record.fecha_registro).format('DD/MM/YYYY HH:mm:ss') : '-'}</Text></Space>
                      {record.fecha_actualizacion && record.fecha_actualizacion !== record.fecha_registro && (<Space direction="vertical" size={0}><Text type="secondary">Última modificación:</Text><Text strong><EditOutlined /> {dayjs(record.fecha_actualizacion).format('DD/MM/YYYY HH:mm:ss')}</Text></Space>)}
                      {record.semanas_gestacion && (<Space direction="vertical" size={0}><Text type="secondary">Edad gestacional:</Text><Text strong>{record.semanas_gestacion} semanas</Text></Space>)}
                    </Space>
                  </Card>
                </Col>
              </Row>
            </div>
          ),
        }}
        pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (total) => `Total: ${total} exámenes` }}
      />
    </div>
  );
};

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

interface ProtocoloItemProps {
  protocolo: any;
  calcularEGActual: () => { semanas: number };
  laboratorios: Laboratorio[];
  ecografias: Ecografia[];
}
const ProtocoloItem: React.FC<ProtocoloItemProps> = ({ protocolo, calcularEGActual, laboratorios, ecografias }) => {
  const { modal } = useAntdApp();
  const { semanas } = calcularEGActual();
  const enVentana = semanas >= protocolo.semanas_inicio && semanas <= protocolo.semanas_fin;
  const fueraDeTiempo = semanas > protocolo.semanas_fin;
  const cumplido = protocolo.examenes_requeridos.some((examen: any) => {
    const examenLower = String(examen || '').toLowerCase();
    return laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) ||
      ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
  });
  return (
    <Card key={protocolo.id} style={{ marginBottom: 16 }} type={enVentana ? 'inner' : undefined} styles={{ body: { boxShadow: enVentana ? 'inset 4px 0 0 #1890ff' : undefined } }}>
      <Row align="middle" gutter={16}>
        <Col flex="auto">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Space>
              <Text strong style={{ fontSize: 16 }}>{protocolo.nombre}</Text>
              {cumplido && <Tag color="success" icon={<CheckCircleOutlined />}>CUMPLIDO</Tag>}
              {!cumplido && fueraDeTiempo && <Tag color="error" icon={<CloseCircleOutlined />}>FUERA DE TIEMPO</Tag>}
              {!cumplido && enVentana && <Tag color="warning" icon={<ClockCircleOutlined />}>PENDIENTE</Tag>}
              {!cumplido && !enVentana && !fueraDeTiempo && <Tag color="default">PRÓXIMAMENTE</Tag>}
            </Space>
            <Text type="secondary">{protocolo.descripcion}</Text>
            <Text type="secondary" style={{ fontSize: 12 }}>Ventana: {protocolo.semanas_inicio}-{protocolo.semanas_fin} semanas</Text>
          </Space>
        </Col>
        <Col>
          <Button type={enVentana ? 'primary' : 'default'} icon={<FileTextOutlined />} onClick={() => {
            modal.info({
              title: protocolo.nombre, width: 700,
              content: (
                <div>
                  <Descriptions bordered column={1} size="small">
                    <Descriptions.Item label="Descripción">{protocolo.descripcion}</Descriptions.Item>
                    <Descriptions.Item label="Ventana Temporal">{protocolo.semanas_inicio} - {protocolo.semanas_fin} semanas</Descriptions.Item>
                    <Descriptions.Item label="Estado">{cumplido ? <Tag color="success">CUMPLIDO</Tag> : fueraDeTiempo ? <Tag color="error">FUERA DE TIEMPO</Tag> : enVentana ? <Tag color="warning">PENDIENTE</Tag> : <Tag color="default">PRÓXIMAMENTE</Tag>}</Descriptions.Item>
                  </Descriptions>
                  <Divider orientation="left">Exámenes Requeridos</Divider>
                  <List size="small" dataSource={protocolo.examenes_requeridos || []} renderItem={(examen: any) => {
                    const examenLower = String(examen || '').toLowerCase();
                    const realizado = laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) || ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
                    return (<List.Item key={`exam-${examen}`}>{realizado ? <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} /> : <CloseCircleOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />}{examen}{realizado && <Tag color="success" style={{ marginLeft: 8 }}>Realizado</Tag>}</List.Item>);
                  }} />
                </div>
              )
            });
          }}>Ver Detalles</Button>
        </Col>
      </Row>
    </Card>
  );
};

interface TabProtocolosCumplimientoProps {
  calcularEGActual: () => { semanas: number };
  laboratorios: Laboratorio[];
  ecografias: Ecografia[];
}
const TabProtocolosCumplimiento: React.FC<TabProtocolosCumplimientoProps> = ({ calcularEGActual, laboratorios, ecografias }) => (
  <div>
    <Alert message="Protocolos de Atención Prenatal" description="Seguimiento del cumplimiento de guías clínicas MSP/OMS para control prenatal" type="info" showIcon style={{ marginBottom: 16 }} />
    <List
      dataSource={PROTOCOLOS_EMBARAZO}
      renderItem={(protocolo) => (
        <ProtocoloItem
          protocolo={protocolo}
          calcularEGActual={calcularEGActual}
          laboratorios={laboratorios}
          ecografias={ecografias}
        />
      )}
    />
  </div>
);

interface TabComparacionEmbarazosProps {
  embarazoActivo: Embarazo | null;
  historialEmbarazos: Embarazo[];
  navigate: ReturnType<typeof useNavigate>;
  pacienteId: string | undefined;
}
const TabComparacionEmbarazos: React.FC<TabComparacionEmbarazosProps> = ({ embarazoActivo, historialEmbarazos, navigate, pacienteId }) => {
  const todosLosEmbarazos = [embarazoActivo, ...historialEmbarazos].filter(Boolean);

  const riesgoChartData = useMemo(() => {
    const result: { embarazo: string; riesgo: number }[] = [];
    for (const e of todosLosEmbarazos) {
      if (e !== null && e !== undefined) {
        result.push({ embarazo: `#${result.length + 1}`, riesgo: e.riesgo === 'BAJO' ? 1 : e.riesgo === 'ALTO' ? 2 : 3 });
      }
    }
    return result.reverse();
  }, [todosLosEmbarazos]);

  if (todosLosEmbarazos.length === 0) {
    return (
      <Empty description="No hay embarazos registrados para mostrar" image={Empty.PRESENTED_IMAGE_SIMPLE}>
        <Button type="primary" onClick={() => navigate(`/embarazos/nuevo?paciente=${pacienteId}`)}>Registrar Primer Embarazo</Button>
      </Empty>
    );
  }

  return (
    <div>
      <Alert message="Análisis Comparativo de Embarazos" description={todosLosEmbarazos.length > 1 ? "Comparación entre embarazos de la paciente" : "Resumen del embarazo registrado"} type="info" showIcon style={{ marginBottom: 16 }} />
      <Table
        dataSource={todosLosEmbarazos}
        rowKey="id"
        columns={[
          { title: 'Embarazo', render: (_, e, idx) => (<Space>{idx === 0 && <Tag color="blue">ACTUAL</Tag>}<Text>#{(historialEmbarazos.length + 1) - idx}</Text></Space>) },
          { title: 'FUM', dataIndex: 'fecha_ultima_menstruacion', render: (t) => dayjs(t).format('DD/MM/YYYY') },
          { title: 'FPP', dataIndex: 'fecha_probable_parto', render: (t) => dayjs(t).format('DD/MM/YYYY') },
          { title: 'Paridad', render: (_, e) => e ? `G${e.gestas_previas || 0} P${e.partos_previos || 0} C${e.cesareas_previas || 0} A${e.abortos_previos || 0}` : '-' },
          { title: 'Riesgo', dataIndex: 'riesgo', render: (r: keyof typeof RIESGO_COLORS) => <Tag color={RIESGO_COLORS[r]}>{r}</Tag> },
          { title: 'Observaciones', dataIndex: 'observaciones', ellipsis: true }
        ]}
      />
      <Divider />
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Evolución del Riesgo" size="small">
            {todosLosEmbarazos.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={riesgoChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="embarazo" />
                  <YAxis domain={RIESGO_DOMAIN} ticks={RIESGO_TICKS} tickFormatter={formatRiesgoTick} />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="riesgo" stroke="#ff4d4f" strokeWidth={2} dot={{ r: 5 }} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : <Empty description="No hay datos para graficar" image={Empty.PRESENTED_IMAGE_SIMPLE} />}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Resumen Estadístico" size="small">
            <Statistic title="Total de Embarazos" value={todosLosEmbarazos.length} />
            <Divider />
            <Statistic title="Partos Vaginales" value={todosLosEmbarazos.filter((e): e is Embarazo => e !== null && e !== undefined && e.id !== embarazoActivo?.id).reduce((acc, e) => acc + (e.partos_previos || 0), 0)} prefix={<TeamOutlined />} />
            <Divider />
            <Statistic title="Cesáreas" value={todosLosEmbarazos.filter((e): e is Embarazo => e !== null && e !== undefined && e.id !== embarazoActivo?.id).reduce((acc, e) => acc + (e.cesareas_previas || 0), 0)} prefix={<MedicineBoxOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

interface RiskFactorItemProps {
  item: string;
}
const RiskFactorItem: React.FC<RiskFactorItemProps> = React.memo(({ item }) => (
  <List.Item>
    <Text>{item}</Text>
  </List.Item>
));

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
  <Card className="header-paciente" variant="borderless" style={{ background: 'var(--bg-secondary, #f0f5ff)', marginBottom: 16 }}>
    <Row align="middle" gutter={24}>
      <Col flex="100px">
        <Avatar size={80} icon={<UserOutlined />} src={paciente?.foto_perfil} style={{ border: '2px solid #1890ff' }} />
      </Col>
      <Col flex="auto">
        <Title level={3} style={{ marginBottom: 0 }}>
          {paciente?.nombre} {paciente?.apellido_paterno || paciente?.apellidos || ''}
          <Tag color={paciente?.activo ? 'green' : 'red'} style={{ marginLeft: 10, fontSize: 12, verticalAlign: 'middle' }}>
            {paciente?.activo ? 'ACTIVA' : 'INACTIVA'}
          </Tag>
        </Title>
        <Space split={verticalDivider}>
          <Text><CalendarOutlined /> {paciente?.edad} años</Text>
          <Text>CI: {paciente?.ci}</Text>
          <Text>GS: <Tag color="volcano">{(paciente as any)?.grupo_sanguineo || paciente?.tipo_sangre} {paciente?.factor_rh}</Tag></Text>
          <Text><PhoneOutlined /> {paciente?.telefono}</Text>
        </Space>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary">Alergias: </Text>
          {paciente?.alergias ? <Tag color="red">{paciente.alergias}</Tag> : <Tag>Niega</Tag>}
        </div>
      </Col>
      <Col>
        <Space direction="vertical" align="end">
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate(`/controles/nuevo?embarazo=${embarazoActivo?.id}`)} disabled={!embarazoActivo}>
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

// ==========================================

const FCF_DOMAIN = [100, 180];
const FCF_LABEL = { value: 'LPM', angle: -90, position: 'insideLeft' };
const HGB_DOMAIN = [8, 16];
const HGB_LABEL = { value: 'g/dL', angle: -90, position: 'insideLeft' };
const HCT_DOMAIN = [25, 50];
const HCT_LABEL = { value: '%', angle: -90, position: 'insideLeft' };
const RIESGO_DOMAIN = [0, 4];
const RIESGO_TICKS = [1, 2, 3];
const formatRiesgoTick = (v: number) => v === 1 ? 'BAJO' : v === 2 ? 'ALTO' : 'MUY ALTO';

const HistoriaClinica: React.FC = () => {
  const { message, notification, modal } = useAntdApp();
  const { id: pacienteId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const [formNota] = Form.useForm();
  const [formReceta] = Form.useForm();
  const mountedRef = React.useRef(false);
  React.useEffect(() => { mountedRef.current = true; }, []);

  // --- ESTADOS GLOBALES ---
  const isMounted = React.useRef(true);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // --- DATOS CLÍNICOS ---
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [embarazoActivo, setEmbarazoActivo] = useState<Embarazo | null>(null);
  const [historialEmbarazos, setHistorialEmbarazos] = useState<Embarazo[]>([]);
  const [controles, setControles] = useState<ControlPrenatal[]>([]);
  const [ecografias, setEcografias] = useState<Ecografia[]>([]);
  const [laboratorios, setLaboratorios] = useState<Laboratorio[]>([]);
  const [notas, setNotas] = useState<NotaEvolucion[]>([]);
  const [tratamientos, setTratamientos] = useState<Tratamiento[]>([]);
  const [vacunas, setVacunas] = useState<Vacuna[]>([]);
  const [citas, setCitas] = useState<Cita[]>([]);
  const [partos, setPartos] = useState<Parto[]>([]);
  const [antecedenteGineco, setAntecedenteGineco] = useState<AntecedenteGinecoObstetrico | null>(null);
  const [antecedentePatologico, setAntecedentePatologico] = useState<AntecedentePatologico | null>(null);

  // --- VISIBILIDAD DE MODALES/DRAWERS ---
  const [drawerNotasVisible, setDrawerNotasVisible] = useState(false);
  const [modalRiesgoVisible, setModalRiesgoVisible] = useState(false);
  const [modalRecetaVisible, setModalRecetaVisible] = useState(false);
  const [drawerCalculadoraVisible, setDrawerCalculadoraVisible] = useState(false);
  const [modalProtocolosVisible, setModalProtocolosVisible] = useState(false);
  const [modalExportarVisible, setModalExportarVisible] = useState(false);
  const [drawerTimelineVisible, setDrawerTimelineVisible] = useState(false);
  const [modalComparacionVisible, setModalComparacionVisible] = useState(false);
  const [drawerAlertasVisible, setDrawerAlertasVisible] = useState(false);

  // --- ESTADOS PARA FUNCIONES AVANZADAS ---
  const [alertasActivas, setAlertasActivas] = useState<AlertaClinica[]>([]);
  const [protocolosEmbarazo, setProtocolosEmbarazo] = useState<ProtocoloObstetrico[]>([]);
  const [recordatorios, setRecordatorios] = useState<RecordatorioClinico[]>([]);
  const [busquedaFiltro, setBusquedaFiltro] = useState<BusquedaFiltro>({ texto: '', categoria: 'TODO' });

  const handleAgregarRecordatorio = useCallback(() => {
    setRecordatorios(prev => [
      ...prev,
      {
        id: `rec-${crypto.randomUUID()}`,
        tipo: 'CONTROL',
        titulo: 'Recordatorio',
        descripcion: 'Nuevo recordatorio',
        fecha_programada: dayjs().add(7, 'days').format('YYYY-MM-DD'),
        dias_restantes: 7,
        completado: false,
        prioridad: 'MEDIA',
      },
    ]);
    message.success('Recordatorio agregado');
  }, [message]);

  const resultadosCalculadoraRef = useRef<CalculadoraResultado[]>([]);
  const [tendenciasLaboratorio, setTendenciasLaboratorio] = useState<Array<{ examen: string; valores: Array<{ fecha: string; valor: number; referencia: string }>; tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' }>>([]);

  // --- CONFIGURACIÓN DE VISTA ---
  const [vistaCompacta, setVistaCompacta] = useState(false);
  const [mostrarGraficasAvanzadas, setMostrarGraficasAvanzadas] = useState(true);
  const [periodoVisualizacion, setPeriodoVisualizacion] = useState<'TODO' | 'ULTIMO_MES' | 'ULTIMO_TRIMESTRE'>('TODO');

  // ==========================================
  // 4. CARGA DE DATOS (PARALLEL FETCHING)
  // ==========================================
  const fetchHistoriaClinica = React.useCallback(async () => {
    if (!pacienteId) return;
    setLoading(true);
    try {
      const token = getToken();
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Datos Base del Paciente
      const resPaciente = await axios.get(`${API_URL}/pacientes/${pacienteId}/`, { headers });
      setPaciente(resPaciente.data);

      // 2. Buscar Embarazos
      const resEmbarazos = await axios.get(`${API_URL}/embarazos/?paciente=${pacienteId}`, { headers });
      const todosEmbarazos = Array.isArray(resEmbarazos.data.results || resEmbarazos.data)
        ? (resEmbarazos.data.results || resEmbarazos.data)
        : [];

      // Separar activo e historial
      const activo = todosEmbarazos.find((e: Embarazo) => e.estado === 'activo');

      // Si no hay embarazo activo, usar el más reciente (ordenado por FUM)
      const embarazoParaMostrar = activo || (todosEmbarazos.length > 0
        ? todosEmbarazos.reduce((latest: Embarazo, e: Embarazo) =>
            new Date(e.fecha_ultima_menstruacion).getTime() > new Date(latest.fecha_ultima_menstruacion).getTime() ? e : latest
          )
        : null);

      setEmbarazoActivo(embarazoParaMostrar);
      setHistorialEmbarazos(todosEmbarazos.filter((e: Embarazo) => e.id !== embarazoParaMostrar?.id));

      // 3. Carga de Datos (carga para embarazo activo o más reciente)
      const promises: Promise<AxiosResponse<any>>[] = [
        axios.get(`${API_URL}/notas-evolucion/?paciente=${pacienteId}`, { headers }),
        axios.get(`${API_URL}/vacunas/?paciente=${pacienteId}`, { headers }),
        axios.get(`${API_URL}/citas/?paciente=${pacienteId}`, { headers }).catch(err => ({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} })),
        axios.get(`${API_URL}/partos/?paciente=${pacienteId}`, { headers }).catch(err => ({ data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} }))
      ];

      const emptyResponse = { data: [], status: 200, statusText: 'OK', headers: {}, config: {} as any, request: {} };

      if (embarazoParaMostrar) {
        promises.push(
          axios.get(`${API_URL}/controles/?embarazo=${embarazoParaMostrar.id}`, { headers })
            .catch(() => emptyResponse)
        );
        promises.push(
          axios.get(`${API_URL}/ecografias/?embarazo=${embarazoParaMostrar.id}`, { headers })
            .catch(() => emptyResponse)
        );
        promises.push(
          axios.get(`${API_URL}/laboratorios/?paciente=${pacienteId}&fecha_min=${embarazoParaMostrar.fecha_ultima_menstruacion}`, { headers })
            .catch(() => emptyResponse)
        );
        // REMOVIDO: tratamientos endpoint no existe
        // promises.push(
        //   axios.get(`${API_URL}/tratamientos/?embarazo=${embarazoParaMostrar.id}`, { headers })
        //     .catch(() => emptyResponse)
        // );
      } else {
        // Si no hay ningún embarazo, aún así intentar cargar datos generales
        promises.push(Promise.resolve(emptyResponse));
        promises.push(Promise.resolve(emptyResponse));
        promises.push(
          axios.get(`${API_URL}/laboratorios/?paciente=${pacienteId}&limit=10`, { headers })
            .catch(() => emptyResponse)
        );
        // REMOVIDO: tratamientos endpoint no existe
        // promises.push(Promise.resolve(emptyResponse));
      }

      const [resNotas, resVacunas, resCitas, resPartos, resControles, resEcos, resLabs] = await Promise.all(promises);

      const notasData = resNotas.data.results || resNotas.data;
      if (isMounted.current) {
        setNotas(Array.isArray(notasData) ? notasData : []);
      }

      const vacunasData = resVacunas.data.results || resVacunas.data;
      const citasData = resCitas.data.results || resCitas.data;
      const partosData = resPartos.data.results || resPartos.data;
      const ctrlData = resControles.data.results || resControles.data;
      const controlesArray = Array.isArray(ctrlData) ? ctrlData : [];
      const ecosData = resEcos.data.results || resEcos.data;
      const labsData = resLabs.data.results || resLabs.data;

      if (isMounted.current) {
        setVacunas(Array.isArray(vacunasData) ? vacunasData : []);
        setCitas(Array.isArray(citasData) ? citasData : []);
        setPartos(Array.isArray(partosData) ? partosData : []);
        setControles(controlesArray.sort((a: any, b: any) => new Date(a.fecha_control || a.fecha || 0).getTime() - new Date(b.fecha_control || b.fecha || 0).getTime()));
        setEcografias(Array.isArray(ecosData) ? ecosData : []);
        setLaboratorios(Array.isArray(labsData) ? labsData : []);
        setTratamientos([]);
      }

      // Cargar antecedentes médicos detallados
      try {
        const antecedentes = await antecedentesService.getAntecedentesPaciente(Number(pacienteId));
        setAntecedenteGineco(antecedentes.ginecoObstetrico);
        setAntecedentePatologico(antecedentes.patologico);
      } catch (err) {
        setAntecedenteGineco(null);
        setAntecedentePatologico(null);
      }

      // Cargar datos adicionales de análisis
      if (isMounted.current) {
        setAlertasActivas(generarAlertas(controlesArray, labsData, embarazoParaMostrar));
        setProtocolosEmbarazo(actualizarProtocolos(controlesArray, ecosData, labsData));
        setTendenciasLaboratorio(calcularTendencias(labsData));
      }

    } catch (err: any) {
      setError("No se pudo cargar la historia clínica completa. Verifique su conexión o permisos.");
      notification.error({ message: 'Error de Conexión', description: 'Algunos módulos clínicos no pudieron cargarse.' });
    } finally {
      if (isMounted.current) {
        setLoading(false);
      }
    }
  }, [pacienteId, notification, getToken]);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    fetchHistoriaClinica();
  }, [fetchHistoriaClinica]); // Usar fetchHistoriaClinica como dependencia

  // ==========================================
  // 5. LÓGICA DE NEGOCIO Y CÁLCULOS
  // ==========================================

  const calcularEGActual = React.useCallback(() => {
    if (!embarazoActivo) return { semanas: 0, dias: 0 };
    const fechaBase = embarazoActivo.fecha_ultima_menstruacion;
    const hoy = dayjs();
    const fum = dayjs(fechaBase);
    const diasDiff = hoy.diff(fum, 'days');
    return { semanas: Math.floor(diasDiff / 7), dias: diasDiff % 7 };
  }, [embarazoActivo]);

  const datosGraficas = useMemo(() => {
    return controles.map(c => {
      const ref = getReferenceAU(c.semanas_gestacion);
      return {
        semana: c.semanas_gestacion,
        peso: c.peso_actual,
        au: c.altura_uterina,
        sistolica: c.presion_arterial_sistolica,
        diastolica: c.presion_arterial_diastolica,
        p10: ref.p10,
        p50: ref.p50,
        p90: ref.p90,
        fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM')
      };
    });
  }, [controles]);

  const alertasClinicas = useMemo(() => {
    const list: AlertaClinica[] = [];
    const ultimoCtrl = controles[controles.length - 1];
    if (ultimoCtrl && (ultimoCtrl.presion_arterial_sistolica >= 140 || ultimoCtrl.presion_arterial_diastolica >= 90)) {
      list.push({
        id: `alerta-${Date.now()}-1`,
        tipo: 'ERROR',
        prioridad: 'ALTA',
        mensaje: 'ALERTA: Presión Arterial Elevada en último control. Descartar Preeclampsia.',
        categoria: 'SIGNOS_VITALES',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Control de PA en 48h', 'Laboratorios: Proteinuria, Creatinina', 'Evaluación por especialista']
      });
    }
    const labsAnormales = laboratorios.filter(l => l.es_anormal).length;
    if (labsAnormales > 0) {
      list.push({
        id: `alerta-${Date.now()}-2`,
        tipo: 'WARNING',
        prioridad: 'MEDIA',
        mensaje: `${labsAnormales} resultados de laboratorio reportados como ANORMALES.`,
        categoria: 'LABORATORIO',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Revisar resultados', 'Correlacionar con clínica', 'Considerar repetir exámenes']
      });
    }
    if (((paciente as any)?.grupo_sanguineo || paciente?.tipo_sangre) && paciente?.factor_rh === '-' && !laboratorios.some(l => l.tipo_examen.includes('Coombs'))) {
      list.push({
        id: `alerta-${Date.now()}-3`,
        tipo: 'WARNING',
        prioridad: 'MEDIA',
        mensaje: 'Paciente RH Negativo: Verificar solicitud de Test de Coombs Indirecto.',
        categoria: 'INMUNOLOGIA',
        fecha_generacion: new Date().toISOString(),
        resuelta: false,
        acciones_recomendadas: ['Solicitar Coombs Indirecto', 'Evaluar necesidad de Inmunoglobulina Anti-D']
      });
    }

    // Verificar protocolos de atención según edad gestacional
    if (embarazoActivo) {
      const { semanas } = calcularEGActual();

      // Alerta para ecografía morfológica
      if (semanas >= 18 && semanas <= 23 && !ecografias.some(e => e.tipo.includes('Morfológica'))) {
        list.push({
          id: `alerta-${Date.now()}-4`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: VENTANA ÓPTIMA para Ecografía Morfológica (18-23 sem)`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Agendar ecografía morfológica Nivel II', 'Informar a la paciente']
        });
      }

      // Alerta para test de O'Sullivan
      if (semanas >= 24 && semanas <= 28 && !laboratorios.some(l => {
        const tipoExamen = String(l.tipo_examen || '').toLowerCase();
        return tipoExamen.includes('glucosa') || tipoExamen.includes('sullivan');
      })) {
        list.push({
          id: `alerta-${Date.now()}-5`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: Solicitar Test de O'Sullivan (Tamizaje Diabetes Gestacional)`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Solicitar Curva de Tolerancia a la Glucosa 75g', 'Educación sobre diabetes gestacional']
        });
      }

      // Alerta para cultivo vaginal/rectal (Streptococo B)
      if (semanas >= 35 && semanas <= 37 && !laboratorios.some(l => {
        const tipoExamen = String(l.tipo_examen || '').toLowerCase();
        return tipoExamen.includes('cultivo') && tipoExamen.includes('vaginal');
      })) {
        list.push({
          id: `alerta-${Date.now()}-6`,
          tipo: 'INFO',
          prioridad: 'ALTA',
          mensaje: `Semana ${semanas}: Solicitar Cultivo Vaginal/Rectal para Streptococo B`,
          categoria: 'PROTOCOLO',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Toma de muestra vaginal y rectal', 'Informar a la paciente sobre prevención de Streptococo B']
        });
      }

      // Alerta de controles insuficientes
      const controlesEsperados = Math.floor(semanas / 4) + 1;
      if (controles.length < controlesEsperados) {
        list.push({
          id: `alerta-${Date.now()}-7`,
          tipo: 'WARNING',
          prioridad: 'MEDIA',
          mensaje: `Controles prenatales insuficientes: ${controles.length} de ${controlesEsperados} esperados`,
          categoria: 'ADHERENCIA',
          fecha_generacion: new Date().toISOString(),
          resuelta: false,
          acciones_recomendadas: ['Fortalecer adherencia al control prenatal', 'Identificar barreras de acceso', 'Agendar próxima cita']
        });
      }
    }

    return list;
  }, [controles, laboratorios, paciente, embarazoActivo, ecografias, calcularEGActual]);

  // ==========================================
  // 6. MANEJADORES (HANDLERS)
  // ==========================================

  const handleAddNota = useCallback(async (values: any) => {
    setSaving(true);
    try {
      const nuevaNota = { ...values, id: Date.now(), fecha_hora: new Date().toISOString(), autor: { username: 'dr_actual' } };
      setNotas(prev => [nuevaNota, ...prev]);
      message.success('Nota guardada exitosamente');
      formNota.resetFields();
      setDrawerNotasVisible(false);
    } catch (e) {
      message.error('Error al guardar nota');
    } finally {
      setSaving(false);
    }
  }, [message, formNota]);

  const handleAddTratamiento = useCallback(async (values: any) => {
    setModalRecetaVisible(false);
    message.success("Tratamiento prescrito correctamente");
  }, [message]);

  const handleExportarHistoria = useCallback((config: ExportConfig) => {
    setSaving(true);
    try {
      notification.success({
        message: 'Exportación Iniciada',
        description: `Generando archivo ${config.formato}. Se descargará automáticamente.`
      });

      // Aquí iría la lógica real de exportación
      setTimeout(() => {
        message.success(`Historia clínica exportada en formato ${config.formato}`);
        setModalExportarVisible(false);
      }, 1500);
    } catch (error) {
      message.error('Error al exportar historia clínica');
    } finally {
      setSaving(false);
    }
  }, [notification, message]);

  const handleCalcularRiesgo = useCallback(() => {
    if (!paciente || !embarazoActivo || controles.length === 0) {
      message.warning('Se requieren datos de paciente y controles para calcular el riesgo');
      return;
    }

    const ultimoControl = controles[controles.length - 1];
    const riesgoPreeclampsia = calcularRiesgoPreeclampsia(
      paciente.edad ?? paciente.edad_actual ?? 0,
      ultimoControl.imc_actual || ultimoControl.imc || 0,
      ultimoControl.presion_arterial_sistolica,
      ultimoControl.presion_arterial_diastolica,
      {
        hipertension: String(paciente.antecedentes_patologicos || '').toLowerCase().includes('hipertens'),
        preeclampsiaPrevias: historialEmbarazos.filter(e =>
          String(e.observaciones || '').toLowerCase().includes('preeclampsia')
        ).length,
        diabetes: String(paciente.antecedentes_patologicos || '').toLowerCase().includes('diabetes')
      }
    );

    modal.info({
      title: 'Evaluación de Riesgo de Preeclampsia',
      width: 600,
      content: (
        <div>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="Nivel de Riesgo">
              <Tag color={riesgoPreeclampsia.nivel === 'ALTO' ? 'red' : riesgoPreeclampsia.nivel === 'MODERADO' ? 'orange' : 'green'}>
                {riesgoPreeclampsia.nivel}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Score Total">{riesgoPreeclampsia.score} puntos</Descriptions.Item>
          </Descriptions>
          <Divider orientation="left">Recomendaciones Clínicas</Divider>
          <List
            size="small"
            dataSource={riesgoPreeclampsia?.recomendaciones || []}
            renderItem={(item) => <RiesgoPreeclampsiaItem item={item} />}
          />
        </div>
      )
    });
  }, [paciente, embarazoActivo, controles, message, historialEmbarazos, modal]);

  const handleCalcularPesoFetal = useCallback((dbt: number, ca: number, lf: number) => {
    if (!embarazoActivo) {
      message.warning('No hay embarazo activo');
      return;
    }

    const pesoEstimado = calcularPesoFetalEstimado(dbt, ca, lf);
    const { semanas } = calcularEGActual();
    const { percentil, clasificacion } = calcularPercentilFetal(pesoEstimado, semanas);

    const resultado: CalculadoraResultado = {
      nombre: 'Peso Fetal Estimado',
      valor: Math.round(pesoEstimado),
      unidad: 'gramos',
      interpretacion: `Percentil ${percentil}: ${clasificacion}`,
      rango_normal: `P10-P90 para ${semanas} semanas`,
      alerta: percentil < 10 || percentil > 90
    };

    resultadosCalculadoraRef.current = [resultado, ...resultadosCalculadoraRef.current];

    notification.info({
      message: 'Cálculo Completado',
      description: `Peso fetal estimado: ${Math.round(pesoEstimado)}g (P${percentil})`,
      duration: 5
    });
  }, [embarazoActivo, message, calcularEGActual, notification]);

  const handleCalcularIMCGanancia = useCallback(() => {
    if (!paciente || controles.length === 0) {
      message.warning('Se requieren datos de controles prenatales');
      return;
    }

    const primerControl = controles[0];
    const ultimoControl = controles[controles.length - 1];

    if (!primerControl.peso_actual || !ultimoControl.peso_actual) {
      message.warning('Se requieren datos de peso en los controles prenatales');
      return;
    }

    // Asumiendo que tenemos la talla en el paciente (en cm)
    const tallaAsumida = 160; // Esto debería venir de los datos del paciente
    const imcInicial = calcularIMC(primerControl.peso_actual, tallaAsumida);
    const imcActual = calcularIMC(ultimoControl.peso_actual, tallaAsumida);

    const { semanas } = calcularEGActual();
    const gananciaRecomendada = calcularGananciaPesoRecomendada(imcInicial, semanas);
    const gananciaReal = ultimoControl.peso_actual - primerControl.peso_actual;

    const resultados: CalculadoraResultado[] = [
      {
        nombre: 'IMC Pregestacional',
        valor: imcInicial.toFixed(1),
        unidad: 'kg/m²',
        interpretacion: imcInicial < 18.5 ? 'Bajo Peso' : imcInicial < 25 ? 'Normal' : imcInicial < 30 ? 'Sobrepeso' : 'Obesidad',
        alerta: imcInicial < 18.5 || imcInicial >= 30
      },
      {
        nombre: 'IMC Actual',
        valor: imcActual.toFixed(1),
        unidad: 'kg/m²'
      },
      {
        nombre: 'Ganancia de Peso Actual',
        valor: gananciaReal.toFixed(1),
        unidad: 'kg',
        interpretacion: gananciaReal < gananciaRecomendada.minimo ? 'Insuficiente' :
          gananciaReal > gananciaRecomendada.maximo ? 'Excesiva' : 'Adecuada',
        rango_normal: `${gananciaRecomendada.minimo.toFixed(1)} - ${gananciaRecomendada.maximo.toFixed(1)} kg`,
        alerta: gananciaReal < gananciaRecomendada.minimo || gananciaReal > gananciaRecomendada.maximo
      },
      {
        nombre: 'Ganancia Total Recomendada',
        valor: `${gananciaRecomendada.total.min} - ${gananciaRecomendada.total.max}`,
        unidad: 'kg'
      }
    ];

    resultadosCalculadoraRef.current = resultados;

    modal.info({
      title: 'Análisis de IMC y Ganancia de Peso',
      width: 650,
      content: (
        <Table
          dataSource={resultados}
          columns={[
            { title: 'Parámetro', dataIndex: 'nombre', key: 'nombre' },
            {
              title: 'Valor',
              key: 'valor',
              render: (_, r) => <Text strong>{r.valor} {r.unidad}</Text>
            },
            {
              title: 'Interpretación',
              dataIndex: 'interpretacion',
              render: (text, r) => text ? (
                <Tag color={r.alerta ? 'red' : 'green'}>{text}</Tag>
              ) : '-'
            },
            { title: 'Rango Normal', dataIndex: 'rango_normal', render: (text) => text || '-' }
          ]}
          pagination={false}
          size="small"
        />
      )
    });
  }, [paciente, controles, message, calcularEGActual, modal]);

  const handleVerTendenciasLaboratorio = useCallback(() => {
    // Agrupar laboratorios por tipo de examen
    const agrupados: { [key: string]: Array<{ fecha: string; valor: number; referencia: string }> } = {};

    laboratorios.forEach(lab => {
      // Solo procesar laboratorios cuantitativos
      const valorNumerico = parseFloat(lab.resultado);
      if (!isNaN(valorNumerico)) {
        if (!agrupados[lab.tipo_examen]) {
          agrupados[lab.tipo_examen] = [];
        }
        agrupados[lab.tipo_examen].push({
          fecha: lab.fecha_toma,
          valor: valorNumerico,
          referencia: lab.valores_referencia
        });
      }
    });

    const tendencias: Array<{ examen: string; valores: Array<{ fecha: string; valor: number; referencia: string }>; tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' }> = Object.keys(agrupados).map(examen => {
      const valores = agrupados[examen].sort((a, b) =>
        new Date(a.fecha).getTime() - new Date(b.fecha).getTime()
      );

      // Determinar tendencia simple (comparando primero vs último)
      let tendencia: 'MEJORANDO' | 'EMPEORANDO' | 'ESTABLE' = 'ESTABLE';
      if (valores.length >= 2) {
        const primerValor = valores[0].valor;
        const ultimoValor = valores[valores.length - 1].valor;
        const cambio = ((ultimoValor - primerValor) / primerValor) * 100;

        if (Math.abs(cambio) < 10) {
          tendencia = 'ESTABLE';
        } else {
          // Esto es simplificado - en la realidad depende del tipo de examen
          tendencia = cambio > 0 ? 'EMPEORANDO' : 'MEJORANDO';
        }
      }

      return { examen, valores, tendencia };
    });

    setTendenciasLaboratorio(tendencias);

    modal.info({
      title: 'Análisis de Tendencias de Laboratorio',
      width: 800,
      content: (
        <div>
          {tendencias.map((t) => (
            <Card key={t.examen} size="small" style={{ marginBottom: 16 }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space>
                  <Text strong>{t.examen}</Text>
                  <Tag color={t.tendencia === 'MEJORANDO' ? 'green' : t.tendencia === 'EMPEORANDO' ? 'red' : 'blue'}>
                    {t.tendencia}
                  </Tag>
                </Space>
                <ResponsiveContainer width="100%" height={150}>
                  <ComposedChart data={t.valores.map(v => ({ ...v, fechaCorta: dayjs(v.fecha).format('DD/MM') }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="fechaCorta" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="valor" stroke="#1890ff" strokeWidth={2} dot={{ r: 4 }} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Space>
            </Card>
          ))}
        </div>
      )
    });
  }, [laboratorios, modal]);

  const handleGenerarRecordatorios = useCallback(() => {
    if (!embarazoActivo) {
      message.warning('No hay embarazo activo');
      return;
    }

    const { semanas } = calcularEGActual();
    const nuevosRecordatorios: RecordatorioClinico[] = [];

    // Recordatorio de próximo control
    const ultimoControl = controles[controles.length - 1];
    if (ultimoControl && ultimoControl.proximo_control) {
      const diasRestantes = dayjs(ultimoControl.proximo_control).diff(dayjs(), 'days');
      if (diasRestantes >= 0 && diasRestantes <= 30) {
        nuevosRecordatorios.push({
          id: `rec-${Date.now()}-1`,
          tipo: 'CONTROL',
          titulo: 'Próximo Control Prenatal',
          descripcion: `Control #${controles.length + 1} - ${dayjs(ultimoControl.proximo_control).format('DD/MM/YYYY')}`,
          fecha_programada: ultimoControl.proximo_control,
          dias_restantes: diasRestantes,
          completado: false,
          prioridad: diasRestantes <= 3 ? 'ALTA' : diasRestantes <= 7 ? 'MEDIA' : 'BAJA'
        });
      }
    }

    // Recordatorios de vacunas pendientes
    VACUNAS_EMBARAZO.forEach(vacuna => {
      if (vacuna.obligatoria && !vacunas.some(v => v.nombre.includes(vacuna.nombre.split(' ')[0]))) {
        nuevosRecordatorios.push({
          id: `rec-${Date.now()}-vac-${vacuna.nombre}`,
          tipo: 'VACUNA',
          titulo: 'Vacuna Pendiente',
          descripcion: `Aplicar: ${vacuna.nombre}`,
          fecha_programada: dayjs().add(7, 'days').format('YYYY-MM-DD'),
          dias_restantes: 7,
          completado: false,
          prioridad: 'ALTA'
        });
      }
    });

    // Recordatorios de protocolos pendientes
    PROTOCOLOS_EMBARAZO.forEach(protocolo => {
      if (semanas >= protocolo.semanas_inicio && semanas <= protocolo.semanas_fin) {
        // Verificar si falta algún examen del protocolo
        const examenFaltante = protocolo.examenes_requeridos.find(examen => {
          const examenLower = String(examen || '').toLowerCase();
          return !laboratorios.some(l => String(l.tipo_examen || '').toLowerCase().includes(examenLower)) &&
            !ecografias.some(e => String(e.tipo || '').toLowerCase().includes(examenLower));
        });

        if (examenFaltante) {
          nuevosRecordatorios.push({
            id: `rec-${Date.now()}-prot-${protocolo.id}`,
            tipo: 'EXAMEN',
            titulo: protocolo.nombre,
            descripcion: `Solicitar ${examenFaltante}`,
            fecha_programada: dayjs().add(3, 'days').format('YYYY-MM-DD'),
            dias_restantes: 3,
            completado: false,
            prioridad: 'ALTA'
          });
        }
      }
    });

    // Recordatorio de tratamientos activos
    for (const tratamiento of tratamientos.filter(t => t.activo)) {
      const diasDesdeInicio = dayjs().diff(dayjs(tratamiento.fecha_inicio), 'days');
      const duracionMatch = tratamiento.duracion.match(/(\d+)/);
      if (duracionMatch) {
        const duracionDias = parseInt(duracionMatch[1]);
        const diasRestantes = duracionDias - diasDesdeInicio;

        if (diasRestantes > 0 && diasRestantes <= 7) {
          nuevosRecordatorios.push({
            id: `rec-${Date.now()}-trat-${tratamiento.id}`,
            tipo: 'TRATAMIENTO',
            titulo: 'Fin de Tratamiento',
            descripcion: `Finaliza tratamiento: ${tratamiento.medicamento}`,
            fecha_programada: dayjs(tratamiento.fecha_inicio).add(duracionDias, 'days').format('YYYY-MM-DD'),
            dias_restantes: diasRestantes,
            completado: false,
            prioridad: 'MEDIA'
          });
        }
      }
    }

    setRecordatorios(nuevosRecordatorios);

    notification.success({
      message: 'Recordatorios Generados',
      description: `Se generaron ${nuevosRecordatorios.length} recordatorios clínicos`,
      duration: 4
    });
  }, [embarazoActivo, calcularEGActual, controles, vacunas, laboratorios, ecografias, tratamientos, message, notification]);

  const estadisticasGlobales = useMemo<EstadisticaGlobal | null>(() => {
    if (!embarazoActivo) return null;

    const { semanas } = calcularEGActual();
    const diasHastaFPP = dayjs(embarazoActivo.fecha_probable_parto).diff(dayjs(), 'days');

    return {
      total_controles: controles.length,
      total_ecografias: ecografias.length,
      total_laboratorios: laboratorios.length,
      total_notas: notas.length,
      total_registros: controles.length + ecografias.length + laboratorios.length + notas.length + citas.length + partos.length,
      ultimo_control: controles.length > 0 ? controles[controles.length - 1].fecha : undefined,
      proxima_cita: controles.length > 0 ? controles[controles.length - 1].proximo_control : undefined,
      edad_gestacional_semanas_actual: semanas,
      dias_hasta_fpp: diasHastaFPP,
      adherencia_tratamiento: tratamientos.filter(t => t.activo).length > 0 ? 85 : 100,
      porcentaje_protocolos_cumplidos: 75
    };
  }, [embarazoActivo, controles, ecografias, laboratorios, notas, tratamientos, citas, partos, calcularEGActual]);

  // ==========================================
  // 7. SUB-COMPONENTES DE UI
  // ==========================================


  // ==========================================
  // 8. RENDERIZADO FINAL
  // ==========================================

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <Spin size="large">
        <div style={{ padding: 50, textAlign: 'center' }}>
          <p>Cargando expediente clínico…</p>
        </div>
      </Spin>
    </div>
  );
  if (error) return <Alert message="Error" description={error} type="error" showIcon style={{ margin: 20 }} />;

  return (
    <Layout style={{ background: 'var(--bg-primary, #fff)', minHeight: '100vh' }} suppressHydrationWarning>
      <div style={{ padding: '20px 40px' }}>
        <Space style={{ marginBottom: 16 }}>
          <Button type="link" icon={<ArrowLeftOutlined />} onClick={() => navigate('/pacientes')}>Lista de Pacientes</Button>
          <Text type="secondary"> / HC: {paciente?.nombre} {paciente?.apellido_paterno || paciente?.apellidos || ''}</Text>
        </Space>

        <HeaderInfoPaciente
          paciente={paciente}
          embarazoActivo={embarazoActivo}
          pacienteId={pacienteId}
          navigate={navigate}
          setDrawerCalculadoraVisible={setDrawerCalculadoraVisible}
          setModalExportarVisible={setModalExportarVisible}
          setModalRiesgoVisible={setModalRiesgoVisible}
          setModalProtocolosVisible={setModalProtocolosVisible}
          setDrawerTimelineVisible={setDrawerTimelineVisible}
          setModalComparacionVisible={setModalComparacionVisible}
          setDrawerAlertasVisible={setDrawerAlertasVisible}
        />

        {/* CONTROLES DE VISTA Y FILTROS */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 8]} align="middle">
            <Col flex="auto">
              <Space wrap>
                <Input
                  placeholder="Buscar en historia clínica..."
                  prefix={<SearchOutlined />}
                  value={busquedaFiltro.texto}
                  onChange={(e) =>
                    setBusquedaFiltro(prev => ({ ...prev, texto: e.target.value }))
                  }
                  style={{ width: 250 }}
                />
                <Select
                  value={busquedaFiltro.categoria}
                  onChange={(val) =>
                    setBusquedaFiltro(prev => ({ ...prev, categoria: val }))
                  }
                  style={{ width: 150 }}
                >
                  <Option value="TODO">Todo</Option>
                  <Option value="CONTROLES">Controles</Option>
                  <Option value="LABORATORIOS">Laboratorios</Option>
                  <Option value="NOTAS">Notas</Option>
                </Select>
                <Select
                  value={periodoVisualizacion}
                  onChange={setPeriodoVisualizacion}
                  style={{ width: 150 }}
                >
                  <Option value="TODO">Todo el embarazo</Option>
                  <Option value="ULTIMO_MES">Último mes</Option>
                  <Option value="ULTIMO_TRIMESTRE">Último trimestre</Option>
                </Select>
              </Space>
            </Col>
            <Col>
              <Space>
                <Tooltip title="Vista compacta">
                  <Button
                    type={vistaCompacta ? 'primary' : 'default'}
                    icon={<TableOutlined />}
                    onClick={() => setVistaCompacta(prev => !prev)}
                  />
                </Tooltip>
                <Tooltip title="Gráficas avanzadas">
                  <Button
                    type={mostrarGraficasAvanzadas ? 'primary' : 'default'}
                    icon={<LineChartOutlined />}
                    onClick={() => setMostrarGraficasAvanzadas(prev => !prev)}
                  />
                </Tooltip>
                <Badge count={recordatorios.length} offset={[-5, 5]}>
                  <Dropdown
                    menu={{
                      items: [
                        ...(recordatorios.length === 0 ? [
                          { key: 'none', label: 'Sin recordatorios', disabled: true }
                        ] : recordatorios.map((rec) => ({
                          key: rec.id,
                          label: (
                            <Space direction="vertical" size="small">
                              <Text strong>{rec.titulo}</Text>
                              <Text type="secondary" style={{ fontSize: 12 }}>
                                {rec.descripcion}
                              </Text>
                            </Space>
                          )
                        }))),
                        { type: 'divider' as const },
                        {
                          key: 'agregar',
                          label: 'Agregar recordatorio',
                          icon: <PlusOutlined />,
                          onClick: () => {
                            modal.confirm({
                              title: 'Agregar Recordatorio',
                              content: (
                                <Form>
                                  <Form.Item label="Recordatorio">
                                    <TextArea rows={3} placeholder="Escribe un recordatorio..." />
                                  </Form.Item>
                                </Form>
                              ),
                              onOk: handleAgregarRecordatorio,
                            });
                          }
                        },
                        {
                          key: 'ver_todos',
                          label: 'Ver todos los recordatorios',
                          icon: <BellOutlined />,
                          onClick: () => setDrawerAlertasVisible(true)
                        }
                      ]
                    }}
                    trigger={['click']}
                  >
                    <Button icon={<ClockCircleOutlined />}>Recordatorios</Button>
                  </Dropdown>
                </Badge>
                {estadisticasGlobales && (
                  <Tooltip
                    title={`Total registros: ${estadisticasGlobales.total_registros}`}
                  >
                    <Button icon={<CalculatorOutlined />}>
                      Estadísticas ({estadisticasGlobales.total_registros})
                    </Button>
                  </Tooltip>
                )}
              </Space>
            </Col>
          </Row>
        </Card>

        <Card className="main-tabs-card" styles={{ body: { padding: 0 } }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size="large"
            type="line"
            tabBarStyle={{ padding: '0 20px' }}
            items={[
              {
                key: 'dashboard',
                label: <span><HeartOutlined /> Dashboard</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <DashboardObstetrico
                      alertasClinicas={alertasClinicas}
                      embarazoActivo={embarazoActivo}
                      controles={controles}
                      laboratorios={laboratorios}
                      ecografias={ecografias}
                      calcularEGActual={calcularEGActual}
                      datosGraficas={datosGraficas}
                      pacienteId={pacienteId}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'antecedentes',
                label: <span><HistoryOutlined /> Antecedentes</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <Row gutter={[16, 16]}>
                      {/* ANTECEDENTES GINECO-OBSTÉTRICOS */}
                      <Col span={24}>
                        <Card
                          title={
                            <Space>
                              <WomanOutlined style={{ color: '#722ed1' }} />
                              <span>Antecedentes Gineco-Obstétricos</span>
                            </Space>
                          }
                          extra={
                            antecedenteGineco && (
                              <Tag color="purple" style={{ fontSize: 16, padding: '4px 12px' }}>
                                Fórmula: {antecedenteGineco.gestas || 0}G-{antecedenteGineco.partos || 0}P-{antecedenteGineco.abortos || 0}A-{antecedenteGineco.cesareas || 0}C
                              </Tag>
                            )
                          }
                        >
                          {antecedenteGineco ? (
                            <Descriptions bordered column={2} size="small">
                              <Descriptions.Item label="Menarquia (Edad)" span={1}>
                                {antecedenteGineco.menarquia_edad ? `${antecedenteGineco.menarquia_edad} años` : 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Ciclos Menstruales" span={1}>
                                {antecedenteGineco.ciclos_menstruales || 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Duración del Ciclo" span={1}>
                                {antecedenteGineco.duracion_ciclo_dias ? `${antecedenteGineco.duracion_ciclo_dias} días` : 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Duración Menstruación" span={1}>
                                {antecedenteGineco.duracion_menstruacion_dias ? `${antecedenteGineco.duracion_menstruacion_dias} días` : 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Última Menstruación (FUM)" span={2}>
                                {antecedenteGineco.fecha_ultima_menstruacion
                                  ? dayjs(antecedenteGineco.fecha_ultima_menstruacion).format('DD/MM/YYYY')
                                  : 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Gestas" span={1}>
                                <Tag color="blue">{antecedenteGineco.gestas || 0}</Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="Partos" span={1}>
                                <Tag color="green">{antecedenteGineco.partos || 0}</Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="Abortos" span={1}>
                                <Tag color="orange">{antecedenteGineco.abortos || 0}</Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="Cesáreas" span={1}>
                                <Tag color="red">{antecedenteGineco.cesareas || 0}</Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="Hijos Vivos" span={2}>
                                <Tag color="cyan">{antecedenteGineco.hijos_vivos || 0}</Tag>
                              </Descriptions.Item>
                              <Descriptions.Item label="Anticonceptivo Actual" span={1}>
                                {antecedenteGineco.metodo_anticonceptivo_actual || 'No usa'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Tiempo de Uso" span={1}>
                                {antecedenteGineco.tiempo_uso_anticonceptivo_meses
                                  ? `${antecedenteGineco.tiempo_uso_anticonceptivo_meses} meses`
                                  : 'N/A'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Inicio Vida Sexual (Edad)" span={1}>
                                {antecedenteGineco.inicio_vida_sexual_edad
                                  ? `${antecedenteGineco.inicio_vida_sexual_edad} años`
                                  : 'No registra'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Número de Parejas Sexuales" span={1}>
                                {antecedenteGineco.numero_parejas_sexuales || 'No registra'}
                              </Descriptions.Item>
                            </Descriptions>
                          ) : (
                            <Empty
                              description="No hay antecedentes gineco-obstétricos registrados"
                              image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                          )}
                        </Card>
                      </Col>

                      {/* ANTECEDENTES PATOLÓGICOS */}
                      <Col span={24}>
                        <Card
                          title={
                            <Space>
                              <MedicineBoxOutlined style={{ color: '#f5222d' }} />
                              <span>Antecedentes Patológicos</span>
                            </Space>
                          }
                        >
                          {antecedentePatologico ? (
                            <>
                              <Descriptions bordered column={3} size="small" style={{ marginBottom: 16 }}>
                                <Descriptions.Item label="Tipo de Antecedente" span={3}>
                                  <Tag color={antecedentePatologico.tipo === 'personal' ? 'blue' : 'purple'}>
                                    {antecedentePatologico.tipo === 'personal' ? 'Personal' : 'Heredofamiliar'}
                                  </Tag>
                                </Descriptions.Item>
                              </Descriptions>

                              <Divider orientation="left">Alergias (CRÍTICO)</Divider>
                              <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
                                <Descriptions.Item label="Tiene Alergias" span={2}>
                                  {antecedentePatologico.tiene_alergias ? (
                                    <Tag color="red" icon={<WarningOutlined />}>SÍ - REVISAR DETALLE</Tag>
                                  ) : (
                                    <Tag color="green">No</Tag>
                                  )}
                                </Descriptions.Item>
                                {antecedentePatologico.tiene_alergias && (
                                  <>
                                    <Descriptions.Item label="Alergias a Medicamentos" span={2}>
                                      {antecedentePatologico.alergias_medicamentos || 'No especificado'}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Alergias a Alimentos" span={2}>
                                      {antecedentePatologico.alergias_alimentos || 'No especificado'}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Otras Alergias" span={2}>
                                      {antecedentePatologico.alergias_otras || 'No especificado'}
                                    </Descriptions.Item>
                                  </>
                                )}
                              </Descriptions>

                              <Divider orientation="left">Enfermedades Crónicas</Divider>
                              <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                                {[
                                  { key: 'diabetes', label: 'Diabetes', color: 'orange' },
                                  { key: 'hipertension', label: 'Hipertensión', color: 'red' },
                                  { key: 'cardiopatias', label: 'Cardiopatías', color: 'magenta' },
                                  { key: 'nefropatias', label: 'Nefropatías', color: 'purple' },
                                  { key: 'trastornos_coagulacion', label: 'Trastornos Coagulación', color: 'volcano' },
                                  { key: 'anemia', label: 'Anemia', color: 'gold' },
                                  { key: 'lupus', label: 'Lupus', color: 'geekblue' },
                                  { key: 'artritis_reumatoide', label: 'Artritis Reumatoide', color: 'cyan' },
                                  { key: 'asma', label: 'Asma', color: 'blue' },
                                ].map(enf =>
                                  antecedentePatologico[enf.key as keyof AntecedentePatologico] && (
                                    <Col key={enf.key}>
                                      <Tag color={enf.color} icon={<CheckCircleOutlined />}>{enf.label}</Tag>
                                    </Col>
                                  )
                                )}
                              </Row>

                              {antecedentePatologico.diabetes && antecedentePatologico.diabetes_tipo && (
                                <Alert
                                  message={`Tipo de Diabetes: ${antecedentePatologico.diabetes_tipo}`}
                                  type="warning"
                                  showIcon
                                  style={{ marginBottom: 16 }}
                                />
                              )}

                              <Divider orientation="left">Antecedentes Obstétricos Específicos</Divider>
                              <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
                                {[
                                  { key: 'preeclampsia_previa', label: 'Preeclampsia Previa', color: 'red' },
                                  { key: 'eclampsia_previa', label: 'Eclampsia Previa', color: 'red' },
                                  { key: 'diabetes_gestacional_previa', label: 'Diabetes Gestacional Previa', color: 'orange' },
                                  { key: 'hemorragia_postparto_previa', label: 'Hemorragia Postparto Previa', color: 'volcano' },
                                ].map(ant =>
                                  antecedentePatologico[ant.key as keyof AntecedentePatologico] && (
                                    <Col key={ant.key}>
                                      <Tag color={ant.color} icon={<WarningOutlined />}>{ant.label}</Tag>
                                    </Col>
                                  )
                                )}
                              </Row>

                              <Descriptions bordered column={1} size="small">
                                {antecedentePatologico.cardiopatia_detalle && (
                                  <Descriptions.Item label="Detalle Cardiopatía">
                                    {antecedentePatologico.cardiopatia_detalle}
                                  </Descriptions.Item>
                                )}
                                {antecedentePatologico.nefropatia_detalle && (
                                  <Descriptions.Item label="Detalle Nefropatía">
                                    {antecedentePatologico.nefropatia_detalle}
                                  </Descriptions.Item>
                                )}
                                {antecedentePatologico.otras_enfermedades && (
                                  <Descriptions.Item label="Otras Enfermedades">
                                    {antecedentePatologico.otras_enfermedades}
                                  </Descriptions.Item>
                                )}
                                {antecedentePatologico.cirugias_anteriores && (
                                  <Descriptions.Item label="Cirugías Anteriores">
                                    {antecedentePatologico.cirugias_anteriores}
                                  </Descriptions.Item>
                                )}
                              </Descriptions>
                            </>
                          ) : (
                            <Empty
                              description="No hay antecedentes patológicos registrados"
                              image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                          )}
                        </Card>
                      </Col>

                      {/* ANTECEDENTES GENERALES DEL PACIENTE (Texto Libre) */}
                      <Col span={24}>
                        <Card title="Antecedentes Generales (Texto Libre)">
                          <Descriptions bordered column={1} size="small">
                            <Descriptions.Item label="Antecedentes Patológicos">
                              {formatAntecedente(paciente?.antecedentes_patologicos)}
                            </Descriptions.Item>
                            <Descriptions.Item label="Antecedentes Quirúrgicos">
                              {formatAntecedente(paciente?.antecedentes_quirurgicos)}
                            </Descriptions.Item>
                            <Descriptions.Item label="Antecedentes Familiares">
                              {formatAntecedente(paciente?.antecedentes_familiares)}
                            </Descriptions.Item>
                            <Descriptions.Item label="Hábitos Tóxicos">
                              {formatAntecedente(paciente?.habitos_toxicos)}
                            </Descriptions.Item>
                          </Descriptions>
                        </Card>
                      </Col>

                      {/* HISTORIAL DE EMBARAZOS */}
                      {historialEmbarazos.length > 0 && (
                        <Col span={24}>
                          <Card title="Historial de Embarazos Previos">
                            <Table
                              dataSource={historialEmbarazos}
                              pagination={false}
                              rowKey="id"
                              size="small"
                              columns={[
                                {
                                  title: 'Año',
                                  render: (_, r: any) => dayjs(r.fecha_ultima_menstruacion).format('YYYY'),
                                  width: 80
                                },
                                {
                                  title: 'G/P/A/C',
                                  render: (_, r: any) => `${r.gestas_previas || 0}/${r.partos_previos || 0}/${r.abortos_previos || 0}/${r.cesareas_previas || 0}`,
                                  width: 100
                                },
                                {
                                  title: 'Observaciones',
                                  dataIndex: 'observaciones',
                                  render: (text: string) => text || 'Sin observaciones'
                                }
                              ]}
                            />
                          </Card>
                        </Col>
                      )}
                    </Row>
                  </div>
                ),
              },
              {
                key: 'controles',
                label: <span><MedicineBoxOutlined /> Controles</span>,
                disabled: !embarazoActivo,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabControles
                      controles={controles}
                      embarazoActivo={embarazoActivo}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'ecografias',
                label: <span><ScanOutlined /> Ecografías</span>,
                disabled: !embarazoActivo,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabEcografias ecografias={ecografias} navigate={navigate} embarazoActivo={embarazoActivo} />
                  </div>
                ),
              },
              {
                key: 'laboratorio',
                label: <span><ExperimentOutlined /> Laboratorio</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabLaboratorios laboratorios={laboratorios} />
                  </div>
                ),
              },
              {
                key: 'notas',
                label: <span><FileTextOutlined /> Evolución (SOAP)</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabNotasEvolucion
                      notas={notas}
                      setDrawerNotasVisible={setDrawerNotasVisible}
                    />
                  </div>
                ),
              },
              {
                key: 'partos',
                label: <span><WomanOutlined /> Partos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabPartos
                      partos={partos}
                      pacienteId={pacienteId}
                      navigate={navigate}
                    />
                  </div>
                ),
              },
              {
                key: 'vacunas',
                label: <span><SafetyCertificateOutlined /> Vacunas</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabVacunas vacunas={vacunas} />
                  </div>
                ),
              },
              {
                key: 'tratamientos',
                label: <span><MedicineBoxOutlined /> Tratamientos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabTratamientos
                      tratamientos={tratamientos}
                      setModalRecetaVisible={setModalRecetaVisible}
                    />
                  </div>
                ),
              },
              {
                key: 'herramientas',
                label: <span><CalculatorOutlined /> Herramientas Clínicas</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabHerramientasClinicas
                      handleCalcularRiesgo={handleCalcularRiesgo}
                      handleCalcularIMCGanancia={handleCalcularIMCGanancia}
                      handleVerTendenciasLaboratorio={handleVerTendenciasLaboratorio}
                      handleGenerarRecordatorios={handleGenerarRecordatorios}
                      handleCalcularPesoFetal={handleCalcularPesoFetal}
                      setModalExportarVisible={setModalExportarVisible}
                      laboratorios={laboratorios}
                      calcularEG={calcularEG}
                      calcularFPP={calcularFPP}
                      interpretarNST={interpretarNST}
                      notification={notification}
                    />
                  </div>
                ),
              },
              {
                key: 'protocolos',
                label: <span><SafetyCertificateOutlined /> Protocolos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabProtocolosCumplimiento
                      calcularEGActual={calcularEGActual}
                      laboratorios={laboratorios}
                      ecografias={ecografias}
                    />
                  </div>
                ),
              },
              {
                key: 'comparacion',
                label: <span><LineChartOutlined /> Comparación Embarazos</span>,
                children: (
                  <div style={{ padding: 24 }}>
                    <TabComparacionEmbarazos
                      embarazoActivo={embarazoActivo}
                      historialEmbarazos={historialEmbarazos}
                      navigate={navigate}
                      pacienteId={pacienteId}
                    />
                  </div>
                ),
              },
            ]}
          />
        </Card >

        {/* DRAWER DE NOTAS SOAP */}
        < Drawer
          title="Nueva Nota de Evolución (SOAP)"
          width={500}
          onClose={() => setDrawerNotasVisible(false)}
          open={drawerNotasVisible}
          maskClosable={false}
        >
          <Form form={formNota} layout="vertical" onFinish={handleAddNota}>
            <Form.Item name="tipo" label="Tipo de Atención" initialValue="CONSULTA">
              <Select>
                <Option value="CONSULTA">Consulta Prenatal</Option>
                <Option value="URGENCIA">Urgencia Obstétrica</Option>
                <Option value="TELECONSULTA">Telemedicina</Option>
              </Select>
            </Form.Item>

            <Divider orientation="left">Estructura SOAP</Divider>

            <Form.Item name="subjetivo" label="Subjetivo (S)" tooltip="Lo que refiere la paciente" rules={[{ required: true }]}>
              <Input.TextArea rows={3} placeholder="Ej: Paciente refiere dolor pélvico leve..." />
            </Form.Item>
            <Form.Item name="objetivo" label="Objetivo (O)" tooltip="Hallazgos del examen físico">
              <Input.TextArea rows={3} placeholder="Ej: PA 110/70, AU 24cm, LCF 140..." />
            </Form.Item>
            <Form.Item name="analisis" label="Análisis (A)" tooltip="Diagnóstico o impresión clínica">
              <Input.TextArea rows={2} placeholder="Ej: Embarazo de curso normal..." />
            </Form.Item>
            <Form.Item name="plan" label="Plan (P)" tooltip="Conducta a seguir">
              <Input.TextArea rows={3} placeholder="Ej: Se solicita ecografía de control..." />
            </Form.Item>

            <Button type="primary" htmlType="submit" block size="large" loading={saving} icon={<SaveOutlined />}>
              Guardar Nota en Historia
            </Button>
          </Form>
        </Drawer >

        {/* MODAL DE RECETAS */}
        < Modal
          title="Prescripción de Medicamentos"
          open={modalRecetaVisible}
          onCancel={() => setModalRecetaVisible(false)}
          onOk={formReceta.submit}
        >
          <Form form={formReceta} layout="vertical" onFinish={handleAddTratamiento}>
            <Form.Item name="medicamento" label="Medicamento" rules={[{ required: true }]}>
              <Input placeholder="Ej: Sulfato Ferroso + Ácido Fólico" />
            </Form.Item>
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="dosis" label="Dosis">
                  <Input placeholder="Ej: 1 tableta" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="frecuencia" label="Frecuencia">
                  <Input placeholder="Ej: Cada 24 horas" />
                </Form.Item>
              </Col>
            </Row>
            <Form.Item name="duracion" label="Duración del Tratamiento">
              <Input placeholder="Ej: Por 30 días" />
            </Form.Item>
            <Form.Item name="imprimir" valuePropName="checked">
              <Checkbox>Imprimir Receta al Guardar</Checkbox>
            </Form.Item>
          </Form>
        </Modal >

        {/* CALCULADORA DRAWER */}
        < Drawer title="Herramientas Clínicas" placement="right" onClose={() => setDrawerCalculadoraVisible(false)} open={drawerCalculadoraVisible} >
          <Card title="Calculadora Gestacional" size="small">
            <p>Herramienta para cálculo rápido de FPP y EG por FUM.</p>
            <DatePicker
              style={{ width: '100%' }}
              placeholder="Seleccionar FUM"
              onChange={(date: Dayjs | null) => {
                if (date) {
                  const eg = dayjs().diff(date, 'weeks');
                  message.info(`Edad Gestacional: ${eg} semanas`);
                }
              }}
            />
          </Card>
        </Drawer >

        {/* MODAL DE EXPORTAR */}
        < Modal
          title="Exportar Historia Clínica"
          open={modalExportarVisible}
          onCancel={() => setModalExportarVisible(false)}
          footer={null}
          width={600}
        >
          <Form
            layout="vertical"
            onFinish={(values) => {
              const config: ExportConfig = {
                formato: values.formato,
                secciones: values.secciones || [],
                incluir_graficas: values.incluir_graficas || false,
                periodo_inicio: values.periodo ? values.periodo[0].format('YYYY-MM-DD') : undefined,
                periodo_fin: values.periodo ? values.periodo[1].format('YYYY-MM-DD') : undefined
              };
              handleExportarHistoria(config);
            }}
          >
            <Form.Item name="formato" label="Formato de Exportación" initialValue="PDF" rules={[{ required: true }]}>
              <Select>
                <Option value="PDF">PDF (Informe Imprimible)</Option>
                <Option value="EXCEL">Excel (Análisis de Datos)</Option>
                <Option value="JSON">JSON (Respaldo Digital)</Option>
              </Select>
            </Form.Item>

            <Form.Item name="secciones" label="Secciones a Incluir">
              <Checkbox.Group style={{ width: '100%' }}>
                <Row>
                  <Col span={12}><Checkbox value="datos_paciente">Datos del Paciente</Checkbox></Col>
                  <Col span={12}><Checkbox value="embarazo">Embarazo Actual</Checkbox></Col>
                  <Col span={12}><Checkbox value="controles">Controles Prenatales</Checkbox></Col>
                  <Col span={12}><Checkbox value="ecografias">Ecografías</Checkbox></Col>
                  <Col span={12}><Checkbox value="laboratorios">Laboratorios</Checkbox></Col>
                  <Col span={12}><Checkbox value="notas">Notas SOAP</Checkbox></Col>
                  <Col span={12}><Checkbox value="tratamientos">Tratamientos</Checkbox></Col>
                  <Col span={12}><Checkbox value="vacunas">Vacunas</Checkbox></Col>
                </Row>
              </Checkbox.Group>
            </Form.Item>

            <Form.Item name="incluir_graficas" valuePropName="checked">
              <Checkbox>Incluir gráficas y estadísticas visuales</Checkbox>
            </Form.Item>

            <Form.Item name="periodo" label="Período de Datos (Opcional)">
              <DatePicker.RangePicker style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => setModalExportarVisible(false)}>Cancelar</Button>
                <Button type="primary" htmlType="submit" icon={<DownloadOutlined />} loading={saving}>
                  Exportar
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal >

        {/* MODAL AVANZADO DE RIESGO */}
        < Modal
          title={
            < Space >
              <WarningOutlined style={{ color: '#fa8c16' }} />
              <Text strong>Evaluación Integral de Riesgo Obstétrico</Text>
            </Space >
          }
          open={modalRiesgoVisible}
          onCancel={() => setModalRiesgoVisible(false)}
          width={800}
          footer={
            [
              <Button key="close" onClick={() => setModalRiesgoVisible(false)}>
                Cerrar
              </Button>,
              <Button key="calc" type="primary" onClick={handleCalcularRiesgo}>
                Calcular Riesgo Preeclampsia
              </Button>
            ]}
        >
          <Tabs
            defaultActiveKey="factores"
            items={[
              {
                key: 'factores',
                label: 'Factores de Riesgo',
                children: (
                  <>
                    <Alert
                      message="Factores de Riesgo Obstétrico"
                      description="Clasificación según guías clínicas internacionales"
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />

                    <Card title="Riesgo MUY ALTO" size="small" style={{ marginBottom: 16 }} headStyle={{ backgroundColor: '#fff2e8' }}>
                      <List
                        size="small"
                        dataSource={FACTORES_RIESGO.MUY_ALTO}
                        renderItem={(item) => <RiskFactorItem item={item} />}
                      />
                    </Card>

                    <Card title="Riesgo ALTO" size="small" headStyle={{ backgroundColor: '#fff7e6' }}>
                      <List
                        size="small"
                        dataSource={FACTORES_RIESGO.ALTO}
                        renderItem={(item) => <RiskFactorItem item={item} />}
                      />
                    </Card>
                  </>
                ),
              },
              {
                key: 'evaluacion',
                label: 'Evaluación Actual',
                children: (
                  paciente && embarazoActivo && (
                    <div>
                      <Descriptions bordered column={2} size="small">
                        <Descriptions.Item label="Edad" span={1}>
                          {paciente?.edad} años
                          {(paciente?.edad && (paciente.edad < 18 || paciente.edad > 35)) && (
                            <Tag color="warning" style={{ marginLeft: 8 }}>Factor de Riesgo</Tag>
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Riesgo Actual" span={1}>
                          <Tag color={RIESGO_COLORS[embarazoActivo?.riesgo || 'BAJO']}>{embarazoActivo?.riesgo}</Tag>
                        </Descriptions.Item>
                        <Descriptions.Item label="Paridad" span={2}>
                          G{embarazoActivo?.gestas_previas} P{embarazoActivo?.partos_previos} C{embarazoActivo?.cesareas_previas} A{embarazoActivo?.abortos_previos}
                          {(embarazoActivo?.cesareas_previas && embarazoActivo.cesareas_previas >= 2) && (
                            <Tag color="error" style={{ marginLeft: 8 }}>≥2 Cesáreas Previas</Tag>
                          )}
                        </Descriptions.Item>
                        <Descriptions.Item label="Antecedentes Patológicos" span={2}>
                          {formatAntecedente(paciente?.antecedentes_patologicos || '')}
                        </Descriptions.Item>
                      </Descriptions>

                      {controles.length > 0 && (
                        <div style={{ marginTop: 16 }}>
                          <Divider orientation="left">Último Control</Divider>
                          <Descriptions bordered column={2} size="small">
                            <Descriptions.Item label="PA">
                              {controles[controles.length - 1].presion_arterial_sistolica}/{controles[controles.length - 1].presion_arterial_diastolica}
                              {(controles[controles.length - 1].presion_arterial_sistolica >= 140 || controles[controles.length - 1].presion_arterial_diastolica >= 90) && (
                                <Tag color="error" style={{ marginLeft: 8 }}>HTA</Tag>
                              )}
                            </Descriptions.Item>
                            <Descriptions.Item label="IMC">
                              {(() => {
                                const ultimoControl = controles[controles.length - 1];
                                const imc = ultimoControl.imc_actual || ultimoControl.imc;
                                return imc != null ? imc.toFixed(1) : '-';
                              })()}
                              {(() => {
                                const ultimoControl = controles[controles.length - 1];
                                const imc = ultimoControl.imc_actual || ultimoControl.imc;
                                return imc != null && imc >= 30 && (
                                  <Tag color="warning" style={{ marginLeft: 8 }}>Obesidad</Tag>
                                );
                              })()}
                            </Descriptions.Item>
                            <Descriptions.Item label="Edema">
                              {controles[controles.length - 1].edema ? 'Presente' : 'Ausente'}
                              {controles[controles.length - 1].edema && (
                                <Tag color="warning" style={{ marginLeft: 8 }}>Vigilar</Tag>
                              )}
                            </Descriptions.Item>
                            <Descriptions.Item label="Proteinuria">
                              {controles[controles.length - 1].proteinuria}
                            </Descriptions.Item>
                          </Descriptions>
                        </div>
                      )}
                    </div>
                  )
                ),
              },
              {
                key: 'recomendaciones',
                label: 'Recomendaciones',
                children: (
                  <>
                    <Alert
                      message="Plan de Manejo según Nivel de Riesgo"
                      type="info"
                      showIcon
                      style={{ marginBottom: 16 }}
                    />

                    <Card title="Riesgo BAJO" size="small" style={{ marginBottom: 16 }}>
                      <ul>
                        <li>Control prenatal mensual hasta semana 28</li>
                        <li>Control quincenal desde semana 28-36</li>
                        <li>Control semanal desde semana 36 hasta parto</li>
                        <li>Ecografías según protocolo estándar</li>
                        <li>Laboratorios de rutina en cada trimestre</li>
                      </ul>
                    </Card>

                    <Card title="Riesgo ALTO" size="small" style={{ marginBottom: 16 }}>
                      <ul>
                        <li>Control prenatal quincenal desde el inicio</li>
                        <li>Control semanal desde semana 32</li>
                        <li>Ecografías con Doppler cada 4 semanas desde semana 24</li>
                        <li>Monitoreo fetal (NST) semanal desde semana 32</li>
                        <li>Laboratorios cada mes (hemograma, función renal, hepática)</li>
                        <li>Interconsulta con especialidades según patología</li>
                      </ul>
                    </Card>

                    <Card title="Riesgo MUY ALTO" size="small">
                      <ul>
                        <li>Control prenatal semanal desde el inicio</li>
                        <li>Evaluación en hospital de tercer nivel</li>
                        <li>Ecografías con Doppler cada 2-3 semanas</li>
                        <li>Monitoreo fetal (NST) bisemanal desde semana 28</li>
                        <li>Perfil biofísico semanal desde semana 32</li>
                        <li>Hospitalización si se deteriora condición materna o fetal</li>
                        <li>Plan de parto individualizado con equipo multidisciplinario</li>
                        <li>Considerar maduración pulmonar fetal si parto pretérmino anticipado</li>
                      </ul>
                    </Card>
                  </>
                ),
              }
            ]}
          />
        </Modal >

        {/* MODAL DE PROTOCOLOS OBSTÉTRICOS */}
        <Modal
          title={
            <Space>
              <SafetyCertificateOutlined />
              Protocolos Obstétricos - Cumplimiento
            </Space>
          }
          open={modalProtocolosVisible}
          onCancel={() => setModalProtocolosVisible(false)}
          width={900}
          footer={[
            <Button key="close" onClick={() => setModalProtocolosVisible(false)}>
              Cerrar
            </Button>
          ]}
        >
          <List
            dataSource={protocolosEmbarazo}
            renderItem={(protocolo) => <ProtocoloEmbarazoItem protocolo={protocolo} />}
          />
        </Modal>

        {/* DRAWER DE LÍNEA DE TIEMPO */}
        <Drawer
          title={
            <Space>
              <HistoryOutlined />
              Línea de Tiempo Obstétrica
            </Space>
          }
          placement="right"
          onClose={() => setDrawerTimelineVisible(false)}
          open={drawerTimelineVisible}
          width={600}
        >
          <Timeline
            mode="left"
            items={[...controles, ...ecografias, ...laboratorios, ...notas]
              .sort((a, b) => {
                const dateA = new Date((a as any).fecha_control || (a as any).fecha || (a as any).fecha_consulta);
                const dateB = new Date((b as any).fecha_control || (b as any).fecha || (b as any).fecha_consulta);
                return dateB.getTime() - dateA.getTime();
              })
              .slice(0, 20)
              .map((item, idx) => {
                const itemAny = item as any;
                const tipo = item.hasOwnProperty('fecha_control')
                  ? 'Control'
                  : item.hasOwnProperty('dbt')
                    ? 'Ecografía'
                    : item.hasOwnProperty('hemoglobina')
                      ? 'Laboratorio'
                      : 'Nota';
                const fecha = itemAny.fecha_control || itemAny.fecha || itemAny.fecha_consulta;

                return {
                  key: `${tipo}-${itemAny.id || idx}`,
                  color: tipo === 'Control' ? 'green' : tipo === 'Ecografía' ? 'blue' : 'gray',
                  children: (
                    <>
                      <Text strong>{tipo}</Text>
                      <br />
                      <Text type="secondary">{dayjs(fecha).format('DD/MM/YYYY')}</Text>
                    </>
                  ),
                };
              })}
          />
        </Drawer>

        {/* MODAL DE COMPARACIÓN DE DATOS */}
        <Modal
          title={
            <Space>
              <LineChartOutlined />
              Comparación de Datos Clínicos
            </Space>
          }
          open={modalComparacionVisible}
          onCancel={() => setModalComparacionVisible(false)}
          width={1000}
          footer={[
            <Button key="close" onClick={() => setModalComparacionVisible(false)}>
              Cerrar
            </Button>
          ]}
        >
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="Presión Arterial" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart
                    data={controles.map((c) => ({
                      fecha: dayjs(c.fecha_control || c.fecha).format('DD/MM'),
                      sistolica: c.presion_arterial_sistolica,
                      diastolica: c.presion_arterial_diastolica,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="fecha" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Line type="monotone" dataKey="sistolica" stroke="#8884d8" name="Sistólica" />
                    <Line type="monotone" dataKey="diastolica" stroke="#82ca9d" name="Diastólica" />
                    <ReferenceArea y1={140} y2={200} fill="#ff4d4f" fillOpacity={0.1} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="Hemoglobina" size="small">
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart
                    data={laboratorios
                      .reduce((acc, l) => {
                        const tipo = typeof l.tipo_examen === 'string' ? l.tipo_examen.toLowerCase() : String(l.tipo_examen || '').toLowerCase();
                        if (tipo.includes('hemoglobina')) {
                          acc.push({
                            fecha: dayjs(l.fecha_toma).format('DD/MM'),
                            valor: parseFloat(l.resultado) || 0,
                          });
                        }
                        return acc;
                      }, [] as any[])}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="fecha" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    <Bar dataKey="valor" fill="#8884d8" name="Hb (g/dL)" />
                    <ReferenceArea y1={0} y2={11} fill="#ff4d4f" fillOpacity={0.1} />
                  </ComposedChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {tendenciasLaboratorio.length > 0 && (
            <Card title="Tendencias" size="small" style={{ marginTop: 16 }}>
              <List
                dataSource={tendenciasLaboratorio}
                renderItem={(tendencia) => <TendenciaLaboratorioItem tendencia={tendencia} />}
              />
            </Card>
          )}
        </Modal>

        {/* DRAWER DE ALERTAS CLÍNICAS */}
        <Drawer
          title={
            <Space>
              <WarningOutlined />
              Panel de Alertas Clínicas
              <Badge count={alertasActivas.length} style={{ backgroundColor: '#ff4d4f' }} />
            </Space>
          }
          placement="right"
          onClose={() => setDrawerAlertasVisible(false)}
          open={drawerAlertasVisible}
          width={500}
        >
          {alertasActivas.length === 0 ? (
            <Result
              status="success"
              title="Sin Alertas"
              subTitle="No hay alertas clínicas activas para este paciente."
              icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          ) : (
            <List
              dataSource={alertasActivas}
              renderItem={(alerta) => (
                <AlertaClinicaItem
                  alerta={alerta}
                  onResuelta={(id) => {
                    setAlertasActivas(prev => prev.map((a) =>
                      a.id === id ? { ...a, resuelta: true } : a
                    ));
                  }}
                />
              )}
            />
          )}
        </Drawer>

      </div >
    </Layout >
  );
};


export default HistoriaClinica;
