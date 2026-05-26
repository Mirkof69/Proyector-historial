/**
 * =============================================================================
 * BÚSQUEDA GLOBAL - SEARCH ACROSS ALL MODULES
 * =============================================================================
 * Búsqueda unificada que permite buscar en todos los módulos del sistema:
 * - Pacientes, Embarazos, Partos, Citas, Ecografías, Laboratorio
 * - Evoluciones, Consultorios, Vacunas, Triaje, Alertas
 * =============================================================================
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card, Input, Tabs, Table, Tag, Space, Button, Row, Col, Statistic,
  Empty, Spin, Badge, Tooltip, Segmented, Typography, message
} from 'antd';
import {
  SearchOutlined, UserOutlined, HeartOutlined, CalendarOutlined,
  FileImageOutlined, ExperimentOutlined, FileTextOutlined,
  HomeOutlined, EyeOutlined, MedicineBoxOutlined, AlertOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { pacientesService } from '../../services/pacientesService';
import { embarazosService } from '../../services/embarazosService';
import { citasService } from '../../services/citasService';
import { ecografiasService } from '../../services/ecografiasService';
import { laboratorioService } from '../../services/laboratorioService';
import { evolucionesService } from '../../services/evolucionesService';
import { consultoriosService } from '../../services/consultoriosService';
import dayjs from 'dayjs';

const { Search } = Input;
const { TabPane } = Tabs;
const { Title, Text } = Typography;

interface SearchResult {
  id: number | string;
  tipo: string;
  titulo: string;
  subtitulo?: string;
  descripcion?: string;
  fecha?: string;
  estado?: string;
  relevancia: number;
  data: any;
}

const EYE_ICON_2 = <EyeOutlined />;

const GlobalSearch: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchMode, setSearchMode] = useState<'all' | 'pacientes' | 'clinical'>('all');
  const [recentSearches, setRecentSearches] = useState<string[]>(() => {
    const stored = localStorage.getItem('recentSearches:v1');
    if (stored) {
      try {
        const searches = JSON.parse(stored);
        return searches.slice(0, 5);
      } catch (error) {
      }
    }
    return [];
  });
  const [pacientesResults, setPacientesResults] = useState<SearchResult[]>([]);
  const [embarazosResults, setEmbarazosResults] = useState<SearchResult[]>([]);
  const [citasResults, setCitasResults] = useState<SearchResult[]>([]);
  const [ecografiasResults, setEcografiasResults] = useState<SearchResult[]>([]);
  const [laboratorioResults, setLaboratorioResults] = useState<SearchResult[]>([]);
  const [evolucionesResults, setEvolucionesResults] = useState<SearchResult[]>([]);
  const [consultoriosResults, setConsultoriosResults] = useState<SearchResult[]>([]);

  const urgentResultsCount = useMemo(() =>
    embarazosResults.filter(r =>
      r.data?.riesgo === 'alto' || r.data?.alto_riesgo
    ).length + citasResults.filter(r =>
      r.estado === 'pendiente' && dayjs(r.fecha).isBefore(dayjs().add(1, 'day'))
    ).length, [embarazosResults, citasResults]);

  const totalResults =
    pacientesResults.length +
    embarazosResults.length +
    citasResults.length +
    ecografiasResults.length +
    laboratorioResults.length +
    evolucionesResults.length +
    consultoriosResults.length;

  const tabTodos = useMemo(() => (
    <Badge count={totalResults} offset={[10, 0]}><span><SearchOutlined /> Todos</span></Badge>
  ), [totalResults]);
  const tabPacientes = useMemo(() => (
    <Badge count={pacientesResults.length}><span><UserOutlined /> Pacientes</span></Badge>
  ), [pacientesResults.length]);
  const tabEmbarazos = useMemo(() => (
    <Badge count={embarazosResults.length}><span><HeartOutlined /> Embarazos</span></Badge>
  ), [embarazosResults.length]);
  const tabCitas = useMemo(() => (
    <Badge count={citasResults.length}><span><CalendarOutlined /> Citas</span></Badge>
  ), [citasResults.length]);
  const tabEcografias = useMemo(() => (
    <Badge count={ecografiasResults.length}><span><FileImageOutlined /> Ecografías</span></Badge>
  ), [ecografiasResults.length]);
  const tabLaboratorio = useMemo(() => (
    <Badge count={laboratorioResults.length}><span><ExperimentOutlined /> Laboratorio</span></Badge>
  ), [laboratorioResults.length]);
  const tabEvoluciones = useMemo(() => (
    <Badge count={evolucionesResults.length}><span><FileTextOutlined /> Evoluciones</span></Badge>
  ), [evolucionesResults.length]);
  const tabConsultorios = useMemo(() => (
    <Badge count={consultoriosResults.length}><span><HomeOutlined /> Consultorios</span></Badge>
  ), [consultoriosResults.length]);

  const handleSearch = async (value: string) => {
    if (!value || value.trim().length < 2) {
      message.warning('Ingrese al menos 2 caracteres para buscar');
      return;
    }

    setLoading(true);
    setSearchQuery(value);
    const query = value.toLowerCase().trim();

    // Guardar en búsquedas recientes
    const newRecentSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
    setRecentSearches(newRecentSearches);
    localStorage.setItem('recentSearches:v1', JSON.stringify(newRecentSearches));

    try {
      // Búsqueda paralela en todos los módulos
      const [
        pacientes,
        embarazos,
        citas,
        ecografias,
        laboratorio,
        evoluciones,
        consultorios
      ] = await Promise.all([
        searchPacientes(query),
        searchEmbarazos(query),
        searchCitas(query),
        searchEcografias(query),
        searchLaboratorio(query),
        searchEvoluciones(query),
        searchConsultorios(query)
      ]);

      setPacientesResults(pacientes);
      setEmbarazosResults(embarazos);
      setCitasResults(citas);
      setEcografiasResults(ecografias);
      setLaboratorioResults(laboratorio);
      setEvolucionesResults(evoluciones);
      setConsultoriosResults(consultorios);

      const total = pacientes.length + embarazos.length + citas.length +
                    ecografias.length + laboratorio.length + evoluciones.length +
                    consultorios.length;

      message.success(`${total} resultados encontrados`);
    } catch (error) {
      message.error('Error al realizar la búsqueda');
    } finally {
      setLoading(false);
    }
  };

  // Búsqueda en Pacientes
  const searchPacientes = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await pacientesService.listar() as any[];
      const results: SearchResult[] = [];
      for (const p of data) {
        const _pSearchText = [p.nombre, p.apellido_paterno, p.apellido_materno, p.ci, p.id_clinico].filter(Boolean).join(' ').toLowerCase();
        if (_pSearchText.includes(query)) {
          results.push({
            id: p.id,
            tipo: 'paciente',
            titulo: `${p.nombre} ${p.apellido_paterno} ${p.apellido_materno || ''}`.trim(),
            subtitulo: `CI: ${p.ci || 'N/A'} | ID: ${p.id_clinico || 'N/A'}`,
            descripcion: `${p.edad || 'N/A'} años | ${p.genero || 'N/A'}`,
            fecha: p.fecha_registro,
            estado: p.embarazo_activo ? 'Embarazo Activo' : 'Sin embarazo',
            relevancia: calculateRelevance(query, [p.nombre, p.apellido_paterno, p.apellido_materno, p.ci, p.id_clinico]),
            data: p
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  const searchEmbarazos = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await embarazosService.listar() as any[];
      const results: SearchResult[] = [];
      for (const e of data) {
        const pacienteNombre = e.paciente_info?.nombre_completo || e.paciente_info?.nombre || '';
        const _eSearchText = [pacienteNombre, e.codigo_embarazo].filter(Boolean).join(' ').toLowerCase();
        if (_eSearchText.includes(query)) {
          results.push({
            id: e.id || 0,
            tipo: 'embarazo',
            titulo: `Embarazo de ${pacienteNombre || 'N/A'}`,
            subtitulo: `Código: ${e.codigo_embarazo || 'N/A'}`,
            descripcion: `${e.semanas_gestacion || 0} semanas | FUM: ${dayjs(e.fecha_ultima_menstruacion).format('DD/MM/YYYY')}`,
            fecha: e.fecha_registro,
            estado: e.estado,
            relevancia: calculateRelevance(query, [pacienteNombre, e.codigo_embarazo]),
            data: e
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  const searchCitas = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await citasService.listar() as any[];
      const results: SearchResult[] = [];
      for (const c of data) {
        const _cSearchText = [c.paciente_nombre, c.medico_nombre, c.motivo].filter(Boolean).join(' ').toLowerCase();
        if (_cSearchText.includes(query)) {
          results.push({
            id: c.id,
            tipo: 'cita',
            titulo: `Cita - ${c.paciente_nombre}`,
            subtitulo: `Médico: ${c.medico_nombre || 'N/A'}`,
            descripcion: c.motivo || 'Sin motivo',
            fecha: c.fecha_hora,
            estado: c.estado,
            relevancia: calculateRelevance(query, [c.paciente_nombre, c.medico_nombre, c.motivo]),
            data: c
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  const searchEcografias = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await ecografiasService.listar() as any[];
      const results: SearchResult[] = [];
      for (const e of data) {
        const _ecSearchText = [e.paciente_nombre, e.tipo_ecografia, e.observaciones].filter(Boolean).join(' ').toLowerCase();
        if (_ecSearchText.includes(query)) {
          results.push({
            id: e.id,
            tipo: 'ecografia',
            titulo: `Ecografía - ${e.paciente_nombre}`,
            subtitulo: `Tipo: ${e.tipo_ecografia || 'N/A'}`,
            descripcion: e.observaciones || 'Sin observaciones',
            fecha: e.fecha,
            estado: 'Realizada',
            relevancia: calculateRelevance(query, [e.paciente_nombre, e.tipo_ecografia, e.observaciones]),
            data: e
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  const searchLaboratorio = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await laboratorioService.listar() as any[];
      const results: SearchResult[] = [];
      for (const l of data) {
        const _lSearchText = [l.paciente_nombre, l.tipo_examen, l.nombre_examen].filter(Boolean).join(' ').toLowerCase();
        if (_lSearchText.includes(query)) {
          results.push({
            id: l.id,
            tipo: 'laboratorio',
            titulo: `Laboratorio - ${l.paciente_nombre}`,
            subtitulo: `Examen: ${l.nombre_examen || l.tipo_examen || 'N/A'}`,
            descripcion: `Resultado: ${l.resultado || 'Pendiente'}`,
            fecha: l.fecha_solicitud,
            estado: l.estado,
            relevancia: calculateRelevance(query, [l.paciente_nombre, l.tipo_examen, l.nombre_examen]),
            data: l
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  const searchEvoluciones = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await evolucionesService.listar() as any[];
      const results: SearchResult[] = [];
      for (const e of data) {
        const _evSearchText = [e.paciente_nombre, e.diagnostico, e.medico_nombre].filter(Boolean).join(' ').toLowerCase();
        if (_evSearchText.includes(query)) {
          results.push({
            id: e.id,
            tipo: 'evolucion',
            titulo: `Evolución - ${e.paciente_nombre}`,
            subtitulo: `Médico: ${e.medico_nombre || 'N/A'}`,
            descripcion: e.diagnostico || 'Sin diagnóstico',
            fecha: e.fecha || e.fecha_evento,
            estado: e.tipo || 'N/A',
            relevancia: calculateRelevance(query, [e.paciente_nombre, e.diagnostico, e.medico_nombre]),
            data: e
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  // Búsqueda en Consultorios
  const searchConsultorios = async (query: string): Promise<SearchResult[]> => {
    try {
      const data = await consultoriosService.getAll() as any[];
      const results: SearchResult[] = [];
      for (const c of data) {
        const _coSearchText = [c.nombre, c.codigo, c.area].filter(Boolean).join(' ').toLowerCase();
        if (_coSearchText.includes(query)) {
          results.push({
            id: c.id || 0,
            tipo: 'consultorio',
            titulo: c.nombre || 'Sin nombre',
            subtitulo: `Código: ${c.codigo || 'N/A'} | ${c.area || 'N/A'}`,
            descripcion: `${c.tipo || 'N/A'} | Capacidad: ${c.capacidad || 'N/A'}`,
            fecha: undefined,
            estado: c.estado,
            relevancia: calculateRelevance(query, [c.nombre, c.codigo, c.area]),
            data: c
          });
        }
      }
      return results.sort((a, b) => b.relevancia - a.relevancia);
    } catch (error) {
      return [];
    }
  };

  // Calcular relevancia de búsqueda (scoring simple)
  const calculateRelevance = (query: string, fields: (string | undefined)[]): number => {
    let score = 0;
    const queryLower = query.toLowerCase();
    const words = queryLower.split(' ');
    const wordSet = new Set(words);

    fields.forEach(field => {
      if (!field) return;
      const fieldLower = field.toLowerCase();

      // Coincidencia exacta
      if (fieldLower === queryLower) score += 100;
      // Empieza con el query
      else if (fieldLower.startsWith(queryLower)) score += 50;
      // Contiene el query
      else if (fieldLower.includes(queryLower)) score += 25;
      // Palabras individuales
      wordSet.forEach(word => {
        if (fieldLower.includes(word)) score += 10;
      });
    });

    return score;
  };

  // Navegar a detalle según tipo
  const handleViewDetail = (result: SearchResult) => {
    switch (result.tipo) {
      case 'paciente':
        navigate(`/pacientes/${result.id}`);
        break;
      case 'embarazo':
        navigate(`/embarazos/${result.id}`);
        break;
      case 'cita':
        navigate(`/citas/${result.id}`);
        break;
      case 'ecografia':
        navigate(`/ecografias/${result.id}`);
        break;
      case 'laboratorio':
        navigate(`/laboratorio/${result.id}`);
        break;
      case 'evolucion':
        navigate(`/evoluciones/${result.id}`);
        break;
      case 'consultorio':
        navigate(`/consultorios/${result.id}`);
        break;
      default:
        message.info('Detalle no disponible');
    }
  };

  // Columnas para tablas de resultados
  const getColumns = (tipo: string) => [
    {
      title: 'Título',
      dataIndex: 'titulo',
      key: 'titulo',
      render: (text: string, record: SearchResult) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.subtitulo}</Text>
        </Space>
      ),
    },
    {
      title: 'Descripción',
      dataIndex: 'descripcion',
      key: 'descripcion',
      ellipsis: true,
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      width: 150,
      render: (fecha: string) => fecha ? dayjs(fecha).format('DD/MM/YYYY HH:mm') : '-',
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 120,
      render: (estado: string, record: SearchResult) => {
        const colors: Record<string, string> = {
          'activo': 'green',
          'Embarazo Activo': 'green',
          'disponible': 'green',
          'confirmada': 'green',
          'completada': 'blue',
          'pendiente': 'orange',
          'cancelada': 'red',
          'ocupado': 'red',
        };

        // Mostrar icono de alerta para resultados urgentes
        const isUrgent = (record.tipo === 'embarazo' && (record.data?.riesgo === 'alto' || record.data?.alto_riesgo)) ||
                        (record.tipo === 'cita' && estado === 'pendiente' && dayjs(record.fecha).isBefore(dayjs().add(1, 'day')));

        return (
          <Space>
            {isUrgent && <AlertOutlined style={{ color: '#ff4d4f' }} />}
            <Tag color={colors[estado] || 'default'}>{estado || 'N/A'}</Tag>
          </Space>
        );
      },
    },
    {
      title: 'Relevancia',
      dataIndex: 'relevancia',
      key: 'relevancia',
      width: 100,
      sorter: (a: SearchResult, b: SearchResult) => b.relevancia - a.relevancia,
      render: (score: number) => (
        <Badge
          count={score}
          style={{ backgroundColor: score > 50 ? '#52c41a' : score > 25 ? '#faad14' : '#d9d9d9' }}
        />
      ),
    },
    {
      title: 'Acciones',
      key: 'acciones',
      width: 100,
      fixed: 'right' as const,
      render: (_: any, record: SearchResult) => (
        <Tooltip title="Ver detalle">
          <Button
            type="primary"
            size="small"
            icon={EYE_ICON_2}
            onClick={() => handleViewDetail(record)}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Cabecera con búsqueda */}
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>
              <SearchOutlined /> Búsqueda Global del Sistema
            </Title>
            <Text type="secondary">
              Busque en todos los módulos: pacientes, embarazos, citas, ecografías, laboratorio, evoluciones y consultorios
            </Text>
          </div>

          <Search
            placeholder="Ingrese nombre de paciente, código, CI, diagnóstico, médico, etc..."
            allowClear
            enterButton="Buscar"
            size="large"
            onSearch={handleSearch}
            loading={loading}
            style={{ maxWidth: 800 }}
          />

          <Segmented
            options={[
              { label: 'Buscar en Todo', value: 'all', icon: <SearchOutlined /> },
              { label: 'Solo Pacientes', value: 'pacientes', icon: <UserOutlined /> },
              { label: 'Solo Clínico', value: 'clinical', icon: <MedicineBoxOutlined /> },
            ]}
            value={searchMode}
            onChange={(value) => setSearchMode(value as any)}
          />

          {recentSearches.length > 0 && !searchQuery && (
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>Búsquedas recientes:</Text>
              <div style={{ marginTop: 8 }}>
                <Space wrap>
                  {recentSearches.map((search) => (
                    <Tag
                      key={search}
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleSearch(search)}
                    >
                      {search}
                    </Tag>
                  ))}
                </Space>
              </div>
            </div>
          )}
        </Space>
      </Card>

      {/* Estadísticas de resultados */}
      {searchQuery && (
        <Row gutter={16} style={{ marginTop: 16, marginBottom: 16 }}>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Total"
                value={totalResults}
                prefix={<SearchOutlined />}
                valueStyle={{ color: '#1890ff', fontSize: 20 }}
              />
            </Card>
          </Col>
          {urgentResultsCount > 0 && (
            <Col xs={24} sm={12} md={6} lg={3}>
              <Card size="small">
                <Statistic
                  title="Urgentes"
                  value={urgentResultsCount}
                  prefix={<AlertOutlined />}
                  valueStyle={{ color: '#ff4d4f', fontSize: 20 }}
                />
              </Card>
            </Col>
          )}
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Pacientes"
                value={pacientesResults.length}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Embarazos"
                value={embarazosResults.length}
                prefix={<HeartOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Citas"
                value={citasResults.length}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Ecografías"
                value={ecografiasResults.length}
                prefix={<FileImageOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Laboratorio"
                value={laboratorioResults.length}
                prefix={<ExperimentOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Evoluciones"
                value={evolucionesResults.length}
                prefix={<FileTextOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6} lg={3}>
            <Card size="small">
              <Statistic
                title="Consultorios"
                value={consultoriosResults.length}
                prefix={<HomeOutlined />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Resultados por tabs */}
      {searchQuery && totalResults > 0 && (
        <Card>
          <Spin spinning={loading}>
            <Tabs defaultActiveKey="all" type="card">
              <TabPane
                tab={tabTodos}
                key="all"
              >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {pacientesResults.length > 0 && (
                    <div>
                      <Title level={5}><UserOutlined /> Pacientes ({pacientesResults.length})</Title>
                      <Table
                        columns={getColumns('paciente')}
                        dataSource={pacientesResults.slice(0, 5)}
                        rowKey="id"
                        pagination={false}
                        size="small"
                      />
                    </div>
                  )}
                  {embarazosResults.length > 0 && (
                    <div>
                      <Title level={5}><HeartOutlined /> Embarazos ({embarazosResults.length})</Title>
                      <Table
                        columns={getColumns('embarazo')}
                        dataSource={embarazosResults.slice(0, 5)}
                        rowKey="id"
                        pagination={false}
                        size="small"
                      />
                    </div>
                  )}
                  {citasResults.length > 0 && (
                    <div>
                      <Title level={5}><CalendarOutlined /> Citas ({citasResults.length})</Title>
                      <Table
                        columns={getColumns('cita')}
                        dataSource={citasResults.slice(0, 5)}
                        rowKey="id"
                        pagination={false}
                        size="small"
                      />
                    </div>
                  )}
                  {evolucionesResults.length > 0 && (
                    <div>
                      <Title level={5}><FileTextOutlined /> Evoluciones ({evolucionesResults.length})</Title>
                      <Table
                        columns={getColumns('evolucion')}
                        dataSource={evolucionesResults.slice(0, 5)}
                        rowKey="id"
                        pagination={false}
                        size="small"
                      />
                    </div>
                  )}
                </Space>
              </TabPane>

              <TabPane tab={tabPacientes} key="pacientes">
                <Table
                  columns={getColumns('paciente')}
                  dataSource={pacientesResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabEmbarazos} key="embarazos">
                <Table
                  columns={getColumns('embarazo')}
                  dataSource={embarazosResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabCitas} key="citas">
                <Table
                  columns={getColumns('cita')}
                  dataSource={citasResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabEcografias} key="ecografias">
                <Table
                  columns={getColumns('ecografia')}
                  dataSource={ecografiasResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabLaboratorio} key="laboratorio">
                <Table
                  columns={getColumns('laboratorio')}
                  dataSource={laboratorioResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabEvoluciones} key="evoluciones">
                <Table
                  columns={getColumns('evolucion')}
                  dataSource={evolucionesResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>

              <TabPane tab={tabConsultorios} key="consultorios">
                <Table
                  columns={getColumns('consultorio')}
                  dataSource={consultoriosResults}
                  rowKey="id"
                  pagination={{ pageSize: 20 }}
                />
              </TabPane>
            </Tabs>
          </Spin>
        </Card>
      )}

      {/* Sin resultados */}
      {searchQuery && totalResults === 0 && !loading && (
        <Card style={{ marginTop: 16 }}>
          <Empty description={`No se encontraron resultados para "${searchQuery}"`} />
        </Card>
      )}
    </div>
  );
};

export default GlobalSearch;
