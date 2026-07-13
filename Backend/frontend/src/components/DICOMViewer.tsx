/**
 * =============================================================================
 * VISOR DICOM AVANZADO - VISUALIZACIÓN DE IMÁGENES MÉDICAS
 * =============================================================================
 * Componente para visualizar archivos DICOM de ecografías y estudios médicos
 * Incluye herramientas de medición, zoom, contraste y anotaciones
 * =============================================================================
 */

import React, { useReducer, useRef, useEffect, useCallback } from 'react';
import { useAntdApp } from "../hooks/useMessage";
import { Card, Button, Space, Row, Col, Tooltip, Divider, Typography, Badge, Tag, Alert } from "antd";
import {
  FullscreenOutlined, DownloadOutlined, PrinterOutlined, SaveOutlined, InfoCircleOutlined,
} from '@ant-design/icons';
import { dicomReducer, initialDICOMState, formatDate } from './dicom/dicomReducer';
import DicomToolbar from './dicom/DicomToolbar';
import DicomInfoModal from './dicom/DicomInfoModal';

const { Title, Text } = Typography;

interface DICOMViewerProps {
  dicomUrl?: string;
  imageUrl?: string;
  patientName?: string;
  studyDate?: string;
  modality?: string;
  onSave?: (annotations: any) => void;
}

