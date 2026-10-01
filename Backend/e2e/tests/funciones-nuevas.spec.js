// Las funciones nuevas del 01/10/2026, USADAS como lo haría el personal:
// partograma (registrar un tacto), Capurro del recién nacido, epicrisis
// (redactar y firmar), importación de laboratorio desde CSV y deshacerla, y
// clasificación de una cardiotocografía. Los datos llevan apellido «E2E»;
// se borran con  python manage.py limpiar_datos_e2e --schema=clinica_demo
const fs = require('fs');
const os = require('os');
const path = require('path');
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const EMAIL = process.env.E2E_EMAIL || 'dra.garcia@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const CI = String(8000000 + (Date.now() % 900000));

/** POST/GET a la API desde la página (misma cookie y token CSRF que el frontend). */
const api = (page, metodo, ruta, cuerpo) => page.evaluate(async ([base, m, r, c]) => {
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const res = await fetch(base + r, {
    method: m, credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: c ? JSON.stringify(c) : undefined,
  });
  return { status: res.status, datos: await res.json().catch(() => null) };
}, [API, metodo, ruta, cuerpo]);

const elegir = async (page, select, opcion) => {
  await select.click();
  await page.locator('.ant-select-dropdown:visible .ant-select-item-option', { hasText: opcion }).first().click();
};

test.describe.configure({ mode: 'serial' });

