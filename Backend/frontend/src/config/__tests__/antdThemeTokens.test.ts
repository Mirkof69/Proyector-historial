/**
 * Las superficies flotantes se estilan por tokens, no por CSS con !important.
 *
 * Por qué existe este test
 * ------------------------
 * `src/styles/` acumuló 389 declaraciones `!important`, casi todas peleando
 * contra Ant Design. La razón era real y no un descuido: Ant Design 5 inyecta
 * sus estilos en tiempo de ejecución, DESPUÉS de las hojas estáticas, así que
 * una regla CSS normal nunca le gana.
 *
 * La salida no es escribir mejor CSS: es dejar de pelear. Los mismos valores
 * puestos como tokens de `ConfigProvider` los aplica el propio Ant Design, sin
 * conflicto y sin `!important`.
 *
 * Este test fija esa migración para las superficies flotantes —tooltip,
 * notificación, popover, mensaje y desplegables—, que eran las que más
 * `!important` gastaban. Si alguien las devuelve al CSS, falla.
 *
 * Cada caso declara el resultado ESPERADO y lo compara con el OBTENIDO.
 */

import fs from 'fs';
import path from 'path';

import { getThemeTokens } from '../antd-theme-tokens';

// Los objetos de tema no se exportan (son detalle interno del módulo): se
// obtienen por la función pública, que es como los consume la aplicación.
const temaOscuro = getThemeTokens('dark');

/** Superficies flotantes que antes se pintaban con !important en el CSS. */
const SUPERFICIES_FLOTANTES = ['Tooltip', 'Notification', 'Popover', 'Message', 'Dropdown'];

/** Clases CSS de esas superficies, tal como las nombra Ant Design. */
const CLASES_FLOTANTES = [
  'ant-tooltip-inner',
  'ant-notification-notice',
  'ant-popover-inner',
  'ant-message-notice-content',
  'ant-select-dropdown',
  'ant-dropdown-menu',
];

const RUTA_CSS = path.join(__dirname, '..', '..', 'styles', 'theme-dark-fixes.css');

/**
 * Lee el CSS sin comentarios.
 *
 * Hace falta porque los comentarios explican POR QUÉ ya no se usa
 * `!important`, y esa palabra dentro de un comentario haría fallar al test
 * sin que hubiera ninguna regla real.
 */
function leerCssSinComentarios(): string {
  return fs.readFileSync(RUTA_CSS, 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
}

/** Declaraciones con !important dentro de los bloques de una clase. */
function importantesDe(clase: string): string[] {
  const css = leerCssSinComentarios();
  return [...css.matchAll(/([^{}]+)\{([^}]*)\}/g)]
    // Limite exacto de clase: `.ant-notification-notice` no debe capturar
    // `.ant-notification-notice-message`, que es el titulo y conserva su
    // propia tipografia (no es una superficie, no se migro a tokens).
    .filter(([, selector]) => new RegExp(`\.${clase}(?![\w-])`).test(selector))
    .flatMap(([, , cuerpo]) =>
      cuerpo
        .split('\n')
        .filter((linea) => linea.includes('!important'))
        .map((linea) => linea.trim()),
    );
}

describe('tokens de Ant Design', () => {
  describe('tema oscuro', () => {
    it.each(SUPERFICIES_FLOTANTES)('%s tiene entrada propia en components', (componente) => {
      expect(temaOscuro.components).toHaveProperty(componente);
    });

    it('cada superficie flotante define su fondo', () => {
      // ESPERADO: colorBgElevated en todas, salvo Tooltip, que en Ant Design
      // usa colorBgSpotlight para lo mismo.
      const comps = temaOscuro.components as Record<string, Record<string, unknown>>;
      for (const nombre of SUPERFICIES_FLOTANTES) {
        const tieneFondo = 'colorBgElevated' in comps[nombre] || 'colorBgSpotlight' in comps[nombre];
        expect(tieneFondo).toBe(true);
      }
    });

    it('el desplegable de Select también', () => {
      const select = (temaOscuro.components as Record<string, Record<string, unknown>>).Select;
      expect(select).toHaveProperty('colorBgElevated');
    });
  });

  describe('el CSS ya no pelea por esas superficies', () => {
    it.each(CLASES_FLOTANTES)('%s no usa ningún !important', (clase) => {
      // ESPERADO: lista vacía. Fondo, color, borde y sombra los aplica ahora
      // Ant Design desde los tokens.
      expect(importantesDe(clase)).toEqual([]);
    });

    it('conserva el desenfoque, que es lo que los tokens no pueden dar', () => {
      // `backdrop-filter` no existe como token de Ant Design, así que se
      // queda en CSS — y nunca necesitó !important, porque Ant Design
      // tampoco lo define y no había nada que sobrescribir.
      const css = leerCssSinComentarios();
      const bloque = /\.ant-tooltip-inner[^{]*\{([^}]*)\}/.exec(css);
      expect(bloque).not.toBeNull();
      expect(bloque![1]).toContain('backdrop-filter');
    });
  });

  describe('selección de tema', () => {
    it('dark y mocha comparten el tema oscuro', () => {
      expect(getThemeTokens('dark')).toBe(getThemeTokens('mocha'));
    });

    it('light y normal comparten el tema claro', () => {
      expect(getThemeTokens('light')).toBe(getThemeTokens('normal'));
    });

    it('el tema claro y el oscuro son distintos', () => {
      expect(getThemeTokens('light')).not.toBe(getThemeTokens('dark'));
    });
  });
});
