import { evaluarRiesgoPreeclampsia } from './riesgoPreeclampsia';

describe('evaluarRiesgoPreeclampsia', () => {
  it('una preeclampsia previa sola ya es riesgo alto (antes salía «moderado»)', () => {
    const r = evaluarRiesgoPreeclampsia({ preeclampsiaPrevia: true });
    expect(r.nivel).toBe('alto');
    expect(r.aspirina).toMatch(/150 mg/);
  });

  it('dos factores moderados dan riesgo moderado; uno solo, bajo', () => {
    expect(evaluarRiesgoPreeclampsia({ nuliparidad: true, edadMaterna: 36 }).nivel).toBe('moderado');
    expect(evaluarRiesgoPreeclampsia({ nuliparidad: true, edadMaterna: 28 }).nivel).toBe('bajo');
  });

  it('la PA alta no suma como factor: se avisa aparte', () => {
    const r = evaluarRiesgoPreeclampsia({ presionSistolica: 150, presionDiastolica: 95, proteinuria: true });
    expect(r.nivel).toBe('bajo');
    expect(r.alertaHipertension).toMatch(/criterios de preeclampsia/);
  });
});
