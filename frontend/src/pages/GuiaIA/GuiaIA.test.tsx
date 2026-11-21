import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import GuiaIA from './GuiaIA';
import * as contenido from './guiaContenido';
import { iaMedicaService } from '../../services/iaMedicaService';

jest.mock('../../services/iaMedicaService', () => ({ iaMedicaService: { getModelos: jest.fn() } }));

/** Los 15 modelos en servicio que devuelve hoy GET /api/ia/imagenes/modelos/ (tests/test_guia_ia.py los comprueba). */
const EN_SERVICIO = [
  'plano_anatomico_fetal_planes', 'segmentacion_cabeza', 'segmentacion_torax', 'segmentacion_abdomen',
  'biometria_femur', 'biometria_abdomen', 'segmentacion_intraparto', 'anomalias_cerebrales_fetales',
  'circunferencia_cefalica_hc18', 'segmentacion_ovario', 'clasificador_ovario', 'segmentacion_mioma',
  'clasificador_ovario_pco', 'cardiotocografia', 'peso_nacimiento',
];

const modelo = (codigo: string, extra: Record<string, unknown> = {}) => ({
  codigo, nombre: `Modelo ${codigo}`, tipo: 'clasificación de imagen (CNN)', origen: 'microservicio',
  disponible: true, metrica_principal: `Cifra medida de ${codigo}`, datos: `Datos de ${codigo}`, datos_reales: true, ...extra,
});

const Ubicacion: React.FC = () => {
  const l = useLocation();
  return <div data-testid="ubicacion">{l.pathname}{l.search}</div>;
};

const renderGuia = () => render(
  <MemoryRouter initialEntries={['/dashboard/ia-guia']}>
    <Routes>
      <Route path="/dashboard/ia-guia" element={<GuiaIA />} />
      <Route path="*" element={<Ubicacion />} />
    </Routes>
  </MemoryRouter>,
);

describe('Guía de IA', () => {
  beforeEach(() => jest.clearAllMocks());

  it('muestra cada modelo con la cifra que manda el backend, no una escrita en la pantalla', async () => {
    (iaMedicaService.getModelos as jest.Mock).mockResolvedValue({
      modelos_builtin: EN_SERVICIO.map((c) => modelo(c)), modelos_descartados: [], total: EN_SERVICIO.length,
    });
    renderGuia();
    for (const codigo of EN_SERVICIO) {
      // eslint-disable-next-line no-await-in-loop
      expect(await screen.findByText(`Cifra medida de ${codigo}`)).toBeInTheDocument();
    }
    expect(screen.getAllByRole('button', { name: /^Usar ahora:/ })).toHaveLength(EN_SERVICIO.length);
  });

  it('«Usar ahora» lleva a la pantalla exacta donde se usa el modelo', async () => {
    (iaMedicaService.getModelos as jest.Mock).mockResolvedValue({
      modelos_builtin: [modelo('clasificador_ovario', { nombre: 'Tipo de lesión ovárica' })], total: 1,
    });
    renderGuia();
    await userEvent.click(await screen.findByRole('button', { name: 'Usar ahora: Tipo de lesión ovárica' }));
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/dashboard/ia-medica/imagenes?pestana=ginecologia');
  });

  it('el ángulo de progresión lleva a Partos y la cardiotocografía a su pestaña', async () => {
    (iaMedicaService.getModelos as jest.Mock).mockResolvedValue({
      modelos_builtin: [modelo('segmentacion_intraparto', { nombre: 'AoP' })], total: 1,
    });
    renderGuia();
    await userEvent.click(await screen.findByRole('button', { name: 'Usar ahora: AoP' }));
    expect(screen.getByTestId('ubicacion')).toHaveTextContent('/dashboard/partos');
    expect(contenido.FICHAS.cardiotocografia.donde.ruta).toBe('/dashboard/ia-medica/imagenes?pestana=cardiotocografia');
  });

  it('los descartados salen con su motivo y sin botón para usarlos', async () => {
    (iaMedicaService.getModelos as jest.Mock).mockResolvedValue({
      modelos_builtin: [],
      modelos_descartados: [{ codigo: 'translucencia_nucal', nombre: 'Translucencia nucal', tipo: 'CNN',
        datos: 'Shenzhen', metrica: 'Cifra del entrenamiento', motivo: 'No generaliza a otro centro.' }],
      total: 0,
    });
    renderGuia();
    expect(await screen.findByText('No generaliza a otro centro.')).toBeInTheDocument();
    expect(screen.getByText('Descartado')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Usar ahora/ })).not.toBeInTheDocument();
  });

  it('sin respuesta del servidor no muestra ninguna cifra', async () => {
    (iaMedicaService.getModelos as jest.Mock).mockRejectedValue(new Error('caído'));
    renderGuia();
    expect(await screen.findByText('No se pudo cargar la lista de modelos')).toBeInTheDocument();
    expect(screen.getByText(/supervisados/)).toBeInTheDocument(); // la explicación sigue
    // eslint-disable-next-line testing-library/no-node-access
    expect(document.body.textContent).not.toMatch(/\d+([.,]\d+)?\s?%/);
  });

  it('cada modelo en servicio tiene su ficha, y las fichas no traen cifras propias', () => {
    EN_SERVICIO.forEach((c) => expect(contenido.FICHAS[c]).toBeDefined());
    const texto = JSON.stringify([contenido.FICHAS, contenido.GRUPOS, contenido.NO_ES_IA]);
    expect(texto).not.toMatch(/\d+([.,]\d+)?\s?(%|mm\b)/);
  });
});
