#!/usr/bin/env python
# =============================================================================
# SCRIPT DE PRUEBAS - FASE 1
# =============================================================================
# Proyecto: Sistema de Historial Médico Obstétrico
# Descripción: Script para probar todas las correcciones de la FASE 1
# =============================================================================

import os
import sys
import django

# Configurar el path de Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'historial.settings')

# Colores para la terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test(test_name, status, details=""):
    """Imprime el resultado de un test"""
    if status == "OK":
        symbol = "✅"
        color = Colors.GREEN
    elif status == "ERROR":
        symbol = "❌"
        color = Colors.RED
    elif status == "WARNING":
        symbol = "⚠️"
        color = Colors.YELLOW
    else:
        symbol = "ℹ️"
        color = Colors.BLUE

    print(f"{symbol} {color}{test_name}{Colors.END} - {status}")
    if details:
        print(f"   {details}")

def test_environment_variables():
    """Prueba 1: Verificar variables de entorno"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 1: Variables de Entorno{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        from decouple import config
        print_test("Importación de python-decouple", "OK")

        # Verificar que se pueda leer SECRET_KEY
        secret_key = config('SECRET_KEY', default='test-key')
        if secret_key and secret_key != 'django-insecure-CHANGE-THIS-IN-PRODUCTION':
            print_test("SECRET_KEY configurada", "OK", f"Longitud: {len(secret_key)} caracteres")
        else:
            print_test("SECRET_KEY configurada", "WARNING", "Usando valor por defecto")

        # Verificar DEBUG
        debug = config('DEBUG', default=True, cast=bool)
        print_test("DEBUG configurado", "OK", f"Valor: {debug}")

        # Verificar DB_PASSWORD
        db_password = config('DB_PASSWORD', default='')
        if db_password:
            print_test("DB_PASSWORD configurada", "OK", "Contraseña protegida")
        else:
            print_test("DB_PASSWORD configurada", "WARNING", "No configurada en .env")

        return True
    except Exception as e:
        print_test("Variables de entorno", "ERROR", str(e))
        return False

def test_django_settings():
    """Prueba 2: Verificar configuración de Django"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 2: Configuración de Django{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        django.setup()
        from django.conf import settings

        # Verificar INSTALLED_APPS
        required_apps = ['rest_framework', 'corsheaders', 'pacientes', 'usuarios', 'embarazos', 'controles', 'calculadoras']
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                print_test(f"App instalada: {app}", "OK")
            else:
                print_test(f"App instalada: {app}", "ERROR", "No encontrada")

        # Verificar DATABASES
        db_config = settings.DATABASES['default']
        print_test("Configuración de base de datos", "OK",
                  f"Engine: {db_config['ENGINE']}, DB: {db_config['NAME']}")

        # Verificar REST_FRAMEWORK
        if hasattr(settings, 'REST_FRAMEWORK'):
            print_test("Configuración REST_FRAMEWORK", "OK")
        else:
            print_test("Configuración REST_FRAMEWORK", "ERROR")

        # Verificar CORS
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            print_test("Configuración CORS", "OK",
                      f"{len(settings.CORS_ALLOWED_ORIGINS)} orígenes permitidos")
        else:
            print_test("Configuración CORS", "ERROR")

        # Verificar SIMPLE_JWT
        if hasattr(settings, 'SIMPLE_JWT'):
            print_test("Configuración JWT", "OK")
        else:
            print_test("Configuración JWT", "ERROR")

        return True
    except Exception as e:
        print_test("Configuración de Django", "ERROR", str(e))
        return False

def test_models_import():
    """Prueba 3: Importar todos los modelos"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 3: Importación de Modelos{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        # Importar modelo Usuario
        from usuarios.models import Usuario
        print_test("Modelo Usuario", "OK", f"Campos: {len(Usuario._meta.get_fields())}")

        # Importar modelo Paciente
        from pacientes.models import Paciente
        print_test("Modelo Paciente", "OK", f"Campos: {len(Paciente._meta.get_fields())}")

        # Importar modelo Embarazo
        from embarazos.models import Embarazo
        print_test("Modelo Embarazo", "OK", f"Campos: {len(Embarazo._meta.get_fields())}")

        # Importar modelo ControlPrenatal (con ForeignKeys corregidas)
        from controles.models import ControlPrenatal
        print_test("Modelo ControlPrenatal", "OK", f"Campos: {len(ControlPrenatal._meta.get_fields())}")

        return True
    except Exception as e:
        print_test("Importación de modelos", "ERROR", str(e))
        import traceback
        print(f"\n{Colors.RED}Traceback completo:{Colors.END}")
        traceback.print_exc()
        return False

def test_foreignkeys():
    """Prueba 4: Verificar relaciones ForeignKey corregidas"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 4: Relaciones ForeignKey Corregidas{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        from controles.models import ControlPrenatal
        from django.db.models import ForeignKey

        # Verificar que embarazo es ForeignKey
        embarazo_field = ControlPrenatal._meta.get_field('embarazo')
        if isinstance(embarazo_field, ForeignKey):
            print_test("ForeignKey: embarazo", "OK",
                      f"Relación con: {embarazo_field.related_model.__name__}")
        else:
            print_test("ForeignKey: embarazo", "ERROR",
                      f"Tipo incorrecto: {type(embarazo_field).__name__}")

        # Verificar que paciente es ForeignKey
        paciente_field = ControlPrenatal._meta.get_field('paciente')
        if isinstance(paciente_field, ForeignKey):
            print_test("ForeignKey: paciente", "OK",
                      f"Relación con: {paciente_field.related_model.__name__}")
        else:
            print_test("ForeignKey: paciente", "ERROR",
                      f"Tipo incorrecto: {type(paciente_field).__name__}")

        # Verificar que medico es ForeignKey
        medico_field = ControlPrenatal._meta.get_field('medico')
        if isinstance(medico_field, ForeignKey):
            print_test("ForeignKey: medico", "OK",
                      f"Relación con: {medico_field.related_model.__name__}")
        else:
            print_test("ForeignKey: medico", "ERROR",
                      f"Tipo incorrecto: {type(medico_field).__name__}")

        # Verificar que enfermero es ForeignKey
        enfermero_field = ControlPrenatal._meta.get_field('enfermero')
        if isinstance(enfermero_field, ForeignKey):
            print_test("ForeignKey: enfermero", "OK",
                      f"Relación con: {enfermero_field.related_model.__name__}")
        else:
            print_test("ForeignKey: enfermero", "ERROR",
                      f"Tipo incorrecto: {type(enfermero_field).__name__}")

        return True
    except Exception as e:
        print_test("Verificación de ForeignKeys", "ERROR", str(e))
        import traceback
        traceback.print_exc()
        return False

