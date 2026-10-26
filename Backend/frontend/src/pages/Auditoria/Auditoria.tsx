import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Table, Tag, Button, Space, Typography, Spin, Input, Statistic, Select, DatePicker, Descriptions, Switch,
} from 'antd';
import type { TablePaginationConfig } from 'antd';
import {
  SearchOutlined, ReloadOutlined, ClearOutlined,
  FileTextOutlined, ClockCircleOutlined, TeamOutlined, AppstoreOutlined,
  FileExcelOutlined,
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import api from '../../services/api';
import { descargarArchivo } from '../../utils/descargarArchivo';

import './Auditoria.css';

const { Text, Title } = Typography;
const { RangePicker } = DatePicker;

interface AuditoriaUsuario {
  id: number;
  email: string;
  nombre_completo: string;
}

interface AuditoriaEntry {
  id: number;
  modulo: string;
  modulo_legible: string;
  accion: string;
  accion_display: string;
  registro_id: string;
  usuario: AuditoriaUsuario | null;
  usuario_nombre: string;
  usuario_rol: string;
  fecha: string;
  endpoint: string;
  sesion_id: string;
  ip_address: string | null;
  user_agent: string;
  detalle: string;
}

interface EstadisticasGenerales {
  total_registros: number;
  ultimas_24h: number;
  usuarios_activos: number;
  modulos_activos: number;
}

interface EstadisticaModulo {
  modulo: string;
  modulo_legible: string;
  total: number;
  creates: number;
  updates: number;
  deletes: number;
  consultas: number;
  ultima: string | null;
}

interface Opciones {
  usuarios: { id: number; nombre: string; rol: string; registros: number }[];
  acciones: { valor: string; etiqueta: string }[];
  modulos: { valor: string; etiqueta: string }[];
  roles: string[];
}

interface Filtros {
  search: string;
  usuario_id?: number;
  rol?: string;
  accion?: string;
  modulo?: string;
  ip: string;
  rango: [Dayjs, Dayjs] | null;
  solo_personas: boolean;
}

const FILTROS_INICIALES: Filtros = {
  search: '', ip: '', rango: [dayjs().subtract(7, 'day'), dayjs()], solo_personas: true,
};

// Color solo donde la acción es un estado que hay que ver (fallos, bajas);
// el resto va en la etiqueta neutra.
const accionColors: Record<string, string> = {
  LOGIN_FALLIDO: 'error',
  CUENTA_BLOQUEADA: 'error',
  MFA_FALLIDO: 'error',
  DESACTIVAR: 'warning',
  eliminar: 'warning',
  ELIMINAR: 'error',
};

/** «Mozilla/5.0 (Windows NT 10.0…) Chrome/149.0…» -> «Chrome 149 · Windows». */
function navegador(ua: string): string {
  if (!ua) return '—';
  const nav = ua.match(/(Edg|OPR|Firefox|Chrome|Safari)\/(\d+)/);
  const so = /Windows/.test(ua) ? 'Windows' : /Android/.test(ua) ? 'Android' : /iPhone|iPad/.test(ua) ? 'iOS'
    : /Mac OS/.test(ua) ? 'macOS' : /Linux/.test(ua) ? 'Linux' : '';
  const nombre = nav ? `${nav[1] === 'Edg' ? 'Edge' : nav[1] === 'OPR' ? 'Opera' : nav[1]} ${nav[2]}` : ua.slice(0, 30);
  return so ? `${nombre} · ${so}` : nombre;
}

function parametros(f: Filtros) {
  return {
    search: f.search || undefined,
    usuario_id: f.usuario_id,
    rol: f.rol,
    accion: f.accion,
    modulo: f.modulo,
    ip: f.ip || undefined,
    fecha_inicio: f.rango?.[0]?.format('YYYY-MM-DD'),
    fecha_fin: f.rango?.[1]?.format('YYYY-MM-DD'),
    solo_personas: f.solo_personas ? '1' : undefined,
  };
}

const moduloColumns = [
  { title: 'Módulo', dataIndex: 'modulo_legible', key: 'modulo' },
  { title: 'Total', dataIndex: 'total', key: 'total', align: 'right' as const, render: (v: number) => v.toLocaleString() },
  { title: 'Creaciones', dataIndex: 'creates', key: 'creates', align: 'right' as const, render: (v: number) => v.toLocaleString() },
  { title: 'Modificaciones', dataIndex: 'updates', key: 'updates', align: 'right' as const, render: (v: number) => v.toLocaleString() },
  { title: 'Bajas', dataIndex: 'deletes', key: 'deletes', align: 'right' as const, render: (v: number) => v.toLocaleString() },
  { title: 'Consultas', dataIndex: 'consultas', key: 'consultas', align: 'right' as const, render: (v: number) => v.toLocaleString() },
  { title: 'Última actividad', dataIndex: 'ultima', key: 'ultima', render: (v: string | null) => v ? dayjs(v).format('DD/MM/YYYY HH:mm') : '—' },
];

const Detalle: React.FC<{ r: AuditoriaEntry }> = ({ r }) => (
  <Descriptions size="small" column={{ xs: 1, md: 2 }} bordered>
    <Descriptions.Item label="Quién">{r.usuario?.nombre_completo || r.usuario_nombre || 'Sistema'} {r.usuario_rol && `(${r.usuario_rol})`}</Descriptions.Item>
    <Descriptions.Item label="Cuándo">{dayjs(r.fecha).format('DD/MM/YYYY HH:mm:ss')}</Descriptions.Item>
    <Descriptions.Item label="Qué">{r.accion_display || r.accion}</Descriptions.Item>
    <Descriptions.Item label="Dónde">{r.modulo_legible}{r.registro_id ? ` · registro ${r.registro_id}` : ''}</Descriptions.Item>
    <Descriptions.Item label="Desde qué red (IP)">{r.ip_address || '—'}</Descriptions.Item>
    <Descriptions.Item label="Cómo (ruta)"><Text code>{r.endpoint || '—'}</Text></Descriptions.Item>
    <Descriptions.Item label="Navegador" span={2}><Text type="secondary">{r.user_agent || '—'}</Text></Descriptions.Item>
    {r.detalle && <Descriptions.Item label="Detalle" span={2}>{r.detalle}</Descriptions.Item>}
    {r.sesion_id && <Descriptions.Item label="Sesión" span={2}><Text code>{r.sesion_id}</Text></Descriptions.Item>}
  </Descriptions>
);

const Auditoria: React.FC = () => {
  const [entries, setEntries] = useState<AuditoriaEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState({ page: 1, pageSize: 20 });
  const [stats, setStats] = useState<EstadisticasGenerales | null>(null);
  const [statsModulo, setStatsModulo] = useState<EstadisticaModulo[]>([]);
  const [opciones, setOpciones] = useState<Opciones>({ usuarios: [], acciones: [], modulos: [], roles: [] });
  const [loading, setLoading] = useState(false);
  const [filtros, setFiltros] = useState<Filtros>(FILTROS_INICIALES);
  const [aplicados, setAplicados] = useState<Filtros>(FILTROS_INICIALES);

  // Cada parte por su lado: las opciones de los filtros recorren toda la tabla y
  // no deben dejar las cifras en cero mientras tanto.
  useEffect(() => {
    api.get('/auditoria/estadisticas-generales/').then((r) => setStats(r.data)).catch(() => undefined);
    api.get('/auditoria/estadisticas-modulos/')
      .then((r) => setStatsModulo(Array.isArray(r.data) ? r.data : [])).catch(() => undefined);
    api.get('/auditoria/opciones/').then((r) => setOpciones(r.data)).catch(() => undefined);
  }, []);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/auditoria/', {
        params: { ...parametros(aplicados), page: pagina.page, page_size: pagina.pageSize },
      });
      setEntries(Array.isArray(data) ? data : data?.results ?? []);
      setTotal(Array.isArray(data) ? data.length : data?.count ?? 0);
    } catch {
      setEntries([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [aplicados, pagina]);

  useEffect(() => { cargar(); }, [cargar]);

  const aplicar = () => { setPagina((p) => ({ ...p, page: 1 })); setAplicados(filtros); };
  const limpiar = () => { setFiltros(FILTROS_INICIALES); setAplicados(FILTROS_INICIALES); setPagina((p) => ({ ...p, page: 1 })); };
  const cambiar = <K extends keyof Filtros>(k: K, v: Filtros[K]) => setFiltros((f) => ({ ...f, [k]: v }));

  const exportar = () => {
    const q = new URLSearchParams(Object.entries(parametros(aplicados))
      .filter(([, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])).toString();
    descargarArchivo(`/auditoria/exportar-excel/${q ? `?${q}` : ''}`, `auditoria_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`);
  };

  const columns = [
    {
      title: 'Cuándo', dataIndex: 'fecha', key: 'fecha', width: 150,
      render: (v: string) => <span className="tabular-nums">{dayjs(v).format('DD/MM/YYYY HH:mm:ss')}</span>,
    },
    {
      title: 'Quién', key: 'usuario',
      render: (_: unknown, r: AuditoriaEntry) => (
        <div>
          <Text strong>{r.usuario?.nombre_completo || r.usuario_nombre || 'Sistema'}</Text>
          {r.usuario_rol && <div className="auditoria-page__secundario">{r.usuario_rol}</div>}
        </div>
      ),
    },
    {
      title: 'Qué', dataIndex: 'accion_display', key: 'accion',
      render: (v: string, r: AuditoriaEntry) => <Tag color={accionColors[r.accion] || 'default'}>{v || r.accion}</Tag>,
    },
    {
      title: 'Dónde', key: 'modulo',
      render: (_: unknown, r: AuditoriaEntry) => (
        <div>
          {r.modulo_legible}
          {r.registro_id && <div className="auditoria-page__secundario">registro {r.registro_id}</div>}
        </div>
      ),
    },
    { title: 'IP', dataIndex: 'ip_address', key: 'ip', render: (v: string | null) => <span className="tabular-nums">{v || '—'}</span> },
    { title: 'Navegador', dataIndex: 'user_agent', key: 'ua', render: (v: string) => navegador(v) },
  ];

  return (
    <div className="auditoria-page page-container">
      <header className="auditoria-page__cabecera">
        <Title level={2}>Auditoría</Title>
        <Text type="secondary">
          Todo lo que hace cada persona: quién, qué, en qué módulo y registro, cuándo, desde qué red y con qué navegador.
          Los registros no se pueden modificar.
        </Text>
      </header>
      <div className="auditoria-page__contenido">
        <div className="auditoria-page__cifras">
          <Card size="small"><Statistic title={<><FileTextOutlined />Total de registros</>} value={stats?.total_registros ?? 0} /></Card>
          <Card size="small"><Statistic title={<><ClockCircleOutlined />Últimas 24 horas</>} value={stats?.ultimas_24h ?? 0} /></Card>
          <Card size="small"><Statistic title={<><TeamOutlined />Personas con actividad</>} value={stats?.usuarios_activos ?? 0} /></Card>
          <Card size="small"><Statistic title={<><AppstoreOutlined />Módulos con actividad</>} value={statsModulo.length || stats?.modulos_activos || 0} /></Card>
        </div>

        <Card title="Explorador de registros">
          <div className="auditoria-page__filtros auditoria-page__filtros--inicio">
            <Input
              placeholder="Buscar: nombre, correo, ruta, detalle, IP…"
              prefix={<SearchOutlined />}
              value={filtros.search}
              onChange={(e) => cambiar('search', e.target.value)}
              onPressEnter={aplicar}
              className="auditoria-page__buscar"
              allowClear
            />
            <Select
              placeholder="Persona" allowClear showSearch optionFilterProp="label" className="auditoria-page__tipo"
              value={filtros.usuario_id} onChange={(v) => cambiar('usuario_id', v)}
              options={opciones.usuarios.map((u) => ({ value: u.id, label: `${u.nombre} (${u.rol})` }))}
            />
            <Select
              placeholder="Rol" allowClear className="auditoria-page__tipo" value={filtros.rol}
              onChange={(v) => cambiar('rol', v)} options={opciones.roles.map((r) => ({ value: r, label: r }))}
            />
            <Select
              placeholder="Acción" allowClear showSearch optionFilterProp="label" className="auditoria-page__tipo"
              value={filtros.accion} onChange={(v) => cambiar('accion', v)}
              options={opciones.acciones.map((a) => ({ value: a.valor, label: a.etiqueta }))}
            />
            <Select
              placeholder="Módulo" allowClear showSearch optionFilterProp="label" className="auditoria-page__tipo"
              value={filtros.modulo} onChange={(v) => cambiar('modulo', v)}
              options={opciones.modulos.map((m) => ({ value: m.valor, label: m.etiqueta }))}
            />
            <Input
              placeholder="IP exacta" value={filtros.ip} className="auditoria-page__tipo"
              onChange={(e) => cambiar('ip', e.target.value.trim())} onPressEnter={aplicar} allowClear
            />
            <RangePicker
              format={{ format: 'DD/MM/YYYY', type: 'mask' }}
              value={filtros.rango}
              onChange={(v) => cambiar('rango', v && v[0] && v[1] ? [v[0], v[1]] : null)}
            />
            <Space>
              <Switch checked={filtros.solo_personas} onChange={(v) => cambiar('solo_personas', v)} />
              <Text>Solo acciones de personas</Text>
            </Space>
          </div>
          <div className="auditoria-page__filtros">
            <Button type="primary" icon={<SearchOutlined />} onClick={aplicar}>Filtrar</Button>
            <Button icon={<ClearOutlined />} onClick={limpiar}>Limpiar</Button>
            <Button icon={<ReloadOutlined />} onClick={cargar} loading={loading}>Recargar</Button>
            <Button icon={<FileExcelOutlined />} onClick={exportar}>Exportar Excel</Button>
          </div>
          <Spin spinning={loading}>
            <Table
              columns={columns}
              dataSource={entries}
              rowKey="id"
              size="middle"
              expandable={{ expandedRowRender: (r: AuditoriaEntry) => <Detalle r={r} /> }}
              pagination={{
                current: pagina.page, pageSize: pagina.pageSize, total, showSizeChanger: true,
                pageSizeOptions: [20, 50, 100], showTotal: (t) => `${t.toLocaleString()} registros`,
              }}
              onChange={(p: TablePaginationConfig) => setPagina({ page: p.current || 1, pageSize: p.pageSize || 20 })}
              locale={{ emptyText: 'No hay registros con esos filtros' }}
              scroll={{ x: 900 }}
            />
          </Spin>
        </Card>

        <Card title="Actividad por módulo">
          <Table
            columns={moduloColumns}
            dataSource={statsModulo}
            rowKey="modulo"
            pagination={{ pageSize: 15, hideOnSinglePage: true }}
            size="small"
            locale={{ emptyText: 'Sin actividad registrada' }}
            scroll={{ x: 720 }}
          />
        </Card>
      </div>
    </div>
  );
};

export default Auditoria;
