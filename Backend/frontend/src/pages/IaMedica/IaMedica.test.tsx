import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
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
// La galería busca pacientes en el servidor (PacienteSelect): sin esto la prueba
// salía a la red de verdad y, lenta, se pasaba de los 5 s.
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: { get: jest.fn().mockResolvedValue({ data: { results: [] } }), post: jest.fn() },
  API_URL: 'http://x/api',
}));
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

const informe = (extra: Record<string, unknown>) => ({
  status: 'success', message: 'ok',
  ai_analysis: {
    status: 'success', fuente: 'redes_medidas', version_flujo: '2.0', filename: 'eco1.jpg',
    plano: { plano: 'cerebro fetal', confianza: 0.97, probabilidades: { 'cerebro fetal': 0.97 }, avisos: [] },
    medidas: {}, estructuras_vistas: {}, hallazgos: [], avisos: [], requiere_revision: false,
    modelos_usados: [{ archivo: 'plano_anatomico_fetal_planes', dataset: 'FETAL_PLANES_DB' }],
    informe_texto: 'Plano detectado: cerebro fetal.', tiempo_ms: 80,
    ...extra,
  },
});

const renderPagina = () => render(<MemoryRouter><IaMedica /></MemoryRouter>);

describe('IaMedica - análisis con redes medidas', () => {
  beforeEach(() => {
    (iaMedicaService.getImagenes as jest.Mock).mockResolvedValue({ results: [imagenMock] });
    (iaMedicaService.getEstadisticas as jest.Mock).mockResolvedValue({});
  });

  it('muestra la medida con su margen medido y la red que la produjo', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      medidas: { circunferencia_cefalica_mm: 251.3, margen_hc_mm: 4.41, diametro_biparietal_mm: 66.2, margen_dbp_mm: 1.61 },
      superposicion_url: '/media/gradcams/seg_1.png',
    }));
    renderPagina();
    await userEvent.click(await screen.findByText('Analizar con IA'));
    expect(await screen.findByText('251.3 mm ± 4.41')).toBeInTheDocument();
    expect(screen.getByText('66.2 mm ± 1.61')).toBeInTheDocument();
    expect(screen.getByText('plano_anatomico_fetal_planes')).toBeInTheDocument();
  });

  it('muestra la longitud del fémur y la circunferencia abdominal con su margen', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      plano: { plano: 'fémur fetal', confianza: 0.97, probabilidades: { 'fémur fetal': 0.97 }, avisos: [] },
      medidas: { longitud_femur_mm: 52.4, margen_lf_mm: 1.29, circunferencia_abdominal_mm: 248.1, margen_ca_mm: 6.05 },
    }));
    renderPagina();
    await userEvent.click(await screen.findByText('Analizar con IA'));
    expect(await screen.findByText('52.4 mm ± 1.29')).toBeInTheDocument();
    expect(screen.getByText('248.1 mm ± 6.05')).toBeInTheDocument();
    expect(screen.getByText('Longitud del fémur')).toBeInTheDocument();
  });

  it('no inventa medidas para un plano sin red de medida', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      // El fémur ya tiene red de medida (RF-32); el cuello uterino todavía no.
      plano: { plano: 'cuello uterino materno', confianza: 0.95, probabilidades: { 'cuello uterino materno': 0.95 }, avisos: [] },
      hallazgos: ['Para el plano «cuello uterino materno» no hay una red de medida validada: solo se informa el plano.'],
    }));
    renderPagina();
    await userEvent.click(await screen.findByText('Analizar con IA'));
    expect(await screen.findByText('Sin medidas para este plano')).toBeInTheDocument();
    expect(screen.queryByText(/mm ±/)).not.toBeInTheDocument();
  });

  it('el informe completo se pide desde la tarjeta de redes, sin paciente, con el tamaño de píxel', async () => {
    // jsdom no implementa las URL de objeto: la vista previa local de la imagen las usa.
    URL.createObjectURL = jest.fn(() => 'blob:vista-previa');
    URL.revokeObjectURL = jest.fn();
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      medidas: { circunferencia_cefalica_mm: 87.5, margen_hc_mm: 4.41 },
    }));
    renderPagina();
    // antd esconde el <input type=file>; el primero es el de la tarjeta de redes (el de la galería pide paciente).
    // eslint-disable-next-line testing-library/no-node-access
    const entrada = document.querySelector('input[type="file"]') as HTMLInputElement;
    const archivo = new File(['png'], 'cabeza.png', { type: 'image/png' });
    await userEvent.upload(entrada, archivo);
    await userEvent.type(screen.getByLabelText(/Tamaño de píxel/), '0.075');
    await userEvent.click(screen.getByRole('button', { name: /Informe completo/ }));
    expect(await screen.findByText('87.5 mm ± 4.41')).toBeInTheDocument();
    expect(iaMedicaService.analyzeWithAI).toHaveBeenCalledWith(archivo, undefined, 0.075);
    // Sin imagen guardada no se ofrece la redacción con el LLM local (necesita el id de la imagen).
    expect(screen.queryByRole('button', { name: /Redactar informe/ })).not.toBeInTheDocument();
  });
});
