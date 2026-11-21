import { ROLES, LISTA_ROLES, configuracionDeRol, contarPorRol } from '../roles';

/**
 * El catálogo de roles del frontend tiene que decir lo mismo que el backend.
 *
 * Estos tests fijan un fallo que no daba ningún error y se veía bien:
 * `ROLES_CONFIG` conocía tres roles (`medico`, `enfermero`, `administrador`)
 * mientras `Usuario.ROLES` del backend define cinco, y uno con otra grafía
 * (`enfermera`). El filtro por enfermera devolvía cero siempre, la tarjeta de
 * enfermeras marcaba cero siempre, y en el detalle la etiqueta del rol salía
 * en blanco. Nada fallaba: la pantalla mentía.
 *
 * Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
 */

/**
 * Copiado a mano de `backend/usuarios/models.py`, `Usuario.ROLES`.
 * Si alguien añade un rol allí y no aquí, este test falla y dice cuál.
 */
const ROLES_DEL_BACKEND = ['medico', 'enfermera', 'laboratorista', 'administrador', 'recepcion'];

describe('catálogo de roles', () => {
  it('conoce exactamente los mismos roles que el backend', () => {
    // ESPERADO: los cinco de Usuario.ROLES, ni uno más ni uno menos.
    expect(LISTA_ROLES.slice().sort()).toEqual(ROLES_DEL_BACKEND.slice().sort());
  });

  it('no usa "enfermero" — el backend guarda "enfermera"', () => {
    // Es el fallo original. Mandar 'enfermero' al filtro no encontraba a nadie.
    expect(LISTA_ROLES).not.toContain('enfermero');
    expect(LISTA_ROLES).toContain('enfermera');
  });

  it('da nombre y color a todos los roles', () => {
    ROLES_DEL_BACKEND.forEach((rol) => {
      const config = configuracionDeRol(rol);
      expect(config.nombre).toBeTruthy();
      expect(config.color).toMatch(/^var\(--[a-z0-9-]+\)$/);
    });
  });

  it('los colores son hexadecimales, no palabras de antd', () => {
    // El color se usa como `backgroundColor` del avatar además de en el Tag.
    // 'default', 'blue' y compañía funcionan en el Tag pero dejan el avatar
    // sin fondo, porque no son colores CSS.
    Object.values(ROLES).forEach((config) => {
      expect(config.color).toMatch(/^var\(--[a-z0-9-]+\)$/);
    });
    expect(configuracionDeRol('rol_que_no_existe').color).toMatch(/^var\(--[a-z0-9-]+\)$/);
  });
});

describe('un rol desconocido nunca deja el hueco vacío', () => {
  it('muestra el nombre técnico en vez de una etiqueta en blanco', () => {
    // ESPERADO: se ve 'obstetra', no ''. Una etiqueta vacía se lee como
    // "esta persona no tiene rol", que es una afirmación falsa.
    expect(configuracionDeRol('obstetra').nombre).toBe('obstetra');
  });

  it('sin rol dice "Sin rol"', () => {
    expect(configuracionDeRol(undefined).nombre).toBe('Sin rol');
    expect(configuracionDeRol(null).nombre).toBe('Sin rol');
    expect(configuracionDeRol('').nombre).toBe('Sin rol');
  });
});

describe('conteo por rol', () => {
  it('cuenta a las enfermeras, que antes salían siempre a cero', () => {
    const equipo = [
      { rol: 'enfermera' }, { rol: 'enfermera' }, { rol: 'medico' },
    ];

    const cuenta = contarPorRol(equipo);

    expect(cuenta.enfermera).toBe(2);
    expect(cuenta.medico).toBe(1);
  });

  it('incluye los roles sin nadie, con cero', () => {
    // Si laboratorista no apareciera en el objeto, su tarjeta mostraría
    // "undefined" en vez de 0.
    const cuenta = contarPorRol([{ rol: 'medico' }]);

    ROLES_DEL_BACKEND.forEach((rol) => {
      expect(typeof cuenta[rol]).toBe('number');
    });
    expect(cuenta.laboratorista).toBe(0);
    expect(cuenta.recepcion).toBe(0);
  });

  it('no se rompe con una usuaria sin rol', () => {
    const cuenta = contarPorRol([{ rol: 'medico' }, {}]);

    expect(cuenta.medico).toBe(1);
  });
});
