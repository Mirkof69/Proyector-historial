# from pacientes.models import Paciente  #  CIRCULAR IMPORT FIX
"""Utils module."""
# from usuarios.models import Usuario  #  CIRCULAR IMPORT FIX
# from embarazos.models import Embarazo  #  CIRCULAR IMPORT FIX
from django.db import connection


class OpcionesDinamicas:
    """Clase para manejar opciones dinámicas de dropdowns"""

    @staticmethod
    def obtener_tipos_reporte():
        """Obtiene todos los tipos de reporte disponibles"""
        from .models import TipoReporte

        return TipoReporte.objects.filter(activo=True).values_list("id", "nombre")

    @staticmethod
    def obtener_pacientes_activos():
        """Obtiene pacientes activos con formato nombre completo"""
        try:
            # ✅ LAZY IMPORT para evitar circular import
            from pacientes.models import Paciente

            pacientes = Paciente.objects.filter(activo=True)
            opciones = []
            for p in pacientes:
                nombre_completo = f"{p.nombre} {p.apellido} (ID: {p.id})"
                opciones.append((p.id, nombre_completo))
            return opciones
        except Exception:
            return [(None, "Sin pacientes disponibles")]

    @staticmethod
    def obtener_usuarios_medicos():
        """Obtiene usuarios que son médicos"""
        try:
            # ✅ LAZY IMPORT para evitar circular import
            from usuarios.models import Usuario

            medicos = Usuario.objects.filter(rol="medico", activo=True)
            opciones = []
            for m in medicos:
                nombre_completo = f"Dr. {m.nombre} {m.apellido} (ID: {m.id})"
                opciones.append((m.id, nombre_completo))
            return opciones
        except Exception:
            return [(None, "Sin médicos disponibles")]

    @staticmethod
    def obtener_embarazos_activos():
        """Obtiene embarazos activos"""
        try:
            # ✅ LAZY IMPORT para evitar circular import
            from embarazos.models import Embarazo

            embarazos = Embarazo.objects.filter(activo=True)
            opciones = []
            for e in embarazos:
                descripcion = f"Embarazo ID: {e.id} - Paciente: {e.paciente_id} - {e.fecha_inicio}"
                opciones.append((e.id, descripcion))
            return opciones
        except Exception:
            return [(None, "Sin embarazos disponibles")]

    @staticmethod
    def obtener_servicios_medicos():
        """Obtiene lista de servicios médicos disponibles"""
        servicios = [
            ("ginecologia", "Ginecología"),
            ("obstetricia", "Obstetricia"),
            ("ecografia", "Ecografía"),
            ("laboratorio", "Laboratorio"),
            ("consulta_externa", "Consulta Externa"),
            ("emergencias", "Emergencias"),
            ("cirugia", "Cirugía"),
        ]
        return servicios

    @staticmethod
    def ejecutar_consulta_kpi(consulta_sql):
        """Ejecuta consulta SQL para KPIs de forma segura"""
        if not consulta_sql or consulta_sql.strip() == "":
            return 0

        try:
            with connection.cursor() as cursor:
                cursor.execute(consulta_sql)
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error ejecutando consulta KPI: {e}")
            return 0

    @staticmethod
    def obtener_consultas_predefinidas():
        """Obtiene consultas SQL predefinidas para KPIs"""
        consultas = [
            (
                "pacientes_total",
                "Total de Pacientes",
                "SELECT COUNT(*) FROM pacientes_paciente WHERE activo = true",
            ),
            (
                "embarazos_activos",
                "Embarazos Activos",
                "SELECT COUNT(*) FROM embarazos_embarazo WHERE activo = true",
            ),
            (
                "controles_mes",
                "Controles Este Mes",
                "SELECT COUNT(*) FROM controles_controlprenatal WHERE fecha_control >= DATE_TRUNC('month', CURRENT_DATE)",
            ),
            (
                "ecografias_mes",
                "Ecografías Este Mes",
                "SELECT COUNT(*) FROM ecografias_ecografia WHERE fecha_ecografia >= DATE_TRUNC('month', CURRENT_DATE)",
            ),
            (
                "partos_mes",
                "Partos Este Mes",
                "SELECT COUNT(*) FROM partos_parto WHERE fecha_parto >= DATE_TRUNC('month', CURRENT_DATE)",
            ),
            (
                "citas_pendientes",
                "Citas Pendientes",
                "SELECT COUNT(*) FROM citas_cita WHERE estado = 'programada'",
            ),
        ]
        return consultas


class ConsultasPredefinidas:
    """Consultas SQL predefinidas para diferentes módulos"""

    REPORTES = {
        "pacientes": "SELECT id, nombre, apellido, fecha_nacimiento FROM pacientes_paciente WHERE activo = true",
        "embarazos": "SELECT id, paciente_id, fecha_inicio, semanas_gestacion FROM embarazos_embarazo WHERE activo = true",
        "controles": "SELECT id, embarazo_id, fecha_control, peso_actual FROM controles_controlprenatal ORDER BY fecha_control DESC",
        "ecografias": "SELECT id, embarazo_id, fecha_ecografia, tipo_ecografia FROM ecografias_ecografia ORDER BY fecha_ecografia DESC",
    }

    KPIS = {
        "conteos_basicos": [
            "SELECT COUNT(*) FROM pacientes_paciente WHERE activo = true",
            "SELECT COUNT(*) FROM embarazos_embarazo WHERE activo = true",
            "SELECT COUNT(*) FROM controles_controlprenatal",
            "SELECT COUNT(*) FROM ecografias_ecografia",
        ],
        "metricas_tiempo": [
            "SELECT COUNT(*) FROM controles_controlprenatal WHERE fecha_control >= CURRENT_DATE - INTERVAL '30 days'",
            "SELECT COUNT(*) FROM ecografias_ecografia WHERE fecha_ecografia >= CURRENT_DATE - INTERVAL '30 days'",
            "SELECT COUNT(*) FROM partos_parto WHERE fecha_parto >= CURRENT_DATE - INTERVAL '30 days'",
        ],
    }
