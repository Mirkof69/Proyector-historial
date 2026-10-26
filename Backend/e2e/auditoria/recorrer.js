// Auditoría de pantallas: entra con cada rol a cada pantalla del menú y anota lo
// que una persona notaría y las pruebas no: tablas vacías, contadores en cero,
// textos rotos («NaN», «undefined», «Invalid Date»), llamadas a la API fallidas
// y errores de JavaScript. Deja auditoria/salida/informe.json y una captura por pantalla.
//
//   node auditoria/recorrer.js            (cwd = Backend/e2e, sistema en marcha)
//   ROLES=admin node auditoria/recorrer.js
const fs = require('fs');
const path = require('path');
const { chromium } = require('@playwright/test');

const BASE = process.env.E2E_BASE_URL || 'http://localhost:3000';
const CLAVE = process.env.E2E_PASSWORD;
const SALIDA = path.join(__dirname, 'salida');
const CUENTAS = {
  admin: 'admin.demo@fetalmedical.bo', medico: 'dra.garcia@fetalmedical.bo', enfermera: 'enf.mamani@fetalmedical.bo',
};
const ROLES = (process.env.ROLES || 'admin,medico,enfermera').split(',');
const TEXTO_ROTO = /\b(NaN|undefined|null|Invalid Date|\[object Object\])\b/;

async function rutasDelMenu(page) {
  // Abre los submenús y junta las rutas que el propio menú ofrece a ese rol.
  for (const sub of await page.locator('.ant-menu-submenu-title').all()) await sub.click().catch(() => {});
  await page.waitForTimeout(400);
  return page.evaluate(() => [...new Set([...document.querySelectorAll('.ant-layout-sider [data-menu-id]')]
    .map((e) => (e.getAttribute('data-menu-id') || '').replace(/^.*?(\/dashboard)/, '$1'))
    .filter((r) => r.startsWith('/dashboard')))]);
}

async function revisar(page, ruta) {
  const red = [];
  const errores = [];
  const alResponder = (r) => {
    if (r.url().includes('/api/') && r.status() >= 400 && r.status() !== 401) red.push(`${r.status()} ${r.request().method()} ${r.url().split('/api')[1]}`);
  };
  const alFallar = (e) => errores.push(e.message);
  page.on('response', alResponder);
  page.on('pageerror', alFallar);
  await page.goto(BASE + ruta);
  await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(1500);
  const datos = await page.evaluate((patron) => {
    const visible = (e) => !!(e.offsetParent || e.getClientRects().length);
    const contenido = document.querySelector('.ant-layout-content') || document.body;
    const texto = contenido.innerText;
    const roto = [...new Set((texto.match(new RegExp(patron, 'g')) || []))];
    const tablas = [...contenido.querySelectorAll('.ant-table')].filter(visible).map((t) => t.querySelectorAll('tbody tr.ant-table-row').length);
    const vacios = [...contenido.querySelectorAll('.ant-empty')].filter(visible).length;
    const ceros = [...contenido.querySelectorAll('.ant-statistic')].filter(visible).map((s) => ({
      titulo: (s.querySelector('.ant-statistic-title')?.innerText || '').trim(),
      valor: (s.querySelector('.ant-statistic-content')?.innerText || '').trim(),
    })).filter((s) => /^(0|0\s*\/\s*0|0[.,]0+%?|0\s*%|-|—)$/.test(s.valor.replace(/\s+/g, ' ')));
    return { roto, tablas, vacios, ceros, titulo: (contenido.querySelector('h1,h2,h3,h4')?.innerText || '').trim().slice(0, 60) };
  }, TEXTO_ROTO.source);
  page.off('response', alResponder);
  page.off('pageerror', alFallar);
  return { ruta, ...datos, red, errores };
}

(async () => {
  if (!CLAVE) throw new Error('Falta E2E_PASSWORD');
  fs.mkdirSync(SALIDA, { recursive: true });
  const navegador = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const informe = {};
  for (const rol of ROLES) {
    const contexto = await navegador.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'light' });
    const page = await contexto.newPage();
    await page.goto(`${BASE}/login`);
    await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', CUENTAS[rol]);
    await page.fill('input[placeholder="Ingrese su contraseña"]', CLAVE);
    await page.click('button[type=submit]');
    await page.waitForURL((u) => !u.pathname.includes('login'));
    await page.waitForTimeout(2000);
    const rutas = await rutasDelMenu(page);
    informe[rol] = [];
    for (const ruta of rutas) {
      const r = await revisar(page, ruta);
      await page.screenshot({ path: path.join(SALIDA, `${rol}_${ruta.replace(/\W+/g, '_')}.png`) });
      informe[rol].push(r);
      const avisos = [
        r.errores.length && `JS ${r.errores.length}`, r.red.length && `API ${r.red.join(', ')}`,
        r.roto.length && `texto roto ${r.roto.join(',')}`, r.tablas.some((n) => n === 0) && 'tabla vacía',
        r.vacios && `${r.vacios} vacíos`, r.ceros.length && `ceros: ${r.ceros.map((c) => c.titulo).join(' | ')}`,
      ].filter(Boolean);
      console.log(`${rol.padEnd(9)} ${ruta.padEnd(42)} ${avisos.join(' · ') || 'ok'}`);
    }
    await contexto.close();
  }
  fs.writeFileSync(path.join(SALIDA, 'informe.json'), JSON.stringify(informe, null, 2));
  await navegador.close();
})();
