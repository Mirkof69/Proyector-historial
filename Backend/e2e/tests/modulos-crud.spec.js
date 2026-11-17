// Alta y edición en cada módulo del menú, como lo hace el personal, y
// comprobación en la API de que lo guardado quedó en la base de datos.
//
// Por cada formulario «nuevo»: rellena los campos obligatorios (abriendo cada
// desplegable y calendario y comprobando que cae DENTRO de la pantalla),
// guarda, lee el mensaje que ve el usuario y busca el registro en la API.
// Luego abre «editar» de ese mismo registro, cambia un texto, guarda y vuelve a
// leerlo de la API: el cambio tiene que estar.
//
// Corre con las animaciones del sistema apagadas (prefers-reduced-motion), que
// es como estaba el equipo donde los desplegables se iban fuera de la pantalla.
// Los datos van a una paciente de apellido «E2E»; se borran con
//   python manage.py limpiar_datos_e2e --schema=clinica_demo
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const ADMIN = process.env.E2E_ADMIN_EMAIL || 'admin.demo@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
// La misma en toda la corrida: si un módulo falla, Playwright abre otro worker
// que vuelve a cargar este archivo y tiene que encontrar la misma paciente.
const MARCA = process.env.E2E_MARCA || String(Math.floor(Date.now() / 36e5) % 1e6);
const CI = String(8000000 + (Number(MARCA) % 900000));

test.use({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } });
test.setTimeout(180_000);
// Sin «serial»: un módulo que falla no salta a los demás.
test.describe.configure({ mode: 'default' });

// Fecha como se teclea en la máscara DD/MM/AAAA (solo dígitos), «dias» atrás.
const fechaTecleada = (dias = 0) => {
  const d = new Date(Date.now() - dias * 864e5);
  return `${String(d.getDate()).padStart(2, '0')}${String(d.getMonth() + 1).padStart(2, '0')}${d.getFullYear()}`;
};

// Valores clínicamente razonables para los campos numéricos obligatorios.
const NUMEROS = {
  presion_arterial_sistolica: '112', presion_arterial_diastolica: '72', frecuencia_cardiaca: '78',
  temperatura: '36.6', peso_actual: '64', edad_gestacional_semanas: '24', numero_control: '1',
  numero_gesta: '1', gestas: '1', numero_dosis: '1', frecuencia_respiratoria: '16', saturacion_oxigeno: '98',
  peso: '64', talla: '158', altura_uterina: '20', frecuencia_cardiaca_fetal: '142',
};

const TEXTOS = { codigo: `E2E${MARCA}`, nombre: `E2E Prueba ${MARCA}`, lote: `L-${MARCA}`, laboratorio: 'Laboratorio E2E' };

// El id del campo puede llevar delante el nombre del formulario («nota_temperatura»).
const valorPara = (tabla, campo) => {
  const clave = Object.keys(tabla).sort((a, b) => b.length - a.length)
    .find((k) => campo === k || campo.endsWith(`_${k}`));
  return clave ? tabla[clave] : undefined;
};

