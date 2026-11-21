import { obtenerValorAnidado, formatearValor } from './excelExport';

describe('obtenerValorAnidado', () => {
  it('obtiene un valor de primer nivel', () => {
    expect(obtenerValorAnidado({ nombre: 'María' }, 'nombre')).toBe('María');
  });

  it('obtiene un valor anidado usando notación de punto', () => {
    const row = { paciente_info: { nombre: 'María', edad: 30 } };
    expect(obtenerValorAnidado(row, 'paciente_info.nombre')).toBe('María');
    expect(obtenerValorAnidado(row, 'paciente_info.edad')).toBe(30);
  });

  it('devuelve cadena vacía si una parte de la ruta es null o undefined', () => {
    expect(obtenerValorAnidado({ paciente_info: null }, 'paciente_info.nombre')).toBe('');
    expect(obtenerValorAnidado({}, 'paciente_info.nombre')).toBe('');
  });
});

describe('formatearValor', () => {
  it('devuelve cadena vacía para null o undefined', () => {
    expect(formatearValor(null)).toBe('');
    expect(formatearValor(undefined)).toBe('');
  });

  it('formatea fechas ISO (YYYY-MM-DD...) a DD/MM/YYYY', () => {
    expect(formatearValor('2026-06-15')).toBe('15/06/2026');
    expect(formatearValor('2026-06-15T10:30:00Z')).toBe('15/06/2026');
  });

  it('convierte booleanos a Sí/No', () => {
    expect(formatearValor(true)).toBe('Sí');
    expect(formatearValor(false)).toBe('No');
  });

  it('convierte objetos/arrays a JSON string', () => {
    expect(formatearValor({ a: 1 })).toBe(JSON.stringify({ a: 1 }));
    expect(formatearValor([1, 2, 3])).toBe(JSON.stringify([1, 2, 3]));
  });

  it('deja números y strings normales sin cambios', () => {
    expect(formatearValor(42)).toBe(42);
    expect(formatearValor('texto normal')).toBe('texto normal');
  });
});
