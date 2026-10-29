// Flujo de negocio con cada rol en su paso, contra el sistema en marcha:
//   recepción registra y agenda → la paciente llega (recepción) → triaje
//   (enfermería) → consulta y control (médica; la cita se cierra sola) →
//   laboratorio con resultados → parto, recién nacido y epicrisis (el embarazo
//   queda finalizado). Más: casos inválidos que deben rechazarse con su motivo,
//   lo que cada rol NO puede hacer, y el cierre de las citas vencidas.
//
// La cita «de hoy» se agenda en un turno libre si queda alguno; de noche (sin
// turnos) se crea con el ORM a las 07:30 (antes de la agenda: no choca con nada),
// porque la API no deja agendar en el pasado. Necesita E2E_PYTHON o Backend/.venv.
// Datos con apellido «E2E»: python manage.py limpiar_datos_e2e --schema=clinica_demo
const path = require('path');
const { execFileSync } = require('child_process');
const { test, expect } = require('@playwright/test');

const API = process.env.E2E_API || 'http://localhost:8000/api';
const PASSWORD = process.env.E2E_PASSWORD || 'Demo2026!';
const BACKEND = path.join(__dirname, '..', '..');
const PYTHON = process.env.E2E_PYTHON || path.join(BACKEND, '.venv', 'Scripts', 'python.exe');
const ESQUEMA = process.env.E2E_SCHEMA || 'clinica_demo';
const CUENTAS = {
  recepcion: 'recep.flores@fetalmedical.bo',
  enfermera: 'enf.mamani@fetalmedical.bo',
  medico: 'dra.garcia@fetalmedical.bo',
};
const CI = String(9100000 + (Date.now() % 800000));

const local = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const dia = (n) => local(new Date(Date.now() + n * 864e5));
const habil = (desde) => {
  const d = new Date(Date.now() + desde * 864e5);
  while ([0, 6].includes(d.getDay())) d.setDate(d.getDate() + 1);
  return local(d);
};
const lista = (d) => (Array.isArray(d) ? d : d?.results || []);

/** ORM en el esquema de la demo (solo para lo que la API, con razón, no deja hacer). */
function orm(codigo) {
  const script = `from django_tenants.utils import schema_context\nwith schema_context(${JSON.stringify(ESQUEMA)}):\n${codigo.split('\n').map((l) => `    ${l}`).join('\n')}`;
  return execFileSync(PYTHON, ['manage.py', 'shell', '-c', script], { cwd: BACKEND, encoding: 'utf-8' });
}