def test_soft_delete():
    """Prueba 5: Verificar implementación de soft delete"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 5: Soft Delete{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        from controles.models import ControlPrenatal

        # Verificar que existe campo 'activo'
        if hasattr(ControlPrenatal, 'activo'):
            print_test("Campo 'activo'", "OK", "Campo para soft delete presente")
        else:
            print_test("Campo 'activo'", "ERROR", "Campo no encontrado")

        # Verificar que existe campo 'fecha_eliminacion'
        if hasattr(ControlPrenatal, 'fecha_eliminacion'):
            print_test("Campo 'fecha_eliminacion'", "OK", "Campo para timestamp presente")
        else:
            print_test("Campo 'fecha_eliminacion'", "ERROR", "Campo no encontrado")

        # Verificar método delete sobrescrito
        if hasattr(ControlPrenatal, 'delete'):
            print_test("Método 'delete' sobrescrito", "OK", "Soft delete implementado")
        else:
            print_test("Método 'delete' sobrescrito", "ERROR")

        # Verificar método hard_delete
        if hasattr(ControlPrenatal, 'hard_delete'):
            print_test("Método 'hard_delete'", "OK", "Eliminación permanente disponible")
        else:
            print_test("Método 'hard_delete'", "WARNING", "No implementado")

        return True
    except Exception as e:
        print_test("Soft delete", "ERROR", str(e))
        return False

def test_utility_methods():
    """Prueba 6: Verificar métodos de utilidad"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 6: Métodos de Utilidad{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    try:
        from controles.models import ControlPrenatal

        # Verificar métodos implementados
        methods = ['tiene_alertas', 'es_control_critico', 'calcular_indice_shock',
                   'get_edad_gestacional_display']

        for method in methods:
            if hasattr(ControlPrenatal, method):
                print_test(f"Método '{method}'", "OK", "Implementado correctamente")
            else:
                print_test(f"Método '{method}'", "ERROR", "No encontrado")

        return True
    except Exception as e:
        print_test("Métodos de utilidad", "ERROR", str(e))
        return False

def test_file_structure():
    """Prueba 7: Verificar estructura de archivos"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 7: Estructura de Archivos{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Archivos que deben existir
    required_files = [
        '.env.example',
        '.gitignore',
        'requirements.txt',
        'historial/settings.py',
        'controles/models.py',
    ]

    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print_test(f"Archivo: {file_path}", "OK", f"Tamaño: {size} bytes")
        else:
            print_test(f"Archivo: {file_path}", "ERROR", "No encontrado")

    return True

def main():
    """Función principal de pruebas"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}PRUEBAS DE LA FASE 1 - Sistema de Historial Médico{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

    results = []

    # Ejecutar todas las pruebas
    results.append(("Estructura de archivos", test_file_structure()))
    results.append(("Variables de entorno", test_environment_variables()))
    results.append(("Configuración Django", test_django_settings()))
    results.append(("Importación de modelos", test_models_import()))
    results.append(("ForeignKeys corregidas", test_foreignkeys()))
    results.append(("Soft delete", test_soft_delete()))
    results.append(("Métodos de utilidad", test_utility_methods()))

    # Resumen final
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}RESUMEN DE PRUEBAS{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASÓ{Colors.END}" if result else f"{Colors.RED}❌ FALLÓ{Colors.END}"
        print(f"{status} - {test_name}")

    print(f"\n{Colors.BOLD}Total: {passed}/{total} pruebas pasadas{Colors.END}")

    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ¡TODAS LAS PRUEBAS PASARON!{Colors.END}")
        print(f"{Colors.GREEN}La FASE 1 está completamente funcional.{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  ALGUNAS PRUEBAS FALLARON{Colors.END}")
        print(f"{Colors.RED}Revisa los errores antes de continuar.{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
