import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Tag, Button, Space, Typography, Spin, Input, Modal, Descriptions } from 'antd';
import { SearchOutlined, ReloadOutlined, AuditOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Text } = Typography;

// Forma real de RegistroAuditoriaListSerializer (auditoria/serializers.py).
// El listado NO trae ip_address/detalle/datos_*: esos solo estan en el
// detalle (GET /auditoria/:id/), que se pide al hacer click en "Ver".
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

interface AuditoriaDetalle extends AuditoriaEntry {
  datos_anteriores: Record<string, unknown> | null;
  datos_nuevos: Record<string, unknown> | null;
  cambios_resumidos?: string;
  ip_address: string | null;
  user_agent: string;
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

const AuditoriaReportes: React.FC = () => {
  const [entries, setEntries] = useState<AuditoriaEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [detalle, setDetalle] = useState<AuditoriaDetalle | null>(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);

  const cargarAuditoria = useCallback(async (busqueda?: string) => {
    setLoading(true);
    try {
      const response = await api.get('/auditoria/', {
        params: busqueda ? { search: busqueda } : undefined,
      });
      const data = response.data;
      const lista = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
      setEntries(lista);
    } catch {
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarAuditoria();
  }, [cargarAuditoria]);

  const verDetalle = async (id: number) => {
    setLoadingDetalle(true);
    try {
      const response = await api.get(`/auditoria/${id}/`);
      setDetalle(response.data);
    } catch {
      setDetalle(null);
    } finally {
      setLoadingDetalle(false);
    }
  };

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
    { title: 'Registro afectado', dataIndex: 'registro_id', key: 'registro_id', render: (v: string) => v || '-' },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY HH:mm:ss') : '-' },
    {
      title: 'Acciones', key: 'acciones',
      render: (_: unknown, record: AuditoriaEntry) => (
        <Button size="small" icon={<EyeOutlined />} onClick={() => verDetalle(record.id)} />
      ),
    },
  ];

  return (
    <Card
      title={<span><AuditOutlined style={{ marginRight: 8 }} />Auditoría de Reportes</span>}
      extra={
        <Space>
          <Input
            placeholder="Buscar por usuario o módulo..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={e => setSearch(e.target.value)}
            onPressEnter={() => cargarAuditoria(search)}
            style={{ width: 250 }}
            allowClear
          />
          <Button icon={<ReloadOutlined />} onClick={() => cargarAuditoria(search)} loading={loading}>Recargar</Button>
        </Space>
      }
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={entries}
          rowKey="id"
          pagination={{ pageSize: 20, showTotal: (t) => `Total ${t} registros` }}
          locale={{ emptyText: 'No hay registros de auditoría' }}
        />
      </Spin>

      <Modal
        title="Detalle del registro de auditoría"
        open={!!detalle || loadingDetalle}
        onCancel={() => setDetalle(null)}
        footer={<Button onClick={() => setDetalle(null)}>Cerrar</Button>}
      >
        <Spin spinning={loadingDetalle}>
          {detalle && (
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Usuario">{detalle.usuario?.nombre_completo || detalle.usuario?.email || 'Sistema'}</Descriptions.Item>
              <Descriptions.Item label="Acción">{detalle.accion_display}</Descriptions.Item>
              <Descriptions.Item label="Módulo">{detalle.modulo || '-'}</Descriptions.Item>
              <Descriptions.Item label="Registro afectado">{detalle.registro_id || '-'}</Descriptions.Item>
              <Descriptions.Item label="Fecha">{dayjs(detalle.fecha).format('DD/MM/YYYY HH:mm:ss')}</Descriptions.Item>
              <Descriptions.Item label="Dirección IP">{detalle.ip_address || 'No registrada'}</Descriptions.Item>
              {detalle.cambios_resumidos && (
                <Descriptions.Item label="Cambios">{detalle.cambios_resumidos}</Descriptions.Item>
              )}
            </Descriptions>
          )}
        </Spin>
      </Modal>
    </Card>
  );
};

export default AuditoriaReportes;
