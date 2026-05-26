"""CAT_ROLES - URLs"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CatRolViewSet

# URLs
router = DefaultRouter()
router.register(r"roles", CatRolViewSet)
urlpatterns = [path("", include(router.urls))]
