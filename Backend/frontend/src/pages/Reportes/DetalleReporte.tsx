import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Button, Spin, Alert, Typography, Space, Tabs, Tooltip,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import {
  ArrowLeftOutlined, DownloadOutlined, PrinterOutlined,
  ReloadOutlined, DeleteOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import { API_URL } from '../../services/api';
import { Reporte } from './reporteTypes';
import { IconoFormatoReporte } from './components/DetalleReporteHelpers';
import TabInfoGeneralReporte from './components/TabInfoGeneralReporte';
import TabFiltrosReporte from './components/TabFiltrosReporte';
import TabVistaPreviaPdfReporte from './components/TabVistaPreviaPdfReporte';

const { Title, Text } = Typography;

const DetalleReporte: React.FC = () => {
  const { modal, message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Estados
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [descargando, setDescargando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const obtenerDetalleReporte = useCallback(async (silencioso = false) => {
    if (!id) return;

    try {
      if (!silencioso) setLoading(true);

      // Auth por cookie httpOnly (withCredentials global en services/api.ts)
      const response = await axios.get(`${API_URL}/reportes/${id}/`);

      setReporte(response.data);
      setError(null);

      // Lógica de Polling: Si el reporte se está procesando, volver a consultar en 5s
      if (response.data.estado === 'PROCESANDO' || response.data.estado === 'PENDIENTE') {
        setTimeout(() => obtenerDetalleReporte(true), 5000);
      }

    } catch (err: any) {
      const msg = err.response?.data?.detail || "Error al conectar con el servidor.";
      setError(msg);
      if (err.response?.status === 404) {
        message.error("El reporte solicitado no existe.");
      }
    } finally {
      if (!silencioso) setLoading(false);
    }
  }, [id, API_URL, message]);

  useEffect(() => {
    obtenerDetalleReporte();
  }, [obtenerDetalleReporte]);

  const handleDownload = async () => {
    if (!reporte?.archivo_url) return;

    try {
      setDescargando(true);
      const urlCompleta = reporte.archivo_url.startsWith('http')
        ? reporte.archivo_url
        : `${API_URL.replace('/api', '')}${reporte.archivo_url}`;

      const link = document.createElement('a');
      link.href = urlCompleta;
      link.setAttribute('download', `${reporte.titulo}.${reporte.formato.toLowerCase()}`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      message.success("Descarga iniciada correctamente");
    } catch (e) {
      message.error("Error al intentar descargar el archivo");
    } finally {
      setDescargando(false);
    }
  };

  const handleDelete = () => {
    modal.confirm({
      title: '¿Eliminar reporte?',
      content: 'Esta acción no se puede deshacer. El archivo físico también será eliminado del servidor.',
      okText: 'Sí, Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          // Cookie httpOnly + X-CSRFToken (defaults globales de axios)
          await axios.delete(`${API_URL}/reportes/${id}/`);
          message.success("Reporte eliminado");
          navigate('/reportes');
        } catch (e) {
          message.error("No se pudo eliminar el reporte");
        }
      }
    });
  };

  if (loading) {
    return (
      <div style={{ padding: 50, textAlign: 'center' }}>
        <Spin size="large" tip="Cargando información del reporte…"><div /></Spin>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <Alert
          message="Error de Acceso"
          description={error}
          type="error"
          showIcon
          action={
            <Button onClick={() => navigate('/reportes')}>Volver a la lista</Button>
          }
        />
      </Card>
    );
  }

  if (!reporte) return null;

  return (
    <div className="animate-fade-in">
      <Card
        style={{ marginBottom: 20 }}
        title={
          <Space align="center">
            <Button
              icon={<ArrowLeftOutlined />}
              type="text"
              onClick={() => navigate('/reportes')}
            />
            <Space direction="vertical" size={0}>
              <Space>
                <IconoFormatoReporte formato={reporte.formato} />
                <Title level={4} style={{ margin: 0 }}>{reporte.titulo}</Title>
              </Space>
              <Text type="secondary" style={{ fontSize: 12 }}>
                ID: {reporte.id} • Generado el {new Date(reporte.fecha_creacion).toISOString().slice(0, 16).replace('T', ' ')}
              </Text>
            </Space>
          </Space>
        }
        extra={
          <Space>
            {reporte.estado === 'TERMINADO' && (
              <>
                <Tooltip title="Imprimir ficha técnica del reporte">
                  <Button icon={<PrinterOutlined />} onClick={() => window.print()}>
                    Imprimir Ficha
                  </Button>
                </Tooltip>
                <Tooltip title="Descargar archivo del reporte generado">
                  <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    loading={descargando}
                    onClick={handleDownload}
                  >
                    Descargar Archivo
                  </Button>
                </Tooltip>
              </>
            )}
            {reporte.estado === 'FALLIDO' && (
              <Tooltip title="Reintentar generación del reporte">
                <Button icon={<ReloadOutlined />} onClick={() => obtenerDetalleReporte()}>
                  Reintentar
                </Button>
              </Tooltip>
            )}
            <Tooltip title="Eliminar permanentemente este reporte">
              <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>
                Eliminar
              </Button>
            </Tooltip>
          </Space>
        }
      >
        <Tabs defaultActiveKey="1" items={[
          {
            key: "1",
            label: "Información General",
            children: <TabInfoGeneralReporte reporte={reporte} />,
          },
          {
            key: "2",
            label: "Filtros Aplicados",
            children: <TabFiltrosReporte reporte={reporte} />,
          },
          ...(reporte.archivo_url && reporte.formato === 'PDF' ? [{
            key: "3",
            label: "Vista Previa (PDF)",
            children: <TabVistaPreviaPdfReporte reporte={reporte} apiUrl={API_URL} />,
          }] : [])
        ]} />
      </Card>
    </div>
  );
};

export default DetalleReporte;
