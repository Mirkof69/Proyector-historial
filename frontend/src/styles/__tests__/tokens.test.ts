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

/** Capa global que importa src/index.tsx (contrato docs/DISENO_INTERFAZ.md). */
const ARCHIVOS_CARGADOS = [
  'tokens.css',
  'base.css',
  'antd.css',
  'layout.css',
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

  it('las hojas que se peleaban entre sí ya no existen', () => {
    // 4.900 líneas en seis archivos que existían para corregirse unos a otros.
    const retiradas = [
      'global-theme.css', 'antd-overrides.css', 'theme-dark.css',
      'theme-dark-fixes.css', 'theme-enhancements.css',
    ].filter((f) => fs.existsSync(path.join(DIRECTORIO, f)));
    expect(retiradas).toEqual([]);
  });

  it('toda variable CSS que se usa en src/ está definida en algún sitio', () => {
    // Los alias de compatibilidad de tokens.css cubren los nombres antiguos
    // (--text-primary, --bg-elevated…). Una variable sin definir hace que la
    // propiedad entera se ignore: texto invisible o tarjetas sin fondo.
    const SRC = path.join(DIRECTORIO, '..');
    const usadas = new Set<string>();
    const definidas = new Set<string>();
    const recorrer = (dir: string) => {
      for (const nombre of fs.readdirSync(dir)) {
        const ruta = path.join(dir, nombre);
        if (fs.statSync(ruta).isDirectory()) {
          recorrer(ruta);
        } else if (/\.(css|tsx?)$/.test(nombre) && !/\.test\.tsx?$/.test(nombre)) {
          const texto = fs.readFileSync(ruta, 'utf8');
          for (const m of texto.matchAll(/var\((--[\w-]+)/g)) usadas.add(m[1]);
          for (const m of texto.matchAll(/(--[\w-]+)['"]?\s*:/g)) definidas.add(m[1]);
        }
      }
    };
    recorrer(SRC);
    // Un nombre que acaba en «-» es un prefijo de plantilla (`var(--grafico-${n})`)
    // o texto de un comentario, no una variable.
    const sinDefinir = [...usadas]
      .filter((v) => !v.endsWith('-') && !definidas.has(v))
      .sort();
    expect(sinDefinir).toEqual([]);
  });

  it('define las variables de transición que usan los componentes', () => {
    const definiciones = leerDefiniciones();
    for (const variable of ['--transition-fast', '--transition-base', '--transition-slow']) {
      expect(definiciones.has(variable)).toBe(true);
    }
  });
});
