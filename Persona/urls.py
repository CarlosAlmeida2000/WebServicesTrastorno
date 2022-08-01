from django.urls import path
from Persona import views

urlpatterns = [
    path('cuidador/', views.Cuidador.as_view()),
    path('autenticacion/', views.Autenticacion.as_view()),
    path('custodiado/', views.Custodiado.as_view())
]