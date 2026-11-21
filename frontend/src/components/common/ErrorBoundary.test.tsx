import React from 'react';
import { render, screen } from '@testing-library/react';
import ErrorBoundary, { esVersionNueva } from './ErrorBoundary';

const Rompe: React.FC<{ error: Error }> = ({ error }) => {
  throw error;
};

const errorDeChunk = () => Object.assign(new Error('Loading chunk 812 failed. (missing: http://localhost:3000/static/js/812.abc.chunk.js)'), { name: 'ChunkLoadError' });

describe('ErrorBoundary ante una versión nueva del sistema', () => {
  const recargaOriginal = window.location;
  let reload: jest.Mock;

  beforeEach(() => {
    sessionStorage.clear();
    reload = jest.fn();
    Object.defineProperty(window, 'location', { configurable: true, value: { ...recargaOriginal, reload } });
    jest.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    Object.defineProperty(window, 'location', { configurable: true, value: recargaOriginal });
    jest.restoreAllMocks();
  });

  it('reconoce el error de un archivo de la versión anterior', () => {
    expect(esVersionNueva(errorDeChunk())).toBe(true);
    expect(esVersionNueva(new Error('Loading CSS chunk 7 failed'))).toBe(true);
    expect(esVersionNueva(new TypeError('x is undefined'))).toBe(false);
    expect(esVersionNueva(null)).toBe(false);
  });

  it('recarga sola una vez y no entra en bucle', () => {
    const { unmount } = render(<ErrorBoundary><Rompe error={errorDeChunk()} /></ErrorBoundary>);
    expect(reload).toHaveBeenCalledTimes(1);
    unmount();

    // Si la recarga no lo resolvió, el segundo fallo muestra el aviso en vez de recargar otra vez.
    render(<ErrorBoundary><Rompe error={errorDeChunk()} /></ErrorBoundary>);
    expect(reload).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Hay una versión nueva del sistema')).toBeInTheDocument();
  });

  it('un error común no recarga y muestra el aviso general', () => {
    render(<ErrorBoundary><Rompe error={new TypeError('x is undefined')} /></ErrorBoundary>);
    expect(reload).not.toHaveBeenCalled();
    expect(screen.getByText('Error inesperado en la aplicación')).toBeInTheDocument();
  });
});
