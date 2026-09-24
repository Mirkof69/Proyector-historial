import { clasificarIla } from './liquidoAmniotico';

describe('clasificarIla', () => {
  it('usa los mismos bordes que el backend', () => {
    const esperado: Array<[number, string]> = [
      [4, 'oligohidramnios'],
      [5, 'oligohidramnios'],
      [5.1, 'limite_bajo'],
      [7.9, 'limite_bajo'],
      [8, 'normal'],
      [22, 'normal'],
      [24.9, 'normal'],
      [25, 'polihidramnios'],
    ];
    esperado.forEach(([ila, codigo]) => expect(clasificarIla(ila).codigo).toBe(codigo));
  });

  it('gradúa el polihidramnios', () => {
    expect(clasificarIla(26).texto).toBe('Polihidramnios leve');
    expect(clasificarIla(31).texto).toBe('Polihidramnios moderado');
    expect(clasificarIla(36).texto).toBe('Polihidramnios severo');
  });

  it('un ILA de 20 es normal (antes una calculadora lo marcaba como límite alto)', () => {
    expect(clasificarIla(20).color).toBe('green');
  });
});
