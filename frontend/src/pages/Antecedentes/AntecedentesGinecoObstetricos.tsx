import React, { useState } from 'react';
import { Card, Input, Space, Table, Tag, Button, Typography } from 'antd';
import { ReloadOutlined, SearchOutlined, WomanOutlined } from '@ant-design/icons';
import { AntecedenteGinecoObstetrico } from '../../services/antecedentesService';
import { useListadoServidor } from '../../hooks/useListadoServidor';
import './Antecedentes.css';

const { Text } = Typography;

const AntecedentesGinecoObstetricos: React.FC = () => {
  const [busqueda, setBusqueda] = useState('');
  const listado = useListadoServidor<AntecedenteGinecoObstetrico>('/antecedentes/gineco-obstetricos/', { busqueda });

  const columns = [
    { title: 'Paciente', key: 'paciente', render: (_: unknown, r: AntecedenteGinecoObstetrico) => r.paciente_info?.nombre_completo || `ID: ${r.paciente}` },
    {
      title: 'Fórmula Obstétrica', key: 'formula',
      render: (_: unknown, r: AntecedenteGinecoObstetrico) => (
        <Tag>{r.formula_obstetrica || `G${r.gestas ?? 0}P${r.partos ?? 0}A${r.abortos ?? 0}C${r.cesareas ?? 0}`}</Tag>
      ),
    },
    { title: 'Gestas', dataIndex: 'gestas', key: 'gestas', render: (v: number) => v ?? '-' },
    { title: 'Partos', dataIndex: 'partos', key: 'partos', render: (v: number) => v ?? '-' },
    { title: 'Abortos', dataIndex: 'abortos', key: 'abortos', render: (v: number) => v ?? '-' },
    { title: 'Cesáreas', dataIndex: 'cesareas', key: 'cesareas', render: (v: number) => v ?? '-' },
    { title: 'Hijos Vivos', dataIndex: 'hijos_vivos', key: 'hijos_vivos', render: (v: number) => v ?? '-' },
    {
      title: 'Ciclos', dataIndex: 'ciclos_menstruales', key: 'ciclos',
      render: (v: string) => {
        const colors: Record<string, string> = { regular: 'success', irregular: 'warning', amenorrea: 'error' };
        return v ? <Tag color={colors[v] || 'default'}>{v}</Tag> : '-';
      },
    },
  ];

  return (
    <Card
      className="antecedentes-pagina"
      title={<span><WomanOutlined className="antecedentes-icono" />Antecedentes Gineco-Obstétricos</span>}
      extra={(
        <Space>
          <Input allowClear prefix={<SearchOutlined />} className="antecedentes-buscar"
            aria-label="Buscar paciente por nombre o CI" placeholder="Buscar paciente por nombre o CI"
            value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          <Button icon={<ReloadOutlined />} onClick={listado.recargar} loading={listado.cargando}>Recargar</Button>
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
        locale={{ emptyText: 'No hay antecedentes gineco-obstétricos con esa búsqueda' }}
      />
    </Card>
  );
};

export default AntecedentesGinecoObstetricos;
