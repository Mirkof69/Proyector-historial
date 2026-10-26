// Recorre la demostración completa en el sistema real, como se hará delante del
// jurado, y saca una captura por paso con recuadros numerados donde hay que
// hacer clic. Deja guion/salida/pasos.json y guion/salida/capturas/*.png;
// generar_pdf.py arma el PDF con eso.
//
//   node guion/capturar_guion.js          (cwd = Backend/e2e, sistema en marcha)
//
// La paciente del guion (María Fernanda Quispe Mamani, CI 8899001) se borra al
// empezar y al terminar con  manage.py limpiar_datos_e2e --ci 8899001, para que
// en la demostración en vivo se pueda registrar otra vez con los mismos datos.
// Contraseñas: E2E_PASSWORD (las tres cuentas de demostración usan la misma).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { chromium } = require('@playwright/test');

const BASE = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API = process.env.E2E_API || 'http://localhost:8000/api';
const CLAVE = process.env.E2E_PASSWORD;
const BACKEND = path.join(__dirname, '..', '..');
const SALIDA = path.join(__dirname, 'salida');
const CAPTURAS = path.join(SALIDA, 'capturas');
const MUESTRAS = path.join(process.env.USERPROFILE, 'Desktop', 'MUESTRAS_IA_Fetal_Medical');
const SOLO_HASTA = Number(process.env.HASTA || 999);

const PACIENTE = {
  nombre: 'María Fernanda', apellido_paterno: 'Quispe', apellido_materno: 'Mamani', ci: '8899001',
  fecha_nacimiento: '14/05/1995', telefono: '71234567', ciudad: 'La Paz',
};
const NOMBRE = `${PACIENTE.nombre} ${PACIENTE.apellido_paterno} ${PACIENTE.apellido_materno}`;

