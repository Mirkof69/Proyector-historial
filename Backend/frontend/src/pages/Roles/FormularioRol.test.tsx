import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import FormularioRol from './FormularioRol';
import cargosService from '../../services/cargosService';

// Estable entre renders, como el useAntdApp real (useMemo).
const mockApp = { message: { success: jest.fn(), error: jest.fn() } };
jest.mock('../../hooks/useMessage', () => ({ useAntdApp: () => mockApp }));
jest.mock('../../services/cargosService');

const modulo = (m: string, nombre: string, obligatorio = false, acciones = ['view', 'add', 'change']) =>
  ({ modulo: m, nombre, obligatorio, acciones });

const CATALOGO = [
  { rol: 'medico', nombre: 'Médico', modulos: [modulo('pacientes', 'Pacientes', true), modulo('partos', 'Partos y recién nacidos'), modulo('laboratorio', 'Laboratorio'), modulo('notificaciones', 'Notificaciones', true)] },
  { rol: 'recepcion', nombre: 'Recepción', modulos: [modulo('pacientes', 'Pacientes', true), modulo('citas', 'Citas'), modulo('consultorios', 'Consultorios', false, ['view']), modulo('notificaciones', 'Notificaciones', true)] },
];

const renderNuevo = () => render(
  <MemoryRouter initialEntries={['/dashboard/roles/nuevo']}>
    <Routes>
      <Route path="/dashboard/roles/nuevo" element={<FormularioRol />} />
      <Route path="/dashboard/roles" element={<div>lista de cargos</div>} />
    </Routes>
  </MemoryRouter>,
);

describe('FormularioRol (cargos)', () => {
  beforeEach(() => {
    (cargosService.modulos as jest.Mock).mockResolvedValue(CATALOGO);
    (cargosService.crear as jest.Mock).mockResolvedValue({ id: 9 });
  });

  it('ofrece solo los módulos del rol base y deja fijos los obligatorios', async () => {
    renderNuevo();
    await userEvent.click(await screen.findByRole('combobox'));
    await userEvent.click(await screen.findByTitle('Recepción'));
    expect(await screen.findByRole('checkbox', { name: /Citas/ })).toBeChecked();
    expect(screen.getByRole('checkbox', { name: /Pacientes/ })).toBeDisabled();
    expect(screen.getByText(/solo ver/)).toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: /Partos/ })).not.toBeInTheDocument();
  });

  it('guarda el cargo sin el módulo que se desmarcó', async () => {
    renderNuevo();
    await userEvent.type(await screen.findByPlaceholderText(/Obstetriz/), 'Obstetriz');
    await userEvent.click(screen.getByRole('combobox'));
    await userEvent.click(await screen.findByTitle('Médico'));
    await userEvent.click(await screen.findByRole('checkbox', { name: /Laboratorio/ }));
    await userEvent.click(screen.getByRole('button', { name: /Guardar/ }));
    expect(await screen.findByText('lista de cargos')).toBeInTheDocument();
    expect(cargosService.crear).toHaveBeenCalledWith(expect.objectContaining({
      nombre: 'Obstetriz', rol_base: 'medico', modulos: ['pacientes', 'partos', 'notificaciones'],
    }));
  });
});
