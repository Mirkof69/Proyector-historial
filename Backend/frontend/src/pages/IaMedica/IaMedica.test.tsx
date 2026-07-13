import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import IaMedica from './IaMedica';
import { iaMedicaService } from '../../services/iaMedicaService';

jest.mock('../../hooks/useMessage', () => ({
  useAntdApp: () => ({
    message: { success: jest.fn(), error: jest.fn(), warning: jest.fn(), info: jest.fn() },
    notification: { success: jest.fn(), error: jest.fn() },
    modal: { confirm: jest.fn(), warning: jest.fn() },
  }),
}));

jest.mock('../../services/iaMedicaService');
jest.mock('../../services/pacientesService', () => ({
  __esModule: true,
  default: { listar: jest.fn().mockResolvedValue([]) },
}));

const imagenMock = {
  id: 1,
  paciente: 1,
  paciente_nombre: 'María Condori',
  url_imagen: '/media/ecografias/1.jpg',
  nombre_original: 'eco1.jpg',
  tipo_imagen: 'eco_2d',
  estado: 'pendiente' as const,
  fecha_subida: '2026-06-01T00:00:00Z',
  tamanio_mb: 1.2,
  resolucion_ancho: 800,
  resolucion_alto: 600,
  es_principal: true,
  tiene_analisis: false,
};

describe('IaMedica - Análisis CNN', () => {
  beforeEach(() => {
    (iaMedicaService.getImagenes as jest.Mock).mockResolvedValue({ results: [imagenMock] });
    (iaMedicaService.getEstadisticas as jest.Mock).mockResolvedValue({});
  });

  it('no inventa una biometría: muestra el mensaje real de "no disponible" cuando el backend lo marca así', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue({
      status: 'ok',
      message: 'Análisis completado',
      ai_analysis: {
        status: 'ok',
        fuente: 'efficientnet_b4',
        modelo_version: 'v1',
        score_global: 0.1,
        pathology_detection: { pathologies: [], total_detected: 0 },
        biometry: {
          disponible: false,
          motivo: 'El módulo de biometría fetal aún no está entrenado con datos reales.',
        },
        shap_risk_scores: {},
      },
    });

    render(<IaMedica />);

    const botonAnalizar = await screen.findByText('EffNetB4 + Grad-CAM');
    await userEvent.click(botonAnalizar);

    await waitFor(() => {
      expect(screen.getByText('Biometría no disponible')).toBeInTheDocument();
    });

    // No debe renderizar ningún valor numérico fabricado de biometría
    // (BPD/HC/AC/FL/peso) cuando el backend indica disponible: false.
    expect(screen.queryByText(/BPD/i)).not.toBeInTheDocument();
  });
});