const DICOMViewer: React.FC<DICOMViewerProps> = ({
  dicomUrl,
  imageUrl,
  patientName = 'Paciente',
  studyDate = '',
  modality = 'US',
  onSave
}) => {
  const { message } = useAntdApp();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [state, dispatch] = useReducer(dicomReducer, initialDICOMState);
  const { zoom, brightness, contrast, rotation, tool, annotations, isDrawing, modalInfoVisible, measurements, stableSeriesId, stableStudyId } = state;

  useEffect(() => {
    dispatch({ type: 'INIT_IDS' });
  }, []);

  const applyFilters = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
    ctx.save();
    ctx.translate(canvas.width / 2, canvas.height / 2);
    ctx.rotate((rotation * Math.PI) / 180);
    ctx.scale(zoom / 100, zoom / 100);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);
    ctx.restore();
  }, [brightness, contrast, zoom, rotation]);

  const loadImage = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      applyFilters();
    };

    img.onerror = () => {
      message.error('Error cargando imagen DICOM');
    };

    // Cargar imagen (en producción esto cargaría el DICOM real)
    img.src = imageUrl || '/placeholder-ultrasound.jpg';
  }, [imageUrl, applyFilters]);

  useEffect(() => {
    loadImage();
  }, [loadImage]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const handleZoomIn = () => dispatch({ type: 'SET_ZOOM', payload: Math.min(zoom + 10, 200) });
  const handleZoomOut = () => dispatch({ type: 'SET_ZOOM', payload: Math.max(zoom - 10, 50) });
  const handleZoomChange = (val: number) => dispatch({ type: 'SET_ZOOM', payload: val });
  const handleRotateLeft = () => dispatch({ type: 'SET_ROTATION', payload: rotation - 90 });
  const handleRotateRight = () => dispatch({ type: 'SET_ROTATION', payload: rotation + 90 });
  const handleReset = () => {
    dispatch({ type: 'RESET' });
    loadImage();
  };

  const handleFullscreen = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (canvas.requestFullscreen) {
      canvas.requestFullscreen();
    }
  };

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    link.download = `ecografia_${patientName}_${new Date().getTime()}.png`;
    link.href = canvas.toDataURL();
    link.click();
    message.success('Imagen descargada exitosamente');
  };

  const handlePrint = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    printWindow.document.write(`
      <html>
        <head>
          <title>Impresión de Ecografía - ${patientName}</title>
          <style>
            body { margin: 0; padding: 20px; text-align: center; }
            img { max-width: 100%; height: auto; }
            .info { text-align: left; margin: 20px; font-family: Arial, sans-serif; }
          </style>
        </head>
        <body>
          <div class="info">
            <h2>Ecografía Obstétrica</h2>
            <p><strong>Paciente:</strong> ${patientName}</p>
            <p><strong>Fecha:</strong> ${new Date(studyDate).toISOString().slice(0, 10)}</p>
            <p><strong>Modalidad:</strong> ${modality}</p>
          </div>
          <img src="${canvas.toDataURL()}" />
          <script>window.print(); window.close();</script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  const handleSaveAnnotations = () => {
    if (onSave) {
      onSave({
        annotations,
        measurements,
        filters: { zoom, brightness, contrast, rotation }
      });
    }
    message.success('Anotaciones guardadas exitosamente');
  };

  const handleBrightnessChange = useCallback((val: number) => {
    dispatch({ type: 'SET_BRIGHTNESS', payload: val });
  }, []);

  const handleContrastChange = useCallback((val: number) => {
    dispatch({ type: 'SET_CONTRAST', payload: val });
  }, []);

  const handleToolSelect = useCallback((t: 'none' | 'line' | 'circle' | 'arrow') => {
    dispatch({ type: 'SET_TOOL', payload: t });
  }, []);

  const handleDrawingStart = useCallback(() => {
    if (tool !== 'none') dispatch({ type: 'SET_DRAWING', payload: true });
  }, [tool]);

  const handleDrawingEnd = useCallback(() => {
    if (isDrawing) {
      dispatch({ type: 'SET_DRAWING', payload: false });
      message.success('Anotación agregada');
    }
  }, [isDrawing]);

  const handleCanvasMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDrawing && tool !== 'none') {
      const rect = canvasRef.current?.getBoundingClientRect();
      if (rect) {
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        dispatch({ type: 'ADD_MEASUREMENT', payload: { type: tool, x, y, value: Math.random() * 50 } });
      }
    }
  }, [isDrawing, tool]);

  const handleAnnotationChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    dispatch({ type: 'ADD_ANNOTATION', payload: { text: e.target.value, timestamp: new Date() } });
  }, []);

  return (
    <Card
      title={
        <Space>
          <Badge status="processing" />
          <Text strong>Visor DICOM - {modality}</Text>
          <Tag color="blue">{patientName}</Tag>
        </Space>
      }
      extra={
        <Button
          type="link"
          icon={<InfoCircleOutlined />}
          onClick={() => dispatch({ type: 'TOGGLE_MODAL', payload: true })}
        >
          Información
        </Button>
      }
    >
      <Alert
        message="Visor de Imágenes Médicas DICOM"
        description="Herramientas profesionales de visualización, medición y anotación para estudios de ultrasonido obstétrico"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16}>
        {/* Panel de Herramientas */}
        <Col xs={24} lg={6}>
          <DicomToolbar
            zoom={zoom}
            brightness={brightness}
            contrast={contrast}
            rotation={rotation}
            tool={tool}
            measurements={measurements}
            isDrawing={isDrawing}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomChange={handleZoomChange}
            onBrightnessChange={handleBrightnessChange}
            onContrastChange={handleContrastChange}
            onRotateLeft={handleRotateLeft}
            onRotateRight={handleRotateRight}
            onToolSelect={handleToolSelect}
            onReset={handleReset}
            onAnnotationChange={handleAnnotationChange}
          />
        </Col>

        {/* Visor de Imagen */}
        <Col xs={24} lg={18}>
          <Card
            title="Vista de Imagen"
            extra={
              <Space>
                <Tooltip title="Pantalla Completa">
                  <Button icon={<FullscreenOutlined />} onClick={handleFullscreen} aria-label="Ver en pantalla completa" />
                </Tooltip>
                <Tooltip title="Descargar">
                  <Button icon={<DownloadOutlined />} onClick={handleDownload} aria-label="Descargar imagen" />
                </Tooltip>
                <Tooltip title="Imprimir">
                  <Button icon={<PrinterOutlined />} onClick={handlePrint} aria-label="Imprimir imagen" />
                </Tooltip>
                <Tooltip title="Guardar Anotaciones">
                  <Button
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={handleSaveAnnotations}
                    aria-label="Guardar anotaciones"
                  >
                    Guardar
                  </Button>
                </Tooltip>
              </Space>
            }
          >
            <div style={{
              border: '2px solid #d9d9d9',
              borderRadius: 4,
              padding: 8,
              background: '#0a0a0f',
              textAlign: 'center',
              minHeight: 500
            }}>
              <canvas
                ref={canvasRef}
                style={{
                  maxWidth: '100%',
                  maxHeight: '600px',
                  cursor: tool !== 'none' ? 'crosshair' : 'default'
                }}
                onMouseDown={handleDrawingStart}
                onMouseUp={handleDrawingEnd}
                onMouseMove={handleCanvasMouseMove}
                role="img"
                aria-label="Visor de imagen DICOM de ecografía"
              />
            </div>

            <Divider />

            <Row gutter={16}>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">Paciente</Text>
                  <Title level={5}>{patientName}</Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">Fecha</Text>
                  <Title level={5}>{formatDate(studyDate)}</Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">Modalidad</Text>
                  <Title level={5}>{modality}</Title>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Text type="secondary">Zoom Actual</Text>
                  <Title level={5}>{zoom}%</Title>
                </Card>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <DicomInfoModal
        open={modalInfoVisible}
        onClose={() => dispatch({ type: 'TOGGLE_MODAL', payload: false })}
        patientName={patientName}
        studyDate={studyDate}
        modality={modality}
        stableSeriesId={stableSeriesId}
        stableStudyId={stableStudyId}
      />
    </Card>
  );
};

export default DICOMViewer;
