"""Ayudante de INICIAR.bat: lo que en un .bat sería frágil, aquí en Python.

    python scripts/arranque.py build-vigente       0 si build/ está al día con src/, 1 si hay que compilar
    python scripts/arranque.py detener             cierra lo que escucha en 3000, 8000, 8001 y 8010
    python scripts/arranque.py esperar URL SEG     0 cuando la URL responde (cualquier código < 500)
    python scripts/arranque.py red [--produccion]  IP de este equipo y si está habilitada para la clínica
    python scripts/arranque.py habilitar-red       agrega la IP de este equipo a .env y a los dominios de la clínica

Lo usa INICIAR.bat con el Python del entorno virtual del backend.
"""
from __future__ import annotations

import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND / "frontend"
PUERTOS = (3000, 8000, 8001, 8010)


def build_vigente() -> int:
    """El build vale si es más nuevo que todo src/, public/ y package.json."""
    indice = FRONTEND / "build" / "index.html"
    if not indice.exists():
        print("    No hay build del frontend.")
        return 1
    fuentes = [p for carpeta in ("src", "public") for p in (FRONTEND / carpeta).rglob("*") if p.is_file()]
    fuentes += [FRONTEND / "package.json"]
    mas_nuevo = max(p.stat().st_mtime for p in fuentes)
    if mas_nuevo > indice.stat().st_mtime:
        print("    El código del frontend cambió desde el último build.")
        return 1
    return 0


def detener() -> int:
    import psutil

    cerrados = 0
    for conexion in psutil.net_connections(kind="tcp"):
        if conexion.status == psutil.CONN_LISTEN and conexion.laddr and conexion.laddr.port in PUERTOS \
                and conexion.pid:
            try:
                proceso = psutil.Process(conexion.pid)
                nombre = proceso.name()
                for hijo in proceso.children(recursive=True):
                    hijo.kill()
                proceso.kill()
                cerrados += 1
                print(f"    cerrado puerto {conexion.laddr.port} ({nombre}, pid {conexion.pid})")
            except psutil.Error:
                pass
    if not cerrados:
        print("    No había servicios del sistema corriendo.")
    return 0


def esperar(url: str, segundos: float) -> int:
    limite = time.time() + segundos
    while time.time() < limite:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return 0
        except urllib.error.HTTPError as e:
            if e.code < 500:
                return 0
        except OSError:
            pass
        time.sleep(2)
    return 1


def ips_locales() -> list[str]:
    ips = set()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))  # no envía nada: solo elige la interfaz de salida
            ips.add(s.getsockname()[0])
    except OSError:
        pass
    try:
        ips.update(i[4][0] for i in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def red(produccion: bool = False) -> int:
    """¿Pueden entrar otras PC de la red? La IP tiene que estar en ALLOWED_HOSTS,
    en CORS/CSRF (puerto 3000) y como dominio de la clínica.

    Con `--produccion` se mira la configuración con DEBUG=False, la de los
    servicios que arrancó INICIAR.bat: con el DEBUG del .env (desarrollo) CORS
    permite todo y no hay lista, y el chequeo daba un aviso falso.
    """
    if produccion:
        os.environ["DEBUG"] = "False"
    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    import django

    django.setup()
    from django.conf import settings

    try:
        from clientes.models import Domain

        dominios = set(Domain.objects.values_list("domain", flat=True))
    except Exception:
        dominios = None
    ips = ips_locales()
    if not ips:
        print("    Sin red: solo se puede usar desde este equipo (http://localhost:3000).")
        return 0
    todo_bien = True
    for ip in ips:
        faltas = []
        if ip not in settings.ALLOWED_HOSTS:
            faltas.append(f"ALLOWED_HOSTS ({ip})")
        origen = f"http://{ip}:3000"
        if not getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False) and                 origen not in getattr(settings, "CORS_ALLOWED_ORIGINS", []):
            faltas.append(f"CORS_ALLOWED_ORIGINS ({origen})")
        if origen not in settings.CSRF_TRUSTED_ORIGINS:
            faltas.append(f"CSRF_TRUSTED_ORIGINS ({origen})")
        if dominios is not None and ip not in dominios:
            faltas.append(f"dominio de la clínica ({ip})")
        if faltas:
            todo_bien = False
            print(f"    AVISO: otras PC no podrán entrar por http://{ip}:3000. Falta en Backend\\.env o en la base:")
            for f in faltas:
                print(f"       - {f}")
        else:
            print(f"    OK otras PC de la red entran por http://{ip}:3000")
    if not todo_bien:
        print("    (Desde este mismo equipo funciona igual por http://localhost:3000.)")
    return 0


def habilitar_red() -> int:
    """Si la IP de este servidor cambió (DHCP), otras PC de la red no podían entrar.

    Agrega la IP a ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS y CSRF_TRUSTED_ORIGINS de
    Backend/.env (con respaldo previo; no toca ninguna otra línea) y la registra
    como dominio de la clínica principal (la de «localhost»). Es la IP del propio
    servidor: no abre el sistema a ningún otro origen.
    """
    import shutil
    from datetime import datetime

    ips = ips_locales()
    if not ips:
        return 0
    archivo = BACKEND / ".env"
    lineas = archivo.read_text(encoding="utf-8").splitlines()
    cambios = []

    def agregar(clave: str, valor: str) -> None:
        for i, linea in enumerate(lineas):
            if linea.startswith(f"{clave}="):
                actuales = [v.strip() for v in linea.split("=", 1)[1].split(",") if v.strip()]
                if valor not in actuales:
                    lineas[i] = f"{clave}={','.join(actuales + [valor])}"
                    cambios.append(f"{clave} += {valor}")
                return
        lineas.append(f"{clave}={valor}")
        cambios.append(f"{clave} = {valor}")

    for ip in ips:
        agregar("ALLOWED_HOSTS", ip)
        agregar("CORS_ALLOWED_ORIGINS", f"http://{ip}:3000")
        agregar("CSRF_TRUSTED_ORIGINS", f"http://{ip}:3000")
    if cambios:
        respaldo = BACKEND / f".env.respaldo-{datetime.now():%Y%m%d-%H%M%S}"
        shutil.copy2(archivo, respaldo)
        archivo.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        for c in cambios:
            print(f"    .env: {c}")
        print(f"    (respaldo del .env anterior: {respaldo.name})")

    sys.path.insert(0, str(BACKEND))
    os.chdir(BACKEND)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    import django

    django.setup()
    from clientes.models import Domain

    principal = Domain.objects.select_related("tenant").filter(domain="localhost").first()
    if principal is None:
        print("    AVISO: no hay dominio «localhost»; no se registró la IP como dominio de la clínica.")
        return 0
    for ip in ips:
        _, creado = Domain.objects.get_or_create(domain=ip, defaults={"tenant": principal.tenant, "is_primary": False})
        if creado:
            print(f"    dominio {ip} -> {principal.tenant.schema_name}")
    if not cambios:
        print(f"    OK la red ya estaba habilitada ({', '.join(ips)})")
    return 0


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else ""
    if accion == "build-vigente":
        sys.exit(build_vigente())
    if accion == "detener":
        sys.exit(detener())
    if accion == "esperar":
        sys.exit(esperar(sys.argv[2], float(sys.argv[3])))
    if accion == "red":
        sys.exit(red(produccion="--produccion" in sys.argv))
    if accion == "habilitar-red":
        sys.exit(habilitar_red())
    print(__doc__)
    sys.exit(2)
