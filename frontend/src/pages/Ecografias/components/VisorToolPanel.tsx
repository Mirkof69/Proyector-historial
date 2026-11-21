import React from 'react';
import { Col, Button, Space, Tooltip, Divider } from 'antd';
import {
  ZoomInOutlined, ZoomOutOutlined, RotateLeftOutlined, RotateRightOutlined,
  UndoOutlined, DownloadOutlined, PrinterOutlined, FireOutlined,
} from '@ant-design/icons';
import { ViewerAction } from '../visorDicomReducer';

export interface Tool {
  name: string;
  icon: React.ReactNode;
  active: boolean;
  tooltip: string;
}

interface VisorToolPanelProps {
  tools: Tool[];
  rotation: number;
  hasGradCam: boolean;
  showGradCam: boolean;
  dispatch: React.Dispatch<ViewerAction>;
  handleZoomIn: () => void;
  handleZoomOut: () => void;
  handleResetView: () => void;
  handleExportImage: () => void;
  handlePrint: () => void;
}

const VisorToolPanel: React.FC<VisorToolPanelProps> = ({
  tools, rotation, hasGradCam, showGradCam, dispatch,
  handleZoomIn, handleZoomOut, handleResetView, handleExportImage, handlePrint,
}) => (
  <Col className="visor-herramientas">
    <Space direction="vertical" size="middle" className="u-ancho">
      {tools.map(tool => (
        <Tooltip key={tool.name} title={tool.tooltip} placement="right">
          <Button
            type={tool.active ? 'primary' : 'default'}
            icon={tool.icon}
            onClick={() => dispatch({ type: 'SET_ACTIVE_TOOL', payload: tool.name })}

            className="u-ancho"
            size="large"
          />
        </Tooltip>
      ))}
      <Divider className="visor-separador" />
      <Tooltip title="Zoom In" placement="right">
        <Button icon={<ZoomInOutlined />} onClick={handleZoomIn} className="u-ancho" />
      </Tooltip>
      <Tooltip title="Zoom Out" placement="right">
        <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut} className="u-ancho" />
      </Tooltip>
      <Tooltip title="Rotar Izquierda" placement="right">
        <Button
          icon={<RotateLeftOutlined />}
          onClick={() => dispatch({ type: 'SET_ROTATION', payload: rotation - 90 })}

          className="u-ancho"
        />
      </Tooltip>
      <Tooltip title="Rotar Derecha" placement="right">
        <Button
          icon={<RotateRightOutlined />}
          onClick={() => dispatch({ type: 'SET_ROTATION', payload: rotation + 90 })}

          className="u-ancho"
        />
      </Tooltip>
      <Tooltip title="Resetear Vista" placement="right">
        <Button icon={<UndoOutlined />} onClick={handleResetView} className="u-ancho" />
      </Tooltip>
      <Divider className="visor-separador" />

      {hasGradCam && (
        <Tooltip title={showGradCam ? "Ocultar Grad-CAM" : "Mostrar Grad-CAM (Heatmap)"} placement="right">
          <Button
            icon={<FireOutlined />}
            type={showGradCam ? "primary" : "default"}
            danger={showGradCam}
            onClick={() => dispatch({ type: 'SET_SHOW_GRADCAM', payload: !showGradCam })}
            className="u-ancho"
          />
        </Tooltip>
      )}

      <Divider className="visor-separador" />
      <Tooltip title="Exportar" placement="right">
        <Button icon={<DownloadOutlined />} onClick={handleExportImage} className="u-ancho" />
      </Tooltip>
      <Tooltip title="Imprimir" placement="right">
        <Button icon={<PrinterOutlined />} onClick={handlePrint} className="u-ancho" />
      </Tooltip>
    </Space>
  </Col>
);

export default VisorToolPanel;
