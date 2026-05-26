"""Urls module."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .stats_views import (
    dashboard_stats_view,
    general_stats_view,
)
from .views import (
    AlertaMedicaViewSet,
    AuditoriaReporteViewSet,
    DashboardKAPIViewSet,
    ReporteGeneradoViewSet,
    TipoReporteViewSet,
)
from .views_config import (
    configuracion_general,
    crear_backup,
    descargar_backup,
    eliminar_backup,
    horarios_atencion,
    listar_backups,
)
from .views_statistics import (
    all_statistics,
    citas_statistics,
    composition_chart,
    controles_statistics,
    dashboard_statistics,
    distribution_chart,
    download_statistics_excel,
    download_statistics_pdf,
    download_statistics_pdf_enhanced,
    embarazos_statistics,
    partos_statistics,
    stacked_bar_chart,
    statistics_by_period,
)

router = DefaultRouter()
router.register(r"tipos-reporte", TipoReporteViewSet, basename="tipo-reporte")
router.register(
    r"reportes-generados", ReporteGeneradoViewSet, basename="reporte-generado",
)
router.register(r"dashboard-kpis", DashboardKAPIViewSet, basename="dashboard-kpi")
router.register(r"alertas-medicas", AlertaMedicaViewSet, basename="alerta-medica")
router.register(
    r"auditoria-reportes", AuditoriaReporteViewSet, basename="auditoria-reporte",
)

urlpatterns = [
    # Endpoints simples y estadísticas (Alineados con reportesService.ts)
    path("dashboard/", dashboard_stats_view, name="dashboard-stats"),
    path("general/", general_stats_view, name="general-stats"),
    path("estadisticas-generales/", all_statistics, name="estadisticas-generales"),
    # Endpoints de reportes/estadísticas por módulo
    path(
        "pacientes/", embarazos_statistics, name="reporte-pacientes",
    ),  # Reusing embarazos_stats for now or mapping specific ones
    path("pacientes-embarazadas/", embarazos_statistics, name="pacientes-embarazadas"),
    path("nuevos-pacientes/", dashboard_statistics, name="nuevos-pacientes"),
    path("embarazos/", embarazos_statistics, name="reporte-embarazos"),
    path("embarazos-alto-riesgo/", embarazos_statistics, name="embarazos-alto-riesgo"),
    path("embarazos-trimestre/", embarazos_statistics, name="embarazos-trimestre"),
    path("partos/", partos_statistics, name="reporte-partos"),
    path("tasa-cesareas/", partos_statistics, name="tasa-cesareas"),
    path("complicaciones-partos/", partos_statistics, name="complicaciones-partos"),
    path("resultados-neonatales/", partos_statistics, name="resultados-neonatales"),
    path("controles/", controles_statistics, name="reporte-controles"),
    path("adherencia-controles/", controles_statistics, name="adherencia-controles"),
    path(
        "laboratorios/", all_statistics, name="reporte-laboratorio",
    ),  # Will need specific laboratory stats
    path("examenes-pendientes/", all_statistics, name="examenes-pendientes"),
    path("resultados-criticos/", all_statistics, name="resultados-criticos"),
    # Estadísticas avanzadas (Legacy/Internal)
    path("statistics/dashboard/", dashboard_statistics, name="dashboard-statistics"),
    path("statistics/embarazos/", embarazos_statistics, name="embarazos-statistics"),
    path("statistics/controles/", controles_statistics, name="controles-statistics"),
    path("statistics/citas/", citas_statistics, name="citas-statistics"),
    path("statistics/partos/", partos_statistics, name="partos-statistics"),
    path("statistics/all/", all_statistics, name="all-statistics"),
    path(
        "statistics/download-pdf/",
        download_statistics_pdf,
        name="download-statistics-pd",
    ),
    path(
        "statistics/download-pdf-enhanced/",
        download_statistics_pdf_enhanced,
        name="download-statistics-pdf-enhanced",
    ),
    path(
        "statistics/download-excel/",
        download_statistics_excel,
        name="download-statistics-excel",
    ),
    path("statistics/by-period/", statistics_by_period, name="statistics-by-period"),
    # Gráficos profesionales
    path("charts/composition/", composition_chart, name="composition-chart"),
    path("charts/stacked-bar/", stacked_bar_chart, name="stacked-bar-chart"),
    path("charts/distribution/", distribution_chart, name="distribution-chart"),
    # Configuración del Sistema
    path("configuracion/general/", configuracion_general, name="config-general"),
    path("configuracion/horarios/", horarios_atencion, name="config-horarios"),
    path("configuracion/backups/", listar_backups, name="listar-backups"),
    path("configuracion/backups/create/", crear_backup, name="crear-backup"),
    path(
        "configuracion/backups/<str:filename>/",
        descargar_backup,
        name="descargar-backup",
    ),
    path(
        "configuracion/backups/<str:filename>/delete/",
        eliminar_backup,
        name="eliminar-backup",
    ),
    # Router URLs
    path("", include(router.urls)),
]

# app_name = 'reportes'  # Comentado temporalmente para diagnosticar
