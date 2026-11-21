// Cada rol recorre TODO su menú lateral con las animaciones del sistema apagadas
// (prefers-reduced-motion, como el equipo donde los desplegables se iban fuera
// de la pantalla). En cada pantalla falla si:
//   - hay un error de JavaScript o un 500 de la API,
//   - la API responde 403 a algo que el menú le ofrece a ese rol,
//   - la pantalla dice «sin permiso», «no encontrada» o «Error inesperado»,
//   - la página desborda hacia los lados,
//   - un desplegable o calendario abierto cae fuera de la pantalla.
// Además abre el menú del perfil y la campana, y sigue una notificación.
const crypto = require('crypto');
const { test, expect } = require('@playwright/test');

const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
// Las cuentas se pueden cambiar por variables de entorno (la base real no tiene
// las de la demo). Sin la variable, ese rol usa la cuenta de la demo.
const ROLES = [
  ['administrador', process.env.E2E_ADMIN_EMAIL || 'admin.demo@fetalmedical.bo'],
  ['médico', process.env.E2E_MEDICO_EMAIL || 'dra.garcia@fetalmedical.bo'],
  ['enfermería', process.env.E2E_ENFERMERIA_EMAIL || 'enf.mamani@fetalmedical.bo'],
  ['recepción', process.env.E2E_RECEPCION_EMAIL || 'recep.flores@fetalmedical.bo'],
  ...(process.env.E2E_LABORATORIO_EMAIL ? [['laboratorio', process.env.E2E_LABORATORIO_EMAIL]] : []),
];

/** Código TOTP (RFC 6238) del secreto que muestra la pantalla de MFA. */
const totp = (secreto) => {
  const alfabeto = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  let bits = '';
  for (const c of secreto.replace(/=+$/, '')) bits += alfabeto.indexOf(c).toString(2).padStart(5, '0');
  const clave = Buffer.from(bits.match(/.{8}/g).map((b) => parseInt(b, 2)));
  const contador = Buffer.alloc(8);
  contador.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const h = crypto.createHmac('sha1', clave).update(contador).digest();
  const o = h[h.length - 1] & 0xf;
  return String((h.readUInt32BE(o) & 0x7fffffff) % 1000000).padStart(6, '0');
};
// «403» solo como «Error 403»: suelto es la última página del paginador, y dentro
// de un código de paciente o un teléfono es un dato.
const AVISOS = /no tiene permiso|acceso denegado|página no encontrada|error inesperado|error 403/i;

test.use({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } });
test.setTimeout(300_000); // el administrador tiene 26 pantallas

async function entrar(page, email) {
  await page.goto('/login');
  await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', email);
  await page.fill('input[placeholder="Ingrese su contraseña"]', PASSWORD);
  await page.click('button[type=submit]');
  // En producción médico y administrador configuran el MFA la primera vez.
  const configurar = page.getByRole('button', { name: /Configurar Google Authenticator/ });
  await Promise.race([page.waitForURL((u) => !u.pathname.includes('login')), configurar.waitFor()]);
  if (await configurar.isVisible()) {
    await configurar.click();
    const secreto = (await page.locator('.ant-typography code').first().innerText()).trim();
    await page.getByRole('button', { name: /Ya escaneé el QR/ }).click();
    await page.fill('input[placeholder="000000"]', totp(secreto));
    await page.getByRole('button', { name: /Activar MFA/ }).click();
    await page.waitForURL((u) => u.pathname.startsWith('/dashboard'), { timeout: 15000 });
  }
}

/** Rutas del menú lateral, con los submenús abiertos. */
async function rutasDelMenu(page) {
  const menu = page.locator('.ant-layout-sider .ant-menu').first();
  await menu.waitFor();
  for (let i = 0; i < 3; i += 1) {
    const cerrados = menu.locator('.ant-menu-submenu:not(.ant-menu-submenu-open) > .ant-menu-submenu-title');
    const n = await cerrados.count();
    if (!n) break;
    for (let j = 0; j < n; j += 1) await cerrados.nth(0).click();
  }
  const claves = await menu.locator('li.ant-menu-item').evaluateAll((lis) =>
    lis.map((li) => (li.getAttribute('data-menu-id') || '').replace(/^.*?(\/dashboard\/)/, '$1')));
  return [...new Set(claves.filter((c) => c.startsWith('/dashboard/')))];
}

