import { act, renderHook, waitFor } from '@testing-library/react';
import api from '../services/api';
import { aQuery, limpiarFiltros, ordenDesdeSorter, useListadoServidor } from './useListadoServidor';

jest.mock('../services/api', () => ({ __esModule: true, default: { get: jest.fn() } }));
const get = api.get as jest.Mock;

describe('utilidades del listado en servidor', () => {
  it('no envía filtros vacíos', () => {
    expect(limpiarFiltros({ a: 1, b: '', c: null, d: undefined, e: false })).toEqual({ a: 1, e: false });
  });

  it('traduce el orden de la tabla al del backend', () => {
    expect(ordenDesdeSorter({ field: 'fecha_parto', order: 'descend' } as any)).toBe('-fecha_parto');
    expect(ordenDesdeSorter({ field: 'fecha_parto', order: 'ascend' } as any)).toBe('fecha_parto');
    expect(ordenDesdeSorter({ field: 'fecha_parto', order: undefined } as any)).toBeUndefined();
  });

  it('arma la query para descargas', () => {
    expect(aQuery({ search: 'quispe', tipo: 'x' })).toBe('?search=quispe&tipo=x');
    expect(aQuery({})).toBe('');
  });
});

describe('useListadoServidor', () => {
  beforeEach(() => get.mockReset());

  it('pide SOLO la página visible y usa el total del servidor', async () => {
    get.mockResolvedValue({ data: { count: 3211, results: [{ id: 1 }, { id: 2 }] } });
    const { result } = renderHook(() => useListadoServidor('/pacientes/', { tamanoInicial: 20 }));
    await waitFor(() => expect(result.current.datos).toHaveLength(2));
    expect(result.current.total).toBe(3211);
    expect(get).toHaveBeenLastCalledWith('/pacientes/', { params: { page: 1, page_size: 20 } });
  });

  it('manda búsqueda y filtros al servidor y vuelve a la página 1', async () => {
    get.mockResolvedValue({ data: { count: 0, results: [] } });
    const { result, rerender } = renderHook(
      ({ busqueda }) => useListadoServidor('/partos/', { busqueda, filtros: { tipo_parto: 'cesarea_electiva' }, esperaBusquedaMs: 0 }),
      { initialProps: { busqueda: '' } },
    );
    await waitFor(() => expect(get).toHaveBeenCalled());
    act(() => result.current.onChange({ current: 3, pageSize: 20 }, {}, {} as any));
    await waitFor(() => expect(get.mock.calls.at(-1)[1].params.page).toBe(3));
    rerender({ busqueda: 'quispe' });
    await waitFor(() => expect(get.mock.calls.at(-1)[1].params).toEqual(
      { tipo_parto: 'cesarea_electiva', search: 'quispe', page: 1, page_size: 20 },
    ));
  });

  it('un error deja la lista vacía con mensaje, no la pantalla en blanco', async () => {
    get.mockRejectedValue({ response: { data: { detail: 'Sin permiso' } } });
    const { result } = renderHook(() => useListadoServidor('/partos/'));
    await waitFor(() => expect(result.current.error).toBe('Sin permiso'));
    expect(result.current.datos).toEqual([]);
  });
});