test.describe('Funciones nuevas en uso', () => {
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
    await page.request.get(`${API}/token/csrf/`);

    const hoy = new Date();
    const fum = new Date(hoy.getTime() - 39 * 7 * 864e5).toISOString().slice(0, 10);
    const paciente = await api(page, 'POST', '/pacientes/', {
      nombre: 'Funciones', apellido_paterno: 'E2E', apellido_materno: 'Nuevas', ci: CI,
      fecha_nacimiento: '1994-05-10', genero: 'femenino', consentimiento_datos_aceptado: true,
    });
    expect(paciente.status, JSON.stringify(paciente.datos)).toBe(201);
    ids.paciente = paciente.datos.id;
    const embarazo = await api(page, 'POST', '/embarazos/', {
      paciente: ids.paciente, numero_gesta: 1, numero_para: 0, numero_abortos: 0,
      fecha_ultima_menstruacion: fum, tipo_embarazo: 'simple',
    });
    expect(embarazo.status, JSON.stringify(embarazo.datos)).toBe(201);
    ids.embarazo = embarazo.datos.id;
    const parto = await api(page, 'POST', '/partos/', {
      embarazo: ids.embarazo, paciente: ids.paciente, tipo_parto: 'vaginal_espontaneo',
      fecha_parto: new Date(hoy.getTime() - 2 * 864e5).toISOString(), edad_gestacional_parto: '39+0',
      parto_finalizado: true, sexo_bebe: 'femenino', peso_bebe: 3150, talla_bebe: 49, apgar_1min: 8, apgar_5min: 9,
    });
    expect(parto.status, JSON.stringify(parto.datos)).toBe(201);
    ids.parto = parto.datos.id;
  });

  test.afterAll(async () => {
    await page.close();
    expect(erroresJs, 'errores de JavaScript en la página').toEqual([]);
  });

  test('1. partograma: registrar un tacto y verlo en la tabla', async () => {
    await page.goto(`/dashboard/partos/${ids.parto}?pestana=trabajo-parto`);
    await page.getByRole('button', { name: 'Registrar tacto' }).click();
    const modal = page.locator('.ant-modal:visible');
    await modal.locator('#dilatacion_cervical').fill('6');
    await modal.locator('#fcf_baseline').fill('142');
    await modal.getByRole('button', { name: 'Guardar' }).click();
    await expect(page.locator('.ant-table-row').first()).toContainText('6 cm');
    await expect(page.locator('.ant-table-row').first()).toContainText('142 lpm');
  });

  test('2. Capurro del recién nacido: 39,7 semanas, a término', async () => {
    await page.getByRole('tab', { name: /Recién nacido/ }).click();
    await page.getByRole('button', { name: 'Registrar Capurro / Ballard' }).click();
    const modal = page.locator('.ant-modal:visible');
    const selects = modal.locator('.ant-select');
    await elegir(page, selects.nth(0), 'Gruesa, grietas superficiales');
    await elegir(page, selects.nth(1), 'Pabellón totalmente incurvado');
    await elegir(page, selects.nth(2), 'Entre 5 y 10 mm');
    await elegir(page, selects.nth(3), 'areola punteada, borde no levantado');
    await elegir(page, selects.nth(4), 'Surcos en la mitad anterior');
    await expect(modal).toContainText('39.7 semanas · a término');
    await modal.getByRole('button', { name: 'Guardar' }).click();
    await expect(page.locator('.ant-tabs-tabpane-active')).toContainText('39.7 semanas');
  });

  test('3. epicrisis: redactar con la sugerencia y firmar', async () => {
    await page.getByRole('tab', { name: 'Epicrisis' }).click();
    await page.getByRole('button', { name: 'Redactar epicrisis' }).click();
    await expect(page.locator('#resumen_clinico')).toHaveValue(/3150 g/);
    await page.locator('#cie10_ingreso').fill('o80');
    await page.locator('#matricula_profesional').fill('MP-4521');
    await page.getByRole('button', { name: 'Guardar borrador' }).click();
    await expect(page.locator('.ant-tabs-tabpane-active')).toContainText('Borrador');
    await expect(page.locator('.ant-tabs-tabpane-active')).toContainText('O80');
    await page.getByRole('button', { name: 'Firmar' }).click();
    await page.locator('.ant-modal-confirm .ant-btn-primary').click();
    await expect(page.locator('.ant-tabs-tabpane-active')).toContainText('Firmada por');
    await expect(page.locator('.ant-tabs-tabpane-active').getByRole('button', { name: 'Editar' })).toHaveCount(0);
  });

  test('4. laboratorio: importar un CSV con otros encabezados y deshacerlo', async () => {
    const ayer = new Date(Date.now() - 864e5);
    const fecha = `${String(ayer.getDate()).padStart(2, '0')}/${String(ayer.getMonth() + 1).padStart(2, '0')}/${ayer.getFullYear()}`;
    const archivo = path.join(os.tmpdir(), `lab_e2e_${CI}.csv`);
    fs.writeFileSync(archivo, `Cédula;Código de examen;Fecha;Analito;Resultado\n${CI};HEM001;${fecha};Hemoglobina;11,9\n${CI};HEM001;${fecha};Plaquetas;250000\n`, 'latin1');
    await page.goto('/dashboard/laboratorio');
    await page.getByRole('button', { name: /Importar Excel o CSV/ }).click();
    await page.locator('.ant-modal:visible input[type=file]').setInputFiles(archivo);
    await page.getByRole('button', { name: 'Revisar archivo' }).click();
    await expect(page.locator('.ant-modal:visible')).toContainText('Lista para importar');
    await page.getByRole('button', { name: /Guardar 2 resultados/ }).click();
    await expect(page.locator('.ant-modal:visible')).toContainText('Se guardaron 2 resultados');
    await page.getByRole('button', { name: 'Terminar' }).click();

    await page.getByRole('button', { name: /Importar Excel o CSV/ }).click();
    await page.getByText('Importaciones anteriores').click();
    const fila = page.locator('.ant-table-row', { hasText: `lab_e2e_${CI}.csv` });
    await fila.getByRole('button', { name: 'Deshacer' }).click();
    await page.locator('.ant-modal:visible textarea').fill('Prueba E2E: se subió el archivo equivocado');
    await page.getByRole('button', { name: 'Deshacer', exact: true }).click();
    await expect(fila).toContainText('Anulada');
    const examenes = await api(page, 'GET', `/laboratorios/examenes/?paciente=${ids.paciente}`);
    expect((examenes.datos.results || examenes.datos).length).toBe(0);
    fs.unlinkSync(archivo);
  });

  test('5. cardiotocografía: un trazado normal se clasifica «Normal»', async () => {
    const normal = {
      linea_base: 132, aceleraciones: 0.006, movimientos_fetales: 0, contracciones: 0.006,
      desaceleraciones_leves: 0.003, desaceleraciones_severas: 0, desaceleraciones_prolongadas: 0,
      vcp_anormal_pct: 17, vcp_media: 2.1, vlp_anormal_pct: 0, vlp_media: 10.4, histograma_ancho: 130,
      histograma_minimo: 68, histograma_maximo: 198, histograma_picos: 6, histograma_ceros: 1, histograma_moda: 141,
      histograma_media: 136, histograma_mediana: 140, histograma_varianza: 12, histograma_tendencia: 0,
    };
    await page.goto('/dashboard/ia-medica/imagenes?pestana=cardiotocografia');
    await page.getByText('Fiabilidad medida del modelo').waitFor();
    for (const [clave, valor] of Object.entries(normal)) {
      const campo = page.locator(`#${clave}`);
      if (await campo.count()) await campo.fill(String(valor));
    }
    await page.getByRole('button', { name: 'Clasificar' }).click();
    await expect(page.locator('.ant-tag', { hasText: 'Normal' }).first()).toBeVisible();
  });
});
