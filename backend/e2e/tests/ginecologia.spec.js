// Ecografía ginecológica con IA, usada como lo haría la médica: elegir el tipo
// de análisis, subir la imagen y leer el resultado con sus límites.
// Usa imágenes reales de prueba de MMOTU y de miomas extraídas localmente (no
// se versionan): si no están, los pasos se saltan con su motivo.
// Necesita backend (8000), frontend (3000) y microservicio de IA (8001).
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const EMAIL = process.env.E2E_EMAIL || 'dra.garcia@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const IA = path.join(__dirname, '..', '..', '..', 'redes-neuronales');

/** Campos de una línea CSV, respetando los que van entre comillas (las cajas del mioma llevan comas). */
const campos = (linea) => (linea.match(/("([^"]|"")*"|[^,]*)(,|$)/g) || [])
  .map((c) => c.replace(/,$/, '').replace(/^"|"$/g, '').replace(/""/g, '"'));

/** Primera imagen de PRUEBA del catálogo con esa clase (pacientes que la red no vio). */
const imagenDePrueba = (catalogo, columnaClase, clase) => {
  const ruta = path.join(IA, 'entrenamiento', 'ginecologia', 'catalogos', catalogo);
  if (!fs.existsSync(ruta)) return null;
  const [cabecera, ...filas] = fs.readFileSync(ruta, 'utf8').trim().split(/\r?\n/);
  const col = campos(cabecera);
  const fila = filas.map(campos).find((f) => f[col.indexOf('particion')] === 'prueba'
    && (!clase || f[col.indexOf(columnaClase)] === clase));
  const archivo = fila && path.join(IA, fila[col.indexOf('imagen')]);
  return archivo && fs.existsSync(archivo) ? archivo : null;
};

const TERATOMA = imagenDePrueba('ovario.csv', 'clase_nombre', 'teratoma');
const MIOMA = imagenDePrueba('mioma.csv', null, null);

test.describe.configure({ mode: 'serial' });

test.describe('Ecografía ginecológica con IA', () => {
  let page;
  const erroresJs = [];

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    page.on('pageerror', (e) => erroresJs.push(e.message));
    await page.goto('/login');
    await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', EMAIL);
    await page.fill('input[placeholder="Ingrese su contraseña"]', PASSWORD);
    await page.click('button[type=submit]');
    await page.waitForURL((u) => !u.pathname.includes('login'));
  });

  test.afterAll(async () => {
    await page.close();
    expect(erroresJs, 'errores de JavaScript en la página').toEqual([]);
  });

  test('1. masa ovárica: dibuja la lesión, da el tipo probable y la alarma de malignidad', async () => {
    test.skip(!TERATOMA, 'no está la imagen de prueba de MMOTU extraída localmente');
    await page.goto('/dashboard/ia-medica/imagenes?pestana=ginecologia');
    await page.getByRole('radio', { name: 'Masa ovárica' }).check();
    await page.locator('input[type=file]').setInputFiles(TERATOMA);
    await page.getByRole('button', { name: 'Analizar', exact: true }).click();
    await expect(page.getByText('Tipo probable')).toBeVisible({ timeout: 60_000 });
    // El recuadro de malignidad muestra la probabilidad y cuántos carcinomas detectó la red en la prueba
    const malignidad = page.locator('.ant-alert').filter({ hasText: 'alarma desde' });
    await expect(malignidad).toContainText(/alarma de malignidad|Alarma: rasgos compatibles/i);
    await expect(malignidad).toContainText(/de los carcinomas/);
    await expect(page.getByAltText('Ecografía con la lesión dibujada')).toBeVisible();
    await expect(page.getByText(/O-RADS/).first()).toBeVisible();
  });

  test('2. mioma: lo ubica y avisa que no sirve para descartarlo', async () => {
    test.skip(!MIOMA, 'no está la imagen de prueba de miomas extraída localmente');
    await page.getByRole('radio', { name: 'Mioma uterino' }).check();
    await page.locator('input[type=file]').setInputFiles(MIOMA);
    await page.getByRole('button', { name: 'Analizar', exact: true }).click();
    await expect(page.getByText(/no sirve para descartar/)).toBeVisible({ timeout: 60_000 });
    await expect(page.getByText('Ancho del mioma (px)')).toBeVisible();
  });
});
