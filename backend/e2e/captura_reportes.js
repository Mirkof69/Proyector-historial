// Verificación (no es un test): cada pestaña del centro de reportes carga sin errores.
const { chromium } = require('@playwright/test');

(async () => {
  const navegador = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || undefined });
  const pagina = await navegador.newPage({ viewport: { width: 1400, height: 1000 } });
  const errores = [];
  pagina.on('pageerror', (e) => errores.push(e.message));
  pagina.on('response', (r) => { if (r.status() >= 500) errores.push(`${r.status()} ${r.url()}`); });
  await pagina.goto('http://localhost:3000/login');
  await pagina.fill('input[placeholder="ejemplo@fetalmedical.com"]', process.env.E2E_EMAIL || 'admin.demo@fetalmedical.bo');
  await pagina.fill('input[placeholder="Ingrese su contraseña"]', 'Demo2026!');
  await pagina.click('button[type="submit"]');
  await pagina.waitForURL((u) => !u.pathname.includes('login'));
  await pagina.goto('http://localhost:3000/dashboard/reportes/kpis');   // ruta vieja: debe redirigir
  await pagina.waitForTimeout(1500);
  console.log('ruta vieja →', new URL(pagina.url()).pathname + new URL(pagina.url()).search);
  for (const nombre of await pagina.getByRole('tab').allInnerTexts()) {
    await pagina.getByRole('tab', { name: nombre }).click();
    await pagina.waitForTimeout(2500);
    console.log('pestaña', JSON.stringify(nombre), '→', new URL(pagina.url()).search, '| errores acumulados:', errores.length);
  }
  await pagina.getByRole('tab', { name: 'Estadísticas por fecha' }).click();
  await pagina.waitForTimeout(2500);
  await pagina.screenshot({ path: process.argv[2] || 'reportes.png' });
  console.log('errores:', errores.length ? errores : 'ninguno');
  await navegador.close();
})();
