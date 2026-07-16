import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Typography } from 'antd';
import { ReloadOutlined, ExperimentOutlined } from '@ant-design/icons';
import { laboratorioService, TipoExamen } from '../../services/laboratorioService';

const { Text } = Typography;

const categoriaColors: Record<string, string> = {
  hematologia: 'red',
  bioquimica: 'blue',
  inmunologia: 'purple',
  microbiologia: 'cyan',
  urinalisis: 'orange',
  serologia: 'magenta',
  hormonal: 'green',
  genetica: 'geekblue',
};

const TiposExamen: React.FC = () => {
  const [tipos, setTipos] = useState<TipoExamen[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarTipos = useCallback(async () => {
    setLoading(true);
    try {
      const data = await laboratorioService.getTiposExamen();
      setTipos(Array.isArray(data) ? data : []);
    } catch {
      setTipos([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarTipos();
  }, [cargarTipos]);

  const columns = [
    { title: 'Nombre', dataIndex: 'nombre', key: 'nombre', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Código', dataIndex: 'codigo', key: 'codigo' },
    {
      title: 'Categoría', dataIndex: 'categoria', key: 'categoria',
      render: (c: string) => <Tag color={categoriaColors[c] || 'default'}>{c?.toUpperCase()}</Tag>,
    },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion', ellipsis: true },
    { title: 'Preparación', dataIndex: 'preparacion', key: 'preparacion', ellipsis: true },
    { title: 'Tiempo Resultado (hrs)', dataIndex: 'tiempo_resultado', key: 'tiempo' },
    {
      title: 'Activo', dataIndex: 'activo', key: 'activo',
      render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? 'Sí' : 'No'}</Tag>,
    },
  ];

  return (
    <Card
      title={<span><ExperimentOutlined style={{ marginRight: 8 }} />Tipos de Examen</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarTipos} loading={loading}>Recargar</Button>}
    >
      <Table
        columns={columns}
        dataSource={tipos}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 20 }}
        locale={{ emptyText: 'No hay tipos de examen registrados' }}
      />
    </Card>
  );
};

export default TiposExamen;