const fecha = (dias) => {
  const d = new Date(Date.now() - dias * 864e5);
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`;
};
const FUM = fecha(39 * 7);

function limpiar() {
  const py = path.join(BACKEND, '.venv', 'Scripts', 'python.exe');
  const salida = execFileSync(py, ['manage.py', 'limpiar_datos_e2e', '--schema=clinica_demo', '--ci', PACIENTE.ci],
    { cwd: BACKEND, encoding: 'utf8', env: { ...process.env, PYTHONIOENCODING: 'utf-8' } });
  console.log(salida.trim().split('\n').pop());
}

let page;
const pasos = [];
const ids = {};

/** Cajas (en coordenadas de la ventana) de los elementos donde hay que hacer clic. */
async function cajasDe(objetivos) {
  const cajas = [];
  for (const [i, o] of objetivos.entries()) {
    const bb = await o.first().boundingBox().catch(() => null);
    if (bb) cajas.push({ ...bb, n: i + 1 });
    else console.log(`   (sin caja para el objetivo ${i + 1})`);
  }
  return cajas;
}

/** Dibuja recuadros rojos numerados (fijos a la ventana) sobre esas cajas. */
async function dibujar(cajas) {
  await page.evaluate((lista) => {
    for (const c of lista) {
      const d = document.createElement('div');
      d.className = 'guion-marca';
      Object.assign(d.style, {
        position: 'fixed', left: `${c.x - 5}px`, top: `${c.y - 5}px`, width: `${c.width + 10}px`,
        height: `${c.height + 10}px`, border: '3px solid #e0262b', borderRadius: '7px', zIndex: 2147483647,
        pointerEvents: 'none', boxShadow: '0 0 0 4px rgba(224,38,43,.22)',
      });
      const n = document.createElement('span');
      n.textContent = c.n;
      Object.assign(n.style, {
        position: 'absolute', left: '-15px', top: '-15px', width: '24px', height: '24px', borderRadius: '12px',
        background: '#e0262b', color: '#fff', font: '700 14px Arial', display: 'flex', alignItems: 'center',
        justifyContent: 'center',
      });
      d.appendChild(n);
      document.body.appendChild(d);
    }
  }, cajas);
}

/**
 * Un paso del guion: captura con los recuadros y el texto que lo acompaña.
 * meta = { seccion, titulo, cuenta, clics: [...], escribir: [[campo, valor]], decir, nota }
 * Si los recuadros no caben en la pantalla, la ventana se agranda para la
 * captura (pegar trozos de la página duplicaba el menú lateral fijo).
 */
async function paso(meta, objetivos = []) {
  // El menú de temas del encabezado se abre al pasar el ratón: lejos de él en cada captura.
  await page.mouse.move(640, 790);
  await page.waitForTimeout(600);
  const base = page.viewportSize();
  if (objetivos.length) {
    await objetivos[0].first().evaluate((el) => {
      const r = el.getBoundingClientRect();
      if (r.top < 70 || r.bottom > window.innerHeight) el.scrollIntoView({ block: 'center' });
    }).catch(() => {});
  }
  let cajas = await cajasDe(objetivos);
  const fuera = cajas.some((c) => c.y < 0 || c.y + c.height > base.height);
  if (fuera) {
    const arriba = Math.min(...cajas.map((c) => c.y));
    const abajo = Math.max(...cajas.map((c) => c.y + c.height));
    await page.setViewportSize({ width: base.width, height: Math.round(Math.min(Math.max(base.height, abajo - arriba + 260), 2000)) });
    await page.waitForTimeout(500);
    await objetivos[0].first().evaluate((el) => {
      el.style.scrollMarginTop = '150px';
      el.scrollIntoView({ block: 'start' });
    }).catch(() => {});
    await page.waitForTimeout(400);
    cajas = await cajasDe(objetivos);
  }
  await dibujar(cajas);
  const n = String(pasos.length + 1).padStart(2, '0');
  await page.screenshot({ path: path.join(CAPTURAS, `${n}.png`) });
  await page.evaluate(() => document.querySelectorAll('.guion-marca').forEach((e) => e.remove()));
  if (fuera) await page.setViewportSize(base);
  pasos.push({ n, ...meta });
  fs.writeFileSync(path.join(SALIDA, 'pasos.json'), JSON.stringify({ paciente: { ...PACIENTE, fum: FUM }, pasos }, null, 2));
  console.log(`${n} ${meta.titulo}`);
  if (pasos.length >= SOLO_HASTA) throw new Error('HASTA');
}

/** Lista de campos y botones visibles (para escribir el guion). */
async function inventario(etiqueta) {
  const datos = await page.evaluate(() => ({
    campos: [...document.querySelectorAll('input[id], textarea[id]')].filter((i) => i.offsetParent).map((i) => i.id),
    botones: [...new Set([...document.querySelectorAll('button')].filter((b) => b.offsetParent)
      .map((b) => b.innerText.trim()).filter(Boolean))],
  }));
  console.log(`   [${etiqueta}] ${page.url()}\n   campos: ${datos.campos.join(', ')}\n   botones: ${datos.botones.join(' | ')}`);
}

const api = (metodo, ruta, cuerpo) => page.evaluate(async ([base, m, r, c]) => {
  const csrf = (document.cookie.match(/csrftoken=([^;]+)/) || [])[1] || '';
  const res = await fetch(base + r, {
    method: m, credentials: 'include', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: c ? JSON.stringify(c) : undefined,
  });
  return { status: res.status, datos: await res.json().catch(() => null) };
}, [API, metodo, ruta, cuerpo]);
const lista = (d) => (Array.isArray(d) ? d : (d && d.results) || []);
const menu = (nombre) => page.getByRole('menuitem', { name: nombre }).first();
const boton = (nombre, exacto = false) => page.getByRole('button', { name: nombre, exact: exacto }).first();
const campo = (id) => page.locator(`#${id}`).first();
const elegirEnSelect = async (select, texto, opcion = texto) => {
  await select.click();
  await page.keyboard.type(texto, { delay: 30 });
  await page.locator('.ant-select-dropdown:visible .ant-select-item-option', { hasText: opcion }).first().click();
};
// Buscar a la paciente en los selectores: por CI donde la lista lo muestra.
const BUSCAR = process.env.BUSCAR_POR_NOMBRE ? 'María Fernanda Quispe' : PACIENTE.ci;

async function entrar(email) {
  await page.context().clearCookies();
  await page.goto(`${BASE}/login`);
  await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', email);
  await page.fill('input[placeholder="Ingrese su contraseña"]', CLAVE);
}

// ─── Secciones ────────────────────────────────────────────────────────────────

async function inicio() {
  await entrar('dra.garcia@fetalmedical.bo');
  await paso({
    seccion: 'Inicio', titulo: 'Iniciar sesión como médica', cuenta: 'dra.garcia',
    clics: ['Escribe el correo de la médica', 'Escribe la contraseña de demostración', 'Clic en «Iniciar sesión»'],
    decir: 'Cada persona entra con su cuenta. Según su rol, el sistema le muestra solo lo que puede usar. '
      + 'Tras 5 contraseñas equivocadas la cuenta se bloquea 15 minutos, y se puede exigir verificación en dos pasos.',
  }, [page.locator('input[placeholder="ejemplo@fetalmedical.com"]'), page.locator('input[placeholder="Ingrese su contraseña"]'),
    page.locator('button[type=submit]')]);
  await page.click('button[type=submit]');
  await page.waitForURL((u) => !u.pathname.includes('login'));
  await page.request.get(`${API}/token/csrf/`);
  await page.waitForTimeout(2500);
  await paso({
    seccion: 'Inicio', titulo: 'Panel Principal', cuenta: 'dra.garcia',
    clics: ['Menú lateral: todos los módulos del sistema', 'Indicadores y alertas del día'],
    decir: 'Este es el panel de la médica: ve de un vistazo pacientes, controles y alertas pendientes. '
      + 'A la izquierda está el menú con todos los módulos, agrupados como trabaja la clínica.',
  }, [page.locator('.ant-layout-sider').first(), page.locator('.ant-layout-content .ant-card').first()]);
}

async function registrarPaciente() {
  await menu('Pacientes').click();
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'Abrir Pacientes y crear una nueva', cuenta: 'dra.garcia',
    clics: ['Menú «Pacientes»', 'Botón «Nueva Paciente»'],
    decir: 'Empezamos como lo haría recepción: llega una paciente nueva y la registramos.',
  }, [menu('Pacientes'), boton(/Nueva Paciente|Nuevo Paciente/)]);
  await boton(/Nueva Paciente|Nuevo Paciente/).click();
  const modal = page.locator('.ant-modal:visible');
  await modal.locator('#nombre').fill(PACIENTE.nombre);
  await modal.locator('#apellido_paterno').fill(PACIENTE.apellido_paterno);
  await modal.locator('#apellido_materno').fill(PACIENTE.apellido_materno);
  await modal.locator('#ci').fill(PACIENTE.ci);
  await modal.locator('#fecha_nacimiento').click();
  await page.keyboard.type(PACIENTE.fecha_nacimiento.replace(/\//g, ''));
  await page.keyboard.press('Tab');
  await inventario('paciente paso 1');
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'Datos personales', cuenta: 'dra.garcia',
    escribir: [['Nombres', PACIENTE.nombre], ['Apellido paterno', PACIENTE.apellido_paterno],
      ['Apellido materno', PACIENTE.apellido_materno], ['Cédula de identidad', PACIENTE.ci],
      ['Fecha de nacimiento', `${PACIENTE.fecha_nacimiento} (escribir solo los números: ${PACIENTE.fecha_nacimiento.replace(/\//g, '')})`]],
    clics: ['Llenar los datos personales', 'Clic en «Siguiente»'],
    decir: 'El nombre y la cédula se guardan cifrados en la base de datos: aunque alguien copiara la base, no podría leerlos.',
  }, [modal.locator('.ant-form').first(), modal.getByRole('button', { name: 'Siguiente' })]);
  await modal.getByRole('button', { name: 'Siguiente' }).click();
  await page.waitForTimeout(500);
  if (await modal.locator('#telefono').count()) await modal.locator('#telefono').fill(PACIENTE.telefono);
  if (await modal.locator('#ciudad').count()) await modal.locator('#ciudad').fill(PACIENTE.ciudad).catch(() => {});
  await inventario('paciente paso 2');
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'Contacto', cuenta: 'dra.garcia',
    escribir: [['Teléfono / Celular', PACIENTE.telefono], ['Ciudad', PACIENTE.ciudad]],
    clics: ['Llenar el contacto', 'Clic en «Siguiente»'],
    decir: 'Los datos de contacto sirven para recordarle sus citas.',
  }, [modal.locator('.ant-form').first(), modal.getByRole('button', { name: 'Siguiente' })]);
  await modal.getByRole('button', { name: 'Siguiente' }).click();
  await page.waitForTimeout(500);
  await inventario('paciente paso 3');
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'Consentimiento y registro', cuenta: 'dra.garcia',
    clics: ['Marcar el consentimiento de uso de datos', 'Clic en «Registrar Paciente»'],
    decir: 'Sin el consentimiento no se puede registrar: lo exige la Ley 164. Si intento registrar sin marcarlo, el sistema no me deja.',
  }, [modal.locator('input[type=checkbox]').locator('..'), modal.getByRole('button', { name: 'Registrar Paciente' })]);
  await modal.locator('input[type=checkbox]').check();
  await modal.getByRole('button', { name: 'Registrar Paciente' }).click();
  await page.locator('.ant-modal-confirm-title', { hasText: '¿Registrar ahora su embarazo?' }).waitFor();
  const pac = lista((await api('GET', `/pacientes/?search=${PACIENTE.ci}`)).datos)[0];
  ids.paciente = pac.id;
  await inventario('confirmar embarazo');
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'El sistema ofrece registrar el embarazo', cuenta: 'dra.garcia',
    clics: ['Clic en el botón para registrar el embarazo ahora'],
    decir: 'Apenas se registra, el sistema propone el paso siguiente: abrir su embarazo, ya con la paciente elegida.',
  }, [page.locator('.ant-modal-confirm .ant-btn-primary')]);
  await page.locator('.ant-modal-confirm .ant-btn-primary').click();
  await page.waitForURL(/embarazos\/nuevo/);
  await page.waitForTimeout(1500);
  await campo('fecha_ultima_menstruacion').click();
  await page.keyboard.type(FUM.replace(/\//g, ''));
  await page.keyboard.press('Tab');
  await page.waitForTimeout(800);
  await inventario('embarazo');
  await paso({
    seccion: 'Recepción: registrar a la paciente', titulo: 'Registrar el embarazo', cuenta: 'dra.garcia',
    escribir: [['Fecha de última menstruación (FUM)', `${FUM}  (hoy menos 39 semanas)`]],
    clics: ['Escribir la FUM: el sistema calcula la edad gestacional y la fecha probable de parto', 'Clic en «Crear Embarazo»'],
    decir: 'Con la fecha de última menstruación el sistema calcula solo la edad gestacional, la fecha probable de parto y el riesgo.',
    nota: 'El día de la demostración usa como FUM la fecha de hoy menos 39 semanas.',
  }, [campo('fecha_ultima_menstruacion'), boton('Crear Embarazo')]);
  await boton('Crear Embarazo').click();
  for (let i = 0; i < 20 && !ids.embarazo; i += 1) {
    await page.waitForTimeout(500);
    ids.embarazo = lista((await api('GET', `/embarazos/?paciente=${ids.paciente}`)).datos)[0]?.id;
  }
  console.log('   ids', ids);
}

async function triajeYCita() {
  await menu('Triaje').click();
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Enfermería: triaje', titulo: 'Abrir Triaje', cuenta: 'dra.garcia',
    clics: ['Menú «Triaje»', 'Botón «Nuevo Triaje»'],
    decir: 'Antes de pasar con la médica, enfermería toma los signos vitales y asigna la prioridad de atención.',
  }, [menu('Triaje'), boton('Nuevo Triaje')]);
  await boton('Nuevo Triaje').click();
  await page.waitForTimeout(2000);
  const selPaciente = page.locator('.ant-select', { has: page.locator('#paciente') }).first();
  await elegirEnSelect(selPaciente, BUSCAR);
  await page.waitForTimeout(1500);
  await inventario('triaje 1');
  await paso({
    seccion: 'Enfermería: triaje', titulo: 'Elegir a la paciente y la prioridad', cuenta: 'dra.garcia',
    escribir: [['Seleccionar paciente', `${PACIENTE.ci} (o «Quispe») y elegirla de la lista`], ['Prioridad', 'Normal']],
    clics: ['Buscar a la paciente por su CI', 'Dejar la prioridad en «Normal»', 'Clic en «Continuar»'],
    decir: 'Busco a la paciente por nombre o por cédula; el sistema trae sus datos y su embarazo.',
  }, [selPaciente, page.locator('.ant-select', { has: page.locator('#prioridad') }), boton(/Continuar/)]);
  await boton(/Continuar/).click();
  await page.waitForTimeout(800);
  const vitales = [['presion_sistolica', '118'], ['presion_diastolica', '76'], ['temperatura', '36.6'],
    ['frecuencia_cardiaca', '82'], ['frecuencia_respiratoria', '18'], ['saturacion_oxigeno', '98'],
    ['peso_kg', '70'], ['talla_cm', '158']];
  for (const [id, v] of vitales) if (await campo(id).count()) await campo(id).fill(v);
  await inventario('triaje 2');
  await paso({
    seccion: 'Enfermería: triaje', titulo: 'Signos vitales', cuenta: 'dra.garcia',
    escribir: [['P. sistólica / diastólica', '118 / 76'], ['Temperatura', '36.6'], ['F. cardíaca', '82'],
      ['F. respiratoria', '18'], ['Saturación', '98'], ['Peso / Talla', '70 kg / 158 cm']],
    clics: ['Escribir los signos vitales', 'Clic en «Continuar»'],
    decir: 'Al elegir a la paciente, el sistema ya muestra sus alertas de riesgo, por ejemplo que tiene un embarazo activo.',
  }, [page.locator('#presion_sistolica').locator('xpath=ancestor::div[contains(@class,"ant-card")][1]'), boton(/Continuar/)]);
  await boton(/Continuar/).click();
  await page.waitForTimeout(800);
  await campo('motivo_visita').fill('Control prenatal a las 39 semanas');
  await inventario('triaje 3');
  const guardar = page.getByRole('button', { name: /Guardar|Registrar|Finalizar/ }).last();
  await paso({
    seccion: 'Enfermería: triaje', titulo: 'Motivo de la visita y guardar', cuenta: 'dra.garcia',
    escribir: [['Motivo de la visita', 'Control prenatal a las 39 semanas']],
    clics: ['Escribir el motivo', 'Clic en guardar'],
    decir: 'El triaje queda en la historia clínica y la médica lo ve al atender.',
  }, [campo('motivo_visita'), guardar]);
  await guardar.click();
  await page.waitForTimeout(2500);
  await inventario('triaje guardado');
  await page.screenshot({ path: path.join(SALIDA, 'explorar_triaje_fin.png') });

  await menu('Agenda de Citas').click();
  await page.waitForTimeout(1500);
  await boton('Nueva Cita').click();
  await page.waitForTimeout(3000);
  await elegirEnSelect(page.locator('.ant-select', { has: page.locator('#paciente') }).first(), BUSCAR);
  await page.waitForTimeout(600);
  await page.locator('.ant-select', { has: page.locator('#medico') }).first().click();
  await page.waitForTimeout(600);
  await page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option', { hasText: 'García' }).first().click();
  await inventario('cita 1');
  await paso({
    seccion: 'Recepción: agendar la cita', titulo: 'Paciente, médico y tipo de cita', cuenta: 'dra.garcia',
    escribir: [['Paciente', PACIENTE.ci], ['Médico', 'María Elena García Soliz'], ['Tipo de cita', 'Control']],
    clics: ['Menú «Agenda de Citas» → «Nueva Cita»', 'Elegir paciente y médico', 'Clic en «Siguiente»'],
    decir: 'Recepción agenda el próximo control. Recepción solo ve citas y el listado de pacientes, nunca datos clínicos.',
  }, [menu('Agenda de Citas'), page.locator('.ant-form').first(), boton('Siguiente')]);
  await boton('Siguiente').click();
  await page.waitForTimeout(1500);
  await inventario('cita 2');
  await page.screenshot({ path: path.join(SALIDA, 'explorar_cita2.png'), fullPage: true });
}

