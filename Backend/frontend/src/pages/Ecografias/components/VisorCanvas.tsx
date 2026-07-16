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
);

export default VisorCanvas;
