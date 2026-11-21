import { decimalesANumero } from './decimales';

describe('decimalesANumero', () => {
  it('pasa a número los decimales que la API manda como texto', () => {
    // ESPERADO: 20, que la regla { type: 'number', min: 10 } acepta (con «20.0» la editaba como inválida).
    expect(decimalesANumero({ altura_uterina: '20.0', temperatura: '36.6' }, ['altura_uterina', 'temperatura']))
      .toEqual({ altura_uterina: 20, temperatura: 36.6 });
  });

  it('deja vacío lo vacío y no toca los demás campos', () => {
    expect(decimalesANumero({ talla: null, peso: '', ci: '0012' }, ['talla', 'peso']))
      .toEqual({ talla: null, peso: undefined, ci: '0012' });
  });
});
