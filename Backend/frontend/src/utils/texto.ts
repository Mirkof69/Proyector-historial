/**
 * Comparación de texto para buscadores.
 *
 * Por qué existe: las tablas del sistema filtraban del lado del cliente con
 * `x.toLowerCase().includes(termino.toLowerCase())`, que distingue acentos.
 * Buscar "lopez" descartaba a "López" y dejaba la tabla en 0 filas aunque el
 * backend hubiera devuelto los resultados correctos. En Bolivia los apellidos
 * se escriben indistintamente con y sin tilde (López/Lopez, Cusí/Cusi,
 * Suárez/Suarez), así que una búsqueda sensible a tildes no sirve en recepción.
 *
 * El backend normaliza igual (ver pacientes/busqueda.py) para que el filtro
 * del cliente no descarte lo que el servidor sí encontró.
 */

/** Marcas diacríticas combinantes (tildes, diéresis, etc.) que NFD separa. */
const DIACRITICOS = /\p{Diacritic}/gu;

/** Minúsculas y sin tildes. */
export const normalizarTexto = (texto?: string | null): string =>
    (texto ?? '').normalize('NFD').replace(DIACRITICOS, '').toLowerCase();

/** ¿`texto` contiene `termino`, ignorando tildes y mayúsculas? */
export const incluyeTexto = (texto: string | null | undefined, termino: string): boolean =>
    normalizarTexto(texto).includes(normalizarTexto(termino));

/**
 * `filterOption` para los Select con buscador: compara la etiqueta visible
 * (`label` o el texto de `children`) sin tildes ni mayúsculas.
 */
export const filtrarOpcion = (entrada: string, opcion?: { label?: unknown; children?: unknown }): boolean => {
    const visible = opcion?.label ?? opcion?.children;
    const texto = Array.isArray(visible) ? visible.filter((p) => typeof p === 'string').join(' ') : String(visible ?? '');
    return incluyeTexto(texto, entrada);
};

/**
 * Personal para elegir en un Select: primero las cuentas reales y por nombre;
 * las de las pruebas de QA (correo «.test») al final, para que no tapen a las demás.
 */
export const ordenarPersonal = <T extends { email?: string; nombre?: string; apellido_paterno?: string }>(lista: T[]): T[] =>
    [...lista].sort((a, b) => {
        const pruebaA = (a.email ?? '').endsWith('.test') ? 1 : 0;
        const pruebaB = (b.email ?? '').endsWith('.test') ? 1 : 0;
        if (pruebaA !== pruebaB) return pruebaA - pruebaB;
        return `${a.nombre ?? ''} ${a.apellido_paterno ?? ''}`.localeCompare(`${b.nombre ?? ''} ${b.apellido_paterno ?? ''}`, 'es');
    });
