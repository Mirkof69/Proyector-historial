// Verificación (no es un test): cada listado carga, pagina en el servidor y
// no tiene errores de JavaScript ni respuestas 500.
const { chromium } = require('@playwright/test');

const PANTALLAS = [
  '/dashboard/pacientes', '/dashboard/embarazos', '/dashboard/controles', '/dashboard/ecografias',
  '/dashboard/partos', '/dashboard/laboratorio', '/dashboard/citas', '/dashboard/vacunas',
  '/dashboard/triaje', '/dashboard/notas-evolucion', '/dashboard/calculadoras', '/dashboard/panel-calculadoras',
  '/dashboard/reportes', '/dashboard',
];

(async () => {
  const navegador = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || undefined });
  const pagina = await navegador.newPage({ viewport: { width: 1400, height: 900 } });
  let errores = [];
  let peticiones = [];
  pagina.on('pageerror', (e) => errores.push(`JS: ${e.message}`));
  pagina.on('response', (r) => {
    if (r.url().includes('/api/')) peticiones.push(r.url());
    if (r.status() >= 500) errores.push(`${r.status()} ${r.url()}`);
  });
  await pagina.goto('http://localhost:3000/login');
  await pagina.fill('input[placeholder="ejemplo@fetalmedical.com"]', process.env.E2E_EMAIL || 'admin.demo@fetalmedical.bo');
  await pagina.fill('input[placeholder="Ingrese su contraseña"]', 'Demo2026!');
  await pagina.click('button[type="submit"]');
  await pagina.waitForURL((u) => !u.pathname.includes('login'));
  let fallos = 0;
  for (const ruta of PANTALLAS) {
    errores = []; peticiones = [];
    const inicio = Date.now();
    await pagina.goto(`http://localhost:3000${ruta}`);
    await pagina.waitForLoadState('networkidle').catch(() => {});
    await pagina.waitForTimeout(800);
    const filas = await pagina.locator('.ant-table-tbody tr.ant-table-row').count();
    const total = await pagina.locator('.ant-pagination-total-text').first().innerText().catch(() => '');
    const masivas = peticiones.filter((u) => /page=\d+.*limit=200|limit=200.*page=/.test(u)).length;
    if (errores.length || masivas > 1) fallos += 1;
    console.log(`${ruta.padEnd(30)} ${String(Date.now() - inicio).padStart(5)} ms  peticiones API ${String(peticiones.length).padStart(3)}  filas ${String(filas).padStart(3)}  ${total}  ${errores.length ? 'ERRORES: ' + errores.join(' | ') : 'ok'}`);
  }
  console.log(fallos ? `${fallos} pantallas con problemas` : 'todas las pantallas sin errores');
  await navegador.close();
})();
