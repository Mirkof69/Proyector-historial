import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Tag, Typography } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import './Laboratorio.css';
import { laboratorioService, TipoExamen } from '../../services/laboratorioService';

const { Text } = Typography;

// La categoría no es un estado: todas en etiqueta neutra.
const categoriaColors: Record<string, string> = {
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
    <div className="laboratorio-page page-container">
      <header className="laboratorio-page__cabecera">
        <div>
          <Typography.Title level={2}>Tipos de Examen</Typography.Title>
          <Typography.Text type="secondary">Catálogo de exámenes que se pueden solicitar.</Typography.Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={cargarTipos} loading={loading}>Recargar</Button>
      </header>
    <Card>
      <Table
        columns={columns}
        dataSource={tipos}
        rowKey="id"
        loading={loading}
        pagination={{ defaultPageSize: 20 }}
        locale={{ emptyText: 'No hay tipos de examen registrados' }}
        scroll={{ x: 720 }}
      />
    </Card>
    </div>
  );
};

export default TiposExamen;
