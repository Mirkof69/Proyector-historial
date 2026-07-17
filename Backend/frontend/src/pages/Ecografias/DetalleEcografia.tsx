/**
 * =============================================================================
 * DETALLE DE ECOGRAFÍA - VISTA COMPLETA
 * =============================================================================
 * Muestra información completa de una ecografía específica con todos los datos
 * relacionados: Biometría, Anatomía, Anexos e Imágenes.
 * =============================================================================
 */

import React, { useState, useEffect } from 'react';
import { useAntdApp } from "../../hooks/useMessage";
import { descargarArchivo } from '../../utils/descargarArchivo';
import {Card,
  Button,
  Space,
  Alert,
  Row,
  Col,
  Divider,
  Spin,
  Typography} from "antd";
import {
  ArrowLeftOutlined,
  EditOutlined,
  PrinterOutlined,
  FilePdfOutlined,
  FileExcelOutlined,
  DeleteOutlined,
  FileImageOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { ecografiasService, Ecografia } from '../../services/ecografiasService';
import { FRONTEND_ROUTES } from '../../config/routes';
import DetalleEcoDatosGenerales from './components/DetalleEcoDatosGenerales';
import DetalleEcoTimeline from './components/DetalleEcoTimeline';
import DetalleEcoTabs from './components/DetalleEcoTabs';
import DetalleEcoImagenes from './components/DetalleEcoImagenes';
import DetalleEcoInfoAdicional from './components/DetalleEcoInfoAdicional';

const { Title, Text } = Typography;

const handleImprimir = () => {
  window.print();
};

const DetalleEcografia: React.FC = () => {
  const { modal, message } = useAntdApp();
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [ecografia, setEcografia] = useState<Ecografia | null>(null);

  // ==========================================================================
  // CARGAR DATOS
  // ==========================================================================
  const cargarDatos = React.useCallback(async () => {
    setLoading(true);
    try {
      const ecoData = await ecografiasService.getById(Number(id));
      setEcografia(ecoData);
      message.success('Datos cargados correctamente');
    } catch (error) {
      message.error('Error al cargar los datos de la ecografía');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) cargarDatos();
  }, [id, cargarDatos]);

  // ==========================================================================
  // HANDLERS
  // ==========================================================================
  const handleVolver = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
  };

  const handleEditar = () => {
    navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS_EDITAR(Number(id)));
  };

  const handleEliminar = () => {
    modal.confirm({
      title: '¿Eliminar esta ecografía?',
      icon: <ExclamationCircleOutlined />,
      content: 'Esta acción no se puede deshacer.',
      okText: 'Eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await ecografiasService.delete(Number(id));
          message.success('Ecografía eliminada correctamente');
          navigate(FRONTEND_ROUTES.DASHBOARD.ECOGRAFIAS);
        } catch (error) {
          message.error('Error al eliminar la ecografía');
        }
      },
    });
  };

  const handleImageUpload = (info: any) => {
    if (info.file.status === 'uploading') {
      message.loading({ content: 'Subiendo imagen...', key: 'upload' });
    }
    if (info.file.status === 'done') {
      message.success({ content: 'Imagen subida correctamente', key: 'upload' });
      cargarDatos(); // Recargar para mostrar las nuevas imágenes
    } else if (info.file.status === 'error') {
      message.error({ content: 'Error al subir la imagen', key: 'upload' });
    }
  };

  // ==========================================================================
  // RENDER
  // ==========================================================================
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Cargando datos de la ecografía…</div>
      </div>
    );
  }

  if (!ecografia) {
    return (
      <Card>
        <Alert
          message="Ecografía no encontrada"
          description="No se encontró la ecografía solicitada."
          type="error"
          showIcon
        />
        <Button onClick={handleVolver} style={{ marginTop: 16 }}>
          Volver al listado
        </Button>
      </Card>
    );
  }

  return (
    <div className="detalle-ecografia-container">
      {/* HEADER */}
      <Card className="header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={handleVolver}>
                Volver
              </Button>
              <Divider type="vertical" />
              <FileImageOutlined style={{ fontSize: 24, color: '#1890ff' }} />
              <div>
                <Title level={4} style={{ margin: 0 }}>
                  Detalle de Ecografía
                </Title>
                <Text type="secondary">
                  {dayjs(ecografia.fecha_ecografia).format('DD/MM/YYYY')}
                </Text>
              </div>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button icon={<PrinterOutlined />} onClick={handleImprimir}>
                Imprimir
              </Button>
              <Button
                icon={<FilePdfOutlined />}
                onClick={() => descargarArchivo(`/ecografias/${id}/exportar-pdf/`, `ecografia_${id}.pdf`)
                  .then(() => message.success('PDF descargado'))
                  .catch(() => message.error('No se pudo generar el PDF'))}
              >
                PDF
              </Button>
              <Button
                icon={<FileExcelOutlined />}
                onClick={() => descargarArchivo(`/ecografias/${id}/exportar-excel/`, `ecografia_${id}.xlsx`)
                  .then(() => message.success('Excel descargado'))
                  .catch(() => message.error('No se pudo generar el Excel'))}
              >
                Excel
              </Button>
              <Button type="primary" icon={<EditOutlined />} onClick={handleEditar}>
                Editar
              </Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleEliminar}>
                Eliminar
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          {/* INFORMACIÓN GENERAL */}
          <DetalleEcoDatosGenerales ecografia={ecografia} />

          {/* TIMELINE DEL ESTUDIO */}
          <DetalleEcoTimeline ecografia={ecografia} />

          {/* SECCIONES ORGANIZADAS EN TABS */}
          <DetalleEcoTabs ecografia={ecografia} />

          {/* IMÁGENES ECOGRÁFICAS */}
          <DetalleEcoImagenes
            ecografia={ecografia}
            id={id}
            handleImageUpload={handleImageUpload}
          />
        </Col>

        {/* COLUMNA DERECHA */}
        <Col xs={24} lg={8}>
          {/* INFORMACIÓN ADICIONAL */}
          <DetalleEcoInfoAdicional ecografia={ecografia} />
        </Col>
      </Row>
    </div>
  );
};

export default DetalleEcografia;
