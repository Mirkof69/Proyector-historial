/**
 * Los tokens de diseño no pueden tener dos valores distintos.
 *
 * Por qué existe este test
 * ------------------------
 * `src/styles/` llegó a tener 7 archivos CSS con 5.245 líneas y 389
 * `!important`. Cuando la misma variable se define en dos archivos con
 * valores distintos, cuál gana depende del orden de importación y no del
 * diseño: por eso tocar una pantalla rompía otra.
 *
 * Este test recorre los archivos que realmente se cargan y falla si alguna
 * variable tiene valores en conflicto. Es la red que impide que la
 * consolidación se deshaga con el tiempo.
 *
 * Cada caso declara el resultado ESPERADO y lo compara con el OBTENIDO.
 */

import fs from 'fs';
import path from 'path';

const DIRECTORIO = path.join(__dirname, '..');

/** Archivos que el código importa de verdad (verificado con grep). */
const ARCHIVOS_CARGADOS = [
  'variables-claude.css',
  'theme-enhancements.css',
  'theme-dark-fixes.css',
  'global-theme.css',
  'antd-overrides.css',
  'theme-dark.css',
];

type Definiciones = Map<string, Map<string, string>>;

function leerDefiniciones(): Definiciones {
  const porVariable: Definiciones = new Map();

  for (const nombre of ARCHIVOS_CARGADOS) {
    const ruta = path.join(DIRECTORIO, nombre);
    if (!fs.existsSync(ruta)) continue;

    const texto = fs.readFileSync(ruta, 'utf8');
    const patron = /(--[a-zA-Z0-9-]+)\s*:\s*([^;]{1,80});/g;
    let coincidencia: RegExpExecArray | null;

    while ((coincidencia = patron.exec(texto)) !== null) {
      const [, variable, valor] = coincidencia;
      if (!porVariable.has(variable)) porVariable.set(variable, new Map());
      const porArchivo = porVariable.get(variable)!;
      // Solo la primera definición de cada archivo: las repeticiones dentro
      // de un mismo archivo son variantes de tema, no conflictos.
      if (!porArchivo.has(nombre)) porArchivo.set(nombre, valor.trim());
    }
  }
  return porVariable;
}

describe('tokens de diseño', () => {
  it('ninguna variable tiene valores distintos en archivos distintos', () => {
    const conflictos: string[] = [];

    for (const [variable, porArchivo] of leerDefiniciones()) {
      const valores = new Set(porArchivo.values());
      if (valores.size > 1) {
        const detalle = [...porArchivo]
          .map(([archivo, valor]) => `      ${archivo} = ${valor}`)
          .join('\n');
        conflictos.push(`  ${variable}\n${detalle}`);
      }
    }

    // ESPERADO: ningún conflicto. OBTENIDO antes de la consolidación: 3
    // (--transition-fast, --transition-base, --transition-slow).
    expect(conflictos.join('\n')).toBe('');
  });

  it('el archivo de tema muerto ya no existe', () => {
    // 373 líneas que definían un tema naranja completo y no se importaban
    // desde ningún sitio: al auditar los conflictos aparecían como reales.
    const muerto = path.join(DIRECTORIO, 'variables-clinical-dark.css');
    expect(fs.existsSync(muerto)).toBe(false);
  });

  it('define las variables de transición que usan los componentes', () => {
    const definiciones = leerDefiniciones();
    for (const variable of ['--transition-fast', '--transition-base', '--transition-slow']) {
      expect(definiciones.has(variable)).toBe(true);
    }
  });
});
