/**
 * Ant Design y las variables CSS dicen lo mismo, en los cuatro temas.
 *
 * Por qué existe este test
 * ------------------------
 * El sistema de diseño (docs/DISENO_INTERFAZ.md) tiene DOS fuentes de verdad
 * que deben coincidir: `src/styles/tokens.css` (variables CSS que usan las
 * hojas de página) y `src/config/antd-theme-tokens.ts` (tokens que Ant Design
 * aplica a sus componentes). Antes se contradecían: el CSS imponía un color
 * con `!important` y el token de Ant Design decía otro; lo que se veía
 * dependía del orden de carga. Llegó a haber ~600 `!important`.
 *
 * Además fija lo que se arregló a la vista:
 *   - las superficies oscuras son oscuras y el texto se lee (≥ 4,5:1),
 *   - el botón primario es plano (sin degradado ni sombra),
 *   - la capa CSS global no vuelve a pelear con Ant Design por colores.
 *
 * Cada caso declara el resultado ESPERADO y lo compara con el OBTENIDO.
 */

import fs from 'fs';
import path from 'path';

import { getThemeTokens, PALETAS, NombreTema } from '../antd-theme-tokens';

const DIR_ESTILOS = path.join(__dirname, '..', '..', 'styles');
const TEMAS: NombreTema[] = ['light', 'normal', 'dark', 'mocha'];
const OSCUROS: NombreTema[] = ['dark', 'mocha'];

type Componentes = Record<string, Record<string, unknown>>;
const componentes = (t: NombreTema) => getThemeTokens(t).components as Componentes;
const token = (t: NombreTema) => getThemeTokens(t).token as Record<string, unknown>;

/* ---------- utilidades de color ---------- */

