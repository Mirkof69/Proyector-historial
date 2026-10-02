import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EcografiaGinecologica from './EcografiaGinecologica';
import api from '../../../services/api';

const mockApp = { message: { success: jest.fn(), error: jest.fn() } };
jest.mock('../../../hooks/useMessage', () => ({ useAntdApp: () => mockApp }));
jest.mock('../../../services/api', () => ({ __esModule: true, default: { post: jest.fn() }, API_URL: 'http://x/api' }));

const elegirImagen = async () => {
  // antd esconde el <input type=file> sin rótulo accesible: no hay otra forma de alcanzarlo.
  // eslint-disable-next-line testing-library/no-node-access
  const entrada = document.querySelector('input[type="file"]') as HTMLInputElement;
  await userEvent.upload(entrada, new File(['png'], 'ovario.png', { type: 'image/png' }));
  // antd procesa el archivo en forma asíncrona: hasta que aparece en la lista, «Analizar» sigue desactivado
  await screen.findByText('ovario.png');
};

describe('EcografiaGinecologica', () => {
  beforeEach(() => jest.clearAllMocks());

  it('muestra la alarma de malignidad con la sensibilidad medida y el tipo probable', async () => {
    (api.post as jest.Mock).mockResolvedValue({ data: {
      tarea: 'ovario', lesion_encontrada: true, tipo_probable: 'Carcinoma seroso de alto grado',
      probabilidades: [{ tipo: 'Carcinoma seroso de alto grado', probabilidad: 0.81 }],
      malignidad: { probabilidad: 0.81, alarma: true, umbral: 0.25, sensibilidad_medida: 0.77, especificidad_medida: 0.95 },
      medidas: { lesion_ancho_mm: 42.5 }, hallazgos: ['Derivar a ginecología oncológica.'], avisos: [],
      superposicion_url: '/media/gradcams/seg_1.png', modelos: [{ archivo: 'clasificador_ovario', dataset: 'MMOTU' }],
    } });
    render(<EcografiaGinecologica />);
    await elegirImagen();
    await userEvent.click(screen.getByRole('button', { name: 'Analizar' }));
    expect(await screen.findByText(/Alarma: rasgos compatibles/)).toBeInTheDocument();
    expect(screen.getByText(/detectó el 77.0 % de los carcinomas/)).toBeInTheDocument();
    expect(screen.getAllByText('Carcinoma seroso de alto grado').length).toBeGreaterThan(0);
    expect(screen.getByText('42.5')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/ia/ginecologia/ovario/', expect.any(FormData), expect.anything());
  });

  it('en mioma deja claro que no descarta cuando no ubica nada', async () => {
    (api.post as jest.Mock).mockResolvedValue({ data: {
      tarea: 'mioma', mioma_ubicado: false, medidas: {}, hallazgos: [], avisos: [], modelos: [{ archivo: 'segmentacion_mioma' }],
    } });
    render(<EcografiaGinecologica />);
    await userEvent.click(screen.getByRole('radio', { name: 'Mioma uterino' }));
    await elegirImagen();
    await userEvent.click(screen.getByRole('button', { name: 'Analizar' }));
    expect(await screen.findByText(/Eso no descarta que lo haya/)).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/ia/ginecologia/mioma/', expect.any(FormData), expect.anything());
  });
});