// ─── Archivos que usa el guion (se dejan en la carpeta de muestras) ───────────
const IA_DIR = path.join(BACKEND, 'Microservicio_IA');
const ARCHIVOS = path.join(MUESTRAS, '00_archivos_del_guion');
const CABEZA = { origen: path.join(IA_DIR, 'entrenamiento', 'redes_ecografia_real', 'imagenes', 'hc18', '973_HC.png'),
  archivo: path.join(ARCHIVOS, 'ecografia_cabeza_tercer_trimestre.png'), px: '0.240927', referencia: '328,0 mm' };
const INTRAPARTO = path.join(ARCHIVOS, 'ecografia_intraparto.png');
const LABORATORIO = path.join(ARCHIVOS, 'laboratorio_maria_quispe.csv');
const ANOMALIA = path.join(MUESTRAS, '08_anomalias_cerebrales', 'anomalia_ventriculomegalia_hidrocefalia.jpg');
const FEMUR = path.join(MUESTRAS, '06_puntos_femur', 'femur_1.png');
const TERATOMA = path.join(MUESTRAS, '10_lesion_ovarica', 'ovario_teratoma.jpg');
const CTG = path.join(MUESTRAS, '13_cardiotocografia', 'ctg_patológica.txt');

function prepararArchivos() {
  fs.mkdirSync(ARCHIVOS, { recursive: true });
  fs.copyFileSync(CABEZA.origen, CABEZA.archivo);
  const dirIugc = path.join(IA_DIR, 'datos', 'extraidos', 'intraparto', 'imagenes');
  const iugc = fs.readdirSync(dirIugc).find((f) => /^\d{8}T\d{6}I\d+_\d+_\d+\.png$/.test(f));
  fs.copyFileSync(path.join(dirIugc, iugc), INTRAPARTO);
  const ayer = fecha(1);
  fs.writeFileSync(LABORATORIO, `Cédula;Código de examen;Fecha;Analito;Resultado\n${PACIENTE.ci};HEM001;${ayer};Hemoglobina;10,8\n`
    + `${PACIENTE.ci};HEM001;${ayer};Plaquetas;215000\n`, 'latin1');
  for (const f of [ANOMALIA, FEMUR, TERATOMA, CTG]) if (!fs.existsSync(f)) throw new Error(`Falta ${f}: corra antes scripts/muestras_ia.py`);
}
const enCarpeta = (f) => `${path.basename(path.dirname(f))}\\${path.basename(f)}`;