function luminancia(hex: string): number {
  const limpio = hex.replace('#', '');
  const [r, g, b] = [0, 2, 4]
    .map((i) => parseInt(limpio.substr(i, 2), 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contraste(a: string, b: string): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
}

/* ---------- lectura de tokens.css ---------- */

const CSS_TOKENS = fs
  .readFileSync(path.join(DIR_ESTILOS, 'tokens.css'), 'utf8')
  .replace(/\/\*[\s\S]*?\*\//g, '');

/** Variables declaradas en el primer bloque cuyo selector contiene `selector`. */
function bloque(selector: string): Record<string, string> {
  const regla = [...CSS_TOKENS.matchAll(/([^{}]+)\{([^}]*)\}/g)].find(([, sel]) =>
    sel.split(',').map((s) => s.trim()).includes(selector),
  );
  if (!regla) throw new Error(`tokens.css no tiene el bloque ${selector}`);
  const vars: Record<string, string> = {};
  for (const [, nombre, valor] of regla[2].matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    vars[nombre] = valor.trim();
  }
  return vars;
}

/** Variables CSS efectivas de un tema (claro + sobrescrituras del tema). */
function variablesDe(tema: NombreTema): Record<string, string> {
  const claro = bloque('html:root');
  if (tema === 'light') return claro;
  return { ...claro, ...bloque(`html.${tema}`) };
}

/** Pareja token de Ant Design ↔ variable CSS que deben valer lo mismo. */
const PAREJAS: Array<[string, string]> = [
  ['colorPrimary', '--color-primario'],
  ['colorLinkHover', '--color-primario-hover'],
  ['colorPrimaryBg', '--color-primario-suave'],
  ['colorTextLightSolid', '--color-sobre-primario'],
  ['colorBgLayout', '--color-fondo'],
  ['colorBgContainer', '--color-superficie'],
  ['colorFillAlter', '--color-superficie-2'],
  ['colorBorder', '--color-borde'],
  ['colorSplit', '--color-borde-suave'],
  ['colorText', '--color-texto'],
  ['colorTextSecondary', '--color-texto-2'],
  ['colorTextTertiary', '--color-texto-3'],
  ['colorSuccess', '--color-exito'],
  ['colorSuccessBg', '--color-exito-suave'],
  ['colorWarning', '--color-aviso'],
  ['colorWarningBg', '--color-aviso-suave'],
  ['colorError', '--color-peligro'],
  ['colorErrorBg', '--color-peligro-suave'],
  ['colorInfo', '--color-info'],
  ['colorInfoBg', '--color-info-suave'],
];

describe('Ant Design y tokens.css coinciden', () => {
  it.each(TEMAS)('tema %s: cada token de Ant Design vale lo mismo que su variable CSS', (tema) => {
    const css = variablesDe(tema);
    const antd = token(tema);
    const distintos = PAREJAS
      .filter(([t, v]) => String(antd[t]).toLowerCase() !== String(css[v]).toLowerCase())
      .map(([t, v]) => `${t}=${antd[t]} ≠ ${v}=${css[v]}`);
    // ESPERADO: ninguna diferencia.
    expect(distintos).toEqual([]);
  });

  it('los valores del contrato están donde dice el documento', () => {
    expect(token('light').colorPrimary).toBe('#155E75');
    expect(token('dark').colorPrimary).toBe('#5BB6CC');
    expect(token('mocha').colorPrimary).toBe('#D9A56B');
    expect(token('light').colorBgLayout).toBe('#F4F6F8');
    expect(token('normal').colorBgLayout).toBe('#FFFFFF');
    expect(token('mocha').colorBgLayout).toBe('#16130F');
  });

  it('usa IBM Plex Sans y los radios 6/8/4', () => {
    const t = token('light');
    expect(String(t.fontFamily)).toMatch(/^'IBM Plex Sans'/);
    expect([t.borderRadius, t.borderRadiusLG, t.borderRadiusSM]).toEqual([6, 8, 4]);
  });
});

describe('legibilidad en los cuatro temas', () => {
  it.each(TEMAS)('tema %s: texto principal y secundario ≥ 4,5:1 sobre superficie', (tema) => {
    const p = PALETAS[tema];
    expect(contraste(p.texto, p.superficie)).toBeGreaterThanOrEqual(4.5);
    expect(contraste(p.texto2, p.superficie)).toBeGreaterThanOrEqual(4.5);
    expect(contraste(p.texto2, p.superficie2)).toBeGreaterThanOrEqual(4.5);
  });

  it.each(TEMAS)('tema %s: el texto del botón primario se lee sobre el primario', (tema) => {
    const p = PALETAS[tema];
    expect(contraste(p.sobrePrimario, p.primario)).toBeGreaterThanOrEqual(4.5);
    expect((componentes(tema).Button as Record<string, string>).primaryColor).toBe(p.sobrePrimario);
  });

  it.each(OSCUROS)('tema %s: las superficies son oscuras de verdad', (tema) => {
    // Antes el tema oscuro pintaba tarjetas casi blancas o transparentes
    // según qué hoja ganara. ESPERADO: luminancia baja en todas.
    const c = componentes(tema);
    const superficies = [
      token(tema).colorBgLayout,
      token(tema).colorBgContainer,
      token(tema).colorBgElevated,
      c.Card.colorBgContainer,
      c.Table.colorBgContainer,
      c.Table.headerBg,
      c.Modal.contentBg,
      c.Layout.siderBg,
      c.Layout.headerBg,
      c.Menu.itemBg,
    ] as string[];
    for (const color of superficies) {
      expect(color).toMatch(/^#[0-9A-Fa-f]{6}$/);
      expect(luminancia(color)).toBeLessThan(0.05);
    }
  });
});

describe('dirección visual', () => {
  it.each(TEMAS)('tema %s: botón primario plano, sin sombra', (tema) => {
    const boton = componentes(tema).Button;
    expect(boton.primaryShadow).toBe('none');
    expect(boton.defaultShadow).toBe('none');
  });

  it.each(TEMAS)('tema %s: el menú activo usa primario-suave y texto primario', (tema) => {
    const menu = componentes(tema).Menu;
    expect(menu.itemSelectedBg).toBe(PALETAS[tema].primarioSuave);
    expect(menu.itemSelectedColor).toBe(PALETAS[tema].primario);
  });

  it('cada superficie flotante tiene fondo y sombra propios en todos los temas', () => {
    for (const tema of TEMAS) {
      const c = componentes(tema);
      for (const nombre of ['Notification', 'Popover', 'Message', 'Dropdown', 'Select', 'DatePicker']) {
        expect(c[nombre]).toHaveProperty('colorBgElevated');
        expect(c[nombre]).toHaveProperty('boxShadowSecondary');
      }
      expect(c.Tooltip).toHaveProperty('colorBgSpotlight');
    }
  });
});

describe('selección de tema', () => {
  it('los cuatro temas tienen configuración propia', () => {
    const configs = new Set(TEMAS.map((t) => getThemeTokens(t)));
    expect(configs.size).toBe(4);
  });

  it('devuelve el mismo objeto en cada llamada (estable entre renders)', () => {
    expect(getThemeTokens('dark')).toBe(getThemeTokens('dark'));
  });

  it('normal es el claro con fondo blanco', () => {
    const claro = token('light');
    const normal = token('normal');
    expect(normal.colorPrimary).toBe(claro.colorPrimary);
    expect(normal.colorText).toBe(claro.colorText);
    expect(normal.colorBgLayout).toBe('#FFFFFF');
  });
});

describe('la capa CSS global no pelea con Ant Design', () => {
  const HOJAS = fs.readdirSync(DIR_ESTILOS).filter((f) => f.endsWith('.css'));
  const sinComentarios = (f: string) =>
    fs.readFileSync(path.join(DIR_ESTILOS, f), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');

  it('ninguna regla global sobre .ant-* usa !important en colores, fondos, bordes o sombras', () => {
    const PROPIEDAD = /^\s*(background|background-color|color|border|border-color|box-shadow)\s*:/;
    const conflictivas = HOJAS.flatMap((f) =>
      [...sinComentarios(f).matchAll(/([^{}]+)\{([^{}]*)\}/g)]
        .filter(([, selector]) => selector.includes('.ant-'))
        .flatMap(([, , cuerpo]) => cuerpo.split('\n'))
        .filter((linea) => linea.includes('!important') && PROPIEDAD.test(linea))
        .map((linea) => `${f}: ${linea.trim()}`),
    );
    // ESPERADO: ninguna. Esos valores los aplica Ant Design desde los tokens.
    expect(conflictivas).toEqual([]);
  });

  it('no queda ningún degradado ni desenfoque en la capa global', () => {
    const encontrados = HOJAS.filter((f) => /gradient\(|backdrop-filter/.test(sinComentarios(f)));
    expect(encontrados).toEqual([]);
  });

  it('solo tokens.css contiene colores fijos', () => {
    const conHex = HOJAS
      .filter((f) => f !== 'tokens.css')
      .filter((f) => /#[0-9a-fA-F]{3,8}\b/.test(sinComentarios(f)));
    expect(conHex).toEqual([]);
  });
});