/** Rellena los obligatorios vacíos que se ven. Devuelve desplegables fuera de pantalla. */
async function rellenarObligatorios(page) {
  const fuera = [];
  const items = page.locator('.ant-form-item:has(label.ant-form-item-required):visible');
  const n = await items.count();
  for (let i = 0; i < n; i += 1) {
    const item = items.nth(i);
    const campo = (await item.locator('label').first().getAttribute('for')) || `campo${i}`;
    if (await item.locator('.ant-select').count()) {
      // Ya elegido, o fijo en la edición (la paciente de un registro no se cambia).
      if (await item.locator('.ant-select-selection-item').count()) continue;
      if (await item.locator('.ant-select-disabled').count()) continue;
      const lista = page.locator('.ant-select-dropdown:not(.ant-select-dropdown-hidden)').last();
      // Un clic que llega mientras la pantalla termina de cargar puede perderse: se reintenta.
      let abierto = false;
      for (let intento = 0; intento < 2 && !abierto; intento += 1) {
        await item.locator('.ant-select-selector').click();
        abierto = await lista.waitFor({ state: 'visible', timeout: 5000 }).then(() => true, () => false);
      }
      if (!abierto) throw new Error(`el desplegable «${campo}» no se abre`);
      if (/paciente|embarazo/.test(campo)) await page.keyboard.type(CI, { delay: 20 });
      await page.waitForTimeout(/paciente|embarazo/.test(campo) ? 1500 : 200);
      if (!(await dentroDePantalla(page, lista))) fuera.push(campo);
      const opcion = lista.locator('.ant-select-item-option:not(.ant-select-item-option-disabled)').first();
      await opcion.waitFor({ state: 'visible', timeout: 8000 });
      await opcion.click();
    } else if (/(^|_)hora/.test(campo) && (await page.locator('.citas-page__horario-libre').count())) {
      // La hora de la cita se elige entre los horarios libres del médico.
      if (await item.locator('.ant-picker input').first().inputValue()) continue;
      await page.locator('.citas-page__horario-libre').first().click();
    } else if (await item.locator('.ant-picker').count()) {
      const entrada = item.locator('.ant-picker input').first();
      if (await entrada.inputValue() || (await entrada.isDisabled())) continue;
      await entrada.click();
      const cal = page.locator('.ant-picker-dropdown:not(.ant-picker-dropdown-hidden)').last();
      await cal.waitFor({ state: 'visible' });
      if (!(await dentroDePantalla(page, cal))) fuera.push(campo);
      // La FUM de un embarazo de 20 semanas; la cita, mañana; el resto, hoy.
      // Los datos de demostración llenan la agenda dos meses: la cita va a 70 días.
      let dias = valorPara({ fecha_ultima_menstruacion: 140, fecha_cita: -70 }, campo) || 0;
      // La agenda atiende de lunes a viernes: una cita en sábado se rechaza con razón.
      while (campo === 'fecha_cita' && [0, 6].includes(new Date(Date.now() - dias * 864e5).getDay())) dias -= 1;
      await page.keyboard.type(fechaTecleada(dias));
      await page.keyboard.press('Enter');
    } else if (await item.locator('.ant-radio-group').count()) {
      if (await item.locator('.ant-radio-wrapper-checked, .ant-radio-button-wrapper-checked').count()) continue;
      await item.locator('.ant-radio-wrapper, .ant-radio-button-wrapper').first().click();
    } else if (await item.locator('.ant-input-number').count()) {
      const entrada = item.locator('input').first();
      if (await entrada.inputValue()) continue;
      await entrada.fill(valorPara(NUMEROS, campo) || '1');
    } else if (await item.locator('textarea, input').count()) {
      const entrada = item.locator('textarea, input').first();
      if (await entrada.inputValue()) continue;
      await entrada.fill(valorPara(TEXTOS, campo) || `Prueba E2E ${MARCA}`);
    }
  }
  return fuera;
}

async function dentroDePantalla(page, popup) {
  const r = await popup.boundingBox();
  const v = page.viewportSize();
  return !!r && r.x >= -2 && r.y >= -2 && r.x + r.width <= v.width + 2 && r.y <= v.height;
}

// El nombre accesible del botón lleva delante el de su icono («save Guardar Cambios»).
const BOTON_AVANCE = /^(\S+ )?(Continuar|Siguiente|Guardar|Registrar|Crear|Actualizar|Agendar|Confirmar)/;

/**
 * Rellena y avanza (formularios de varios pasos) hasta que la API responde a
 * la escritura. Devuelve { respuesta, json, fuera, mensajes }.
 */
async function enviarFormulario(page, metodos) {
  const fuera = [];
  for (let paso = 0; paso < 6; paso += 1) {
    fuera.push(...(await rellenarObligatorios(page)));
    const boton = page.locator('.ant-layout-content').getByRole('button', { name: BOTON_AVANCE }).last();
    const escritura = page.waitForResponse(
      // La escritura del formulario, no la renovación del token ni la auditoría.
      (r) => r.url().startsWith(API) && [].concat(metodos).includes(r.request().method())
        && !/\/(token|auditoria|logs|notificaciones|usuarios\/(logout|me))\//.test(r.url()),
      { timeout: 6000 },
    ).catch(() => null);
    await boton.click();
    const respuesta = await escritura;
    if (respuesta) {
      await page.waitForTimeout(800);
      const mensajes = await page.locator('.ant-message-notice-content, .ant-notification-notice-message').allTextContents();
      let json = null;
      try { json = await respuesta.json(); } catch { /* sin cuerpo */ }
      return { respuesta, json, fuera, mensajes };
    }
    const errores = await page.locator('.ant-form-item-explain-error:visible').allTextContents();
    if (errores.length && paso > 2) return { respuesta: null, fuera, mensajes: errores };
  }
  return { respuesta: null, fuera, mensajes: ['el formulario no envió nada a la API'] };
}

const apiGet = (page, url) =>
  page.evaluate(async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    return { status: r.status, cuerpo: r.ok ? await r.json() : null };
  }, url);

// [nombre, ruta de alta, ruta de edición (con :id)]
const MODULOS = [
  ['Embarazos', 'embarazos/nuevo', 'embarazos/:id/editar'],
  ['Triaje', 'triaje/nuevo', 'triaje/:id/editar'],
  ['Antecedentes patológicos', 'antecedentes/patologicos/nuevo', 'antecedentes/patologicos/:id/editar'],
  ['Controles prenatales', 'controles/nuevo', 'controles/:id/editar'],
  ['Notas de evolución', 'notas-evolucion/nuevo', 'notas-evolucion/:id/editar'],
  ['Vacunas', 'vacunas/nuevo', 'vacunas/:id/editar'],
  ['Laboratorio', 'laboratorio/nuevo', 'laboratorio/:id/editar'],
  ['Citas', 'citas/nuevo', 'citas/:id/editar'],
  ['Consultorios', 'consultorios/nuevo', 'consultorios/editar/:id'],
];

