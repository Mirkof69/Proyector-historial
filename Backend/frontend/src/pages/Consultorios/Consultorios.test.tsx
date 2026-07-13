import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Consultorios from './Consultorios';
import { consultoriosService } from '../../services/consultoriosService';

jest.mock('../../hooks/useAuth', () => ({
  useAuth: () => ({ user: { id: 1, nombre: 'Test User' } }),
}));

jest.mock('../../hooks/useMessage', () => ({
  useAntdApp: () => ({
    message: { success: jest.fn(), error: jest.fn(), warning: jest.fn(), info: jest.fn() },
    notification: { success: jest.fn(), error: jest.fn() },
    modal: { confirm: jest.fn(), warning: jest.fn() },
  }),
}));

jest.mock('../../services/consultoriosService');

describe('Consultorios - columna Capacidad', () => {
  // Regresión de la Fase 11: el frontend usaba el campo "capacidad", que no
  // existe en el backend real (el modelo expone "capacidad_personas"). La
  // columna siempre aparecía vacía. Este test falla si alguien vuelve a usar
  // el nombre de campo equivocado en la tabla.
  it('muestra la capacidad real del consultorio (capacidad_personas) en la tabla', async () => {
    (consultoriosService.getAll as jest.Mock).mockResolvedValue([
      {
        id: 1,
        codigo: 'C-001',
        nombre: 'Consultorio 1',
        tipo: 'general',
        area: 'Planta baja',
        piso: 1,
        capacidad_personas: 5,
        estado: 'disponible',
        tiene_camilla: true,
        tiene_escritorio: true,
        tiene_computadora: true,
      },
    ]);

    render(
      <MemoryRouter>
        <Consultorios />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });
});