async function entrar(browser, rol) {
  const ctx = await browser.newContext({ reducedMotion: 'reduce', viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  page.errores = [];
  page.on('pageerror', (e) => page.errores.push(e.message));
  await page.goto('/login');
  await page.fill('input[placeholder="ejemplo@fetalmedical.com"]', CUENTAS[rol]);
  await page.fill('input[placeholder="Ingrese su contraseña"]', PASSWORD);
  await page.click('button[type=submit]');
  await page.waitForURL((u) => !u.pathname.includes('login'));
  /** fetch con la sesión y el CSRF de la página, como lo hace la aplicación. */
  page.api = (metodo, ruta, cuerpo) => page.evaluate(async ([api, metodo, ruta, cuerpo]) => {
    const csrf = (document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/) || [])[1];
    const r = await fetch(api + ruta, {
      method: metodo,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRFToken': decodeURIComponent(csrf) } : {}) },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
    let datos = null;
    try { datos = await r.json(); } catch { /* sin cuerpo */ }
    return { status: r.status, datos };
  }, [API, metodo, ruta, cuerpo]);
  return page;
}

/** Abre «Más acciones» de la cita en la lista y elige la acción; el menú debe verse entero. */
async function accionEnLista(page, idClinico, accion, aviso) {
  await page.goto('/dashboard/citas');
  const buscar = page.getByPlaceholder('Buscar por paciente, médico, motivo, ID clínico...');
  await buscar.fill(idClinico);
  const [a, m, d] = dia(0).split('-');
  const fila = page.locator('.ant-table-row', { hasText: idClinico }).filter({ hasText: `${d}/${m}/${a}` }).first();
  await expect(fila).toBeVisible();
  await fila.getByRole('button', { name: 'Más acciones de la cita' }).click();
  const opcion = page.locator('.ant-dropdown:not(.ant-dropdown-hidden) .ant-dropdown-menu-item', { hasText: accion });
  await expect(opcion).toBeVisible();
  const caja = await opcion.boundingBox();
  const vista = page.viewportSize();
  expect(caja.y + caja.height, `«${accion}» cae fuera de la pantalla`).toBeLessThanOrEqual(vista.height);
  await opcion.click();
  await expect(page.locator('.ant-message-notice', { hasText: aviso })).toBeVisible();
}

test.describe.configure({ mode: 'serial' });
test.setTimeout(180_000);

test.describe('Flujo de negocio por roles', () => {
  const p = {};
  const ids = {};

  test.beforeAll(async ({ browser }) => {
    for (const rol of Object.keys(CUENTAS)) p[rol] = await entrar(browser, rol);
    ids.medico = (await p.medico.api('GET', '/usuarios/me/')).datos.id;
  });

  test.afterAll(async () => {
    for (const [rol, page] of Object.entries(p)) {
      expect(page.errores, `errores de JavaScript (${rol})`).toEqual([]);
      await page.context().close();
    }
  });

  test('1. recepción registra a la paciente (y el sistema rechaza los datos imposibles)', async () => {
    const base = { nombre: 'Negocio', apellido_paterno: 'E2E', apellido_materno: 'Flujo', fecha_nacimiento: '1995-03-12',
      ci: CI, genero: 'femenino', consentimiento_datos_aceptado: true };
    const r = await p.recepcion.api('POST', '/pacientes/', base);
    expect(r.status, JSON.stringify(r.datos)).toBe(201);
    ids.paciente = r.datos.id;
    ids.idClinico = r.datos.id_clinico;
    const rechazos = [
      [{ ...base }, 'ci'],
      [{ ...base, ci: `${CI}1`, fecha_nacimiento: dia(1) }, 'fecha_nacimiento'],
      [{ ...base, ci: `${CI}2`, consentimiento_datos_aceptado: false }, 'consentimiento_datos_aceptado'],
    ];
    for (const [datos, campo] of rechazos) {
      const x = await p.recepcion.api('POST', '/pacientes/', datos);
      expect(x.status, `paciente sin rechazo en «${campo}»`).toBe(400);
      expect(Object.keys(x.datos)).toContain(campo);
    }
  });

  test('2. la agenda tiene turnos libres y las reglas de la cita se cumplen', async () => {
    const fecha = habil(1);
    const h = await p.recepcion.api('GET', `/citas/disponibilidades/horarios-disponibles/?medico_id=${ids.medico}&fecha=${fecha}`);
    const libres = (h.datos.horarios || []).filter((x) => x.disponible);
    // ESPERADO: turnos libres para agendar (antes: agenda 100 % llena hasta fin de año).
    expect(libres.length, `sin turnos libres el ${fecha}`).toBeGreaterThan(0);
    const cita = { paciente: ids.paciente, medico: ids.medico, tipo_cita: 'control', motivo: 'Control prenatal', fecha_cita: fecha };
    const r = await p.recepcion.api('POST', '/citas/citas/', { ...cita, hora_cita: libres[0].hora });
    expect(r.status, JSON.stringify(r.datos)).toBe(201);
    ids.citaManana = r.datos.id;

    const casos = [
      ['mismo turno otra vez', { ...cita, hora_cita: libres[0].hora }, 'hora_cita'],
      ['en el pasado', { ...cita, fecha_cita: dia(-1), hora_cita: '09:30:00' }, 'fecha_cita'],
      ['fuera de los turnos (09:17)', { ...cita, hora_cita: '09:17:00' }, 'hora_cita'],
      ['en el almuerzo', { ...cita, hora_cita: '12:30:00' }, 'hora_cita'],
    ];
    for (const [nombre, datos, campo] of casos) {
      const x = await p.recepcion.api('POST', '/citas/citas/', datos);
      expect(x.status, `cita ${nombre}: ${JSON.stringify(x.datos)}`).toBe(400);
      expect(Object.keys(x.datos)).toContain(campo);
    }
    const acc = (accion, cuerpo) => p.recepcion.api('POST', `/citas/citas/${ids.citaManana}/${accion}/`, cuerpo);
    expect((await acc('no-asistio')).status, '«No asistió» antes del día de la cita').toBe(400);
    expect((await acc('marcar-presente')).status, 'llegada registrada otro día').toBe(400);
    expect((await acc('confirmar')).status).toBe(200);
    if (libres[1]) {
      const rp = await acc('reprogramar', { fecha_cita: fecha, hora_cita: libres[1].hora });
      expect(rp.status, JSON.stringify(rp.datos)).toBe(200);
    }
    expect((await acc('cancelar')).status).toBe(200);
    expect((await acc('cancelar')).status, 'cancelar dos veces').toBe(400);
  });

  test('3. la paciente llega: recepción la marca presente desde la lista', async () => {
    const hoy = dia(0);
    const h = await p.recepcion.api('GET', `/citas/disponibilidades/horarios-disponibles/?medico_id=${ids.medico}&fecha=${hoy}`);
    const libre = (h.datos.horarios || []).find((x) => x.disponible);
    if (libre) {
      const r = await p.recepcion.api('POST', '/citas/citas/', { paciente: ids.paciente, medico: ids.medico,
        tipo_cita: 'control', motivo: 'Control prenatal', fecha_cita: hoy, hora_cita: libre.hora });
      expect(r.status, JSON.stringify(r.datos)).toBe(201);
      ids.cita = r.datos.id;
    } else {
      const salida = orm([
        'import datetime',
        'from django.utils import timezone',
        'from citas.models import Cita',
        `c = Cita.objects.bulk_create([Cita(paciente_id=${ids.paciente}, medico_id=${ids.medico}, fecha_cita=timezone.localdate(), hora_cita=datetime.time(7, 30), tipo_cita="control", estado="agendada", motivo="Control prenatal")])[0]`,
        'print("CITA", c.id)',
      ].join('\n'));
      ids.cita = Number(/CITA (\d+)/.exec(salida)[1]);
    }
    await accionEnLista(p.recepcion, ids.idClinico, 'Marcar Presente', 'Paciente marcado como presente');
    const c = await p.recepcion.api('GET', `/citas/citas/${ids.cita}/`);
    expect(c.datos.estado).toBe('en_espera');
  });

  test('4. enfermería hace el triaje: queda unido a la cita (y rechaza signos imposibles)', async () => {
    const tri = { paciente: ids.paciente, prioridad: 'normal', peso_kg: '68.0', talla_cm: '158.0', presion_sistolica: 112,
      presion_diastolica: 72, temperatura: '36.6', frecuencia_cardiaca: 82, frecuencia_respiratoria: 16, motivo_visita: 'Control prenatal' };
    for (const [nombre, cambio, campo] of [
      ['presión invertida 60/120', { presion_sistolica: 60, presion_diastolica: 120 }, 'presion_sistolica'],
      ['temperatura 50 °C', { temperatura: '50.0' }, 'temperatura'],
      ['saturación 120 %', { saturacion_oxigeno: 120 }, 'saturacion_oxigeno'],
    ]) {
      const x = await p.enfermera.api('POST', '/triaje/triajes/', { ...tri, ...cambio });
      expect(x.status, `triaje con ${nombre}`).toBe(400);
      expect(Object.keys(x.datos)).toContain(campo);
    }
    const r = await p.enfermera.api('POST', '/triaje/triajes/', tri);
    expect(r.status, JSON.stringify(r.datos)).toBe(201);
    const unidos = lista((await p.enfermera.api('GET', `/triaje/triajes/?cita=${ids.cita}`)).datos);
    expect(unidos.map((t) => t.id), 'el triaje no quedó unido a la cita').toContain(r.datos.id);
    // Recepción no ve datos clínicos.
    expect((await p.recepcion.api('POST', '/triaje/triajes/', tri)).status).toBe(403);
  });

  test('5. la médica la pasa a consulta desde la lista', async () => {
    await accionEnLista(p.medico, ids.idClinico, 'Pasar a Consulta', 'Paciente pasado a consulta');
    expect((await p.medico.api('GET', `/citas/citas/${ids.cita}/`)).datos.estado).toBe('en_consulta');
  });

  test('6. embarazo y control prenatal de hoy: la cita queda completada', async () => {
    const emb = { paciente: ids.paciente, numero_gesta: 1, fecha_ultima_menstruacion: dia(-273) };
    expect((await p.medico.api('POST', '/embarazos/', { ...emb, fecha_ultima_menstruacion: dia(5) })).status, 'FUM futura').toBe(400);
    const e = await p.medico.api('POST', '/embarazos/', emb);
    expect(e.status, JSON.stringify(e.datos)).toBe(201);
    ids.embarazo = e.datos.id;
    expect((await p.medico.api('POST', '/embarazos/', { ...emb, numero_gesta: 2 })).status, 'segundo embarazo activo').toBe(400);

    const ctl = { embarazo: ids.embarazo, paciente: ids.paciente, numero_control: 1, fecha_control: dia(0), semanas_gestacion: 39,
      peso_actual: '68.0', talla: '158', presion_arterial_sistolica: 112, presion_arterial_diastolica: 72, frecuencia_cardiaca_fetal: 142 };
    for (const [nombre, cambio, campo] of [
      ['futuro', { fecha_control: dia(3) }, 'fecha_control'],
      ['anterior a la FUM', { fecha_control: dia(-300) }, 'fecha_control'],
      ['presión invertida', { presion_arterial_sistolica: 70, presion_arterial_diastolica: 110 }, 'presion_arterial_sistolica'],
      ['FCF 320', { frecuencia_cardiaca_fetal: 320 }, 'frecuencia_cardiaca_fetal'],
    ]) {
      const x = await p.medico.api('POST', '/controles/', { ...ctl, ...cambio });
      expect(x.status, `control ${nombre}: ${JSON.stringify(x.datos)}`).toBe(400);
      expect(Object.keys(x.datos)).toContain(campo);
    }
    expect((await p.recepcion.api('POST', '/controles/', ctl)).status, 'recepción registra controles').toBe(403);
    const c = await p.medico.api('POST', '/controles/', ctl);
    expect(c.status, JSON.stringify(c.datos)).toBe(201);
    const cita = (await p.medico.api('GET', `/citas/citas/${ids.cita}/`)).datos;
    // ESPERADO: completada por el control (antes: seguía «en consulta» y al día siguiente «No asistió»).
    expect(cita.estado).toBe('completada');
    expect(cita.historial.map((x) => x.estado_nuevo)).toEqual(expect.arrayContaining(['en_espera', 'en_consulta', 'completada']));
  });

  test('7. laboratorio: se piden exámenes y los resultados SE GUARDAN', async () => {
    const tipos = lista((await p.medico.api('GET', '/laboratorios/tipos-examenes/?page_size=100')).datos);
    let tipo = null;
    let valores = [];
    for (const t of tipos) {
      valores = (await p.medico.api('GET', `/laboratorios/examenes/valores-referencia-por-tipo/?tipo_examen_id=${t.id}`)).datos;
      valores = Array.isArray(valores) ? valores : valores?.valores_referencia || [];
      if (valores.length) { tipo = t; break; }
    }
    expect(tipo, 'ningún tipo de examen con valores de referencia').not.toBeNull();
    const ex = await p.medico.api('POST', '/laboratorios/examenes/', { paciente: ids.paciente, tipo_examen: tipo.id, embarazo: ids.embarazo });
    expect(ex.status, JSON.stringify(ex.datos)).toBe(201);
    const url = `/laboratorios/examenes/${ex.datos.id}`;
    expect((await p.medico.api('POST', `${url}/cambiar-estado/`, { estado: 'completado' })).status, 'completar sin resultados').toBe(400);
    const vr = valores[0];
    const valor = vr.valor_minimo != null && vr.valor_maximo != null ? (Number(vr.valor_minimo) + Number(vr.valor_maximo)) / 2 : undefined;
    const r = await p.medico.api('POST', `${url}/crear-resultado-multiple/`, {
      resultados: [{ valor_referencia: vr.id, valor_numerico: valor, valor_texto: valor === undefined ? 'Negativo' : undefined }],
      completar_examen: true,
    });
    expect(r.status, JSON.stringify(r.datos)).toBe(201);
    // ESPERADO: 1 guardado y examen completado (antes: 201 con 0 guardados).
    expect(r.datos.resultados_creados).toBe(1);
    const examen = (await p.medico.api('GET', `${url}/`)).datos;
    expect(examen.estado).toBe('completado');
    expect((await p.medico.api('POST', `${url}/cambiar-estado/`, { estado: 'solicitado' })).status, 'reabrir un examen completado').toBe(400);
  });

  test('8. parto, recién nacido y epicrisis: el embarazo queda finalizado', async () => {
    const ahora = new Date();
    const parto = { paciente: ids.paciente, embarazo: ids.embarazo, edad_gestacional_parto: '39', tipo_parto: 'vaginal_espontaneo', parto_finalizado: true,
      fecha_parto: ahora.toISOString() };
    expect((await p.enfermera.api('POST', '/partos/', parto)).status, 'enfermería registra partos').toBe(403);
    expect((await p.medico.api('POST', '/partos/', { ...parto, edad_gestacional_parto: '50' })).status, 'parto a las 50 semanas').toBe(400);
    const r = await p.medico.api('POST', '/partos/', parto);
    expect(r.status, JSON.stringify(r.datos)).toBe(201);
    ids.parto = r.datos.id;
    const rn = { parto: ids.parto, fecha_nacimiento: ahora.toISOString(), sexo: 'femenino', peso_nacimiento: 3250,
      talla_nacimiento: '49.5', apgar_1_minuto: 8, apgar_5_minutos: 9 };
    expect((await p.medico.api('POST', '/partos/recien-nacidos/', { ...rn, peso_nacimiento: 50 })).status, 'recién nacido de 50 g').toBe(400);
    expect((await p.medico.api('POST', '/partos/recien-nacidos/', { ...rn, apgar_5_minutos: 11 })).status, 'Apgar 11').toBe(400);
    const n = await p.medico.api('POST', '/partos/recien-nacidos/', rn);
    expect(n.status, JSON.stringify(n.datos)).toBe(201);
    const epi = { parto: ids.parto, fecha_egreso: new Date().toISOString(), diagnostico_ingreso: 'Embarazo de 39 semanas en trabajo de parto',
      diagnostico_egreso: 'Puerperio inmediato sin complicaciones', resumen_clinico: 'Parto eutócico, recién nacida vigorosa.' };
    const ep = await p.medico.api('POST', '/partos/epicrisis/', epi);
    expect(ep.status, JSON.stringify(ep.datos)).toBe(201);
    expect((await p.medico.api('GET', `/embarazos/${ids.embarazo}/`)).datos.estado).toBe('finalizado');
  });

  test('9. una cita de ayer que nadie atendió queda «No asistió»', async () => {
    const salida = orm([
      'import datetime',
      'from django.utils import timezone',
      'from citas.models import Cita',
      `c = Cita.objects.bulk_create([Cita(paciente_id=${ids.paciente}, medico_id=${ids.medico}, fecha_cita=timezone.localdate() - datetime.timedelta(days=1), hora_cita=datetime.time(7, 30), tipo_cita="control", estado="confirmada", motivo="Control prenatal")])[0]`,
      'print("CITA", c.id)',
    ].join('\n'));
    const vencida = Number(/CITA (\d+)/.exec(salida)[1]);
    execFileSync(PYTHON, ['manage.py', 'cerrar_citas_vencidas', `--tenant=${ESQUEMA}`], { cwd: BACKEND });
    const c = (await p.recepcion.api('GET', `/citas/citas/${vencida}/`)).datos;
    expect(c.estado).toBe('no_asistio');
    expect(c.historial[0].motivo_cambio).toMatch(/Cierre automático/);
  });
});
