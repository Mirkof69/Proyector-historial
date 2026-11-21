import { hadlock3p, hadlock4p, hadlockCaLf, hadlockCcCaLf, pesoFetalEstimado } from './pesoFetal';

// Los mismos casos que el backend (`ecografias/peso_fetal.py`): pantalla y
// servidor tienen que dar el mismo número.
describe('peso fetal (Hadlock 1985) con medidas en milímetros', () => {
  it('coincide con el backend', () => {
    expect(hadlock4p(90, 320, 330, 70)).toBe(2959);
    expect(hadlock4p(48, 177, 154, 33)).toBe(354);
    expect(hadlock4p(78, 285, 270, 58)).toBe(1660);
  });

  it('un feto de término no pesa 0 g (el error de la calculadora básica)', () => {
    const peso = hadlock3p(90, 330, 70) as number;
    expect(peso).toBeGreaterThan(2500);
    expect(peso).toBeLessThan(3500);
  });

  it('si faltan medidas o las unidades son absurdas devuelve null, nunca 0', () => {
    expect(hadlock4p(90, null, 330, 70)).toBeNull();
    expect(hadlock4p(9, 32, 33, 7)).toBeNull(); // centímetros metidos como milímetros
  });

  it('sin circunferencia cefálica usa la fórmula de 3 parámetros', () => {
    expect(pesoFetalEstimado({ dbp: 90, ca: 330, lf: 70 })?.formula).toContain('DBP, CA, LF');
    expect(pesoFetalEstimado({ dbp: 90, cc: 320, ca: 330, lf: 70 })?.peso).toBe(2959);
  });

  it('las cuatro variantes dan un peso de término razonable', () => {
    for (const peso of [hadlockCaLf(330, 70), hadlockCcCaLf(320, 330, 70), hadlock3p(90, 330, 70), hadlock4p(90, 320, 330, 70)]) {
      expect(peso).toBeGreaterThan(2600);
      expect(peso).toBeLessThan(3400);
    }
  });
});
