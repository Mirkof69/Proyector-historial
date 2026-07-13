import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin, Input, Select } from 'antd';
import { SearchOutlined, ReloadOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../services/api';

const { Text } = Typography;

interface AuditoriaUsuario {
  id: number;
  email: string;
  nombre_completo: string;
}

interface AccesoEntry {
  id: number;
  accion: string;
  accion_display: string;
  usuario: AuditoriaUsuario | null;
  fecha: string;
}

// Solo los eventos de autenticacion (login/logout/MFA), no todo el log de
// auditoria general — eso es lo que distingue esta pantalla de Auditoria.
const ACCIONES_ACCESO = ['LOGIN', 'LOGOUT', 'LOGIN_FALLIDO', 'MFA_ACTIVADO', 'MFA_FALLIDO', 'MFA_DESACTIVADO', 'CUENTA_BLOQUEADA'];

const accionColors: Record<string, string> = {
  LOGIN: 'green',
  LOGOUT: 'default',
  LOGIN_FALLIDO: 'red',
  MFA_ACTIVADO: 'blue',
  MFA_FALLIDO: 'orange',
  MFA_DESACTIVADO: 'orange',
  CUENTA_BLOQUEADA: 'red',
};

const AccessLogs: React.FC = () => {
  const [entries, setEntries] = useState<AccesoEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [accionFiltro, setAccionFiltro] = useState<string | undefined>(undefined);

  const cargar = useCallback(async (busqueda?: string, accion?: string) => {
    setLoading(true);
    try {
      const todos: AccesoEntry[] = [];
      // El backend filtra por una sola "accion" a la vez; si no hay filtro
      // seleccionado, se consulta cada accion de acceso y se combinan.
      const accionesAConsultar = accion ? [accion] : ACCIONES_ACCESO;
      // Cada acción se consulta en paralelo (son independientes) en vez de en
      // serie, para no encadenar N round-trips.
      const respuestas = await Promise.all(
        accionesAConsultar.map((acc) =>
          api.get('/auditoria/', {
            params: { accion: acc, search: busqueda || undefined, page_size: 100 },
          })
        )
      );
      for (const response of respuestas) {
        const data = response.data;
        const lista = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
        todos.push(...lista);
      }
      todos.sort((a, b) => dayjs(b.fecha).valueOf() - dayjs(a.fecha).valueOf());
      setEntries(todos);
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  const columns = [
    {
      title: 'Usuario', dataIndex: 'usuario', key: 'usuario',
      render: (u: AuditoriaUsuario | null) => <Text strong>{u?.nombre_completo || u?.email || 'Desconocido'}</Text>,
    },
    {
      title: 'Evento', dataIndex: 'accion_display', key: 'accion',
      render: (v: string, record: AccesoEntry) => (
        <Tag color={accionColors[record.accion] || 'default'}>{v || record.accion}</Tag>
      ),
    },
    { title: 'Fecha y hora', dataIndex: 'fecha', key: 'fecha', render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY HH:mm:ss') : '-' },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={<span><SafetyCertificateOutlined style={{ marginRight: 8 }} />Registro de Accesos</span>}
        extra={
          <Space>
            <Select
              placeholder="Tipo de evento"
              allowClear
              style={{ width: 180 }}
              value={accionFiltro}
              onChange={(v) => { setAccionFiltro(v); cargar(search, v); }}
              options={ACCIONES_ACCESO.map(a => ({ value: a, label: a.replace(/_/g, ' ') }))}
            />
            <Input
              placeholder="Buscar por usuario..."
              prefix={<SearchOutlined />}
              value={search}
              onChange={e => setSearch(e.target.value)}
              onPressEnter={() => cargar(search, accionFiltro)}
              style={{ width: 220 }}
              allowClear
            />
            <Button icon={<ReloadOutlined />} onClick={() => cargar(search, accionFiltro)} loading={loading}>
              Recargar
            </Button>
          </Space>
        }
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={entries}
            rowKey="id"
            pagination={{ pageSize: 20, showTotal: (t) => `Total ${t} accesos` }}
            locale={{ emptyText: 'No hay registros de acceso' }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default AccessLogs;
