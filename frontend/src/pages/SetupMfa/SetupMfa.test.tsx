/**
 * El QR del MFA se pide UNA sola vez al entrar.
 *
 * Cada pedido genera un secreto nuevo en el servidor: si se pedía dos veces
 * (StrictMode en desarrollo, o un remontaje) la pantalla podía mostrar un
 * secreto y el servidor guardar el otro, y el primer código de Google
 * Authenticator salía «inválido» (E2E de cargos, 14/10/2026).
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { App as AntdApp } from 'antd';
import SetupMfa from './SetupMfa';
import { authService } from '../../services/authService';

jest.mock('../../hooks/useAuth', () => ({ useAuth: () => ({ refreshAuth: jest.fn() }) }));

describe('SetupMfa', () => {
  beforeEach(() => {
    jest.spyOn(authService, 'isAuthenticated').mockReturnValue(false);
    jest.spyOn(authService, 'hasMfaSetupToken').mockReturnValue(true);
  });

  afterEach(() => jest.restoreAllMocks());

  it('pide el QR una sola vez aunque React monte la pantalla dos veces', async () => {
    const pedir = jest.spyOn(authService, 'setupMfaInicial').mockResolvedValue({
      secret: 'JBSWY3DPEHPK3PXP', qr_code: 'data:image/png;base64,AAAA', uri: 'otpauth://totp/x', mensaje: '',
    } as any);

    render(
      <React.StrictMode>
        <AntdApp>
          <MemoryRouter>
            <SetupMfa />
          </MemoryRouter>
        </AntdApp>
      </React.StrictMode>,
    );

    expect(await screen.findByText('JBSWY3DPEHPK3PXP')).toBeInTheDocument();
    expect(pedir).toHaveBeenCalledTimes(1);
  });
});