/** Próximo día hábil a una semana de hoy: [dd/mm/aaaa, aaaa-mm-dd]. */
function proximaCita() {
  const d = new Date(Date.now() + 7 * 864e5);
  while ([0, 6].includes(d.getDay())) d.setDate(d.getDate() + 1);
  const [dd, mm, aa] = [String(d.getDate()).padStart(2, '0'), String(d.getMonth() + 1).padStart(2, '0'), d.getFullYear()];
  return [`${dd}/${mm}/${aa}`, `${aa}-${mm}-${dd}`];
}

async function citaResto() {
  const [dia, iso] = proximaCita();
  await campo('fecha_cita').click();
  const celda = page.locator(`.ant-picker-dropdown:visible td[title="${iso}"]`);
  if (!(await celda.count())) await page.locator('.ant-picker-dropdown:visible .ant-picker-header-next-btn').click();
  await celda.click();
  await page.waitForTimeout(2000);
  const libre = page.locator('.citas-page__horario-libre').first();
  if (await libre.count()) {
    await libre.click();
  } else {
    await campo('hora_cita').click();
    const panel = page.locator('.ant-picker-dropdown:visible');
    await panel.locator('.ant-picker-time-panel-column').nth(0).locator('.ant-picker-time-panel-cell', { hasText: /^10$/ }).click();
    await panel.locator('.ant-picker-time-panel-column').nth(1).locator('.ant-picker-time-panel-cell', { hasText: /^00$/ }).click();
    if (await panel.locator('.ant-picker-ok button').count()) await panel.locator('.ant-picker-ok button').click();
  }
  await page.waitForTimeout(500);
  await paso({
    seccion: 'Recepción: agendar la cita', titulo: 'Fecha y hora', cuenta: 'dra.garcia',
    escribir: [['Fecha de la cita', `${dia} (un día hábil de la próxima semana)`], ['Hora de la cita', 'un horario libre de la lista']],
    clics: ['Elegir la fecha', 'Elegir un horario disponible', 'Clic en «Siguiente»'],
    decir: 'Si la médica tiene horarios configurados, el sistema muestra los libres y no deja agendar dos citas a la misma hora.',
  }, [campo('fecha_cita'), campo('hora_cita'), boton('Siguiente')]);
  await boton('Siguiente').click();
  await page.waitForTimeout(1500);
  await inventario('cita 3');
  await page.screenshot({ path: path.join(SALIDA, 'explorar_cita3.png'), fullPage: true });
  const motivo = page.locator('textarea').first();
  if (await motivo.count()) await motivo.fill('Control prenatal de la semana 40');
  const guardar = page.getByRole('button', { name: /Guardar|Crear|Agendar|Confirmar/ }).last();
  await paso({
    seccion: 'Recepción: agendar la cita', titulo: 'Detalles y guardar la cita', cuenta: 'dra.garcia',
    escribir: [['Motivo', 'Control prenatal de la semana 40']],
    clics: ['Escribir el motivo', 'Clic en guardar'],
    decir: 'La cita queda en la agenda de la médica y en la historia de la paciente.',
  }, [motivo, guardar]);
  await guardar.click();
  await page.waitForTimeout(2500);
  await inventario('cita guardada');
}

async function abrirHistoria(titulo, decir) {
  await menu('Pacientes').click();
  await page.waitForTimeout(1500);
  const buscar = page.getByPlaceholder(/Buscar/).first();
  await buscar.fill(PACIENTE.ci);
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2000);
  const fila = page.locator('.ant-table-row', { hasText: PACIENTE.ci }).first();
  const carpeta = fila.locator('td').last().locator('button').first();
  await paso({
    seccion: 'Médica: embarazo y control', titulo, cuenta: 'dra.garcia',
    escribir: [['Buscador de pacientes', PACIENTE.ci]],
    clics: ['Menú «Pacientes» y escribir el CI en el buscador', 'Clic en el botón de la carpeta: abre la historia clínica'],
    decir,
  }, [buscar, carpeta]);
  await carpeta.click();
  await boton('Nuevo Control').waitFor();
  await page.waitForTimeout(2000);
}

async function control() {
  await abrirHistoria('Buscar a la paciente y abrir su historia clínica',
    'La médica busca a la paciente y abre su historia: aquí ve todo lo que se registró de ella, incluido el triaje.');
  await inventario('historia');
  await paso({
    seccion: 'Médica: embarazo y control', titulo: 'Historia clínica: nuevo control prenatal', cuenta: 'dra.garcia',
    clics: ['Clic en «Nuevo Control»'],
    decir: 'La historia clínica reúne en una sola vista antecedentes, embarazos, controles, ecografías, laboratorio y partos.',
  }, [boton('Nuevo Control')]);
  await boton('Nuevo Control').click();
  await page.waitForTimeout(2500);
  for (const [id, v] of [['peso_actual', '70'], ['presion_arterial_sistolica', '150'], ['presion_arterial_diastolica', '100'],
    ['altura_uterina', '33'], ['frecuencia_cardiaca_fetal', '140']]) await campo(id).fill(v);
  // A partir de la semana 20 todos los campos obstétricos son obligatorios.
  const elegidos = {};
  for (const id of ['presentacion_fetal', 'movimientos_fetales', 'edema', 'proteinuria']) {
    if (!(await campo(id).count())) continue;
    await page.locator('.ant-select', { has: page.locator(`#${id}`) }).first().click();
    const opcion = page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option').first();
    elegidos[id] = (await opcion.innerText()).trim();
    await opcion.click();
    await page.waitForTimeout(300);
  }
  await inventario('control');
  await paso({
    seccion: 'Médica: embarazo y control', titulo: 'Registrar el control prenatal', cuenta: 'dra.garcia',
    escribir: [['Semanas de gestación', '39 (lo calcula solo)'], ['Peso actual', '70'], ['PA sistólica / diastólica', '150 / 100'],
      ['Altura uterina', '33 (a propósito, baja)'], ['FCF', '140'], ['Presentación', elegidos.presentacion_fetal],
      ['Movimientos fetales', elegidos.movimientos_fetales], ['Edema', elegidos.edema], ['Proteinuria', elegidos.proteinuria]],
    clics: ['La paciente y el embarazo ya vienen elegidos; la edad gestacional se calcula sola',
      'Escribir los datos del control (altura uterina 33 a propósito)', 'Clic en «Guardar Control»'],
    decir: 'Escribo una altura uterina de 33 centímetros a propósito: es demasiado baja para 39 semanas. Veamos si el sistema lo deja pasar.',
  }, [campo('edad_gestacional_semanas'), campo('altura_uterina'), boton(/Guardar Control/)]);
  await boton(/Guardar Control/).click();
  await page.waitForTimeout(2500);
  const aviso = page.locator('.ant-modal-confirm:visible .ant-modal-confirm-body').first();
  await paso({
    seccion: 'Médica: embarazo y control', titulo: 'El sistema rechaza un dato clínicamente imposible', cuenta: 'dra.garcia',
    clics: ['Mensaje: altura uterina muy baja para 39 semanas (esperado 37 a 41 cm)'],
    decir: 'El sistema no guarda un dato que no tiene sentido clínico y explica por qué: a las 39 semanas se espera entre 37 y 41 cm.',
  }, [aviso]);
  const aceptar = page.getByRole('button', { name: 'Aceptar' });
  for (let i = 0; i < 4 && (await aceptar.count()); i += 1) {
    await aceptar.last().click({ force: true });
    await page.waitForTimeout(500);
  }
  await campo('altura_uterina').fill('38');
  await paso({
    seccion: 'Médica: embarazo y control', titulo: 'Corregir y guardar', cuenta: 'dra.garcia',
    escribir: [['Altura uterina', '38']],
    clics: ['Corregir la altura uterina a 38', 'Clic en «Guardar Control»'],
    decir: 'Corrijo la altura uterina. La presión sigue en 150/100, que en una embarazada a término es sospecha de preeclampsia.',
  }, [campo('altura_uterina'), boton(/Guardar Control/)]);
  await boton(/Guardar Control/).click();
  await page.waitForTimeout(3000);
  await inventario('control guardado');
  const guardado = lista((await api('GET', `/controles/?embarazo=${ids.embarazo}`)).datos).length;
  console.log(`   controles guardados: ${guardado}`);
  await paso({
    seccion: 'Médica: embarazo y control', titulo: 'Control guardado y alerta de hipertensión', cuenta: 'dra.garcia',
    clics: ['El control aparece en la lista con la presión en rojo y una alerta'],
    decir: 'El control se guardó: la presión 150/100 sale en rojo y el control queda marcado con la alerta de hipertensión, riesgo de preeclampsia. Arriba se ve cuántos controles de la clínica tienen alertas.',
  }, [page.locator('.ant-table-row', { hasText: 'Quispe Mamani' }).first()]);
}

