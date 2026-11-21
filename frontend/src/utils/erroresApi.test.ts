import { aplanarErrores } from './erroresApi';

describe('aplanarErrores', () => {
  it('lee los errores anidados del recién nacido (antes «[object Object]»)', () => {
    const datos = { recien_nacidos: [{ peso_nacimiento: ['El mínimo es 300 g.'] }] };
    expect(aplanarErrores(datos)).toEqual(['recien nacidos › peso nacimiento: El mínimo es 300 g.']);
  });

  it('numera cuando hay varios elementos con error y omite non_field_errors', () => {
    const datos = { recien_nacidos: [{ apgar_1_minuto: ['Máximo 10'] }, { apgar_5_minutos: ['Máximo 10'] }], non_field_errors: ['Revise'] };
    expect(aplanarErrores(datos)).toEqual([
      'recien nacidos › n.º 1 › apgar 1 minuto: Máximo 10',
      'recien nacidos › n.º 2 › apgar 5 minutos: Máximo 10',
      'Revise',
    ]);
  });
});
