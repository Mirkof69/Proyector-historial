"""Fields module."""
import base64
import hashlib
import hmac
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings
from django.db import models

# Prefijo del sobre versionado: valores AES-256-GCM empiezan con "v2:".
# Los valores Fernet legados (v1) NO tienen prefijo — asi se distinguen sin
# necesitar una migracion de esquema, y ambos formatos se pueden desencriptar
# indefinidamente (ver EncryptedFieldMixin.decrypt_value).
_V2_PREFIX = "v2:"

_cipher_cache: Fernet | None = None
_aesgcm_key_cache: bytes | None = None


def _raw_key_bytes() -> bytes:
    raw_key = getattr(settings, "ENCRYPTION_KEY", None)
    if not raw_key:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            "ENCRYPTION_KEY debe estar definido en .env. "
            'Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
        )
    return raw_key.encode("utf-8") if isinstance(raw_key, str) else raw_key


def get_cipher() -> Fernet:
    """Retorna una instancia Fernet con clave derivada mediante HKDF-SHA256.

    Formato legado (v1, sin prefijo). Internamente Fernet usa AES-128-CBC +
    HMAC-SHA256, NO AES-256 (independientemente del tamaño de la clave de
    entrada) — por eso existe get_aesgcm_key() para AES-256 real.
    La instancia se cachea en memoria para evitar recalcular HKDF en cada acceso.
    """
    global _cipher_cache
    if _cipher_cache is not None:
        return _cipher_cache

    raw_key_bytes = _raw_key_bytes()
    salt_str = getattr(settings, "ENCRYPTION_SALT", "perinatal-fernet-salt-v1")
    salt = salt_str.encode("utf-8") if isinstance(salt_str, str) else salt_str

    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"fernet-field-encryption-v1",
    )
    derived = kdf.derive(raw_key_bytes)
    _cipher_cache = Fernet(base64.urlsafe_b64encode(derived))
    return _cipher_cache


def get_aesgcm_key() -> bytes:
    """Deriva una clave AES-256 real (32 bytes) independiente de la clave
    Fernet (info distinto en el HKDF), cacheada en memoria."""
    global _aesgcm_key_cache
    if _aesgcm_key_cache is not None:
        return _aesgcm_key_cache

    raw_key_bytes = _raw_key_bytes()
    salt_str = getattr(settings, "ENCRYPTION_SALT", "perinatal-fernet-salt-v1")
    salt = salt_str.encode("utf-8") if isinstance(salt_str, str) else salt_str

    kdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=b"aes256gcm-field-encryption-v2",
    )
    _aesgcm_key_cache = kdf.derive(raw_key_bytes)
    return _aesgcm_key_cache


def _aesgcm_encrypt(plaintext: str) -> str:
    """AES-256-GCM real: nonce aleatorio de 96 bits por operacion,
    nonce||ciphertext+tag en base64, con prefijo de version."""
    aesgcm = AESGCM(get_aesgcm_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    blob = base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")
    return _V2_PREFIX + blob


def _aesgcm_decrypt(value: str) -> str:
    blob = base64.urlsafe_b64decode(value[len(_V2_PREFIX):])
    nonce, ciphertext = blob[:12], blob[12:]
    aesgcm = AESGCM(get_aesgcm_key())
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def compute_search_hash(value: str) -> str:
    """HMAC-SHA256 del valor en texto plano para búsquedas/unicidad.
    Permite comprobar unicidad de CI sin exponer el valor real.
    """
    secret = getattr(settings, "ENCRYPTION_KEY", None)
    if not secret:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("ENCRYPTION_KEY debe estar definido para compute_search_hash")
    if isinstance(secret, bytes):
        secret = secret.decode("utf-8")
    return hmac.new(
        secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256,
    ).hexdigest()


logger = logging.getLogger(__name__)


class EncryptedFieldMixin:
    """Mixin que encripta/desencripta datos con Fernet (v1, legado) o
    AES-256-GCM (v2, real). El modo de ESCRITURA se elige por
    settings.ENCRYPTION_CIPHER_MODE ("fernet" por defecto, "aes256gcm" para
    AES-256 real); la LECTURA siempre detecta el formato por el prefijo "v2:"
    y soporta ambos indefinidamente, sin necesitar migrar todo de una vez.
    Si la encriptación falla, se loguea el error y se retorna el valor original
    para no bloquear operaciones críticas.
    """
    def encrypt_value(self, value):
        if not value:
            return value
        try:
            modo = getattr(settings, "ENCRYPTION_CIPHER_MODE", "fernet")
            if modo == "aes256gcm":
                return _aesgcm_encrypt(str(value))
            return get_cipher().encrypt(str(value).encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error("Error de encriptación (guardando valor original): %s", e)
            return value

    def decrypt_value(self, value):
        if not value:
            return value
        try:
            if value.startswith(_V2_PREFIX):
                return _aesgcm_decrypt(value)
            return get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.warning("Error de desencriptacion (retornando valor almacenado): %s", e)
            return value


class EncryptedCharField(EncryptedFieldMixin, models.CharField):
    """Encryptedcharfield"""
    def get_prep_value(self, value):
        return self.encrypt_value(super().get_prep_value(value))

    def from_db_value(self, value, _expression, _connection):
        return self.decrypt_value(value)


class EncryptedEmailField(EncryptedFieldMixin, models.EmailField):
    """Encryptedemailfield"""
    def get_prep_value(self, value):
        return self.encrypt_value(super().get_prep_value(value))

    def from_db_value(self, value, _expression, _connection):
        return self.decrypt_value(value)


class EncryptedTextField(EncryptedFieldMixin, models.TextField):
    """Encryptedtextfield"""
    def get_prep_value(self, value):
        return self.encrypt_value(super().get_prep_value(value))

    def from_db_value(self, value, _expression, _connection):
        return self.decrypt_value(value)
