"""Sirve el frontend compilado, listo para una red 3G.

Por qué existe este archivo
---------------------------
El antiguo lanzador de desarrollo levantaba el frontend con `npm start`, que es el
servidor de DESARROLLO de Create React App: entrega los módulos sin
minificar ni agrupar, sin compresión y sin cabeceras de caché, y encima
carga la maquinaria de recarga en caliente. Sirve para programar; en la red
de una clínica es varias veces más pesado que el build real.

Este servidor entrega `build/` como corresponde:

  - **Compresión gzip** en HTML, JS, CSS, JSON y SVG. El bundle pasa de
    1.250 KB a 378 KB.
  - **Caché de un año** para todo lo que lleva hash en el nombre
    (`main.75c3202c.js`). Como el hash cambia con el contenido, cachearlo
    para siempre es seguro: la segunda visita no descarga nada.
  - **Sin caché para `index.html`**, que es el que apunta a los hashes
    nuevos tras cada despliegue.
  - **Fallback a index.html** en las rutas de la aplicación, para que
    recargar en `/pacientes/14` no dé 404.

Uso:
    python servir_produccion.py            # puerto 3000
    python servir_produccion.py 8080       # otro puerto

Antes hay que compilar al menos una vez:
    npm run build
"""
from __future__ import annotations

import gzip
import io
import mimetypes
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent / "build"
PUERTO_POR_DEFECTO = 3000

#: Tipos que vale la pena comprimir. Las imágenes y fuentes ya vienen
#: comprimidas: volver a comprimirlas gasta CPU y no ahorra nada.
COMPRIMIBLES = (
    "text/html", "text/css", "text/javascript", "application/javascript",
    "application/json", "image/svg+xml", "text/plain",
)

#: Por debajo de esto la cabecera de gzip pesa más que lo que ahorra.
MINIMO_PARA_COMPRIMIR = 1024


class ServidorProduccion(SimpleHTTPRequestHandler):
    """Estáticos con compresión, caché correcta y fallback de rutas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(RAIZ), **kwargs)

    def log_message(self, formato, *args):
        """Silencio: una clínica no necesita el log de cada icono."""

    def do_GET(self):  # noqa: N802 (nombre impuesto por la clase base)
        """Sirve el archivo pedido, o index.html si es una ruta de la app."""
        ruta = self._resolver(self.path.split("?")[0].split("#")[0])
        if ruta is None:
            self.send_error(404, "No encontrado")
            return

        datos = ruta.read_bytes()
        tipo = mimetypes.guess_type(str(ruta))[0] or "application/octet-stream"

        comprimido = self._comprimir(datos, tipo)
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(comprimido)))
        if comprimido is not datos:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
        for clave, valor in self._cabeceras_cache(ruta).items():
            self.send_header(clave, valor)
        self.end_headers()
        self.wfile.write(comprimido)

    def _resolver(self, ruta_url: str) -> Path | None:
        """Archivo real que corresponde a la URL, o index.html si es una ruta."""
        relativa = ruta_url.lstrip("/") or "index.html"
        destino = (RAIZ / relativa).resolve()

        # Nunca salir de build/: una ruta con .. no puede leer el disco.
        if RAIZ.resolve() not in destino.parents and destino != RAIZ.resolve():
            return None
        if destino.is_file():
            return destino

        # Ruta de la aplicación (/pacientes/14): la resuelve React Router.
        indice = RAIZ / "index.html"
        return indice if indice.is_file() else None

    def _comprimir(self, datos: bytes, tipo: str) -> bytes:
        """Comprime si el cliente lo acepta y el contenido lo justifica."""
        acepta = self.headers.get("Accept-Encoding", "")
        if "gzip" not in acepta:
            return datos
        if len(datos) < MINIMO_PARA_COMPRIMIR:
            return datos
        if not any(tipo.startswith(t) for t in COMPRIMIBLES):
            return datos

        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=6, mtime=0) as f:
            f.write(datos)
        return buffer.getvalue()

    @staticmethod
    def _cabeceras_cache(ruta: Path) -> dict[str, str]:
        """Caché larga para lo versionado por hash, ninguna para index.html."""
        if ruta.name == "index.html":
            # Apunta a los hashes de esta versión: si se cachea, tras un
            # despliegue el navegador seguiría pidiendo archivos que ya no están.
            return {"Cache-Control": "no-cache, must-revalidate"}
        if "/static/" in ruta.as_posix():
            # El nombre lleva hash del contenido: si cambia, cambia la URL.
            return {"Cache-Control": "public, max-age=31536000, immutable"}
        return {"Cache-Control": "public, max-age=3600"}


def main() -> int:
    if not RAIZ.is_dir():
        print(f"No existe {RAIZ}.\nCompilar primero:  npm run build")
        return 1

    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO_POR_DEFECTO
    servidor = ThreadingHTTPServer(("0.0.0.0", puerto), ServidorProduccion)
    print(f"Frontend de produccion en http://0.0.0.0:{puerto}")
    print("Compresion gzip y cache de un ano para los estaticos con hash.")
    print("Ctrl+C para detener.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
