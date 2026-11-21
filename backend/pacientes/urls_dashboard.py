"""Urls dashboard module."""
from django.urls import path

from .dashboard_views import dashboard_graficas, dashboard_kpis

urlpatterns = [
    path("kpis/", dashboard_kpis, name="dashboard-kpis"),
    path("graficas/", dashboard_graficas, name="dashboard-graficas"),
]
