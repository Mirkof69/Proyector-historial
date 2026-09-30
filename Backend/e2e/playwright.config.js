// Pruebas E2E del flujo clínico. Requiere el sistema en marcha:
//   Django (8000), frontend (3000) y, para el paso de IA, el microservicio (8001).
// Variables: E2E_BASE_URL, E2E_API, E2E_EMAIL, E2E_PASSWORD, PW_CHROMIUM (ruta a chrome.exe).
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests',
  timeout: 120_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'reporte' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    viewport: { width: 1400, height: 950 },
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    launchOptions: process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {},
  },
});
