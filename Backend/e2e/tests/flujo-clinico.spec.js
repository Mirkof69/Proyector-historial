// Flujo clínico completo, como lo hace el personal: registro de la paciente
// → embarazo → control → ecografía con imagen → análisis con las redes
// medidas → parto. Cada paso llega con la paciente y el embarazo ya elegidos.
// Los datos se crean con apellido «E2E»; se borran con
//   python manage.py limpiar_datos_e2e --schema=clinica_demo
const path = require('path');
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const EMAIL = process.env.E2E_EMAIL || 'dra.garcia@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const IMAGEN = path.join(__dirname, '..', 'datos', 'eco_cabeza.png');
const CI = String(9000000 + (Date.now() % 900000));

const hace = (dias) => {
  const d = new Date(Date.now() - dias * 864e5);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const apiGet = (page, ruta) =>
  page.evaluate(async ([api, r]) => (await fetch(api + r, { credentials: 'include' })).json(), [API, ruta]);
const lista = (d) => (Array.isArray(d) ? d : d.results || []);
const valorDeSelect = (page, campo) =>
  page.locator(`.ant-form-item:has(label[for="${campo}"]) .ant-select-selection-item`).first();

test.describe.configure({ mode: 'serial' });

test.describe('Flujo clínico de punta a punta', () => {
  let page;
  const ids = {};
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

  test('1. registrar la paciente con el asistente (consentimiento obligatorio)', async () => {
    await page.goto('/dashboard/pacientes');
    await page.getByRole('button', { name: /Nueva Paciente|Nuevo Paciente/ }).first().click();
    const modal = page.locator('.ant-modal');
    await modal.locator('#nombre').fill('Flujo');
    await modal.locator('#apellido_paterno').fill('E2E');
    await modal.locator('#apellido_materno').fill('Prueba');
    await modal.locator('#ci').fill(CI);
    await modal.locator('#fecha_nacimiento').fill('12/03/1996');
    await page.keyboard.press('Tab');
    for (let i = 0; i < 2; i += 1) await modal.getByRole('button', { name: 'Siguiente' }).click();
    // Sin consentimiento no se registra (Ley 164)
    await modal.getByRole('button', { name: 'Registrar Paciente' }).click();
    await expect(modal.locator('.ant-form-item-explain-error')).toContainText('Ley 164');
    await modal.locator('input[type=checkbox]').check();
    await modal.getByRole('button', { name: 'Registrar Paciente' }).click();
    await expect(page.getByText('Paciente registrado exitosamente')).toBeVisible();
    // Tras el alta se ofrece registrar el embarazo con la paciente ya elegida
    await expect(page.locator('.ant-modal-confirm-title', { hasText: '¿Registrar ahora su embarazo?' })).toBeVisible();
    await page.getByRole('button', { name: 'Más tarde' }).click();
    const pac = lista(await apiGet(page, `/pacientes/?search=${CI}`))[0];
    expect(pac).toBeTruthy();
    ids.paciente = pac.id;
  });

  test('2. iniciar el embarazo desde la historia clínica', async () => {
    await page.goto(`/dashboard/historia-clinica/${ids.paciente}`);
    await page.getByRole('button', { name: /Iniciar Embarazo|Registrar Primer Embarazo/ }).first().click();
    await expect(page).toHaveURL(new RegExp(`/embarazos/nuevo\\?paciente=${ids.paciente}`));
    await expect(valorDeSelect(page, 'paciente')).toContainText('Flujo E2E Prueba');
    await page.locator('#fecha_ultima_menstruacion').fill(hace(140));
    await page.keyboard.press('Tab');
    await page.getByRole('button', { name: 'Crear Embarazo' }).click();
    await expect.poll(async () => lista(await apiGet(page, `/embarazos/?paciente=${ids.paciente}`)).length).toBe(1);
    ids.embarazo = lista(await apiGet(page, `/embarazos/?paciente=${ids.paciente}`))[0].id;
  });

  test('3. registrar el control prenatal', async () => {
    await page.goto(`/dashboard/historia-clinica/${ids.paciente}`);
    await page.getByRole('button', { name: 'Nuevo Control' }).first().click();
    await expect(valorDeSelect(page, 'embarazo')).toContainText('Flujo E2E Prueba');
    await expect(page.locator('#edad_gestacional_semanas')).toHaveValue('20');
    for (const [id, v] of [['peso_actual', '64'], ['presion_arterial_sistolica', '112'],
      ['presion_arterial_diastolica', '72'], ['altura_uterina', '20'], ['frecuencia_cardiaca_fetal', '146']]) {
      await page.fill(`#${id}`, v);
    }
    await page.click('#presentacion_fetal');
    await page.locator('.ant-select-dropdown:visible .ant-select-item-option').first().click();
    await page.getByRole('button', { name: /Guardar Control/ }).click();
    await expect.poll(async () => lista(await apiGet(page, `/controles/?embarazo=${ids.embarazo}`)).length).toBe(1);
  });

  test('4. registrar la ecografía con su imagen', async () => {
    await page.goto(`/dashboard/ecografias/nuevo?embarazo=${ids.embarazo}`);
    await expect(valorDeSelect(page, 'paciente')).toContainText('Flujo E2E Prueba');
    await expect(valorDeSelect(page, 'tipo_ecografia')).toContainText('Segundo Trimestre');
    await page.fill('#frecuencia_cardiaca_fetal', '146');
    await page.getByRole('tab', { name: /Imágenes y Conclusiones/ }).click();
    await page.locator('input[type=file]').last().setInputFiles(IMAGEN);
    await page.fill('#diagnostico', 'Feto único vivo, biometría acorde a 20 semanas.');
    await page.getByRole('button', { name: /Guardar Ecografía/ }).click();
    const delEmbarazo = async () => lista(await apiGet(page, `/ecografias/?embarazo=${ids.embarazo}`));
    await expect.poll(async () => (await delEmbarazo()).length).toBe(1);
    ids.ecografia = (await delEmbarazo())[0].id;
    await expect.poll(async () => (await apiGet(page, `/ecografias/${ids.ecografia}/`)).imagenes.length,
      { message: 'la imagen adjunta se subió' }).toBe(1);
  });

  test('5. analizar la ecografía con las redes medidas', async () => {
    const salud = await page.evaluate(async () => {
      try { return (await fetch('http://localhost:8001/health')).status; } catch { return 0; }
    });
    test.skip(salud !== 200, 'microservicio de IA no disponible');
    await page.goto(`/dashboard/ecografias/${ids.ecografia}`);
    await page.getByRole('tab', { name: /IA medida/ }).click();
    await page.fill('#tamano-pixel', '0.154');
    await page.getByRole('button', { name: 'Analizar' }).click();
    await expect(page.getByText('La imagen muestra')).toBeVisible({ timeout: 60000 });
    await expect(page.locator('body')).toContainText('cerebro fetal');
    // La cabeza de prueba es normal: la red de anomalías no debe alarmar.
    await expect(page.getByText('Cribado de anomalías cerebrales')).toBeVisible();
    await expect(page.getByText('Sin alarma', { exact: true })).toBeVisible();
  });

  test('6. el parto llega con el embarazo elegido', async () => {
    await page.goto(`/dashboard/partos/nuevo?paciente=${ids.paciente}`);
    await expect(valorDeSelect(page, 'embarazo')).toContainText('Flujo E2E Prueba');
    await expect(page.locator('#semanas_gestacion')).toHaveValue('20');
  });
});
