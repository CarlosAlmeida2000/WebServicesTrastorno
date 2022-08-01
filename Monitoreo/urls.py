from django.urls import path
from Persona import views

urlpatterns = [
    path('historial/', views.Historial.as_view()),
    path('monitorea/', views.Monitorea.as_view())
]