async function ecografia() {
  await page.goto(`${BASE}/dashboard/historia-clinica/${ids.paciente}`);
  await page.waitForTimeout(2500);
  await inventario('historia para ecografía');
  await page.goto(`${BASE}/dashboard/ecografias/nuevo?embarazo=${ids.embarazo}`);
  await page.waitForTimeout(2500);
  await campo('frecuencia_cardiaca_fetal').fill('140');
  await inventario('ecografía 1');
  await paso({
    seccion: 'Médica: ecografía con IA', titulo: 'Nueva ecografía', cuenta: 'dra.garcia',
    escribir: [['FCF', '140']],
    clics: ['El embarazo y el tipo (tercer trimestre) ya vienen elegidos', 'Escribir la FCF', 'Pestaña «Imágenes y Conclusiones»'],
    decir: 'Registro la ecografía de hoy. El sistema ya sabe de qué paciente y de qué embarazo es.',
  }, [page.locator('.ant-form-item', { has: page.locator('#embarazo') }).first(), campo('frecuencia_cardiaca_fetal'),
    page.getByRole('tab', { name: /Imágenes y Conclusiones/ })]);
  await page.getByRole('tab', { name: /Imágenes y Conclusiones/ }).click();
  await page.locator('input[type=file]').last().setInputFiles(CABEZA.archivo);
  await campo('diagnostico').fill('Feto único vivo, cefálico. Biometría para valorar con IA.');
  await page.waitForTimeout(1000);
  await paso({
    seccion: 'Médica: ecografía con IA', titulo: 'Subir la imagen y guardar', cuenta: 'dra.garcia',
    escribir: [['Imagen', enCarpeta(CABEZA.archivo)], ['Diagnóstico', 'Feto único vivo, cefálico.']],
    clics: ['Subir la imagen de la ecografía', 'Escribir el diagnóstico', 'Clic en «Guardar Ecografía»'],
    decir: 'Adjunto la imagen del ecógrafo. Queda guardada en la historia y lista para analizarla con las redes.',
  }, [page.locator('.ant-upload').last(), campo('diagnostico'), boton(/Guardar Ecografía/)]);
  await boton(/Guardar Ecografía/).click();
  for (let i = 0; i < 30 && !ids.ecografia; i += 1) {
    await page.waitForTimeout(500);
    ids.ecografia = lista((await api('GET', `/ecografias/?embarazo=${ids.embarazo}`)).datos)[0]?.id;
  }
  await page.waitForTimeout(2000);
  await page.goto(`${BASE}/dashboard/ecografias/${ids.ecografia}`);
  await page.waitForTimeout(2500);
  await page.getByRole('tab', { name: /IA medida/ }).click();
  await campo('tamano-pixel').fill(CABEZA.px);
  await paso({
    seccion: 'Médica: ecografía con IA', titulo: 'Analizar la ecografía con las redes', cuenta: 'dra.garcia',
    escribir: [['Tamaño de píxel (mm)', CABEZA.px]],
    clics: ['En la ficha de la ecografía, pestaña «IA medida»', 'Escribir el tamaño de píxel', 'Clic en «Analizar»'],
    decir: 'El tamaño de píxel lo da el ecógrafo: sin él la red mide en píxeles, con él pasa a milímetros.',
  }, [page.getByRole('tab', { name: /IA medida/ }), campo('tamano-pixel'), boton('Analizar', true)]);
  await boton('Analizar', true).click();
  await page.getByText('La imagen muestra').waitFor({ timeout: 60000 });
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Médica: ecografía con IA', titulo: 'Resultado: plano, cribado y circunferencia cefálica', cuenta: 'dra.garcia',
    clics: ['Plano reconocido por la primera red', 'Cribado de anomalías cerebrales', 'Circunferencia cefálica y edad gestacional'],
    decir: 'Tres redes trabajaron en cadena: una reconoce que es un corte de cerebro, otra hace el cribado de anomalías '
      + `y otra mide la circunferencia cefálica (el ecografista midió ${CABEZA.referencia}). Cada número trae su margen de error.`,
  }, [page.getByText('La imagen muestra').first(), page.getByText('Cribado de anomalías cerebrales').first(),
    page.getByText('Edad gestacional', { exact: true }).first()]);
}

