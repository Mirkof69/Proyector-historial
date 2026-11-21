// Verificación en el navegador (no es un test): recorre las pantallas nuevas
// del 01/10/2026 y anota errores de JavaScript y llamadas a la API que fallan.
//   node captura_nuevas_pantallas.js <id_parto> <carpeta_capturas>
const { chromium } = require('@playwright/test');
const path = require('path');

(async () => {
  const carpeta = process.argv[3] || '.';
  const navegador = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || undefined });
  const pagina = await navegador.newPage({ viewport: { width: 1400, height: 1000 } });
  const errores = [];
  const fallos = [];
  pagina.on('pageerror', (e) => errores.push(e.message));
  pagina.on('response', (r) => {
    if (r.url().includes('/api/') && r.status() >= 400) fallos.push(`${r.status()} ${r.url().replace(/^.*\/api/, '/api')}`);
  });
  const foto = (nombre) => pagina.screenshot({ path: path.join(carpeta, `${nombre}.png`) });

  await pagina.goto('http://localhost:3000/login');
  await pagina.fill('input[placeholder="ejemplo@fetalmedical.com"]', 'dra.garcia@fetalmedical.bo');
  await pagina.fill('input[placeholder="Ingrese su contraseña"]', 'Demo2026!');
  await pagina.click('button[type="submit"]');
  await pagina.waitForURL((u) => !u.pathname.includes('login'));

  // 1. Parto en 5 pestañas
  await pagina.goto(`http://localhost:3000/dashboard/partos/${process.argv[2] || 20}`);
  await pagina.getByRole('tab', { name: 'Admisión' }).waitFor();
  console.log('pestañas del parto:', await pagina.getByRole('tab').allInnerTexts());
  await foto('01_parto_admision');
  await pagina.getByRole('tab', { name: 'Trabajo de parto' }).click();
  await pagina.getByText('Partograma', { exact: true }).waitFor();
  await foto('02_parto_trabajo');
  await pagina.getByRole('tab', { name: /Recién nacido/ }).click();
  await pagina.waitForTimeout(500);
  await foto('03_parto_rn');
  await pagina.getByRole('tab', { name: /Alumbramiento/ }).click();
  await pagina.waitForTimeout(500);
  await foto('04_parto_alumbramiento');
  await pagina.getByRole('tab', { name: 'Epicrisis' }).click();
  await pagina.waitForTimeout(1200);
  await foto('05_parto_epicrisis');
  console.log('epicrisis:', (await pagina.locator('.ant-tabs-tabpane-active').innerText()).slice(0, 120).replace(/\n/g, ' | '));

  // 2. IA: cardiotocografía y modelos
  await pagina.goto('http://localhost:3000/dashboard/ia-medica/imagenes?pestana=cardiotocografia');
  await pagina.getByText('Fiabilidad medida del modelo').waitFor({ timeout: 30000 });
  await foto('06_ia_ctg');
  await pagina.goto('http://localhost:3000/dashboard/ia-medica/imagenes?pestana=modelos');
  await pagina.waitForTimeout(2500);
  await foto('07_ia_modelos');
  console.log('modelos:', await pagina.locator('.ant-table-row').count());

  // 3. Reportes: natalidad e IA
  await pagina.goto('http://localhost:3000/dashboard/reportes?pestana=natalidad');
  await pagina.getByText('Partos por mes, según la vía').waitFor({ timeout: 30000 }).catch(() => {});
  await pagina.waitForTimeout(1500);
  await foto('08_reporte_natalidad');
  await pagina.getByText('Este año').click();
  await pagina.waitForTimeout(2000);
  await foto('09_reporte_natalidad_anio');
  await pagina.goto('http://localhost:3000/dashboard/reportes?pestana=ia');
  await pagina.waitForTimeout(3000);
  await foto('10_reporte_ia');

  // 4. Laboratorio: importación
  await pagina.goto('http://localhost:3000/dashboard/laboratorio');
  await pagina.getByRole('button', { name: /Importar Excel/ }).first().click();
  await pagina.getByText('Importaciones anteriores').waitFor();
  await foto('11_lab_importar');

  console.log('errores JS:', errores.length ? errores : 'ninguno');
  console.log('API con error:', fallos.length ? [...new Set(fallos)] : 'ninguna');
  await navegador.close();
})();
