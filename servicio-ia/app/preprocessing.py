import io
import random

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    import pydicom  # noqa: F401  # probe de disponibilidad; el uso real re-importa local en load_dicom()
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    PILImage = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


def frost_filter(image: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    if not CV2_AVAILABLE:
        return image
    sigma = 1.0
    kernel = cv2.getGaussianKernel(kernel_size, sigma)
    kernel_2d = kernel @ kernel.T
    kernel_2d = kernel_2d / kernel_2d.sum()
    return cv2.filter2D(image, -1, kernel_2d)


def clahe_equalization(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    if not CV2_AVAILABLE:
        return image
    if image.ndim == 3 and image.shape[-1] == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_chan, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        l_chan = clahe.apply(l_chan)
        lab = cv2.merge([l_chan, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    return clahe.apply(image)


def percentile_normalize(image: np.ndarray, low_pct: float = 2.0, high_pct: float = 98.0) -> np.ndarray:
    image_f = image.astype(np.float32)
    low = np.percentile(image_f, low_pct)
    high = np.percentile(image_f, high_pct)
    if high - low < 1e-6:
        return np.clip((image_f - low) / 255.0, 0.0, 1.0)
    normalized = np.clip((image_f - low) / (high - low), 0.0, 1.0)
    return (normalized * 255.0).astype(np.uint8)


def preprocess_ultrasound(image: np.ndarray) -> np.ndarray:
    img = frost_filter(image, kernel_size=5)
    img = clahe_equalization(img, clip_limit=2.0, tile_size=8)
    return percentile_normalize(img, 2.0, 98.0)


if CV2_AVAILABLE:

    def elastic_deformation(image: np.ndarray, alpha: float = 30.0, sigma: float = 4.0) -> np.ndarray:
        h, w = image.shape[:2]
        dx = np.random.randn(h, w).astype(np.float32) * alpha
        dy = np.random.randn(h, w).astype(np.float32) * alpha
        dx = cv2.GaussianBlur(dx, (0, 0), sigma)
        dy = cv2.GaussianBlur(dy, (0, 0), sigma)
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        map_x = (x + dx).astype(np.float32)
        map_y = (y + dy).astype(np.float32)
        return cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    def add_speckle_noise(image: np.ndarray, variance_range=(0.01, 0.03)) -> np.ndarray:
        noise_var = random.uniform(*variance_range)
        noise = np.random.randn(*image.shape[:2]) * np.sqrt(noise_var)
        if image.ndim == 3:
            noise = np.stack([noise] * 3, axis=-1)
        result = image.astype(np.float32) * (1.0 + noise)
        return np.clip(result, 0, 255).astype(np.uint8)

    def add_shadow(image: np.ndarray) -> np.ndarray:
        h, w = image.shape[:2]
        shadow_width = random.randint(w // 8, w // 3)
        shadow_x = random.randint(0, w - shadow_width)
        shadow_mask = np.zeros((h, w), dtype=np.float32)
        cv2.rectangle(shadow_mask, (shadow_x, 0), (shadow_x + shadow_width, h), 1.0, -1)
        shadow_mask = cv2.GaussianBlur(shadow_mask, (w // 4 | 1, h // 4 | 1), shadow_width // 2)
        alpha = random.uniform(0.2, 0.5)
        result = image.astype(np.float32) * (1.0 - alpha * shadow_mask[..., None])
        return np.clip(result, 0, 255).astype(np.uint8)

else:

    def elastic_deformation(image, alpha=30.0, sigma=4.0):
        return image

    def add_speckle_noise(image, variance_range=(0.01, 0.03)):
        return image

    def add_shadow(image):
        return image


def apply_ultrasound_augmentation(image: np.ndarray) -> np.ndarray:
    img = image.copy()
    if random.random() < 0.5:
        img = elastic_deformation(img, alpha=random.uniform(20, 40), sigma=random.uniform(3, 5))
    if random.random() < 0.4:
        img = add_speckle_noise(img, variance_range=(0.01, 0.03))
    if random.random() < 0.3:
        img = add_shadow(img)
    if random.random() < 0.5:
        angle = random.uniform(-20, 20)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    if random.random() < 0.3:
        scale = random.uniform(0.9, 1.1)
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w // 2, h // 2), 0, scale)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    if random.random() < 0.3:
        brightness = random.uniform(0.8, 1.2)
        img = np.clip(img.astype(np.float32) * brightness, 0, 255).astype(np.uint8)
    if random.random() < 0.3:
        contrast = random.uniform(0.85, 1.15)
        mean = img.mean()
        img = np.clip((img.astype(np.float32) - mean) * contrast + mean, 0, 255).astype(np.uint8)
    return img


class UltrasoundTransform:
    def __init__(self, augment: bool = False):
        self.augment = augment

    def __call__(self, image: np.ndarray) -> np.ndarray:
        img = preprocess_ultrasound(image)
        if self.augment:
            img = apply_ultrasound_augmentation(img)
        img = cv2.resize(img, (384, 384))
        return img.astype(np.float32) / 255.0


class PILImagePreprocessor:
    @staticmethod
    def load_image(file_content: bytes, file_extension: str) -> np.ndarray:
        if file_extension.lower() in [".dicom", ".dcm"]:
            return PILImagePreprocessor.load_dicom(file_content)
        return PILImagePreprocessor.load_standard_image(file_content)

    @staticmethod
    def load_dicom(file_content: bytes) -> np.ndarray:
        if not PYDICOM_AVAILABLE:
            raise ValueError("pydicom no instalado")
        try:
            import pydicom
            dicom = pydicom.dcmread(io.BytesIO(file_content))
            image = dicom.pixel_array
            if CV2_AVAILABLE:
                image = cv2.normalize(image, np.empty_like(image), 0, 255, cv2.NORM_MINMAX)
            else:
                mn, mx = image.min(), image.max()
                image = ((image - mn) / max(mx - mn, 1) * 255).astype(np.uint8)
            image = image.astype(np.uint8)
            if len(image.shape) == 2:
                image = np.stack([image] * 3, axis=-1)
            return image
        except Exception as e:
            raise ValueError(f"Error al leer DICOM: {e!s}") from e

    @staticmethod
    def load_standard_image(file_content: bytes) -> np.ndarray:
        if not PIL_AVAILABLE:
            raise ValueError("Pillow no instalado")
        try:
            img = PILImage.open(io.BytesIO(file_content))
            return np.array(img.convert("RGB"))
        except Exception as e:
            raise ValueError(f"Error al leer imagen: {e!s}") from e

    @staticmethod
    def preprocess_for_classification(image: np.ndarray, target_size: tuple = (384, 384)) -> np.ndarray:
        img = preprocess_ultrasound(image)
        if CV2_AVAILABLE:
            img = cv2.resize(img, target_size)
        img = img.astype(np.float32) / 255.0
        return np.expand_dims(img, axis=0)

    @staticmethod
    def preprocess_for_segmentation(image: np.ndarray, target_size: tuple = (256, 256)) -> np.ndarray:
        if CV2_AVAILABLE:
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            image = cv2.resize(image, target_size)
        image = image.astype(np.float32) / 255.0
        image = np.expand_dims(image, axis=0)
        return np.expand_dims(image, axis=-1)

    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        return clahe_equalization(image) if CV2_AVAILABLE else image

    @staticmethod
    def denoise_image(image: np.ndarray) -> np.ndarray:
        if not CV2_AVAILABLE:
            return image
        try:
            return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        except Exception:
            return image

    # Por debajo de esto la imagen se sobre-amplia al redimensionar a 384x384
    # y pierde detalle real (no es una recomendacion arbitraria: es el tamaño
    # de entrada del modelo).
    RECOMMENDED_MIN_DIM = 256

    # Saturacion HSV mediana (0-255). Medido contra el propio dataset de
    # entrenamiento (datasets_pathology/train/, 25 imagenes x 15 clases):
    # la saturacion mediana varia mucho por clase, incluso en ecografias
    # reales — atresia_duodenal (media 216), muerte_fetal (media 168) y
    # oligohidramnios (media 107) tienen saturacion alta de forma legitima
    # (artefactos de compresion / Doppler color). Esos casos de saturacion
    # alta por senal real quedan protegidos en
    # routes.py:_apply_safety_checks via "señal_real_detectada" (si el
    # modelo ve >=40% de probabilidad en alguna clase real, no se rechaza
    # por color sin importar el umbral de aca abajo). El umbral de esta
    # funcion solo necesita cubrir el caso SIN esa proteccion: imagen
    # ambigua para el modelo (baja_confianza) Y con colores claramente
    # fotograficos. Verificado contra una foto real no-ecografica de
    # prueba (saturacion ~47) que SI debe seguir rechazandose: 40 sigue
    # capturandola sin heredar el problema del umbral anterior (35), que
    # rechazaba hasta 16% de imagenes reales de embarazo_multiple sin
    # señal de respaldo.
    NON_ULTRASOUND_SATURATION_THRESHOLD = 40.0

    @staticmethod
    def validate_ultrasound(image: np.ndarray) -> dict:
        quality = PILImagePreprocessor.calculate_image_quality(image)
        color = PILImagePreprocessor.looks_like_ultrasound(image)

        errores = []
        # Solo rechazar resolucion extremadamente baja (menos de 100px)
        h, w = image.shape[:2]
        if min(h, w) < 100:
            errores.append("resolucion_insuficiente")
        # Solo rechazar si es extremadamente borrosa (sharpness < 1)
        if quality.get("sharpness", 100) < 1.0:
            errores.append("imagen_muy_borrosa")
        # Rechazar por color solo si la saturacion es muy alta.
        # looks_like_ultrasound devuelve saturacion_media normalizado [0-1]
        # (raw = valor * 255). Umbral raw ~100 → 0.392 normalizado.
        sat = color.get("saturacion_media")
        if sat is not None and sat > 0.392:
            errores.append("no_parece_ecografia")

        es_valida = len(errores) == 0

        return {
            "es_valida": es_valida,
            "errores": errores,
            "motivo": "; ".join(errores) if errores else "",
            "calidad": quality,
            "color": color,
        }

    @staticmethod
    def calculate_image_quality(image: np.ndarray) -> dict:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if CV2_AVAILABLE else np.mean(image, axis=2).astype(np.uint8)
        else:
            gray = image
        if CV2_AVAILABLE:
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        else:
            gy = np.diff(gray.astype(np.float64), axis=0)
            gx = np.diff(gray.astype(np.float64), axis=1)
            laplacian_var = float(np.var(gy) + np.var(gx))
        contrast = float(gray.std())
        brightness = float(gray.mean())
        quality = "excelente" if laplacian_var > 100 and contrast > 50 else "buena" if laplacian_var > 50 and contrast > 30 else "aceptable" if laplacian_var > 20 else "mala"

        h, w = image.shape[:2]
        min_dim = min(h, w)
        resolucion_baja = min_dim < PILImagePreprocessor.RECOMMENDED_MIN_DIM

        return {
            "sharpness": laplacian_var,
            "contrast": contrast,
            "brightness": brightness,
            "quality": quality,
            "ancho_px": int(w),
            "alto_px": int(h),
            "resolucion_baja": resolucion_baja,
            "resolucion_minima_recomendada_px": PILImagePreprocessor.RECOMMENDED_MIN_DIM,
        }

    @staticmethod
    def looks_like_ultrasound(image: np.ndarray) -> dict:
        """Heuristica de color (no ML): las ecografias son casi en escala de
        grises. Sirve de red de seguridad para detectar fotos/imagenes que
        claramente no son una ecografia, mientras el modelo no tenga datos
        de entrenamiento para la clase 'no_ecografia'.

        Usa la MEDIANA de saturacion por pixel, no el promedio. Equipos de
        ultrasonido reales suelen grabar overlays de color (calipers de
        medicion amarillos, texto de mediciones, logos pequenos) sobre el
        contenido anatomico en escala de grises. Esos pocos pixeles muy
        saturados pueden arrastrar el PROMEDIO de toda la imagen por encima
        del umbral aunque la imagen sea, en la inmensa mayoria de sus
        pixeles, una ecografia real — la mediana es robusta a ese tipo de
        outliers minoritarios.
        """
        if not CV2_AVAILABLE or image.ndim != 3:
            return {"parece_ecografia": True, "saturacion_media": None}
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        median_sat = float(np.median(hsv[..., 1]))
        return {
            "parece_ecografia": median_sat < PILImagePreprocessor.NON_ULTRASOUND_SATURATION_THRESHOLD,
            "saturacion_media": round(median_sat / 255.0, 3),
        }
