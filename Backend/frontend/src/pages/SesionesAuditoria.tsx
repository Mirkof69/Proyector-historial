import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Button, DatePicker, Space, Switch, Table, Tag, Timeline, Typography } from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import api from '../services/api';
import { exportarExcel } from '../utils/excelExport';

const { Text } = Typography;
const { RangePicker } = DatePicker;

/** Una sesión de login: del inicio de sesión a la última acción o al cierre. */
interface Sesion {
  sesion_id: string;
  usuario_id: number | null;
  usuario_nombre: string;
  usuario_rol: string;
  inicio: string;
  ultima_actividad: string;
  duracion_min: number;
  acciones: number;
  cerrada: boolean;
  ip: string | null;
  navegador: string | null;
}

interface AccionDeSesion {
  id: number;
  accion: string;
  accion_display?: string;
  modulo: string;
  fecha: string;
  endpoint?: string;
}

const COLOR_ACCION: Record<string, string> = {
  LOGIN: 'green', LOGOUT: 'default', CREAR: 'blue', EDITAR: 'gold', DESACTIVAR: 'red',
  EXPORTAR: 'purple', ANALISIS_CNN: 'cyan', CONSULTA_IA: 'cyan',
};

const navegadorCorto = (ua: string | null) => {
  if (!ua) return '—';
  const m = ua.match(/(Edg|Chrome|Firefox|Safari)\/[\d.]+/);
  return m ? m[0].replace('Edg', 'Edge') : ua.slice(0, 30);
};

/** Acciones de una sesión, cargadas al desplegar la fila. */
const DetalleSesion: React.FC<{ sid: string }> = ({ sid }) => {
  const [acciones, setAcciones] = useState<AccionDeSesion[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get(`/auditoria/sesiones/${sid}/`)
      .then((r) => setAcciones(r.data))
      .catch(() => setError('No se pudieron cargar las acciones de esta sesión.'));
  }, [sid]);

  if (error) return <Alert type="error" showIcon message={error} />;
  if (!acciones) return <Text type="secondary">Cargando…</Text>;
  return (
    <Timeline
      style={{ marginTop: 8 }}
      items={acciones.map((a) => ({
        color: a.accion === 'LOGIN' ? 'green' : a.accion === 'LOGOUT' ? 'gray' : 'blue',
        children: (
          <Space size="small" wrap>
            <Text code>{dayjs(a.fecha).format('HH:mm:ss')}</Text>
            <Tag color={COLOR_ACCION[a.accion] || 'default'}>{a.accion_display || a.accion}</Tag>
            <Text>{a.modulo}</Text>
            {a.endpoint && <Text type="secondary" style={{ fontSize: 12 }}>{a.endpoint}</Text>}
          </Space>
        ),
      }))}
    />
  );
};

/**
 * Logs por sesión: cada inicio de sesión, con todo lo que la persona hizo
 * hasta que salió. Solo el administrador tiene acceso.
 */
