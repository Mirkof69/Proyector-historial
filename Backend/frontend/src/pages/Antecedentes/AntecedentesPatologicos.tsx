import React, { useState } from 'react';
import { Card, Input, Table, Tag, Button, Space } from 'antd';
import { ReloadOutlined, SearchOutlined, WarningOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { AntecedentePatologico } from '../../services/antecedentesService';
import { useListadoServidor } from '../../hooks/useListadoServidor';
import './Antecedentes.css';

const AntecedentesPatologicos: React.FC = () => {
  const [busqueda, setBusqueda] = useState('');
  const listado = useListadoServidor<AntecedentePatologico>('/antecedentes/patologicos/', { busqueda });
  const navigate = useNavigate();

  const columns = [
    { title: 'Paciente', key: 'paciente', render: (_: unknown, r: AntecedentePatologico) => r.paciente_info?.nombre_completo || `ID: ${r.paciente}` },
    {
      title: 'Tipo', dataIndex: 'tipo', key: 'tipo',
      render: (v: string) => <Tag>{v === 'personal' ? 'Personal' : 'Heredofamiliar'}</Tag>,
    },
    { title: 'Diabetes', dataIndex: 'diabetes', key: 'diabetes', render: (v: boolean) => v ? <Tag color="warning">Sí</Tag> : 'No' },
    { title: 'Hipertensión', dataIndex: 'hipertension', key: 'hipertension', render: (v: boolean) => v ? <Tag color="error">Sí</Tag> : 'No' },
    { title: 'Alergias', dataIndex: 'tiene_alergias', key: 'alergias', render: (v: boolean) => v ? <Tag>Sí</Tag> : 'No' },
    { title: 'Asma', dataIndex: 'asma', key: 'asma', render: (v: boolean) => v ? <Tag>Sí</Tag> : 'No' },
    {
      title: 'Riesgo', key: 'riesgo',
      render: (_: unknown, r: AntecedentePatologico) => r.tiene_factores_riesgo_calculado
        ? <Tag color="error" icon={<WarningOutlined />}>Alto</Tag>
        : <Tag color="success">Bajo</Tag>,
    },
    {
      title: 'Acciones', key: 'acciones', width: 90,
      render: (_: unknown, r: AntecedentePatologico) => (
        <Button type="link" icon={<EditOutlined />} aria-label="Editar"
          onClick={() => navigate(`/dashboard/antecedentes/patologicos/${r.id}/editar`)} />
      ),
    },
  ];

  return (
    <Card
      className="antecedentes-pagina"
      title={<span><WarningOutlined className="antecedentes-icono" />Antecedentes Patológicos</span>}
      extra={(
        <Space>
          <Input allowClear prefix={<SearchOutlined />} className="antecedentes-buscar"
            aria-label="Buscar paciente por nombre o CI" placeholder="Buscar paciente por nombre o CI"
            value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          <Button icon={<ReloadOutlined />} onClick={listado.recargar} loading={listado.cargando}>Recargar</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/dashboard/antecedentes/patologicos/nuevo')}>
            Nuevo
          </Button>
        </Space>
      )}
    >
      <Table
        columns={columns}
        dataSource={listado.datos}
        loading={listado.cargando}
        rowKey="id"
        pagination={listado.paginacion}
        onChange={listado.onChange}
        locale={{ emptyText: 'No hay antecedentes patológicos con esa búsqueda' }}
      />
    </Card>
  );
};

export default AntecedentesPatologicos;
