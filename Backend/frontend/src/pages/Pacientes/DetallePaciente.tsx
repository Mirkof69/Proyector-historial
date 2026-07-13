/* eslint-disable react-doctor/prefer-dynamic-import */
import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Descriptions,
  Tabs,
  Button,
  Spin,
  Table,
  Tag,
  Space,
  Alert,
  Typography,
  Divider,
  Row,
  Col,
  Statistic,
  Timeline,
  Empty,
  Tooltip as AntTooltip,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  BarChartOutlined,
  LineChartOutlined,
  DashboardOutlined,
  ArrowLeftOutlined,
  UserOutlined,
  EditOutlined,
  PrinterOutlined,
  MedicineBoxOutlined,
  HeartOutlined,
  FileTextOutlined,
  SafetyOutlined,
  ScanOutlined,
  PhoneOutlined,
  HomeOutlined,
  ExperimentOutlined,
  RobotOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { pacientesService, Paciente } from '../../services/pacientesService';
import { triajeService } from '../../services/triajeService';
import { antecedentesService } from '../../services/antecedentesService';
import { notasEvolucionService } from '../../services/notasEvolucionService';
import { vacunasService } from '../../services/vacunasService';
import { ecografiasService } from '../../services/ecografiasService';
import { Embarazo } from '../../services/embarazosService';
import { FRONTEND_ROUTES } from '../../config/routes';
import dayjs from 'dayjs';
// eslint-disable-next-line react-doctor/prefer-dynamic-import
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend,
  ResponsiveContainer, AreaChart, Area, ComposedChart
} from 'recharts';

const { Title, Text } = Typography;

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];
const renderVacunaLabel = (entry: any) => `${entry.name}: ${entry.value}`;

const getEstadoCivilConGenero = (estadoCivil: string | undefined, genero: string | undefined): string => {
  if (!estadoCivil) return '-';
  const esFemenino = genero === 'femenino';
  switch (estadoCivil) {
    case 'soltero': return esFemenino ? 'Soltera' : 'Soltero';
    case 'casado': return esFemenino ? 'Casada' : 'Casado';
    case 'divorciado': return esFemenino ? 'Divorciada' : 'Divorciado';
    case 'viudo': return esFemenino ? 'Viuda' : 'Viudo';
    case 'union_libre': return 'Unión Libre';
    default: return estadoCivil;
  }
};

