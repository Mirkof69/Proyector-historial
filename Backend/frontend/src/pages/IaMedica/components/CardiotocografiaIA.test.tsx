import React from 'react';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CardiotocografiaIA from './CardiotocografiaIA';
import HistorialCardiotocografias from './HistorialCardiotocografias';
import api from '../../../services/api';

const mockApp = { message: { success: jest.fn(), error: jest.fn(), warning: jest.fn() } };
jest.mock('../../../hooks/useMessage', () => ({ useAntdApp: () => mockApp }));
jest.mock('../../../services/api', () => ({ __esModule: true, default: { post: jest.fn(), get: jest.fn() }, API_URL: 'http://x/api' }));
// El buscador real de pacientes pide al servidor; aquí basta con elegir una.
jest.mock('../../../components/clinico/SelectoresClinicos', () => ({
  PacienteSelect: ({ onChange }: { onChange: (id?: number, p?: { nombre_completo: string }) => void }) => (
    <button type="button" onClick={() => onChange(7, { nombre_completo: 'Rosa Quispe' })}>Elegir a Rosa Quispe</button>
  ),
}));

const VARIABLES = [
  { clave: 'linea_base', etiqueta: 'Línea de base de la FCF', unidad: 'lpm', minimo: 50, maximo: 220 },
  { clave: 'aceleraciones', etiqueta: 'Aceleraciones', unidad: 'por segundo', minimo: 0, maximo: 0.1 },
];
const RESULTADO = {
  clase: 'sospechosa', clase_nombre: 'Sospechosa',
  probabilidades: { normal: 0.3, sospechosa: 0.6, patologica: 0.1 }, advertencias: ['Apoyo a la lectura.'],
};
const REGISTRO = {
  id: 3, paciente: 7, paciente_nombre: 'Rosa Quispe', semana_gestacional: 36, clase: 'patologica', clase_nombre: 'Patológica',
  probabilidades: { normal: 0.05, sospechosa: 0.15, patologica: 0.8 }, advertencias: [], modelo_version: '1.2',
  realizado_por_nombre: 'Ana Ctg', fecha: '2026-11-07T10:00:00Z',
  valores_etiquetados: [{ clave: 'linea_base', etiqueta: 'Línea de base de la FCF', unidad: 'lpm', valor: 98 }],
};

describe('Cardiotocografía guardada por paciente', () => {
  beforeEach(() => jest.clearAllMocks());

  const llenarYClasificar = async () => {
    await userEvent.type(await screen.findByLabelText('Línea de base de la FCF (lpm)'), '132');
    await userEvent.type(screen.getByLabelText('Aceleraciones (por segundo)'), '0.006');
    await userEvent.click(screen.getByRole('button', { name: 'Clasificar' }));
  };

  it('sin paciente clasifica y avisa que no se guarda', async () => {
    (api.get as jest.Mock).mockResolvedValue({ data: { variables: VARIABLES, modelo: {} } });
    (api.post as jest.Mock).mockResolvedValue({ data: { ...RESULTADO, guardado: false } });
    render(<CardiotocografiaIA />);
    expect(await screen.findByText('Sin paciente se clasifica pero no se guarda.')).toBeInTheDocument();
    await llenarYClasificar();
    expect(await screen.findByText('Sospechosa', { selector: '.ia-ctg-clase' })).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/ia/cardiotocografia/', { linea_base: 132, aceleraciones: 0.006 });
    expect(screen.queryByText(/Guardado en el historial/)).not.toBeInTheDocument();
  });

  it('con paciente envía su id, confirma que quedó en su historial y avisa para recargar', async () => {
    (api.get as jest.Mock).mockResolvedValue({ data: { variables: VARIABLES, modelo: {} } });
    (api.post as jest.Mock).mockResolvedValue({ data: { ...RESULTADO, guardado: true, registro_id: 3 } });
    const onGuardado = jest.fn();
    render(<CardiotocografiaIA onGuardado={onGuardado} />);
    await userEvent.click(await screen.findByRole('button', { name: 'Elegir a Rosa Quispe' }));
    expect(screen.getByText('La clasificación quedará en su historial.')).toBeInTheDocument();
    await llenarYClasificar();
    expect(await screen.findByText('Guardado en el historial de Rosa Quispe')).toBeInTheDocument();
    expect(api.post).toHaveBeenCalledWith('/ia/cardiotocografia/', { linea_base: 132, aceleraciones: 0.006, paciente_id: 7 });
    expect(onGuardado).toHaveBeenCalledTimes(1);
  });

  it('el historial de la ficha pide solo las de la paciente y abre el registro con sus valores', async () => {
    (api.get as jest.Mock).mockResolvedValue({ data: { count: 1, results: [REGISTRO] } });
    render(<HistorialCardiotocografias pacienteId={7} />);
    const fila = await screen.findByRole('row', { name: /Ana Ctg/ });
    expect(within(fila).getByText('Patológica')).toBeInTheDocument();
    expect(within(fila).getByText('80.0 %')).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/ia/cardiotocografias/', { params: expect.objectContaining({ paciente_id: 7, page: 1, page_size: 10 }) });
    // En la ficha no se repite el nombre de la paciente en cada fila.
    expect(screen.queryByRole('columnheader', { name: 'Paciente' })).not.toBeInTheDocument();
    await userEvent.click(within(fila).getByRole('button', { name: /Ver registro/ }));
    const modal = await screen.findByRole('dialog', { name: 'Cardiotocografía de Rosa Quispe' });
    expect(within(modal).getByText('Línea de base de la FCF (lpm)')).toBeInTheDocument();
    expect(within(modal).getByText('98')).toBeInTheDocument();
  });
});
