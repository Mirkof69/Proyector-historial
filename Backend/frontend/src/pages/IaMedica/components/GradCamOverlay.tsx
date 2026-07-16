import React from 'react';
import { useAntdApp } from "../../../hooks/useMessage";
import { AnalisisCNNCompleto } from '../../../services/iaMedicaService';

interface GradCamOverlayProps {
  ai: AnalisisCNNCompleto;
  originalUrl: string;
}

const GradCamOverlay: React.FC<GradCamOverlayProps> = ({ ai, originalUrl }) => {
  const { message } = useAntdApp();
  if (!ai.gradcam_base64) return null;
  return (
    <div style={{ position: 'relative', display: 'inline-block', width: '100%' }}>
      <img
        src={originalUrl}
        alt="Ecografía original"
        style={{ width: '100%', display: 'block', borderRadius: 4 }}
      />
      <img
        src={`data:image/png;base64,${ai.gradcam_base64}`}
        alt="Grad-CAM overlay"
        style={{
          position: 'absolute',
          top: 0, left: 0,
          width: '100%',
          opacity: 0.55,
          mixBlendMode: 'multiply',
          borderRadius: 4,
        }}
      />
      <div className="gradcam-badge">
        Grad-CAM: {ai.modelo_version || 'EfficientNet-B4'}
      </div>
    </div>
  );
};

export default GradCamOverlay;
