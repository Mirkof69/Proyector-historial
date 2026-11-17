"""Código de 6 dígitos de Google Authenticator (TOTP, RFC 6238) a partir del secreto guardado en .env."""
from __future__ import annotations

import pyotp


def codigo(secreto: str) -> str:
    if not secreto:
        raise RuntimeError("Falta el secreto TOTP del rol en .env (QA_ADMIN_TOTP_SECRET / QA_MEDICO_TOTP_SECRET).")
    return pyotp.TOTP(secreto).now()