async function moduloIA() {
  const activo = page.locator('.ant-tabs-tabpane-active');
  const analizar = () => activo.getByRole('button', { name: 'Analizar', exact: true }).first();
  await menu('Análisis CNN (IA)').click();
  await page.waitForTimeout(2500);
  await inventario('módulo IA');
  await activo.locator('input[type=file]').first().setInputFiles(ANOMALIA);
  await activo.locator('#tamano-pixel').fill('');
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Cribado de anomalías cerebrales', cuenta: 'dra.garcia',
    escribir: [['Imagen', enCarpeta(ANOMALIA)]],
    clics: ['Menú «Análisis CNN (IA)», pestaña Ecografía: subir la imagen', 'Clic en «Analizar»'],
    decir: 'Ahora una ecografía real con ventriculomegalia. La red de cribado debe levantar la alarma.',
  }, [activo.locator('.ant-upload').first(), analizar()]);
  await analizar().click();
  const tarjeta = page.locator('.ant-card').filter({ hasText: 'Cribado de anomalías cerebrales' }).last();
  await tarjeta.getByText('P(anomalía)').first().waitFor({ timeout: 60000 });
  await page.waitForTimeout(1000);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'La red levanta la alarma', cuenta: 'dra.garcia',
    clics: ['Alarma y familia de anomalía sospechada'],
    decir: 'Alarma con 98 % de probabilidad y sospecha de ventriculomegalia. Es cribado: toda alarma la confirma un especialista.',
  }, [tarjeta]);

  await activo.locator('input[type=file]').first().setInputFiles(FEMUR);
  const pxFemur = fs.readFileSync(path.join(path.dirname(FEMUR), 'RESULTADO.txt'), 'utf8')
    .match(/femur_1\.png[\s\S]*?tamaño de píxel ([\d.]+)/)[1];
  await activo.locator('#tamano-pixel').fill(pxFemur);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Informe completo: longitud del fémur', cuenta: 'dra.garcia',
    escribir: [['Imagen', enCarpeta(FEMUR)], ['Tamaño de píxel', pxFemur]],
    clics: ['Subir la imagen del fémur', 'Escribir el tamaño de píxel', 'Clic en «Informe completo»'],
    decir: 'Esta red no pinta: ubica los dos extremos del fémur y mide la distancia. Error medido de 1,3 mm.',
  }, [activo.locator('.ant-upload').first(), activo.locator('#tamano-pixel'), boton(/Informe completo/)]);
  await boton(/Informe completo/).click();
  const modal = page.getByRole('dialog', { name: /Análisis de la ecografía con redes medidas/ });
  await modal.waitFor({ timeout: 60000 });
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Informe con la imagen dibujada', cuenta: 'dra.garcia',
    clics: ['Medidas con su margen de error', 'Imagen con los puntos que puso la red'],
    decir: 'El informe muestra la medida, su margen y la imagen con lo que dibujó la red, para que la médica lo verifique con sus ojos.',
  }, [modal.getByText('Longitud del fémur').first(), modal.locator('img').first()]);
  await modal.getByRole('button', { name: 'Cerrar', exact: true }).click();

  await page.getByRole('tab', { name: /ginecol/i }).click();
  await page.waitForTimeout(1000);
  await page.getByRole('radio', { name: 'Masa ovárica' }).check();
  await activo.locator('input[type=file]').first().setInputFiles(TERATOMA);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Ginecología: masa ovárica', cuenta: 'dra.garcia',
    escribir: [['Imagen', enCarpeta(TERATOMA)]],
    clics: ['Pestaña «Ecografía ginecológica»', 'Elegir «Masa ovárica»', 'Subir la imagen y clic en «Analizar»'],
    decir: 'En ginecología, una U-Net pinta la lesión y dos clasificadores votan el tipo y la alarma de malignidad.',
  }, [page.getByRole('tab', { name: /ginecol/i }), page.getByRole('radio', { name: 'Masa ovárica' }).locator('..'),
    analizar()]);
  await analizar().click();
  await page.getByText('Tipo probable').first().waitFor({ timeout: 60000 });
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Tipo probable y alarma de malignidad', cuenta: 'dra.garcia',
    clics: ['Tipo probable (teratoma)', 'Lesión dibujada por la U-Net'],
    decir: 'Acierta el teratoma. El sistema avisa que es orientativo: detecta 7 de 13 carcinomas, así que no sirve como tamizaje de cáncer.',
  }, [page.getByText('Tipo probable').first(), page.getByAltText('Ecografía con la lesión dibujada')]);

  await page.getByRole('tab', { name: /Cardiotocograf/ }).click();
  await page.getByText('Fiabilidad medida del modelo').first().waitFor();
  const { variables } = (await api('GET', '/ia/cardiotocografia/')).datos;
  const valores = fs.readFileSync(CTG, 'utf8').split(/\r?\n/).filter((l) => l.includes(' = ')).map((l) => l.split(' = ')[1]);
  for (let i = 0; i < variables.length; i += 1) await campo(variables[i].clave).fill(valores[i]);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Cardiotocografía: aprendizaje supervisado', cuenta: 'dra.garcia',
    escribir: [['Las 21 variables', `copiar de ${enCarpeta(CTG)}`]],
    clics: ['Pestaña «Cardiotocografía»', 'Escribir las 21 variables del monitoreo', 'Clic en «Clasificar»'],
    decir: 'Este modelo no es una red neuronal: es gradient boosting, aprendizaje supervisado sobre una tabla de 21 variables '
      + 'del monitoreo fetal. Acierta el 96 % en registros que no vio.',
  }, [page.getByRole('tab', { name: /Cardiotocograf/ }), campo(variables[0].clave), boton('Clasificar')]);
  await boton('Clasificar').click();
  await page.locator('.ia-ctg-clase').waitFor({ timeout: 30000 });
  await page.waitForTimeout(1000);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Resultado: patológica', cuenta: 'dra.garcia',
    clics: ['Clase y probabilidades'],
    decir: 'Patológica: coincide con el consenso de los tres obstetras que etiquetaron este registro.',
  }, [page.locator('.ia-ctg-clase')]);

  await menu('Guía de IA').click();
  await page.waitForTimeout(2500);
  await paso({
    seccion: 'Análisis CNN (IA)', titulo: 'Guía de IA', cuenta: 'dra.garcia',
    clics: ['Menú «Guía de IA»', 'Cómo funcionan las redes, explicado para el personal'],
    decir: 'La guía explica cada modelo al personal: qué hace, cuánto acierta en pacientes que no vio y cuándo no confiar en él. '
      + 'Abajo están los modelos que probamos y descartamos, con el motivo.',
  }, [menu('Guía de IA'), page.getByRole('heading', { name: 'Cómo funcionan' })]);
}

async function laboratorio() {
  await menu('Laboratorio').click();
  await page.waitForTimeout(2000);
  await paso({
    seccion: 'Laboratorio', titulo: 'Importar resultados del laboratorio', cuenta: 'dra.garcia',
    clics: ['Menú «Laboratorio»', 'Clic en «Importar Excel o CSV»'],
    decir: 'Los resultados llegan del laboratorio en Excel o CSV; el sistema reconoce las columnas aunque tengan otros nombres.',
  }, [menu('Laboratorio'), boton(/Importar Excel o CSV/)]);
  await boton(/Importar Excel o CSV/).click();
  const modal = page.locator('.ant-modal:visible');
  await modal.locator('input[type=file]').setInputFiles(LABORATORIO);
  await paso({
    seccion: 'Laboratorio', titulo: 'Elegir el archivo y revisarlo', cuenta: 'dra.garcia',
    escribir: [['Archivo', enCarpeta(LABORATORIO)]],
    clics: ['Subir el archivo', 'Clic en «Revisar archivo»'],
    decir: 'Antes de guardar, el sistema revisa cada fila: a qué paciente pertenece y si el valor tiene sentido.',
  }, [modal.locator('.ant-upload').first(), boton('Revisar archivo')]);
  await boton('Revisar archivo').click();
  await modal.getByText('Lista para importar').first().waitFor();
  await paso({
    seccion: 'Laboratorio', titulo: 'Guardar los resultados', cuenta: 'dra.garcia',
    clics: ['Filas reconocidas', 'Clic en «Guardar 2 resultados»'],
    decir: 'Reconoció a la paciente por su cédula y comparó cada valor con su rango de referencia antes de guardarlo.',
  }, [modal.locator('.ant-table').first(), boton(/Guardar 2 resultados/)]);
  await boton(/Guardar 2 resultados/).click();
  await modal.getByText(/Se guardaron 2 resultados/).waitFor();
  await boton('Terminar').click();
}

const elegirOpcion = async (id, texto) => {
  await page.keyboard.press('Escape');
  await page.locator('.ant-select', { has: page.locator(`#${id}`) }).first().click();
  await page.waitForTimeout(400);
  const opciones = page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option');
  await (texto ? opciones.filter({ hasText: texto }) : opciones).first().click();
};

