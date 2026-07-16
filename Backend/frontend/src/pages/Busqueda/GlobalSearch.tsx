/**
 * =============================================================================
 * BÚSQUEDA GLOBAL - SEARCH ACROSS ALL MODULES
 * =============================================================================
 * Búsqueda unificada que permite buscar en todos los módulos del sistema:
 * - Pacientes, Embarazos, Partos, Citas, Ecografías, Laboratorio
 * - Evoluciones, Consultorios, Vacunas, Triaje, Alertas
 * =============================================================================
 */

import React, { useState, useMemo } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import {Card, Input, Tag, Space, Empty, Segmented, Typography} from "antd";
import {
  SearchOutlined, UserOutlined, MedicineBoxOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import {
  SearchResult,
  searchPacientes, searchEmbarazos, searchCitas, searchEcografias,
  searchLaboratorio, searchEvoluciones, searchConsultorios,
} from './globalSearchUtils';
import GlobalSearchStats from './components/GlobalSearchStats';
import GlobalSearchResults from './components/GlobalSearchResults';

const { Search } = Input;
const { Title, Text } = Typography;

const GlobalSearch: React.FC = () => {
  const navigate = useNavigate();
  const { message } = useAntdApp();
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
        <GlobalSearchStats
          totalResults={totalResults}
          urgentResultsCount={urgentResultsCount}
          pacientesResults={pacientesResults}
          embarazosResults={embarazosResults}
          citasResults={citasResults}
          ecografiasResults={ecografiasResults}
          laboratorioResults={laboratorioResults}
          evolucionesResults={evolucionesResults}
          consultoriosResults={consultoriosResults}
        />
      )}

      {/* Resultados por tabs */}
      {searchQuery && totalResults > 0 && (
        <GlobalSearchResults
          loading={loading}
          totalResults={totalResults}
          pacientesResults={pacientesResults}
          embarazosResults={embarazosResults}
          citasResults={citasResults}
          ecografiasResults={ecografiasResults}
          laboratorioResults={laboratorioResults}
          evolucionesResults={evolucionesResults}
          consultoriosResults={consultoriosResults}
          handleViewDetail={handleViewDetail}
        />
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
