"""Registro de ACCESOS a datos clínicos (quién vio qué y cuándo).

Por qué existe este módulo
--------------------------
Los signals de auditoría cubren las ESCRITURAS: crear, editar y borrar. Pero
en una historia clínica la lectura también es un hecho auditable — quién abrió
el expediente de una paciente es exactamente el tipo de acceso que un hospital
tiene que poder responder. Antes de esto, la acción `VER` estaba declarada en
`RegistroAuditoria.ACCIONES` pero **no se registraba nunca**: cero filas en la
base.

Qué registra y qué no
---------------------
Registra las lecturas (`GET`/`HEAD`) de endpoints clínicos autenticados, con
el usuario, su rol, el módulo, el identificador del registro consultado, la
IP, el navegador y la ruta exacta. Deja fuera:

  - Peticiones anónimas y de infraestructura (`/health`, `/api/schema`,
    estáticos): no son accesos a datos de pacientes y solo harían ruido.
  - Las escrituras: ya las cubren los signals, y registrarlas aquí también
    duplicaría cada operación.

Sobre el volumen
----------------
Una lectura genera una fila. Es mucho, y es intencional: es lo que convierte
la auditoría en trazabilidad real. `MODULOS_AUDITABLES` acota el registro a
las rutas con datos de pacientes, para no llenar la tabla con navegación de
catálogos.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

#: Prefijo de ruta -> nombre del módulo que se guarda en la auditoría.
#: Solo estas rutas se auditan al leer: son las que exponen datos clínicos.
MODULOS_AUDITABLES = {
    "pacientes": "Paciente",
    "embarazos": "Embarazo",
    "controles": "ControlPrenatal",
    "ecografias": "Ecografia",
    "ecografias-archivos": "ArchivoEcografia",
    "laboratorios": "ExamenLaboratorio",
    "partos": "Parto",
    "antecedentes": "Antecedente",
    "evoluciones": "NotaEvolucion",
    "notas-evolucion": "NotaEvolucion",
    "triaje": "Triaje",
    "vacunas": "Vacuna",
    "citas": "Cita",
    "ia": "AnalisisIA",
    "reportes": "Reporte",
}

#: Rutas que nunca se auditan aunque cuelguen de /api/.
RUTAS_IGNORADAS = ("/api/schema", "/api/docs", "/api/redoc", "/api/health", "/api/metrics")


def describir_ruta(path: str) -> tuple[str, str]:
    """Módulo y id de registro a partir de la ruta.

    `/api/pacientes/14/historia-clinica/` -> `("Paciente", "14")`
    `/api/pacientes/`                     -> `("Paciente", "")`
    Devuelve `("", "")` si la ruta no corresponde a datos clínicos.
    """
    partes = [p for p in path.split("/") if p]
    if len(partes) < 2 or partes[0] != "api":
        return "", ""

    modulo = MODULOS_AUDITABLES.get(partes[1], "")
    if not modulo:
        return "", ""

    registro_id = partes[2] if len(partes) > 2 and partes[2].isdigit() else ""
    return modulo, registro_id


def _modo_auditoria_lecturas() -> str:
    """Qué lecturas se auditan: 'detalle' (por defecto), 'todo' o 'no'.

    `detalle` audita solo el acceso a un registro concreto —abrir la historia
    de una paciente— y no los listados. Es el valor por defecto por una razón
    medida: auditar también los listados añadía un INSERT a cada petición de
    la pantalla más usada, y con 100 usuarios concurrentes eso empujó el
    agotamiento de conexiones de PostgreSQL de 94 errores 500 a más de 1.300.

    Auditar quién abrió el expediente de una paciente es el hecho que un
    hospital necesita poder responder; que alguien haya listado la agenda no
    lo es, y cuesta el doble de latencia en la pantalla principal.

    `todo` registra también los listados: correcto donde la normativa lo exija
    y haya un pooler de conexiones delante de la base.
    """
    from django.conf import settings

    return str(getattr(settings, "AUDITAR_LECTURAS", "detalle")).lower()


def es_lectura_auditable(request) -> bool:
    """¿Esta petición es una lectura de datos clínicos por un usuario conocido?"""
    modo = _modo_auditoria_lecturas()
    if modo == "no":
        return False

    if request.method not in ("GET", "HEAD"):
        return False

    path = request.path or ""
    if not path.startswith("/api/") or path.startswith(RUTAS_IGNORADAS):
        return False

    usuario = getattr(request, "user", None)
    if not usuario or not getattr(usuario, "is_authenticated", False):
        return False

    modulo, registro_id = describir_ruta(path)
    if not modulo:
        return False

    # En modo `detalle` solo cuenta el acceso a un registro concreto: abrir la
    # historia de una paciente. Un listado no identifica a quién se consultó.
    if modo == "detalle" and not registro_id:
        return False

    return True


def registrar_acceso(request, status_code: int) -> None:
    """Guarda una fila `VER` si la petición fue una lectura clínica exitosa.

    Nunca lanza: un fallo registrando la auditoría no puede tumbar la
    respuesta que el médico está esperando. Si algo falla se deja en el log
    de la aplicación, que es donde se puede ver que la trazabilidad se rompió.
    """
    try:
        if status_code >= 400 or not es_lectura_auditable(request):
            return

        from .models import RegistroAuditoria

        modulo, registro_id = describir_ruta(request.path)
        detalle = (
            f"Consultó {modulo} {registro_id}".strip()
            if registro_id
            else f"Listó {modulo}"
        )
        RegistroAuditoria.registrar(
            usuario=request.user,
            accion="VER",
            modulo=modulo,
            registro_id=registro_id,
            detalle=detalle,
            request=request,
        )
    except Exception as e:  # nunca romper la respuesta por auditar
        logger.warning("No se pudo registrar el acceso a %s: %s", request.path, e)