async function parto() {
  await menu('Partos').click();
  await page.waitForTimeout(2000);
  await inventario('partos lista');
  const nuevo = page.getByRole('button', { name: /Nuevo Parto|Registrar Parto|Nuevo Registro|Nuevo/ }).first();
  await paso({
    seccion: 'Parto', titulo: 'Registrar el parto', cuenta: 'dra.garcia',
    clics: ['Menú «Partos»', 'Botón para registrar un parto nuevo'],
    decir: 'Llega el momento del parto. Lo registramos para la misma paciente.',
  }, [menu('Partos'), nuevo]);
  await nuevo.click();
  await page.waitForTimeout(2500);
  const selEmbarazo = page.locator('.ant-form-item').filter({ has: page.locator('label', { hasText: /^Embarazo/ }) }).first();
  await selEmbarazo.locator('.ant-select').click();
  await page.keyboard.type(PACIENTE.ci, { delay: 30 });
  await page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option', { hasText: 'Quispe' })
    .first().click({ timeout: 15000 });
  await page.waitForTimeout(2000);
  await inventario('parto tras elegir embarazo');
  const tipoEvento = page.locator('.ant-form-item').filter({ has: page.locator('label', { hasText: /Tipo de Evento/ }) }).first();
  if (!(await tipoEvento.innerText()).includes('PARTO')) {
    await tipoEvento.locator('.ant-select').click();
    await page.locator('.ant-select-dropdown:visible').last().locator('.ant-select-item-option', { hasText: 'PARTO' }).first().click();
    await page.waitForTimeout(1500);
  }
  await campo('fecha_parto').click();
  const calendario = page.locator('.ant-picker-dropdown:visible').last();
  await calendario.locator('.ant-picker-now-btn, .ant-picker-today-btn').first().click();
  const okFecha = calendario.locator('.ant-picker-ok button');
  if ((await okFecha.count()) && (await okFecha.isEnabled())) await okFecha.click();
  await page.waitForTimeout(800);
  await elegirOpcion('presentacion_fetal', 'Cefálica');
  await paso({
    seccion: 'Parto', titulo: 'Embarazo, tipo y fecha del parto', cuenta: 'dra.garcia',
    escribir: [['Embarazo', 'escribir 8899001 y elegir el de María Fernanda'], ['Tipo de evento', 'PARTO (≥ 20 semanas)'], ['Tipo de parto', 'Vaginal espontáneo'],
      ['Fecha del parto', 'abrir el calendario y pulsar «Ahora»'], ['Semanas', '39 (lo calcula solo)'], ['Presentación fetal', 'Cefálica']],
    clics: ['Elegir el embarazo de María Fernanda', 'Fecha del parto: hoy', 'Las semanas se calculan solas'],
    decir: 'Elijo el embarazo y el sistema calcula las semanas de gestación al momento del parto.',
  }, [selEmbarazo, campo('fecha_parto'), campo('semanas_gestacion')]);
  await elegirOpcion('sexo_bebe', 'Femenino');
  await campo('peso_bebe').fill('3200');
  await campo('talla_bebe').fill('50');
  await campo('apgar_1min').fill('8');
  await campo('apgar_5min').fill('9');
  await paso({
    seccion: 'Parto', titulo: 'Datos del recién nacido y guardar', cuenta: 'dra.garcia',
    escribir: [['Sexo', 'Femenino'], ['Peso', '3200 g'], ['Talla', '50 cm'], ['Apgar 1 min / 5 min', '8 / 9']],
    clics: ['Datos de la recién nacida', 'Clic en «Guardar»'],
    decir: 'Registro a la recién nacida: peso, talla y Apgar. Si se tratara de gemelos, se agrega otro recién nacido aquí mismo.',
    nota: 'No escribas un peso menor de 400 g (fallo conocido BUG-009/010).',
  }, [page.locator('.ant-form-item', { has: page.locator('#sexo_bebe') }).locator('xpath=ancestor::div[contains(@class,"ant-row")][1]'),
    page.getByRole('button', { name: 'Guardar' }).last()]);
  await page.getByRole('button', { name: 'Guardar' }).last().click();
  for (let i = 0; i < 30 && !ids.parto; i += 1) {
    await page.waitForTimeout(500);
    ids.parto = lista((await api('GET', `/partos/?paciente=${ids.paciente}`)).datos)[0]?.id;
  }
  await page.waitForTimeout(2000);
  await inventario('parto guardado');

  await page.goto(`${BASE}/dashboard/partos/${ids.parto}?pestana=trabajo-parto`);
  await page.waitForTimeout(2500);
  await paso({
    seccion: 'Parto', titulo: 'Partograma: registrar un tacto', cuenta: 'dra.garcia',
    clics: ['En la ficha del parto, pestaña «Trabajo de parto»', 'Clic en «Registrar tacto»'],
    decir: 'Durante el trabajo de parto se registran los tactos en el partograma, y aquí entra otra red neuronal.',
  }, [page.getByRole('tab', { name: 'Trabajo de parto' }), boton('Registrar tacto')]);
  await boton('Registrar tacto').click();
  const modal = page.locator('.ant-modal:visible');
  await modal.locator('#dilatacion_cervical').fill('6');
  await modal.locator('#fcf_baseline').fill('142');
  await modal.locator('input[type=file]').setInputFiles(INTRAPARTO);
  await modal.getByText('(red entrenada con IUGC 2024)').first().waitFor({ timeout: 60000 });
  await page.waitForTimeout(1500);
  await paso({
    seccion: 'Parto', titulo: 'La red mide el ángulo de progresión', cuenta: 'dra.garcia',
    escribir: [['Dilatación', '6 cm'], ['FCF basal', '142'], ['Ecografía intraparto', enCarpeta(INTRAPARTO)]],
    clics: ['Dilatación y FCF', 'Subir la ecografía intraparto: la red llena el ángulo de progresión', 'Clic en «Guardar»'],
    decir: 'La U-Net encuentra la sínfisis del pubis y la cabeza fetal y mide el ángulo de progresión: cuanto mayor, '
      + 'más descendida está la cabeza. Error medido: 6,7 grados.',
  }, [modal.locator('#dilatacion_cervical'), modal.locator('#angulo_progresion').locator('xpath=ancestor::div[contains(@class,"ant-form-item")][1]'),
    modal.getByRole('button', { name: 'Guardar' })]);
  await modal.getByRole('button', { name: 'Guardar' }).click();
  await page.locator('.ant-table-row').first().waitFor();
  await page.waitForTimeout(1000);

  await page.getByRole('tab', { name: /Recién nacido/ }).click();
  await boton('Registrar Capurro / Ballard').click();
  const mc = page.locator('.ant-modal:visible');
  const selects = mc.locator('.ant-select');
  for (const [i, texto] of ['Gruesa, grietas superficiales', 'Pabellón totalmente incurvado', 'Entre 5 y 10 mm',
    'areola punteada, borde no levantado', 'Surcos en la mitad anterior'].entries()) {
    await selects.nth(i).click();
    await page.locator('.ant-select-dropdown:visible .ant-select-item-option', { hasText: texto }).first().click();
  }
  await paso({
    seccion: 'Parto', titulo: 'Recién nacido: edad gestacional por Capurro', cuenta: 'dra.garcia',
    escribir: [['Piel', 'Gruesa, grietas superficiales'], ['Oreja', 'Pabellón totalmente incurvado'],
      ['Glándula mamaria', 'Entre 5 y 10 mm'], ['Pezón', 'areola punteada, borde no levantado'], ['Pliegues plantares', 'Surcos en la mitad anterior']],
    clics: ['Pestaña «Recién nacido» → «Registrar Capurro / Ballard»: elegir los cinco signos', 'Ver el resultado y «Guardar»'],
    decir: 'El método de Capurro estima la edad gestacional de la recién nacida por cinco signos físicos: 39,7 semanas, a término.',
  }, [selects.first(), mc.getByRole('button', { name: 'Guardar' })]);
  await mc.getByRole('button', { name: 'Guardar' }).click();
  await page.waitForTimeout(1500);

  await page.getByRole('tab', { name: 'Epicrisis' }).click();
  await boton('Redactar epicrisis').click();
  await page.waitForTimeout(1000);
  await campo('cie10_ingreso').fill('o80');
  await campo('matricula_profesional').fill('MP-4521');
  await paso({
    seccion: 'Parto', titulo: 'Epicrisis: el resumen de alta', cuenta: 'dra.garcia',
    escribir: [['CIE-10 de ingreso', 'O80'], ['Matrícula profesional', 'MP-4521']],
    clics: ['Pestaña «Epicrisis» → «Redactar epicrisis»: el resumen viene redactado con los datos del parto',
      'Código CIE-10 y matrícula', 'Clic en «Guardar borrador»'],
    decir: 'La epicrisis se redacta sola con los datos registrados; la médica la revisa, la guarda y la firma.',
  }, [campo('resumen_clinico'), campo('cie10_ingreso'), boton('Guardar borrador')]);
  await boton('Guardar borrador').click();
  await page.locator('.ant-tabs-tabpane-active').getByText('Borrador').first().waitFor();
  await paso({
    seccion: 'Parto', titulo: 'Firmar la epicrisis', cuenta: 'dra.garcia',
    clics: ['Clic en «Firmar» y confirmar'],
    decir: 'Una vez firmada ya no se puede editar: queda como documento legal de la historia clínica.',
  }, [boton('Firmar')]);
  await boton('Firmar').click();
  await page.locator('.ant-modal-confirm .ant-btn-primary').click();
  await page.locator('.ant-tabs-tabpane-active').getByText('Firmada por').first().waitFor();
}

