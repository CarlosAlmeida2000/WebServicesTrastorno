from django.urls import path
from Monitoreo import views

urlpatterns = [
    path('historial/', views.Historial.as_view()),
    path('monitorea/', views.Monitoreo.as_view())
]