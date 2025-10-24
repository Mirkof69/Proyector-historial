from django.urls import path
from .views import (
    CalculadoraEdadGestacionalView,
    CalculadoraIMCView,
    CalculadoraRiesgoPreeclampsiaView
)

urlpatterns = [
    path('edad-gestacional/', CalculadoraEdadGestacionalView.as_view(), name='calc-edad-gestacional'),
    path('imc/', CalculadoraIMCView.as_view(), name='calc-imc'),
    path('riesgo-preeclampsia/', CalculadoraRiesgoPreeclampsiaView.as_view(), name='calc-preeclampsia'),
]