// Otro funcionario sin programar: el administrador crea el cargo «Obstetriz»
// sobre el rol médico sin el módulo de laboratorio, le da ese cargo a un
// usuario nuevo, y ese usuario entra: ve Partos, no ve Laboratorio, y la API
// se lo rechaza. El cargo lleva «E2E» y se borra con
//   python manage.py limpiar_datos_e2e --schema=clinica_demo
// El usuario de prueba es siempre el mismo y se reutiliza: quien ya entró tiene
// registros de auditoría, que son inmutables (Ley 164), así que no se borra:
// la limpieza lo desactiva y le quita el cargo.
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const ADMIN = process.env.E2E_ADMIN_EMAIL || 'admin.demo@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const SELLO = Date.now() % 1000000;
const CARGO = `E2E Obstetriz ${SELLO}`;
const USUARIO = 'obstetriz@e2e.test';
// Clave de un solo uso, generada en cada corrida.
const CLAVE_USUARIO = `Cargo-${SELLO}-${Math.random().toString(36).slice(2, 8)}!A`;

const api = (page, metodo, ruta, cuerpo) => page.evaluate(async ([base, m, r, c]) => {
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const res = await fetch(base + r, {
    method: m, credentials: 'include',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: c ? JSON.stringify(c) : undefined,
  });
  return { status: res.status, datos: await res.json().catch(() => null) };
}, [API, metodo, ruta, cuerpo]);

const entrar = async (page, email, clave) => {
  await page.goto('/login');
  await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', email);
  await page.fill('input[placeholder="Ingrese su contraseña"]', clave);
  await page.click('button[type=submit]');
  await page.waitForURL((u) => !u.pathname.includes('login'));
  await page.request.get(`${API}/token/csrf/`);
};

test.describe.configure({ mode: 'serial' });

test.describe('Cargos: otros funcionarios', () => {
  let admin;
  const ids = {};
  const erroresJs = [];

  test.beforeAll(async ({ browser }) => {
    admin = await browser.newPage();
    admin.on('pageerror', (e) => erroresJs.push(e.message));
    await entrar(admin, ADMIN, PASSWORD);
  });

  test.afterAll(async () => {
    await admin.close();
    expect(erroresJs, 'errores de JavaScript en la página').toEqual([]);
  });

  test('1. el administrador crea el cargo sin laboratorio', async () => {
    await admin.goto('/dashboard/roles/nuevo');
    await admin.getByPlaceholder(/Obstetriz/).fill(CARGO);
    await admin.getByLabel('Rol en que se basa').click();
    await admin.locator('.ant-select-dropdown:visible .ant-select-item-option', { hasText: 'Médico' }).click();
    const laboratorio = admin.getByRole('checkbox', { name: /^Laboratorio/ });
    await expect(laboratorio).toBeChecked();
    await laboratorio.uncheck();
    await admin.getByRole('button', { name: /Guardar/ }).click();
    await admin.waitForURL('**/dashboard/roles');
    await expect(admin.getByText(CARGO)).toBeVisible();

    const cargos = await api(admin, 'GET', '/roles/cargos/');
    const cargo = cargos.datos.find((c) => c.nombre === CARGO);
    expect(cargo.rol_base).toBe('medico');
    expect(cargo.modulos).not.toContain('laboratorio');
    expect(cargo.modulos).toContain('partos');
    ids.cargo = cargo.id;
  });

  test('2. un usuario nuevo con ese cargo entra: ve Partos, no Laboratorio, y la API lo bloquea', async ({ browser }) => {
    const datos = {
      email: USUARIO, nombre: 'Obstetriz', apellido_paterno: 'E2E', cargo: ids.cargo,
      password: CLAVE_USUARIO, password_confirm: CLAVE_USUARIO, activo: true,
    };
    const todos = await api(admin, 'GET', '/usuarios/todos/');
    const existente = (todos.datos.results || todos.datos).find((u) => u.email === USUARIO);
    const alta = existente
      ? await api(admin, 'PATCH', `/usuarios/${existente.id}/`, datos)
      : await api(admin, 'POST', '/usuarios/', datos);
    expect([200, 201], JSON.stringify(alta.datos)).toContain(alta.status);

    const contexto = await browser.newContext();
    const obstetriz = await contexto.newPage();
    obstetriz.on('pageerror', (e) => erroresJs.push(e.message));
    await entrar(obstetriz, USUARIO, CLAVE_USUARIO);

    const menu = obstetriz.locator('.ant-layout-sider');
    await expect(menu.getByText('Partos', { exact: true })).toBeVisible();
    await expect(menu.getByText('Laboratorio', { exact: true })).toHaveCount(0);

    expect((await api(obstetriz, 'GET', '/laboratorios/examenes/')).status).toBe(403);
    expect((await api(obstetriz, 'GET', '/partos/')).status).toBe(200);
    await contexto.close();
  });
});
