import React, { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Space, Tag, Typography, Spin, Alert, Image, Modal } from 'antd';
import { FileImageOutlined, DownloadOutlined, EyeOutlined, ReloadOutlined, DeleteOutlined } from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import api from '../../services/api';

const { Text } = Typography;

interface ArchivoEcografia {
  id: number;
  nombre: string;
  tipo: string;
  url: string;
  tamaño: number;
  fecha_subida: string;
  descripcion?: string;
}

const formatTamaño = (bytes: number) => {
  if (!bytes) return '-';
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
};

const ArchivosEcografia: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [archivos, setArchivos] = useState<ArchivoEcografia[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const cargarArchivos = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await api.get(`/ecografias/${id}/archivos/`);
      const data = response.data?.results || response.data || [];
      setArchivos(Array.isArray(data) ? data : []);
    } catch {
      setArchivos([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    cargarArchivos();
  }, [cargarArchivos]);


  const columns = [
    { title: 'Nombre', dataIndex: 'nombre', key: 'nombre', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Tipo', dataIndex: 'tipo', key: 'tipo', render: (v: string) => <Tag color="cyan">{v?.toUpperCase()}</Tag> },
    { title: 'Tamaño', dataIndex: 'tamaño', key: 'tamaño', render: (v: number) => formatTamaño(v) },
    { title: 'Fecha Subida', dataIndex: 'fecha_subida', key: 'fecha', render: (v: string) => v ? dayjs(v).format('DD/MM/YYYY HH:mm') : '-' },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion', ellipsis: true },
    {
      title: 'Acciones', key: 'acciones',
      render: (_: unknown, r: ArchivoEcografia) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setPreviewUrl(r.url)} />
          <Button size="small" icon={<DownloadOutlined />} href={r.url} target="_blank" />
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ];

  if (!id) {
    return (
      <Card title={<span><FileImageOutlined style={{ marginRight: 8 }} />Archivos de Ecografía</span>}>
        <Alert message="Seleccione una ecografía" description="Navegue a un detalle de ecografía para ver sus archivos." type="info" showIcon />
      </Card>
    );
  }

  return (
    <Card
      title={<span><FileImageOutlined style={{ marginRight: 8 }} />Archivos de Ecografía</span>}
      extra={<Button icon={<ReloadOutlined />} onClick={cargarArchivos} loading={loading}>Recargar</Button>}
    >
      <Spin spinning={loading}>
        <Table
          columns={columns}
          dataSource={archivos}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          locale={{ emptyText: 'No hay archivos asociados a esta ecografía' }}
        />
      </Spin>
      <Modal open={!!previewUrl} onCancel={() => setPreviewUrl(null)} footer={null} width={800} title="Vista Previa">
        {previewUrl && <Image src={previewUrl} style={{ width: '100%' }} />}
      </Modal>
    </Card>
  );
};

export default ArchivosEcografia;
