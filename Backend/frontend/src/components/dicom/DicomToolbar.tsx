import React from 'react';
import { Card, Space, Divider, Tooltip, Button, Slider, Typography, Input, Tag } from 'antd';
import {
  ZoomInOutlined, ZoomOutOutlined, BgColorsOutlined, RotateLeftOutlined, RotateRightOutlined,
  LineOutlined, RadiusSettingOutlined, ColumnWidthOutlined, UndoOutlined, RedoOutlined, ClearOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

type Tool = 'none' | 'line' | 'circle' | 'arrow';

interface DicomToolbarProps {
  zoom: number;
  brightness: number;
  contrast: number;
  rotation: number;
  tool: Tool;
  measurements: any[];
  isDrawing: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomChange: (val: number) => void;
  onBrightnessChange: (val: number) => void;
  onContrastChange: (val: number) => void;
  onRotateLeft: () => void;
  onRotateRight: () => void;
  onToolSelect: (t: Tool) => void;
  onReset: () => void;
  onAnnotationChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}

const DicomToolbar: React.FC<DicomToolbarProps> = ({
  zoom, brightness, contrast, rotation, tool, measurements, isDrawing,
  onZoomIn, onZoomOut, onZoomChange, onBrightnessChange, onContrastChange,
  onRotateLeft, onRotateRight, onToolSelect, onReset, onAnnotationChange,
}) => (
  <>
    <Card title="🔧 Herramientas" size="small">
      <Space direction="vertical" style={{ width: '100%' }}>
        <Divider orientation="left" plain>Zoom</Divider>
        <Space>
          <Tooltip title="Alejar">
            <Button icon={<ZoomOutOutlined />} onClick={onZoomOut} aria-label="Alejar imagen" />
          </Tooltip>
          <Slider value={zoom} onChange={onZoomChange} min={50} max={200} style={{ width: 120 }} />
          <Tooltip title="Acercar">
            <Button icon={<ZoomInOutlined />} onClick={onZoomIn} aria-label="Acercar imagen" />
          </Tooltip>
        </Space>
        <Text type="secondary">{zoom}%</Text>

        <Divider orientation="left" plain>Brillo</Divider>
        <Space>
          <BgColorsOutlined />
          <Slider value={brightness} onChange={onBrightnessChange} min={0} max={200} style={{ width: 120 }} />
        </Space>
        <Text type="secondary">{brightness}%</Text>

        <Divider orientation="left" plain>Contraste</Divider>
        <Space>
          <BgColorsOutlined />
          <Slider value={contrast} onChange={onContrastChange} min={0} max={200} style={{ width: 120 }} />
        </Space>
        <Text type="secondary">{contrast}%</Text>

        <Divider orientation="left" plain>Rotación</Divider>
        <Space>
          <Tooltip title="Rotar Izquierda">
            <Button icon={<RotateLeftOutlined />} onClick={onRotateLeft} aria-label="Rotar imagen a la izquierda" />
          </Tooltip>
          <Text>{rotation}°</Text>
          <Tooltip title="Rotar Derecha">
            <Button icon={<RotateRightOutlined />} onClick={onRotateRight} aria-label="Rotar imagen a la derecha" />
          </Tooltip>
        </Space>

        <Divider orientation="left" plain>Mediciones</Divider>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button
            block
            icon={<LineOutlined />}
            type={tool === 'line' ? 'primary' : 'default'}
            onClick={() => onToolSelect('line')}
            aria-label="Herramienta de medición de línea"
          >
            Línea
          </Button>
          <Button
            block
            icon={<RadiusSettingOutlined />}
            type={tool === 'circle' ? 'primary' : 'default'}
            onClick={() => onToolSelect('circle')}
            aria-label="Herramienta de medición de círculo"
          >
            Círculo
          </Button>
          <Button
            block
            icon={<ColumnWidthOutlined />}
            type={tool === 'arrow' ? 'primary' : 'default'}
            onClick={() => onToolSelect('arrow')}
            aria-label="Herramienta de medición de flecha"
          >
            Flecha
          </Button>
        </Space>

        <Divider />

        <Space direction="vertical" style={{ width: '100%' }}>
          <Button block icon={<UndoOutlined />} aria-label="Deshacer última acción">Deshacer</Button>
          <Button block icon={<RedoOutlined />} aria-label="Rehacer última acción">Rehacer</Button>
          <Button block icon={<ClearOutlined />} onClick={onReset} danger aria-label="Resetear todas las configuraciones">
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
        onChange={onAnnotationChange}
        style={{ marginBottom: 8 }}
        aria-label="Anotaciones de la imagen DICOM"
      />
      <Tag color={isDrawing ? 'processing' : 'default'}>
        {isDrawing ? '✏️ Dibujando...' : '✓ Listo'}
      </Tag>
    </Card>
  </>
);

export default DicomToolbar;
