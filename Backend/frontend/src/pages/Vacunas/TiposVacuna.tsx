import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin } from 'antd';
import { ReloadOutlined, MedicineBoxOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { vacunasService } from '../../services/vacunasService';

const { Text } = Typography;

interface TipoVacuna {
  id: number;
  nombre: string;
  descripcion?: string;
  dosis_requeridas: number;
  intervalo_dias?: number;
  edad_minima_meses?: number;
  activo: boolean;
  total_aplicadas?: number;
}

const TiposVacuna: React.FC = () => {
  const navigate = useNavigate();
  const [tipos, setTipos] = useState<TipoVacuna[]>([]);
  const [loading, setLoading] = useState(false);

  const cargarTipos = useCallback(async () => {
    setLoading(true);
    try {
      const response = await vacunasService.getTiposVacunas();
      const data = response?.results || [];
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
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion', ellipsis: true },
    { title: 'Dosis Requeridas', dataIndex: 'dosis_requeridas', key: 'dosis', render: (v: number) => <Tag color="blue">{v}</Tag> },
    { title: 'Intervalo (días)', dataIndex: 'intervalo_dias', key: 'intervalo', render: (v: number) => v ? `${v} días` : '-' },
    { title: 'Edad Mínima (meses)', dataIndex: 'edad_minima_meses', key: 'edad_min', render: (v: number) => v != null ? `${v} meses` : '-' },
    {
      title: 'Activo', dataIndex: 'activo', key: 'activo',
      render: (v: boolean) => <Tag color={v ? 'success' : 'default'}>{v ? 'Sí' : 'No'}</Tag>,
    },
    {
      title: 'Total Aplicadas', dataIndex: 'total_aplicadas', key: 'total',
      render: (v: number) => v != null ? v : '-',
    },
  ];

  return (
    <Card
      title={<span><MedicineBoxOutlined style={{ marginRight: 8 }} />Tipos de Vacuna</span>}
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={cargarTipos} loading={loading}>Recargar</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/dashboard/vacunas/tipos/nuevo')}>Nuevo Tipo</Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={tipos}
          rowKey="id"
          pagination={{ pageSize: 20 }}
          locale={{ emptyText: 'No hay tipos de vacuna registrados' }}
        />
      </Spin>
    </Card>
  );
};

export default TiposVacuna;
