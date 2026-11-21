"""Tests del flujo clínico: subir una ecografía y analizarla con IA.

Es el camino más usado en consulta y el que más pesa en una red móvil.
Cada test declara el resultado ESPERADO y lo compara con el OBTENIDO.
"""


from django.core.files.storage import default_storage
from django.test import TestCase, override_settings

from ecografias.ai_views import obtener_url_ia

# PNG de 1x1 píxel: el más pequeño válido. Sirve para probar el guardado sin
# depender de una imagen real ni de la GPU.
PNG_MINIMO = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class ConfiguracionDelMicroservicioTest(TestCase):
    """La URL del microservicio debe salir de settings, no de os.environ.

    Leer `os.environ` directamente hacía que `.env` pudiera apuntar a un
    puerto donde no escucha nada (8002) sin que ningún test lo notara: el
    análisis de ecografías devolvía 503 y el sistema parecía sano.
    """

    @override_settings(AI_SERVICE_URL="http://ia-de-prueba:9999")
    def test_la_url_sale_de_settings(self):
        """ESPERADO: 'http://ia-de-prueba:9999' — el valor de settings."""
        obtenido = obtener_url_ia()
        assert obtenido == "http://ia-de-prueba:9999", (
            f"Esperado 'http://ia-de-prueba:9999', obtenido {obtenido!r}"
        )

    @override_settings(AI_SERVICE_URL="http://ia:8001/")
    def test_se_quita_la_barra_final(self):
        """ESPERADO: sin barra final, para no construir '//api/analyze'."""
        obtenido = obtener_url_ia()
        assert obtenido == "http://ia:8001", (
            f"Esperado 'http://ia:8001', obtenido {obtenido!r}"
        )


class GuardarGradcamTest(TestCase):
    """El mapa de calor se guarda como archivo, no viaja dentro del JSON."""

    def test_devuelve_una_url_no_el_base64(self):
        """ESPERADO: una ruta corta bajo /media/, no 249 KB incrustados."""
        from ecografias.gradcam import guardar_gradcam

        url = guardar_gradcam(PNG_MINIMO, prefijo="eco-test")

        assert url.startswith("/media/"), f"Esperada una URL /media/..., obtenida {url!r}"
        assert len(url) < 200, f"La URL mide {len(url)} caracteres; debería ser corta."
        assert "base64" not in url

    def test_el_archivo_queda_guardado_y_es_un_png(self):
        """ESPERADO: el archivo existe y empieza con la firma de PNG."""
        from ecografias.gradcam import guardar_gradcam

        url = guardar_gradcam(PNG_MINIMO, prefijo="eco-test")
        ruta = url.replace("/media/", "")

        assert default_storage.exists(ruta), "El Grad-CAM no se guardó."
        with default_storage.open(ruta, "rb") as f:
            firma = f.read(8)
        assert firma == b"\x89PNG\r\n\x1a\n", f"No es un PNG válido: {firma!r}"

    def test_base64_invalido_devuelve_cadena_vacia(self):
        """ESPERADO: '' — un Grad-CAM roto no puede tumbar el análisis clínico.

        El resultado de patologías es lo importante; el mapa de calor es
        ayuda visual. Si falla, se pierde la imagen, no el diagnóstico.
        """
        from ecografias.gradcam import guardar_gradcam

        assert guardar_gradcam("esto-no-es-base64-valido!!", prefijo="x") == ""

    def test_sin_datos_devuelve_cadena_vacia(self):
        """ESPERADO: '' — el microservicio puede no mandar mapa de calor."""
        from ecografias.gradcam import guardar_gradcam

        assert guardar_gradcam("", prefijo="x") == ""