const DetallePaciente: React.FC = () => {
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Estados principales
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const loadingRef = useRef(true);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Estados de datos médicos
  const [embarazos, setEmbarazos] = useState<Embarazo[]>([]);
  const [triajes, setTriajes] = useState<any[]>([]);
  const [antecedentes, setAntecedentes] = useState<any[]>([]);
  const [notasEvolucion, setNotasEvolucion] = useState<any[]>([]);
  const [vacunas, setVacunas] = useState<any[]>([]);
  const [ecografias, setEcografias] = useState<any[]>([]);
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  // ✅ Función para mostrar estado civil según género
  const fetchData = async (pacienteId: number) => {
    loadingRef.current = true;
    try {
      // Cargar todos los datos en paralelo
      const [
        pacienteData,
        embarazosData,
        triajesData,
        antecedentesData,
        notasData,
        vacunasData,
        ecografiasData,
      ] = await Promise.all([
        pacientesService.getById(pacienteId),
        pacientesService.getEmbarazos(pacienteId),
        triajeService.listar().then(data => Array.isArray(data) ? data.filter((t: any) => t.paciente === pacienteId) : []),
        antecedentesService.listar().then(data => Array.isArray(data) ? data.filter((a: any) => (a.paciente_id || a.paciente) === pacienteId) : []),
        notasEvolucionService.getNotas({ page_size: 1000 }).then(res => {
          const data = res.results || res;
          return Array.isArray(data) ? data.filter((n: any) => n.paciente === pacienteId) : [];
        }),
        vacunasService.getRegistros({ page_size: 1000 }).then(res => {
          const data = res.results || res;
          return Array.isArray(data) ? data.filter((v: any) => v.paciente === pacienteId) : [];
        }),
        ecografiasService.obtenerPorPaciente(pacienteId),
      ]);

      if (isMounted.current) {
        setPaciente(pacienteData);
        setEmbarazos(Array.isArray(embarazosData) ? embarazosData : []);
        setTriajes(triajesData);
        setAntecedentes(antecedentesData);
        setNotasEvolucion(notasData);
        setVacunas(vacunasData);
        setEcografias(Array.isArray(ecografiasData) ? ecografiasData : (ecografiasData?.results || []));
        message.success('Datos cargados correctamente');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al cargar los datos del paciente');
      }
    } finally {
      if (isMounted.current) {
        loadingRef.current = false;
      }
    }
  };

  useEffect(() => {
    if (id) fetchData(parseInt(id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const handleEdit = () => {
    if (paciente) {
      navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES_EDITAR(paciente.id));
    }
  };

  const handlePrintHistory = async () => {
    if (!paciente) return;
    setLoadingHistory(true);
    try {
      const blob = await pacientesService.getHistoriaClinica(paciente.id);
      if (isMounted.current) {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `Historia_Clinica_${paciente.id_clinico}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.parentNode?.removeChild(link);
        message.success('Historia clínica descargada');
      }
    } catch (error) {
      if (isMounted.current) {
        message.error('Error al generar la historia clínica');
      }
    } finally {
      if (isMounted.current) {
        setLoadingHistory(false);
      }
    }
  };

  // Calcular estadísticas
  const stats = {
    totalEmbarazos: embarazos.length,
    embarazosActivos: embarazos.filter(e => e.estado === 'activo').length,
    totalTriajes: triajes.length,
    totalNotas: notasEvolucion.length,
    totalVacunas: vacunas.length,
    vacunasCompletas: vacunas.filter(v => !v.proxima_dosis_fecha).length,
  };

  // Datos para gráficas
  const getTriajesTimeline = () => {
    return triajes
      .slice(-10)
      .map(t => ({
        fecha: dayjs(t.fecha_hora || t.fecha_registro).format('DD/MM'),
        PA_Sistolica: t.presion_sistolica || 0,
        PA_Diastolica: t.presion_diastolica || 0,
        FC: t.frecuencia_cardiaca || 0,
        Temp: t.temperatura || 0,
      }));
  };

  const getEstadisticasVacunas = () => {
    const conteo: { [key: string]: number } = {};
    vacunas.forEach(v => {
      const tipo = v.tipo_vacuna_nombre || v.tipo_vacuna_info?.nombre || 'Desconocida';
      conteo[tipo] = (conteo[tipo] || 0) + 1;
    });
    return Object.entries(conteo).map(([name, value]) => ({ name, value }));
  };

  const getNotasPorTipo = (tipo: string) => {
    const conteo: { [key: string]: number } = {};
    notasEvolucion.forEach(n => {
      const tipo = n.tipo_consulta || 'otro';
      conteo[tipo] = (conteo[tipo] || 0) + 1;
    });
    return Object.entries(conteo).map(([tipo, cantidad]) => ({ tipo, cantidad }));
  };

  // Columns para tablas
  const columnsEmbarazos = [
    {
      title: 'Gesta',
      dataIndex: 'numero_gesta',
      key: 'numero_gesta',
    },
    {
      title: 'FUM',
      dataIndex: 'fecha_ultima_menstruacion',
      key: 'fecha_ultima_menstruacion',
      render: (text: string) => text ? dayjs(text).format('DD/MM/YYYY') : '-',
    },
    {
      title: 'FPP',
      dataIndex: 'fecha_probable_parto',
      key: 'fecha_probable_parto',
      render: (text: string) => text ? dayjs(text).format('DD/MM/YYYY') : '-',
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        let color = 'default';
        if (estado === 'activo') color = 'green';
        if (estado === 'finalizado') color = 'blue';
        return <Tag color={color}>{estado?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Riesgo',
      dataIndex: 'riesgo_embarazo',
      key: 'riesgo_embarazo',
      render: (riesgo: string) => {
        let color = 'default';
        if (riesgo === 'alto') color = 'red';
        if (riesgo === 'medio') color = 'orange';
        if (riesgo === 'bajo') color = 'green';
        return <Tag color={color}>{riesgo ? riesgo.toUpperCase() : 'NO DEFINIDO'}</Tag>;
      },
    },
  ];

  const columnsTriajes = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_hora',
      key: 'fecha',
      render: (text: string, record: any) => dayjs(text || record.fecha_registro).format('DD/MM/YYYY HH:mm'),
    },
    {
      title: 'Prioridad',
      dataIndex: 'prioridad',
      key: 'prioridad',
      render: (p: string) => {
        const colors: any = { urgente: 'red', alto: 'orange', normal: 'blue', bajo: 'green' };
        return <Tag color={colors[p] || 'default'}>{p?.toUpperCase()}</Tag>;
      },
    },
    {
      title: 'PA',
      render: (_: any, record: any) => `${record.presion_sistolica || '-'}/${record.presion_diastolica || '-'}`,
    },
    {
      title: 'FC',
      dataIndex: 'frecuencia_cardiaca',
      render: (fc: number) => `${fc} bpm`,
    },
    {
      title: 'Temp',
      dataIndex: 'temperatura',
      render: (t: number) => `${t}°C`,
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      render: (e: string) => <Tag color={e === 'completado' ? 'green' : 'orange'}>{e}</Tag>,
    },
  ];

  const columnsNotas = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_consulta',
      render: (f: string) => dayjs(f).format('DD/MM/YYYY'),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_consulta',
      render: (tipo: string) => {
        const labels: any = {
          control_prenatal: 'Control',
          urgencia: 'Urgencia',
          seguimiento: 'Seguimiento',
        };
        return <Tag>{labels[tipo] || tipo}</Tag>;
      },
    },
    {
      title: 'Motivo',
      dataIndex: 'motivo_consulta',
      render: (m: string) => m?.substring(0, 50) + '...',
    },
    {
      title: 'Médico',
      dataIndex: 'medico_nombre',
    },
  ];

  const columnsVacunas = [
    {
      title: 'Fecha',
      dataIndex: 'fecha_aplicacion',
      render: (f: string) => dayjs(f).format('DD/MM/YYYY'),
    },
    {
      title: 'Vacuna',
      dataIndex: 'tipo_vacuna_nombre',
      render: (_: any, record: any) => record.tipo_vacuna_nombre || record.tipo_vacuna_info?.nombre || '-',
    },
    {
      title: 'Dosis',
      dataIndex: 'numero_dosis',
      render: (n: number) => <Tag color="blue">{n}</Tag>,
    },
    {
      title: 'Lote',
      dataIndex: 'lote',
    },
    {
      title: 'Próxima Dosis',
      dataIndex: 'proxima_dosis_fecha',
      render: (f: string) => f ? dayjs(f).format('DD/MM/YYYY') : <Tag color="green">Completo</Tag>,
    },
  ];

  if (loadingRef.current) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" tip="Cargando historial clínico completo del paciente…"><div /></Spin>
      </div>
    );
  }

  if (!paciente) {
    return <Alert message="Paciente no encontrado" type="error" showIcon />;
  }

  return (
    <div style={{ padding: '24px', backgroundColor: '#f0f2f5' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(FRONTEND_ROUTES.DASHBOARD.PACIENTES)}>
            Volver
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            <UserOutlined /> {paciente.nombre_completo}
          </Title>
          <Tag color={paciente.activo ? 'green' : 'red'}>
            {paciente.activo ? 'ACTIVO' : 'INACTIVO'}
          </Tag>
        </Space>
        <Space>
          <Button icon={<EditOutlined />} onClick={handleEdit}>
            Editar
          </Button>
          <Button
            icon={<PrinterOutlined />}
            type="primary"
            onClick={handlePrintHistory}
            loading={loadingHistory}
          >
            Historia Clínica PDF
          </Button>
        </Space>
      </div>

      {/* Estadísticas Generales */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Embarazos"
              value={stats.totalEmbarazos}
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Activos"
              value={stats.embarazosActivos}
              prefix={<HeartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Triajes"
              value={stats.totalTriajes}
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Notas Médicas"
              value={stats.totalNotas}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Vacunas"
              value={stats.totalVacunas}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8} lg={4}>
          <Card>
            <Statistic
              title="Completas"
              value={stats.vacunasCompletas}
              prefix={<SafetyOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Separador de Sección */}
      <Divider orientation="left">
        <Space>
          <ScanOutlined />
          <Text strong>Análisis Gráfico del Expediente</Text>
        </Space>
      </Divider>

      {/* Gráficas de Análisis */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title={<span><LineChartOutlined /> Evolución de Signos Vitales (Últimos Triajes)</span>} bordered={false}>
            {triajes.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={getTriajesTimeline()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" fontSize={12} />
                  <YAxis fontSize={12} />
                  <RechartsTooltip />
                  <Legend />
                  <Line type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" name="PA Sistólica" strokeWidth={2} />
                  <Line type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" name="PA Diastólica" strokeWidth={2} />
                  <Line type="monotone" dataKey="FC" stroke="#52c41a" name="Frecuencia Cardíaca" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Sin triajes registrados" />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={<span><BarChartOutlined /> Distribución de Vacunas</span>} bordered={false}>
            {vacunas.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={getEstadisticasVacunas()}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderVacunaLabel}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {getEstadisticasVacunas().map((entry, index) => (
                      <Cell key={`cell-${entry.name}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Sin vacunas registradas" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Nuevas Gráficas Avanzadas */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title={<span><BarChartOutlined /> Distribución de Notas por Tipo</span>} bordered={false}>
            {notasEvolucion.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getNotasPorTipo('tipo')}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="tipo" fontSize={12} />
                  <YAxis fontSize={12} />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="cantidad" fill="#8884d8" name="Cantidad de Notas" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Sin notas de evolución registradas" />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={<span><DashboardOutlined /> Tendencia de Signos Vitales (Área)</span>} bordered={false}>
            {triajes.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={getTriajesTimeline()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" fontSize={12} />
                  <YAxis fontSize={12} />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" fill="#ff4d4f" fillOpacity={0.3} name="PA Sistólica" />
                  <Area type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" fill="#1890ff" fillOpacity={0.3} name="PA Diastólica" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Sin triajes registrados" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Gráfico Compuesto */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card title={<span><LineChartOutlined /> Análisis Combinado de Signos Vitales y Tendencias</span>} bordered={false}>
            {triajes.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={getTriajesTimeline()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" fontSize={12} />
                  <YAxis fontSize={12} />
                  <RechartsTooltip />
                  <Legend />
                  <Area type="monotone" dataKey="Temperatura" fill="#faad14" stroke="#faad14" fillOpacity={0.2} name="Temperatura (°C)" />
                  <Bar dataKey="FC" fill="#52c41a" name="Frecuencia Cardíaca" />
                  <Line type="monotone" dataKey="PA_Sistolica" stroke="#ff4d4f" strokeWidth={2} name="PA Sistólica" />
                  <Line type="monotone" dataKey="PA_Diastolica" stroke="#1890ff" strokeWidth={2} name="PA Diastólica" />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <Empty description="Sin datos para análisis combinado" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Información del Paciente */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card title={<span><UserOutlined /> Información Personal</span>} bordered={false}>
            <Descriptions bordered column={{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
              <Descriptions.Item label="ID Clínico"><strong>{paciente.id_clinico}</strong></Descriptions.Item>
              <Descriptions.Item label="Cédula de Identidad">{paciente.ci}</Descriptions.Item>
              <Descriptions.Item label="Fecha de Nacimiento">
                {dayjs(paciente.fecha_nacimiento).format('DD/MM/YYYY')} <Tag color="blue">{paciente.edad} años</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Género">{paciente.genero}</Descriptions.Item>
              <Descriptions.Item label="Teléfono">
                <Space>
                  <PhoneOutlined /> {paciente.telefono || '-'}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Email">{paciente.email || '-'}</Descriptions.Item>
              <Descriptions.Item label="Dirección" span={2}>
                <Space>
                  <HomeOutlined /> {paciente.direccion || '-'}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Ciudad">{paciente.ciudad || '-'}</Descriptions.Item>
              <Descriptions.Item label="País">{paciente.pais}</Descriptions.Item>
              <Descriptions.Item label="Estado Civil">
                <Tag color="blue">{getEstadoCivilConGenero(paciente.estado_civil, paciente.genero)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Ocupación">{paciente.ocupacion || '-'}</Descriptions.Item>
              <Descriptions.Item label="Nivel Educativo">{paciente.nivel_educativo || '-'}</Descriptions.Item>
              <Descriptions.Item label="Tipo de Sangre">{paciente.tipo_sangre || '-'}</Descriptions.Item>
              <Descriptions.Item label="Factor RH">{paciente.factor_rh || '-'}</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        <Col span={24}>
          <Card title={<span><HeartOutlined /> Información Médica</span>} bordered={false}>
            <Descriptions bordered column={{ xxl: 4, xl: 3, lg: 3, md: 2, sm: 1, xs: 1 }}>
              <Descriptions.Item label="Peso">
                {paciente.peso_kg ? <Text strong>{paciente.peso_kg} kg</Text> : <Text type="secondary">No registrado</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="Altura">
                {paciente.altura_cm ? <Text strong>{paciente.altura_cm} cm</Text> : <Text type="secondary">No registrado</Text>}
              </Descriptions.Item>
              <Descriptions.Item label="IMC" span={2}>
                {paciente.imc ? (
                  <Space>
                    <Text strong style={{ fontSize: '16px' }}>{paciente.imc.toFixed(1)}</Text>
                    <Tag color={
                      paciente.imc < 18.5 ? 'orange' :
                        paciente.imc < 25 ? 'green' :
                          paciente.imc < 30 ? 'gold' : 'red'
                    }>
                      {paciente.imc < 18.5 ? 'Bajo Peso' :
                        paciente.imc < 25 ? 'Normal' :
                          paciente.imc < 30 ? 'Sobrepeso' : 'Obesidad'}
                    </Tag>
                  </Space>
                ) : (
                  <Text type="secondary">No disponible</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Alergias" span={3}>
                {paciente.alergias || 'Ninguna registrada'}
              </Descriptions.Item>
              <Descriptions.Item label="Enfermedades Crónicas" span={3}>
                {paciente.enfermedades_cronicas || 'Ninguna registrada'}
              </Descriptions.Item>
              <Descriptions.Item label="Contacto Emergencia">
                {paciente.contacto_emergencia_nombre || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Tel. Emergencia">
                {paciente.contacto_emergencia_telefono || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Relación">
                {paciente.contacto_emergencia_relacion || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>

        {/* Historial Médico Completo en Tabs */}
        <Col span={24}>
          <Card bordered={false}>
            <Tabs
              defaultActiveKey="1"
              items={[
                {
                  key: '1',
                  label: (
                    <span>
                      <MedicineBoxOutlined /> Embarazos ({embarazos.length})
                    </span>
                  ),
                  children: (
                    <Table
                      dataSource={embarazos}
                      columns={columnsEmbarazos}
                      rowKey="id"
                      pagination={{ pageSize: 5 }}
                      locale={{ emptyText: <Empty description="No hay embarazos registrados" /> }}
                    />
                  ),
                },
                {
                  key: '2',
                  label: (
                    <span>
                      <DashboardOutlined /> Triajes ({triajes.length})
                    </span>
                  ),
                  children: (
                    <Table
                      dataSource={triajes}
                      columns={columnsTriajes}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      locale={{ emptyText: <Empty description="No hay triajes registrados" /> }}
                    />
                  ),
                },
                {
                  key: '3',
                  label: (
                    <span>
                      <FileTextOutlined /> Notas Médicas ({notasEvolucion.length})
                    </span>
                  ),
                  children: (
                    <Table
                      dataSource={notasEvolucion}
                      columns={columnsNotas}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      locale={{ emptyText: <Empty description="No hay notas de evolución registradas" /> }}
                    />
                  ),
                },
                {
                  key: '4',
                  label: (
                    <span>
                      <SafetyOutlined /> Vacunas ({vacunas.length})
                    </span>
                  ),
                  children: (
                    <Table
                      dataSource={vacunas}
                      columns={columnsVacunas}
                      rowKey="id"
                      pagination={{ pageSize: 10 }}
                      locale={{ emptyText: <Empty description="No hay vacunas registradas" /> }}
                    />
                  ),
                },
                {
                  key: '5',
                  label: (
                    <span>
                      <ExperimentOutlined /> Antecedentes ({antecedentes.length})
                    </span>
                  ),
                  children: antecedentes.length > 0 ? (
                    <Card>
                      <Descriptions bordered column={2}>
                        {antecedentes[0].diabetes !== undefined && (
                          <Descriptions.Item label="Diabetes">
                            <Tag color={antecedentes[0].diabetes ? 'red' : 'green'}>
                              {antecedentes[0].diabetes ? 'Sí' : 'No'}
                            </Tag>
                          </Descriptions.Item>
                        )}
                        {antecedentes[0].hipertension !== undefined && (
                          <Descriptions.Item label="Hipertensión">
                            <Tag color={antecedentes[0].hipertension ? 'red' : 'green'}>
                              {antecedentes[0].hipertension ? 'Sí' : 'No'}
                            </Tag>
                          </Descriptions.Item>
                        )}
                        {antecedentes[0].cardiopatia !== undefined && (
                          <Descriptions.Item label="Cardiopatía">
                            <Tag color={antecedentes[0].cardiopatia ? 'orange' : 'green'}>
                              {antecedentes[0].cardiopatia ? 'Sí' : 'No'}
                            </Tag>
                          </Descriptions.Item>
                        )}
                        {antecedentes[0].alergias && (
                          <Descriptions.Item label="Alergias" span={2}>
                            {antecedentes[0].alergias}
                          </Descriptions.Item>
                        )}
                        {antecedentes[0].medicamentos && (
                          <Descriptions.Item label="Medicamentos" span={2}>
                            {antecedentes[0].medicamentos}
                          </Descriptions.Item>
                        )}
                        {antecedentes[0].quirurgicos && (
                          <Descriptions.Item label="Quirúrgicos" span={2}>
                            {antecedentes[0].quirurgicos}
                          </Descriptions.Item>
                        )}
                      </Descriptions>
                    </Card>
                  ) : (
                    <Empty description="No hay antecedentes registrados" />
                  ),
                },
                {
                  key: '6',
                  label: (
                    <span>
                      <ScanOutlined /> Ecografías ({ecografias.length})
                    </span>
                  ),
                  children: (
                    <Table
                      dataSource={ecografias}
                      columns={[
                        { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
                        { title: 'Fecha', dataIndex: 'fecha_ecografia', key: 'fecha_ecografia', width: 120,
                          render: (f: string) => dayjs(f).format('DD/MM/YYYY') },
                        { title: 'Tipo', dataIndex: 'tipo_ecografia', key: 'tipo_ecografia', width: 150,
                          render: (t: string) => <Tag>{t?.replace(/_/g, ' ')}</Tag> },
                        { title: 'Edad Gestacional', key: 'eg', width: 120,
                          render: (_: any, r: any) => `${r.edad_gestacional_semanas || 0}+${r.edad_gestacional_dias || 0}` },
                        { title: 'Diagnóstico', dataIndex: 'diagnostico', key: 'diagnostico', ellipsis: true },
                        { title: 'IA', key: 'ia', width: 60, align: 'center' as const,
                          render: (_: any, r: any) => (r as any).tiene_analisis_ia
                            ? <AntTooltip title="Tiene análisis IA"><RobotOutlined style={{ color: '#722ed1', fontSize: 18 }} /></AntTooltip>
                            : null },
                        { title: 'Acción', key: 'accion', width: 100,
                          render: (_: any, r: any) => (
                            <Button type="link" size="small" icon={<EyeOutlined />}
                              onClick={() => navigate(`/dashboard/ecografias/${r.id}`)}>
                              Ver
                            </Button>
                          ) },
                      ]}
                      rowKey="id"
                      pagination={{ pageSize: 5 }}
                      locale={{ emptyText: <Empty description="No hay ecografías registradas" /> }}
                      size="small"
                    />
                  ),
                },
                {
                  key: '7',
                  label: (
                    <span>
                      <LineChartOutlined /> Timeline Completo
                    </span>
                  ),
                  children: (
                    <Timeline
                      mode="left"
                      items={[...triajes, ...notasEvolucion, ...vacunas]
                        .sort((a, b) => {
                          const dateA = new Date(a.fecha_hora || a.fecha_consulta || a.fecha_aplicacion || a.fecha_registro);
                          const dateB = new Date(b.fecha_hora || b.fecha_consulta || b.fecha_aplicacion || b.fecha_registro);
                          return dateB.getTime() - dateA.getTime();
                        })
                        .slice(0, 20)
                        .map((item) => {
                          let label = '';
                          let content = '';
                          let color = 'blue';

                          if (item.prioridad) {
                            label = dayjs(item.fecha_hora || item.fecha_registro).format('DD/MM/YYYY HH:mm');
                            content = `Triaje - Prioridad: ${item.prioridad}`;
                            color = item.prioridad === 'urgente' ? 'red' : item.prioridad === 'alto' ? 'orange' : 'blue';
                          } else if (item.tipo_consulta) {
                            label = dayjs(item.fecha_consulta).format('DD/MM/YYYY');
                            content = `Nota Médica - ${item.tipo_consulta}: ${item.motivo_consulta?.substring(0, 50)}...`;
                            color = 'purple';
                          } else if (item.lote) {
                            label = dayjs(item.fecha_aplicacion).format('DD/MM/YYYY');
                            content = `Vacuna - ${item.tipo_vacuna_nombre || 'Vacuna'} (Dosis ${item.numero_dosis})`;
                            color = 'green';
                          }

                          return {
                            key: item.id || `${item.fecha_hora || item.fecha_registro || item.fecha_consulta || item.fecha_aplicacion}-${content}`,
                            label,
                            children: content,
                            color,
                          };
                        })}
                    />
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DetallePaciente;
