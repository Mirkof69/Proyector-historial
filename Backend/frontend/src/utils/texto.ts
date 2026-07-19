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