class PresupuestoDeRedTest(TestCase):
    """El JSON del análisis debe caber en una red móvil lenta."""

    def test_la_respuesta_no_lleva_base64_incrustado(self):
        """ESPERADO: 'gradcam_url' presente y 'gradcam_base64' ausente.

        Con el base64 dentro, la respuesta medía 252 KB de los cuales 249 KB
        (98%) eran el mapa de calor: unos 5 segundos en 3G lento para leer un
        resultado clínico que ocupa 2 KB.
        """
        from ecografias.ai_views import preparar_respuesta_ia

        crudo = {
            "gradcam_base64": PNG_MINIMO,
            "pathology_detection": {"normal": 0.9},
            "biometry": {"BPD_mm": 82.0},
        }
        salida = preparar_respuesta_ia(crudo)

        assert "gradcam_base64" not in salida, (
            "El base64 sigue viajando en el JSON; era el 98% del peso."
        )
        assert salida["gradcam_url"].startswith("/media/")
        assert salida["pathology_detection"] == {"normal": 0.9}
        assert salida["biometry"] == {"BPD_mm": 82.0}

    def test_los_datos_clinicos_caben_en_el_presupuesto(self):
        """ESPERADO: el JSON sin la imagen pesa menos de 50 KB.

        50 KB es el presupuesto para el camino clínico en 3G: por encima de
        eso la consulta se vuelve incómoda en la red de una clínica.
        """
        import json

        from ecografias.ai_views import preparar_respuesta_ia

        crudo = {
            "gradcam_base64": PNG_MINIMO,
            "pathology_detection": {f"patologia_{i}": 0.1 for i in range(16)},
            "biometry": {"BPD_mm": 82.0, "HC_mm": 300.0},
            "clinical_recommendations": ["control en 2 semanas"],
        }
        peso = len(json.dumps(preparar_respuesta_ia(crudo)))

        assert peso < 50_000, f"Esperado menos de 50.000 bytes, obtenido {peso}"

    def test_sin_mapa_de_calor_la_respuesta_sigue_siendo_valida(self):
        """ESPERADO: los datos clínicos pasan aunque no haya imagen."""
        from ecografias.ai_views import preparar_respuesta_ia

        salida = preparar_respuesta_ia({"pathology_detection": {"normal": 1.0}})

        assert salida["pathology_detection"] == {"normal": 1.0}
        assert salida.get("gradcam_url", "") == ""


class MiniaturasTest(TestCase):
    """Los listados sirven miniaturas, no la imagen de diagnóstico completa."""

    @staticmethod
    def _imagen(ancho, alto):
        from io import BytesIO

        from PIL import Image

        buf = BytesIO()
        Image.new("RGB", (ancho, alto), "gray").save(buf, format="PNG")
        buf.seek(0)
        return buf

    def test_respeta_el_ancho_maximo_y_la_proporcion(self):
        """ESPERADO: 480x270 a partir de una imagen 1920x1080."""
        from PIL import Image

        from ecografias.miniaturas import generar_miniatura

        chica = Image.open(generar_miniatura(self._imagen(1920, 1080), ancho_max=480))

        assert chica.width == 480, f"Esperado ancho 480, obtenido {chica.width}"
        assert chica.height == 270, f"Esperado alto 270, obtenido {chica.height}"

    def test_una_imagen_ya_pequena_no_se_agranda(self):
        """ESPERADO: 200x100 sin cambios; ampliar solo añade peso sin detalle."""
        from PIL import Image

        from ecografias.miniaturas import generar_miniatura

        chica = Image.open(generar_miniatura(self._imagen(200, 100), ancho_max=480))

        assert chica.width == 200, f"Esperado ancho 200, obtenido {chica.width}"

    def test_la_miniatura_pesa_mucho_menos_que_el_original(self):
        """ESPERADO: la miniatura ocupa menos de la mitad que el original.

        Es el punto de todo: en 3G, abrir una historia con 3 ecografías a
        resolución de diagnóstico es inviable.
        """
        from ecografias.miniaturas import generar_miniatura

        original = self._imagen(1920, 1080)
        peso_original = len(original.getvalue())
        original.seek(0)
        peso_mini = len(generar_miniatura(original, ancho_max=480).read())

        assert peso_mini < peso_original / 2, (
            f"Original {peso_original} bytes, miniatura {peso_mini}: no compensa."
        )
