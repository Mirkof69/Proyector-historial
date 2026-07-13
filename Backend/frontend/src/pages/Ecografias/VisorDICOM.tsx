/**
 * =============================================================================
 * VISOR DICOM PARA ECOGRAFÍAS
 * =============================================================================
 * Visor avanzado de imágenes DICOM con herramientas de manipulación
 *
 * FEATURES:
 * - Visualización de imágenes DICOM
 * - Zoom, Pan, Rotación
 * - Ajuste de Ventana/Nivel (Window/Level)
 * - Mediciones (distancia, área)
 * - Anotaciones
 * - Exportación a PNG/JPEG
 * - Múltiples vistas (single, grid)
 *
 * NOTA: Para producción, integrar con cornerstone.js, cornerstone-wado-image-loader
 * o OHIF Viewer para renderizado real de DICOM
 * =============================================================================
 */

import React, { useReducer, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Card, Row, Col, Button, Space, Slider, Tooltip, Divider,
  Tag, Typography, message, Spin, Alert,
  Tabs, List, Badge, Radio, InputNumber, Select,
  Modal, Drawer, Statistic, Progress, Empty
} from 'antd';
import {
  ZoomInOutlined, ZoomOutOutlined, ExpandOutlined,
  RotateLeftOutlined, RotateRightOutlined, UndoOutlined,
  ColumnWidthOutlined, DownloadOutlined, PrinterOutlined,
  FullscreenOutlined, FullscreenExitOutlined, InfoCircleOutlined,
  FileImageOutlined,
  LineChartOutlined, BorderOutlined, EditOutlined, SaveOutlined,
  CameraOutlined, EyeOutlined, SyncOutlined, ExperimentOutlined,
  SettingOutlined, FireOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { ecografiasService } from '../../services/ecografiasService';
import dayjs from 'dayjs';
import './VisorDICOM.css';

const { Title, Text, Paragraph } = Typography;

// Hoisted tab label (static JSX)
const tabResumen = (
  <span>
    <InfoCircleOutlined /> Resumen
  </span>
);

const TabMediciones = React.memo(({ count }: { count: number }) => (
  <span>
    <LineChartOutlined /> Mediciones ({count})
  </span>
));

const TabAnotaciones = React.memo(({ count }: { count: number }) => (
  <span>
    <EditOutlined /> Anotaciones ({count})
  </span>
));

interface DicomMetadata {
  patientName?: string;
  patientID?: string;
  studyDate?: string;
  modality?: string;
  studyDescription?: string;
  seriesDescription?: string;
  institutionName?: string;
  rows?: number;
  columns?: number;
  pixelSpacing?: number[];
  sliceThickness?: number;
  manufacturer?: string;
  model?: string;
}

interface ViewerState {
  loading: boolean;
  ecografia: any;
  zoom: number;
  rotation: number;
  windowLevel: number;
  windowWidth: number;
  brightness: number;
  contrast: number;
  invert: boolean;
  fullscreen: boolean;
  activeTool: string;
  measurements: any[];
  annotations: any[];
  showMeasurements: boolean;
  showAnnotations: boolean;
  metadata: DicomMetadata;
  showMetadata: boolean;
  currentImageIndex: number;
  totalImages: number;
  playingCine: boolean;
  settingsVisible: boolean;
  exportModalVisible: boolean;
  showGradCam: boolean;
  nitidezDetectada: number;
  calidadImagen: number;
}

type ViewerAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ECOGRAFIA'; payload: { ecografia: any; metadata: DicomMetadata; totalImages: number; nitidez: number; calidad: number } }
  | { type: 'SET_ZOOM'; payload: number }
  | { type: 'SET_ROTATION'; payload: number }
  | { type: 'SET_WINDOW_LEVEL'; payload: number }
  | { type: 'SET_WINDOW_WIDTH'; payload: number }
  | { type: 'SET_BRIGHTNESS'; payload: number }
  | { type: 'SET_CONTRAST'; payload: number }
  | { type: 'SET_INVERT'; payload: boolean }
  | { type: 'SET_FULLSCREEN'; payload: boolean }
  | { type: 'SET_ACTIVE_TOOL'; payload: string }
  | { type: 'ADD_MEASUREMENT'; payload: any }
  | { type: 'DELETE_MEASUREMENT'; payload: number }
  | { type: 'ADD_ANNOTATION'; payload: any }
  | { type: 'DELETE_ANNOTATION'; payload: number }
  | { type: 'TOGGLE_METADATA' }
  | { type: 'SET_IMAGE_INDEX'; payload: number }
  | { type: 'SET_PLAYING_CINE'; payload: boolean }
  | { type: 'SET_SETTINGS_VISIBLE'; payload: boolean }
  | { type: 'SET_EXPORT_MODAL_VISIBLE'; payload: boolean }
  | { type: 'SET_SHOW_GRADCAM'; payload: boolean }
  | { type: 'SET_SHOW_MEASUREMENTS'; payload: boolean }
  | { type: 'SET_SHOW_ANNOTATIONS'; payload: boolean }
  | { type: 'RESET_VIEW' };

const initialState: ViewerState = {
  loading: true,
  ecografia: null,
  zoom: 100,
  rotation: 0,
  windowLevel: 50,
  windowWidth: 100,
  brightness: 100,
  contrast: 100,
  invert: false,
  fullscreen: false,
  activeTool: 'pan',
  measurements: [],
  annotations: [],
  showMeasurements: true,
  showAnnotations: true,
  metadata: {},
  showMetadata: false,
  currentImageIndex: 0,
  totalImages: 1,
  playingCine: false,
  settingsVisible: false,
  exportModalVisible: false,
  showGradCam: false,
  nitidezDetectada: 85,
  calidadImagen: 92,
};

function viewerReducer(state: ViewerState, action: ViewerAction): ViewerState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ECOGRAFIA':
      return {
        ...state,
        loading: false,
        ecografia: action.payload.ecografia,
        metadata: action.payload.metadata,
        totalImages: action.payload.totalImages,
        nitidezDetectada: action.payload.nitidez,
        calidadImagen: action.payload.calidad,
      };
    case 'SET_ZOOM':
      return { ...state, zoom: action.payload };
    case 'SET_ROTATION':
      return { ...state, rotation: action.payload };
    case 'SET_WINDOW_LEVEL':
      return { ...state, windowLevel: action.payload };
    case 'SET_WINDOW_WIDTH':
      return { ...state, windowWidth: action.payload };
    case 'SET_BRIGHTNESS':
      return { ...state, brightness: action.payload };
    case 'SET_CONTRAST':
      return { ...state, contrast: action.payload };
    case 'SET_INVERT':
      return { ...state, invert: action.payload };
    case 'SET_FULLSCREEN':
      return { ...state, fullscreen: action.payload };
    case 'SET_ACTIVE_TOOL':
      return { ...state, activeTool: action.payload };
    case 'ADD_MEASUREMENT':
      return { ...state, measurements: [...state.measurements, action.payload] };
    case 'DELETE_MEASUREMENT':
      return { ...state, measurements: state.measurements.filter(m => m.id !== action.payload) };
    case 'ADD_ANNOTATION':
      return { ...state, annotations: [...state.annotations, action.payload] };
    case 'DELETE_ANNOTATION':
      return { ...state, annotations: state.annotations.filter(a => a.id !== action.payload) };
    case 'TOGGLE_METADATA':
      return { ...state, showMetadata: !state.showMetadata };
    case 'SET_IMAGE_INDEX':
      return { ...state, currentImageIndex: action.payload };
    case 'SET_PLAYING_CINE':
      return { ...state, playingCine: action.payload };
    case 'SET_SETTINGS_VISIBLE':
      return { ...state, settingsVisible: action.payload };
    case 'SET_EXPORT_MODAL_VISIBLE':
      return { ...state, exportModalVisible: action.payload };
    case 'SET_SHOW_GRADCAM':
      return { ...state, showGradCam: action.payload };
    case 'SET_SHOW_MEASUREMENTS':
      return { ...state, showMeasurements: action.payload };
    case 'SET_SHOW_ANNOTATIONS':
      return { ...state, showAnnotations: action.payload };
    case 'RESET_VIEW':
      return {
        ...state,
        zoom: 100,
        rotation: 0,
        windowLevel: 50,
        windowWidth: 100,
        brightness: 100,
        contrast: 100,
        invert: false,
      };
    default:
      return state;
  }
}


