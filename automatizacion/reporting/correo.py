"""Envío automático del reporte por correo (SMTP con STARTTLS; Gmail con contraseña de aplicación).

Variables de .env: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, MAIL_TO (varios separados por coma).
Adjunta reporte.pdf (o reporte.docx si no hay PDF) y reporte.html. Las capturas no viajan: quedan en el ZIP local.
Sin SMTP_PASSWORD no intenta enviar y lo informa.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from reporting.modelo import cargar
from utils import config


def configurado() -> bool:
    return all(config.env(v) for v in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "MAIL_TO"))


def _metricas() -> list[tuple[str, str]]:
    """Coberturas calculadas por tools/exportar_casos.py (docs/cobertura.json), si existen."""
    import json
    f = config.RAIZ / "docs" / "cobertura.json"
    if not f.exists():
        return []
    c = json.loads(f.read_text(encoding="utf-8"))
    h = c.get("por_herramienta", {})
    return [("Casos de prueba diseñados", str(c["casos_diseñados"])),
            ("Casos automatizados", f"{c['automatizados']} de {c['seleccionados_automatizar']} seleccionados "
                                    f"({c['cobertura_automatizacion_pct']} %)"),
            ("Por herramienta", ", ".join(f"{k}: {v}" for k, v in h.items())),
            ("Cobertura de requisitos", f"{c['rf_con_casos'] + c['rnf_con_casos']} de {c['rf_total'] + c['rnf_total']} "
                                        f"({c['cobertura_requisitos_pct']} %)")]


def _cuerpo(r) -> tuple[str, str]:
    t = r.totales
    fallos = "".join(f"<li><b>{c['tc']}</b> {c['nombre']} — {c['error'][:160]}</li>" for c in r.fallos[:15])
    texto = (f"Corrida {r.run_id} ({r.datos.get('suite') or 'completa'}): {t['total']} pruebas, {t['PASS']} PASS, "
             f"{t['FAIL']} FAIL, {t['BLOCKED']} BLOCKED, {t['NOT RUN']} NOT RUN. Éxito {r.tasa_exito} % sobre ejecutadas.")
    html = f"""<div style="font-family:Segoe UI,Arial,sans-serif;color:#1b2a2c">
