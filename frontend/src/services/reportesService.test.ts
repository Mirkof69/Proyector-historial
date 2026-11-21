import { formatoAlBackend, formatoDelBackend, normalizeListResponse } from './reportesService';

describe('formatoAlBackend', () => {
  it('convierte "pdf" al código interno real del backend "pd"', () => {
    expect(formatoAlBackend('pdf')).toBe('pd');
  });

  it('deja otros formatos sin cambios (ej. "excel")', () => {
    expect(formatoAlBackend('excel')).toBe('excel');
  });
});

describe('formatoDelBackend', () => {
  it('convierte el código interno "pd" de vuelta a "pdf" para mostrar en la UI', () => {
    expect(formatoDelBackend('pd')).toBe('pdf');
  });

  it('deja otros formatos sin cambios (ej. "excel")', () => {
    expect(formatoDelBackend('excel')).toBe('excel');
  });

  it('es el inverso exacto de formatoAlBackend para "pdf"', () => {
    expect(formatoDelBackend(formatoAlBackend('pdf'))).toBe('pdf');
  });
});

describe('normalizeListResponse', () => {
  it('devuelve el array directamente si la respuesta ya es un array', () => {
    const data = [{ id: 1 }, { id: 2 }];
    expect(normalizeListResponse(data)).toEqual(data);
  });

  it('extrae "results" de una respuesta paginada de DRF', () => {
    const data = { count: 2, next: null, previous: null, results: [{ id: 1 }, { id: 2 }] };
    expect(normalizeListResponse(data)).toEqual([{ id: 1 }, { id: 2 }]);
  });

  it('extrae "data" cuando la respuesta viene envuelta en { data: [...] }', () => {
    const data = { data: [{ id: 1 }] };
    expect(normalizeListResponse(data)).toEqual([{ id: 1 }]);
  });

  it('devuelve un array vacío si la respuesta no coincide con ningún formato conocido', () => {
    expect(normalizeListResponse({ algo: 'inesperado' })).toEqual([]);
  });

  it('devuelve un array vacío si la respuesta es null o undefined', () => {
    expect(normalizeListResponse(null)).toEqual([]);
    expect(normalizeListResponse(undefined)).toEqual([]);
  });
});