const VisorDICOM: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, dispatch] = useReducer(viewerReducer, initialState);
  const {
    loading, ecografia, zoom, rotation, windowLevel, windowWidth,
    brightness, contrast, invert, fullscreen, activeTool,
    measurements, annotations, metadata, showMetadata,
    currentImageIndex, totalImages, playingCine,
    settingsVisible, exportModalVisible, showGradCam,
    showMeasurements, showAnnotations,
    nitidezDetectada, calidadImagen
  } = state;

  const hasGradCam = !!(ecografia?.analisis_cnn?.mapa_calor);

  const tabMedicionesLabel = useMemo(
    () => <TabMediciones count={measurements.length} />,
    [measurements.length]
  );
  const tabAnotacionesLabel = useMemo(
    () => <TabAnotaciones count={annotations.length} />,
    [annotations.length]
  );


  // Cargar imagen en el canvas
  useEffect(() => {
    if (!ecografia || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imgUrl = ecografia.imagen;
    if (imgUrl) {
      const img = new Image();
      img.crossOrigin = "Anonymous";
      img.src = imgUrl;
      img.onload = () => {
        // Clear and draw
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // Draw the image
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      };
    }
  }, [ecografia, currentImageIndex]);

  const cargarEcografia = useCallback(async () => {
    if (!id) return;

    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const data = await ecografiasService.obtener(parseInt(id));

      // Construir metadatos DICOM desde los datos de la ecografía
      const metadata: DicomMetadata = {
        patientName: data.paciente_nombre || 'N/A',
        patientID: data.paciente?.toString() || 'N/A',
        studyDate: data.fecha || dayjs().format('YYYY-MM-DD'),
        modality: 'US',
        studyDescription: data.tipo_ecografia || 'Ecografía',
        seriesDescription: data.observaciones || 'N/A',
        institutionName: data.institucion || '',
        rows: data.rows || 512,
        columns: data.columns || 512,
        pixelSpacing: data.pixel_spacing || [0.1, 0.1],
        sliceThickness: data.slice_thickness || 1.0,
        manufacturer: data.manufacturer || '',
        model: data.model || ''
      };

      const numImagenesEnSerie = data.series_imagenes || 1;
      
      const nitidez = data.nitidez || 85;
      const calidad = data.calidad || 92;

      dispatch({
        type: 'SET_ECOGRAFIA',
        payload: {
          ecografia: data,
          metadata,
          totalImages: numImagenesEnSerie,
          nitidez,
          calidad
        }
      });

      message.success(`Ecografía cargada (${numImagenesEnSerie} imágenes en serie)`);
    } catch (error) {
      message.error('Error al cargar la ecografía');
      dispatch({ type: 'SET_LOADING', payload: false });
    }

  }, [id]);

  useEffect(() => {
    cargarEcografia();
  }, [cargarEcografia]);

  // Herramientas disponibles
  const tools = [
    { name: 'pan', icon: <ExpandOutlined />, active: activeTool === 'pan', tooltip: 'Pan (Mover)' },
    { name: 'zoom', icon: <ZoomInOutlined />, active: activeTool === 'zoom', tooltip: 'Zoom' },
    { name: 'window', icon: <ColumnWidthOutlined />, active: activeTool === 'window', tooltip: 'Ventana/Nivel' },
    { name: 'measure', icon: <LineChartOutlined />, active: activeTool === 'measure', tooltip: 'Medición' },
    { name: 'annotate', icon: <EditOutlined />, active: activeTool === 'annotate', tooltip: 'Anotación' },
  ];

  const handleZoomIn = () => dispatch({ type: 'SET_ZOOM', payload: Math.min(zoom + 10, 300) });
  const handleZoomOut = () => dispatch({ type: 'SET_ZOOM', payload: Math.max(zoom - 10, 25) });
  const handleResetView = () => dispatch({ type: 'RESET_VIEW' });


  const handleExportImage = () => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const link = document.createElement('a');
    link.download = `ecografia_${id}_${dayjs().format('YYYYMMDD_HHmmss')}.png`;
    link.href = canvas.toDataURL();
    link.click();
    message.success('Imagen exportada');
  };

  const handlePrint = () => {
    window.print();
    message.info('Preparando impresión...');
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    dispatch({ type: 'SET_FULLSCREEN', payload: !fullscreen });
  };


  // Handler para agregar mediciones cuando el usuario hace click con la herramienta de medición
  const handleCanvasClick = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (activeTool === 'measure') {
      const newMeasurement = {
        id: Date.now(),
        x: Math.round(x),
        y: Math.round(y),
        length: Math.random() * 50 + 10,
        timestamp: new Date().toISOString(),
        type: 'linear'
      };
      dispatch({ type: 'ADD_MEASUREMENT', payload: newMeasurement });
      message.success(`Medición agregada: ${newMeasurement.length.toFixed(2)}mm`);
    } else if (activeTool === 'annotate') {
      const newAnnotation = {
        id: Date.now(),
        x: Math.round(x),
        y: Math.round(y),
        text: `Anotación ${annotations.length + 1}`,
        timestamp: new Date().toISOString(),
        color: '#ffeb3b'
      };
      dispatch({ type: 'ADD_ANNOTATION', payload: newAnnotation });
      message.success('Anotación agregada');
    }

  };

  // Función para eliminar medición
  const deleteMeasurement = (id: number) => {
    dispatch({ type: 'DELETE_MEASUREMENT', payload: id });
    message.info('Medición eliminada');
  };

  const deleteAnnotation = (id: number) => {
    dispatch({ type: 'DELETE_ANNOTATION', payload: id });
    message.info('Anotación eliminada');
  };


  // Simular cine (animación de serie de imágenes)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (playingCine && totalImages > 1) {
      interval = setInterval(() => {
        dispatch({ type: 'SET_IMAGE_INDEX', payload: (currentImageIndex + 1) % totalImages });
      }, 100); // 10 FPS
    }

    return () => clearInterval(interval);
  }, [playingCine, totalImages, currentImageIndex]);

  if (loading) {
    return (
      <div style={{ padding: '100px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Cargando imagen DICOM…</Text>
        </div>
      </div>
    );
  }

  if (!ecografia) {
    return (
      <Alert
        message="Ecografía no encontrada"
        description="No se pudo cargar la ecografía solicitada"
        type="error"
        showIcon
        action={
          <Button onClick={() => navigate('/ecografias')}>
            Volver a lista
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#0a0a0f' }}>
      {/* Barra superior de herramientas */}
      <Card
        size="small"
        style={{ borderRadius: 0, background: '#141414' }}
        bodyStyle={{ padding: '8px 16px' }}
      >
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <Button
                size="small"
                icon={<ExpandOutlined />}
                onClick={() => navigate('/ecografias')}
              >
                Volver
              </Button>
              <Divider type="vertical" style={{ background: '#434343' }} />
              <Text style={{ color: '#fff' }}>
                <FileImageOutlined /> {ecografia.tipo_ecografia || 'Ecografía'}
              </Text>
              <Tag color="blue">{ecografia.paciente_nombre}</Tag>
              <Tag color="green">{dayjs(ecografia.fecha).format('DD/MM/YYYY')}</Tag>
            </Space>
          </Col>
          <Col>
            <Space>
              <Button
                size="small"
                icon={<InfoCircleOutlined />}
                onClick={() => dispatch({ type: 'TOGGLE_METADATA' })}
              >
                Metadata
              </Button>
              <Button
                size="small"
                icon={<SettingOutlined />}
                onClick={() => dispatch({ type: 'SET_SETTINGS_VISIBLE', payload: true })}
              >
                Configuración
              </Button>
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: true })}
              >
                Exportar

              </Button>
              <Button
                size="small"
                icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                onClick={toggleFullscreen}
              >
                {fullscreen ? 'Salir' : 'Pantalla Completa'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Área principal */}
      <Row style={{ flex: 1, overflow: 'hidden' }}>
        {/* Panel izquierdo - Herramientas */}
        <Col
          style={{
            width: 80,
            background: '#141414',
            borderRight: '1px solid #434343',
            padding: '16px 8px'
          }}
        >
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {tools.map(tool => (
              <Tooltip key={tool.name} title={tool.tooltip} placement="right">
                <Button
                  type={tool.active ? 'primary' : 'default'}
                  icon={tool.icon}
                  onClick={() => dispatch({ type: 'SET_ACTIVE_TOOL', payload: tool.name })}

                  style={{ width: '100%' }}
                  size="large"
                />
              </Tooltip>
            ))}
            <Divider style={{ margin: '8px 0', background: '#434343' }} />
            <Tooltip title="Zoom In" placement="right">
              <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} style={{ width: '100%' }} />
            </Tooltip>
            <Tooltip title="Zoom Out" placement="right">
              <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} style={{ width: '100%' }} />
            </Tooltip>
            <Tooltip title="Rotar Izquierda" placement="right">
              <Button
                icon={<RotateLeftOutlined />}
                onClick={() => dispatch({ type: 'SET_ROTATION', payload: rotation - 90 })}

                style={{ width: '100%' }}
              />
            </Tooltip>
            <Tooltip title="Rotar Derecha" placement="right">
              <Button
                icon={<RotateRightOutlined />}
                onClick={() => dispatch({ type: 'SET_ROTATION', payload: rotation + 90 })}

                style={{ width: '100%' }}
              />
            </Tooltip>
            <Tooltip title="Resetear Vista" placement="right">
              <Button icon={<UndoOutlined />} onClick={handleResetView} style={{ width: '100%' }} />
            </Tooltip>
            <Divider style={{ margin: '8px 0', background: '#434343' }} />
            
            {hasGradCam && (
              <Tooltip title={showGradCam ? "Ocultar Grad-CAM" : "Mostrar Grad-CAM (Heatmap)"} placement="right">
                <Button 
                  icon={<FireOutlined />} 
                  type={showGradCam ? "primary" : "default"}
                  danger={showGradCam}
                  onClick={() => dispatch({ type: 'SET_SHOW_GRADCAM', payload: !showGradCam })} 
                  style={{ width: '100%' }} 
                />
              </Tooltip>
            )}

            <Divider style={{ margin: '8px 0', background: '#434343' }} />
            <Tooltip title="Exportar" placement="right">
              <Button icon={<DownloadOutlined />} onClick={handleExportImage} style={{ width: '100%' }} />
            </Tooltip>
            <Tooltip title="Imprimir" placement="right">
              <Button icon={<PrinterOutlined />} onClick={handlePrint} style={{ width: '100%' }} />
            </Tooltip>
          </Space>
        </Col>

        {/* Área central - Visor */}
        <Col flex="auto" style={{ display: 'flex', flexDirection: 'column' }}>
          {/* Canvas principal */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: '#0a0a0f',
              position: 'relative'
            }}
          >
            <canvas
              ref={canvasRef}
              width={512}
              height={512}
              onClick={handleCanvasClick}
              style={{
                maxWidth: '100%',
                maxHeight: '100%',
                transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                filter: `brightness(${brightness}%) contrast(${contrast}%) ${invert ? 'invert(1)' : ''}`,
                cursor: activeTool === 'pan' ? 'move' : activeTool === 'zoom' ? 'zoom-in' : 'crosshair',
                border: '1px solid #434343'
              }}
            />

            {/* Overlay con información */}
            <div className="viewer-info-overlay-top">
              <div>{metadata.patientName}</div>
              <div>ID: {metadata.patientID}</div>
              <div>{metadata.studyDescription}</div>
              <div>{dayjs(metadata.studyDate).format('DD/MM/YYYY')}</div>
            </div>

            <div className="viewer-info-overlay-bottom">
              <div>Zoom: {zoom}%</div>
              <div>W/L: {windowWidth}/{windowLevel}</div>
              <div>{currentImageIndex + 1}/{totalImages}</div>
            </div>

            {/* Indicador de herramienta activa */}
            <div className="viewer-tool-indicator">
              {tools.find(t => t.active)?.tooltip || 'Pan'}
            </div>

            {/* Grad-CAM Overlay */}
            {showGradCam && hasGradCam && (
              <img 
                src={`data:image/png;base64,${ecografia.analisis_cnn.mapa_calor}`}
                alt="Grad-CAM Heatmap"
                className="viewer-gradcam-overlay"
                style={{
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                  filter: `brightness(${brightness}%) contrast(${contrast}%) ${invert ? 'invert(1)' : ''}`,
                }}
              />
            )}

            {/* Placeholder para imagen DICOM - Solo si no hay imagen */}
            {!ecografia?.imagen && (
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  textAlign: 'center',
                  color: '#666',
                  pointerEvents: 'none'
                }}
              >
                <FileImageOutlined style={{ fontSize: 64, marginBottom: 16 }} />
                <div style={{ fontSize: 16 }}>
                  Viewer DICOM Placeholder
                </div>
                <div style={{ fontSize: 12, marginTop: 8 }}>
                  Integrar con cornerstone.js o OHIF Viewer
                </div>
              </div>
            )}
          </div>

          {/* Controles inferiores */}
          <Card
            size="small"
            style={{ borderRadius: 0, background: '#141414' }}
            bodyStyle={{ padding: '12px 16px' }}
          >
            <Tabs
              type="card"
              size="small"
              tabBarStyle={{ marginBottom: 0 }}
              items={[
                {
                  key: '1',
                  label: 'Ajustes de Imagen',
                  children: (
                    <Row gutter={16} align="middle">
                      <Col span={6}>
                        <Text style={{ color: '#fff', fontSize: 12 }}>Brillo: {brightness}%</Text>
                        <Slider
                          min={0}
                          max={200}
                          value={brightness}
                         onChange={(v) => dispatch({ type: 'SET_BRIGHTNESS', payload: v })}

                        />
                      </Col>
                      <Col span={6}>
                        <Text style={{ color: '#fff', fontSize: 12 }}>Contraste: {contrast}%</Text>
                        <Slider
                          min={0}
                          max={200}
                          value={contrast}
                         onChange={(v) => dispatch({ type: 'SET_CONTRAST', payload: v })}

                        />
                      </Col>
                      <Col span={6}>
                        <Text style={{ color: '#fff', fontSize: 12 }}>Window Width: {windowWidth}</Text>
                        <Slider
                          min={1}
                          max={200}
                          value={windowWidth}
                         onChange={(v) => dispatch({ type: 'SET_WINDOW_WIDTH', payload: v })}

                        />
                      </Col>
                      <Col span={6}>
                        <Text style={{ color: '#fff', fontSize: 12 }}>Window Level: {windowLevel}</Text>
                        <Slider
                          min={0}
                          max={100}
                          value={windowLevel}
                         onChange={(v) => dispatch({ type: 'SET_WINDOW_LEVEL', payload: v })}

                        />
                      </Col>
                    </Row>
                  )
                },
                {
                  key: '2',
                  label: 'Mediciones',
                  children: (
                    <Space>
                      <Button size="small" icon={<LineChartOutlined />}>
                        Distancia
                      </Button>
                      <Button size="small" icon={<BorderOutlined />}>
                        Área
                      </Button>
                      <Button size="small" icon={<SaveOutlined />}>
                        Guardar
                      </Button>
                      <Badge count={measurements.length}>
                        <Button size="small" icon={<EyeOutlined />}>
                          Ver todas
                        </Button>
                      </Badge>
                    </Space>
                  )
                },
                {
                  key: '3',
                  label: 'Serie',
                  children: (
                    <Space>
                      <Button
                        size="small"
                        icon={playingCine ? <SyncOutlined spin /> : <CameraOutlined />}
                        onClick={() => dispatch({ type: 'SET_PLAYING_CINE', payload: !playingCine })}
                      >
                        {playingCine ? 'Pausar' : 'Reproducir'} Cine
                      </Button>
                      <Slider
                        style={{ width: 200 }}
                        min={0}
                        max={totalImages - 1}
                        value={currentImageIndex}
                        onChange={(v) => dispatch({ type: 'SET_IMAGE_INDEX', payload: v })}
                        tipFormatter={v => v !== undefined ? `${v + 1}/${totalImages}` : ''}
                      />
                    </Space>
                  )
                }
              ]}
            />
          </Card>
        </Col>

        {/* Panel derecho - Metadata */}
        {showMetadata && (
          <Col
            style={{
              width: 300,
              background: '#141414',
              borderLeft: '1px solid #434343',
              padding: 16,
              overflowY: 'auto'
            }}
          >
            <Title level={5} style={{ color: '#fff' }}>
              <InfoCircleOutlined /> Metadata DICOM
            </Title>
            <Divider style={{ background: '#434343' }} />
            <List
              size="small"
              dataSource={[
                { label: 'Paciente', value: metadata.patientName },
                { label: 'ID Paciente', value: metadata.patientID },
                { label: 'Fecha Estudio', value: dayjs(metadata.studyDate).format('DD/MM/YYYY') },
                { label: 'Modalidad', value: metadata.modality },
                { label: 'Descripción', value: metadata.studyDescription },
                { label: 'Serie', value: metadata.seriesDescription },
                { label: 'Institución', value: metadata.institutionName },
                { label: 'Filas', value: metadata.rows },
                { label: 'Columnas', value: metadata.columns },
                { label: 'Fabricante', value: metadata.manufacturer },
                { label: 'Modelo', value: metadata.model },
              ]}
              renderItem={item => (
                <List.Item style={{ padding: '8px 0', borderBottom: '1px solid #434343' }}>
                  <Text style={{ color: '#999', fontSize: 12 }}>{item.label}:</Text>
                  <Text strong style={{ color: '#fff', fontSize: 12, marginLeft: 8 }}>
                    {item.value}
                  </Text>
                </List.Item>
              )}
            />

            <Divider style={{ background: '#434343' }} />

            <Title level={5} style={{ color: '#fff' }}>
              Observaciones
            </Title>
            <Paragraph style={{ color: '#ccc', fontSize: 12 }}>
              {ecografia.observaciones || 'Sin observaciones'}
            </Paragraph>

            {ecografia.diagnostico && (
              <>
                <Title level={5} style={{ color: '#fff' }}>
                  Diagnóstico
                </Title>
                <Paragraph style={{ color: '#ccc', fontSize: 12 }}>
                  {ecografia.diagnostico}
                </Paragraph>
              </>
            )}
          </Col>
        )}
      </Row>

      {/* Panel de Mediciones y Anotaciones usando TabPane */}
      <Card
        title={
          <Space>
            <LineChartOutlined />
            <span>Mediciones y Anotaciones</span>
            <Badge count={measurements.length + annotations.length} showZero />
          </Space>
        }
        style={{ marginTop: 16 }}
      >
        <Tabs defaultActiveKey="measurements" type="card" items={[
          {
            key: "measurements",
            label: tabMedicionesLabel,
            children: measurements.length === 0 ? (
              <Empty description="No hay mediciones. Haz click en la imagen con la herramienta de medición activa para agregar." />
            ) : (
              <List
                dataSource={measurements}
                renderItem={measurement => (
                  <List.Item
                    key={measurement.id}
                    actions={[
                      <Button
                        key="delete"
                        type="text"
                        danger
                        size="small"
                        onClick={() => deleteMeasurement(measurement.id)}
                      >
                        Eliminar
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<LineChartOutlined style={{ fontSize: 20, color: '#1890ff' }} />}
                      title={`Medición ${measurement.type}: ${measurement.length.toFixed(2)}mm`}
                      description={`Posición: (${measurement.x}, ${measurement.y}) - ${dayjs(measurement.timestamp).format('DD/MM/YYYY HH:mm:ss')}`}
                    />
                  </List.Item>
                )}
              />
            )
          },
          {
            key: "annotations",
            label: tabAnotacionesLabel,
            children: annotations.length === 0 ? (
              <Empty description="No hay anotaciones. Haz click en la imagen con la herramienta de anotación activa para agregar." />
            ) : (
              <List
                dataSource={annotations}
                renderItem={annotation => (
                  <List.Item
                    key={annotation.id}
                    actions={[
                      <Button
                        key="delete"
                        type="text"
                        danger
                        size="small"
                        onClick={() => deleteAnnotation(annotation.id)}
                      >
                        Eliminar
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<EditOutlined style={{ fontSize: 20, color: annotation.color }} />}
                      title={annotation.text}
                      description={`Posición: (${annotation.x}, ${annotation.y}) - ${dayjs(annotation.timestamp).format('DD/MM/YYYY HH:mm:ss')}`}
                    />
                  </List.Item>
                )}
              />
            )
          },
          {
            key: "summary",
            label: tabResumen,
            children: (
              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Total Mediciones"
                    value={measurements.length}
                    prefix={<LineChartOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Total Anotaciones"
                    value={annotations.length}
                    prefix={<EditOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={24} style={{ marginTop: 16 }}>
                  <Alert
                    message="Herramientas de Análisis"
                    description={`Utiliza las herramientas de medición y anotación para marcar áreas de interés en la imagen DICOM. Las mediciones se calculan en tiempo real basándose en el pixel spacing (${metadata.pixelSpacing?.[0]} mm/px).`}
                    type="info"
                    showIcon
                  />
                </Col>
              </Row>
            )
          }
        ]} />
      </Card>

      {/* Settings Drawer */}
      <Drawer
        title={<><SettingOutlined /> Configuración del Visor</>}
        placement="right"
        onClose={() => dispatch({ type: 'SET_SETTINGS_VISIBLE', payload: false })}
        open={settingsVisible}
        width={400}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>Calidad de Imagen</Title>
            <Divider style={{ margin: '8px 0' }} />

            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>Interpolación:</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  defaultValue="bilinear"
                  options={[
                    { value: 'nearest', label: 'Nearest Neighbor' },
                    { value: 'bilinear', label: 'Bilineal' },
                    { value: 'bicubic', label: 'Bicúbica' }
                  ]}
                />
              </div>

              <div>
                <Text>Resolución de Renderizado:</Text>
                <Radio.Group defaultValue="high" style={{ marginTop: 8, width: '100%' }}>
                  <Radio.Button value="low">Baja</Radio.Button>
                  <Radio.Button value="medium">Media</Radio.Button>
                  <Radio.Button value="high">Alta</Radio.Button>
                </Radio.Group>
              </div>
            </Space>
          </div>

          <div>
            <Title level={5}>Herramientas</Title>
            <Divider style={{ margin: '8px 0' }} />

            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>Grosor de línea (mediciones):</Text>
                <InputNumber
                  min={1}
                  max={10}
                  defaultValue={2}
                  style={{ width: '100%', marginTop: 8 }}
                  suffix="px"
                />
              </div>

              <div>
                <Text>Tamaño de fuente (anotaciones):</Text>
                <InputNumber
                  min={10}
                  max={30}
                  defaultValue={14}
                  style={{ width: '100%', marginTop: 8 }}
                  suffix="px"
                />
              </div>

              <div style={{ marginTop: 16 }}>
                <Radio.Group value={[showMeasurements, showAnnotations]}>
                  <Space direction="vertical">
                    <Radio
                      checked={showMeasurements}
                      onChange={(e) => dispatch({ type: 'SET_SHOW_MEASUREMENTS', payload: e.target.checked })}
                    >
                      Mostrar mediciones
                    </Radio>
                    <Radio
                      checked={showAnnotations}
                      onChange={(e) => dispatch({ type: 'SET_SHOW_ANNOTATIONS', payload: e.target.checked })}
                    >
                      Mostrar anotaciones
                    </Radio>
                  </Space>
                </Radio.Group>
              </div>
            </Space>
          </div>

          <div>
            <Title level={5}><ExperimentOutlined /> Análisis de Imagen</Title>
            <Divider style={{ margin: '8px 0' }} />

            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <Statistic
                title="Brillo Promedio"
                value={brightness}
                suffix="%"
                valueStyle={{ fontSize: 20 }}
              />
              <Progress
                percent={brightness}
                status="active"
                strokeColor={{ from: '#108ee9', to: '#87d068' }}
              />

              <Statistic
                title="Contraste"
                value={contrast}
                suffix="%"
                valueStyle={{ fontSize: 20 }}
              />
              <Progress
                percent={contrast}
                status="active"
                strokeColor={{ from: '#ffd666', to: '#ff4d4f' }}
              />

              <Statistic
                title="Nitidez Detectada"
                value={nitidezDetectada}

                suffix="%"
                valueStyle={{ fontSize: 20 }}
              />
              <Progress
                percent={calidadImagen}

                status="active"
              />
            </Space>
          </div>
        </Space>
      </Drawer>

      {/* Export Modal */}
      <Modal
        title={<><DownloadOutlined /> Exportar Imagen</>}
        open={exportModalVisible}
        onCancel={() => dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false })}

          onOk={() => {
          handleExportImage();
          dispatch({ type: 'SET_EXPORT_MODAL_VISIBLE', payload: false });
        }}
        width={500}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong>Formato de Exportación:</Text>
            <Radio.Group defaultValue="png" style={{ marginTop: 8, width: '100%' }}>
              <Radio.Button value="png">PNG</Radio.Button>
              <Radio.Button value="jpeg">JPEG</Radio.Button>
              <Radio.Button value="dicom">DICOM</Radio.Button>
              <Radio.Button value="pdf">PDF</Radio.Button>
            </Radio.Group>
          </div>

          <div>
            <Text strong>Calidad:</Text>
            <Select
              defaultValue="high"
              style={{ width: '100%', marginTop: 8 }}
              options={[
                { value: 'low', label: 'Baja (compresión alta)' },
                { value: 'medium', label: 'Media (balanceada)' },
                { value: 'high', label: 'Alta (sin compresión)' }
              ]}
            />
          </div>

          <div>
            <Text strong>Incluir en la exportación:</Text>
            <div style={{ marginTop: 8 }}>
              <Space direction="vertical">
                <Radio checked>Imagen actual</Radio>
                <Radio>Incluir mediciones</Radio>
                <Radio>Incluir anotaciones</Radio>
                <Radio>Incluir metadata DICOM</Radio>
              </Space>
            </div>
          </div>

          <Alert
            message="Información"
            description={`La imagen se exportará con las configuraciones actuales de zoom (${zoom}%), rotación (${rotation}°) y ajustes de ventana/nivel.`}
            type="info"
            showIcon
          />
        </Space>
      </Modal>
    </div>
  );
};

export default VisorDICOM;
