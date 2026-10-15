import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin, Input, Statistic } from 'antd';
import {
  SearchOutlined, ReloadOutlined,
  FileTextOutlined, ClockCircleOutlined, TeamOutlined, AppstoreOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../../services/api';
import { descargarArchivo } from '../../utils/descargarArchivo';

import './Auditoria.css';

const { Text, Title } = Typography;

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

// Color solo donde la acción es un estado que hay que ver (fallos, bajas);
// el resto va en la etiqueta neutra.
const accionColors: Record<string, string> = {
  LOGIN_FALLIDO: 'error',
  DESACTIVAR: 'warning',
  eliminar: 'error',
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
    { title: 'Módulo', dataIndex: 'modulo', key: 'modulo', render: (v: string) => <Tag>{v || '-'}</Tag> },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY HH:mm:ss') : '-' },
  ];

  return (
    <div className="auditoria-page page-container">
      <header className="auditoria-page__cabecera">
        <Title level={2}>Auditoría</Title>
        <Text type="secondary">Quién hizo qué y cuándo en el sistema. Los registros no se pueden modificar.</Text>
      </header>
      <Spin spinning={loading}>
        <div className="auditoria-page__contenido">
        <div className="auditoria-page__cifras">
          <Card size="small"><Statistic title={<><FileTextOutlined />Total de registros</>} value={stats?.total_registros ?? 0} /></Card>
          <Card size="small"><Statistic title={<><ClockCircleOutlined />Últimas 24 horas</>} value={stats?.ultimas_24h ?? 0} /></Card>
          <Card size="small"><Statistic title={<><TeamOutlined />Usuarios activos</>} value={stats?.usuarios_activos ?? 0} /></Card>
          <Card size="small"><Statistic title={<><AppstoreOutlined />Módulos activos</>} value={stats?.modulos_activos ?? 0} /></Card>
        </div>

        <Card title="Actividad por módulo">
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
          title="Registros recientes"
          extra={
            <Space wrap>
              <Input
                placeholder="Buscar por usuario o módulo..."
                prefix={<SearchOutlined />}
                value={search}
                onChange={e => setSearch(e.target.value)}
                onPressEnter={() => cargarTodo(search)}
                className="auditoria-page__buscar"
                allowClear
              />
              <Button icon={<ReloadOutlined />} onClick={() => cargarTodo(search)} loading={loading}>Recargar</Button>
              <Button icon={<FileExcelOutlined />}
                onClick={() => descargarArchivo(`/auditoria/exportar-excel/${search ? `?search=${encodeURIComponent(search)}` : ''}`,
                  `auditoria_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`)}>
                Exportar Excel
              </Button>
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={entries}
            rowKey="id"
            pagination={{ pageSize: 20, showTotal: (t) => `Total ${t} registros` }}
            locale={{ emptyText: 'No hay registros de auditoría' }}
            scroll={{ x: 640 }}
          />
        </Card>
        </div>
      </Spin>
    </div>
  );
};

export default Auditoria;