test.describe('Alta y edición en cada módulo (con animaciones apagadas)', () => {
  let page;
  const erroresJs = [];
  const errores500 = [];

  test.beforeAll(async ({ browser }) => {
    page = await browser.newPage();
    page.on('pageerror', (e) => erroresJs.push(`${page.url()}: ${e.message}`));
    page.on('response', (r) => { if (r.status() >= 500) errores500.push(`${r.status()} ${r.request().method()} ${r.url()}`); });
    await page.goto('/login');
    await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', ADMIN);
    await page.fill('input[placeholder="Ingrese su contraseña"]', PASSWORD);
    await page.click('button[type=submit]');
    await page.waitForURL((u) => !u.pathname.includes('login'));
  });

  test.afterAll(async () => {
    await page.close();
    expect(erroresJs, 'errores de JavaScript').toEqual([]);
    expect(errores500, 'errores 500 de la API').toEqual([]);
  });

  test('0. registrar la paciente de prueba', async () => {
    await page.goto('/dashboard/pacientes');
    await page.getByRole('button', { name: /Nueva Paciente|Nuevo Paciente/ }).first().click();
    const modal = page.locator('.ant-modal');
    await modal.locator('#nombre').fill('Modulos');
    await modal.locator('#apellido_paterno').fill('E2E');
    await modal.locator('#apellido_materno').fill('Prueba');
    await modal.locator('#ci').fill(CI);
    await modal.locator('#fecha_nacimiento').click();
    await page.keyboard.type('05061994');
    await page.keyboard.press('Tab');
    for (let i = 0; i < 2; i += 1) await modal.getByRole('button', { name: 'Siguiente' }).click();
    await modal.locator('input[type=checkbox]').check();
    await modal.getByRole('button', { name: 'Registrar Paciente' }).click();
    await expect(page.getByText('Paciente registrado exitosamente')).toBeVisible();
    await page.getByRole('button', { name: 'Más tarde' }).click();
    const { cuerpo } = await apiGet(page, `${API}/pacientes/?search=${CI}`);
    expect((cuerpo.results || cuerpo).length).toBe(1);
  });

  for (const [nombre, alta, edicion] of MODULOS) {
    test(`${nombre}: alta, edición y que quede en la base`, async () => {
      // Alta
      await page.goto(`/dashboard/${alta}`);
      await page.locator('.ant-form').first().waitFor();
      const creado = await enviarFormulario(page, 'POST');
      expect(creado.respuesta, `${nombre}: ${creado.mensajes.join(' | ')}`).not.toBeNull();
      expect(creado.respuesta.status(), `${nombre}: ${creado.respuesta.request().method()} ${creado.respuesta.url()} ${creado.respuesta.request().postData()} → ${JSON.stringify(creado.json)}`).toBeLessThan(300);
      expect(creado.fuera, `${nombre}: desplegables fuera de la pantalla`).toEqual([]);
      expect(creado.mensajes.join(' '), `${nombre}: el usuario no vio confirmación`).toMatch(/éxito|exitos|correctamente|registrad|guardad|cread|agendad|actualizad/i);
      const id = creado.json?.id;
      expect(id, `${nombre}: la API no devolvió el id`).toBeTruthy();
      const base = creado.respuesta.url().split('?')[0].replace(/\/$/, '');
      const detalle = `${base}/${id}/`;
      expect((await apiGet(page, detalle)).status, `${nombre}: no está en la base`).toBe(200);

      // Edición: cambia el primer texto largo (observaciones, notas…) y guarda
      await page.goto(`/dashboard/${edicion.replace(':id', id)}`);
      await page.locator('.ant-form').first().waitFor();
      const texto = page.locator('.ant-form textarea:visible').last();
      await texto.waitFor({ timeout: 8000 }).catch(() => {}); // la edición carga el registro
      // En los formularios por pasos (triaje) el texto está en un paso posterior.
      for (let paso = 0; paso < 4 && !(await texto.count()); paso += 1) {
        await page.locator('.ant-layout-content').getByRole('button', { name: /Continuar|Siguiente/ }).last().click();
        await page.waitForTimeout(400);
      }
      await texto.waitFor();
      const nuevo = `Editado E2E ${MARCA}`;
      await texto.fill(nuevo);
      const editado = await enviarFormulario(page, ['PUT', 'PATCH']);
      expect(editado.respuesta, `${nombre} (editar): ${editado.mensajes.join(' | ')}`).not.toBeNull();
      expect(editado.respuesta.status(), `${nombre} (editar): ${JSON.stringify(editado.json)}`).toBeLessThan(300);
      expect(editado.fuera, `${nombre} (editar): desplegables fuera de la pantalla`).toEqual([]);
      const releido = await apiGet(page, detalle);
      expect(JSON.stringify(releido.cuerpo), `${nombre}: la edición no quedó en la base`).toContain(nuevo);
    });
  }
});
