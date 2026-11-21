import React from 'react';
import { Card, Row, Col, Button, Space, Slider, Typography, Badge, Tabs } from 'antd';
import {
  LineChartOutlined, BorderOutlined, SaveOutlined, CameraOutlined,
  EyeOutlined, SyncOutlined, FileImageOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { ViewerAction, DicomMetadata } from '../visorDicomReducer';
import { Tool } from './VisorToolPanel';

const { Text } = Typography;

interface VisorCanvasProps {
  canvasRef: React.RefObject<HTMLCanvasElement>;
  ecografia: any;
  metadata: DicomMetadata;
  tools: Tool[];
  zoom: number;
  rotation: number;
  brightness: number;
  contrast: number;
  invert: boolean;
  activeTool: string;
  windowWidth: number;
  windowLevel: number;
  currentImageIndex: number;
  totalImages: number;
  showGradCam: boolean;
  hasGradCam: boolean;
  playingCine: boolean;
  measurements: any[];
  handleCanvasClick: (event: React.MouseEvent<HTMLCanvasElement>) => void;
  dispatch: React.Dispatch<ViewerAction>;
}

const VisorCanvas: React.FC<VisorCanvasProps> = ({
  canvasRef, ecografia, metadata, tools, zoom, rotation, brightness, contrast,
  invert, activeTool, windowWidth, windowLevel, currentImageIndex, totalImages,
  showGradCam, hasGradCam, playingCine, measurements, handleCanvasClick, dispatch,
}) => (
  <Col flex="auto" className="u-flex u-columna">
    {/* Canvas principal */}
    <div className="visor-lienzo">
      <canvas
        ref={canvasRef}
        width={512}
        height={512}
        // El canvas responde al clic, asi que es un control: necesita nombre
        // accesible y rol. Sin esto un lector de pantalla solo anuncia
        // "imagen" y no dice que se puede interactuar con ella.
        role="button"
        tabIndex={0}
        aria-label="Imagen de la ecografia: haga clic para medir sobre ella"
        onClick={handleCanvasClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleCanvasClick(e as unknown as React.MouseEvent<HTMLCanvasElement>);
          }
        }}
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
          filter: `brightness(${brightness}%) contrast(${contrast}%) ${invert ? 'invert(1)' : ''}`,
          cursor: activeTool === 'pan' ? 'move' : activeTool === 'zoom' ? 'zoom-in' : 'crosshair',
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
        <div className="visor-marcador">
          <FileImageOutlined className="u-t-icono u-mb-4" />
          <div className="u-t-md">
            Viewer DICOM Placeholder
          </div>
          <div className="u-t-xs u-mt-2">
            Integrar con cornerstone.js o OHIF Viewer
          </div>
        </div>
      )}
    </div>

    {/* Controles inferiores */}
    <Card
      size="small"
      className="visor-controles"
    >
      <Tabs
        type="card"
        size="small"
        items={[
          {
            key: '1',
            label: 'Ajustes de Imagen',
            children: (
              <Row gutter={16} align="middle">
                <Col xs={12} md={6}>
                  <Text className="u-t-xs">Brillo: {brightness}%</Text>
                  <Slider
                    min={0}
                    max={200}
                    value={brightness}
                    onChange={(v) => dispatch({ type: 'SET_BRIGHTNESS', payload: v })}

                  />
                </Col>
                <Col xs={12} md={6}>
                  <Text className="u-t-xs">Contraste: {contrast}%</Text>
                  <Slider
                    min={0}
                    max={200}
                    value={contrast}
                    onChange={(v) => dispatch({ type: 'SET_CONTRAST', payload: v })}

                  />
                </Col>
                <Col xs={12} md={6}>
                  <Text className="u-t-xs">Window Width: {windowWidth}</Text>
                  <Slider
                    min={1}
                    max={200}
                    value={windowWidth}
                    onChange={(v) => dispatch({ type: 'SET_WINDOW_WIDTH', payload: v })}

                  />
                </Col>
                <Col xs={12} md={6}>
                  <Text className="u-t-xs">Window Level: {windowLevel}</Text>
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
                  className="visor-deslizador"
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
);

export default VisorCanvas;
