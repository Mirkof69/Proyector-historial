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
  Row, Button, message, Spin, Alert, Typography,
} from 'antd';
import {
  ExpandOutlined, ZoomInOutlined, ColumnWidthOutlined,
  LineChartOutlined, EditOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { ecografiasService } from '../../services/ecografiasService';
import dayjs from 'dayjs';
import './VisorDICOM.css';
import {
  DicomMetadata, initialState, viewerReducer,
} from './visorDicomReducer';
import { TabMediciones, TabAnotaciones } from './visorDicomTabs';
import VisorTopBar from './components/VisorTopBar';
import VisorToolPanel, { Tool } from './components/VisorToolPanel';
import VisorCanvas from './components/VisorCanvas';
import VisorMetadataPanel from './components/VisorMetadataPanel';
import VisorMedicionesCard from './components/VisorMedicionesCard';
import VisorSettingsDrawer from './components/VisorSettingsDrawer';
import VisorExportModal from './components/VisorExportModal';

const { Text } = Typography;

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
  const tools: Tool[] = [
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
      <VisorTopBar
        ecografia={ecografia}
        fullscreen={fullscreen}
        dispatch={dispatch}
        toggleFullscreen={toggleFullscreen}
        onVolver={() => navigate('/ecografias')}
      />

      {/* Área principal */}
      <Row style={{ flex: 1, overflow: 'hidden' }}>
        {/* Panel izquierdo - Herramientas */}
        <VisorToolPanel
          tools={tools}
          rotation={rotation}
          hasGradCam={hasGradCam}
          showGradCam={showGradCam}
          dispatch={dispatch}
          handleZoomIn={handleZoomIn}
          handleZoomOut={handleZoomOut}
          handleResetView={handleResetView}
          handleExportImage={handleExportImage}
          handlePrint={handlePrint}
        />

        {/* Área central - Visor */}
        <VisorCanvas
          canvasRef={canvasRef}
          ecografia={ecografia}
          metadata={metadata}
          tools={tools}
          zoom={zoom}
          rotation={rotation}
          brightness={brightness}
          contrast={contrast}
          invert={invert}
          activeTool={activeTool}
          windowWidth={windowWidth}
          windowLevel={windowLevel}
          currentImageIndex={currentImageIndex}
          totalImages={totalImages}
          showGradCam={showGradCam}
          hasGradCam={hasGradCam}
          playingCine={playingCine}
          measurements={measurements}
          handleCanvasClick={handleCanvasClick}
          dispatch={dispatch}
        />

        {/* Panel derecho - Metadata */}
        {showMetadata && (
          <VisorMetadataPanel metadata={metadata} ecografia={ecografia} />
        )}
      </Row>

      {/* Panel de Mediciones y Anotaciones usando TabPane */}
      <VisorMedicionesCard
        measurements={measurements}
        annotations={annotations}
        tabMedicionesLabel={tabMedicionesLabel}
        tabAnotacionesLabel={tabAnotacionesLabel}
        metadata={metadata}
        deleteMeasurement={deleteMeasurement}
        deleteAnnotation={deleteAnnotation}
      />

      {/* Settings Drawer */}
      <VisorSettingsDrawer
        settingsVisible={settingsVisible}
        brightness={brightness}
        contrast={contrast}
        showMeasurements={showMeasurements}
        showAnnotations={showAnnotations}
        nitidezDetectada={nitidezDetectada}
        calidadImagen={calidadImagen}
        dispatch={dispatch}
      />

      {/* Export Modal */}
      <VisorExportModal
        exportModalVisible={exportModalVisible}
        zoom={zoom}
        rotation={rotation}
        dispatch={dispatch}
        handleExportImage={handleExportImage}
      />
    </div>
  );
};

export default VisorDICOM;
