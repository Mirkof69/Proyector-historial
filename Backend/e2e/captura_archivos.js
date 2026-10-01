// Verificación (no es un test): subir, ver y borrar un adjunto de una ecografía.
const path = require('path');
const { chromium } = require('@playwright/test');

(async () => {
  const navegador = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || undefined });
  const pagina = await navegador.newPage({ viewport: { width: 1300, height: 900 } });
  const errores = [];
  pagina.on('pageerror', (e) => errores.push(e.message));
  pagina.on('response', (r) => { if (r.status() >= 500) errores.push(`${r.status()} ${r.url()}`); });
  await pagina.goto('http://localhost:3000/login');
  await pagina.fill('input[placeholder="ejemplo@fetalmedical.com"]', 'admin.demo@fetalmedical.bo');
  await pagina.fill('input[placeholder="Ingrese su contraseña"]', 'Demo2026!');
  await pagina.click('button[type="submit"]');
  await pagina.waitForURL((u) => !u.pathname.includes('login'));
  const id = process.argv[2];
  await pagina.goto(`http://localhost:3000/dashboard/ecografias/${id}`);
  await pagina.getByRole('button', { name: /Archivos adjuntos/ }).click();
  await pagina.waitForURL(/\/archivos$/);
  await pagina.setInputFiles('input[type="file"]', path.join(__dirname, 'datos', 'eco_cabeza.png'));
  await pagina.getByPlaceholder('Descripción (opcional)').fill('Prueba de adjunto');
  await pagina.getByRole('button', { name: 'Subir' }).click();
  try {
    await pagina.locator('.ant-table-tbody').getByText('eco_cabeza.png').first().waitFor({ timeout: 15000 });
  } catch (e) {
    await pagina.screenshot({ path: process.argv[3] || 'archivos.png' });
    console.log('no apareció; avisos en pantalla:', await pagina.locator('.ant-message, .ant-form-item-explain-error, .ant-alert').allInnerTexts());
    console.log('errores:', errores);
    await navegador.close();
    return;
  }
  console.log('subido y listado:', await pagina.locator('.ant-table-tbody tr.ant-table-row').count(), 'fila(s)');
  await pagina.getByRole('button', { name: 'Ver imagen' }).first().click();
  await pagina.waitForTimeout(1500);
  const ancho = await pagina.locator('.ant-modal img').first().evaluate((img) => img.naturalWidth);
  console.log('vista previa cargada (ancho px):', ancho);
  await pagina.screenshot({ path: process.argv[3] || 'archivos.png' });
  await pagina.keyboard.press('Escape');
  await pagina.getByRole('button', { name: 'Eliminar' }).first().click();
  await pagina.getByRole('button', { name: 'Eliminar', exact: true }).last().click();
  await pagina.waitForTimeout(1500);
  console.log('tras borrar:', await pagina.locator('.ant-table-tbody tr.ant-table-row').count(), 'fila(s)');
  console.log('errores:', errores.length ? errores : 'ninguno');
  await navegador.close();
})();
