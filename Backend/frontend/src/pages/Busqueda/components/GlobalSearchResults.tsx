import React, { useMemo } from 'react';
import { Card, Tabs, Table, Space, Spin, Badge, Typography } from 'antd';
import {
  SearchOutlined, UserOutlined, HeartOutlined, CalendarOutlined,
  FileImageOutlined, ExperimentOutlined, FileTextOutlined, HomeOutlined,
} from '@ant-design/icons';
import { SearchResult } from '../globalSearchUtils';
import { getSearchColumns } from '../globalSearchColumns';

const { Title } = Typography;

interface GlobalSearchResultsProps {
  loading: boolean;
  totalResults: number;
  pacientesResults: SearchResult[];
  embarazosResults: SearchResult[];
  citasResults: SearchResult[];
  ecografiasResults: SearchResult[];
  laboratorioResults: SearchResult[];
  evolucionesResults: SearchResult[];
  consultoriosResults: SearchResult[];
  handleViewDetail: (result: SearchResult) => void;
}

const GlobalSearchResults: React.FC<GlobalSearchResultsProps> = ({
  loading, totalResults, pacientesResults, embarazosResults, citasResults,
  ecografiasResults, laboratorioResults, evolucionesResults, consultoriosResults,
  handleViewDetail,
}) => {
  const getColumns = (_tipo: string) => getSearchColumns(handleViewDetail);

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

  return (
    <Card>
      <Spin spinning={loading}>
        <Tabs defaultActiveKey="all" type="card" items={[
          {
            key: "all",
            label: tabTodos,
            children: (
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
            )
          },
          {
            key: "pacientes",
            label: tabPacientes,
            children: (
              <Table
                columns={getColumns('paciente')}
                dataSource={pacientesResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "embarazos",
            label: tabEmbarazos,
            children: (
              <Table
                columns={getColumns('embarazo')}
                dataSource={embarazosResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "citas",
            label: tabCitas,
            children: (
              <Table
                columns={getColumns('cita')}
                dataSource={citasResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "ecografias",
            label: tabEcografias,
            children: (
              <Table
                columns={getColumns('ecografia')}
                dataSource={ecografiasResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "laboratorio",
            label: tabLaboratorio,
            children: (
              <Table
                columns={getColumns('laboratorio')}
                dataSource={laboratorioResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "evoluciones",
            label: tabEvoluciones,
            children: (
              <Table
                columns={getColumns('evolucion')}
                dataSource={evolucionesResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          },
          {
            key: "consultorios",
            label: tabConsultorios,
            children: (
              <Table
                columns={getColumns('consultorio')}
                dataSource={consultoriosResults}
                rowKey="id"
                pagination={{ pageSize: 20 }}
              />
            )
          }
        ]} />
      </Spin>
    </Card>
  );
};

export default GlobalSearchResults;
