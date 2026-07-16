"""=============================================================================
MODELO: AUDITORÍA Y TRAZABILIDAD COMPLETA
=============================================================================
Registra inmutablemente TODAS las acciones del sistema.
- Checksum SHA-256 por registro para detección de tampering
- Datos anteriores/nuevos en JSON para trazabilidad completa
- Usuario desnormalizado para preservar historial aunque el usuario sea eliminado
=============================================================================
"""

import hashlib

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

Usuario = get_user_model()


def _get_client_ip(request) -> str | None:
    """Extrae IP real del cliente considerando proxies."""
    if request is None:
        return None
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",", 1)[0].strip()
    return request.META.get("REMOTE_ADDR")


class RegistroAuditoria(models.Model):
    """Registro inmutable de todas las acciones del sistema.
    Mantiene compatibilidad con el nombre anterior (RegistroAuditoria).
    """

    ACCIONES = (
        # Autenticación
        ("LOGIN", "Inicio de sesión"),
        ("LOGOUT", "Cierre de sesión"),
        ("LOGIN_FALLIDO", "Intento de login fallido"),
        ("MFA_ACTIVADO", "MFA activado"),
        ("MFA_FALLIDO", "Intento MFA fallido"),
        ("MFA_DESACTIVADO", "MFA desactivado"),
        ("CUENTA_BLOQUEADA", "Cuenta bloqueada por intentos"),
        # CRUD genérico (compatibilidad legacy)
        ("crear", "Crear"),
        ("actualizar", "Actualizar"),
        ("eliminar", "Eliminar"),
        # Acciones clínicas
        ("CREAR", "Creación de registro"),
        ("EDITAR", "Modificación de registro"),
        ("VER", "Visualización de registro"),
        ("DESACTIVAR", "Desactivación (soft delete)"),
        ("ACTIVAR", "Reactivación de registro"),
        ("EXPORTAR", "Exportación de datos"),
        # IA
        ("CONSULTA_IA", "Consulta al chatbot IA"),
        ("ANALISIS_CNN", "Análisis de imagen con CNN"),
        # Administración
        ("CAMBIO_ROL", "Cambio de rol de usuario"),
        ("BACKUP", "Respaldo de base de datos"),
        ("DESACTIVAR_PACIENTE", "Desactivación de paciente"),
    )

    # ── Quién ─────────────────────────────────────────────────────────────────
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias_realizadas",
        help_text="Usuario que realizó el cambio",
        db_index=True,
    )
    # Desnormalizado para preservar historial si el usuario es eliminado
    usuario_nombre = models.CharField(max_length=200, blank=True, default="")
    usuario_rol = models.CharField(max_length=20, blank=True, default="")

    # ── Qué ───────────────────────────────────────────────────────────────────
    accion = models.CharField(max_length=30, choices=ACCIONES, db_index=True)
    modulo = models.CharField(
        max_length=100, blank=True, help_text="Módulo/modelo afectado",
    )
    registro_id = models.CharField(
        max_length=64, blank=True, help_text="ID del registro afectado",
    )

    # ── Datos antes/después ───────────────────────────────────────────────────
    datos_anteriores = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    detalle = models.TextField(blank=True)

    # ── Cuándo y dónde ────────────────────────────────────────────────────────
    fecha = models.DateTimeField(default=timezone.now, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    endpoint = models.CharField(max_length=500, blank=True)

    # ── Integridad ────────────────────────────────────────────────────────────
    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 del registro para detección de tampering",
    )

    class Meta:
        """Meta"""
        db_table = "auditoria_registros"
        ordering = ["-fecha"]
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        indexes = [
            models.Index(fields=["modulo", "-fecha"]),
            models.Index(fields=["usuario", "-fecha"]),
            models.Index(fields=["accion", "-fecha"]),
        ]

    def save(self, *args, **kwargs):
        """APPEND-ONLY: solo permite crear (INSERT), NUNCA actualizar (UPDATE).
        Si el registro ya existe (UPDATE), lanza excepción.
        """
        if self.pk is not None:
            raise PermissionError(
                "VIOLACIÓN DE SEGURIDAD: No se permite modificar registros de auditoría. "
                f"Esta acción ha sido registrada. ID del intento: {self.pk}",
            )
        if self.usuario and not self.usuario_nombre:
            self.usuario_nombre = str(self.usuario)
            self.usuario_rol = getattr(self.usuario, "rol", "")

        data_str = f"{getattr(self, 'usuario_id', '')}|{self.accion}|{self.modulo}|{self.registro_id}|{self.fecha}"
        self.checksum = hashlib.sha256(data_str.encode("utf-8")).hexdigest()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """APPEND-ONLY: prohibido eliminar registros de auditoría."""
        raise PermissionError(
            f"VIOLACIÓN DE SEGURIDAD: No se permite eliminar registros de auditoría. "
            f"Acción denegada para registro ID: {self.pk or 'nuevo'}",
        )

    def __str__(self) -> str:
        """Str"""
        nombre = self.usuario_nombre or (
            getattr(self.usuario, "email", "Sistema") if self.usuario else "Sistema"
        )
        return f"{self.accion} en {self.modulo} por {nombre} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    @property
    def usuario_nombre_completo(self) -> str:
        """Retorna el nombre del usuario (desnormalizado o desde FK)."""
        if self.usuario_nombre:
            return self.usuario_nombre
        if self.usuario:
            return str(
                getattr(self.usuario, "nombre_completo", None)
                or getattr(self.usuario, "email", "") or ""
            )
        return "Sistema"

    @property
    def cambios_resumidos(self) -> str:
        """Resumen legible de los cambios realizados."""
        accion_lower = self.accion.lower()
        if accion_lower in ("crear", "CREAR"):
            return f"Creado nuevo registro #{self.registro_id}"
        if accion_lower in ("eliminar", "DESACTIVAR", "DESACTIVAR_PACIENTE"):
            return f"Desactivado/eliminado registro #{self.registro_id}"
        if (
            accion_lower in ("actualizar", "EDITAR")
            and self.datos_anteriores
            and self.datos_nuevos
        ):
            cambios = []
            for key in (self.datos_nuevos or {}):
                anterior = self.datos_anteriores.get(key)
                nuevo = self.datos_nuevos.get(key)
                if anterior != nuevo:
                    cambios.append(f"{key}: {anterior} → {nuevo}")
            return "; ".join(cambios) if cambios else "Sin cambios detectados"
        return self.detalle or "N/A"

    @classmethod
    def registrar(
        cls,
        usuario,
        accion: str,
        modulo: str = "",
        registro_id: str = "",
        datos_anteriores=None,
        datos_nuevos=None,
        detalle: str = "",
        request=None,
    ) -> "RegistroAuditoria":
        """Método de factoría para crear registros de auditoría de forma uniforme.

        Uso:
            RegistroAuditoria.registrar(
                usuario=request.user,
                accion='DESACTIVAR_PACIENTE',
                modulo='Paciente',
                registro_id=str(paciente.id),
                detalle=f'Paciente {paciente.nombre} desactivado',
                request=request,
            )
        """
        nombre = ""
        rol = ""
        if usuario and hasattr(usuario, "nombre_completo"):
            nombre = usuario.nombre_completo
        elif usuario and hasattr(usuario, "email"):
            nombre = usuario.email
        if usuario and hasattr(usuario, "rol"):
            rol = usuario.rol

        return cls.objects.create(
            usuario=usuario
            if (usuario and hasattr(usuario, "pk") and usuario.pk)
            else None,
            usuario_nombre=nombre,
            usuario_rol=rol,
            accion=accion,
            modulo=modulo,
            registro_id=registro_id if isinstance(registro_id, str) else str(registro_id),
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            detalle=detalle,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
            endpoint=request.path if request else "",
        )
