import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin, Input, Row, Col, Statistic } from 'antd';
import {
  SearchOutlined, ReloadOutlined, AuditOutlined,
  FileTextOutlined, ClockCircleOutlined, TeamOutlined, AppstoreOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Text } = Typography;

interface AuditoriaUsuario {
  id: number;
  email: string;
  nombre_completo: string;
}

interface AuditoriaEntry {
  id: number;
  modulo: string;
  accion: string;
  accion_display: string;
  registro_id: string;
  usuario: AuditoriaUsuario | null;
  fecha: string;
}

interface EstadisticasGenerales {
  total_registros: number;
  ultimas_24h: number;
  usuarios_activos: number;
  modulos_activos: number;
}

interface EstadisticaModulo {
  modulo: string;
  total: number;
  creates: number;
  updates: number;
  deletes: number;
}

const accionColors: Record<string, string> = {
  LOGIN: 'purple',
  LOGOUT: 'default',
  LOGIN_FALLIDO: 'red',
  CREAR: 'green',
  crear: 'green',
  EDITAR: 'blue',
  actualizar: 'blue',
  VER: 'cyan',
  DESACTIVAR: 'orange',
  eliminar: 'red',
  EXPORTAR: 'gold',
};

const moduloColumns = [
  { title: 'Módulo', dataIndex: 'modulo', key: 'modulo' },
  { title: 'Total', dataIndex: 'total', key: 'total' },
  { title: 'Creaciones', dataIndex: 'creates', key: 'creates' },
  { title: 'Actualizaciones', dataIndex: 'updates', key: 'updates' },
  { title: 'Eliminaciones', dataIndex: 'deletes', key: 'deletes' },
];

const Auditoria: React.FC = () => {
  const [entries, setEntries] = useState<AuditoriaEntry[]>([]);
  const [stats, setStats] = useState<EstadisticasGenerales | null>(null);
  const [statsModulo, setStatsModulo] = useState<EstadisticaModulo[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const cargarTodo = useCallback(async (busqueda?: string) => {
    setLoading(true);
    try {
      const [generales, porModulo, registros] = await Promise.all([
        api.get('/auditoria/estadisticas-generales/'),
        api.get('/auditoria/estadisticas-modulos/'),
        api.get('/auditoria/', { params: { search: busqueda || undefined, page_size: 50 } }),
      ]);
      setStats(generales.data);
      setStatsModulo(Array.isArray(porModulo.data) ? porModulo.data : []);
      const data = registros.data;
      const lista = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
      setEntries(lista);
    } catch {
      setStats(null);
      setStatsModulo([]);
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarTodo();
  }, [cargarTodo]);

  const columns = [
    {
      title: 'Usuario', dataIndex: 'usuario', key: 'usuario',
      render: (u: AuditoriaUsuario | null) => <Text strong>{u?.nombre_completo || u?.email || 'Sistema'}</Text>,
    },
    {
      title: 'Acción', dataIndex: 'accion_display', key: 'accion',
      render: (v: string, record: AuditoriaEntry) => (
        <Tag color={accionColors[record.accion] || 'default'}>{v || record.accion}</Tag>
      ),
    },
    { title: 'Módulo', dataIndex: 'modulo', key: 'modulo', render: (v: string) => <Tag color="geekblue">{v || '-'}</Tag> },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY HH:mm:ss') : '-' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Spin spinning={loading}>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card><Statistic title="Total de registros" value={stats?.total_registros ?? 0} prefix={<FileTextOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="Últimas 24 horas" value={stats?.ultimas_24h ?? 0} prefix={<ClockCircleOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="Usuarios activos" value={stats?.usuarios_activos ?? 0} prefix={<TeamOutlined />} /></Card>
          </Col>
          <Col span={6}>
            <Card><Statistic title="Módulos activos" value={stats?.modulos_activos ?? 0} prefix={<AppstoreOutlined />} /></Card>
          </Col>
        </Row>

        <Card title="Actividad por módulo" style={{ marginBottom: 16 }}>
          <Table
            columns={moduloColumns}
            dataSource={statsModulo}
            rowKey="modulo"
            pagination={false}
            size="small"
            locale={{ emptyText: 'Sin actividad registrada' }}
          />
        </Card>

        <Card
          title={<span><AuditOutlined style={{ marginRight: 8 }} />Registros recientes</span>}
          extra={
            <Space>
              <Input
                placeholder="Buscar por usuario o módulo..."
                prefix={<SearchOutlined />}
                value={search}
                onChange={e => setSearch(e.target.value)}
                onPressEnter={() => cargarTodo(search)}
                style={{ width: 250 }}
                allowClear
              />
              <Button icon={<ReloadOutlined />} onClick={() => cargarTodo(search)} loading={loading}>Recargar</Button>
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={entries}
            rowKey="id"
            pagination={{ pageSize: 20, showTotal: (t) => `Total ${t} registros` }}
            locale={{ emptyText: 'No hay registros de auditoría' }}
          />
        </Card>
      </Spin>
    </div>
  );
};

export default Auditoria;
