// Recorre TODAS las pantallas sin parámetros del sistema, como administrador,
// en tema claro y oscuro, y falla si alguna:
//   - lanza un error de JavaScript,
//   - recibe un 500 de la API,
//   - se queda en blanco (sin el menú lateral ni contenido),
//   - desborda la página hacia los lados (scroll horizontal).
// Deja una captura por pantalla y tema en test-results/pantallas/ para revisar
// el diseño a ojo. Las rutas con :id se prueban en los flujos (flujo-clinico…).
const fs = require('fs');
const path = require('path');
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const ADMIN = process.env.E2E_ADMIN_EMAIL || 'admin.demo@fetalmedical.bo';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const CAPTURAS = path.join(__dirname, '..', 'test-results', 'pantallas');

const RUTAS = [
  'home', 'pacientes', 'pacientes/nuevo', 'pacientes/buscar', 'historia-clinica', 'embarazos', 'embarazos/nuevo',
  'controles', 'controles/nuevo', 'ecografias', 'ecografias/nuevo', 'ia-medica/imagenes', 'ia-guia', 'ia-asistente',
  'partos', 'partos/nuevo', 'triaje', 'triaje/nuevo', 'citas', 'citas/hoy', 'citas/calendario', 'citas/nuevo',
  'laboratorio', 'laboratorio/nuevo', 'laboratorio/resultados', 'laboratorio/tipos-examen',
  'laboratorio/valores-referencia', 'laboratorios', 'vacunas', 'vacunas/nuevo', 'vacunas/tipos',
  'notas-evolucion', 'notas-evolucion/nuevo', 'antecedentes', 'antecedentes/patologicos',
  'antecedentes/gineco-obstetricos', 'calculadoras', 'calculadoras/bishop', 'calculadoras/crecimiento-fetal',
  'calculadoras/dosis-medicamentos', 'calculadoras/hemorragia-obstetrica', 'calculadoras/imc-ganancia',
  'calculadoras/preeclampsia', 'calculadoras/riesgo-cromosomico', 'calculadoras/sufrimiento-fetal',
  'calculadoras-avanzadas', 'panel-calculadoras', 'alertas', 'alertas/configuracion', 'alertas/sistema',
  'notificaciones', 'reportes', 'reportes/kpis', 'reportes/indicadores', 'reportes/pdf', 'estadisticas',
  'graficas', 'busqueda', 'consultorios', 'usuarios', 'roles', 'roles/nuevo', 'auditoria', 'access-logs',
  'backup', 'configuracion', 'perfil', 'ayuda',
];

test.describe.configure({ mode: 'default' });

for (const tema of ['light', 'dark']) {
  test.describe(`Todas las pantallas · tema ${tema}`, () => {
    let page;
    const problemas = [];

    test.beforeAll(async ({ browser }) => {
      fs.mkdirSync(CAPTURAS, { recursive: true });
      const contexto = await browser.newContext({ viewport: { width: 1440, height: 900 } });
      await contexto.addInitScript((t) => {
        try { localStorage.setItem('app-theme', t); } catch { /* sin almacenamiento */ }
      }, tema);
      page = await contexto.newPage();
      page.on('pageerror', (e) => problemas.push(`JS: ${e.message}`));
      page.on('response', (r) => {
        if (r.status() >= 500) problemas.push(`HTTP ${r.status()} ${r.url()}`);
      });
      await page.goto('/login');
      await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', ADMIN);
      await page.fill('input[placeholder="Ingrese su contraseña"]', PASSWORD);
      await page.click('button[type=submit]');
      await page.waitForURL((u) => !u.pathname.includes('login'));
      await page.request.get(`${API}/token/csrf/`);
    });

    test.afterAll(async () => { await page.context().close(); });

    for (const ruta of RUTAS) {
      test(`${tema} · ${ruta}`, async () => {
        problemas.length = 0;
        await page.goto(`/dashboard/${ruta}`);
        await page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {});
        await expect.soft(page.locator('.ant-layout-sider')).toBeVisible();
        const contenido = await page.locator('.ant-layout-content').first().innerText().catch(() => '');
        expect.soft(contenido.trim().length, 'la pantalla quedó en blanco').toBeGreaterThan(20);
        const desborde = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
        await page.screenshot({ path: path.join(CAPTURAS, `${tema}__${ruta.replace(/\//g, '_')}.png`) });
        expect.soft(desborde, 'la página se desborda hacia los lados').toBeLessThanOrEqual(1);
        expect.soft(problemas, 'errores en la pantalla').toEqual([]);
      });
    }
  });
}