/** Abre hasta 4 desplegables y 2 calendarios de la pantalla; devuelve los que caen fuera. */
async function desplegablesFuera(page) {
  return page.evaluate(async () => {
    const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
    const visible = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && r.top < innerHeight; };
    const abierto = () => [...document.querySelectorAll('.ant-select-dropdown:not(.ant-select-dropdown-hidden), .ant-picker-dropdown:not(.ant-picker-dropdown-hidden)')]
      .find((e) => getComputedStyle(e).display !== 'none');
    const cerrar = async () => {
      document.activeElement?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
      document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
      document.activeElement?.blur?.();
      await esperar(200);
    };
    const main = document.querySelector('.ant-layout-content') || document.body;
    const disparadores = [
      ...[...main.querySelectorAll('.ant-select:not(.ant-select-disabled)')].filter(visible).slice(0, 4)
        .map((e, i) => [`desplegable ${i + 1}`, () => e.querySelector('.ant-select-selector').dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))]),
      ...[...main.querySelectorAll('.ant-picker:not(.ant-picker-disabled)')].filter(visible).slice(0, 2)
        .map((e, i) => [`calendario ${i + 1}`, () => { const inp = e.querySelector('input'); inp.dispatchEvent(new MouseEvent('mousedown', { bubbles: true })); inp.click(); inp.focus(); }]),
    ];
    const fuera = [];
    for (const [nombre, abrir] of disparadores) {
      await cerrar();
      abrir();
      await esperar(450);
      const p = abierto();
      if (!p) continue; // algunos selectores solo buscan al escribir
      const r = p.getBoundingClientRect();
      if (r.left < -2 || r.top < -2 || r.right > innerWidth + 2 || r.top > innerHeight) {
        fuera.push(`${nombre} en (${Math.round(r.left)}, ${Math.round(r.top)})`);
      }
    }
    await cerrar();
    return fuera;
  });
}

for (const [rol, email] of ROLES) {
  test(`${rol}: todo su menú funciona y despliega dentro de la pantalla`, async ({ browser }) => {
    const contexto = await browser.newContext();
    const page = await contexto.newPage();
    const problemas = [];
    let ruta = '';
    page.on('pageerror', (e) => problemas.push(`${ruta} · JS: ${e.message}`));
    page.on('response', (r) => {
      if (!r.url().includes(':8000/')) return;
      if (r.status() >= 500 || r.status() === 403) problemas.push(`${ruta} · HTTP ${r.status()} ${r.request().method()} ${r.url().replace(/^.*:8000/, '')}`);
    });
    await entrar(page, email);
    const rutas = await rutasDelMenu(page);
    expect(rutas.length, `${rol}: menú vacío`).toBeGreaterThan(2);

    for (ruta of rutas) {
      const inicio = Date.now();
      await page.goto(ruta);
      // Las pantallas con refresco periódico nunca quedan sin red: se espera poco.
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(600);
      const texto = await page.locator('.ant-layout-content').first().innerText().catch(() => '');
      const aviso = texto.split('\n').find((l) => AVISOS.test(l) && l.length < 120);
      if (aviso) problemas.push(`${ruta} · la pantalla dice «${aviso.trim()}»`);
      const [ancho, visibleAncho] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
      if (ancho > visibleAncho + 1) problemas.push(`${ruta} · desborda ${ancho - visibleAncho}px hacia los lados`);
      for (const f of await desplegablesFuera(page)) problemas.push(`${ruta} · ${f} fuera de la pantalla`);
      console.log(`${rol} ${ruta} ${Date.now() - inicio} ms`);
    }

    // Menú del perfil
    ruta = 'perfil (cabecera)';
    await page.goto('/dashboard/home');
    await page.locator('.ant-layout-header .ant-avatar').first().click();
    const menuPerfil = page.locator('.ant-dropdown:not(.ant-dropdown-hidden)').last();
    await expect(menuPerfil, `${rol}: el menú del perfil no abre`).toBeVisible();
    const caja = await menuPerfil.boundingBox();
    expect(caja.x + caja.width, `${rol}: menú del perfil fuera de la pantalla`).toBeLessThanOrEqual(1442);
    await page.keyboard.press('Escape');

    // Campana: abre y la primera notificación lleva a una pantalla que existe
    ruta = 'notificaciones (campana)';
    await page.locator('[aria-label^="Notificaciones"]').first().click();
    const panel = page.locator('.ant-dropdown:not(.ant-dropdown-hidden), .ant-popover:not(.ant-popover-hidden)').last();
    await expect(panel, `${rol}: la campana no abre`).toBeVisible();
    const pcaja = await panel.boundingBox();
    expect(pcaja.x >= -2 && pcaja.x + pcaja.width <= 1442, `${rol}: panel de notificaciones fuera de la pantalla`).toBe(true);
    const primera = panel.locator('.ant-list-item, [role="listitem"], li').first();
    if (await primera.count()) {
      const antes = page.url();
      await primera.click();
      await page.waitForTimeout(1500);
      const destino = page.url();
      // Con timeout: la página de «sin permiso» no tiene .ant-layout-content y la
      // espera sin límite colgaba la prueba hasta los 5 min.
      const textoDestino = await page.locator('.ant-layout-content').first().innerText({ timeout: 5000 }).catch(() => '');
      const pagina = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
      if (destino === antes) problemas.push(`${ruta} · la notificación no llevó a ningún lado`);
      if (/página no encontrada|404/i.test(textoDestino)) problemas.push(`${ruta} · llevó a ${destino}, que no existe`);
      if (/\/403|unauthorized/.test(destino) || /Acceso Restringido/.test(pagina)) {
        problemas.push(`${ruta} · llevó a ${destino}, que este rol no puede ver`);
      }
    }

    await contexto.close();
    expect(problemas, `${rol}: ${rutas.length} pantallas del menú`).toEqual([]);
  });
}
