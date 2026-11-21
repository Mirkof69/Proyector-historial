import { curvaPartograma } from './partogramaUtils';

const h = (horas: number) => new Date(Date.UTC(2026, 9, 1, 8) + horas * 3_600_000).toISOString();

describe('curvaPartograma (líneas de alerta y acción de la OMS)', () => {
  it('sin registros no inventa curva', () => {
    expect(curvaPartograma([])).toMatchObject({ puntos: [], alerta: [], cruzaAlerta: false, velocidadActiva: null });
  });

  it('la fase activa empieza en el primer tacto de 4 cm o más', () => {
    const c = curvaPartograma([
      { hora_registro: h(0), dilatacion_cervical: 2 },
      { hora_registro: h(2), dilatacion_cervical: 4 },
      { hora_registro: h(4), dilatacion_cervical: 6 },
    ]);
    expect(c.alerta).toEqual([{ horas: 2, dilatacion: 4 }, { horas: 8, dilatacion: 10 }]);
    expect(c.accion).toEqual([{ horas: 6, dilatacion: 4 }, { horas: 12, dilatacion: 10 }]);
  });

  it('progreso de 1 cm/h o más: no cruza la alerta', () => {
    const c = curvaPartograma([4, 5, 6.5, 8, 10].map((d, i) => ({ hora_registro: h(i), dilatacion_cervical: d })));
    expect([c.cruzaAlerta, c.cruzaAccion]).toEqual([false, false]);
    expect(c.velocidadActiva).toBe(1.5);
  });

  it('progreso lento: cruza la alerta pero aún no la acción', () => {
    const c = curvaPartograma([
      { hora_registro: h(0), dilatacion_cervical: 4 },
      { hora_registro: h(3), dilatacion_cervical: 5 },
    ]);
    expect([c.cruzaAlerta, c.cruzaAccion]).toEqual([true, false]);
  });

  it('detención: cruza la línea de acción', () => {
    const c = curvaPartograma([
      { hora_registro: h(0), dilatacion_cervical: 4 },
      { hora_registro: h(6), dilatacion_cervical: 5 },
    ]);
    expect([c.cruzaAlerta, c.cruzaAccion]).toEqual([true, true]);
  });

  it('ordena por hora aunque lleguen desordenados', () => {
    const c = curvaPartograma([
      { hora_registro: h(2), dilatacion_cervical: 7, fcf_baseline: 140 },
      { hora_registro: h(0), dilatacion_cervical: 5, fcf_baseline: 150 },
    ]);
    expect(c.puntos).toEqual([{ horas: 0, dilatacion: 5, fcf: 150 }, { horas: 2, dilatacion: 7, fcf: 140 }]);
  });
});
