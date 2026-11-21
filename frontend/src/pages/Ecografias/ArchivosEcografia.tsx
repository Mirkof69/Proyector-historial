import React, { useState, useEffect, useCallback } from 'react';
import {
  Alert, Button, Card, Form, Image, Input, Modal, Popconfirm, Space, Table, Tag, Typography, Upload,
} from 'antd';
import {
  DeleteOutlined, DownloadOutlined, EyeOutlined, FileImageOutlined, ReloadOutlined, UploadOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import api from '../../services/api';
import { useAntdApp } from '../../hooks/useMessage';
import { usePermissions } from '../../hooks/usePermissions';
import '../Embarazos/paginaClinica.css';
import './Ecografias.css';

const { Text } = Typography;
const URL_ARCHIVOS = '/ecografias-archivos/archivos/';

interface ArchivoEcografia {
  id: number;
  archivo: string;
  nombre_archivo: string;
  tipo_archivo: 'imagen' | 'video' | 'dicom' | 'pdf';
  tamano_bytes: number | null;
  fecha_subida: string;
  subido_por_nombre?: string;
  descripcion?: string;
}

const ETIQUETA_TIPO: Record<string, string> = { imagen: 'Imagen', video: 'Video', dicom: 'DICOM', pdf: 'PDF' };

const formatoTamano = (bytes: number | null) => {
  if (!bytes) return '—';
  const mb = bytes / (1024 * 1024);
  return mb >= 1 ? `${mb.toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
};

/** /media/ exige sesión: se baja con la cookie y se entrega como archivo. */
const descargar = async (a: ArchivoEcografia) => {
  const r = await fetch(a.archivo, { credentials: 'include' });
  if (!r.ok) throw new Error(String(r.status));
  const enlace = document.createElement('a');
  enlace.href = URL.createObjectURL(await r.blob());
  enlace.download = a.nombre_archivo;
  enlace.click();
  URL.revokeObjectURL(enlace.href);
};

/**
 * Adjuntos de una ecografía (imágenes, DICOM, PDF, video).
 *
 * Antes la pantalla pedía /ecografias/<id>/archivos/ (no existe: 404, siempre
 * vacía), leía campos con otros nombres, el botón de borrar no hacía nada y no
 * se podía subir nada. El tipo lo deduce el servidor del contenido del archivo.
 */
const ArchivosEcografia: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = useAntdApp();
  const { canAdd, canDelete } = usePermissions();
  const [archivos, setArchivos] = useState<ArchivoEcografia[]>([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [subiendo, setSubiendo] = useState(false);
  const [vista, setVista] = useState<ArchivoEcografia | null>(null);
  const [form] = Form.useForm();

  const cargar = useCallback(async () => {
    if (!id) return;
    setCargando(true);
    setError(null);
    try {
      const r = await api.get(URL_ARCHIVOS, { params: { ecografia: id, page_size: 200 } });
      setArchivos(r.data?.results ?? r.data ?? []);
    } catch (e: any) {
      setArchivos([]);
      setError(e?.response?.status === 403 ? 'Su rol no tiene acceso a los archivos clínicos.' : 'No se pudieron cargar los archivos.');
    } finally {
      setCargando(false);
    }
  }, [id]);

  useEffect(() => { cargar(); }, [cargar]);

  const subir = async (valores: { archivo?: any[]; descripcion?: string }) => {
    const archivo = valores.archivo?.[0]?.originFileObj;
    if (!archivo || !id) return;
    const datos = new FormData();
    datos.append('ecografia', id);
    datos.append('archivo', archivo);
    if (valores.descripcion) datos.append('descripcion', valores.descripcion);
    setSubiendo(true);
    try {
      await api.post(URL_ARCHIVOS, datos, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 });
      message.success('Archivo subido');
      form.resetFields();
      cargar();
    } catch (e: any) {
      const d = e?.response?.data;
      message.error((d && (d.archivo?.[0] || d.detail || d.error)) || 'No se pudo subir el archivo');
    } finally {
      setSubiendo(false);
    }
  };

  const borrar = async (a: ArchivoEcografia) => {
    try {
      await api.delete(`${URL_ARCHIVOS}${a.id}/`);
      message.success('Archivo eliminado');
      cargar();
    } catch {
      message.error('No se pudo eliminar el archivo');
    }
  };

  const columnas = [
    { title: 'Nombre', dataIndex: 'nombre_archivo', key: 'nombre', render: (v: string) => <Text strong>{v}</Text> },
    { title: 'Tipo', dataIndex: 'tipo_archivo', key: 'tipo', render: (v: string) => <Tag>{ETIQUETA_TIPO[v] ?? v}</Tag> },
    { title: 'Tamaño', dataIndex: 'tamano_bytes', key: 'tamano', render: formatoTamano },
    { title: 'Subido', dataIndex: 'fecha_subida', key: 'fecha',
      render: (v: string, a: ArchivoEcografia) => <>{v ? dayjs(v).format('DD/MM/YYYY HH:mm') : '—'}{a.subido_por_nombre && <><br /><Text type="secondary">{a.subido_por_nombre}</Text></>}</> },
    { title: 'Descripción', dataIndex: 'descripcion', key: 'descripcion', ellipsis: true },
    {
      title: 'Acciones', key: 'acciones',
      render: (_: unknown, a: ArchivoEcografia) => (
        <Space>
          {a.tipo_archivo === 'imagen' && (
            <Button size="small" icon={<EyeOutlined />} aria-label="Ver imagen" title="Ver imagen" onClick={() => setVista(a)} />
          )}
          <Button size="small" icon={<DownloadOutlined />} aria-label="Descargar" title="Descargar"
            onClick={() => descargar(a).catch(() => message.error('No se pudo descargar'))} />
          {canDelete('ecografiaarchivo') && (
            <Popconfirm title="¿Eliminar este archivo?" okText="Eliminar" okButtonProps={{ danger: true }} cancelText="Cancelar"
              onConfirm={() => borrar(a)}>
              <Button size="small" danger icon={<DeleteOutlined />} aria-label="Eliminar" title="Eliminar" />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  if (!id) {
    return (
      <Card className="pagina-clinica" title={<span><FileImageOutlined className="u-mr-2" />Archivos de la ecografía</span>}>
        <Alert message="Abra una ecografía para ver sus archivos." type="info" showIcon />
      </Card>
    );
  }

  return (
    <Card
      className="pagina-clinica ecografias-archivos"
      title={<span><FileImageOutlined className="u-mr-2" />Archivos de la ecografía</span>}
      extra={
        <Space>
          <Button onClick={() => navigate(`/dashboard/ecografias/${id}`)}>Volver a la ecografía</Button>
          <Button icon={<ReloadOutlined />} onClick={cargar} loading={cargando}>Recargar</Button>
        </Space>
      }
    >
      {canAdd('ecografiaarchivo') && (
        <Form form={form} layout="inline" onFinish={subir} className="eco-archivos__subir">
          <Form.Item name="archivo" valuePropName="fileList" getValueFromEvent={(e) => e?.fileList}
            rules={[{ required: true, message: 'Elija un archivo' }]}>
            <Upload beforeUpload={() => false} maxCount={1} accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff,.dcm,.pdf,.mp4,.avi">
              <Button icon={<UploadOutlined />}>Elegir archivo</Button>
            </Upload>
          </Form.Item>
          <Form.Item name="descripcion">
            <Input placeholder="Descripción (opcional)" className="eco-archivos__descripcion" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={subiendo}>Subir</Button>
          <Text type="secondary" className="eco-archivos__ayuda">Imagen, DICOM, PDF o video · hasta 50 MB</Text>
        </Form>
      )}
      {error && <Alert type="error" showIcon message={error} className="u-mb-3" />}
      <Table
        columns={columnas}
        dataSource={archivos}
        rowKey="id"
        loading={cargando}
        pagination={{ defaultPageSize: 10 }}
        locale={{ emptyText: 'Esta ecografía no tiene archivos adjuntos' }}
      />
      <Modal rootClassName="capa-clinica" open={!!vista} onCancel={() => setVista(null)} footer={null} width={800} title={vista?.nombre_archivo}>
        {vista && <Image src={vista.archivo} crossOrigin="use-credentials" className="u-ancho" />}
      </Modal>
    </Card>
  );
};

export default ArchivosEcografia;
