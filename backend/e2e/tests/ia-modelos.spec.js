// Cada modelo de IA EN SERVICIO, usado desde la pantalla donde lo usa la médica,
// con imágenes y registros REALES de los conjuntos de prueba (pacientes que la
// red no vio). Empieza por la Guía de IA y sigue sus botones «Usar ahora».
//
// Imágenes: redes-neuronales/datos/extraidos/** y los catálogos de
// prueba de entrenamiento/**. No se versionan: si faltan, el paso se salta con
// su motivo. Necesita backend (8000), frontend (3000) y microservicio de IA (8001).
//
// Registra, por cada llamada, el código HTTP y la latencia vistos desde el
// navegador (se imprimen al final como tabla).
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const EMAIL = process.env.E2E_EMAIL || 'dra.garcia@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const API = process.env.E2E_API || 'http://localhost:8000/api';
const IA = path.join(__dirname, '..', '..', '..', 'redes-neuronales');
const ENT = path.join(IA, 'entrenamiento');

/** Filas de un CSV simple (sin comas dentro de los campos). */
const csv = (ruta) => {
  if (!fs.existsSync(ruta)) return [];
  const [cab, ...filas] = fs.readFileSync(ruta, 'utf8').trim().split(/\r?\n/);
  const col = cab.split(',');
  return filas.map((f) => Object.fromEntries(f.split(',').map((v, i) => [col[i], v])));
};
const existe = (p) => (p && fs.existsSync(p) ? p : null);

// Cabeza del segundo trimestre de HC18 (otro hospital), partición de prueba.
// Tamaño de píxel de la hoja «HC18» de entrenamiento/redes_ecografia_real/catalogo_imagenes.xlsx.
const CABEZA = { archivo: existe(path.join(ENT, 'redes_ecografia_real', 'imagenes', 'hc18', '147_HC.png')), px: '0.074836' };
const TORAX = existe((() => {
  const f = csv(path.join(ENT, 'segmentacion', 'catalogos', 'torax.csv')).find((r) => r.particion === 'prueba');
  return f && path.join(IA, f.imagen);
})());
const MULTI = path.join(IA, 'datos', 'extraidos', 'obstetricia', 'FetalBiometry-Multicentre-Landmarks-2026', 'images', 'MULTICENTRE');
const conPx = (tarea, carpeta) => {
  const f = csv(path.join(ENT, 'biometria', 'salidas', tarea, 'prueba_medidas.csv'))[0];
  return f ? { archivo: existe(path.join(MULTI, carpeta, f.imagen)), px: Number(f.mm_por_px).toFixed(4) } : { archivo: null };
};
const FEMUR = conPx('femur', 'Femur');
const ABDOMEN = conPx('abdomen', 'Abdomen');
const ANOMALIA = (() => {
  const dir = path.join(IA, 'datos', 'extraidos', 'fetal_brain_abnormalities', 'test');
  if (!fs.existsSync(dir)) return null;
  const f = fs.readdirSync(dir).find((n) => n.includes('ventriculomegaly') && n.endsWith('.jpg'));
  return f ? path.join(dir, f) : null;
})();
const INTRAPARTO = existe((() => {
  const f = csv(path.join(ENT, 'segmentacion', 'salidas', 'intraparto', 'prueba_medidas.csv'))[0];
  return f && path.join(IA, f.imagen);
})());
const PCO = existe((() => {
  const f = csv(path.join(ENT, 'ginecologia', 'catalogos', 'ovario_pco.csv')).find((r) => r.clase_nombre === 'poliquistico');
  return f && path.join(IA, f.ruta);
})());
// Primer registro patológico (consenso de 3 obstetras) de la tabla SisPorto.
const CTG = csv(path.join(__dirname, '..', '..', 'ia_medica', 'ml', 'datos', 'fetal_health.csv')).find((r) => r.fetal_health === '3.0');

const llamadas = [];

test.describe.configure({ mode: 'serial' });

