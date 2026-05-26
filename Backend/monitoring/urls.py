"""URLs for the monitoring app.
"""

from django.urls import path

from . import views

app_name = "monitoring"

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
]