<h2 style="margin:0 0 6px">Fetal Medical · Reporte de pruebas automatizadas</h2>
<p style="margin:0 0 12px;color:#5b6e70">Corrida {r.run_id} · suite {r.datos.get('suite') or 'completa'} · {r.duracion_legible}</p>
<table cellpadding="8" style="border-collapse:collapse;font-size:14px">
<tr><td style="border:1px solid #d9e2e2">Pruebas<br><b style="font-size:20px">{t['total']}</b></td>
<td style="border:1px solid #d9e2e2;color:#1e7f4f">PASS<br><b style="font-size:20px">{t['PASS']}</b></td>
<td style="border:1px solid #d9e2e2;color:#b3261e">FAIL<br><b style="font-size:20px">{t['FAIL']}</b></td>
<td style="border:1px solid #d9e2e2;color:#a15c00">BLOCKED<br><b style="font-size:20px">{t['BLOCKED']}</b></td>
<td style="border:1px solid #d9e2e2;color:#6b7280">NOT RUN<br><b style="font-size:20px">{t['NOT RUN']}</b></td>
<td style="border:1px solid #d9e2e2">Éxito<br><b style="font-size:20px">{r.tasa_exito} %</b></td></tr></table>
<p style="font-size:15px"><b>Porcentaje de salud de la suite: {r.tasa_exito} %</b> (PASS sobre pruebas ejecutadas)</p>
{'<h3>Fallos</h3><ul>' + fallos + '</ul>' if fallos else '<p>Sin fallos en esta corrida.</p>'}
<h3>Resultados por módulo</h3><table cellpadding="5" style="border-collapse:collapse;font-size:13px">
<tr style="background:#1f3864;color:#fff"><th>Módulo</th><th>Pruebas</th><th>PASS</th><th>FAIL</th><th>Salud</th></tr>
{''.join(f"<tr><td style='border:1px solid #d9e2e2'>{m['modulo']}</td><td style='border:1px solid #d9e2e2' align='right'>{m['total']}</td><td style='border:1px solid #d9e2e2' align='right'>{m['PASS']}</td><td style='border:1px solid #d9e2e2' align='right'>{m['FAIL']}</td><td style='border:1px solid #d9e2e2' align='right'>{m['tasa']} %</td></tr>" for m in r.por_modulo)}</table>
<h3>Métricas</h3><table cellpadding="5" style="border-collapse:collapse;font-size:13px">
{''.join(f"<tr><td style='border:1px solid #d9e2e2'><b>{k}</b></td><td style='border:1px solid #d9e2e2'>{v}</td></tr>" for k, v in _metricas())}
{''.join(f"<tr><td style='border:1px solid #d9e2e2'><b>Carga ({x['escenario']})</b></td><td style='border:1px solid #d9e2e2'>{x['peticiones']} peticiones, p95 {x['p95_ms']:.0f} ms, errores {x['error_pct']} %</td></tr>" for x in r.rendimiento)}
<tr><td style='border:1px solid #d9e2e2'><b>Defectos</b></td><td style='border:1px solid #d9e2e2'>{len(r.defectos)} registrados, {sum(d['estado'] == 'Verificado' for d in r.defectos)} corregidos y verificados</td></tr></table>
<p style="color:#5b6e70;font-size:12px">Adjuntos: reporte en PDF/Word y HTML. Las evidencias (capturas EV) quedan en
reports/{r.run_id}/ del equipo de pruebas. Datos sintéticos QA; sin datos de pacientes reales.</p></div>"""
    return texto, html


def enviar(run_id: str | None = None) -> dict:
    r = cargar(run_id)
    if not configurado():
        return {"enviado": False, "motivo": "Falta configurar SMTP en .env (SMTP_PASSWORD de aplicación de Gmail)"}
    texto, html = _cuerpo(r)
    m = EmailMessage()
    estado = "con fallos" if r.totales["FAIL"] else "sin fallos"
    m["Subject"] = f"[Fetal Medical QA] Corrida {r.run_id} {estado}: {r.totales['PASS']}/{r.totales['total']} PASS"
    m["From"] = config.env("SMTP_USER")
    destinatarios = [x.strip() for x in config.env("MAIL_TO").split(",") if x.strip()]
    m["To"] = ", ".join(destinatarios)
    m.set_content(texto)
    m.add_alternative(html, subtype="html")
    adjuntos = []
    capitulo = config.RAIZ / "capitulo6" / "entregables" / "Capitulo_6_Estrategia_y_Ejecucion_de_Pruebas.pdf"
    if capitulo.exists() and capitulo.stat().st_size < 18 * 1024 * 1024:
        m.add_attachment(capitulo.read_bytes(), maintype="application", subtype="pdf", filename=capitulo.name)
        adjuntos.append(capitulo.name)
    for nombre, tipo in (("reporte.pdf", ("application", "pdf")), ("reporte.docx", ("application",
                         "vnd.openxmlformats-officedocument.wordprocessingml.document")), ("reporte.html", ("text", "html"))):
        f = r.dir_run / nombre
        if nombre == "reporte.docx" and (r.dir_run / "reporte.pdf").exists():
            continue
        if f.exists() and f.stat().st_size < 20 * 1024 * 1024:
            m.add_attachment(f.read_bytes(), maintype=tipo[0], subtype=tipo[1], filename=f"{r.run_id}_{nombre}")
            adjuntos.append(nombre)
    try:
        with smtplib.SMTP(config.env("SMTP_HOST"), int(config.env("SMTP_PORT", "587")), timeout=60) as s:
            s.starttls()
            s.login(config.env("SMTP_USER"), config.env("SMTP_PASSWORD"))
            s.send_message(m)
    except smtplib.SMTPAuthenticationError as e:
        return {"enviado": False, "motivo": f"Gmail rechazó la clave ({e.smtp_code}). Use una contraseña de aplicación: "
                                            "myaccount.google.com/apppasswords"}
    except smtplib.SMTPServerDisconnected:
        # Gmail responde 534 «Application-specific password required» y corta la conexión cuando se le da la
        # contraseña normal de una cuenta con verificación en dos pasos
        return {"enviado": False, "motivo": "Gmail cerró la conexión al autenticar: la cuenta exige una contraseña de "
                                            "aplicación (myaccount.google.com/apppasswords), no la contraseña normal"}
    except Exception as e:  # el reporte ya existe en disco: un fallo del correo no invalida la corrida
        return {"enviado": False, "motivo": f"{type(e).__name__}: {str(e)[:200]}"}
    return {"enviado": True, "para": destinatarios, "adjuntos": adjuntos}
