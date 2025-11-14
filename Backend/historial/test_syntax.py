#!/usr/bin/env python
# =============================================================================
# SCRIPT DE PRUEBAS DE SINTAXIS - FASE 1
# =============================================================================
# Verifica la sintaxis de Python de todos los archivos modificados
# =============================================================================

import os
import sys
import ast
import json

# Colores
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_test(test_name, status, details=""):
    """Imprime resultado de test"""
    if status == "OK":
        symbol = "✅"
        color = Colors.GREEN
    elif status == "ERROR":
        symbol = "❌"
        color = Colors.RED
    else:
        symbol = "⚠️"
        color = Colors.YELLOW

    print(f"{symbol} {color}{test_name}{Colors.END} - {status}")
    if details:
        print(f"   {details}")

def check_python_syntax(file_path):
    """Verifica la sintaxis de un archivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"Línea {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)

def count_lines(file_path):
    """Cuenta las líneas de un archivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def check_file_content(file_path, keywords):
    """Verifica que un archivo contenga ciertas palabras clave"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        found = []
        for keyword in keywords:
            if keyword in content:
                found.append(keyword)
        return found
    except:
        return []

def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}PRUEBAS DE SINTAXIS Y ESTRUCTURA - FASE 1{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    results = {
        'total_tests': 0,
        'passed': 0,
        'failed': 0
    }

    # =========================================================================
    # PRUEBA 1: Verificar estructura de archivos
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 1: Estructura de Archivos{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    files_to_check = {
        '.env.example': 'Archivo de ejemplo de variables de entorno',
        '.gitignore': 'Archivo de exclusiones de Git',
        'requirements.txt': 'Dependencias de Python',
        'historial/settings.py': 'Configuración de Django',
        'controles/models.py': 'Modelo de controles prenatales',
    }

    for file_path, description in files_to_check.items():
        results['total_tests'] += 1
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            lines = count_lines(full_path)
            print_test(f"{file_path}", "OK",
                      f"{description} ({lines} líneas, {size} bytes)")
            results['passed'] += 1
        else:
            print_test(f"{file_path}", "ERROR", "Archivo no encontrado")
            results['failed'] += 1

    # =========================================================================
    # PRUEBA 2: Verificar sintaxis de Python
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 2: Sintaxis de Python{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    python_files = [
        'historial/settings.py',
        'controles/models.py',
        'usuarios/models.py',
        'pacientes/models.py',
        'embarazos/models.py',
        'calculadoras/calculos_obstetricos.py',
    ]

    for file_path in python_files:
        results['total_tests'] += 1
        full_path = os.path.join(base_dir, file_path)
        if os.path.exists(full_path):
            valid, error = check_python_syntax(full_path)
            if valid:
                lines = count_lines(full_path)
                print_test(f"Sintaxis: {file_path}", "OK", f"{lines} líneas válidas")
                results['passed'] += 1
            else:
                print_test(f"Sintaxis: {file_path}", "ERROR", error)
                results['failed'] += 1
        else:
            print_test(f"Sintaxis: {file_path}", "ERROR", "Archivo no encontrado")
            results['failed'] += 1

    # =========================================================================
    # PRUEBA 3: Verificar contenido de settings.py
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 3: Contenido de settings.py{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    settings_keywords = [
        'python-decouple',
        'config(',
        'SECRET_KEY',
        'DB_PASSWORD',
        'DATABASES',
        'REST_FRAMEWORK',
        'SIMPLE_JWT',
        'CORS_ALLOWED_ORIGINS',
    ]

    results['total_tests'] += 1
    settings_path = os.path.join(base_dir, 'historial/settings.py')
    found = check_file_content(settings_path, settings_keywords)

    if len(found) >= 6:
        print_test("Configuraciones en settings.py", "OK",
                  f"Encontradas {len(found)}/{len(settings_keywords)} configuraciones clave")
        for keyword in found[:5]:
            print(f"      - {keyword}")
        results['passed'] += 1
    else:
        print_test("Configuraciones en settings.py", "ERROR",
                  f"Solo {len(found)}/{len(settings_keywords)} configuraciones encontradas")
        results['failed'] += 1

    # =========================================================================
    # PRUEBA 4: Verificar correcciones en controles/models.py
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 4: ForeignKeys en controles/models.py{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    controles_keywords = [
        'ForeignKey',
        'embarazo = models.ForeignKey',
        'medico = models.ForeignKey',
        'enfermero = models.ForeignKey',
        'soft delete',
        'activo = models.BooleanField',
        'def tiene_alertas',
        'def es_control_critico',
    ]

    results['total_tests'] += 1
    controles_path = os.path.join(base_dir, 'controles/models.py')
    found = check_file_content(controles_path, controles_keywords)

    if len(found) >= 6:
        print_test("ForeignKeys y funcionalidades", "OK",
                  f"Encontradas {len(found)}/{len(controles_keywords)} implementaciones")
        for keyword in found:
            print(f"      - {keyword}")
        results['passed'] += 1
    else:
        print_test("ForeignKeys y funcionalidades", "ERROR",
                  f"Solo {len(found)}/{len(controles_keywords)} implementaciones encontradas")
        results['failed'] += 1

    # =========================================================================
    # PRUEBA 5: Verificar requirements.txt
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 5: Dependencias en requirements.txt{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    required_packages = [
        'Django',
        'djangorestframework',
        'psycopg2',
        'python-decouple',
        'django-cors-headers',
        'djangorestframework-simplejwt',
        'django-redis',
    ]

    results['total_tests'] += 1
    requirements_path = os.path.join(base_dir, 'requirements.txt')
    found = check_file_content(requirements_path, required_packages)

    if len(found) >= 5:
        print_test("Dependencias esenciales", "OK",
                  f"Encontradas {len(found)}/{len(required_packages)} dependencias")
        for pkg in found:
            print(f"      - {pkg}")
        results['passed'] += 1
    else:
        print_test("Dependencias esenciales", "ERROR",
                  f"Solo {len(found)}/{len(required_packages)} dependencias encontradas")
        results['failed'] += 1

    # =========================================================================
    # PRUEBA 6: Verificar .env.example
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}PRUEBA 6: Variables en .env.example{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    env_vars = [
        'SECRET_KEY',
        'DEBUG',
        'DB_NAME',
        'DB_PASSWORD',
        'REDIS_URL',
        'JWT_ACCESS_TOKEN_LIFETIME',
    ]

    results['total_tests'] += 1
    env_path = os.path.join(base_dir, '.env.example')
    found = check_file_content(env_path, env_vars)

    if len(found) >= 4:
        print_test("Variables de entorno documentadas", "OK",
                  f"Encontradas {len(found)}/{len(env_vars)} variables")
        results['passed'] += 1
    else:
        print_test("Variables de entorno documentadas", "ERROR",
                  f"Solo {len(found)}/{len(env_vars)} variables encontradas")
        results['failed'] += 1

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}RESUMEN DE PRUEBAS{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

    percentage = (results['passed'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0

    print(f"Total de pruebas: {results['total_tests']}")
    print(f"{Colors.GREEN}Pasadas: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Falladas: {results['failed']}{Colors.END}")
    print(f"Porcentaje de éxito: {percentage:.1f}%\n")

    if results['failed'] == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ¡TODAS LAS PRUEBAS PASARON!{Colors.END}")
        print(f"{Colors.GREEN}La FASE 1 está lista. Puedes continuar con la FASE 2.{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  ALGUNAS PRUEBAS FALLARON{Colors.END}")
        print(f"{Colors.YELLOW}Revisa los errores antes de continuar.{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
