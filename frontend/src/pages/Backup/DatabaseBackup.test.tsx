import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from 'antd';
import DatabaseBackup from './DatabaseBackup';
import { backupService } from '../../services/backupService';

jest.mock('../../services/backupService', () => ({
  backupService: {
    listar: jest.fn(),
    crear: jest.fn(),
    eliminar: jest.fn(),
    descargar: jest.fn(),
    restaurar: jest.fn(),
  },
}));

const respaldo = {
  filename: 'backup_manual_20261029_090000.sql',
  size: 1024,
  size_formatted: '1 KB',
  created_at: '2026-10-29T09:00:00',
};

const abrirRestaurar = async () => {
  render(<App><DatabaseBackup /></App>);
  // fireEvent: mientras la tabla termina de cargar, el Spin le pone pointer-events: none
  fireEvent.click(await screen.findByRole('button', { name: `Restaurar ${respaldo.filename}` }));
  return screen.findByLabelText('Confirmación de restauración');
};
const botonRestaurar = () => screen.getByRole('button', { name: /sí, restaurar/i });

describe('DatabaseBackup — restaurar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (backupService.listar as jest.Mock).mockResolvedValue([respaldo]);
    (backupService.restaurar as jest.Mock).mockResolvedValue({ success: true, backup_seguridad: 'pre.sql' });
  });

  it('restaura cuando se escribe RESTAURAR', async () => {
    // Antes el onOk del modal leía el estado del primer render ('') y
    // rechazaba siempre: «Restaurar» no se podía usar desde la pantalla.
    const campo = await abrirRestaurar();
    expect(botonRestaurar()).toBeDisabled();
    await userEvent.type(campo, 'RESTAURAR');
    await waitFor(() => expect(botonRestaurar()).toBeEnabled());
    await userEvent.click(botonRestaurar());
    await waitFor(() => expect(backupService.restaurar).toHaveBeenCalledWith(respaldo.filename));
  });

  it('no restaura si la confirmación no coincide', async () => {
    const campo = await abrirRestaurar();
    await userEvent.type(campo, 'restaurar mal');
    expect(botonRestaurar()).toBeDisabled();
    fireEvent.click(botonRestaurar());
    expect(backupService.restaurar).not.toHaveBeenCalled();
  });
});
