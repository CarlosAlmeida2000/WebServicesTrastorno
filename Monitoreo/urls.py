from django.urls import path
from Monitoreo import views

urlpatterns = [
    path('historial/', views.HistorialCustodiado.as_view()),
    path('grafico/', views.GraficoCustodiado.as_view()),
    path('monitorea/', views.Monitoreo.as_view())
]