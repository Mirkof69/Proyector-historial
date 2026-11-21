import { imcRedondeado } from './imc';

describe('imcRedondeado', () => {
  it('64 kg y 1,60 m dan exactamente 25 (antes 24,999… → «Normal»)', () => {
    expect(imcRedondeado(64, 1.6)).toBe(25);
  });

  it('76,8 kg y 1,60 m dan exactamente 30', () => {
    expect(imcRedondeado(76.8, 1.6)).toBe(30);
  });
});
