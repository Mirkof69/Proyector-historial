import React from 'react';
import { render, screen } from '@testing-library/react';
import RolesDelSistema from './RolesDelSistema';
import cargosService from '../../services/cargosService';

jest.mock('../../services/cargosService', () => ({
  __esModule: true,
  default: { modulos: jest.fn() },
}));

describe('RolesDelSistema', () => {
  it('muestra los roles con sus permisos y al administrador con todo', async () => {
    (cargosService.modulos as jest.Mock).mockResolvedValue([
      { rol: 'recepcion', nombre: 'Recepción', modulos: [
        { modulo: 'citas', nombre: 'Citas', obligatorio: false, acciones: ['view', 'add', 'change'] },
        { modulo: 'consultorios', nombre: 'Consultorios', obligatorio: false, acciones: ['view'] },
      ] },
    ]);
    render(<RolesDelSistema />);
    expect(await screen.findByText('Citas: ver, crear, editar')).toBeInTheDocument();
    expect(screen.getByText('Consultorios: ver')).toBeInTheDocument();
    expect(screen.getByText(/Todo el sistema/)).toBeInTheDocument();
  });
});
