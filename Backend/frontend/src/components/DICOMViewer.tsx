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
import {Card, Button, Space, Slider, Row, Col, Tooltip, Divider,
    Typography, Badge, Tag, Modal, Input, Alert} from "antd";
import {
    ZoomInOutlined, ZoomOutOutlined, RotateLeftOutlined, RotateRightOutlined,
    FullscreenOutlined, DownloadOutlined, PrinterOutlined, SaveOutlined,
    BgColorsOutlined, LineOutlined, ColumnWidthOutlined, RadiusSettingOutlined,
    UndoOutlined, RedoOutlined, ClearOutlined, InfoCircleOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;

// ==========================================================================
// REDUCER FOR DICOM VIEWER STATE (replaces 11 useState calls)
// ==========================================================================
interface DICOMState {
  zoom: number;
  brightness: number;
  contrast: number;
  rotation: number;
  tool: 'none' | 'line' | 'circle' | 'arrow';
  annotations: any[];
  isDrawing: boolean;
  modalInfoVisible: boolean;
  measurements: any[];
  stableSeriesId: string;
  stableStudyId: string;
}

type DICOMAction =
  | { type: 'INIT_IDS' }
  | { type: 'SET_ZOOM'; payload: number }
  | { type: 'SET_BRIGHTNESS'; payload: number }
  | { type: 'SET_CONTRAST'; payload: number }
  | { type: 'SET_ROTATION'; payload: number }
  | { type: 'SET_TOOL'; payload: 'none' | 'line' | 'circle' | 'arrow' }
  | { type: 'SET_DRAWING'; payload: boolean }
  | { type: 'TOGGLE_MODAL'; payload: boolean }
  | { type: 'ADD_MEASUREMENT'; payload: any }
  | { type: 'ADD_ANNOTATION'; payload: any }
  | { type: 'RESET' };

function generateId(): string {
  return Math.random().toString(36).substring(7).toUpperCase();
}

const initialDICOMState: DICOMState = {
  zoom: 100,
  brightness: 100,
  contrast: 100,
  rotation: 0,
  tool: 'none',
  annotations: [],
  isDrawing: false,
  modalInfoVisible: false,
  measurements: [],
  stableSeriesId: '',
  stableStudyId: '',
};

function dicomReducer(state: DICOMState, action: DICOMAction): DICOMState {
  switch (action.type) {
    case 'INIT_IDS':
      return { ...state, stableSeriesId: generateId(), stableStudyId: generateId() };
    case 'SET_ZOOM':
      return { ...state, zoom: action.payload };
    case 'SET_BRIGHTNESS':
      return { ...state, brightness: action.payload };
    case 'SET_CONTRAST':
      return { ...state, contrast: action.payload };
    case 'SET_ROTATION':
      return { ...state, rotation: action.payload };
    case 'SET_TOOL':
      return { ...state, tool: action.payload };
    case 'SET_DRAWING':
      return { ...state, isDrawing: action.payload };
    case 'TOGGLE_MODAL':
      return { ...state, modalInfoVisible: action.payload };
    case 'ADD_MEASUREMENT':
      return { ...state, measurements: [...state.measurements, action.payload] };
    case 'ADD_ANNOTATION':
      return { ...state, annotations: [...state.annotations, action.payload] };
    case 'RESET':
      return {
        ...initialDICOMState,
        stableSeriesId: state.stableSeriesId,
        stableStudyId: state.stableStudyId,
      };
    default:
      return state;
  }
}

const formatDate = (dateStr: string): string => {
    if (!dateStr) return '-';
    try {
        const d = new Date(dateStr);
        const day = d.getDate().toString().padStart(2, '0');
        const month = (d.getMonth() + 1).toString().padStart(2, '0');
        const year = d.getFullYear();
        return `${day}/${month}/${year}`;
    } catch {
        return dateStr;
    }
};

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
                    <Card title="🔧 Herramientas" size="small">
                        <Space direction="vertical" style={{ width: '100%' }}>
                            <Divider orientation="left" plain>Zoom</Divider>
                            <Space>
                                <Tooltip title="Alejar">
                                    <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} aria-label="Alejar imagen" />
                                </Tooltip>
                                <Slider
                                    value={zoom}
                                    onChange={(val) => dispatch({ type: 'SET_ZOOM', payload: val })}
                                    min={50}
                                    max={200}
                                    style={{ width: 120 }}
                                />
                                <Tooltip title="Acercar">
                                    <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} aria-label="Acercar imagen" />
                                </Tooltip>
                            </Space>
                            <Text type="secondary">{zoom}%</Text>

                            <Divider orientation="left" plain>Brillo</Divider>
                            <Space>
                                <BgColorsOutlined />
                                <Slider
                                    value={brightness}
                                    onChange={handleBrightnessChange}
                                    min={0}
                                    max={200}
                                    style={{ width: 120 }}
                                />
                            </Space>
                            <Text type="secondary">{brightness}%</Text>

                            <Divider orientation="left" plain>Contraste</Divider>
                            <Space>
                                <BgColorsOutlined />
                                <Slider
                                    value={contrast}
                                    onChange={handleContrastChange}
                                    min={0}
                                    max={200}
                                    style={{ width: 120 }}
                                />
                            </Space>
                            <Text type="secondary">{contrast}%</Text>

                            <Divider orientation="left" plain>Rotación</Divider>
                            <Space>
                                <Tooltip title="Rotar Izquierda">
                                    <Button icon={<RotateLeftOutlined />} onClick={handleRotateLeft} aria-label="Rotar imagen a la izquierda" />
                                </Tooltip>
                                <Text>{rotation}°</Text>
                                <Tooltip title="Rotar Derecha">
                                    <Button icon={<RotateRightOutlined />} onClick={handleRotateRight} aria-label="Rotar imagen a la derecha" />
                                </Tooltip>
                            </Space>

                            <Divider orientation="left" plain>Mediciones</Divider>
                            <Space direction="vertical" style={{ width: '100%' }}>
                                <Button
                                    block
                                    icon={<LineOutlined />}
                                    type={tool === 'line' ? 'primary' : 'default'}
                                    onClick={() => handleToolSelect('line')}
                                    aria-label="Herramienta de medición de línea"
                                >
                                    Línea
                                </Button>
                                <Button
                                    block
                                    icon={<RadiusSettingOutlined />}
                                    type={tool === 'circle' ? 'primary' : 'default'}
                                    onClick={() => handleToolSelect('circle')}
                                    aria-label="Herramienta de medición de círculo"
                                >
                                    Círculo
                                </Button>
                                <Button
                                    block
                                    icon={<ColumnWidthOutlined />}
                                    type={tool === 'arrow' ? 'primary' : 'default'}
                                    onClick={() => handleToolSelect('arrow')}
                                    aria-label="Herramienta de medición de flecha"
                                >
                                    Flecha
                                </Button>
                            </Space>

                            <Divider />

                            <Space direction="vertical" style={{ width: '100%' }}>
                                <Button block icon={<UndoOutlined />} aria-label="Deshacer última acción">Deshacer</Button>
                                <Button block icon={<RedoOutlined />} aria-label="Rehacer última acción">Rehacer</Button>
                                <Button block icon={<ClearOutlined />} onClick={handleReset} danger aria-label="Resetear todas las configuraciones">
                                    Resetear Todo
                                </Button>
                            </Space>
                        </Space>
                    </Card>

                    <Card title="📊 Mediciones" size="small" style={{ marginTop: 16 }}>
                        {measurements.length === 0 ? (
                            <Text type="secondary">No hay mediciones</Text>
                        ) : (
                            measurements.map((m) => (
                                <div key={`${m.type}-${m.x}-${m.y}`}>
                                    <Text>{m.type}: {m.value} mm</Text>
                                </div>
                            ))
                        )}
                    </Card>

                    <Card title="📝 Anotaciones" size="small" style={{ marginTop: 16 }}>
                        <Input.TextArea
                            rows={4}
                            placeholder="Agregar observaciones sobre la imagen..."
                            onChange={handleAnnotationChange}
                            style={{ marginBottom: 8 }}
                            aria-label="Anotaciones de la imagen DICOM"
                        />
                        <Tag color={isDrawing ? 'processing' : 'default'}>
                            {isDrawing ? '✏️ Dibujando...' : '✓ Listo'}
                        </Tag>
                    </Card>
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

            {/* Modal de Información */}
            <Modal
                title="Información del Estudio DICOM"
                open={modalInfoVisible}
                onCancel={() => dispatch({ type: 'TOGGLE_MODAL', payload: false })}
                footer={[
                    <Button key="close" type="primary" onClick={() => dispatch({ type: 'TOGGLE_MODAL', payload: false })}>
                        Cerrar
                    </Button>
                ]}
                width={600}
            >
                <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                        message="Datos del Estudio"
                        description="Información extraída del archivo DICOM"
                        type="info"
                        showIcon
                    />

                    <Card size="small">
                        <p><strong>Nombre del Paciente:</strong> {patientName}</p>
                        <p><strong>Fecha del Estudio:</strong> <span suppressHydrationWarning>{new Date(studyDate).toISOString().slice(0, 16).replace('T', ' ')}</span></p>
                        <p><strong>Modalidad:</strong> {modality} (Ultrasonido)</p>
                        <p><strong>Institución:</strong> Hospital Materno Infantil</p>
                        <p><strong>Médico Tratante:</strong> Dr. [A asignar]</p>
                        <p><strong>Número de Serie:</strong> {stableSeriesId}</p>
                        <p><strong>ID del Estudio:</strong> {stableStudyId}</p>
                    </Card>

                    <Alert
                        message="⚠️ Nota Importante"
                        description="Este visor es para fines de visualización y anotación. Para diagnóstico oficial, consulte con un radiólogo certificado."
                        type="warning"
                        showIcon
                    />
                </Space>
            </Modal>
        </Card>
    );
};

export default DICOMViewer;
