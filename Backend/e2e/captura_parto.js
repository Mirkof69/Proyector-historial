// Captura de verificación (no es un test): detalle de un parto gemelar en pestañas.
const { chromium } = require('@playwright/test');

(async () => {
  const navegador = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || undefined });
  const pagina = await navegador.newPage({ viewport: { width: 1400, height: 1000 } });
  const errores = [];
  pagina.on('pageerror', (e) => errores.push(e.message));
  await pagina.goto('http://localhost:3000/login');
  await pagina.fill('input[placeholder="ejemplo@fetalmedical.com"]', 'dra.garcia@fetalmedical.bo');
  await pagina.fill('input[placeholder="Ingrese su contraseña"]', 'Demo2026!');
  await pagina.click('button[type="submit"]');
  await pagina.waitForURL((u) => !u.pathname.includes('login'));
  await pagina.goto(`http://localhost:3000/dashboard/partos/${process.argv[2] || 20}`);
  await pagina.getByRole('tab', { name: /Recién nacido/ }).click();
  await pagina.waitForTimeout(800);
  await pagina.screenshot({ path: process.argv[3] || 'parto.png', fullPage: false });
  console.log('errores JS:', errores.length ? errores : 'ninguno');
  console.log('pestañas:', await pagina.getByRole('tab').allInnerTexts());
  await navegador.close();
})();