test.describe('Modelos de IA desde sus pantallas', () => {
  let page;
  const erroresJs = [];

  /** Espera la respuesta de `ruta`, la anota (HTTP y ms) y la devuelve. */
  const medir = async (nombre, ruta, accion) => {
    const t0 = Date.now();
    const [r] = await Promise.all([
      page.waitForResponse((resp) => resp.url().includes(ruta) && resp.request().method() !== 'OPTIONS', { timeout: 90_000 }),
      accion(),
    ]);
    llamadas.push({ modelo: nombre, ruta, http: r.status(), ms: Date.now() - t0 });
    return r;
  };

  const apiGet = (ruta) => page.evaluate(async ([api, r]) => (await fetch(api + r, { credentials: 'include' })).json(), [API, ruta]);
  const subir = (selector, archivo) => page.locator(selector).first().setInputFiles(archivo);

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
    // eslint-disable-next-line no-console
    console.log(`\n| Modelo | Llamada | HTTP | ms |\n|---|---|---|---|\n${
      llamadas.map((l) => `| ${l.modelo} | ${l.ruta} | ${l.http} | ${l.ms} |`).join('\n')}\n`);
    await page.close();
    expect(erroresJs, 'errores de JavaScript en la página').toEqual([]);
  });

  test('1. la Guía de IA está en el menú y lista cada modelo con su cifra medida', async () => {
    await page.goto('/dashboard/home');
    await page.getByRole('menuitem', { name: /Guía de IA/ }).click();
    await expect(page).toHaveURL(/\/dashboard\/ia-guia/);
    await expect(page.getByRole('heading', { name: 'Cómo funcionan' })).toBeVisible();
    await expect(page.getByText('Por qué no se usa aprendizaje no supervisado para decidir')).toBeVisible();
    // 15 modelos en servicio, cada uno con su botón; las cifras llegan del backend.
    await expect(page.getByRole('button', { name: /^Usar ahora:/ })).toHaveCount(15, { timeout: 30_000 });
    await expect(page.locator('body')).toContainText('Exactitud 92,7 %');
    await expect(page.locator('body')).toContainText('detecta 7 de 13');
    // Los descartados con su motivo, sin botón para usarlos.
    const descartados = page.locator('section').filter({ has: page.getByRole('heading', { name: 'Evaluados y descartados' }) });
    await expect(descartados).toContainText('68,6 % en otra sede');
    await expect(descartados).toContainText('Acidemia al nacer');
    await expect(descartados.getByRole('button', { name: /Usar ahora/ })).toHaveCount(0);
  });

  test('2. «Usar ahora» del plano lleva a la pestaña Ecografía; plano, cribado cerebral y CC', async () => {
    test.skip(!CABEZA.archivo, 'no está la imagen de HC18 extraída localmente');
    await page.goto('/dashboard/ia-guia');
    await page.getByRole('button', { name: 'Usar ahora: Plano anatómico (EfficientNet-B0)' }).click();
    await expect(page).toHaveURL(/pestana=ecografia/);
    await subir('input[type=file]', CABEZA.archivo);
    await page.fill('#tamano-pixel', CABEZA.px);
    await medir('Plano anatómico + anomalías + CC (regresión)', '/ecografias/plano-anatomico/',
      () => page.getByRole('button', { name: /^(scan )?Analizar$/ }).click());
    await expect(page.getByText('La imagen muestra')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('body')).toContainText('cerebro fetal');
    await expect(page.getByText('Cribado de anomalías cerebrales')).toBeVisible();
    await expect(page.getByText('Sin alarma', { exact: true })).toBeVisible();
    await expect(page.getByText('Edad gestacional', { exact: true })).toBeVisible();
  });

  /** El análisis de la tarjeta de redes: devuelve la vista del resultado. */
  const informeCompleto = async (nombre, archivo, px) => {
    await subir('input[type=file]', archivo);
    await page.fill('#tamano-pixel', px || '');
    await medir(nombre, '/ecografias/analyze-with-ai/',
      () => page.getByRole('button', { name: /^(scan )?Analizar$/ }).click());
    const resultado = page.locator('.ia-informe').first();
    await expect(resultado).toBeVisible({ timeout: 60_000 });
    return resultado;
  };
  const cerrar = async () => {};

  test('3. U-Net de cabeza: CC y DBP en mm con su margen, y la imagen con lo que dibujó', async () => {
    test.skip(!CABEZA.archivo, 'no está la imagen de HC18');
    const modal = await informeCompleto('U-Net de cabeza (CC, DBP)', CABEZA.archivo, CABEZA.px);
    await expect(modal).toContainText('Circunferencia cefálica');
    await expect(modal).toContainText(/\d+(\.\d)? mm ± 4\.41/);
    await expect(modal).toContainText('segmentacion_cabeza');
    await expect(modal.getByAltText('Estructuras segmentadas')).toBeVisible();
    await cerrar(modal);
  });

  test('4. U-Net de tórax: índice cardiotorácico', async () => {
    test.skip(!TORAX, 'no está la imagen de FOCUS');
    const modal = await informeCompleto('U-Net de tórax (ICT)', TORAX);
    await expect(modal).toContainText('Índice cardiotorácico (áreas)');
    await expect(modal).toContainText('segmentacion_torax');
    await cerrar(modal);
  });

  test('5. U-Net abdominal + puntos: corte adecuado y circunferencia abdominal', async () => {
    test.skip(!ABDOMEN.archivo, 'no está la imagen de biometría multicéntrica');
    const modal = await informeCompleto('U-Net abdomen + puntos CA', ABDOMEN.archivo, ABDOMEN.px);
    await expect(modal).toContainText('Corte adecuado para medir la CA');
    await expect(modal).toContainText('Circunferencia abdominal');
    await expect(modal).toContainText('biometria_abdomen');
    await cerrar(modal);
  });

  test('6. red de puntos del fémur: longitud femoral', async () => {
    test.skip(!FEMUR.archivo, 'no está la imagen de biometría multicéntrica');
    const modal = await informeCompleto('Puntos: longitud del fémur', FEMUR.archivo, FEMUR.px);
    await expect(modal).toContainText('Longitud del fémur');
    await expect(modal).toContainText(/mm ± 1\.29/);
    await cerrar(modal);
  });

  test('7. cribado de anomalías cerebrales con una ventriculomegalia real', async () => {
    test.skip(!ANOMALIA, 'no está la imagen de Fetal Brain Abnormalities');
    await subir('input[type=file]', ANOMALIA);
    await page.fill('#tamano-pixel', '');
    await medir('Cribado de anomalías cerebrales', '/ecografias/anomalias-cerebrales/',
      () => page.getByRole('button', { name: /^(scan )?Analizar$/ }).click());
    const tarjeta = page.locator('.ant-card').filter({ hasText: 'Cribado de anomalías cerebrales' }).last();
    await expect(tarjeta).toContainText('P(anomalía)', { timeout: 60_000 });
    await expect(tarjeta).toContainText(/sensibilidad en ecografías clínicas no se puede medir/);
  });

  test('8. ginecología: ovario poliquístico (la masa ovárica y el mioma los cubre ginecologia.spec.js)', async () => {
    test.skip(!PCO, 'no está la imagen de ovario poliquístico');
    await page.goto('/dashboard/ia-guia');
    await page.getByRole('button', { name: 'Usar ahora: Ovario poliquístico (EfficientNet-B0)' }).click();
    await expect(page).toHaveURL(/pestana=ginecologia/);
    await page.getByRole('radio', { name: 'Ovario poliquístico' }).check();
    await page.locator('input[type=file]').setInputFiles(PCO);
    await medir('Ovario poliquístico', '/ia/ginecologia/ovario-pco/',
      () => page.getByRole('button', { name: 'Analizar', exact: true }).click());
    await expect(page.getByText('Categoría probable')).toBeVisible({ timeout: 60_000 });
    await expect(page.locator('body')).toContainText('clasificador_ovario_pco');
  });

  test('9. cardiotocografía: un registro patológico real se clasifica como patológico', async () => {
    test.skip(!CTG, 'no está la tabla fetal_health.csv');
    await page.goto('/dashboard/ia-guia');
    await page.getByRole('button', { name: 'Usar ahora: Cardiotocografía (Gradient Boosting)' }).click();
    await expect(page).toHaveURL(/pestana=cardiotocografia/);
    const { variables } = await apiGet('/ia/cardiotocografia/');
    const columnas = Object.keys(CTG).filter((c) => c !== 'fetal_health');
    expect(variables).toHaveLength(columnas.length);
    for (let i = 0; i < variables.length; i += 1) {
      // eslint-disable-next-line no-await-in-loop
      await page.fill(`#${variables[i].clave}`, String(Number(CTG[columnas[i]])));
    }
    await medir('Cardiotocografía (gradient boosting)', '/ia/cardiotocografia/',
      () => page.getByRole('button', { name: 'Clasificar' }).click());
    await expect(page.locator('.ia-ctg-clase')).toHaveText('Patológica', { timeout: 30_000 });
    await expect(page.getByText('Fiabilidad medida del modelo')).toBeVisible();
  });

  test('10. ángulo de progresión desde el partograma (sin guardar el tacto)', async () => {
    test.skip(!INTRAPARTO, 'no está la imagen intraparto de IUGC');
    const partos = await apiGet('/partos/?page_size=1');
    const parto = (partos.results || partos)[0];
    test.skip(!parto, 'no hay partos en la base');
    await page.goto(`/dashboard/partos/${parto.id}`);
    await page.getByRole('tab', { name: 'Trabajo de parto' }).click();
    await page.getByRole('button', { name: 'Registrar tacto' }).click();
    const modal = page.getByRole('dialog', { name: 'Registrar tacto' });
    await medir('U-Net intraparto (AoP)', '/partos/angulo-progresion/',
      () => modal.locator('input[type=file]').setInputFiles(INTRAPARTO));
    await expect(modal).toContainText('red entrenada con IUGC 2024', { timeout: 60_000 });
    await expect(modal.getByAltText('Ángulo de progresión dibujado')).toBeVisible();
    await modal.getByRole('button', { name: /Cancel|Cancelar/ }).click();
  });

  test('11. «Modelos y métricas» lista las 13 redes y los 2 modelos de tabla', async () => {
    await page.goto('/dashboard/ia-medica/imagenes?pestana=modelos');
    const tabla = page.locator('.ant-table');
    await expect(tabla).toContainText('Mioma uterino (U-Net)', { timeout: 30_000 });
    await expect(tabla).toContainText('Longitud del fémur (U-Net de puntos)');
    await expect(tabla.locator('tbody tr.ant-table-row')).toHaveCount(15);
  });

  test('12. peso al nacer (demostración) desde la ficha de una ecografía', async () => {
    const ecos = await apiGet('/ecografias/?page_size=50');
    const eco = (ecos.results || ecos).find((e) => e.biometria || e.circunferencia_abdominal || e.peso_fetal_estimado);
    test.skip(!eco, 'no hay ecografías con biometría');
    await page.goto(`/dashboard/ecografias/${eco.id}`);
    await page.getByRole('tab', { name: /Biometr/ }).click();
    const tarjeta = page.locator('.ant-card').filter({ hasText: 'Peso al nacer previsto' }).last();
    const r = await medir('Peso al nacer (regresión supervisada)', '/ia/prediccion-peso/',
      () => tarjeta.getByRole('button', { name: 'Calcular' }).click());
    // Con datos suficientes da el peso; si no (múltiple, < 20 semanas) lo explica: nunca una pantalla rota.
    if (r.status() === 200) await expect(tarjeta).toContainText('Hadlock (fórmula clínica)');
    else await expect(tarjeta.locator('.ant-alert')).toBeVisible();
  });

  test('13. asistente de consulta: una consulta rápida responde desde la base de conocimiento', async () => {
    await page.goto('/dashboard/ia-asistente');
    await medir('Asistente (base de conocimiento, no IA entrenada)', '/ia/consultas/consultar/',
      () => page.getByRole('button', { name: /Preeclampsia/ }).click());
    await expect(page.getByText(/Base de conocimiento · Preeclampsia/)).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('body')).not.toContainText(/Precisión \d/);
  });
});
