from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CalculadorasViewSet, CalculoClinicoViewSet

router = DefaultRouter()
router.register(r'historial', CalculoClinicoViewSet, basename='calculo-clinico')

# URLs personalizadas para calculadoras
calculadoras_urls = [
    path('edad-gestacional/', CalculadorasViewSet.as_view({'post': 'edad_gestacional'}), name='edad-gestacional'),
    path('imc/', CalculadorasViewSet.as_view({'post': 'imc'}), name='imc'),
    path('ganancia-peso/', CalculadorasViewSet.as_view({'post': 'ganancia_peso'}), name='ganancia-peso'),
    path('bishop/', CalculadorasViewSet.as_view({'post': 'bishop'}), name='bishop'),
    path('riesgo-preeclampsia/', CalculadorasViewSet.as_view({'post': 'riesgo_preeclampsia'}), name='riesgo-preeclampsia'),
    path('diabetes-gestacional/', CalculadorasViewSet.as_view({'post': 'diabetes_gestacional'}), name='diabetes-gestacional'),
    path('ila/', CalculadorasViewSet.as_view({'post': 'ila'}), name='ila'),
    path('peso-fetal/', CalculadorasViewSet.as_view({'post': 'peso_fetal'}), name='peso-fetal'),
    path('apgar/', CalculadorasViewSet.as_view({'post': 'apgar'}), name='apgar'),
    path('rmi-ovario/', CalculadorasViewSet.as_view({'post': 'rmi_ovario'}), name='rmi-ovario'),
    path('riesgo-endometrio/', CalculadorasViewSet.as_view({'post': 'riesgo_endometrio'}), name='riesgo-endometrio'),
    path('pam/', CalculadorasViewSet.as_view({'post': 'pam'}), name='pam'),
    path('superficie-corporal/', CalculadorasViewSet.as_view({'post': 'superficie_corporal'}), name='superficie-corporal'),
]

urlpatterns = [
    path('', include(router.urls)),
] + calculadoras_urls