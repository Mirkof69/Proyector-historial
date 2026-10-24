// HTML → PDF A4 con el Chromium de Playwright (el de Backend/e2e).
//   node a_pdf.js entrada.html salida.pdf      (ejecutar con cwd = Backend/e2e)
const path = require('path');
const { chromium } = require(require.resolve('@playwright/test', { paths: [process.cwd()] }));

(async () => {
  const [entrada, salida] = process.argv.slice(2);
  const navegador = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const pagina = await navegador.newPage();
  await pagina.goto('file:///' + path.resolve(entrada).replace(/\\/g, '/'), { waitUntil: 'networkidle' });
  await pagina.evaluate(() => document.fonts.ready);
  await pagina.pdf({
    path: salida, format: 'A4', preferCSSPageSize: true, printBackground: true, displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:7pt;color:#5b6470;width:100%;text-align:center">Guion de demostración · '
      + 'Fetal Medical Bolivia · página <span class="pageNumber"></span> de <span class="totalPages"></span></div>',
  });
  await navegador.close();
})();
