import { evaluarDiabetesGestacional } from './diabetesGestacional';

describe('diabetes gestacional (PTOG 75 g, IADPSG/OMS)', () => {
  it('UN solo valor alterado ya es diabetes gestacional (antes se perdía)', () => {
    expect(evaluarDiabetesGestacional(85, 190, 130).diagnostico).toBe('diabetes_gestacional');
    expect(evaluarDiabetesGestacional(92, 120, 120).diagnostico).toBe('diabetes_gestacional');
    expect(evaluarDiabetesGestacional(80, 150, 153).diagnostico).toBe('diabetes_gestacional');
  });

  it('justo por debajo de los cortes es normal', () => {
    expect(evaluarDiabetesGestacional(91, 179, 152).diagnostico).toBe('normal');
  });

  it('ayunas ≥ 126 es diabetes manifiesta, no gestacional', () => {
    expect(evaluarDiabetesGestacional(130).diagnostico).toBe('diabetes_manifiesta');
    expect(evaluarDiabetesGestacional(100, 210, 205).diagnostico).toBe('diabetes_manifiesta');
  });

  it('dice qué valores salieron alterados', () => {
    expect(evaluarDiabetesGestacional(95, 185, 140).alterados).toEqual(['Ayunas 95 ≥ 92', '1 hora 185 ≥ 180']);
  });
});
