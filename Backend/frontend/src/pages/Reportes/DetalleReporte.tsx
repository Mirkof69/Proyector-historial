import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Card, 
  Descriptions, 
  Button, 
  Tag, 
  Spin, 
  Alert, 
  Typography, 
  Divider, 
  Space, 
  Tabs,
  Table,
  Tooltip,
  Badge,
  Modal,
} from 'antd';
import { useAntdApp } from '../../hooks/useMessage';
import { 
  FilePdfOutlined, 
  FileExcelOutlined, 
  ArrowLeftOutlined, 
  DownloadOutlined, 
  PrinterOutlined, 
  ReloadOutlined, 
  DeleteOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../../hooks/useAuth';

// ==========================================
// 1. DEFINICIÓN DE TIPOS (INTERFACES)
// ==========================================
// Estas interfaces deben coincidir con tus Serializers de Django

interface UsuarioResumen {
  id: number;
  username: string;
  nombre_completo: string;
  rol: string;
}

interface ReporteMetadata {
  total_registros: number;
  tiempo_procesamiento_seg?: number;
  fuente_datos: string; // Ej: "Base de Datos Principal"
}

interface Reporte {
  id: number;
  uuid?: string; // Si usas UUID en tu modelo
  titulo: string;
  tipo_reporte: 'PACIENTES' | 'EMBARAZOS' | 'CONTROLES' | 'ESTADISTICAS' | 'CLINICO';
  formato: 'PDF' | 'EXCEL' | 'CSV';
  fecha_creacion: string;
  fecha_actualizacion: string;
  
  // Relaciones
  creado_por: UsuarioResumen;
  
  // Campos de Estado y Archivo
  estado: 'PENDIENTE' | 'PROCESANDO' | 'TERMINADO' | 'FALLIDO';
  archivo_url: string | null;
  
  // Campos JSON de la Base de Datos (PostgreSQL JSONField)
  parametros_busqueda: Record<string, any>; // Filtros que se usaron
  resumen_data?: ReporteMetadata; // Metadatos del resultado
  mensaje_error?: string;
}

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface EstadoTagProps {
  estado: string;
}

const EstadoTag: React.FC<EstadoTagProps> = ({ estado }) => {
  switch (estado) {
    case 'TERMINADO':
      return <Tag icon={<CheckCircleOutlined />} color="success">TERMINADO</Tag>;
    case 'PROCESANDO':
      return <Tag icon={<ReloadOutlined spin />} color="processing">PROCESANDO</Tag>;
    case 'PENDIENTE':
      return <Tag icon={<ClockCircleOutlined />} color="warning">EN COLA</Tag>;
    case 'FALLIDO':
      return <Tag icon={<CloseCircleOutlined />} color="error">FALLIDO</Tag>;
    default:
      return <Tag color="default">{estado}</Tag>;
  }
};

interface IconoFormatoProps {
  formato: string;
}

const IconoFormato: React.FC<IconoFormatoProps> = ({ formato }) => {
  return formato === 'PDF'
    ? <FilePdfOutlined style={{ fontSize: '24px', color: '#ff4d4f' }} />
    : <FileExcelOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
};

// ==========================================
// 2. COMPONENTE PRINCIPAL
// ==========================================

const DetalleReporte: React.FC = () => {
  const { message } = useAntdApp();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();

  // Estados
  const [reporte, setReporte] = useState<Reporte | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [descargando, setDescargando] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Configuración de API (Ajustar según tu variable de entorno)
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // ==========================================
  // 3. LÓGICA DE CONEXIÓN (FETCH DATA)
  // ==========================================
  
  const obtenerDetalleReporte = useCallback(async (silencioso = false) => {
    if (!id) return;
    
    try {
      if (!silencioso) setLoading(true);
      
      const token = getToken();
      if (!token) {
        throw new Error("No autenticado. Por favor inicie sesión.");
      }

      const response = await axios.get(`${API_URL}/reportes/${id}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });

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
  }, [id, API_URL, getToken]);

  useEffect(() => {
    obtenerDetalleReporte();
  }, [obtenerDetalleReporte]);

  // ==========================================
  // 4. MANEJADORES DE ACCIÓN
  // ==========================================

  const handleDownload = async () => {
    if (!reporte?.archivo_url) return;
    
    try {
      setDescargando(true);
      // Si la URL es relativa al backend, agregar el dominio
      const urlCompleta = reporte.archivo_url.startsWith('http') 
        ? reporte.archivo_url 
        : `${API_URL.replace('/api', '')}${reporte.archivo_url}`;
        
      // Crear un link temporal para forzar descarga
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
    Modal.confirm({
      title: '¿Eliminar reporte?',
      content: 'Esta acción no se puede deshacer. El archivo físico también será eliminado del servidor.',
      okText: 'Sí, Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          const token = getToken();
          await axios.delete(`${API_URL}/reportes/${id}/`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          message.success("Reporte eliminado");
          navigate('/reportes');
        } catch (e) {
          message.error("No se pudo eliminar el reporte");
        }
      }
    });
  };

  // ==========================================
  // 6. RENDERIZADO PRINCIPAL
  // ==========================================

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
      {/* CABECERA DE ACCIONES */}
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
                  <IconoFormato formato={reporte.formato} />
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
        {/* CONTENIDO PRINCIPAL CON TABS */}
        <Tabs defaultActiveKey="1">
          
          {/* TAB 1: RESUMEN GENERAL */}
          <TabPane tab="Información General" key="1">
            <Descriptions 
              bordered 
              column={{ xxl: 3, xl: 3, lg: 2, md: 2, sm: 1, xs: 1 }}
              layout="vertical"
            >
              <Descriptions.Item label="Estado Actual">
                <EstadoTag estado={reporte.estado} />
              </Descriptions.Item>
              
              <Descriptions.Item label="Tipo de Reporte">
                <Tag color="blue">{reporte.tipo_reporte}</Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Formato">
                <Tag color="geekblue">{reporte.formato}</Tag>
              </Descriptions.Item>

              <Descriptions.Item label="Generado Por">
                <Space>
                  <Badge status="processing" />
                  <Text strong>{reporte.creado_por.nombre_completo}</Text>
                  <Text type="secondary">({reporte.creado_por.rol})</Text>
                </Space>
              </Descriptions.Item>

              <Descriptions.Item label="Fecha de Finalización">
                {reporte.fecha_actualizacion ? new Date(reporte.fecha_actualizacion).toISOString().slice(0, 16).replace('T', ' ') : '-'}
              </Descriptions.Item>

              <Descriptions.Item label="Metadatos del Archivo">
                {reporte.resumen_data ? (
                   <Space direction="vertical" size={0}>
                     <Text>Registros: {reporte.resumen_data.total_registros}</Text>
                     {reporte.resumen_data.tiempo_procesamiento_seg && (
                       <Text type="secondary">Tiempo: {reporte.resumen_data.tiempo_procesamiento_seg}s</Text>
                     )}
                   </Space>
                ) : (
                  <Text type="secondary">No disponible</Text>
                )}
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Paragraph>
              <InfoCircleOutlined style={{ color: '#1890ff', marginRight: 8 }} />
              Este reporte fue generado automáticamente por el sistema Fetal Medical.
              Los datos reflejan el estado de la base de datos al momento de la creación.
            </Paragraph>

            {reporte.estado === 'FALLIDO' && (
              <Alert
                style={{ marginTop: 20 }}
                message="Causa del Error"
                description={reporte.mensaje_error || "Error desconocido durante la generación del reporte."}
                type="error"
                showIcon
                icon={<InfoCircleOutlined />}
              />
            )}
          </TabPane>

          {/* TAB 2: CRITERIOS DE BÚSQUEDA (JSON VIEWER) */}
          <TabPane tab="Filtros Aplicados" key="2">
            <div style={{ background: '#f5f5f5', padding: 20, borderRadius: 8 }}>
              <Alert
                message="Auditoría de Filtros"
                description="Estos son los parámetros exactos que se utilizaron para generar este documento."
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
                style={{ marginBottom: 15 }}
              />

              {/* Renderizado dinámico del objeto JSON de parámetros */}
              <Descriptions title="Parámetros" bordered size="small" column={1}>
                {Object.entries(reporte.parametros_busqueda).map(([key, value]) => (
                  <Descriptions.Item label={key.replace(/_/g, ' ').toUpperCase()} key={key}>
                    {/* Manejo de valores booleanos, nulos o arrays */}
                    {typeof value === 'boolean'
                      ? (value ? 'SÍ' : 'NO')
                      : Array.isArray(value)
                        ? value.join(', ')
                        : String(value || 'N/A')}
                  </Descriptions.Item>
                ))}
              </Descriptions>

              <Divider>Tabla de Parámetros</Divider>

              <Table
                dataSource={Object.entries(reporte.parametros_busqueda).map(([key, value], index) => ({
                  key: index,
                  parametro: key.replace(/_/g, ' ').toUpperCase(),
                  valor: typeof value === 'boolean'
                    ? (value ? 'SÍ' : 'NO')
                    : Array.isArray(value)
                      ? value.join(', ')
                      : String(value || 'N/A'),
                  tipo: Array.isArray(value) ? 'Array' : typeof value
                }))}
                columns={[
                  {
                    title: 'Parámetro',
                    dataIndex: 'parametro',
                    key: 'parametro',
                    render: (text) => <Text strong>{text}</Text>
                  },
                  {
                    title: 'Valor',
                    dataIndex: 'valor',
                    key: 'valor',
                  },
                  {
                    title: 'Tipo',
                    dataIndex: 'tipo',
                    key: 'tipo',
                    render: (tipo) => <Tag color="blue">{tipo}</Tag>
                  }
                ]}
                pagination={false}
                size="small"
              />
            </div>
          </TabPane>
          
          {/* TAB 3: VISTA PREVIA (Solo si hay URL y es soportado por navegador) */}
          {reporte.archivo_url && reporte.formato === 'PDF' && (
            <TabPane tab="Vista Previa (PDF)" key="3">
               <div style={{ height: '600px', width: '100%', border: '1px solid #d9d9d9' }}>
                    <iframe 
                      src={reporte.archivo_url.startsWith('http') ? reporte.archivo_url : `${API_URL.replace('/api', '')}${reporte.archivo_url}`}
                      width="100%" 
                      height="100%" 
                      title="Vista Previa PDF"
                      sandbox="allow-scripts"
                      style={{ border: 'none' }}
                    />
               </div>
            </TabPane>
          )}

        </Tabs>
      </Card>
    </div>
  );
};

export default DetalleReporte;
