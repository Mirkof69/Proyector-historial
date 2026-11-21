import dayjs from 'dayjs';
import { rangoDePreset } from './rangoReportes';

describe('rangoDePreset', () => {
  const hoy = dayjs('2026-10-15T14:30:00');
  const f = (d: dayjs.Dayjs) => d.format('YYYY-MM-DD HH:mm');

  it('hoy va de 00:00 a 23:59 del mismo día', () => {
    expect(rangoDePreset('hoy', hoy).map(f)).toEqual(['2026-10-15 00:00', '2026-10-15 23:59']);
  });
  it('7 días incluye hoy y los 6 anteriores', () => {
    expect(rangoDePreset('semana', hoy).map(f)).toEqual(['2026-10-09 00:00', '2026-10-15 23:59']);
  });
  it('este mes empieza el día 1', () => {
    expect(f(rangoDePreset('mes', hoy)[0])).toBe('2026-10-01 00:00');
  });
  it('este año empieza el 1 de enero', () => {
    expect(f(rangoDePreset('anio', hoy)[0])).toBe('2026-01-01 00:00');
  });
});
