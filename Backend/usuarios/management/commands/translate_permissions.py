"""Translate permissions module."""
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    """Command"""
    help = "Translates system permissions to Spanish"

    def handle(self, *args, **_kwargs):
        """Handle"""
        self.stdout.write("Translating permissions...")

        # Mapping of English actions to Spanish
        action_map = {
            "add": "Crear",
            "change": "Editar",
            "delete": "Eliminar",
            "view": "Ver",
        }

        # Corrections for model names if needed
        _model_name_map = {
            "log entry": "Log de Acceso",
            "user": "Usuario",
            "permission": "Permiso",
            "group": "Grupo",
            "content type": "Tipo de Contenido",
            "session": "Sesión",
        }

        with transaction.atomic():
            count = 0
            for perm in Permission.objects.all():
                # Default logic: "Can [action] [model]"
                # We want: "[Acción] [Modelo]"

                # Check codename usually looks like "add_user", "change_patient"
                action, _model = perm.codename.split("_", 1)

                if action in action_map:
                    spanish_action = action_map[action]

                    # Try to get a nice name from the model verbose name if possible
                    # But permission name usually has the model name in English "Can add user"

                    # Let's rely on the content_type model class verbose name if available
                    ct = perm.content_type
                    model_class = ct.model_class()

                    if model_class:
                        model_name = model_class._meta.verbose_name.title()
                    else:
                        # Fallback to existing name parsing
                        # Remove "Can " and action
                        english_name = perm.name
                        for eng_act in [
                            "Can add",
                            "Can change",
                            "Can delete",
                            "Can view",
                        ]:
                            if english_name.startswith(eng_act):
                                # model part is the rest
                                # but sometimes it's "Can add log entry"
                                pass

                        # Better approach:
                        # Use the calculated model name from the ContentType
                        # This matches the user's desire for consistent naming
                        model_name = ct.name
                        # ct.name seems to be what provides "log entry", "user", etc.

                    # Manual overrides for specific tricky ones
                    if ct.model in ["logentry"]:
                        model_name = "Log de Acceso"

                    # Create the new name
                    new_name = f"{spanish_action} {model_name}"

                    # Update if different
                    if perm.name != new_name:
                        # self.stdout.write(f"Renaming '{perm.name}' -> '{new_name}'")
                        perm.name = new_name
                        perm.save()
                        count += 1

            self.stdout.write(
                self.style.SUCCESS(f"Successfully translated {count} permissions."),
            )
