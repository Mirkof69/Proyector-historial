import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import IaMedica from './IaMedica';
import { iaMedicaService } from '../../services/iaMedicaService';
import api from '../../services/api';

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
  default: { get: jest.fn(), post: jest.fn() },
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

const guardada = { ...imagenMock, id: 2, estado: 'analizada' as const, tiene_analisis: true, paciente_nombre: 'Rosa Quispe',
  analisis_resultado: { resultado: 'requiere_revision', confianza: 71.2, plano: 'abdomen fetal', fecha: '2026-06-02T00:00:00Z' } };

describe('IaMedica - análisis con redes medidas', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockImplementation((url: string, config?: { params?: Record<string, unknown> }) => {
      if (url !== '/ia/imagenes/') return Promise.resolve({ data: { results: [] } });
      const filas = config?.params?.search === 'Quispe' ? [guardada] : [imagenMock, guardada];
      return Promise.resolve({ data: { count: filas.length, results: filas } });
    });
    (iaMedicaService.getEstadisticas as jest.Mock).mockResolvedValue({});
    (iaMedicaService.clasificarPlano as jest.Mock).mockResolvedValue(null);
    (iaMedicaService.detectarAnomaliasCerebrales as jest.Mock).mockResolvedValue(null);
    // jsdom no implementa las URL de objeto: la vista previa local de la imagen las usa.
    URL.createObjectURL = jest.fn(() => 'blob:vista-previa');
    URL.revokeObjectURL = jest.fn();
  });

  /** Espera a que la tabla termine de cargar: mientras tanto antd bloquea los clics. */
  const clicEnFila = async (texto: string) => {
    const boton = await screen.findByText(texto);
    // eslint-disable-next-line testing-library/no-node-access
    await waitFor(() => expect(document.querySelector('.ant-spin-blur')).toBeNull());
    await userEvent.click(boton);
  };

  const elegirImagen = async () => {
    // antd esconde el <input type=file>.
    // eslint-disable-next-line testing-library/no-node-access
    const entrada = document.querySelector('input[type="file"]') as HTMLInputElement;
    const archivo = new File(['png'], 'cabeza.png', { type: 'image/png' });
    await userEvent.upload(entrada, archivo);
    return archivo;
  };

  it('muestra la medida con su margen medido y la red que la produjo', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      medidas: { circunferencia_cefalica_mm: 251.3, margen_hc_mm: 4.41, diametro_biparietal_mm: 66.2, margen_dbp_mm: 1.61 },
      superposicion_url: '/media/gradcams/seg_1.png',
    }));
    renderPagina();
    await clicEnFila('Analizar con IA');
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
    await clicEnFila('Analizar con IA');
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
    await clicEnFila('Analizar con IA');
    expect(await screen.findByText('Sin medidas para este plano')).toBeInTheDocument();
    expect(screen.queryByText(/mm ±/)).not.toBeInTheDocument();
  });

  it('al poner la imagen muestra la vista del análisis y su resultado, sin guardar si no hay paciente', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      medidas: { circunferencia_cefalica_mm: 87.5, margen_hc_mm: 4.41 },
    }));
    renderPagina();
    const archivo = await elegirImagen();
    expect(await screen.findByAltText('Ecografía elegida')).toHaveAttribute('src', 'blob:vista-previa');
    await userEvent.type(screen.getByLabelText(/Tamaño de píxel/), '0.075');
    await userEvent.click(screen.getByRole('button', { name: /^(scan )?Analizar$/ }));
    expect(await screen.findByText('87.5 mm ± 4.41')).toBeInTheDocument();
    expect(screen.getByText('Sin hallazgos en lo evaluado')).toBeInTheDocument();
    expect(screen.getByAltText('Ecografía original')).toHaveAttribute('src', 'blob:vista-previa');
    expect(iaMedicaService.analyzeWithAI).toHaveBeenCalledWith(archivo, undefined, 0.075);
    expect(iaMedicaService.uploadImagen).not.toHaveBeenCalled();
    expect(screen.getByText('Sin paciente se analiza pero no se guarda.')).toBeInTheDocument();
  });

  it('el veredicto avisa si la red sospecha una anomalía', async () => {
    (iaMedicaService.analyzeWithAI as jest.Mock).mockResolvedValue(informe({
      anomalias_cerebrales: { aplicable: true, alarma_anomalia: true, probabilidad_anomalia: 0.8, umbral: 0.5,
        familia_sospechada: 'fosa_posterior', familia_sospechada_nombre: 'Fosa posterior' },
    }));
    renderPagina();
    await elegirImagen();
    await userEvent.click(screen.getByRole('button', { name: /^(scan )?Analizar$/ }));
    expect(await screen.findByText('Posible anomalía: Fosa posterior')).toBeInTheDocument();
  });

  it('el historial reabre el análisis guardado con los datos de la paciente', async () => {
    (iaMedicaService.getInforme as jest.Mock).mockResolvedValue({
      ...informe({ medidas: { longitud_femur_mm: 52.4, margen_lf_mm: 1.29 }, resultado: 'requiere_revision' }).ai_analysis,
      paciente: { id: 1, nombre: 'Rosa Quispe', ci: '7700101', edad: 33 }, semana_gestacional: 22,
      realizado_por: 'Dra. Ana', fecha_analisis: '2026-06-02T00:00:00Z', imagen_url: '/media/ecografias/2.jpg',
    });
    renderPagina();
    await clicEnFila('Ver análisis');
    expect(await screen.findByText('52.4 mm ± 1.29')).toBeInTheDocument();
    expect(iaMedicaService.getInforme).toHaveBeenCalledWith(2);
    expect(screen.getByText('7700101')).toBeInTheDocument();
    expect(screen.getByText('Dra. Ana')).toBeInTheDocument();
    expect(screen.getByText('Requiere revisión del médico')).toBeInTheDocument();
  });

  it('«requiere revisión» no se pinta como crítico', async () => {
    renderPagina();
    expect(await screen.findByText('Requiere revisión')).toBeInTheDocument();
    expect(screen.queryByText('Crítico')).not.toBeInTheDocument();
  });

  it('el historial busca a la paciente en el servidor y pide de a 10', async () => {
    renderPagina();
    await screen.findByText('María Condori');
    expect(api.get).toHaveBeenCalledWith('/ia/imagenes/', expect.objectContaining({
      params: expect.objectContaining({ page: 1, page_size: 10 }),
    }));
    await userEvent.type(screen.getByLabelText('Buscar paciente por nombre o CI'), 'Quispe');
    await waitFor(() => expect(screen.queryByText('María Condori')).not.toBeInTheDocument());
    expect(screen.getByText('Rosa Quispe')).toBeInTheDocument();
  });
});
