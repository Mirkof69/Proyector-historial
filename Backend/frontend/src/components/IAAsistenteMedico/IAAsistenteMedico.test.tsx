import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { IAAsistenteMedico } from './IAAsistenteMedico';
import { iaMedicaService } from '../../services/iaMedicaService';

const mockApp = { message: { success: jest.fn(), error: jest.fn() } };
jest.mock('../../hooks/useMessage', () => ({ useAntdApp: () => mockApp }));
jest.mock('../../hooks/useSystemDiagnostics', () => ({
  __esModule: true,
  default: () => ({
    errors: [], isMonitoring: false, toggleMonitoring: jest.fn(), interpretError: jest.fn(), clearErrors: jest.fn(),
    hasErrors: false, criticalErrors: 0, highErrors: 0,
  }),
}));
jest.mock('../../services/statisticsService', () => ({
  __esModule: true, default: { getDashboardStatistics: jest.fn().mockResolvedValue({}) },
}));
jest.mock('../../services/iaMedicaService', () => ({ iaMedicaService: { consultarIA: jest.fn() } }));

const respuesta = (texto: string, categoria = 'preeclampsia') => ({
  consulta: { id: 7, respuesta_ia: texto, categoria, confianza: 80, tiempo_respuesta_ms: 3 },
  nlp_info: { keywords: ['preeclampsia'], confianza: 80 },
});

const renderAsistente = () => render(<MemoryRouter><IAAsistenteMedico /></MemoryRouter>);

describe('Asistente de consulta', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('una consulta rápida SÍ se envía (antes leía el campo vacío y no mandaba nada)', async () => {
    (iaMedicaService.consultarIA as jest.Mock).mockResolvedValue(respuesta('Preeclampsia: PA ≥ 140/90 mmHg.'));
    renderAsistente();
    await userEvent.click(screen.getByRole('button', { name: /Preeclampsia/ }));
    expect(await screen.findByText('Preeclampsia: PA ≥ 140/90 mmHg.')).toBeInTheDocument();
    expect(iaMedicaService.consultarIA).toHaveBeenCalledWith(expect.objectContaining({ consulta: '¿Cómo detectar preeclampsia?' }));
    expect(screen.getByText('Base de conocimiento · Preeclampsia')).toBeInTheDocument();
  });

  it('no muestra una precisión inventada ni confianzas', async () => {
    (iaMedicaService.consultarIA as jest.Mock).mockResolvedValue(respuesta('Texto de la guía.'));
    renderAsistente();
    await userEvent.type(screen.getByLabelText('Consulta al asistente'), 'diabetes gestacional');
    await userEvent.click(screen.getByRole('button', { name: /Enviar/ }));
    expect(await screen.findByText('Texto de la guía.')).toBeInTheDocument();
    expect(screen.queryByText(/Precisión/)).not.toBeInTheDocument();
    expect(screen.queryByText(/% confianza/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/no un modelo entrenado/).length).toBeGreaterThan(0);
  });

  it('si el servicio no responde lo dice, sin inventar una respuesta clínica', async () => {
    (iaMedicaService.consultarIA as jest.Mock).mockRejectedValue(new Error('caído'));
    renderAsistente();
    await userEvent.type(screen.getByLabelText('Consulta al asistente'), 'rciu');
    await userEvent.click(screen.getByRole('button', { name: /Enviar/ }));
    expect(await screen.findByText('Sin conexión')).toBeInTheDocument();
    expect(screen.getByText(/no hay respuesta para «rciu»/)).toBeInTheDocument();
    // eslint-disable-next-line testing-library/no-node-access
    expect(document.body.textContent).not.toMatch(/Confianza\W+\d/);
  });
});
