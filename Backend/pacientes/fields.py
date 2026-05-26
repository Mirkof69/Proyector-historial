"""Fields module."""
import base64
import hashlib
import hmac

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings
from django.db import models


def get_cipher() -> Fernet:
    """Retorna una instancia Fernet con clave derivada mediante HKDF-SHA256.

    Producción: requiere ENCRYPTION_KEY en .env (clave maestra en texto plano o base64).
    Desarrollo: fallback al SECRET_KEY con advertencia — NUNCA usar en producción.

    HKDF garantiza que la clave Fernet tenga entropía uniforme de 32 bytes
    independientemente de la longitud o formato de ENCRYPTION_KEY.
    """
    raw_key = getattr(settings, "ENCRYPTION_KEY", None)

    if raw_key:
        if isinstance(raw_key, str):
            raw_key_bytes = raw_key.encode("utf-8")
        else:
            raw_key_bytes = raw_key

        salt_str = getattr(settings, "ENCRYPTION_SALT", "perinatal-fernet-salt-v1")
        salt = salt_str.encode("utf-8") if isinstance(salt_str, str) else salt_str

        # HKDF-SHA256: deriva 32 bytes de alta entropía desde la clave maestra
        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"fernet-field-encryption-v1",
        )
        derived = kdf.derive(raw_key_bytes)
        return Fernet(base64.urlsafe_b64encode(derived))

    # Fallback desarrollo: verificar que no estamos en producción
    from django.core.exceptions import ImproperlyConfigured

    if not getattr(settings, "DEBUG", True):
        raise ImproperlyConfigured(
            "ENCRYPTION_KEY debe estar definido en .env para entornos de producción. "
            'Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"',
        )

    import logging

    logging.getLogger(__name__).warning(
        "ENCRYPTION_KEY no definida — usando fallback de SECRET_KEY (SOLO DESARROLLO)",
    )
    key = settings.SECRET_KEY.encode("utf-8")[:32].ljust(32, b"=")
    return Fernet(base64.urlsafe_b64encode(key))


def compute_search_hash(value: str) -> str:
    """HMAC-SHA256 del valor en texto plano para búsquedas/unicidad.
    Permite comprobar unicidad de CI sin exponer el valor real.
    Usar ENCRYPTION_KEY como secret del HMAC (o SECRET_KEY como fallback).
    """
    secret = getattr(settings, "ENCRYPTION_KEY", None) or settings.SECRET_KEY
    if isinstance(secret, bytes):
        secret = secret.decode("utf-8")
    return hmac.new(
        secret.encode("utf-8"), value.encode("utf-8"), hashlib.sha256,
    ).hexdigest()


class EncryptedCharField(models.CharField):
    """Encryptedcharfield"""
    def get_prep_value(self, value):
        """Get prep value"""
        value = super().get_prep_value(value)
        if value:
            try:
                return get_cipher().encrypt(str(value).encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value

    def from_db_value(self, value, _expression, _connection):
        """From db value"""
        if value:
            try:
                return get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value


class EncryptedEmailField(models.EmailField):
    """Encryptedemailfield"""
    def get_prep_value(self, value):
        """Get prep value"""
        value = super().get_prep_value(value)
        if value:
            try:
                return get_cipher().encrypt(str(value).encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value

    def from_db_value(self, value, _expression, _connection):
        """From db value"""
        if value:
            try:
                return get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value


class EncryptedTextField(models.TextField):
    """Encryptedtextfield"""
    def get_prep_value(self, value):
        """Get prep value"""
        value = super().get_prep_value(value)
        if value:
            try:
                return get_cipher().encrypt(str(value).encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value

    def from_db_value(self, value, _expression, _connection):
        """From db value"""
        if value:
            try:
                return get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
            except Exception:
                return value
        return value