const SesionesAuditoria: React.FC = () => {
  const [sesiones, setSesiones] = useState<Sesion[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [rango, setRango] = useState<[Dayjs, Dayjs] | null>([dayjs().subtract(7, 'day'), dayjs()]);
  const [soloAbiertas, setSoloAbiertas] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parametros = useCallback((extra: Record<string, unknown> = {}) => ({
    desde: rango?.[0]?.format('YYYY-MM-DD'),
    hasta: rango?.[1]?.format('YYYY-MM-DD'),
    abiertas: soloAbiertas ? '1' : undefined,
    ...extra,
  }), [rango, soloAbiertas]);

  const cargar = useCallback(async (numero = 1) => {
    setCargando(true);
    setError(null);
    try {
      const r = await api.get('/auditoria/sesiones/', { params: parametros({ page: numero, page_size: 20 }) });
      const datos = r.data;
      setSesiones(Array.isArray(datos) ? datos : datos.results ?? []);
      setTotal(Array.isArray(datos) ? datos.length : datos.count ?? 0);
      setPagina(numero);
    } catch (e: any) {
      setSesiones([]);
      setError(e?.response?.status === 403 ? 'Solo el administrador puede ver las sesiones.' : 'No se pudieron cargar las sesiones.');
    } finally {
      setCargando(false);
    }
  }, [parametros]);

  useEffect(() => { cargar(1); }, [cargar]);

  const exportar = async () => {
    const r = await api.get('/auditoria/sesiones/', { params: parametros({ page_size: 1000 }) });
    const filas: Sesion[] = Array.isArray(r.data) ? r.data : r.data.results ?? [];
    exportarExcel(
      filas.map((s) => ({
        usuario: s.usuario_nombre, rol: s.usuario_rol,
        inicio: dayjs(s.inicio).format('DD/MM/YYYY HH:mm:ss'),
        ultima_actividad: dayjs(s.ultima_actividad).format('DD/MM/YYYY HH:mm:ss'),
        duracion_min: s.duracion_min, acciones: s.acciones,
        estado: s.cerrada ? 'Cerrada' : 'Abierta', ip: s.ip ?? '', navegador: navegadorCorto(s.navegador),
        sesion: s.sesion_id,
      })),
      { usuario: 'Usuario', rol: 'Rol', inicio: 'Inicio', ultima_actividad: 'Última actividad',
        duracion_min: 'Duración (min)', acciones: 'Acciones', estado: 'Estado', ip: 'IP',
        navegador: 'Navegador', sesion: 'ID de sesión' },
      { filename: `sesiones_${dayjs().format('YYYYMMDD_HHmm')}.xlsx`, sheetName: 'Sesiones', title: 'Sesiones de usuario' },
    );
  };

  const columnas = [
    {
      title: 'Usuario', key: 'usuario',
      render: (_: unknown, s: Sesion) => (
        <Space direction="vertical" size={0}>
          <Text strong>{s.usuario_nombre || 'Desconocido'}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{s.usuario_rol}</Text>
        </Space>
      ),
    },
    { title: 'Inicio', dataIndex: 'inicio', key: 'inicio', render: (v: string) => dayjs(v).format('DD/MM/YYYY HH:mm') },
    { title: 'Última actividad', dataIndex: 'ultima_actividad', key: 'ultima', render: (v: string) => dayjs(v).format('HH:mm:ss') },
    { title: 'Duración', dataIndex: 'duracion_min', key: 'duracion', render: (v: number) => `${v} min` },
    { title: 'Acciones', dataIndex: 'acciones', key: 'acciones', align: 'right' as const },
    { title: 'IP', dataIndex: 'ip', key: 'ip', render: (v: string | null) => v || '—' },
    { title: 'Navegador', dataIndex: 'navegador', key: 'navegador', render: navegadorCorto },
    {
      title: 'Estado', dataIndex: 'cerrada', key: 'estado',
      render: (c: boolean) => <Tag color={c ? 'default' : 'green'}>{c ? 'Cerrada' : 'Abierta'}</Tag>,
    },
  ];

  return (
    <>
      <Space wrap style={{ marginBottom: 16 }}>
        <RangePicker value={rango} format="DD/MM/YYYY" allowClear
          onChange={(v) => setRango(v && v[0] && v[1] ? [v[0], v[1]] : null)} />
        <Space>
          <Switch checked={soloAbiertas} onChange={setSoloAbiertas} aria-label="Solo sesiones abiertas" />
          <Text>Solo abiertas</Text>
        </Space>
        <Button icon={<ReloadOutlined />} onClick={() => cargar(pagina)} loading={cargando}>Recargar</Button>
        <Button icon={<DownloadOutlined />} onClick={exportar} disabled={!total}>Exportar Excel</Button>
      </Space>
      {error && <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} />}
      <Table
        rowKey="sesion_id"
        columns={columnas}
        dataSource={sesiones}
        loading={cargando}
        expandable={{ expandedRowRender: (s: Sesion) => <DetalleSesion sid={s.sesion_id} /> }}
        pagination={{ current: pagina, total, pageSize: 20, showSizeChanger: false,
          showTotal: (t) => `${t} sesiones`, onChange: (n) => cargar(n) }}
        locale={{ emptyText: 'No hay sesiones en este periodo' }}
        scroll={{ x: 900 }}
      />
    </>
  );
};

export default SesionesAuditoria;