async function cierreYRoles() {
  await page.goto(`${BASE}/dashboard/historia-clinica/${ids.paciente}`);
  await page.waitForTimeout(3000);
  await paso({
    seccion: 'Seguimiento', titulo: 'La historia clínica completa', cuenta: 'dra.garcia',
    clics: ['Pacientes → buscar 8899001 → carpeta: la historia ya tiene todo lo de hoy'],
    decir: 'Cierro el ciclo: en la historia de María Fernanda está todo lo que hicimos hoy, el triaje, el embarazo, el control, '
      + 'la ecografía con IA, el laboratorio y el parto, en orden y sin escribir nada dos veces.',
  }, [page.getByText('Completitud de la historia clínica').locator('xpath=ancestor::div[contains(@class,"ant-card")][1]')]);
  await menu('Calculadoras').click();
  await page.waitForTimeout(600);
  await menu('Calculadoras rápidas').click();
  await page.waitForTimeout(2500);
  await inventario('calculadoras');
  await paso({
    seccion: 'Seguimiento', titulo: 'Calculadoras clínicas', cuenta: 'dra.garcia',
    clics: ['Menú «Calculadoras» → «Calculadoras rápidas»'],
    decir: 'Las calculadoras obstétricas de uso diario: edad gestacional, fecha probable de parto, IMC, Bishop y más.',
    nota: 'Si muestras una: IMC con 23 o 27 y Bishop con 3 u 8 (BUG-005 y BUG-006 con 25, 30 y 5).',
  }, [menu('Calculadoras rápidas')]);
  await menu('Centro de reportes').click();
  await page.waitForTimeout(2500);
  await inventario('reportes');
  await paso({
    seccion: 'Seguimiento', titulo: 'Centro de reportes', cuenta: 'dra.garcia',
    clics: ['Menú «Centro de reportes»'],
    decir: 'Los reportes salen en PDF o Excel: estadísticas de la clínica, controles, partos e indicadores.',
  }, [menu('Centro de reportes')]);

  await entrar('enf.mamani@fetalmedical.bo');
  await page.click('button[type=submit]');
  await page.waitForURL((u) => !u.pathname.includes('login'));
  await page.waitForTimeout(2500);
  await paso({
    seccion: 'Roles y seguridad', titulo: 'La enfermera ve menos módulos', cuenta: 'enf.mamani',
    clics: ['Cerrar sesión y entrar como enfermera (arriba: su nombre y su rol)', 'Menú más corto: no tiene Partos ni Reportes'],
    decir: 'Mínimo privilegio: enfermería hace triaje, controles y vacunas, pero no puede abrir partos ni reportes.',
  }, [page.getByText('Rosa Mamani Condori').first(), menu('Triaje')]);

  await entrar('admin.demo@fetalmedical.bo');
  await page.click('button[type=submit]');
  await page.waitForURL((u) => !u.pathname.includes('login'));
  await page.waitForTimeout(2500);
  for (const [item, titulo, decir] of [
    ['Cargos y permisos', 'Cargos y permisos', 'El administrador crea cargos (obstetriz, nutricionista…) sobre un rol y elige qué módulos usa cada uno.'],
    ['Gestión de Usuarios', 'Gestión de usuarios', 'Aquí se crean las cuentas del personal, se bloquean y se exige la verificación en dos pasos.'],
    ['Logs de Acceso', 'Registro de accesos', 'Todo queda registrado: quién entró, cuándo y desde dónde. Lo que hicimos en esta demostración ya está aquí.'],
  ]) {
    await menu(item).click();
    await page.waitForTimeout(2500);
    await paso({ seccion: 'Roles y seguridad', titulo, cuenta: 'admin.demo', clics: [`Menú «${item}»`], decir }, [menu(item)]);
  }
}

(async () => {
  if (!CLAVE) throw new Error('Falta E2E_PASSWORD');
  fs.mkdirSync(CAPTURAS, { recursive: true });
  for (const f of fs.readdirSync(CAPTURAS)) fs.unlinkSync(path.join(CAPTURAS, f));
  limpiar();
  const navegador = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  page = await navegador.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1.5, colorScheme: 'light' });
  // Mismo tema claro en todas las capturas (el tema se guarda en el navegador).
  await page.addInitScript(() => localStorage.setItem('app-theme', 'light'));
  page.on('response', async (r) => {
    if (r.status() >= 400 && r.url().includes('/api/')) {
      console.log(`   [HTTP ${r.status()}] ${r.request().method()} ${r.url()} ${(await r.text().catch(() => '')).slice(0, 400)}`);
    }
  });
  prepararArchivos();
  try {
    const todas = [inicio, registrarPaciente, triajeYCita, citaResto, control, ecografia, moduloIA, laboratorio, parto, cierreYRoles];
    const solo = (process.env.SOLO || '').split(',').filter(Boolean);
    for (const seccion of todas.filter((f) => !solo.length || solo.includes(f.name))) {
      try {
        await seccion();
      } catch (e) {
        if (e.message === 'HASTA') throw e;
        await page.screenshot({ path: path.join(SALIDA, `error_${seccion.name}.png`) });
        console.error(`ERROR en ${seccion.name}: ${e.message.split('\n').slice(0, 4).join(' | ')}`);
        process.exitCode = 1;
      }
    }
  } catch (e) {
    if (e.message !== 'HASTA') throw e;
  } finally {
    await navegador.close();
    if (!process.env.CONSERVAR) limpiar();
  }
})();
