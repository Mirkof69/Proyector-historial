"""Preprocesamiento de imágenes médicas
"""

import io

import numpy as np

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pydicom

    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False


class ImagePreprocessor:
    """Procesador de imágenes médicas"""

    @staticmethod
    def load_image(file_content: bytes, file_extension: str) -> np.ndarray:
        """Carga una imagen desde bytes

        Args:
            file_content: Contenido del archivo en bytes
            file_extension: Extensión del archivo (.jpg, .dicom, etc)

        Returns:
            Imagen como array numpy

        """
        if file_extension.lower() in [".dicom", ".dcm"]:
            return ImagePreprocessor.load_dicom(file_content)
        return ImagePreprocessor.load_standard_image(file_content)

    @staticmethod
    def load_dicom(file_content: bytes) -> np.ndarray:
        """Carga imagen DICOM"""
        if not PYDICOM_AVAILABLE:
            raise ValueError("pydicom no instalado. Instale con: pip install pydicom")
        try:
            # Leer DICOM
            dicom = pydicom.dcmread(io.BytesIO(file_content))
            image = dicom.pixel_array

            # Normalizar a 0-255
            if CV2_AVAILABLE:
                image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
            else:
                mn, mx = image.min(), image.max()
                image = ((image - mn) / max(mx - mn, 1) * 255).astype(np.uint8)
            image = image.astype(np.uint8)

            # Convertir a RGB si es escala de grises
            if len(image.shape) == 2:
                if CV2_AVAILABLE:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                else:
                    image = np.stack([image] * 3, axis=-1)

            return image
        except Exception as e:
            raise ValueError(f"Error al leer DICOM: {e!s}") from e

    @staticmethod
    def load_standard_image(file_content: bytes) -> np.ndarray:
        """Carga imagen estándar (JPG, PNG, etc)"""
        if not PIL_AVAILABLE:
            raise ValueError("Pillow no instalado. Instale con: pip install Pillow")
        try:
            image = Image.open(io.BytesIO(file_content))
            image = image.convert("RGB")
            return np.array(image)
        except Exception as e:
            raise ValueError(f"Error al leer imagen: {e!s}") from e

    @staticmethod
    def preprocess_for_classification(
        image: np.ndarray, target_size: tuple[int, int] = (384, 384),
    ) -> np.ndarray:
        """Preprocesa imagen para clasificación CNN

        Args:
            image: Imagen como array numpy
            target_size: Tamaño objetivo (alto, ancho)

        Returns:
            Imagen preprocesada

        """
        if CV2_AVAILABLE:
            image = cv2.resize(image, target_size)
        elif PIL_AVAILABLE:
            img_pil = Image.fromarray(image.astype(np.uint8)).resize(target_size)
            image = np.array(img_pil)
        else:
            raise RuntimeError(
                "Se requiere opencv-python-headless o Pillow para redimensionar imágenes",
            )

        # Normalizar a [0, 1]
        image = image.astype(np.float32) / 255.0

        # Expandir dimensiones para batch
        image = np.expand_dims(image, axis=0)

        return image

    @staticmethod
    def preprocess_for_segmentation(
        image: np.ndarray, target_size: tuple[int, int] = (256, 256),
    ) -> np.ndarray:
        """Preprocesa imagen para segmentación U-Net

        Args:
            image: Imagen como array numpy
            target_size: Tamaño objetivo (alto, ancho)

        Returns:
            Imagen preprocesada en escala de grises

        """
        if CV2_AVAILABLE:
            # Convertir a escala de grises
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            image = cv2.resize(image, target_size)
        elif PIL_AVAILABLE:
            img_pil = Image.fromarray(image.astype(np.uint8))
            if img_pil.mode != "L":
                img_pil = img_pil.convert("L")
            img_pil = img_pil.resize(target_size)
            image = np.array(img_pil)
        else:
            raise RuntimeError(
                "Se requiere opencv-python-headless o Pillow para preprocesar imágenes",
            )

        # Normalizar
        image = image.astype(np.float32) / 255.0

        # Expandir dimensiones: (1, height, width, 1)
        image = np.expand_dims(image, axis=0)
        image = np.expand_dims(image, axis=-1)

        return image

    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """Mejora la calidad de la imagen médica (CLAHE).
        Fallback: devuelve imagen original si cv2 no está disponible.
        """
        if not CV2_AVAILABLE:
            return image  # Fallback sin transformación
        try:
            if len(image.shape) == 3:
                lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l = clahe.apply(l)
                lab = cv2.merge([l, a, b])
                enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            else:
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(image)
            return enhanced
        except Exception:
            return image

    @staticmethod
    def denoise_image(image: np.ndarray) -> np.ndarray:
        """Reduce ruido en la imagen.
        Fallback: devuelve imagen original si cv2 no está disponible.
        """
        if not CV2_AVAILABLE:
            return image
        try:
            if len(image.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
            else:
                denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            return denoised
        except Exception:
            return image

    @staticmethod
    def calculate_image_quality(image: np.ndarray) -> dict:
        """Calcula métricas de calidad de la imagen.
        Usa cv2 si disponible, fallback a numpy puro.
        """
        # Convertir a escala de grises
        if len(image.shape) == 3:
            if CV2_AVAILABLE:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = np.mean(image, axis=2).astype(np.uint8)
        else:
            gray = image

        # Calcular nitidez (varianza del Laplaciano)
        if CV2_AVAILABLE:
            laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        else:
            # Aproximación con filtro de diferencias finitas (numpy)
            gy = np.diff(gray.astype(np.float64), axis=0)
            gx = np.diff(gray.astype(np.float64), axis=1)
            laplacian_var = float(np.var(gy) + np.var(gx))

        # Calcular contraste y brillo
        contrast = float(gray.std())
        brightness = float(gray.mean())

        # Clasificar calidad
        if laplacian_var > 100 and contrast > 50:
            quality = "excelente"
        elif laplacian_var > 50 and contrast > 30:
            quality = "buena"
        elif laplacian_var > 20:
            quality = "aceptable"
        else:
            quality = "mala"

        return {
            "sharpness": laplacian_var,
            "contrast": contrast,
            "brightness": brightness,
            "quality": quality,
        }
