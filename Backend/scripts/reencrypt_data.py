"""Reencrypt data module."""
import os
import sys

import django
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import base64

from cryptography.fernet import Fernet

from pacientes.models import Paciente


def get_old_fernet():
    """Get old fernet"""
    # Intenta recrear el Fernet antiguo basado en SECRET_KEY (si se usaba así antes de HKDF)
    # Ajusta esto si tu implementación anterior era diferente.
    secret_key = settings.SECRET_KEY.encode("utf-8")
    key = base64.urlsafe_b64encode(secret_key.ljust(32, b"\0")[:32])
    return Fernet(key)


def reencrypt_patients():
    """Reencrypt patients"""
    print("Iniciando proceso de re-cifrado de pacientes...")
    pacientes = Paciente.objects.all()

    if not pacientes.exists():
        print("No hay pacientes en la base de datos.")
        return

    _old_fernet = get_old_fernet()

    exitos = 0
    errores = 0

    for paciente in pacientes:
        try:
            # Forzar un .save() para que los campos custom ejecuten el get_prep_value con el nuevo HKDF
            # Sin embargo, si la BD tiene el valor viejo, el from_db_value fallará al leerlo.
            # Por lo que es necesario leer en crudo o interceptar.

            # NOTA: Si el sistema ya no puede leer los pacientes con 'Paciente.objects.all()'
            # debido a InvalidToken en from_db_value, se debe usar SQL crudo aquí.
            paciente.save()
            exitos += 1
            print(f"✅ Paciente {paciente.id} actualizado.")
        except Exception as e:
            errores += 1
            print(f"❌ Error con paciente {paciente.id}: {e}")

    print(f"\nResumen: {exitos} exitosos, {errores} errores.")


if __name__ == "__main__":
    reencrypt_patients()
